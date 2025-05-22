import random
from app.services.azure_openai import AzureOpenAIClient
from app.services.supabase import SupabasePhasesService

class CustomerAgent:
    def __init__(self, scenario_context=None):
        self.llm = AzureOpenAIClient()
        self.supabase = SupabasePhasesService()
        assert self.supabase.initialize(), "Could not initialize Supabase client"

        # Load scenario context or use default
        if scenario_context:
            self.general_context = scenario_context
            print(f"✅ Using scenario context from Supabase ({len(scenario_context)} characters)")
            preview = scenario_context[:200] + "..." if len(scenario_context) > 200 else scenario_context
            print(f"📄 CONTEXT PREVIEW:\n{preview}")
        else:
            self.general_context = """
            **B. Customer Profile:**
            - Customer is Rachel Sanchez, using Microsoft 365 and interested in Copilot.
            - She's a marketing professional looking to improve workflow efficiency.
            - Has some experience with Microsoft 365 but is curious about new Copilot features.
            """
            print("⚠️ No scenario context provided, using default profile.")
            print(f"📄 DEFAULT CONTEXT:\n{self.general_context}")

        self.profile = self._load_customer_profile()
        print(f"👤 PROFILE LOADED:\n{self.profile[:200]}..." if len(self.profile) > 200 else self.profile)
        self.conversation_history = []

        # Load phases from Supabase
        self.phases = {phase['name']: phase for phase in self.supabase.get_all_phases()}
        self.current_phase_name = list(self.phases.keys())[0] if self.phases else None

    def _load_customer_profile(self) -> str:
        profile_start = self.general_context.find("**B. Customer Profile:**")
        if profile_start == -1:
            return self.general_context.strip()
        profile_end = self.general_context.find("- **B. Channel of Communication:**")
        if profile_end == -1:
            return self.general_context[profile_start:].strip()
        return self.general_context[profile_start:profile_end].strip()

    def _build_prompt(self, user_message: str) -> str:
        current_phase = self.current_phase_name or "Unknown"
        prompt = f"""
        You are roleplaying as Rachel Sanchez, a Microsoft 365 customer. Stay fully in character.

        # CUSTOMER CONTEXT
        {self.profile}

        # CURRENT PHASE:
        {current_phase}

        # PAST CONVERSATION:
        """
        for message in self.conversation_history[-4:]:
            role = "Microsoft Representative" if message["role"] == "user" else "You (Customer)"
            prompt += f"{role}: {message['content']}\n\n"

        prompt += f"""
        # NEW MESSAGE FROM MICROSOFT REPRESENTATIVE:
        {user_message}

        # INSTRUCTIONS:
        1. Respond as this specific customer would, maintaining consistent personality and concerns
        2. Keep responses concise (1-3 sentences) and conversational
        3. Don't be overly polite or helpful - be realistic based on your profile
        4. Occasionally express frustration, confusion, or satisfaction as appropriate
        5. Use industry-specific terminology when relevant
        6. Never break character or mention that you're an AI
        7. Don't provide a prefix or explanation - just respond as the customer would
        8. Consider the current conversation phase ({current_phase}) in your response
        9. If the conversation naturally reaches a conclusion, provide an appropriate closing remark
        10. Pay attention to derailment triggers and recovery options for the current phase

        Generate a realistic, human-like response that this customer would give to the Microsoft representative.
        """
        return prompt

    def generate_response(self, user_message: str) -> str:
        # Get the system_prompt of the current phase
        phase = self.phases.get(self.current_phase_name)
        if not phase:
            print(f"⚠️ Phase '{self.current_phase_name}' not found. Using default system prompt.")
            system_prompt = "You are a helpful assistant that only responds as the customer, never as an AI."
        else:
            system_prompt = phase.get("system_prompt", "You are a helpful assistant that only responds as the customer, never as an AI.")
            print(f"[DEBUG] Using system_prompt for phase '{self.current_phase_name}':\n{system_prompt}\n")

        combined_prompt = self._build_prompt(user_message)
        try:
            response = self.llm.get_response(
                system_prompt=system_prompt,
                user_prompt=combined_prompt
            )
            customer_response = response.strip()
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": customer_response})
            return customer_response
        except Exception as e:
            print(f"Error generating customer response: {e}")
            return "I'm not sure how to respond to that right now."

    def set_phase(self, phase_name: str):
        if phase_name in self.phases:
            self.current_phase_name = phase_name
        else:
            print(f"Phase '{phase_name}' not found. Keeping current phase.")

    def generate_terminal_response(self) -> str:
        closing_phrases = [
            "This conversation has ended.",
            "I don't have time for this. This conversation is over.",
            "Do not contact me again about this.",
            "I'm hanging up now.",
            "This conversation is terminated.",
            "I have nothing more to say. Goodbye."
        ]
        return random.choice(closing_phrases)

# Example usage
if __name__ == "__main__":
    agent = CustomerAgent()
    print(agent.generate_response("Hello, how can I help you?"))