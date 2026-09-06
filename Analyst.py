from crewai import Agent, Task, Crew, LLM
import os
from getpass import getpass

# Get Groq API Key
print("🔑 Enter your Groq API Key")
groq_api_key = getpass("Groq API Key: ")

os.environ["GROQ_API_KEY"] = groq_api_key

# Initialize LLM
llm = LLM(
    model="groq/llama-3.1-8b-instant",
    temperature=0.7,
    max_tokens=1000,
    api_key=groq_api_key
)

print("✅ LLM initialized!")

# 👇 Ask user for topic
user_topic = input("\n🧠 Enter a topic you want to research: ")

# Create Agent
researcher = Agent(
    role="Research Analyst",
    goal=f"Research the topic: {user_topic} and provide clear insights",
    backstory="You are a skilled researcher who provides accurate and structured information.",
    verbose=True,
    llm=llm
)

# Create Task dynamically
task = Task(
    description=f"Analyze and explain: {user_topic}",
    expected_output="A short, clear summary with key insights and examples.",
    agent=researcher
)

# Create Crew
crew = Crew(
    agents=[researcher],
    tasks=[task],
    verbose=True
)

# Run
result = crew.kickoff()

print("\n📊 Final Output:\n")
print(result)