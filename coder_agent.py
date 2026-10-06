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
    Use standard SQLite syntax. Always include a LIMIT clause for exploratory queries."""
    try:
        conn = sqlite3.connect("fraud_data.db")
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        conn.close()
        result = f"Columns: {columns}\nRows: {rows[:20]}"
        return result
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

code_task = Task(
    description="Using the 'transactions' table in fraud_data.db, run a query that returns "
                "isFraud alongside COUNT(*), grouped by isFraud, so the label is unambiguous. "
                "You MUST use the Run SQL Query tool to get the real answer — do not guess.",
    expected_output="A clear table showing isFraud value (0 or 1) alongside its exact count, based on real query results.",
    agent=coder
)

crew = Crew(agents=[coder], tasks=[code_task], verbose=True)
result = crew.kickoff()

print("\n--- FINAL ANSWER ---")
print(result)