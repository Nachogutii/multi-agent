import json
from pathlib import Path
from typing import List, Dict

class PhaseConfig:
    def __init__(
        self,
        name: str,
        system_prompt: str,
        success_criteria: List[str],
        failure_criteria: List[str],
        on_success: str,
        on_failure: str
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.success_criteria = success_criteria
        self.failure_criteria = failure_criteria
        self.on_success = on_success
        self.on_failure = on_failure

class ConversationFlowConfig:
    def __init__(self, path: str = "conversation_phases.json"):
        self.path = Path(path)
        self.phases: Dict[str, PhaseConfig] = {}
        self.load()

    def load(self):
        with self.path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            for phase in data:
                phase_obj = PhaseConfig(
                    name=phase["name"],
                    system_prompt=phase["system_prompt"],
                    success_criteria=phase["success_criteria"],
                    failure_criteria=phase["failure_criteria"],
                    on_success=phase["on_success"],
                    on_failure=phase["on_failure"]
                )
                self.phases[phase["name"]] = phase_obj

    def get_phase(self, phase_name: str) -> PhaseConfig:
        return self.phases.get(phase_name)

    def get_all_phase_names(self) -> List[str]:
        return list(self.phases.keys())
