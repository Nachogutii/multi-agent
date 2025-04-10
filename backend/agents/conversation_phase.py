from enum import Enum
from typing import List, Dict, Optional
import time

class ConversationPhase(Enum):
    INTRODUCTION_DISCOVERY = "introduction_discovery"
    VALUE_PROPOSITION = "value_proposition"
    OBJECTION_HANDLING = "objection_handling"
    CLOSING = "closing"
    ABRUPT_CLOSURE = "abrupt_closure"

class ConversationPhaseManager:
    """Manages the progression of PLG conversation phases using AI-based semantic analysis."""

    def __init__(self, azure_client=None, deployment=None):
        self.current_phase = ConversationPhase.INTRODUCTION_DISCOVERY
        self.phase_history: List[Dict] = []
        self.client = azure_client
        self.deployment = deployment
        self.conversation_history: List[Dict] = []

        self.phase_patterns = {
            ConversationPhase.INTRODUCTION_DISCOVERY: {
                "key_aspects": [
                    "establishing rapport",
                    "understanding customer context",
                    "identifying customer role",
                    "discovering customer needs",
                    "understanding current situation"
                ]
            },
            ConversationPhase.VALUE_PROPOSITION: {
                "key_aspects": [
                    "presenting product features",
                    "explaining benefits",
                    "showing value proposition",
                    "demonstrating capabilities",
                    "sharing success stories"
                ]
            },
            ConversationPhase.OBJECTION_HANDLING: {
                "key_aspects": [
                    "addressing concerns",
                    "providing solutions",
                    "clarifying doubts",
                    "handling objections",
                    "building confidence"
                ]
            },
            ConversationPhase.CLOSING: {
                "key_aspects": [
                    "confirming next steps",
                    "expressing gratitude",
                    "saying goodbye",
                    "offering support",
                    "ensuring satisfaction"
                ]
            }
        }

    def add_message(self, message: str, is_agent: bool = True):
        self.conversation_history.append({
            "message": message,
            "is_agent": is_agent,
            "timestamp": time.time()
        })

    def decide_phase(self, evaluation_result: Dict[str, any]) -> ConversationPhase:
        """Decide the next phase based on the evaluation result from LLM."""
        fulfilled_aspects = evaluation_result.get("fulfilled_aspects", [])
        progress = evaluation_result.get("progress", 0)
        is_empathetic = evaluation_result.get("CustomerBelievesAgentIsEmpathetic", False)
        is_legit = evaluation_result.get("CustomerBelievesAgentIsLegit", False)

        print(f"✅ Fulfilled Aspects: {fulfilled_aspects}")
        print(f"✅ Progress: {progress}%")
        print(f"✅ Empathy: {is_empathetic}")
        print(f"✅ Legitimacy: {is_legit}")

        # Obtener aspectos clave esperados de la fase actual
        expected_aspects = self.phase_patterns.get(self.current_phase, {}).get("key_aspects", [])

        # Si el progreso es 100% y se cumplen todos los aspectos esperados
        if progress == 100 and set(fulfilled_aspects) >= set(expected_aspects):
            return self._get_next_phase()

        # Si no hay progreso o no se cumple nada
        if progress < 40 or not fulfilled_aspects:
            return ConversationPhase.ABRUPT_CLOSURE

        # Si está cumpliendo parcialmente, mantener la fase
        return self.current_phase
    
    def _get_next_phase(self) -> ConversationPhase:
        """Determina la siguiente fase lógica a partir de la actual."""
        phase_order = [
            ConversationPhase.INTRODUCTION_DISCOVERY,
            ConversationPhase.VALUE_PROPOSITION,
            ConversationPhase.OBJECTION_HANDLING,
            ConversationPhase.CLOSING
        ]
        try:
            idx = phase_order.index(self.current_phase)
            if idx < len(phase_order) - 1:
                return phase_order[idx + 1]
            return self.current_phase  # Si ya está en CLOSING
        except ValueError:
            return self.current_phase

    def is_closing_phase(self) -> bool:
        return self.current_phase == ConversationPhase.CLOSING

    def get_phase_history(self) -> List[Dict]:
        return self.phase_history

    def get_current_phase(self) -> ConversationPhase:
        return self.current_phase

    def update_phase_if_needed(self, new_phase: ConversationPhase):
        if new_phase != self.current_phase:
            print(f"🔄 Phase transition: {self.current_phase.value} ➜ {new_phase.value}")
            self.phase_history.append({
                "from_phase": self.current_phase,
                "to_phase": new_phase,
                "timestamp": time.time()
            })
            self.current_phase = new_phase
