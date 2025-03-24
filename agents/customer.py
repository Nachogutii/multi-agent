import re
import time
import os
from typing import Dict, List
from openai import AzureOpenAI
from profiles import CUSTOMER_PROFILES, PRODUCT_INFO
from agents.conversation_phase import ConversationPhaseManager, ConversationPhase

class CustomerAgent:
    """Agent that simulates a Microsoft 365 customer with specific traits."""
    
    def __init__(self, personality: str, tech_level: str, role: str, industry: str, company_size: str, azure_client: AzureOpenAI):
        self.personality = personality
        self.tech_level = tech_level
        self.role = role
        self.industry = industry
        self.company_size = company_size
        self.profile = self._create_profile()
        self.conversation_history = []
        self.phase_manager = ConversationPhaseManager(
            azure_client=azure_client,
            deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
        )
        self.client = azure_client
        self.deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
        
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
        # Analyze conversation phase
        current_phase = self.phase_manager.analyze_message(user_message)
        
        # Check for closing phase
        if current_phase == ConversationPhase.CLOSING:
            return self._generate_closing_remark()
        
        # Update conversation history
        self.conversation_history.append({"role": "user", "content": user_message})
        
        # Build the prompt for customer response generation
        prompt = self._build_prompt(user_message, current_phase)
        
        try:
            # Generate response using Azure OpenAI
            response = self.client.chat.completions.create(
                model=self.deployment,  # Use the deployment name from environment
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "Please generate a realistic customer response based on my previous message."}
                ],
                max_tokens=800,
                temperature=0.5,
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
    
    def _generate_closing_remark(self) -> str:
        """Generates an appropriate closing remark based on personality and conversation context."""
        current_phase = self.phase_manager.get_current_phase()
        phase_history = self.phase_manager.get_phase_history()
        
        # Base closing remarks by personality
        closing_remarks = {
            "Friendly": "Thanks so much for your help today! I really appreciate it.",
            "Busy": "Alright, thanks for the info. Got to run!",
            "Skeptical": "I'll think about what you've said and get back to you if I have more questions.",
            "Direct": "That's all I needed to know. Thanks.",
            "Budget-conscious": "Thanks for the detailed information. I'll review the pricing and get back to you.",
            "Security-focused": "Thank you for addressing my security concerns. I'll discuss this with our IT team."
        }
        
        # Get base remark based on personality
        base_remark = closing_remarks.get(self.personality, "Thank you for your time.")
        
        # Add context based on conversation phase and history
        if current_phase == ConversationPhase.DECISION_MAKING:
            return f"{base_remark} I'll discuss this with my team and let you know our decision."
        elif current_phase == ConversationPhase.FOLLOW_UP:
            return f"{base_remark} I'll be in touch if we need any clarification."
        elif current_phase == ConversationPhase.OBJECTION_HANDLING:
            return f"{base_remark} I'll review the information you provided about my concerns."
        elif current_phase == ConversationPhase.PRODUCT_EXPERIENCE:
            return f"{base_remark} I'll try out the demo and get back to you with my feedback."
        elif current_phase == ConversationPhase.VALUE_ALIGNMENT:
            return f"{base_remark} I'll review the ROI calculations and discuss with our finance team."
        else:
            return base_remark
    
    def _build_prompt(self, user_message: str, current_phase: ConversationPhase) -> str:
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

# CURRENT CONVERSATION PHASE:
{current_phase.value}

# PHASE-SPECIFIC GUIDELINES:
{self._get_phase_guidelines(current_phase)}

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
8. Consider the current conversation phase ({current_phase.value}) in your response
9. If the conversation naturally reaches a conclusion, provide an appropriate closing remark

Generate a realistic, human-like response that this customer would give to the Microsoft representative.
"""
        return prompt
    
    def _get_phase_guidelines(self, phase: ConversationPhase) -> str:
        """Returns specific guidelines for the current conversation phase."""
        guidelines = {
            ConversationPhase.DISCOVERY: """
- Show initial interest in the product
- Ask basic questions about capabilities
- Express curiosity about potential benefits
- Keep questions general and exploratory""",
            
            ConversationPhase.NEEDS_ANALYSIS: """
- Share specific challenges and pain points
- Discuss current workflow issues
- Express concerns about existing solutions
- Provide context about your role and responsibilities""",
            
            ConversationPhase.VALUE_ALIGNMENT: """
- Focus on ROI and business impact
- Discuss efficiency improvements
- Consider cost implications
- Evaluate potential benefits for your organization""",
            
            ConversationPhase.PRODUCT_EXPERIENCE: """
- Express interest in trying the product
- Ask about demo or trial options
- Share concerns about implementation
- Discuss technical requirements""",
            
            ConversationPhase.SOLUTION_PRESENTATION: """
- Evaluate proposed solutions
- Compare with alternatives
- Consider implementation timeline
- Discuss resource requirements""",
            
            ConversationPhase.OBJECTION_HANDLING: """
- Express specific concerns
- Question pricing or complexity
- Share security or compliance worries
- Discuss integration challenges""",
            
            ConversationPhase.DECISION_MAKING: """
- Show readiness to make a decision
- Discuss next steps
- Consider approval process
- Plan for implementation""",
            
            ConversationPhase.FOLLOW_UP: """
- Express appreciation for information
- Plan for next interaction
- Set expectations for follow-up
- Summarize key points discussed""",
            
            ConversationPhase.CLOSING: """
- Provide appropriate closing remarks
- Express gratitude
- Set expectations for next steps
- End conversation professionally"""
        }
        return guidelines.get(phase, "") 