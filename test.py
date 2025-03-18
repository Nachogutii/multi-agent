import os
import random
import json
import time
import sys
import re
from typing import Dict, List, Optional, Tuple
import requests
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Check if Azure configuration is set
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY = os.environ.get("AZURE_OPENAI_KEY") 
AZURE_OPENAI_DEPLOYMENT = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4")

if not AZURE_OPENAI_ENDPOINT or not AZURE_OPENAI_KEY:
    print("Please set your Azure OpenAI environment variables:")
    print("export AZURE_OPENAI_ENDPOINT='your-endpoint'")
    print("export AZURE_OPENAI_KEY='your-key'")
    print("export AZURE_OPENAI_DEPLOYMENT='your-deployment-name'")
    sys.exit(1)

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key=AZURE_OPENAI_KEY,
    api_version="2024-10-21",
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

# Define Microsoft 365 customer profiles
CUSTOMER_PROFILES = {
    "personalities": {
        "impatient": {
            "description": "Gets frustrated easily, wants quick solutions, uses short sentences",
            "traits": ["interrupts frequently", "uses phrases like 'just get to the point'", 
                      "shows time pressure", "may use exclamation marks"]
        },
        "curious": {
            "description": "Asks many questions, wants to understand how things work",
            "traits": ["asks follow-up questions", "shows interest in details", 
                      "uses phrases like 'how does that work?'", "explores options"]
        },
        "resistant": {
            "description": "Skeptical about new solutions, prefers familiar approaches",
            "traits": ["expresses doubt", "mentions previous solutions", 
                      "uses phrases like 'I'm not sure about this'", "needs convincing"]
        },
        "budget-conscious": {
            "description": "Primarily concerned with costs and ROI",
            "traits": ["asks about pricing frequently", "mentions budget constraints", 
                      "compares with existing solutions", "focuses on business value"]
        },
        "security-focused": {
            "description": "Prioritizes data security and compliance",
            "traits": ["asks about security features", "mentions compliance requirements", 
                      "concerned about data access", "asks about certifications"]
        }
    },
    "tech_levels": {
        "beginner": {
            "description": "Limited technical knowledge, needs simple explanations",
            "traits": ["asks basic questions", "may misuse technical terms", 
                      "prefers step-by-step guidance", "gets confused by jargon"]
        },
        "intermediate": {
            "description": "Understands core concepts but may struggle with advanced topics",
            "traits": ["familiar with common terms", "can follow technical explanations", 
                      "occasionally needs clarification", "some hands-on experience"]
        },
        "advanced": {
            "description": "High technical proficiency, understands complex concepts",
            "traits": ["uses technical terminology correctly", "asks sophisticated questions", 
                      "refers to technical documentation", "has extensive hands-on experience"]
        }
    },
    "roles": {
        "IT Admin": {
            "description": "Responsible for implementation, security, and maintenance",
            "traits": ["concerned with tenant management", "interested in security controls", 
                      "thinks about deployment", "wants technical specifications"]
        },
        "Business Manager": {
            "description": "Focuses on business impact, ROI, and team productivity",
            "traits": ["concerned with costs", "interested in productivity gains", 
                      "thinks about user adoption", "less interested in technical details"]
        },
        "Knowledge Worker": {
            "description": "End user focused on productivity and task completion",
            "traits": ["interested in ease of use", "concerned with daily workflows", 
                      "thinks about time savings", "wants practical examples"]
        },
        "Developer": {
            "description": "Focuses on extensibility, APIs, and integration",
            "traits": ["interested in API capabilities", "concerned with customization", 
                      "thinks about integration with existing systems", "detail-oriented"]
        },
        "Compliance Officer": {
            "description": "Focuses on data governance, security, and regulatory compliance",
            "traits": ["concerned with data protection", "interested in audit trails", 
                      "thinks about regulatory requirements", "questions data handling"]
        }
    },
    "industries": {
        "Healthcare": {
            "concerns": ["HIPAA compliance", "patient data security", "workflow efficiency"],
            "terminology": ["patient records", "clinical workflows", "care coordination"]
        },
        "Financial Services": {
            "concerns": ["financial regulations", "data security", "client confidentiality"],
            "terminology": ["client portfolios", "compliance", "risk management"]
        },
        "Education": {
            "concerns": ["student privacy", "collaboration tools", "classroom integration"],
            "terminology": ["learning management", "student engagement", "educational outcomes"]
        },
        "Retail": {
            "concerns": ["customer data", "operational efficiency", "marketing insights"],
            "terminology": ["customer experience", "inventory management", "omnichannel"]
        },
        "Manufacturing": {
            "concerns": ["supply chain visibility", "operational efficiency", "knowledge sharing"],
            "terminology": ["production processes", "quality control", "supply chain"]
        }
    },
    "company_size": {
        "Small": {
            "description": "Under 50 employees",
            "traits": ["budget sensitive", "wears multiple hats", "quick decision making", "flexible adoption"]
        },
        "Medium": {
            "description": "50-500 employees",
            "traits": ["balanced approach", "departmental needs", "moderate approval process", "growing infrastructure"]
        },
        "Enterprise": {
            "description": "500+ employees",
            "traits": ["complex requirements", "formal procurement", "extensive testing", "global deployment needs"]
        }
    }
}

# Define Microsoft Copilot product information
PRODUCT_INFO = {
    "name": "Microsoft Copilot for Microsoft 365",
    "description": "An AI-powered productivity assistant that integrates across Microsoft 365 apps",
    "key_features": [
        "AI-powered writing assistance in Word, Outlook, and PowerPoint",
        "Data analysis and insights in Excel",
        "Meeting summaries and action items in Teams",
        "Intelligent search across all content",
        "Business Chat for cross-app productivity",
        "Natural language queries for data"
    ],
    "pricing": {
        "Copilot for Microsoft 365": {
            "price": "$30 per user/month",
            "requirements": "Requires Microsoft 365 E3/E5 or Business Standard/Premium subscription"
        },
        "Copilot Pro": {
            "price": "$20 per user/month",
            "features": "Enhanced AI capabilities for individual users"
        },
        "Copilot Studio": {
            "price": "Starting at $10 per user/month",
            "features": "Build and deploy custom copilots"
        }
    },
    "prerequisites": [
        "Microsoft 365 subscription",
        "Minimum of 300 seats for enterprise customers",
        "Azure Active Directory",
        "Proper licensing for all users"
    ],
    "common_issues": [
        "Deployment requirements and prerequisites",
        "Integration with existing workflows",
        "Data privacy and security concerns",
        "User adoption and training needs",
        "ROI and productivity measurement",
        "Licensing and pricing questions"
    ]
}

# Define scenario templates
SCENARIOS = [
    {
        "title": "Initial Inquiry",
        "description": "Customer is exploring Microsoft Copilot capabilities",
        "customer_context": "Heard about {product_name} and wants to understand how it could benefit their organization",
        "initial_query": "We're looking to improve our productivity and I've heard about Microsoft Copilot. Can you tell me more about what it can do for us?"
    },
    {
        "title": "Licensing and Pricing",
        "description": "Customer has questions about licensing requirements and pricing",
        "customer_context": "Considering {product_name} but needs to understand the cost structure",
        "initial_query": "I'm trying to figure out the licensing for Copilot. How does it work with our existing Microsoft 365 subscriptions?"
    },
    {
        "title": "Security and Compliance",
        "description": "Customer has concerns about data security and compliance",
        "customer_context": "Interested in {product_name} but worried about data privacy",
        "initial_query": "Before we consider implementing Copilot, I need to understand how it handles our sensitive data and whether it meets our compliance requirements."
    },
    {
        "title": "Implementation Planning",
        "description": "Customer needs guidance on implementation approach",
        "customer_context": "Approved {product_name} purchase and planning deployment",
        "initial_query": "We've decided to move forward with Copilot. What's the best approach to roll it out to our organization?"
    },
    {
        "title": "Use Case Exploration",
        "description": "Customer wants to understand specific use cases for their industry",
        "customer_context": "Evaluating {product_name} for specific department needs",
        "initial_query": "I'm wondering how other companies in our industry are using Copilot. Can you share some specific examples that might be relevant to us?"
    },
    {
        "title": "Technical Integration",
        "description": "Customer has questions about technical integration",
        "customer_context": "IT team evaluating {product_name} integration requirements",
        "initial_query": "We have a complex IT environment with custom applications. How does Copilot integrate with our existing systems and what do we need to prepare?"
    },
    {
        "title": "Training and Adoption",
        "description": "Customer needs guidance on user adoption strategy",
        "customer_context": "Concerned about user adoption of {product_name}",
        "initial_query": "What kind of training and change management do we need to implement to ensure our users actually get value from Copilot?"
    }
]

class CustomerAgent:
    """Agent that simulates a Microsoft 365 customer with specific traits."""
    
    def __init__(self, personality: str, tech_level: str, role: str, industry: str, company_size: str):
        self.personality = personality
        self.tech_level = tech_level
        self.role = role
        self.industry = industry
        self.company_size = company_size
        self.profile = self._create_profile()
        self.conversation_history = []
        
    def _create_profile(self) -> Dict:
        """Create a complete customer profile."""
        return {
            "personality": CUSTOMER_PROFILES["personalities"][self.personality],
            "tech_level": CUSTOMER_PROFILES["tech_levels"][self.tech_level],
            "role": CUSTOMER_PROFILES["roles"][self.role],
            "industry": CUSTOMER_PROFILES["industries"][self.industry],
            "company_size": CUSTOMER_PROFILES["company_size"][self.company_size]
        }
    
    def generate_response(self, user_message: str) -> str:
        """Generate a customer response based on the profile and conversation history."""
        # Update conversation history
        self.conversation_history.append({"role": "user", "content": user_message})
        
        # Build the prompt for customer response generation
        prompt = self._build_prompt(user_message)
        
        try:
            # Generate response using Azure OpenAI
            response = client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "Please generate a realistic customer response based on my previous message."}
                ],
                max_tokens=800,
                temperature=0.7,
            )
            
            customer_response = response.choices[0].message.content
            
            # Clean up the response
            customer_response = re.sub(r'^.*?:', '', customer_response).strip()
            customer_response = re.sub(r'^"', '', customer_response).strip()
            customer_response = re.sub(r'"$', '', customer_response).strip()
            
            # Update conversation history
            self.conversation_history.append({"role": "assistant", "content": customer_response})
            
            return customer_response
            
        except Exception as e:
            print(f"Error generating customer response: {e}")
            return "Sorry, I'm having trouble connecting right now. Can we try again in a moment?"
    
    def _build_prompt(self, user_message: str) -> str:
        """Build a detailed prompt for the customer agent."""
        product_name = PRODUCT_INFO["name"]
        
        prompt = f"""
You are roleplaying as a customer interested in {product_name}.

# YOUR CUSTOMER PROFILE:
- Personality: {self.personality} - {self.profile['personality']['description']}
- Technical knowledge: {self.tech_level} - {self.profile['tech_level']['description']}
- Role: {self.role} - {self.profile['role']['description']}
- Industry: {self.industry} with concerns about {', '.join(self.profile['industry']['concerns'])}
- Company Size: {self.company_size} - {self.profile['company_size']['description']}

# PERSONALITY TRAITS (reflect these in your responses):
{', '.join(self.profile['personality']['traits'])}

# TECHNICAL KNOWLEDGE TRAITS (reflect these in your responses):
{', '.join(self.profile['tech_level']['traits'])}

# ROLE-BASED CONCERNS (reflect these in your responses):
{', '.join(self.profile['role']['traits'])}

# COMPANY SIZE TRAITS (reflect these in your responses):
{', '.join(self.profile['company_size']['traits'])}

# PREVIOUS CONVERSATION:
"""
        # Add conversation history to prompt
        for message in self.conversation_history[-4:]:  # Include last 4 messages only to save context
            role = "Microsoft Representative" if message["role"] == "user" else "You (Customer)"
            prompt += f"{role}: {message['content']}\n\n"
        
        prompt += f"""
# LATEST MESSAGE FROM MICROSOFT REPRESENTATIVE:
{user_message}

# INSTRUCTIONS:
1. Respond as this specific customer would, maintaining consistent personality, technical knowledge, and role-specific concerns
2. Keep responses concise (1-3 sentences) and conversational
3. Don't be overly polite or helpful - be realistic based on your profile
4. Occasionally express frustration, confusion, or satisfaction as appropriate
5. Use industry-specific terminology when relevant
6. Never break character or mention that you're an AI
7. Don't provide a prefix or explanation - just respond as the customer would

Generate a realistic, human-like response that this customer would give to the Microsoft representative.
"""
        return prompt

class DialogueController:
    """Controls and monitors the customer dialogue to ensure it remains realistic."""
    
    def __init__(self, customer_agent: CustomerAgent):
        self.customer_agent = customer_agent
    
    def process_customer_response(self, response: str) -> str:
        """Processes and potentially modifies customer responses to ensure realism."""
        # Check response length
        if len(response) > 500:
            return self._fix_verbose_response(response)
        
        # Check for unnatural formality or AI patterns
        if self._is_too_formal(response) or self._has_ai_patterns(response):
            return self._naturalize_response(response)
            
        return response
    
    def _fix_verbose_response(self, response: str) -> str:
        """Fixes overly verbose responses."""
        prompt = f"""
You need to make this customer response more concise and natural. The response is too long and detailed for a typical customer conversation.

Original response:
"{response}"

Make it:
1. Shorter (ideally 1-3 sentences)
2. More conversational and less formal
3. Focus on the main point or question
4. Maintain the original sentiment and personality
5. Sound like something a real person would type in a chat

Return only the revised response with no explanation.
"""
        try:
            result = client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "Please revise this customer response to be more concise and natural."}
                ],
                max_tokens=300,
                temperature=0.4,
            )
            
            revised = result.choices[0].message.content
            revised = re.sub(r'^"', '', revised).strip()
            revised = re.sub(r'"$', '', revised).strip()
            
            return revised
        except Exception as e:
            print(f"Error fixing verbose response: {e}")
            # Fallback to simple truncation if API call fails
            sentences = response.split('. ')
            if len(sentences) > 3:
                return '. '.join(sentences[:3]) + '.'
            return response
    
    def _is_too_formal(self, response: str) -> bool:
        """Checks if a response is unnaturally formal."""
        formal_indicators = [
            "I would like to inquire",
            "I am writing to",
            "I hereby",
            "thus",
            "furthermore",
            "nevertheless",
            "I am pleased to inform you",
            "per our conversation",
            "kindly assist"
        ]
        
        return any(indicator in response.lower() for indicator in formal_indicators)
    
    def _has_ai_patterns(self, response: str) -> bool:
        """Checks for common AI response patterns."""
        ai_patterns = [
            "As an AI",
            "I'm happy to help",
            "I don't have personal",
            "I don't have access to",
            "As requested",
            "I'd be happy to assist",
            "Thank you for providing",
            "I appreciate your patience"
        ]
        
        return any(pattern in response for pattern in ai_patterns)
    
    def _naturalize_response(self, response: str) -> str:
        """Makes an unnatural response sound more human."""
        personality = self.customer_agent.personality
        tech_level = self.customer_agent.tech_level
        
        prompt = f"""
This customer response sounds too formal or AI-like. Rewrite it to sound like a real {personality} customer with {tech_level} technical knowledge.

Original response:
"{response}"

Make it:
1. More conversational and casual
2. Use contractions (don't, can't, I'm)
3. Add mild typographical inconsistencies if appropriate
4. Remove overly formal phrases
5. Match the {personality} personality traits

Return only the revised response with no explanation.
"""
        try:
            result = client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "Please naturalize this customer response."}
                ],
                max_tokens=300,
                temperature=0.7,
            )
            
            revised = result.choices[0].message.content
            revised = re.sub(r'^"', '', revised).strip()
            revised = re.sub(r'"$', '', revised).strip()
            
            return revised
        except Exception as e:
            print(f"Error naturalizing response: {e}")
            return response

class RoleplaySystem:
    """Main system that manages the roleplay scenario."""
    
    def __init__(self):
        self.scenario = None
        self.customer_agent = None
        self.dialogue_controller = None
        self.conversation_history = []
    
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
        
        # Create customer agent
        self.customer_agent = CustomerAgent(personality, tech_level, role, industry, company_size)
        
        # Create dialogue controller
        self.dialogue_controller = DialogueController(self.customer_agent)
        
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
        
        # Generate customer response
        raw_response = self.customer_agent.generate_response(message)
        
        # Process response through dialogue controller
        final_response = self.dialogue_controller.process_customer_response(raw_response)
        
        # Add to conversation history
        self.conversation_history.append({
            "user": message,
            "customer": final_response
        })
        
        return final_response

    def get_product_info(self) -> Dict:
        """Return product information."""
        return PRODUCT_INFO

class ObserverCoach:
    """Analyzes user interaction with the customer and provides feedback."""
    
    def __init__(self):
        self.conversation_history = []
        self.score = 0
        self.max_score = 100
        self.feedback_points = []
        
    def add_interaction(self, user_message: str, customer_response: str):
        """Adds an interaction to the conversation history."""
        self.conversation_history.append({
            "user": user_message,
            "customer": customer_response,
            "timestamp": time.time()
        })
    
    def analyze_conversation(self) -> Dict:
        """Analyzes the conversation and provides feedback."""
        if not self.conversation_history:
            return {
                "score": 0,
                "feedback": ["No interactions to analyze."],
                "suggestions": ["Start a conversation to receive feedback."]
            }
        
        feedback = []
        suggestions = []
        score = 0
        
        # Analyze each interaction
        for interaction in self.conversation_history:
            # Analyze clarity and professionalism
            if self._is_clear_and_professional(interaction["user"]):
                score += 5
            else:
                feedback.append("Consider being clearer and more professional in your responses.")
                suggestions.append("Use more formal and structured language.")
            
            # Analyze empathy
            if self._shows_empathy(interaction["user"]):
                score += 5
            else:
                feedback.append("You could show more empathy with customer concerns.")
                suggestions.append("Acknowledge customer concerns before offering solutions.")
            
            # Analyze product knowledge
            if self._demonstrates_product_knowledge(interaction["user"]):
                score += 5
            else:
                feedback.append("Consider including more product details.")
                suggestions.append("Mention specific product features relevant to the context.")
            
            # Analyze problem-solving
            if self._addresses_customer_concerns(interaction["user"]):
                score += 5
            else:
                feedback.append("Make sure to address customer concerns directly.")
                suggestions.append("Respond specifically to questions and concerns raised.")
        
        # Adjust score to not exceed maximum
        score = min(score, self.max_score)
        
        return {
            "score": score,
            "feedback": list(set(feedback)),  # Remove duplicates
            "suggestions": list(set(suggestions))  # Remove duplicates
        }
    
    def _is_clear_and_professional(self, message: str) -> bool:
        """Checks if the message is clear and professional."""
        return len(message.split()) > 5 and not any(word in message.lower() for word in ["uh", "um", "like", "you know"])
    
    def _shows_empathy(self, message: str) -> bool:
        """Checks if the message shows empathy."""
        empathy_indicators = ["understand", "comprehend", "recognize", "appreciate", "value", "glad", "sorry", "feel"]
        return any(indicator in message.lower() for indicator in empathy_indicators)
    
    def _demonstrates_product_knowledge(self, message: str) -> bool:
        """Checks if the message demonstrates product knowledge."""
        product_terms = ["copilot", "microsoft 365", "productivity", "features", "capabilities", "integration", "functionality"]
        return any(term in message.lower() for term in product_terms)
    
    def _addresses_customer_concerns(self, message: str) -> bool:
        """Checks if the message addresses customer concerns."""
        return len(message.split()) > 10 and "?" in message
    
    def get_summary(self) -> str:
        """Generates a summary of the conversation and feedback."""
        analysis = self.analyze_conversation()
        
        summary = "\n=== CONVERSATION SUMMARY ===\n"
        summary += f"Total Score: {analysis['score']}/{self.max_score}\n\n"
        
        if analysis['feedback']:
            summary += "Areas for Improvement:\n"
            for point in analysis['feedback']:
                summary += f"- {point}\n"
            summary += "\n"
        
        if analysis['suggestions']:
            summary += "Suggestions:\n"
            for suggestion in analysis['suggestions']:
                summary += f"- {suggestion}\n"
        
        return summary

def print_colored(text, color=None):
    """Print text with ANSI color codes."""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m"
    }
    
    if color and color in colors:
        print(f"{colors[color]}{text}{colors['reset']}")
    else:
        print(text)

def print_banner(text):
    """Print a banner with the given text."""
    border = "=" * (len(text) + 4)
    print_colored(border, "cyan")
    print_colored(f"| {text} |", "cyan")
    print_colored(border, "cyan")

def print_scenario_info(scenario_info):
    """Print information about the current scenario."""
    print_banner("MICROSOFT COPILOT PLG CUSTOMER SERVICE ROLEPLAY")
    print_colored("\nSCENARIO:", "yellow")
    print(f"{scenario_info['scenario']} - {scenario_info['description']}")
    
    print_colored("\nCUSTOMER PROFILE:", "yellow")
    profile = scenario_info['customer_profile']
    print(f"Personality: {profile['personality']}")
    print(f"Technical Level: {profile['tech_level']}")
    print(f"Role: {profile['role']}")
    print(f"Industry: {profile['industry']}")
    print(f"Company Size: {profile['company_size']}")
    
    print_colored("\nPRODUCT:", "yellow")
    print(f"{PRODUCT_INFO['name']} - {PRODUCT_INFO['description']}")
    print("\nKey Features:")
    for feature in PRODUCT_INFO['key_features'][:3]:  # Show just 3 features
        print(f"- {feature}")
    
    print_colored("\nCONVERSATION STARTS:", "green")
    print_colored(f"Customer: {scenario_info['initial_query']}", "magenta")
    print()

def main():
    """Main function to run the roleplay system."""
    system = RoleplaySystem()
    observer = ObserverCoach()  # Create observer instance
    
    # Set up initial scenario
    scenario_info = system.setup_scenario()
    print_scenario_info(scenario_info)
    
    initial_query = scenario_info['initial_query']
    
    # Start conversation loop
    while True:
        # Get user input
        user_input = input("You: ").strip()
        
        # Check for commands
        if user_input.lower() in ['/quit', '/exit', '/q']:
            print_colored("\n=== FINAL SUMMARY ===", "yellow")
            print_colored(observer.get_summary(), "cyan")
            print_colored("\nExiting roleplay. Thanks for practicing!", "yellow")
            break
        
        if user_input.lower() in ['/new', '/reset']:
            scenario_info = system.setup_scenario()
            observer = ObserverCoach()  # Reset observer
            print_colored("\n\n", "reset")
            print_scenario_info(scenario_info)
            continue
            
        if user_input.lower() in ['/help', '/?']:
            print_colored("\nCOMMANDS:", "cyan")
            print("/new or /reset - Start a new scenario")
            print("/quit or /exit - Exit the roleplay")
            print("/help - Show this help message")
            print("/info - Show current scenario and product information")
            print("/list - Show all possible scenarios")
            print("/feedback - Show current conversation feedback")
            continue
            
        if user_input.lower() == '/feedback':
            print_colored("\n=== CURRENT FEEDBACK ===", "yellow")
            print_colored(observer.get_summary(), "cyan")
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
        
        # Registrar la interacción en el observador
        observer.add_interaction(user_input, customer_response)
        
        # Print customer response
        print_colored(f"Customer: {customer_response}", "magenta")
        print()

def test_azure_connection():
    """Función para probar la conexión con Azure OpenAI."""
    try:
        # Initialize Azure OpenAI client
        client = AzureOpenAI(
            api_key=AZURE_OPENAI_KEY,
            api_version="2024-10-21",
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )
        
        # Intentar hacer una llamada simple
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "Eres un asistente de prueba."},
                {"role": "user", "content": "Di 'hola'"}
            ],
            max_tokens=10
        )
        
        print("\n✅ Conexión exitosa con Azure OpenAI!")
        print(f"Endpoint: {AZURE_OPENAI_ENDPOINT}")
        print(f"Deployment: {AZURE_OPENAI_DEPLOYMENT}")
        print(f"Respuesta de prueba: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print("\n❌ Error al conectar con Azure OpenAI:")
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    if not AZURE_OPENAI_ENDPOINT or not AZURE_OPENAI_KEY:
        print("Por favor, configura las variables de entorno de Azure OpenAI:")
        print("export AZURE_OPENAI_ENDPOINT='tu-endpoint'")
        print("export AZURE_OPENAI_KEY='tu-key'")
        print("export AZURE_OPENAI_DEPLOYMENT='nombre-de-tu-deployment'")
        sys.exit(1)
    
    # Probar la conexión
    test_azure_connection()

    try:
        main()
    except KeyboardInterrupt:
        print_colored("\n\nRoleplay terminated. Thanks for practicing!", "yellow")
    except Exception as e:
        print_colored(f"\n\nAn error occurred: {e}", "red")