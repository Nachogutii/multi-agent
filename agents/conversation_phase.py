from enum import Enum
from typing import List, Dict
import time

class ConversationPhase(Enum):
    DISCOVERY = "discovery"
    NEEDS_ANALYSIS = "needs_analysis"
    VALUE_ALIGNMENT = "value_alignment"
    PRODUCT_EXPERIENCE = "product_experience"
    SOLUTION_PRESENTATION = "solution_presentation"
    OBJECTION_HANDLING = "objection_handling"
    DECISION_MAKING = "decision_making"
    FOLLOW_UP = "follow_up"
    CLOSING = "closing"

class ConversationPhaseManager:
    """Manages the progression of PLG conversation phases."""
    
    def __init__(self, azure_client=None, deployment=None):
        self.current_phase = ConversationPhase.DISCOVERY
        self.phase_history: List[Dict] = []
        self.client = azure_client
        self.deployment = deployment
        self.phase_indicators = {
            ConversationPhase.DISCOVERY: [
                "tell me more about",
                "what can it do",
                "how does it work",
                "explain",
                "describe"
            ],
            ConversationPhase.NEEDS_ANALYSIS: [
                "what are your needs",
                "what problems",
                "what challenges",
                "what are you trying to achieve",
                "what's your goal"
            ],
            ConversationPhase.VALUE_ALIGNMENT: [
                "benefits",
                "value",
                "roi",
                "return on investment",
                "cost savings",
                "efficiency"
            ],
            ConversationPhase.PRODUCT_EXPERIENCE: [
                "try it",
                "demo",
                "trial",
                "test",
                "experience",
                "hands-on"
            ],
            ConversationPhase.SOLUTION_PRESENTATION: [
                "solution",
                "package",
                "offer",
                "proposal",
                "recommendation"
            ],
            ConversationPhase.OBJECTION_HANDLING: [
                "concern",
                "worried",
                "hesitant",
                "not sure",
                "doubt",
                "expensive",
                "complicated"
            ],
            ConversationPhase.DECISION_MAKING: [
                "decide",
                "choose",
                "select",
                "move forward",
                "proceed",
                "next steps"
            ],
            ConversationPhase.FOLLOW_UP: [
                "follow up",
                "check back",
                "keep in touch",
                "stay in contact",
                "reach out"
            ],
            ConversationPhase.CLOSING: [
                "thank you",
                "thanks",
                "goodbye",
                "bye",
                "have a good day",
                "talk to you later",
                "that's all",
                "that will be all"
            ]
        }
    
    def analyze_message(self, message: str) -> ConversationPhase:
        """Analyzes a message to determine the current conversation phase."""
        message_lower = message.lower()
        
        # Check for closing phase first
        if any(indicator in message_lower for indicator in self.phase_indicators[ConversationPhase.CLOSING]):
            return ConversationPhase.CLOSING
        
        # Check other phases in order
        for phase in ConversationPhase:
            if phase == ConversationPhase.CLOSING:
                continue
                
            if any(indicator in message_lower for indicator in self.phase_indicators[phase]):
                self._update_phase(phase)
                return phase
        
        return self.current_phase
    
    def _update_phase(self, new_phase: ConversationPhase):
        """Updates the current phase and records the transition."""
        if new_phase != self.current_phase:
            self.phase_history.append({
                "from_phase": self.current_phase,
                "to_phase": new_phase,
                "timestamp": time.time()
            })
            self.current_phase = new_phase
    
    def is_closing_phase(self) -> bool:
        """Checks if the conversation is in the closing phase."""
        return self.current_phase == ConversationPhase.CLOSING
    
    def get_phase_history(self) -> List[Dict]:
        """Returns the history of phase transitions."""
        return self.phase_history
    
    def get_current_phase(self) -> ConversationPhase:
        """Returns the current conversation phase."""
        return self.current_phase 