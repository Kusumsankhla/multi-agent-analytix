from crewai import Agent, Task, Crew, LLM
from crewai.tools import tool
import sqlite3

llm = LLM(
    model="ollama/llama3.1",
    base_url="http://localhost:11434"
)

@tool("Run SQL Query")
def run_sql_query(query: str) -> str:
    """Executes a SQL query against the fraud_data.db SQLite database and returns the results.
    The database has two tables: 'transactions' and 'identity'.
    Use standard SQLite syntax. Do NOT add LIMIT unless the task explicitly asks for it."""
    try:
        conn = sqlite3.connect("fraud_data.db")
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        conn.close()
        return f"Columns: {columns}\nRows: {rows}"
    except Exception as e:
        return f"SQL Error: {str(e)}"

coder = Agent(
    role="Data Analyst Coder",
    goal="Write and execute SQL queries to answer data analysis questions using real, verified data",
    backstory="You are a skilled data analyst who writes precise SQL queries and always verifies "
               "your answers by actually running them against the database, never guessing.",
    tools=[run_sql_query],
    llm=llm,
    verbose=True
)

verifier = Agent(
    role="Verification Agent",
    goal="Independently re-check analysis claims by re-running queries and comparing results",
    backstory="You are a strict, skeptical auditor. You NEVER modify the query you are checking "
               "in any way — no LIMIT, no extra clauses, nothing. You run the EXACT same query, "
               "capture its full raw output, and only then compare it to the claim.",
    tools=[run_sql_query],
    llm=llm,
    verbose=True
)

code_task = Task(
    description="Using the 'transactions' table in fraud_data.db, run this EXACT query: "
                "'SELECT isFraud, COUNT(*) FROM transactions GROUP BY isFraud'. "
                "Do not modify it. Report the real results.",
    expected_output="A clear table showing isFraud value (0 or 1) alongside its exact count.",
    agent=coder
)

verify_task = Task(
    description="Run this EXACT SAME query yourself, with no changes whatsoever: "
                "'SELECT isFraud, COUNT(*) FROM transactions GROUP BY isFraud'. "
                "Do NOT add LIMIT or any other clause. First show the raw tool output in full, "
                "then compare it line by line to the Coder's claim above. "
                "State clearly: CONFIRMED (exact match) or FLAGGED (any mismatch).",
    expected_output="The raw tool output, followed by a CONFIRMED or FLAGGED verdict with both sets of numbers shown.",
    agent=verifier,
    context=[code_task]
)

crew = Crew(agents=[coder, verifier], tasks=[code_task, verify_task], verbose=True)
result = crew.kickoff()

print("\n--- FINAL VERIFIED ANSWER (from agents) ---")
print(result)

# --- INDEPENDENT PYTHON-LEVEL GROUND TRUTH CHECK ---
# This does NOT trust the agents at all — it re-runs the query directly in Python
# and checks whether the agents' final text actually contains the correct numbers.
print("\n--- AUTOMATED GROUND-TRUTH CHECK (no LLM involved) ---")
conn = sqlite3.connect("fraud_data.db")
cursor = conn.cursor()
cursor.execute("SELECT isFraud, COUNT(*) FROM transactions GROUP BY isFraud")
ground_truth = cursor.fetchall()
conn.close()

print("Ground truth (from direct Python query):", ground_truth)

result_text = str(result)
all_match = True
for label, count in ground_truth:
    if str(count) not in result_text:
        all_match = False
        print(f"MISMATCH: expected count {count} for isFraud={label}, not found in agent output")

if all_match:
    print("AUTOMATED CHECK: PASSED — all ground-truth numbers appear in the agents' final output")
else:
    print("AUTOMATED CHECK: FAILED — agent output does not contain the correct ground-truth numbers")