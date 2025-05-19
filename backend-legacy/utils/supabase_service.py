import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_scenarios():
    try:
        print(f"🔍 Buscando escenarios en Supabase...")
        data = supabase.table("scenarios").select("*").execute().data
        print(f"✅ Encontrados {len(data)} escenarios")
        return data
    except Exception as e:
        print(f"❌ Error obteniendo escenarios: {str(e)}")
        return []

def get_scenario_by_id(scenario_id):
    try:
        print(f"🔍 Buscando escenario con ID: {scenario_id}")
        data = supabase.table("scenarios").select("*").eq("id", scenario_id).execute().data
        if not data:
            print(f"⚠️ No se encontró escenario con ID: {scenario_id}")
            return None
        print(f"✅ Escenario encontrado: {data[0].get('name', 'Sin nombre')}")
        return data[0] if data else None
    except Exception as e:
        print(f"❌ Error obteniendo escenario por ID: {str(e)}")
        return None

def get_phases_for_scenario(scenario_id):
    try:
        print(f"🔍 Buscando fases para escenario ID: {scenario_id}")
        data = supabase.table("phases").select("*").eq("scenario_id", scenario_id).order("phase_order").execute().data
        print(f"✅ Encontradas {len(data)} fases para el escenario")
        return data
    except Exception as e:
        print(f"❌ Error obteniendo fases: {str(e)}")
        return []

def get_aspects_for_phase(phase_id):
    try:
        print(f"🔍 Buscando aspectos para fase ID: {phase_id}")
        data = supabase.table("aspects").select("*").eq("phase_id", phase_id).execute().data
        print(f"✅ Encontrados {len(data)} aspectos para la fase")
        return data
    except Exception as e:
        print(f"❌ Error obteniendo aspectos: {str(e)}")
        return []