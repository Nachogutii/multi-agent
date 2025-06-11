from fastapi import APIRouter, HTTPException
from ...schemas.scenario import ScenarioCreate
from ...services.supabase import SupabasePhasesService
from ...scenario_creator.creator import ScenarioCreator
from typing import Dict, Any
import logging
import json

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/scenarios")
async def create_scenario(scenario_data: ScenarioCreate):
    """
    Endpoint para crear un nuevo escenario.
    1. Valida el JSON del escenario
    2. Si la validación es exitosa, intenta crear en la base de datos
    """
    try:
        # Log del JSON recibido
        logger.info("\n=== JSON RECIBIDO DEL FRONTEND ===")
        logger.info(json.dumps(scenario_data.model_dump(), indent=2))

        # Validación automática por Pydantic
        logger.info("\n✅ Validación del schema exitosa")
        
        # Mostrar estructura detallada
        logger.info("\n=== ESTRUCTURA DETALLADA ===")
        logger.info(f"\nESCENARIO:")
        logger.info(f"Nombre: {scenario_data.scenario.name}")
        logger.info(f"System Prompt: {scenario_data.scenario.system_prompt}")
        
        logger.info(f"\nCONDICIONES ({len(scenario_data.conditions)}):")
        for cond in scenario_data.conditions:
            logger.info(f"- ID: {cond.id}, Descripción: {cond.description}")
        
        logger.info(f"\nFASES ({len(scenario_data.phases)}):")
        for phase in scenario_data.phases:
            logger.info(f"\nFase ID: {phase.id}")
            logger.info(f"Nombre: {phase.name}")
            logger.info(f"System Prompt: {phase.system_prompt}")
            logger.info(f"Success Phases: {phase.success_phases}")
            logger.info(f"Failure Phases: {phase.failure_phases}")
        
        logger.info(f"\nRELACIONES FASE-CONDICIÓN:")
        for pc in scenario_data.phase_conditions:
            logger.info(f"- Fase {pc.phase_id} -> Condición {pc.conditions_id}")

        # Intentar crear en la base de datos
        logger.info("\n=== CREANDO EN BASE DE DATOS ===")
        creator = ScenarioCreator()
        if not creator.initialized:
            logger.error("❌ Error: Could not initialize database service")
            raise HTTPException(status_code=500, detail="Could not initialize database service")

        scenario_id = creator.create_scenario_from_validated_data(scenario_data)
        
        if not scenario_id:
            logger.error("❌ Error: Could not create scenario in database")
            raise HTTPException(status_code=500, detail="Error creating scenario in database")

        logger.info(f"✅ Scenario successfully created with ID: {scenario_id}")
        return {
            "message": "Scenario successfully created",
            "scenario_id": scenario_id,
            "data": scenario_data.model_dump()
        }

    except HTTPException as e:
        # Re-lanzar excepciones HTTP tal cual
        raise e
    except ValueError as e:
        # Errores de validación de Pydantic
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        # Cualquier otro error
        error_msg = str(e)
        logger.error(f"Error creating scenario: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)

@router.get("/scenarios")
async def get_scenarios():
    """
    Endpoint para obtener todos los escenarios disponibles.
    """
    try:
        service = SupabasePhasesService()
        if not service.initialize():
            raise HTTPException(status_code=500, detail="No se pudo inicializar el servicio de base de datos")

        response = service.client.table("scenarios").select("*").execute()
        if not response.data:
            return []

        return response.data
    except Exception as e:
        logger.error(f"Error obteniendo escenarios: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 