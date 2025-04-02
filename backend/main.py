import random
import sys
import os
from typing import Dict
from openai import AzureOpenAI
from dotenv import load_dotenv

from frontend.display import print_colored, print_scenario_info
from agents.customer import CustomerAgent
from agents.evaluator import ObserverCoach
from agents.conversation_phase import ConversationPhase
from profiles import CUSTOMER_PROFILES, PRODUCT_INFO, SCENARIOS

class AzureConnection:
    """Manages Azure OpenAI connection and configuration."""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Get Azure configuration
        self.endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        self.api_key = os.environ.get("AZURE_OPENAI_KEY")
        self.deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
        self.client = None
    
    def initialize(self) -> bool:
        """Initialize Azure OpenAI client."""
        try:
            if not self.endpoint or not self.api_key:
                raise ValueError("Azure OpenAI credentials not found in environment variables")
            
            if not self.deployment:
                raise ValueError("Azure OpenAI deployment name not found in environment variables")
            
            self.client = AzureOpenAI(
                api_key=self.api_key,
                api_version="2024-10-21",
                azure_endpoint=self.endpoint
            )
            
            # Test the connection
            self.test_connection()
            return True
            
        except Exception as e:
            print("\n❌ Error initializing Azure OpenAI:")
            print(f"Error: {str(e)}")
            return False
    
    def test_connection(self) -> bool:
        """Test Azure OpenAI connection."""
        try:
            if not self.client:
                raise ValueError("Azure OpenAI client not initialized")
            
            # Try a simple call
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "You are a test assistant."},
                    {"role": "user", "content": "Say 'hello'"}
                ],
                max_tokens=10
            )
            
            print("\n✅ Successfully connected to Azure OpenAI!")
            print(f"Endpoint: {self.endpoint}")
            print(f"Deployment: {self.deployment}")
            print(f"Test response: {response.choices[0].message.content}")
            return True
            
        except ValueError as e:
            print("\n❌ Configuration Error:")
            print(f"Error: {str(e)}")
            print("\nPlease ensure you have set the following environment variables:")
            print("export AZURE_OPENAI_ENDPOINT='your-endpoint'")
            print("export AZURE_OPENAI_KEY='your-key'")
            print("export AZURE_OPENAI_DEPLOYMENT='your-deployment-name'")
            return False
        except Exception as e:
            print("\n❌ Error connecting to Azure OpenAI:")
            print(f"Error: {str(e)}")
            return False
    
    def get_client(self) -> AzureOpenAI:
        """Get the Azure OpenAI client."""
        if not self.client:
            raise ValueError("Azure OpenAI client not initialized")
        return self.client

class RoleplaySystem:
    """Main system that manages the roleplay scenario."""
    
    def __init__(self):
        self.scenario = None
        self.customer_agent = None
        self.observer = None
        self.conversation_history = []
        self.azure = AzureConnection()
    
    def initialize(self) -> bool:
        """Initialize the roleplay system."""
        return self.azure.initialize()
    
    def setup_scenario(self):
        """Set up a new roleplay scenario."""
        # Choose a random scenario
        self.scenario = random.choice(SCENARIOS)
        
        # Choose random customer attributes
        personality = random.choice(list(CUSTOMER_PROFILES["personalities"].keys()))
        tech_level = random.choice(list(CUSTOMER_PROFILES["tech_levels"].keys()))
        role = random.choice(list(CUSTOMER_PROFILES["roles"].keys()))
        industry = random.choice(list(CUSTOMER_PROFILES["industries"].keys()))
        company_size = random.choice(list(CUSTOMER_PROFILES["company_size"].keys()))
        
        # Create customer agent with Azure client
        self.customer_agent = CustomerAgent(
            personality, tech_level, role, industry, company_size,
            azure_client=self.azure.get_client()
        )
        
        # Create observer
        self.observer = ObserverCoach()
        
        # Format initial query with product name
        initial_query = self.scenario["initial_query"].format(product_name=PRODUCT_INFO["name"])
        
        # Reset conversation history
        self.conversation_history = []
        
        return {
            "scenario": self.scenario["title"],
            "description": self.scenario["description"],
            "customer_profile": {
                "personality": personality,
                "tech_level": tech_level,
                "role": role,
                "industry": industry,
                "company_size": company_size
            },
            "initial_query": initial_query
        }
    
    def process_user_message(self, message: str) -> str:
        """Process user message and get customer response."""
        if not self.customer_agent:
            return "Error: No scenario has been set up. Please set up a scenario first."
        
        try:
            # Generate customer response
            customer_response = self.customer_agent.generate_response(message)
            
            # Add to conversation history
            self.conversation_history.append({
                "user": message,
                "customer": customer_response
            })
            
            # Update observer
            self.observer.add_interaction(message, customer_response)
            
            return customer_response
            
        except Exception as e:
            print_colored(f"\nError generating customer response: {str(e)}", "red")
            return "I apologize, but I encountered an error processing your message. Please try again."

    def get_product_info(self) -> Dict:
        """Return product information."""
        return PRODUCT_INFO

def main():
    """Main function to run the roleplay system."""
    system = RoleplaySystem()
    
    # Initialize Azure connection
    if not system.initialize():
        print_colored("\nFailed to initialize Azure OpenAI connection. Please check your configuration.", "red")
        sys.exit(1)
    
    # Set up initial scenario
    scenario_info = system.setup_scenario()
    print_scenario_info(scenario_info, PRODUCT_INFO)
    
    initial_query = scenario_info['initial_query']
    
    # Start conversation loop
    while True:
        # Get user input
        user_input = input("You: ").strip()
        
        # Check for commands
        if user_input.lower() in ['/quit', '/exit', '/q']:
            print_colored("\n=== FINAL SUMMARY ===", "yellow")
            print_colored(system.observer.get_summary(), "cyan")
            print_colored("\nExiting roleplay. Thanks for practicing!", "yellow")
            break
        
        if user_input.lower() in ['/new', '/reset']:
            scenario_info = system.setup_scenario()
            system.observer = ObserverCoach()  # Reset observer
            print_colored("\n\n", "reset")
            print_scenario_info(scenario_info, PRODUCT_INFO)
            continue
            
        if user_input.lower() in ['/help', '/?']:
            print_colored("\nCOMMANDS:", "cyan")
            print("/new or /reset - Start a new scenario")
            print("/quit or /exit - Exit the roleplay")
            print("/help - Show this help message")
            print("/info - Show current scenario and product information")
            print("/list - Show all possible scenarios")
            print("/feedback - Show current conversation feedback")
            print("/phase - Show current conversation phase")
            continue
            
        if user_input.lower() == '/feedback':
            print_colored("\n=== CURRENT FEEDBACK ===", "yellow")
            print_colored(system.observer.get_summary(), "cyan")
            continue
            
        if user_input.lower() == '/phase':
            current_phase = system.observer.phase_manager.get_current_phase()
            print_colored(f"\nCurrent Conversation Phase: {current_phase.value}", "cyan")
            continue
            
        if user_input.lower() == '/info':
            print_colored("\nCURRENT SCENARIO:", "cyan")
            profile = scenario_info['customer_profile']
            print(f"Scenario: {scenario_info['scenario']}")
            print(f"Customer: {profile['personality']} {profile['role']} in {profile['industry']} (Tech: {profile['tech_level']}, Size: {profile['company_size']})")
            print(f"Product: {PRODUCT_INFO['name']}")
            continue
            
        if user_input.lower() == '/list':
            print_colored("\nAVAILABLE SCENARIOS:", "cyan")
            for i, scenario in enumerate(SCENARIOS, 1):
                print(f"{i}. {scenario['title']} - {scenario['description']}")
            continue
        
        # Process user message
        print_colored("Processing...", "yellow")
        customer_response = system.process_user_message(user_input)
        
        # Print customer response
        print_colored(f"Customer: {customer_response}", "magenta")
        print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_colored("\n\nRoleplay terminated. Thanks for practicing!", "yellow")
    except Exception as e:
        print_colored(f"\n\nAn error occurred: {e}", "red") 

# -------------------------------
# FastAPI backend (modo web/API)
# -------------------------------
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

# Modelo para recibir mensajes
class Message(BaseModel):
    text: str
    phase: str

# Instanciar el sistema (una vez)
roleplay_system = RoleplaySystem()
roleplay_system.initialize()
scenario_info = roleplay_system.setup_scenario()

@app.post("/api/chat")
def chat(msg: Message):
    response = roleplay_system.process_user_message(msg.text)
    return {
        "response": response,
        "phase": msg.phase,
        "feedback": roleplay_system.observer.get_summary()
    }

@app.get("/api/scenario")
def get_scenario():
    if not roleplay_system.scenario:
        roleplay_system.setup_scenario()
    
    return {
        "title": roleplay_system.scenario["title"],
        "description": roleplay_system.scenario["description"],
        "customer_profile": scenario_info["customer_profile"],
        "initial_query": scenario_info["initial_query"]
    }
@app.get("/api/feedback")
def get_feedback():
    """Devuelve el feedback de la conversación actual"""
    feedback = roleplay_system.observer.get_summary()
    return { "feedback": feedback }

@app.post("/api/reset")
def reset_scenario():
    """Reinicia el escenario y el observador."""
    scenario_info = roleplay_system.setup_scenario()
    roleplay_system.observer = ObserverCoach()  # Reinicia el observador
    return {
        "scenario": scenario_info["scenario"],
        "description": scenario_info["description"],
        "customer_profile": scenario_info["customer_profile"],
        "initial_query": scenario_info["initial_query"]
    }
# Alternativa para levantar como servidor
def run_api():
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


@app.get("/api/feedback/structured")
def get_structured_feedback():
    """Devuelve métricas, sugerencias e issues reales desde el evaluador."""
    result = roleplay_system.observer.analyze_conversation()

    return {
        "metrics": result.get("phase_scores", {}),
        "suggestions": result.get("suggestions", []),
        "issues": result.get("missed_opportunities", [])
    }