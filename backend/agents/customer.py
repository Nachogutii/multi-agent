import re
from openai import AzureOpenAI
from agents.conversation_phase import ConversationPhaseManager
from pathlib import Path

class CustomerAgent:
    def __init__(self, azure_client: AzureOpenAI, deployment: str):
        self.client = azure_client
        self.deployment = deployment
        self.general_context = Path("scenario_context.md").read_text(encoding="utf-8")
        self.profile = self._load_customer_profile()
        self.conversation_history = []
        self.phase_manager = ConversationPhaseManager(azure_client, deployment)

    def _load_customer_profile(self) -> str:
        # Extract the customer profile section from the scenario context
        profile_start = self.general_context.find("**B. Customer Profile:**")
        profile_end = self.general_context.find("- **B. Channel of Communication:**")
        return self.general_context[profile_start:profile_end].strip()

    def _build_prompt(self, user_message: str) -> str:
        current_phase = self.phase_manager.get_current_phase()
        prompt = f"""
        You are roleplaying as Rachel Sanchez, a Microsoft 365 customer.

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
        # NEW MESSAGE FROM MICROSOFT REP:
        {user_message}

        # INSTRUCTIONS:
        1. Respond as this specific customer would, based on role, intent, personality, and emotion.
        2. Be concise (1-3 sentences), natural, and phase-appropriate.
        3. Do not mention you're an AI. Do not break character.
        4. Don't be overly polite or helpful - be realistic based on your profile
        5. Don't provide a prefix or explanation - just respond as the customer would
        """
        return prompt

    def generate_response(self, user_message: str) -> str:
        # Build a detailed prompt
        combined_prompt = self._build_prompt(user_message)

        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": combined_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500,
                temperature=0.6
            )

            customer_response = response.choices[0].message.content.strip()
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": customer_response})
            return customer_response

        except Exception as e:
            print(f"Error generating customer response: {e}")
            return "I'm not sure how to respond to that right now."
    
    def set_system_prompt(self, prompt: str):
        self.system_prompt = prompt

