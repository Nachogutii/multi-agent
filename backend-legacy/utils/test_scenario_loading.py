import os
import sys
import inspect
from pathlib import Path

# Añadir el directorio padre al path para poder importar módulos
current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
parent_dir = str(current_dir.parent.parent)
sys.path.insert(0, parent_dir)

from dotenv import load_dotenv
from openai import AzureOpenAI
from backend.utils.supabase_service import get_scenarios, get_scenario_by_id, get_phases_for_scenario, get_aspects_for_phase
from backend.phase_config import ConversationPhaseConfig
from backend.agents.conversation_phase import ConversationPhaseManager

def test_supabase_connection():
    print("\n=== PRUEBA DE CONEXIÓN A SUPABASE ===")
    scenarios = get_scenarios()
    print(f"Escenarios encontrados: {len(scenarios)}")
    
    if scenarios:
        print("\nDetalles del primer escenario:")
        for key, value in scenarios[0].items():
            print(f"  {key}: {value}")
    else:
        print("⚠️ No se encontraron escenarios en Supabase.")
    
    return scenarios

def test_phase_loading(scenario_id=None):
    print("\n=== PRUEBA DE CARGA DE FASES ===")
    
    # Si no se proporciona ID, obtener el primero disponible
    if not scenario_id and test_supabase_connection():
        scenario_id = test_supabase_connection()[0]['id']
        print(f"Usando el primer escenario encontrado: ID={scenario_id}")
    
    # Obtener detalles del escenario
    scenario = get_scenario_by_id(scenario_id)
    if not scenario:
        print(f"⚠️ No se encontró el escenario con ID: {scenario_id}")
        return None
    
    print(f"Escenario: {scenario['name']}")
    
    # Obtener fases
    phases = get_phases_for_scenario(scenario_id)
    if not phases:
        print(f"⚠️ El escenario no tiene fases configuradas.")
        return None
    
    print(f"Fases encontradas: {len(phases)}")
    
    # Verificar campos requeridos de las fases
    for i, phase in enumerate(phases):
        print(f"\nFase #{i+1}: {phase.get('name', 'Sin nombre')}")
        
        # Verificar campos obligatorios
        required_fields = ["name", "system_prompt", "on_success", "on_failure"]
        missing = [field for field in required_fields if field not in phase]
        
        if missing:
            print(f"  ⚠️ Faltan campos: {missing}")
        else:
            print("  ✅ Todos los campos requeridos están presentes")
        
        # Cargar aspectos
        phase_id = phase.get("id")
        if not phase_id:
            print("  ⚠️ La fase no tiene ID")
            continue
            
        aspects = get_aspects_for_phase(phase_id)
        critical = [a for a in aspects if a.get("type") == "critical"]
        optional = [a for a in aspects if a.get("type") == "optional"]
        red_flags = [a for a in aspects if a.get("type") == "red_flag"]
        
        print(f"  Aspectos críticos: {len(critical)}")
        for a in critical:
            print(f"    - {a.get('name', 'Sin nombre')}")
        
        print(f"  Aspectos opcionales: {len(optional)}")
        print(f"  Red flags: {len(red_flags)}")
    
    return phases

def test_phase_config_construction(phases):
    print("\n=== PRUEBA DE CONSTRUCCIÓN DE PhaseConfig ===")
    if not phases:
        print("⚠️ No hay fases para construir el PhaseConfig")
        return None
    
    config = ConversationPhaseConfig(phases)
    print(f"✅ PhaseConfig creado correctamente")
    print(f"Fases configuradas: {len(config.phases)}")
    print(f"Orden de fases: {config.phase_order}")
    
    # Verificar cada fase
    for phase_name in config.phase_order:
        phase = config.get_phase(phase_name)
        print(f"\nFase: {phase_name}")
        print(f"  Transición éxito: {phase.success_transition}")
        print(f"  Transición fracaso: {phase.failure_transition}")
        print(f"  Aspectos críticos: {len(phase.critical_aspects)}")
        print(f"  Aspectos opcionales: {len(phase.optional_aspects)}")
        print(f"  Red flags: {len(phase.red_flags)}")
    
    return config

def test_phase_manager(config):
    print("\n=== PRUEBA DE PhaseManager ===")
    if not config:
        print("⚠️ No hay configuración para crear el PhaseManager")
        return None
    
    # Inicializar cliente Azure (solo para pruebas)
    load_dotenv()
    client = AzureOpenAI(
        api_key=os.environ.get("AZURE_OPENAI_KEY"),
        api_version="2024-10-21",
        azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT")
    )
    
    # Crear Phase Manager con la configuración
    phase_manager = ConversationPhaseManager(
        azure_client=client,
        deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
        phase_config=config
    )
    
    print(f"✅ PhaseManager creado correctamente")
    print(f"Fase inicial: {phase_manager.get_current_phase()}")
    print(f"System prompt: {phase_manager.get_system_prompt()[:50]}...")
    
    return phase_manager

if __name__ == "__main__":
    print("=== INICIO DE LA PRUEBA DE CARGA DE ESCENARIOS ===")
    load_dotenv()
    
    # Probar conexión y obtener escenarios
    print("\nVerificando conexión a Supabase...")
    scenarios = test_supabase_connection()
    
    if not scenarios:
        print("\n❌ No se pudieron obtener escenarios de Supabase.")
        print("Verifica las credenciales en el archivo .env:")
        print(f"SUPABASE_URL: {'✅ Configurado' if os.environ.get('SUPABASE_URL') else '❌ No configurado'}")
        print(f"SUPABASE_KEY: {'✅ Configurado' if os.environ.get('SUPABASE_KEY') else '❌ No configurado'}")
        sys.exit(1)
    
    # Probar carga de fases para el primer escenario
    scenario_id = scenarios[0]['id']
    phases = test_phase_loading(scenario_id)
    
    if not phases:
        print("\n❌ No se pudieron cargar las fases del escenario.")
        sys.exit(1)
    
    # Probar construcción de PhaseConfig
    config = test_phase_config_construction(phases)
    
    if not config:
        print("\n❌ No se pudo construir el PhaseConfig.")
        sys.exit(1)
    
    # Probar creación de PhaseManager
    phase_manager = test_phase_manager(config)
    
    if not phase_manager:
        print("\n❌ No se pudo crear el PhaseManager.")
        sys.exit(1)
    
    print("\n=== PRUEBA COMPLETADA CON ÉXITO ===")
    print("✅ El sistema de carga de escenarios funciona correctamente.") 