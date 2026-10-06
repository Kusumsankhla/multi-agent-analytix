import os
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

import sqlite3
from crewai import Agent, Task, Crew, LLM
from crewai.tools import tool

llm = LLM(
    model="ollama/qwen2.5:7b",
    base_url="http://localhost:11434"
)

TOOL_CALL_LOG = []

@tool("Run SQL Query")
def run_sql_query(query: str) -> str:
    """Executes a SQL query against the fraud_data.db SQLite database and returns the results.
    The database has two tables: 'transactions' and 'identity'.
    Use standard SQLite syntax. Do NOT add LIMIT unless explicitly asked.
    You MUST call this tool to get real data — never write out a fake result."""
    try:
        conn = sqlite3.connect("fraud_data.db")
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        conn.close()
        result = f"Columns: {columns}\nRows: {rows}"
        TOOL_CALL_LOG.append({"query": query, "result": result})
        return result
    except Exception as e:
        error_result = f"SQL Error: {str(e)}"
        TOOL_CALL_LOG.append({"query": query, "result": error_result})
        return error_result

SCHEMA_INFO = """
Database: SQLite file 'fraud_data.db'
Table 'transactions' has columns including: TransactionID, isFraud, TransactionAmt, ProductCD, card1-card6, addr1, addr2, dist1, dist2, P_emaildomain, R_emaildomain, C1-C14, D1-D15, M1-M9, V1-V339
Table 'identity' has columns including: TransactionID, DeviceType, DeviceInfo, id_01-id_38
Use ONLY these real table and column names. This is SQLite — do NOT use PostgreSQL syntax like information_schema.
IMPORTANT: card1-card6 have too many unique values to GROUP BY directly — never group by them.
For meaningful groupings, use LOW-cardinality columns instead: isFraud, ProductCD, or DeviceType.
Always add LIMIT 15 to any query that could return more than 15 rows.
Write ONE simple query — no subqueries, no joins, no CTEs.
"""

QUESTION = "How does the ProductCD (product category) relate to fraud rate in this dataset?"

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
    description=f"{SCHEMA_INFO}\nBreak this question into 2-3 concrete SQL-answerable steps: '{QUESTION}'. "
                "Only reference the real columns listed above.",
    expected_output="A numbered list of 2-3 concrete steps, each answerable with a single SQL query using only real column names.",
    agent=planner
)

code_task = Task(
    description=f"{SCHEMA_INFO}\nBased on the plan above, write and run ONE SQL query using the Run SQL Query tool "
                "on the 'transactions' table to answer the first step. Use only real column names. "
                "You MUST actually call the tool — do not write a results table from memory or imagination.",
    expected_output="The SQL query used and its real result from the tool.",
    agent=coder,
    context=[plan_task]
)

verify_task = Task(
    description="Run the EXACT SAME query the Coder used, with no changes, using the Run SQL Query tool. "
                "You MUST actually call the tool. Show the real raw output, then give a verdict: CONFIRMED or FLAGGED.",
    expected_output="Real raw tool output plus a CONFIRMED/FLAGGED verdict.",
    agent=verifier,
    context=[code_task]
)

crew = Crew(agents=[planner, coder, verifier], tasks=[plan_task, code_task, verify_task], verbose=True)
result = crew.kickoff()

print("\n--- FINAL PIPELINE OUTPUT (agents' claims) ---")
print(result)

print("\n--- ACTUAL TOOL CALLS MADE (ground truth, not agent's claims) ---")
if not TOOL_CALL_LOG:
    print("WARNING: No tool calls were made at all. The agents' answers are fully hallucinated.")
else:
    for i, call in enumerate(TOOL_CALL_LOG, 1):
        print(f"\nCall {i}:")
        print(f"  Query: {call['query']}")
        print(f"  Real result: {call['result']}")