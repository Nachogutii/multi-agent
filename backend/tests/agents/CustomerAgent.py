import re
import os
from openai import AzureOpenAI

class CustomerAgent:
    def __init__(self, azure_client: AzureOpenAI):
        self.profile = None
        self.client = azure_client
        self.deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
        self.conversation_history = []

    def set_profile(self, profile):
        self.profile = profile

    def generate_reply(self, user_input, phase, emotion):
        if not self.profile:
            raise ValueError("Customer profile has not been set.")

        prompt = self._build_prompt(user_input, phase, emotion)

        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "Please generate a realistic customer response based on my previous message."}
                ],
                max_tokens=800,
                temperature=0.5,
            )

            customer_response = response.choices[0].message.content
            customer_response = re.sub(r'^.*?:', '', customer_response).strip()
            customer_response = re.sub(r'^"', '', customer_response).strip()
            customer_response = re.sub(r'"$', '', customer_response).strip()

            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append({"role": "assistant", "content": customer_response})

            return customer_response

        except Exception as e:
            print(f"Error generating customer response: {e}")
            return "Sorry, I'm having trouble connecting right now. Can we try again in a moment?"

    def _build_prompt(self, user_message: str, current_phase: str, emotion: str) -> str:
        prompt = f"""
You are roleplaying as a Microsoft 365 customer.

# CUSTOMER CONTEXT
{self.general_context}

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
3. Reflect emotional tone: {emotion}.
4. Do not mention you're an AI. Do not break character.
"""
        return prompt
