from pydantic import BaseModel, conlist, validator
from typing import List, Set

class ScenarioBase(BaseModel):
    name: str
    system_prompt: str

class ConditionBase(BaseModel):
    id: int
    description: str

class PhaseBase(BaseModel):
    id: int
    name: str
    system_prompt: str
    success_phases: List[int] = []
    failure_phases: List[int] = []

    @validator('success_phases', 'failure_phases')
    def validate_phase_references(cls, v):
        # Asegurarse de que es una lista válida
        if not isinstance(v, list):
            raise ValueError('Must be a list of phase IDs')
        # Asegurarse de que todos los elementos son enteros positivos
        if not all(isinstance(x, int) and x > 0 for x in v):
            raise ValueError('All elements must be positive integers')
        return v

class PhaseConditionBase(BaseModel):
    phase_id: int
    conditions_id: int

class ScenarioCreate(BaseModel):
    scenario: ScenarioBase
    conditions: List[ConditionBase]
    phases: List[PhaseBase]
    phase_conditions: List[PhaseConditionBase]

    @validator('conditions')
    def validate_conditions(cls, v):
        # Verificar que los IDs de las condiciones son únicos
        condition_ids = {cond.id for cond in v}
        if len(condition_ids) != len(v):
            raise ValueError('Condition IDs must be unique')
        return v

    @validator('phases')
    def validate_phase_references(cls, v, values):
        if not v:
            raise ValueError('At least one phase is required')

        # Obtener todos los IDs de phase disponibles
        phase_ids = {phase.id for phase in v}

        for phase in v:
            # Validar que las phases referenciadas existan
            for phase_id in phase.success_phases:
                if phase_id not in phase_ids:
                    raise ValueError(f'Phase {phase_id} is referenced as a success phase but does not exist')
                if phase_id == phase.id:
                    raise ValueError(f'Phase {phase.id} cannot reference itself as a success phase')

            for phase_id in phase.failure_phases:
                if phase_id not in phase_ids:
                    raise ValueError(f'Phase {phase_id} is referenced as a failure phase but does not exist')
                if phase_id == phase.id:
                    raise ValueError(f'Phase {phase.id} cannot reference itself as a failure phase')

        return v

    @validator('phase_conditions')
    def validate_phase_conditions(cls, v, values):
        if not v:
            return v

        # Obtener IDs disponibles
        phase_ids = {phase.id for phase in values.get('phases', [])}
        condition_ids = {cond.id for cond in values.get('conditions', [])}

        # Validar cada relación
        for pc in v:
            if pc.phase_id not in phase_ids:
                raise ValueError(f'Phase {pc.phase_id} does not exist')
            if pc.conditions_id not in condition_ids:
                raise ValueError(f'Condition {pc.conditions_id} does not exist')

        # Verificar que no hay duplicados en las relaciones
        relations = {(pc.phase_id, pc.conditions_id) for pc in v}
        if len(relations) != len(v):
            raise ValueError('Duplicate phase-condition relationships found')

        return v

    class Config:
        json_schema_extra = {
            "example": {
                "scenario": {
                    "name": "Example Scenario",
                    "system_prompt": "This is an example"
                },
                "conditions": [
                    {
                        "id": 1,
                        "description": "First condition"
                    }
                ],
                "phases": [
                    {
                        "id": 1,
                        "name": "First Phase",
                        "system_prompt": "Phase prompt",
                        "success_phases": [2,3],
                        "failure_phases": [4]
                    }
                ],
                "phase_conditions": [
                    {
                        "phase_id": 1,
                        "conditions_id": 1
                    }
                ]
            }
        } 