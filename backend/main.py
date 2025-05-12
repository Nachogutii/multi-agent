import random
import sys
import os
from typing import Dict
from openai import AzureOpenAI
from dotenv import load_dotenv

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
    response = orchestrator.process_user_input(msg.text)
    # Get the phase directly from the orchestrator for consistency
    # Note: observer and phase_manager may be out of sync
    current_phase = orchestrator.phase_manager.get_current_phase()
    print(f"🚨 PHASE RETURNED TO FRONTEND: {current_phase}")
    return {
        "response": response,
        "phase": current_phase,
        "feedback": roleplay_system.observer.summarize_conversation()
    }

@app.get("/api/feedback/structured")
def get_structured_feedback():
    # Ensure we use the observer from the Orchestrator for consistency
    observer = roleplay_system.observer
    
    all_phases_in_history = list({m.get("phase") for m in observer.conversation_history})
    for phase in all_phases_in_history:
        if phase and phase not in observer.phase_scores:
            context = "\n".join([
                f"User: {m['user']}\nCustomer: {m['customer']}"
                for m in observer.conversation_history
                if m.get("phase") == phase
            ])
            if context.strip():
                observer.evaluate_phase(phase, context)

    result = observer.summarize_conversation()
    phase_scores = result.get("phase_scores", {})
    feedback_data = result.get("feedback", {})
    
    # Get the custom score based on fulfilled aspects
    custom_score_data = result.get("custom_score", {})
    custom_score = custom_score_data.get("score", 0)
    custom_score_explanation = custom_score_data.get("explanation", "")
    score_details = custom_score_data.get("details", {})
    
    # Get aspect counters
    aspect_counts = result.get("aspect_counts", {})
    total_critical_aspects = aspect_counts.get("critical_aspects", 0)
    total_optional_aspects = aspect_counts.get("optional_aspects", 0)
    total_red_flags = aspect_counts.get("red_flags", 0)

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
        "custom_score": custom_score,
        "custom_score_explanation": custom_score_explanation,
        "score_details": score_details,
        "aspect_counts": {
            "critical": total_critical_aspects,
            "optional": total_optional_aspects,
            "red_flags": total_red_flags
        },
        "suggestions": suggestions,
        "strength": strengths,
        "opportunity": opportunities,
        "training": trainings,
        "issues": opportunities
    }

@app.post("/api/reset")
def reset():
    # Reset the entire RoleplaySystem (agent + observer + scenario)
    new_scenario = roleplay_system.setup_scenario()

    # Reset the Orchestrator using the observer instance
    global orchestrator
    orchestrator = Orchestrator(
        azure_client=roleplay_system.azure.get_client(),
        deployment=roleplay_system.azure.deployment,
        shared_observer=roleplay_system.observer
    )
    
    # Verify they share the same phase_manager
    observer_phase = roleplay_system.observer.phase_manager.get_current_phase()
    orchestrator_phase = orchestrator.phase_manager.get_current_phase()
    print(f"🔄 RESET - Observer phase: {observer_phase}")
    print(f"🔄 RESET - Orchestrator phase: {orchestrator_phase}")
    print(f"🔄 RESET - Same instance: {roleplay_system.observer.phase_manager is orchestrator.phase_manager}")

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