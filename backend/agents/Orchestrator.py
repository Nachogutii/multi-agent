from agents.evaluator import ObserverCoach
from agents.conversation_phase import ConversationPhaseManager
from agents.customer import CustomerAgent

class Orchestrator:
    def __init__(self, azure_client, deployment, observer):
        self.azure_client = azure_client
        self.deployment = deployment
        self.evaluator_agent = observer
        self.phase_manager = ConversationPhaseManager()
        self.customer_agent = CustomerAgent(
            personality="open",
            tech_level="intermediate",
            role="it_manager",
            industry="technology",
            company_size="medium",
            azure_client=azure_client
        )

    def process_user_input(self, user_input):
        # Orchestrator recibe la entrada del usuario
        print(f"Orchestrator received input: {user_input}")

        # Enviar mensaje al Evaluator Agent y obtener el estado del cliente
        customer_state = self.evaluator_agent.update_customer_state(user_input, "")

        # Evaluator Agent actualiza el estado del cliente
        print(f"Updated Customer State: {customer_state}")

        # Orchestrator envía el nuevo estado del cliente al PhaseManager
        current_phase = self.phase_manager.decide_phase(customer_state)

        # PhaseManager decide si cambiar de fase o no
        print(f"Current Phase: {current_phase.value}")

        # Orchestrator indica al CustomerAgent que responda según la fase y el estado del cliente
        response = self.customer_agent.generate_response(user_input, current_phase=current_phase)


        # Orchestrator envía la respuesta de vuelta al usuario
        return response

# Ejemplo de uso
if __name__ == "__main__":
    # Crear instancia del cliente de Azure
    azure_client = None  # Reemplazar con la instancia real de AzureOpenAI

    orchestrator = Orchestrator(azure_client)
    user_input = "Hello, I am Miguel from Microsoft 365, I wanted to know how your Copilot Subscription is going."
    response = orchestrator.process_user_input(user_input)
    print(f"Response to User: {response}") 