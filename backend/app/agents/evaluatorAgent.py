import json
from backend.app.services.supabase import SupabasePhasesService
from backend.app.services.azure_openai import AzureOpenAIClient
import re

class EvaluatorAgent:
    def __init__(self):
        self.supabase_service = SupabasePhasesService()
        assert self.supabase_service.initialize(), "Could not initialize Supabase client"
        self.red_flags = self.supabase_service.get_red_flags()
        self.phases = {phase['name']: phase for phase in self.supabase_service.get_all_phases()}
        self.success_conditions_achieved = []
        self.llm = AzureOpenAIClient()
        
    def extract_json(self, text):
        import re
        text = re.sub(r"```json|```", "", text, flags=re.IGNORECASE).strip()
        return text

    def evaluate(self, user_input, current_phase_name):
        current_phase = self.phases[current_phase_name]

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
            system_prompt = (
                "You are a strict JSON generator. "
                "You must return ONLY a valid JSON object as specified in the instructions, "
                "with no extra text, no explanations, and no markdown formatting."
            ),
            user_prompt=f"User message: {user_input}\n\n{red_flag_prompt}"
        )
        print("LLM raw response:", red_flag_response)
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
            failure_response_clean = self.extract_json(failure_response)
            res = json.loads(failure_response_clean)
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
            success_conditions_prompt = f"""
                Evaluate if the message matches all of the following conditions

                ## Conditions 
                {conditions}

                ## response

                Return ONLY a JSON with two fields:
                - "has_success_conditions": boolean (true ONLY if the message matches all of the conditions)
                - "success_conditions_found": list of specific conditions found (empty if none)
            """
            success_response = self.llm.get_response(
                system_prompt="You are an evaluator that only returns valid JSON as specified.",
                user_prompt=f"User message: {user_input}\n\n{success_conditions_prompt}"
            )
            success_response_clean = self.extract_json(success_response)
            res = json.loads(success_response_clean)
            if res.get('has_success_conditions'):
                return {
                    'phase': phase_name,
                    'observations': conditions
                }
            else:
                # Track which success conditions have been achieved
                for item in res.get('success_conditions_found', []):
                    if item not in self.success_conditions_achieved:
                        self.success_conditions_achieved.append(item)
                if sorted(self.success_conditions_achieved) == sorted(conditions):
                    return {
                        'phase': phase_name,
                        'observations': conditions
                    }
                else:
                    return {
                        'phase': current_phase_name,
                        'observations': []
                    }

        # If no match, stay in current phase
        return {
            'phase': current_phase_name,
            'observations': []
        }

# Example usage
if __name__ == "__main__":
    agent = EvaluatorAgent()
    result = agent.evaluate("Hello I am Miguel from Microsoft, can you tell me more abour your business goals?", "welcome")
    print(result)