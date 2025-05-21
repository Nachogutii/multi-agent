from backend.app.agents.phase import PhaseAgent
from backend.app.agents.customer import CustomerAgent
from backend.app.services.supabase import SupabasePhasesService

class SimpleOrchestrator:
    def __init__(self):
        self.phase_agent = PhaseAgent()
        self.customer_agent = CustomerAgent()
        self.supabase_service = SupabasePhasesService()
        self.supabase_service.initialize()
        # Set initial phase
        self.current_phase = "welcome"
        # Dictionary to track conditions by phase
        self.conditions_by_phase = {}
        
    def process_message(self, user_message: str):
        # Get current accumulated conditions for this phase
        current_conditions = self.conditions_by_phase.get(self.current_phase, [])
        
        # Get phase data from database
        phase_data = self.supabase_service.get_phase_by_name(self.current_phase)
        if phase_data and "id" in phase_data:
            # Get conditions from success phases
            success_conditions = self.supabase_service.get_success_phase_conditions(self.current_phase)
            
            # Add success phase conditions to current conditions if they don't already exist
            for condition in success_conditions:
                if condition not in current_conditions:
                    current_conditions.append(condition)
        
        print(f"[DEBUG] Current phase: {self.current_phase}")
        print(f"[DEBUG] Accumulated conditions: {current_conditions}")
        
        # Evaluate message with current conditions
        phase_result = self.phase_agent.evaluate(
            user_message, 
            self.current_phase,
            current_conditions
        )
        print(f"[DEBUG] PhaseAgent result: {phase_result}")

        # Handle conversation end
        if phase_result.get("end"):
            return {
                "phase": "abrupt_closure",
                "customer_response": self.customer_agent.generate_terminal_response(),
                "phase_observations": phase_result.get("observations", [])
            }
        
        # Get next phase and updated conditions
        next_phase = phase_result.get("phase", self.current_phase)
        updated_conditions = phase_result.get("observations", [])
        
        # Update accumulated conditions for current phase
        if next_phase == self.current_phase:
            # Still in same phase, update conditions
            self.conditions_by_phase[self.current_phase] = updated_conditions
            print(f"[DEBUG] Updated conditions for phase '{self.current_phase}': {updated_conditions}")
        else:
            # Phase changed, initialize conditions for new phase from database
            next_success_conditions = self.supabase_service.get_success_phase_conditions(next_phase)
            self.conditions_by_phase[next_phase] = next_success_conditions
            print(f"[DEBUG] Phase changed from '{self.current_phase}' to '{next_phase}'")
            print(f"[DEBUG] Initial conditions for new phase from success phases: {next_success_conditions}")
        
        # Update phase in customer agent
        self.customer_agent.set_phase(next_phase)
        self.current_phase = next_phase

        # Generate customer response
        customer_response = self.customer_agent.generate_response(user_message)

        return {
            "phase": self.current_phase,
            "customer_response": customer_response,
            "phase_observations": updated_conditions,
            "accumulated_conditions": self.conditions_by_phase.get(self.current_phase, [])
        }

# Example usage
if __name__ == "__main__":
    orchestrator = SimpleOrchestrator()
    while True:
        user_message = input("Microsoft Rep: ")
        result = orchestrator.process_message(user_message)
        print(f"\n[Phase: {result['phase']}] Customer: {result['customer_response']}\n")
        print(f"Accumulated conditions: {result['accumulated_conditions']}")
        if result['phase'] in ["abrupt_closure", "polite_closure"]:
            print("Conversation ended by customer.")
            break