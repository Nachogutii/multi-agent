import os
import json
import sys
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Añadir directorio raíz al path para poder importar utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def migrate_to_supabase():
    """Migra los datos de los archivos locales a Supabase"""
    print("\n=== MIGRACIÓN DE DATOS A SUPABASE ===\n")
    
    # Cargar variables de entorno
    load_dotenv()
    
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Error: No se encontraron las variables de entorno SUPABASE_URL y SUPABASE_KEY")
        return False
    
    try:
        # Crear cliente de Supabase
        print("🔄 Conectando a Supabase...")
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Conexión exitosa")
        
        # 1. Leer el contexto del escenario
        context_path = Path("../scenario_context.md")
        if not context_path.exists():
            print(f"⚠️ No se encontró el archivo {context_path}")
            context = ""
        else:
            context = context_path.read_text(encoding="utf-8")
            print(f"✅ Contexto leído: {len(context)} caracteres")
        
        # 2. Leer las fases desde el JSON
        phases_path = Path("../conversation_phases.json")
        if not phases_path.exists():
            print(f"❌ No se encontró el archivo {phases_path}")
            return False
            
        print(f"🔄 Leyendo fases desde {phases_path}...")
        with open(phases_path, "r", encoding="utf-8") as f:
            phases_data = json.load(f)
            print(f"✅ Datos cargados: {len(phases_data.get('Phases', []))} fases")
        
        # 3. Verificar si ya existe el escenario antes de crearlo
        print("🔍 Verificando si ya existe el escenario...")
        scenarios = supabase.table("scenarios").select("*").execute().data
        scenario_exists = False
        scenario_id = None
        
        for s in scenarios:
            if s.get("name") == phases_data.get("ScenarioName", "Default Scenario"):
                scenario_exists = True
                scenario_id = s.get("id")
                print(f"✅ Escenario ya existe con ID: {scenario_id}")
                break
        
        # 4. Crear el escenario si no existe
        if not scenario_exists:
            print("🔄 Creando escenario...")
            scenario_data = {
                "name": phases_data.get("ScenarioName", "Default Scenario"),
                "description": phases_data.get("ScenarioDescription", ""),
                "initial_prompt": phases_data.get("InitialPrompt", ""),
                "context": context
            }
            
            scenario_response = supabase.table("scenarios").insert(scenario_data).execute()
            scenario_id = scenario_response.data[0].get("id")
            print(f"✅ Escenario creado con ID: {scenario_id}")
        
        # 5. Importar las fases
        for i, phase_data in enumerate(phases_data.get("Phases", [])):
            print(f"\n🔄 Procesando fase: {phase_data.get('name')}")
            
            # Verificar si la fase ya existe
            existing_phases = supabase.table("phases").select("*").eq("scenario_id", scenario_id).eq("name", phase_data.get("name")).execute().data
            
            if existing_phases:
                phase_id = existing_phases[0].get("id")
                print(f"  ✅ Fase ya existe con ID: {phase_id}")
            else:
                # Crear la fase
                new_phase_data = {
                    "scenario_id": scenario_id,
                    "name": phase_data.get("name"),
                    "system_prompt": phase_data.get("system_prompt"),
                    "on_success": phase_data.get("on_success"),
                    "on_failure": phase_data.get("on_failure"),
                    "phase_order": i
                }
                
                phase_response = supabase.table("phases").insert(new_phase_data).execute()
                phase_id = phase_response.data[0].get("id")
                print(f"  ✅ Fase creada con ID: {phase_id}")
            
            # 6. Importar los aspectos críticos
            for aspect in phase_data.get("critical_aspects", []):
                print(f"    🔄 Aspecto crítico: {aspect}")
                
                # Verificar si el aspecto ya existe
                existing_aspects = supabase.table("aspects").select("*").eq("phase_id", phase_id).eq("name", aspect).eq("type", "critical").execute().data
                
                if existing_aspects:
                    print(f"      ✓ Ya existe")
                else:
                    # Crear el aspecto
                    aspect_data = {
                        "phase_id": phase_id,
                        "name": aspect,
                        "type": "critical"
                    }
                    
                    supabase.table("aspects").insert(aspect_data).execute()
                    print(f"      ✅ Creado")
            
            # 7. Importar los aspectos opcionales
            for aspect in phase_data.get("optional_aspects", []):
                print(f"    🔄 Aspecto opcional: {aspect}")
                
                # Verificar si el aspecto ya existe
                existing_aspects = supabase.table("aspects").select("*").eq("phase_id", phase_id).eq("name", aspect).eq("type", "optional").execute().data
                
                if existing_aspects:
                    print(f"      ✓ Ya existe")
                else:
                    # Crear el aspecto
                    aspect_data = {
                        "phase_id": phase_id,
                        "name": aspect,
                        "type": "optional"
                    }
                    
                    supabase.table("aspects").insert(aspect_data).execute()
                    print(f"      ✅ Creado")
            
            # 8. Importar los red flags
            for aspect in phase_data.get("red_flags", []):
                print(f"    🔄 Red flag: {aspect}")
                
                # Verificar si el aspecto ya existe
                existing_aspects = supabase.table("aspects").select("*").eq("phase_id", phase_id).eq("name", aspect).eq("type", "red_flag").execute().data
                
                if existing_aspects:
                    print(f"      ✓ Ya existe")
                else:
                    # Crear el aspecto
                    aspect_data = {
                        "phase_id": phase_id,
                        "name": aspect,
                        "type": "red_flag"
                    }
                    
                    supabase.table("aspects").insert(aspect_data).execute()
                    print(f"      ✅ Creado")
        
        print("\n✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
        return True
        
    except Exception as e:
        print(f"❌ Error durante la migración: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    migrate_to_supabase()