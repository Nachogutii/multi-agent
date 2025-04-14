import json
from pathlib import Path
from typing import Dict, List, Optional
import os


class Phase:
    def __init__(self, name: str, system_prompt: str,
                 success_criteria: List[str], failure_criteria: List[str],
                 success_transition: str, failure_transition: str):
        self.name = name
        self.system_prompt = system_prompt
        self.success_criteria = success_criteria
        self.failure_criteria = failure_criteria
        self.success_transition = success_transition
        self.failure_transition = failure_transition


class ConversationPhaseConfig:
    def __init__(self, config_path: str = "conversation_phases.json"):
        self.config_path = Path(os.path.join(os.path.dirname(__file__), config_path))
        self.phases: Dict[str, Phase] = {}
        self.phase_order: List[str] = []
        self._load_config()

    def _load_config(self):
        with open(self.config_path, encoding="utf-8") as f:
            data = json.load(f)

        for phase_data in data["Phases"]:
            phase = Phase(
                name=phase_data["name"],
                system_prompt=phase_data["system_prompt"],
                success_criteria=phase_data["success_criteria"],
                failure_criteria=phase_data["failure_criteria"],
                success_transition=phase_data["on_success"],
                failure_transition=phase_data["on_failure"]
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
