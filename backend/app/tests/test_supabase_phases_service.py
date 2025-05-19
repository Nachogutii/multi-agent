import pytest
from backend.app.services.supabase_phases_service import SupabasePhasesService

@pytest.fixture(scope="module")
def service():
    svc = SupabasePhasesService()
    assert svc.initialize(), "Could not initialize Supabase client"
    return svc

def test_get_red_flags(service):
    red_flags = service.get_red_flags()
    assert isinstance(red_flags, list), "Red flags should be a list"
    assert len(red_flags) > 0, "There should be at least one red flag"
    assert any("rude" in rf.lower() for rf in red_flags), "There should be a red flag mentioning 'rude'"

def test_get_all_phases(service):
    phases = service.get_all_phases()
    assert isinstance(phases, list), "Phases should be a list"
    assert len(phases) > 0, "There should be at least one phase"
    assert any("name" in phase for phase in phases), "Each phase should have a 'name' field"

def test_get_phase_by_name(service):
    phase = service.get_phase_by_name("welcome")
    assert phase is not None, "Phase 'welcome' should exist"
    assert phase["name"] == "welcome", "Phase name should be 'welcome'"
    assert "system_prompt" in phase, "'system_prompt' should be present in the phase"
    assert isinstance(phase["on_success"], list), "'on_success' should be a list"
    assert isinstance(phase["on_failure"], list), "'on_failure' should be a list"