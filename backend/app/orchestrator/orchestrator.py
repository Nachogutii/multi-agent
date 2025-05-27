from app.agents.phase import PhaseAgent
from app.agents.customer import CustomerAgent
from app.services.supabase import SupabasePhasesService

class SimpleOrchestrator:
    def __init__(self, scenario_id=None):
        self.phase_agent = PhaseAgent(scenario_id=scenario_id)
        self.customer_agent = CustomerAgent(scenario_id=scenario_id)
        self.supabase_service = SupabasePhasesService(scenario_id=scenario_id)
        self.supabase_service.initialize()
        # Set initial phase
        self.current_phase = "welcome"
        # Dictionary to track conditions by phase
        self.conditions_by_phase = {}
        # Global history of all conditions
        self.global_conditions_history = []
        # Track red flags and optional aspects
        self.red_flags = []
        self.optional_aspects = []
        
    def process_message(self, user_message: str):
        # Get current accumulated conditions for this phase
        current_conditions = self.conditions_by_phase.get(self.current_phase, [])
        
        print(f"[INFO] Current phase: {self.current_phase}")
        print(f"[INFO] Accumulated conditions: {current_conditions}")
        print(f"[INFO] Global conditions: {self.global_conditions_history}")
        
        # Evaluate message with current conditions
        phase_result = self.phase_agent.evaluate(
            user_message, 
            self.current_phase,
            current_conditions
        )
        print(f"[INFO] Evaluation result: {phase_result}")

        # Handle conversation end due to red flags
        if phase_result.get("end"):
            terminal_response = self.customer_agent.generate_terminal_response()
            # Add red flags if any
            if phase_result.get("details"):
                self.red_flags.extend(phase_result.get("details"))
            return {
                "end": True,
                "phase": "abrupt_closure",
                "customer_response": terminal_response,
                "details": phase_result.get("details", []),
                "global_conditions": self.global_conditions_history,
                "red_flags": self.red_flags,
                "optional_aspects": self.optional_aspects,
                "conditions_for_next_phases": phase_result.get("conditions_for_next_phases", [])
            }
        
        # Get next phase and updated conditions
        next_phase = phase_result.get("phase", self.current_phase)
        updated_conditions = phase_result.get("observations", [])
        
        # Update global conditions history
        for condition in updated_conditions:
            if condition not in self.global_conditions_history:
                self.global_conditions_history.append(condition)
        
        # Update accumulated conditions for current phase
        if next_phase == self.current_phase:
            # Still in same phase, update conditions
            self.conditions_by_phase[self.current_phase] = updated_conditions
            print(f"[INFO] Updated conditions: {updated_conditions}")
        else:
            # Phase changed, initialize conditions for new phase
            self.conditions_by_phase[next_phase] = []
            print(f"[INFO] Phase changed: {self.current_phase} -> {next_phase}")
        
        # Update phase in customer agent
        self.customer_agent.set_phase(next_phase)
        self.current_phase = next_phase

        # Generate customer response
        customer_response = self.customer_agent.generate_response(user_message)

        return {
            "phase": self.current_phase,
            "customer_response": customer_response,
            "phase_observations": updated_conditions,
            "accumulated_conditions": self.conditions_by_phase.get(self.current_phase, []),
            "global_conditions": self.global_conditions_history,
            "red_flags": self.red_flags,
            "optional_aspects": self.optional_aspects,
            "conditions_for_next_phases": phase_result.get("conditions_for_next_phases", [])
        }

# Example usage
if __name__ == "__main__":
    orchestrator = SimpleOrchestrator()
    while True:
        user_message = input("Microsoft Rep: ")
        result = orchestrator.process_message(user_message)
        print(f"\n[Phase: {result['phase']}] Customer: {result['customer_response']}\n")
        print(f"Phase conditions: {result.get('accumulated_conditions', [])}")
        print(f"Global conditions: {result.get('global_conditions', [])}")
        if result.get('end') or result['phase'] in ["abrupt_closure", "polite_closure"]:
            print("Conversation ended by customer.")
            break