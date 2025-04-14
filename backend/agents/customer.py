import re
from openai import AzureOpenAI
from agents.conversation_phase import ConversationPhaseManager
from pathlib import Path

class CustomerAgent:
    def __init__(self, azure_client: AzureOpenAI, deployment: str):
        self.client = azure_client
        self.deployment = deployment
        self.system_prompt = ""
        self.phase_manager = ConversationPhaseManager(azure_client, deployment)
        self.general_context = Path("scenario_context.md").read_text(encoding="utf-8")

    def generate_response(self, user_message: str) -> str:
        system_prompt = self.phase_manager.get_system_prompt()

        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500,
                temperature=0.6
            )

            customer_response = response.choices[0].message.content.strip()
            self.phase_manager.add_message(user_message, is_agent=True)
            self.phase_manager.add_message(customer_response, is_agent=False)
            return customer_response

        except Exception as e:
            print(f"Error generating customer response: {e}")
            return "I'm not sure how to respond to that right now."
    
    def set_system_prompt(self, prompt: str):
        self.system_prompt = prompt

