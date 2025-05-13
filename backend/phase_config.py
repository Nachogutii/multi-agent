import json
from pathlib import Path
from typing import Dict, List, Optional

class Phase:
    def __init__(self, name: str, system_prompt: str,
                 success_transition: str, failure_transition: str,
                 critical_aspects: List[str] = None, 
                 red_flags: List[str] = None,
                 optional_aspects: List[str] = None):
        self.name = name
        self.system_prompt = system_prompt
        self.success_transition = success_transition
        self.failure_transition = failure_transition
        
        # Fields for the improved transition system
        self.critical_aspects = critical_aspects or []
        self.red_flags = red_flags or []
        self.optional_aspects = optional_aspects or []

class ConversationPhaseConfig:
    def __init__(self, phases_data: List[dict] = None):
        self.phases: Dict[str, Phase] = {}
        self.phase_order: List[str] = []
        
        if phases_data:
            self._load_from_data(phases_data)
        else:
            # Por compatibilidad, usar una fase default si no hay datos
            default_phase = Phase(
                name="welcome",
                system_prompt="You are a helpful assistant.",
                success_transition="welcome",
                failure_transition="welcome",
                critical_aspects=[],
                red_flags=[],
                optional_aspects=[]
            )
            self.phases["welcome"] = default_phase
            self.phase_order.append("welcome")
            print("⚠️ ConversationPhaseConfig: No se proporcionaron datos de fases, usando fase default.")

    def _load_from_data(self, phases_data: List[dict]):
        for phase_data in phases_data:
            phase = Phase(
                name=phase_data["name"],
                system_prompt=phase_data["system_prompt"],
                success_transition=phase_data["on_success"],
                failure_transition=phase_data["on_failure"],
                critical_aspects=phase_data.get("critical_aspects", []),
                red_flags=phase_data.get("red_flags", []),
                optional_aspects=phase_data.get("optional_aspects", [])
            )
            self.phases[phase.name] = phase
            self.phase_order.append(phase.name)

    def get_phase(self, name: str) -> Optional[Phase]:
        return self.phases.get(name)

    def get_initial_phase(self) -> str:
        return self.phase_order[0] if self.phase_order else "welcome"

    def get_next_phase(self, current_phase: str, success: bool) -> Optional[str]:
        phase = self.get_phase(current_phase)
        if not phase:
            return None
        return phase.success_transition if success else phase.failure_transition