from fastapi import APIRouter, HTTPException
from ...schemas.scenario import ScenarioCreate
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
            logger.error("❌ Error: No se pudo inicializar el servicio de Supabase")
            raise HTTPException(status_code=500, detail="No se pudo inicializar el servicio de base de datos")

        scenario_id = creator.create_scenario_from_validated_data(scenario_data)
        
        if not scenario_id:
            logger.error("❌ Error: No se pudo crear el escenario en la base de datos")
            raise HTTPException(status_code=500, detail="Error creando el escenario en la base de datos")

        logger.info(f"✅ Escenario creado exitosamente con ID: {scenario_id}")
        return {
            "message": "Escenario creado exitosamente",
            "scenario_id": scenario_id,
            "data": scenario_data.model_dump()
        }

    except Exception as e:
        logger.error(f"\n❌ Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) 