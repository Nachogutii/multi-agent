from .conversation_phase import ConversationPhaseManager
from .customer import CustomerAgent

class Orchestrator:
    def __init__(self, azure_client, deployment, shared_observer, scenario_context=None):
        self.azure_client = azure_client
        self.deployment = deployment
        # Reuse the evaluator's phase_manager to maintain synchronization
        self.evaluator_agent = shared_observer  # ✅ Use global instance
        self.phase_manager = self.evaluator_agent.phase_manager  # ⚠️ IMPORTANT: Use the same instance
        self.scenario_context = scenario_context
        
        print("⚠️ ORCHESTRATOR: Using the same phase_manager as the evaluator")
        
        # Usar el mismo phase_config que el evaluator y pasarle el contexto del escenario
        self.customer_agent = CustomerAgent(
            azure_client=azure_client,
            deployment=deployment,
            scenario_context=scenario_context,  # Pasar el contexto del escenario
            phase_config=self.phase_manager.config  # Pasar la configuración compartida
        )

    def process_user_input(self, user_input):
        print(f"Orchestrator received input: {user_input}")

        # First check if we are in a terminal phase
        current_phase = self.phase_manager.get_current_phase()
        print(f"🔄 Current phase before processing: {current_phase}")
        
        # If we are in "Conversation End", ignore user input and generate closing response
        if current_phase == "Conversation End":
            print("⚠️ TERMINAL PHASE DETECTED: 'Conversation End' - IGNORING USER INPUT")
            print("🛑 Generating definitive closing message (CONVERSATION ENDED)")
            
            # Get specific prompt for terminal phase
            system_prompt = self.phase_manager.get_system_prompt()
            self.customer_agent.set_system_prompt(system_prompt)
            
            # Generate closing response using specific prompt for "Conversation End"
            customer_response = self.customer_agent.generate_terminal_response()
            print(f"🛑 Terminal response generated: '{customer_response}'")
            
            # Save the interaction
            self.evaluator_agent.add_interaction(user_input, customer_response)
            
            # Save in context
            self.phase_manager.add_message(user_input, is_agent=True)
            self.phase_manager.add_message(customer_response, is_agent=False)
            
            return customer_response
        
        # Pre-check for red flags to immediately enter terminal phase if needed
        # This prevents generating a regular response when profanity is detected
        contains_profanity = any(word in user_input.lower() for word in ["fuck", "shit", "ass", "bitch", "damn"])
        if contains_profanity:
            print("⚠️ PROFANITY DETECTED IN USER INPUT - IMMEDIATELY ENTERING TERMINAL PHASE")
            # Force phase transition to Conversation End
            self.phase_manager._record_phase_transition("Conversation End")
            
            # Generate terminal response immediately
            customer_response = self.customer_agent.generate_terminal_response()
            print(f"🛑 Terminal response generated: '{customer_response}'")
            
            # Save the interaction
            self.evaluator_agent.add_interaction(user_input, customer_response)
            
            # Save in context
            self.phase_manager.add_message(user_input, is_agent=True)
            self.phase_manager.add_message(customer_response, is_agent=False)
            
            return customer_response
        
        # Normal flow for non-terminal phases
        # Get updated system prompt for current phase
        system_prompt = self.phase_manager.get_system_prompt()
        self.customer_agent.set_system_prompt(system_prompt)

        # Generate customer response
        customer_response = self.customer_agent.generate_response(user_input)

        # Save the interaction globally
        self.evaluator_agent.add_interaction(user_input, customer_response)

        # Save in context
        self.phase_manager.add_message(user_input, is_agent=True)
        self.phase_manager.add_message(customer_response, is_agent=False)
        
        # Check if after this interaction we've moved to a terminal phase
        updated_phase = self.phase_manager.get_current_phase()
        print(f"🔄 Current phase after processing: {updated_phase}")
        if updated_phase == "Conversation End" and current_phase != "Conversation End":
            print("⚠️ TRANSITION TO TERMINAL PHASE 'Conversation End' DETECTED")
            print("⚠️ Next interaction will ONLY generate closing responses")
            
        return customer_response