from typing import List, Dict
import time
from openai import AzureOpenAI
from phase_config import ConversationPhaseConfig

class ConversationPhaseManager:
    def __init__(self, azure_client=None, deployment=None):
        self.client = azure_client
        self.deployment = deployment
        self.conversation_history: List[Dict] = []
        self.phase_config = ConversationPhaseConfig()  
        self.current_phase = self.phase_config.get_initial_phase()  
        self.phase_history: List[Dict] = []

    def add_message(self, message: str, is_agent: bool = True):
        self.conversation_history.append({
            "message": message,
            "is_agent": is_agent,
            "timestamp": time.time()
        })

    def analyze_message(self, agent_message: str, customer_response: str) -> str:
        current_config = self.phase_config.get_phase(self.current_phase)

        prompt = f"""
        You are an expert evaluator on Product led Growth conversation, evaluating whether the conversation can move to the next phase based on the following criteria.

        ## CURRENT PHASE: {self.current_phase}

        ## SUCCESS CRITERIA
        {chr(10).join('- ' + c for c in current_config.success_criteria)}

        ## FAILURE CRITERIA
        {chr(10).join('- ' + c for c in current_config.failure_criteria)}

        ## AGENT MESSAGE
        {agent_message}

        ## CUSTOMER RESPONSE
        {customer_response}

        Respond only with one of the following phase names:
        - {current_config.success_transition}
        - {current_config.failure_transition}
        - {self.current_phase} (if criteria are partially met)
        """

        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "You are a conversation phase evaluator."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=20,
                temperature=0
            )

            decision = response.choices[0].message.content.strip()

            if decision != self.current_phase:
                self.phase_history.append({
                    "from": self.current_phase,
                    "to": decision,
                    "timestamp": time.time()
                })
                self.current_phase = decision

            return self.current_phase

        except Exception as e:
            print(f"Error during phase evaluation: {str(e)}")
            return self.current_phase

    def get_current_phase(self) -> str:
        return self.current_phase

    def get_system_prompt(self) -> str:
        return self.phase_config.get_phase(self.current_phase).system_prompt

    def get_phase_history(self) -> List[Dict]:
        return self.phase_history
