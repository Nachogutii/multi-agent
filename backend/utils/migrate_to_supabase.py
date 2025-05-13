import os
import json
from supabase import create_client, Client

# Carga claves desde .env
from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 1. Lee el contexto del escenario
with open("../scenario_context.md", "r", encoding="utf-8") as f:
    context = f.read()

# 2. Lee las fases y prompts
with open("../conversation_phases.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 3. Crea el escenario en Supabase
scenario_name = data.get("ScenarioName", "Default Scenario")
scenario_description = data.get("ScenarioDescription", "")
initial_prompt = data.get("InitialPrompt", "")

scenario_resp = supabase.table("scenarios").insert({
    "name": scenario_name,
    "description": scenario_description,
    "context": context,
    "initial_prompt": initial_prompt
}).execute()
scenario_id = scenario_resp.data[0]["id"]

# 4. Inserta las fases y aspectos
for idx, phase in enumerate(data["Phases"]):
    phase_resp = supabase.table("phases").insert({
        "scenario_id": scenario_id,
        "name": phase["name"],
        "system_prompt": phase["system_prompt"],
        "on_success": phase["on_success"],
        "on_failure": phase["on_failure"],
        "phase_order": idx
    }).execute()
    phase_id = phase_resp.data[0]["id"]

    # Aspectos críticos
    for aspect in phase.get("critical_aspects", []):
        supabase.table("aspects").insert({
            "phase_id": phase_id,
            "name": aspect,
            "type": "critical"
        }).execute()
    # Aspectos opcionales
    for aspect in phase.get("optional_aspects", []):
        supabase.table("aspects").insert({
            "phase_id": phase_id,
            "name": aspect,
            "type": "optional"
        }).execute()
    # Red flags
    for aspect in phase.get("red_flags", []):
        supabase.table("aspects").insert({
            "phase_id": phase_id,
            "name": aspect,
            "type": "red_flag"
        }).execute()

print("✅ Migración completada con éxito.")