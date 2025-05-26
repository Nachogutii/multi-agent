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
        
        # Initialize new_conditions here to avoid UnboundLocalError
        new_conditions = []
        
        current_phase = self.phases[current_phase_name]
        
        # Get success and failure phase names
        success_phase_ids = current_phase.get('success_phases', [])
        success_phase_names = [self.phase_id_to_name.get(phase_id) for phase_id in success_phase_ids if phase_id in self.phase_id_to_name]
        
        failure_phase_ids = current_phase.get('failure_phases', [])
        failure_phase_names = [self.phase_id_to_name.get(phase_id) for phase_id in failure_phase_ids if phase_id in self.phase_id_to_name]
        
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
            return {"end": True, "reason": "red_flag", "details": red_flag_result["red_flags_found"]}

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
            
            if res.get('has_failure_conditions'):
                print(f"[INFO] Transitioning to failure phase '{phase_name}'")
                return {
                    'phase': phase_name,
                    'observations': []
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
                return {
                    'phase': phase_name,
                    'observations': []
                }
        
        # No transition, return updated accumulated conditions for current phase
        all_updated_conditions = accumulated_conditions.copy()
        for condition in new_conditions:
            if condition not in all_updated_conditions:
                all_updated_conditions.append(condition)
        
        print(f"[INFO] Staying in phase '{current_phase_name}'")        
        return {
            'phase': current_phase_name,
            'observations': all_updated_conditions
        }

