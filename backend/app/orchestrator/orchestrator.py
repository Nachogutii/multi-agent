from backend.app.agents.phase import PhaseAgent
from backend.app.agents.costumer import CustomerAgent

class SimpleOrchestrator:
    def __init__(self):
        self.phase_agent = PhaseAgent()
        self.customer_agent = CustomerAgent()
        # Set initial phase (you can change this to your preferred starting phase)
        self.current_phase = "welcome"

    def process_message(self, user_message: str):
        phase_result = self.phase_agent.evaluate(user_message, self.current_phase)
        print(f"[DEBUG] PhaseAgent result: {phase_result}")

        # SIEMPRE actualiza la fase con la que devuelve PhaseAgent
        next_phase = phase_result.get("phase", self.current_phase)
        self.customer_agent.set_phase(next_phase)
        self.current_phase = next_phase

        customer_response = self.customer_agent.generate_response(user_message)

        return {
            "phase": self.current_phase,
            "customer_response": customer_response,
            "phase_observations": phase_result.get("observations", [])
        }

# Example usage
if __name__ == "__main__":
    orchestrator = SimpleOrchestrator()
    while True:
        user_message = input("Microsoft Rep: ")
        result = orchestrator.process_message(user_message)
        print(f"\n[Phase: {result['phase']}] Customer: {result['customer_response']}\n")
        if result['phase'] in ["abrupt_closure", "polite_closure"]:
            print("Conversation ended by customer.")
            break