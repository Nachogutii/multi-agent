import os
from openai import AzureOpenAI
from tests.agents.CustomerAgent import CustomerAgent
from tests.agents.ConversationPhaseManager import ConversationPhaseManager
from tests.agents.CustomerStateAgent import CustomerStateAgent
from tests.agents.Orchestrator import Orchestrator
from agents.evaluator import ObserverCoach
from dotenv import load_dotenv
load_dotenv()


# Initialize Azure client
azure_client = AzureOpenAI(
    api_key=os.environ.get("AZURE_OPENAI_KEY"),
    azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
    api_version=os.environ.get("AZURE_OPENAI_API_VERSION")
)

deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT")


# Initialize agents
customer_agent = CustomerAgent(azure_client=azure_client)
phase_manager = ConversationPhaseManager()
emotion_agent = CustomerStateAgent()
evaluator = ObserverCoach()  # Assuming this is already implemented
orchestrator = Orchestrator(customer_agent, phase_manager, emotion_agent, evaluator)

# Start conversation
orchestrator.initialize_conversation()

print("\nConversation started. Type 'exit' to end.\n")
while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        break

    reply, feedback = orchestrator.handle_user_input(user_input)
    print(f"Customer: {reply}\n")

    if feedback:
        print("--- Conversation Feedback ---")
        print(feedback)
        break