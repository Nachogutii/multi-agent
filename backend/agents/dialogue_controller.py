class DialogueController:
    """Controls and monitors the customer dialogue to ensure it remains realistic."""
    
    def __init__(self, customer_agent: CustomerAgent):
        self.customer_agent = customer_agent
        self.question_control = customer_agent.question_control
        self.client = customer_agent.client
        self.deployment = customer_agent.deployment
    
    def process_customer_response(self, response: str) -> str:
        """Processes and potentially modifies customer responses to ensure realism."""
        # Check for closing remarks
        if self.question_control.is_closing_remark(response):
            return self.question_control.generate_closing_remark(self.customer_agent.personality, self.customer_agent.scenario["title"])
        
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
            result = self.client.chat.completions.create(
                model=self.deployment,
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
            result = self.client.chat.completions.create(
                model=self.deployment,
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
        self.observer = None
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
        
        # Create observer with Azure client
        self.observer = ObserverCoach(
            azure_client=self.customer_agent.client,
            deployment=self.customer_agent.deployment
        )
        
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
        
        # Check if current question needs verification
        if self.customer_agent.question_control.current_question:
            is_satisfactory, feedback = self.customer_agent.question_control.verify_answer(message)
            if not is_satisfactory:
                return feedback
        
        # Generate customer response
        raw_response = self.customer_agent.generate_response(message)
        
        # Process response through dialogue controller
        final_response = self.dialogue_controller.process_customer_response(raw_response)
        
        # Add to conversation history
        self.conversation_history.append({
            "user": message,
            "customer": final_response
        })
        
        # Update observer
        self.observer.add_interaction(message, final_response)
        
        return final_response

    def get_product_info(self) -> Dict:
        """Return product information."""
        return PRODUCT_INFO
