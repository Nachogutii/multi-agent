from agents.evaluator import ObserverCoach
from agents.conversation_phase import ConversationPhaseManager
from agents.customer import CustomerAgent

class Orchestrator:
    def __init__(self, azure_client, deployment):
        self.azure_client = azure_client
        self.deployment = deployment
        self.phase_manager = ConversationPhaseManager(azure_client=azure_client, deployment=deployment)
        self.evaluator_agent = ObserverCoach(azure_client=azure_client, deployment=deployment)

        self.customer_agent = CustomerAgent(
            azure_client=azure_client,
            deployment=deployment
        )

    def process_user_input(self, user_input):
        print(f"Orchestrator received input: {user_input}")

        # Prompt de sistema según fase actual
        system_prompt = self.phase_manager.get_system_prompt()
        self.customer_agent.set_system_prompt(system_prompt)

        # Generar respuesta
        customer_response = self.customer_agent.generate_response(user_input)

        # Restauramos: el evaluador se encarga de fase y análisis
        self.evaluator_agent.add_interaction(user_input, customer_response)

        # Guardar mensaje en el PhaseManager
        self.phase_manager.add_message(user_input, is_agent=True)
        self.phase_manager.add_message(customer_response, is_agent=False)

        return customer_response