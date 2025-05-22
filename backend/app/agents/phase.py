import json
from app.services.supabase import SupabasePhasesService
from app.services.azure_openai import AzureOpenAIClient

class PhaseAgent:
    def __init__(self):
        self.supabase_service = SupabasePhasesService()
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
        
        print(f"[INFO] Evaluating: Success paths: {success_phase_names}, Failure paths: {failure_phase_names}")

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
                Evaluate if the message matches any of the following conditions. The context of the conversation is the following:
                Rachel is a customer from Microsoft who has a small marketing business. Keep in mind for checking the conditions that Rachel is a customer from Microsoft.

                ## Conditions 
                {conditions}
                
                ## The message to evaluate
                "{user_input}"

                ## response

                Return ONLY a JSON with two fields:
                - "has_failure_conditions": boolean (true ONLY if the message matches any of the conditions)
                - "failure_conditions_found": list of specific conditions found (empty if none)
            """
            failure_response = self.llm.get_response(
                system_prompt="You are an evaluator that only returns valid JSON as specified.",
                user_prompt=failure_conditions_prompt
            )
            failure_response = self.extract_json(failure_response)
            res = json.loads(failure_response)
            
            if res.get('has_failure_conditions'):
                print(f"[INFO] Failure conditions met for phase '{phase_name}': {res['failure_conditions_found']}")
                return {
                    'phase': phase_name,
                    'observations': res['failure_conditions_found']
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
                Evaluate if the message matches any of the following conditions.
                The user might have already satisfied some conditions in previous messages.

                ## All required conditions 
                {conditions}
                
                ## Already satisfied conditions
                {accumulated_conditions}
                
                ## Current message to evaluate
                "{user_input}"

                ## response

                Return ONLY a JSON with two fields:
                - "has_success_conditions": boolean (true ONLY if ALL required conditions are now satisfied, 
                  either from previous messages or this message)
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
            if sorted(all_conditions) == sorted(conditions) or res.get('has_success_conditions'):
                print(f"[INFO] Success conditions met for phase '{phase_name}': {all_conditions}")
                return {
                    'phase': phase_name,
                    'observations': all_conditions
                }
        
        # No transition, return updated accumulated conditions
        all_updated_conditions = accumulated_conditions.copy()
        for condition in new_conditions:
            if condition not in all_updated_conditions:
                all_updated_conditions.append(condition)
        
        print(f"[INFO] No phase transition, staying in '{current_phase_name}'")        
        return {
            'phase': current_phase_name,
            'observations': all_updated_conditions
        }

