import random
from profiles import profiles

class Orchestrator:
    def __init__(self, customer_agent, phase_manager, emotion_agent, evaluator):
        self.customer_agent = customer_agent
        self.phase_manager = phase_manager
        self.emotion_agent = emotion_agent
        self.evaluator = evaluator
        self.dialogue_history = []
        self.customer_profile = None

    def initialize_conversation(self):
        phenotype_name = random.choice(list(profiles.keys()))
        self.customer_profile = profiles[phenotype_name]

        self.customer_agent.set_profile(self.customer_profile)
        self.phase_manager.set_phase_slots(self.customer_profile["phase_slots"])
        self.emotion_agent.set_initial_state(self.customer_profile["emotional_state"])

    def handle_user_input(self, user_input):
        self.emotion_agent.update_state(user_input)

        current_phase = self.phase_manager.get_current_phase()
        current_emotion = self.emotion_agent.get_state()

        customer_reply = self.customer_agent.generate_reply(
            user_input=user_input,
            phase=current_phase,
            emotion=current_emotion
        )

        self.dialogue_history.append({
            "user": user_input,
            "customer": customer_reply,
            "phase": current_phase,
            "emotion": current_emotion
        })

        self.phase_manager.advance_phase_if_needed(user_input)

        if self.phase_manager.is_closing_phase():
            final_feedback = self.evaluator.evaluate_conversation(self.dialogue_history)
            return customer_reply + "\n\n[Conversation Ended]", final_feedback

        return customer_reply, None

    def end_conversation(self):
        return self.evaluator.evaluate_conversation(self.dialogue_history)
