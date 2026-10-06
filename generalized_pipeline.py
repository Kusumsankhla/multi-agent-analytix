import os
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

import sqlite3
import pandas as pd
from crewai import Agent, Task, Crew, LLM
from crewai.tools import tool
from fetch_crypto_data import fetch_live_crypto_data

llm = LLM(
    model="ollama/qwen2.5:7b",
    base_url="http://localhost:11434"
)


def load_csv_to_db(csv_path, db_path, table_name, sample_size=None):
    """Loads a CSV into a SQLite database. Returns the real column names and dtypes."""
    df = pd.read_csv(csv_path, encoding="latin1")
    if sample_size and len(df) > sample_size:
        df = df.sample(n=sample_size, random_state=42)
    conn = sqlite3.connect(db_path)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()
    return list(df.columns), df.dtypes


def load_dataframe_to_db(df, db_path, table_name):
    """Like load_csv_to_db, but takes a DataFrame directly — for live/API data sources."""
    conn = sqlite3.connect(db_path)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()
    return list(df.columns), df.dtypes


def build_schema_info(db_path, table_name, columns, dtypes, extra_notes=""):
    """Auto-builds a schema description string the agents can use, flagging
    high-cardinality columns so agents avoid bad GROUP BYs."""
    col_lines = []
    high_cardinality_warns = []
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    for col in columns:
        try:
            cursor.execute(f'SELECT COUNT(DISTINCT "{col}") FROM "{table_name}"')
            distinct_count = cursor.fetchone()[0]
        except Exception:
            distinct_count = None
        col_lines.append(f"{col} ({dtypes[col]})")
        if distinct_count and distinct_count > 50:
            high_cardinality_warns.append(col)
    conn.close()

    schema = f"""
Database: SQLite file '{db_path}'
Table '{table_name}' has columns: {', '.join(col_lines)}
Use ONLY these real column names. This is SQLite — do NOT use PostgreSQL syntax like information_schema.
Write ONE simple query — no subqueries, no joins, no CTEs.
Always add LIMIT 15 to any query that could return more than 15 rows.
When calculating rates or averages by dividing counts, always multiply by 1.0 first to avoid integer division (SQLite truncates division between two integers).
"""
    if high_cardinality_warns:
        schema += f"IMPORTANT: These columns have too many unique values to GROUP BY directly — never group by them: {', '.join(high_cardinality_warns)}\n"
    if extra_notes:
        schema += extra_notes + "\n"
    return schema


def run_pipeline(db_path, table_name, schema_info, question, progress_callback=None):
    """Runs the Planner -> Coder -> Verifier pipeline against any dataset,
    given its schema. Returns (final_output, tool_call_log)."""

    TOOL_CALL_LOG = []

    @tool("Run SQL Query")
    def run_sql_query(query: str) -> str:
        """Executes a SQL query against the connected SQLite database and returns the results.
        Use standard SQLite syntax. Do NOT add LIMIT unless explicitly asked.
        You MUST call this tool to get real data — never write out a fake result."""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [d[0] for d in cursor.description]
            conn.close()
            result = f"Columns: {columns}\nRows: {rows}"
            TOOL_CALL_LOG.append({"query": query, "result": result})
            return result
        except Exception as e:
            error_result = f"SQL Error: {str(e)}"
            TOOL_CALL_LOG.append({"query": query, "result": error_result})
            return error_result

    planner = Agent(
        role="Data Analysis Planner",
        goal="Break down a business question into clear, actionable SQL-based analysis steps",
        backstory="You are an expert data analyst who plans investigations before executing them.",
        llm=llm,
        verbose=True
    )

    coder = Agent(
        role="Data Analyst Coder",
        goal="Write and execute SQL queries to answer data analysis questions using real, verified data",
        backstory="You are a skilled data analyst who writes precise SQL queries and always verifies "
                   "your answers by actually running them, never guessing. You NEVER write out a "
                   "results table without first calling the Run SQL Query tool.",
        tools=[run_sql_query],
        llm=llm,
        verbose=True
    )

    verifier = Agent(
        role="Verification Agent",
        goal="Independently re-check analysis claims by re-running queries and comparing results",
        backstory="You are a strict, skeptical auditor. You NEVER modify the query you are checking. "
                   "You NEVER write out a raw output without first actually calling the Run SQL Query "
                   "tool yourself. You run the exact same query, show the real tool output, and only "
                   "then give a verdict.",
        tools=[run_sql_query],
        llm=llm,
        verbose=True
    )

    plan_task = Task(
        description=f"{schema_info}\nBreak this question into 2-3 concrete SQL-answerable steps: '{question}'. "
                    "Only reference the real columns listed above.",
        expected_output="A numbered list of 2-3 concrete steps, each answerable with a single SQL query using only real column names.",
        agent=planner,
        callback=lambda output: progress_callback("Planning complete — Coding started") if progress_callback else None
    )

    code_task = Task(
        description=f"{schema_info}\nBased on the plan above, write and run ONE SQL query using the Run SQL Query tool "
                    f"on the '{table_name}' table to answer the first step. Use only real column names. "
                    "You MUST actually call the tool — do not write a results table from memory or imagination.",
        expected_output="The SQL query used and its real result from the tool.",
        agent=coder,
        context=[plan_task],
        callback=lambda output: progress_callback("Coding complete — Verifying started") if progress_callback else None
    )

    verify_task = Task(
        description="Run the EXACT SAME query the Coder used, with no changes, using the Run SQL Query tool. "
                    "You MUST actually call the tool. Show the real raw output, then give a verdict: CONFIRMED or FLAGGED.",
        expected_output="Real raw tool output plus a CONFIRMED/FLAGGED verdict.",
        agent=verifier,
        context=[code_task],
        callback=lambda output: progress_callback("Verification complete") if progress_callback else None
    )

    if progress_callback:
        progress_callback("Planning started")

    crew = Crew(agents=[planner, coder, verifier], tasks=[plan_task, code_task, verify_task], verbose=True)
    result = crew.kickoff()
    return result, TOOL_CALL_LOG


def analyze_dataset(csv_path, db_path, table_name, question, sample_size=None, extra_notes="", progress_callback=None):
    """One call to go from a raw CSV to a verified answer. This is the reusable entry point."""
    columns, dtypes = load_csv_to_db(csv_path, db_path, table_name, sample_size)
    schema_info = build_schema_info(db_path, table_name, columns, dtypes, extra_notes)
    result, tool_log = run_pipeline(db_path, table_name, schema_info, question, progress_callback)

    print("\n--- FINAL PIPELINE OUTPUT (agents' claims) ---")
    print(result)

    print("\n--- ACTUAL TOOL CALLS MADE (ground truth) ---")
    if not tool_log:
        print("WARNING: No tool calls were made at all. The agents' answers are fully hallucinated.")
    else:
        for i, call in enumerate(tool_log, 1):
            print(f"\nCall {i}:")
            print(f"  Query: {call['query']}")
            print(f"  Real result: {call['result']}")

    return result, tool_log


if __name__ == "__main__":
    analyze_dataset(
        csv_path="train_transaction.csv",
        db_path="fraud_data.db",
        table_name="transactions",
        question="How does ProductCD relate to fraud rate in this dataset?",
        sample_size=20000
    )

    df = fetch_live_crypto_data()
    columns, dtypes = load_dataframe_to_db(df, "crypto_data.db", "coins")
    schema_info = build_schema_info("crypto_data.db", "coins", columns, dtypes)
    result, tool_log = run_pipeline("crypto_data.db", "coins", schema_info,
                                     "Which coin has had the highest price change percentage today?")
    print("\n--- FINAL PIPELINE OUTPUT (agents' claims) ---")
    print(result)
    