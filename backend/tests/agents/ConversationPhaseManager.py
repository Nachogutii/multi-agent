from enum import Enum

class ConversationPhase(Enum):
    INTRODUCTION_DISCOVERY = "introduction_discovery"
    VALUE_PROPOSITION = "value_proposition"
    OBJECTION_HANDLING = "objection_handling"
    CLOSING = "closing"
    IMMEDIATE_CLOSURE = "immediate_closure"

class ConversationPhaseManager:
    def __init__(self):
        self.phase_slots = []
        self.current_index = 0
        self.phase_history = []

    def set_phase_slots(self, phase_slots):
        self.phase_slots = [ConversationPhase(phase) for phase in phase_slots]
        self.current_index = 0
        self.phase_history = []

    def get_current_phase(self):
        if self.current_index < len(self.phase_slots):
            return self.phase_slots[self.current_index].value
        return ConversationPhase.CLOSING.value

    def advance_phase_if_needed(self, user_input):
        # Placeholder logic (expand as needed)
        if "next" in user_input.lower() or len(user_input.split()) > 15:
            if self.current_index < len(self.phase_slots) - 1:
                self.current_index += 1
                self.phase_history.append(self.phase_slots[self.current_index].value)

    def get_phase_history(self):
        return self.phase_history

    def is_closing_phase(self):
        current = self.phase_slots[self.current_index] if self.current_index < len(self.phase_slots) else None
        return current in [ConversationPhase.CLOSING, ConversationPhase.IMMEDIATE_CLOSURE]
