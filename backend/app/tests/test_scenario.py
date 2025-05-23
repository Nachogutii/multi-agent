import sys
import os
from pathlib import Path

# Añadir el directorio raíz al path
current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
parent_dir = str(current_dir.parent.parent.parent)
sys.path.insert(0, parent_dir)

from backend.app.services.supabase import SupabasePhasesService

def test_get_scenario():
    print("\n=== PRUEBA DE OBTENCIÓN DE ESCENARIO ===")
    
    # Inicializar el servicio
    service = SupabasePhasesService()
    if not service.initialize():
        print("❌ No se pudo inicializar el cliente de Supabase")
        return
    
    # Obtener el contexto del escenario
    context = service.get_scenario_context()
    
    if context:
        print("\n✅ Contexto del escenario obtenido:")
        print("\n" + "="*50)
        print(context)
        print("="*50)
    else:
        print("\n❌ No se pudo obtener el contexto del escenario")

if __name__ == "__main__":
    test_get_scenario() 