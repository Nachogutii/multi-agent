import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Añadir directorio raíz al path para poder importar utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_supabase_connection():
    """Verifica la conexión a Supabase y lista los datos disponibles"""
    print("\n=== VERIFICACIÓN DE CONEXIÓN A SUPABASE ===\n")
    
    # Cargar variables de entorno
    load_dotenv()
    
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Error: No se encontraron las variables de entorno SUPABASE_URL y SUPABASE_KEY")
        return False
    
    print(f"🔑 URL de Supabase: {SUPABASE_URL}")
    print(f"🔑 Key de Supabase: {SUPABASE_KEY[:10]}...{SUPABASE_KEY[-5:]}")
    
    try:
        # Intentar crear cliente
        print("\n🔄 Intentando conectar a Supabase...")
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Conexión a Supabase exitosa")
        
        # Verificar tablas
        print("\n=== VERIFICACIÓN DE TABLAS ===\n")
        
        # 1. Verificar tabla scenarios
        print("\n🔍 Buscando escenarios...")
        scenarios = supabase.table("scenarios").select("*").execute().data
        print(f"✅ Se encontraron {len(scenarios)} escenarios:")
        for s in scenarios:
            print(f"  - ID: {s.get('id')}, Nombre: {s.get('name')}")
            
            # 2. Verificar tabla phases para este escenario
            print(f"\n🔍 Buscando fases para escenario {s.get('id')}...")
            phases = supabase.table("phases").select("*").eq("scenario_id", s.get('id')).execute().data
            print(f"✅ Se encontraron {len(phases)} fases:")
            
            for p in phases:
                print(f"  - ID: {p.get('id')}, Nombre: {p.get('name')}")
                
                # 3. Verificar tabla aspects para esta fase
                print(f"    🔍 Buscando aspectos para fase {p.get('id')}...")
                aspects = supabase.table("aspects").select("*").eq("phase_id", p.get('id')).execute().data
                print(f"    ✅ Se encontraron {len(aspects)} aspectos:")
                
                aspects_by_type = {
                    "critical": [a for a in aspects if a.get('type') == 'critical'],
                    "optional": [a for a in aspects if a.get('type') == 'optional'],
                    "red_flag": [a for a in aspects if a.get('type') == 'red_flag']
                }
                
                for aspect_type, aspect_list in aspects_by_type.items():
                    print(f"      - {len(aspect_list)} aspectos de tipo '{aspect_type}'")
                    for a in aspect_list:
                        print(f"        * {a.get('name')}")
                        
        if not scenarios:
            print("⚠️ No hay escenarios en la base de datos. Es necesario migrar los datos primero.")
            return False
            
        return True
            
    except Exception as e:
        print(f"❌ Error al conectar a Supabase: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_supabase_connection() 