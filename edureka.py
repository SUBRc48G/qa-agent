# Install OpenAI (latest)
# !pip install openai

import os
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

print("🚀 Script started")

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Missing OPENAI_API_KEY")

model_name = os.getenv("MODEL_NAME", "gpt-4o-mini")

print("✅ Requirements loaded")

client = OpenAI()

# ---------------- BASIC CALL ----------------
def simple_chat(message):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": message}
        ]
    )
    return response.choices[0].message.content


# ---------------- AGENTS ----------------

# Agent 1: Symptom Agent
def symptom_agent(input_text):
    print("\n🤖 [Symptom Agent]")
    response = simple_chat(
        f"Classify the severity of this symptom and list possible conditions: {input_text}"
    )
    print(response)
    return response


# Agent 2: Scheduler Agent
def scheduler_agent(symptom_summary):
    print("\n📅 [Scheduler Agent]")
    response = simple_chat(
        f"Based on this summary, suggest next steps for the patient: {symptom_summary}"
    )
    print(response)
    return response


# Agent 3: Follow-Up Agent
def followup_agent():
    print("\n💬 [Follow-Up Agent]")
    response = simple_chat(
        "Ask how the patient is feeling now and whether the patient's condition is better or worse."
    )
    print(response)
    return response


# Agent 4: Logger Agent
def logger_agent(name, pid, input_text, output_text):
    print("\n📘 [Logger Agent] Recording information...")
    log_entry = (
        f"\nTime: {datetime.now()}\n"
        f"Patient: {name} (ID: {pid})\n"
        f"Input: {input_text}\n"
        f"AI Summary:\n{output_text}\n"
        f"{'='*50}\n"
    )
    with open("multiagent_conversation_log.txt", "a") as f:
        f.write(log_entry)


# ---------------- MAIN WORKFLOW ----------------
if __name__ == "__main__":

    print("AI Health Assistant (OpenAI Version)\n")

    name = input("Enter your name: ")
    pid = input("Enter your Patient ID: ")
    user_input = input("Please describe your health symptoms: ")

    # Agent 1
    summary = symptom_agent(user_input)

    # Agent 2
    next_steps = scheduler_agent(summary)

    # Agent 3
    followups = followup_agent()

    # Agent 4
    logger_agent(
        name,
        pid,
        user_input,
        summary + "\n\n" + next_steps + "\n\n" + followups
    )