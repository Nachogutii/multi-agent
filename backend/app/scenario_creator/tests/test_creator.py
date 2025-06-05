import pytest
from app.scenario_creator.creator import ScenarioCreator

@pytest.fixture
def sample_scenario_json():
    return {
        "scenario": {
            "name": "Onboarding Copilot",
            "system_prompt": "You are a Copilot onboarding assistant..."
        },
        "conditions": [
            {"id": 1, "description": "User understands Copilot concept"},
            {"id": 2, "description": "User asks for use cases"},
            {"id": 3, "description": "User seems disengaged"}
        ],
        "phases": [
            {
                "id": 1,
                "name": "Welcome",
                "system_prompt": "Welcome the user and introduce Copilot...",
                "success_phases": [2],
                "failure_phases": [3],
                "conditions": [1]
            },
            {
                "id": 2,
                "name": "Show Use Cases",
                "system_prompt": "Describe relevant Copilot use cases...",
                "success_phases": [],
                "failure_phases": [3],
                "conditions": [2]
            },
            {
                "id": 3,
                "name": "Re-engage",
                "system_prompt": "Try to re-engage the user if they're not responsive...",
                "success_phases": [2],
                "failure_phases": [],
                "conditions": [3]
            }
        ]
    }

@pytest.fixture
def creator():
    creator = ScenarioCreator()
    assert creator.initialized, "El servicio de Supabase debería inicializarse correctamente"
    return creator

def test_create_scenario_from_json(creator, sample_scenario_json):
    """Prueba la creación completa de un escenario desde JSON."""
    # Crear el escenario
    scenario_id = creator.create_scenario_from_json(sample_scenario_json)
    assert scenario_id is not None, "La creación del escenario debería ser exitosa"

    # Verificar que el escenario se creó correctamente
    scenario = creator.service.client.table("scenarios").select("*").eq("id", scenario_id).execute()
    assert len(scenario.data) == 1, "Debería existir un escenario con el ID creado"
    assert scenario.data[0]["name"] == sample_scenario_json["scenario"]["name"]

    # Verificar que las condiciones se crearon
    for condition in sample_scenario_json["conditions"]:
        original_id = condition["id"]
        mapped_id = creator.id_mapping[original_id]
        condition_data = creator.service.client.table("conditions").select("*").eq("id", mapped_id).execute()
        assert len(condition_data.data) == 1, f"La condición {condition['id']} debería existir"
        assert condition_data.data[0]["description"] == condition["description"]

    # Verificar que las fases se crearon
    for phase in sample_scenario_json["phases"]:
        original_id = phase["id"]
        mapped_id = creator.id_mapping[original_id]
        phase_data = creator.service.client.table("phases").select("*").eq("id", mapped_id).execute()
        assert len(phase_data.data) == 1, f"La fase {phase['name']} debería existir"
        assert phase_data.data[0]["name"] == phase["name"]

        # Verificar las condiciones de la fase
        phase_conditions = creator.service.client.table("phase_conditions").select("*").eq("phase_id", mapped_id).execute()
        assert len(phase_conditions.data) == len(phase["conditions"]), f"La fase {phase['name']} debería tener {len(phase['conditions'])} condiciones"

        # Verificar que las condiciones mapeadas están correctamente asociadas
        condition_ids = [pc["conditions_id"] for pc in phase_conditions.data]
        expected_condition_ids = [creator.id_mapping[cid] for cid in phase["conditions"]]
        assert sorted(condition_ids) == sorted(expected_condition_ids), f"Las condiciones de la fase {phase['name']} no coinciden" 