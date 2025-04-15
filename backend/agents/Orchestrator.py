from agents.conversation_phase import ConversationPhaseManager
from agents.customer import CustomerAgent

class Orchestrator:
    def __init__(self, azure_client, deployment, shared_observer):
        self.azure_client = azure_client
        self.deployment = deployment
        self.phase_manager = ConversationPhaseManager(azure_client=azure_client, deployment=deployment)
        self.evaluator_agent = shared_observer  # ✅ Usa instancia global
        self.customer_agent = CustomerAgent(
            azure_client=azure_client,
            deployment=deployment
        )

    def process_user_input(self, user_input):
        print(f"Orchestrator received input: {user_input}")

        # Obtener prompt actualizado de sistema para la fase actual
        system_prompt = self.phase_manager.get_system_prompt()
        self.customer_agent.set_system_prompt(system_prompt)

        # Generar respuesta del cliente
        customer_response = self.customer_agent.generate_response(user_input)

        # Guardar la interacción globalmente
        self.evaluator_agent.add_interaction(user_input, customer_response)

        # Guardar en contexto
        self.phase_manager.add_message(user_input, is_agent=True)
        self.phase_manager.add_message(customer_response, is_agent=False)

        return customer_response