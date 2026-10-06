from crewai import Agent, Task, Crew, LLM

llm = LLM(
    model="ollama/llama3.1",
    base_url="http://localhost:11434"
)

print("LLM CLASS:", type(llm))
print("LLM PROVIDER:", getattr(llm, "provider", None))
print("LLM BASE URL:", getattr(llm, "base_url", None))

planner = Agent(
    role="Data Analysis Planner",
    goal="Break down a business question into clear analysis steps",
    backstory="You are an expert data analyst who plans investigations before executing them.",
    llm=llm,
    verbose=True
)

plan_task = Task(
    description="Break down this question into 3-5 concrete analysis steps: "
                "'Which transaction patterns are most associated with fraud in this dataset?'",
    expected_output="A numbered list of 3-5 concrete analysis steps.",
    agent=planner
)

crew = Crew(agents=[planner], tasks=[plan_task], verbose=True)
result = crew.kickoff()

print("\n--- FINAL PLAN ---")
print(result)