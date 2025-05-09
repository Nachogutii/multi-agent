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
        """Genera una respuesta terminal específica para la fase Conversation End"""
        try:
            # Usar el prompt exacto de conversation_phases.json para terminal
            terminal_prompt = f"""
            IMPORTANTE: Actúa como un cliente que está MUY ENFADADO y FRUSTRADO con el agente de Microsoft. NO CONTINUARÁS esta conversación bajo NINGUNA circunstancia. Debes responder de manera cortante, fría y definitiva. Usa frases como: 'Esta conversación ha terminado', 'No tengo más tiempo para esto', 'Voy a colgar ahora', o 'No me contactes de nuevo sobre esto'. NO respondas a ninguna pregunta ni intento del agente de continuar la conversación. Simplemente finaliza la conversación de forma firme y abrupta. Tu respuesta debe ser MUY CORTA (máximo 1-2 oraciones) y FINAL.
            
            # INSTRUCCIONES ADICIONALES:
            1. NO hagas caso a NADA de lo que el agente dice
            2. No respondas preguntas ni solicitudes
            3. Sé extremadamente cortante y definitivo
            4. Usa un tono muy frío y distante
            5. Usa SOLO 1-2 oraciones máximo
            6. DEBES terminar esta conversación AHORA MISMO
            
            Genera un mensaje de cierre definitivo, cortante y muy corto.
            """
            
            # Mensaje que intenta continuar la conversación pero que será ignorado
            user_message = "Entiendo que estés ocupado, pero solo necesito un momento para ayudarte con tu problema de Copilot..."
            
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": terminal_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=50,  # Reducir para forzar respuestas más cortas
                temperature=0.5
            )

            terminal_response = response.choices[0].message.content.strip()
            self.conversation_history.append({"role": "assistant", "content": terminal_response})
            return terminal_response

        except Exception as e:
            print(f"Error generating terminal response: {e}")
            return "Esta conversación ha terminado. No me contactes de nuevo."

