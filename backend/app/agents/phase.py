import json
from backend.app.services.supabase import SupabasePhasesService
from backend.app.services.azure_openai import AzureOpenAIClient

class PhaseAgent:
    def __init__(self):
        self.supabase_service = SupabasePhasesService()
        assert self.supabase_service.initialize(), "Could not initialize Supabase client"
        self.red_flags = self.supabase_service.get_red_flags()
        self.phases = {phase['name']: phase for phase in self.supabase_service.get_all_phases()}
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
        
        current_phase = self.phases[current_phase_name]
        print(f"[DEBUG] Evaluating message for phase '{current_phase_name}'")
        print(f"[DEBUG] Accumulated conditions: {accumulated_conditions}")

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
            print("** Conversation has ended due to inappropriate behavior **")
            return {"end": True, "reason": "red_flag", "details": red_flag_result["red_flags_found"]}

        # 2. Check failure conditions for each failure phase
        for phase_name in current_phase.get('on_failure', []):
            phase = self.phases.get(phase_name)
            if not phase:
                continue
            conditions = phase.get('conditions', [])
            failure_conditions_prompt = f"""
                Evaluate if the message matches any of the following conditions

                ## Conditions 
                {conditions}

                ## response

                Return ONLY a JSON with two fields:
                - "has_failure_conditions": boolean (true ONLY if the message matches any of the conditions)
                - "failure_conditions_found": list of specific conditions found (empty if none)
            """
            failure_response = self.llm.get_response(
                system_prompt="You are an evaluator that only returns valid JSON as specified.",
                user_prompt=f"User message: {user_input}\n\n{failure_conditions_prompt}"
            )
            failure_response = self.extract_json(failure_response)
            res = json.loads(failure_response)
            if res.get('has_failure_conditions'):
                return {
                    'phase': phase_name,
                    'observations': res['failure_conditions_found']
                }

        # 3. Check success conditions for each success phase
        for phase_name in current_phase.get('on_success', []):
            phase = self.phases.get(phase_name)
            if not phase:
                continue
            conditions = phase.get('conditions', [])
            
            # Si no hay condiciones, podemos pasar directamente a esta fase
            if not conditions:
                print(f"[DEBUG] Phase '{phase_name}' has no conditions, transitioning directly")
                return {
                    'phase': phase_name,
                    'observations': []
                }
            
            success_conditions_prompt = f"""
                Evaluate if the message matches any of the following conditions.
                The user might have already satisfied some conditions in previous messages.

                ## All required conditions 
                {conditions}
                
                ## Already satisfied conditions from previous messages
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
            print(f"[DEBUG] Phase '{phase_name}' evaluation result: {res}")
            
            # Add newly found conditions to accumulated ones
            new_conditions = res.get('success_conditions_found', [])
            all_conditions = accumulated_conditions.copy()
            for condition in new_conditions:
                if condition not in all_conditions:
                    all_conditions.append(condition)
            
            # Check if we have all required conditions now
            if sorted(all_conditions) == sorted(conditions) or res.get('has_success_conditions'):
                print(f"[DEBUG] All conditions met for phase '{phase_name}', transitioning")
                return {
                    'phase': phase_name,
                    'observations': all_conditions
                }
        
        # No transition, return updated accumulated conditions
        return {
            'phase': current_phase_name,
            'observations': accumulated_conditions + [c for c in new_conditions if c not in accumulated_conditions]
        }

