import re
from openai import AzureOpenAI
from .conversation_phase import ConversationPhaseManager
from pathlib import Path
import random
import os

class CustomerAgent:
    def __init__(self, azure_client: AzureOpenAI, deployment: str, scenario_context=None, phase_config=None):
        self.client = azure_client
        self.deployment = deployment
        
        # Usar el contexto de escenario si se proporciona, o cargar desde archivo
        if scenario_context:
            self.general_context = scenario_context
        else:
            # Verificar si el archivo existe antes de leerlo
            context_path = Path("scenario_context.md")
            if context_path.exists():
                self.general_context = context_path.read_text(encoding="utf-8")
            else:
                self.general_context = """
                **B. Customer Profile:**
                - Customer is Rachel Sanchez, using Microsoft 365 and interested in Copilot.
                - She's a marketing professional looking to improve workflow efficiency.
                - Has some experience with Microsoft 365 but is curious about new Copilot features.
                """
                print("⚠️ No se encontró el archivo scenario_context.md, usando perfil por defecto.")
        
        self.profile = self._load_customer_profile()
        self.conversation_history = []
        
        # Usar phase_config si se proporciona
        self.phase_manager = ConversationPhaseManager(azure_client, deployment, phase_config)

    def _load_customer_profile(self) -> str:
        # Extract the customer profile section from the scenario context
        profile_start = self.general_context.find("**B. Customer Profile:**")
        if profile_start == -1:  # Si no se encuentra, usar todo el contexto
            return self.general_context.strip()
            
        profile_end = self.general_context.find("- **B. Channel of Communication:**")
        if profile_end == -1:  # Si no se encuentra el final, usar hasta el final
            return self.general_context[profile_start:].strip()
            
        return self.general_context[profile_start:profile_end].strip()

    def _build_prompt(self, user_message: str) -> str:
        current_phase = self.phase_manager.get_current_phase()
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
        
    def generate_terminal_response(self) -> str:
        # For terminal phases, we need a fixed response pattern
        # Always return a definitive closing message in English
        closing_phrases = [
            "This conversation has ended.",
            "I don't have time for this. This conversation is over.",
            "Do not contact me again about this.",
            "I'm hanging up now.",
            "This conversation is terminated.",
            "I have nothing more to say. Goodbye."
        ]
        
        # Choose a random closing phrase to add variety
        return random.choice(closing_phrases)

