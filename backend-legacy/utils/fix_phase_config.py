import os
import sys
from pathlib import Path

# Añadir directorio raíz al path
current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
parent_dir = str(current_dir.parent.parent)
sys.path.insert(0, parent_dir)

from dotenv import load_dotenv
from backend.utils.supabase_service import get_scenarios, get_scenario_by_id, get_phases_for_scenario, get_aspects_for_phase
from backend.phase_config import ConversationPhaseConfig

def cargar_escenario():
    """Carga un escenario desde Supabase y crea un ConversationPhaseConfig"""
    load_dotenv()  # Cargar variables de entorno
    
    print("Buscando escenarios en Supabase...")
    scenarios = get_scenarios()
    
    if not scenarios:
        print("No se encontraron escenarios.")
        return
    
    print(f"Se encontraron {len(scenarios)} escenarios.")
    
    # Usar el primer escenario
    scenario_id = scenarios[0]['id']
    scenario = get_scenario_by_id(scenario_id)
    
    if not scenario:
        print(f"No se pudo cargar el escenario con ID {scenario_id}")
        return
    
    print(f"Escenario cargado: {scenario['name']}")
    
    # Cargar fases
    phases = get_phases_for_scenario(scenario_id)
    
    if not phases:
        print("El escenario no tiene fases configuradas.")
        return
    
    print(f"Se cargaron {len(phases)} fases.")
    
    # Cargar aspectos para cada fase
    for phase in phases:
        phase_id = phase.get('id')
        if not phase_id:
            continue
            
        aspects = get_aspects_for_phase(phase_id)
        
        # Agrupar aspectos por tipo
        critical = [a for a in aspects if a.get("type") == "critical"]
        optional = [a for a in aspects if a.get("type") == "optional"]
        red_flags = [a for a in aspects if a.get("type") == "red_flag"]
        
        # Añadir listas de nombres de aspectos al diccionario de la fase
        phase["critical_aspects"] = [a["name"] for a in critical]
        phase["optional_aspects"] = [a["name"] for a in optional]
        phase["red_flags"] = [a["name"] for a in red_flags]
        
        print(f"Fase '{phase.get('name')}': {len(critical)} críticos, {len(optional)} opcionales, {len(red_flags)} red flags")
    
    # Crear PhaseConfig
    try:
        config = ConversationPhaseConfig(phases)
        print("✅ ConversationPhaseConfig creado exitosamente.")
        print(f"Número de fases configuradas: {len(config.phases)}")
        print(f"Orden de fases: {config.phase_order}")
        
        # Verificar cada fase
        for name in config.phase_order:
            phase = config.get_phase(name)
            print(f"\nFase: {name}")
            print(f"  Aspectos críticos: {phase.critical_aspects}")
            print(f"  Aspectos opcionales: {phase.optional_aspects}")
            print(f"  Red flags: {phase.red_flags}")
        
        # Si llegamos aquí, todo está bien
        print("\n✅ La carga de escenarios y fases funciona correctamente!")
        return config
    except Exception as e:
        print(f"❌ Error al crear ConversationPhaseConfig: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("=== PROBANDO CARGA DE ESCENARIO Y CREACIÓN DE PHASE CONFIG ===")
    config = cargar_escenario()
    if config:
        print("✅ Prueba completada con éxito.")
    else:
        print("❌ La prueba ha fallado.") 