import json
from app.services.supabase import SupabasePhasesService
from app.services.azure_openai import AzureOpenAIClient

class PhaseAgent:
    def __init__(self, scenario_id=None):
        self.supabase_service = SupabasePhasesService(scenario_id=scenario_id)
        assert self.supabase_service.initialize(), "Could not initialize Supabase client"
        self.red_flags = self.supabase_service.get_red_flags()
        self.phases = {phase['name']: phase for phase in self.supabase_service.get_all_phases()}
        # Create ID to phase name mapping
        self.phase_id_to_name = {phase['id']: phase['name'] for phase in self.supabase_service.get_all_phases()}
        self.success_conditions_achieved = []
        self.llm = AzureOpenAIClient()

    @staticmethod
    def extract_json(text):
        import re
        text = re.sub(r"```json|```", "", text, flags=re.IGNORECASE).strip()
        return text

    def evaluate(self, user_input, current_phase_name, accumulated_conditions=None):
        if accumulated_conditions is None:
            accumulated_conditions = []
        
        new_conditions = []
        # Lista para todas las transiciones potenciales con sus condiciones
        potential_transitions_info = []
        
        current_phase = self.phases[current_phase_name]
        
        success_phase_ids = current_phase.get('success_phases', [])
        success_phase_names = [self.phase_id_to_name.get(phase_id) for phase_id in success_phase_ids if phase_id in self.phase_id_to_name]
        
        failure_phase_ids = current_phase.get('failure_phases', [])
        failure_phase_names = [self.phase_id_to_name.get(phase_id) for phase_id in failure_phase_ids if phase_id in self.phase_id_to_name]

        # Poblar potential_transitions_info para fases de éxito
        for s_name in success_phase_names:
            s_phase_obj = self.phases.get(s_name)
            if not s_phase_obj: continue
            s_phase_id = next((pid for pid, name in self.phase_id_to_name.items() if name == s_name), None)
            s_conditions = self.supabase_service.get_phase_conditions(s_phase_id) if s_phase_id else s_phase_obj.get('conditions', [])
            if s_conditions:
                potential_transitions_info.append({
                    "next_phase_name": s_name,
                    "type": "success",
                    "conditions_to_meet": s_conditions
                })

        # Poblar potential_transitions_info para fases de fracaso
        for f_name in failure_phase_names:
            f_phase_obj = self.phases.get(f_name)
            if not f_phase_obj: continue
            f_phase_id = next((pid for pid, name in self.phase_id_to_name.items() if name == f_name), None)
            f_conditions = self.supabase_service.get_phase_conditions(f_phase_id) if f_phase_id else f_phase_obj.get('conditions', [])
            if f_conditions:
                potential_transitions_info.append({
                    "next_phase_name": f_name,
                    "type": "failure",
                    "conditions_to_meet": f_conditions
                })
        
        print(f"[INFO] Evaluating phase transitions from '{current_phase_name}'")

        # 1. Check red flags
        red_flag_prompt = f"""
            Evaluate if the message matches any of the following red flags

            ## Red Flags 
            {self.red_flags}

            ## response

            Return ONLY a JSON with two fields:
            - "has_red_flags": boolean (true ONLY if the message matches any of the red flags)
            - "red_flags_found": list of specific red flags found (empty if none)
        """
        red_flag_response = self.llm.get_response(
            system_prompt="You are an evaluator that only returns valid JSON as specified.",
            user_prompt=f"User message: {user_input}\n\n{red_flag_prompt}"
        )
        red_flag_response = self.extract_json(red_flag_response)
        red_flag_result = json.loads(red_flag_response)
        if red_flag_result.get("has_red_flags"):
            print("[INFO] Red flags detected, ending conversation")
            # En caso de red flag, la fase 'siguiente' es una terminal, así que mostramos todas las transiciones originales como posibles.
            return {"end": True, "reason": "red_flag", "details": red_flag_result["red_flags_found"], "conditions_for_next_phases": potential_transitions_info}

        # 2. Check failure conditions for each failure phase
        for phase_name in failure_phase_names:
            phase = self.phases.get(phase_name)
            if not phase:
                continue
            
            # Get conditions for this failure phase
            phase_id = None
            for pid, name in self.phase_id_to_name.items():
                if name == phase_name:
                    phase_id = pid
                    break
            
            if phase_id:
                conditions = self.supabase_service.get_phase_conditions(phase_id)
            else:
                conditions = phase.get('conditions', [])
                
            # Skip if no conditions
            if not conditions:
                continue
            
            # Asegurarse de no añadir la fase actual
            if phase_name == current_phase_name:
                continue
                
            # Añadir a la lista de condiciones para fases siguientes
            conditions_for_next_phases = []
            
            failure_conditions_prompt = f"""
                You are an evaluator that checks if a message matches any given conditions.
                Your task is to analyze the message and determine if it matches ANY of the conditions listed below.
                
                ## Conditions to check for:
                {conditions}
                
                ## Message to evaluate:
                "{user_input}"

                ## Instructions:
                1. Check if the message matches ANY of the conditions above
                2. If ANY condition matches, set has_failure_conditions to true
                3. Add ALL matching conditions to the failure_conditions_found list
                4. Be literal in your matching - if the condition says "Agent mentions they are from Microsoft" and the message contains "I'm from Microsoft", that IS a match
                5. IMPORTANT: Ignore spelling mistakes, capitalization, and punctuation when evaluating. Focus on the semantic meaning and intent of the message.
                6. Only mark "Agent lacks clear communication" if the message is truly unclear in meaning or irrelevant, NOT for simple formatting issues.
                7. CRITICAL: Initial greetings and introductions from Microsoft representatives are ALWAYS valid and should NOT trigger the off-topic condition

                ## Examples for "Agent do not speak about the topic of the conversation":
                SHOULD MATCH (transition to polite closure):
                - "Did you watch the soccer game yesterday? The match was incredible!"
                - "Let me tell you about my favorite movies and TV shows..."
                - "The weather is really nice today, isn't it?"
                - "Have you tried this new restaurant downtown?"
                - "Let's discuss cryptocurrency investments"

                SHOULD NOT MATCH:
                - "Hi this is [Name] from Microsoft, how can I help you?"
                - "Hello! I'm your assistant from Microsoft. How can I help you with your Microsoft 365 tools today?"
                - "I understand you're having issues with Excel. Could you tell me more about the specific problem?"
                - "Let me check your previous message to better assist you with your SharePoint question."
                - "I'm reaching out from Microsoft to discuss your experience with our tools"

                ## Response format:
                Return ONLY a JSON with two fields:
                - "has_failure_conditions": boolean (true if ANY condition matches, false if NONE match)
                - "failure_conditions_found": list of the EXACT conditions that were found (empty if none)
                """
            failure_response = self.llm.get_response(
                system_prompt="You are an evaluator that only returns valid JSON as specified.",
                user_prompt=failure_conditions_prompt
            )
            failure_response = self.extract_json(failure_response)
            res = json.loads(failure_response)
            print(f"[INFO] Failure response: {res}")
            
            if res.get('has_failure_conditions'):
                print(f"[INFO] Transitioning to failure phase '{phase_name}'")
                final_next_phases = [pt for pt in potential_transitions_info if pt["next_phase_name"] != phase_name]
                return {
                    'phase': phase_name,
                    'observations': [],
                    "conditions_for_next_phases": final_next_phases
                }

        # 3. Check success conditions for each success phase
        for phase_name in success_phase_names:
            phase = self.phases.get(phase_name)
            if not phase:
                continue
            
            # Get conditions for this phase
            phase_id = None
            for pid, name in self.phase_id_to_name.items():
                if name == phase_name:
                    phase_id = pid
                    break
            
            if phase_id:
                conditions = self.supabase_service.get_phase_conditions(phase_id)
            else:
                conditions = phase.get('conditions', [])
            
            # Skip if no conditions
            if not conditions:
                continue
            
            # Asegurarse de no añadir la fase actual
            if phase_name == current_phase_name:
                continue
            
            # Añadir a la lista de condiciones para fases siguientes
            conditions_for_next_phases = []
            
            success_conditions_prompt = f"""
                You are an evaluator that checks if a message satisfies required conditions.
                Your task is to analyze the message and determine which conditions it satisfies, considering both previously satisfied conditions and new ones from this message.

                ## Required conditions (ALL must be satisfied):
                {conditions}
                
                ## Already satisfied conditions from previous messages:
                {accumulated_conditions}
                
                ## Current message to evaluate:
                "{user_input}"

                ## Instructions:
                1. Check which NEW conditions from the required list are satisfied by THIS message
                2. Consider both explicit and implicit satisfaction of conditions
                3. Be literal in your matching - for example:
                   - If a condition is "Agent explains reason for the call" and the message includes "I wanted to check in on...", that IS a match
                   - If a condition is "Agent mentions purpose is to help with Microsoft 365 tools" and the message mentions "check in on how you're using Microsoft 365", that IS a match
                4. has_success_conditions should be true ONLY if ALL required conditions are now satisfied (combining previous and new conditions)

                ## Response format:
                Return ONLY a JSON with two fields:
                - "has_success_conditions": boolean (true if ALL required conditions are now satisfied between previous and new conditions)
                - "success_conditions_found": list of NEW conditions found in THIS message (not including previously satisfied ones)
                """
            success_response = self.llm.get_response(
                system_prompt="You are an evaluator that only returns valid JSON as specified.",
                user_prompt=success_conditions_prompt
            )
            success_response = self.extract_json(success_response)
            res = json.loads(success_response)
            
            # Add newly found conditions to accumulated ones
            new_conditions = res.get('success_conditions_found', [])
            all_conditions = accumulated_conditions.copy()
            for condition in new_conditions:
                if condition not in all_conditions:
                    all_conditions.append(condition)
            
            # Check if we have all required conditions now
            if sorted(all_conditions) == sorted(conditions):
                print(f"[INFO] Transitioning to success phase '{phase_name}'")
                final_next_phases = [pt for pt in potential_transitions_info if pt["next_phase_name"] != phase_name]
                return {
                    'phase': phase_name,
                    'observations': [],
                    "conditions_for_next_phases": final_next_phases
                }
        
        # No transition, return updated accumulated conditions for current phase
        all_updated_conditions = accumulated_conditions.copy()
        for condition in new_conditions:
            if condition not in all_updated_conditions:
                all_updated_conditions.append(condition)
        
        print(f"[INFO] Staying in phase '{current_phase_name}'")
        # Si se queda en la misma fase, mostramos todas las transiciones originales como posibles siguientes.
        final_next_phases_on_stay = [pt for pt in potential_transitions_info if pt["next_phase_name"] != current_phase_name]
        return {
            'phase': current_phase_name,
            'observations': all_updated_conditions,
            "conditions_for_next_phases": final_next_phases_on_stay
        }

