
from agents.evaluator import ObserverCoach
from agents.conversation_phase import ConversationPhaseManager
from agents.customer import CustomerAgent

class Orchestrator:
    def __init__(self, azure_client, deployment):
        self.azure_client = azure_client
        self.deployment = deployment
        self.phase_manager = ConversationPhaseManager(azure_client=azure_client, deployment=deployment)
        self.evaluator_agent = ObserverCoach(azure_client=azure_client, deployment=deployment)

        # CustomerAgent will receive system_prompt dynamically
        self.customer_agent = CustomerAgent(
            azure_client=azure_client,
            deployment=deployment
        )

    def process_user_input(self, user_input):
        print(f"Orchestrator received input: {user_input}")

        # Placeholder: empty response until we have customer response
        customer_response = ""

        # Evaluate the current interaction
        customer_state = self.evaluator_agent.update_customer_state(user_input, customer_response)

        # Decide and update phase if needed
        new_phase = self.phase_manager.analyze_message(user_input, customer_response)
        print(f"Current Phase: {new_phase}")

        # Get updated system prompt for the current phase
        system_prompt = self.phase_manager.get_system_prompt()
        self.customer_agent.set_system_prompt(system_prompt)

        # Generate response
        customer_response = self.customer_agent.generate_response(user_input)

        # Save the message and customer response to phase manager
        self.phase_manager.add_message(user_input, is_agent=True)
        self.phase_manager.add_message(customer_response, is_agent=False)

        return customer_response
