import random
import sys
import os
from typing import Dict
from openai import AzureOpenAI
from dotenv import load_dotenv

from frontend.display import print_colored, print_scenario_info
from agents.customer import CustomerAgent
from agents.evaluator import ObserverCoach
from agents.conversation_phase import ConversationPhaseManager
from agents.Orchestrator import Orchestrator

class AzureConnection:
    def __init__(self):
        load_dotenv()
        self.endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        self.api_key = os.environ.get("AZURE_OPENAI_KEY")
        self.deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
        self.client = None
        print(f"Deployment set to: {self.deployment}")

    def initialize(self) -> bool:
        try:
            if not self.endpoint or not self.api_key:
                raise ValueError("Azure OpenAI credentials not found in environment variables")

            self.client = AzureOpenAI(
                api_key=self.api_key,
                api_version="2024-10-21",
                azure_endpoint=self.endpoint
            )

            self.test_connection()
            return True

        except Exception as e:
            print("\n❌ Error initializing Azure OpenAI:")
            print(f"Error: {str(e)}")
            return False

    def test_connection(self) -> bool:
        try:
            if not self.client:
                raise ValueError("Azure OpenAI client not initialized")

            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "You are a test assistant."},
                    {"role": "user", "content": "Say 'hello'"}
                ],
                max_tokens=10
            )

            print("\n✅ Successfully connected to Azure OpenAI!")
            print(f"Test response: {response.choices[0].message.content}")
            return True

        except Exception as e:
            print("\n❌ Error connecting to Azure OpenAI:")
            print(f"Error: {str(e)}")
            return False

    def get_client(self) -> AzureOpenAI:
        if not self.client:
            raise ValueError("Azure OpenAI client not initialized")
        return self.client

class RoleplaySystem:
    def __init__(self):
        self.scenario = None
        self.customer_agent = None
        self.observer = None
        self.conversation_history = []
        self.azure = AzureConnection()

    def initialize(self) -> bool:
        return self.azure.initialize()

    def setup_scenario(self):
        self.scenario = {
            "title": "Copilot Welcome",
            "description": "Customer is already using Microsoft 365 and is exploring how Copilot can improve her workflow.",
            "initial_query": "Hi, I'm Rachel. I just got Copilot and was curious how to get the most out of it."
        }

        self.customer_agent = CustomerAgent(
            azure_client=self.azure.get_client(),
            deployment=self.azure.deployment
        )

        self.observer = ObserverCoach(
            azure_client=self.azure.get_client(),
            deployment=self.azure.deployment
        )

        self.conversation_history = []

        return {
            "scenario": self.scenario["title"],
            "description": self.scenario["description"],
            "initial_query": self.scenario["initial_query"]
        }

    def process_user_message(self, message: str) -> str:
        customer_response = self.customer_agent.generate_response(message)
        self.observer.add_interaction(message, customer_response)
        return customer_response

# === FASTAPI MODE ===

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    text: str

roleplay_system = RoleplaySystem()
roleplay_system.initialize()
roleplay_system.setup_scenario()

orchestrator = Orchestrator(
    azure_client=roleplay_system.azure.get_client(),
    deployment=roleplay_system.azure.deployment,
    shared_observer=roleplay_system.observer
)

@app.post("/api/chat")
def chat(msg: Message):
    response = roleplay_system.process_user_message(msg.text)
    phase = roleplay_system.observer.phase_manager.get_current_phase()
    return {
        "response": response,
        "phase": phase,
        "feedback": roleplay_system.observer.summarize_conversation()
    }

@app.get("/api/feedback/structured")
def get_structured_feedback():
    all_phases_in_history = list({m.get("phase") for m in roleplay_system.observer.conversation_history})
    for phase in all_phases_in_history:
        if phase and phase not in roleplay_system.observer.phase_scores:
            context = "\n".join([
                f"User: {m['user']}\nCustomer: {m['customer']}"
                for m in roleplay_system.observer.conversation_history
                if m.get("phase") == phase
            ])
            if context.strip():
                roleplay_system.observer.evaluate_phase(phase, context)

    result = roleplay_system.observer.summarize_conversation()
    phase_scores = result.get("phase_scores", {})
    feedback_data = result.get("feedback", {})

    suggestions = []
    strengths = []
    opportunities = []
    trainings = []

    if isinstance(feedback_data, dict):
        for f in feedback_data.values():
            if isinstance(f, dict):
                if f.get("suggestion"):
                    suggestions.append(f["suggestion"])
                if f.get("strength"):
                    strengths.append(f["strength"])
                if f.get("opportunity"):
                    opportunities.append(f["opportunity"])
                if f.get("training"):
                    trainings.append(f["training"])

    return {
        "metrics": phase_scores,
        "suggestions": suggestions,
        "strength": strengths,
        "opportunity": opportunities,
        "training": trainings,
        "issues": opportunities
    }

@app.post("/api/reset")
def reset():
    # Reinicia todo el RoleplaySystem (agente + observador + escenario)
    new_scenario = roleplay_system.setup_scenario()

    # Reinicia también el Orchestrator
    global orchestrator
    orchestrator = Orchestrator(
        azure_client=roleplay_system.azure.get_client(),
        deployment=roleplay_system.azure.deployment,
        shared_observer=roleplay_system.observer
    )

    return {
        "scenario": new_scenario["scenario"],
        "description": new_scenario["description"],
        "initial_query": new_scenario["initial_query"]
    }


@app.get("/api/scenario")
def get_scenario():
    return {
        "title": "Copilot Welcome",
        "description": "Customer is already using Microsoft 365 and is exploring how Copilot can improve her workflow.",
        "initial_query": "Hi, I'm Rachel. I just got Copilot and was curious how to get the most out of it."
    }

def run_api():
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()