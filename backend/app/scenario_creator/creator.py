from typing import Dict, List, Optional, Any, Tuple
from ..services.supabase import SupabasePhasesService
from ..schemas.scenario import ScenarioCreate
import json
import logging

logger = logging.getLogger(__name__)

class ScenarioCreator:
    """Clase para crear escenarios completos en Supabase usando datos ya validados."""

    def __init__(self):
        self.service = SupabasePhasesService()
        self.initialized = self.service.initialize()
        self.phase_id_mapping = {}  # Para mapear IDs de fases
        self.condition_id_mapping = {}  # Para mapear IDs de condiciones
        
        if not self.initialized:
            logger.error("❌ Error: No se pudo inicializar el servicio de Supabase")
            logger.error(f"URL: {'*' * 5}{self.service.url[-4:] if self.service.url else 'No URL'}")
            logger.error(f"Key: {'*' * 5}{self.service.key[-4:] if self.service.key else 'No Key'}")
        else:
            logger.info("✅ Servicio de Supabase inicializado correctamente")

    def _check_table_structure(self):
        """Verifica la estructura de las tablas necesarias."""
        try:
            # Verificar que podemos leer de la tabla scenarios
            response = self.service.client.table("scenarios").select("*").limit(1).execute()
            logger.info("✅ Tabla 'scenarios' accesible")
            logger.info(f"Estructura de la respuesta: {response}")
            if response.data:
                logger.info(f"Ejemplo de registro: {response.data[0]}")
        except Exception as e:
            logger.error(f"❌ Error accediendo a la tabla 'scenarios': {str(e)}")
            if hasattr(e, 'message'):
                logger.error(f"Mensaje de error: {e.message}")
            if hasattr(e, 'code'):
                logger.error(f"Código de error: {e.code}")

    def _get_next_id(self, table_name: str) -> int:
        """Obtiene el siguiente ID disponible para una tabla."""
        try:
            response = self.service.client.table(table_name).select("id").execute()
            existing_ids = set(item['id'] for item in response.data if item.get('id') is not None)
            
            if not existing_ids:
                return 1
                
            next_id = 1
            while next_id in existing_ids:
                next_id += 1
                
            return next_id
        except Exception as e:
            logger.error(f"❌ Error obteniendo siguiente ID para {table_name}: {str(e)}")
            return 1

    def _prepare_scenario_creation(self, scenario_data: ScenarioCreate) -> Tuple[bool, str, Dict]:
        """
        Prepara y valida todos los datos necesarios para crear el escenario.
        Retorna (éxito, mensaje de error, diccionario con IDs)
        """
        try:
            # Preparar todos los IDs necesarios
            ids = {
                "scenario_id": self._get_next_id("scenarios"),
                "condition_ids": {},  # Mapeo de ID original a nuevo ID
                "phase_ids": {},      # Mapeo de ID original a nuevo ID
                "phase_condition_ids": []  # Lista de IDs para phase_conditions
            }

            # Validar que hay al menos una fase
            if not scenario_data.phases:
                return False, "The scenario must have at least one phase", {}

            # Validar que hay al menos una condición
            if not scenario_data.conditions:
                return False, "The scenario must have at least one condition", {}

            # Preparar IDs para condiciones
            for condition in scenario_data.conditions:
                if not condition.description.strip():
                    return False, f"Condition {condition.id} has an empty description", {}
                new_id = self._get_next_id("conditions")
                ids["condition_ids"][condition.id] = new_id

            # Preparar IDs para fases
            for phase in scenario_data.phases:
                if not phase.name.strip():
                    return False, f"Phase {phase.id} has an empty name", {}
                if not phase.system_prompt.strip():
                    return False, f"Phase {phase.id} ({phase.name}) has an empty system prompt", {}
                new_id = self._get_next_id("phases")
                ids["phase_ids"][phase.id] = new_id

            # Preparar IDs para phase_conditions
            for _ in scenario_data.phase_conditions:
                ids["phase_condition_ids"].append(self._get_next_id("phase_conditions"))

            # Validar que todos los IDs de fase referenciados existen
            for phase in scenario_data.phases:
                for phase_id in phase.success_phases:
                    if phase_id not in ids["phase_ids"]:
                        return False, f"Error in phase '{phase.name}': Success phase {phase_id} does not exist", {}
                    if phase_id == phase.id:
                        return False, f"Error in phase '{phase.name}': A phase cannot have itself as a success phase", {}

                for phase_id in phase.failure_phases:
                    if phase_id not in ids["phase_ids"]:
                        return False, f"Error in phase '{phase.name}': Failure phase {phase_id} does not exist", {}
                    if phase_id == phase.id:
                        return False, f"Error in phase '{phase.name}': A phase cannot have itself as a failure phase", {}

            # Validar que todas las condiciones referenciadas existen
            for pc in scenario_data.phase_conditions:
                if pc.phase_id not in ids["phase_ids"]:
                    phase_name = next((p.name for p in scenario_data.phases if p.id == pc.phase_id), f"ID {pc.phase_id}")
                    return False, f"Error in phase conditions: Phase '{phase_name}' does not exist", {}
                
                if pc.conditions_id not in ids["condition_ids"]:
                    condition_desc = next((c.description for c in scenario_data.conditions if c.id == pc.conditions_id), f"ID {pc.conditions_id}")
                    return False, f"Error in phase conditions: Condition '{condition_desc}' does not exist", {}

            # Validar que cada fase tiene al menos una condición
            phases_with_conditions = {pc.phase_id for pc in scenario_data.phase_conditions}
            for phase in scenario_data.phases:
                if phase.id not in phases_with_conditions:
                    return False, f"Phase '{phase.name}' has no conditions assigned", {}

            return True, "", ids

        except Exception as e:
            return False, f"Unexpected error preparing scenario creation: {str(e)}", {}

    def create_scenario_from_validated_data(self, scenario_data: ScenarioCreate) -> Optional[int]:
        """
        Crea un escenario completo a partir de datos ya validados por Pydantic.

        Args:
            scenario_data (ScenarioCreate): Datos validados del escenario

        Returns:
            Optional[int]: ID del escenario creado o None si hay error
        """
        if not self.initialized or not self.service.client:
            logger.error("⚠️ Supabase client not initialized")
            return None

        # Primero validamos y preparamos todos los datos
        success, error_msg, ids = self._prepare_scenario_creation(scenario_data)
        if not success:
            logger.error(f"❌ Error en la validación: {error_msg}")
            return None

        try:
            # 1. Crear escenario
            logger.info("1. Creando escenario...")
            scenario_id = ids["scenario_id"]
            
            response = self.service.client.table("scenarios").insert({
                "id": scenario_id,
                "name": scenario_data.scenario.name,
                "system_prompt": scenario_data.scenario.system_prompt
            }).execute()

            if not response.data or not response.data[0].get('id'):
                logger.error("❌ Error: No se pudo crear el escenario")
                return None

            logger.info(f"✅ Escenario creado con ID: {scenario_id}")

            # 2. Crear condiciones
            logger.info("2. Creando condiciones...")
            for condition in scenario_data.conditions:
                condition_id = ids["condition_ids"][condition.id]
                response = self.service.client.table("conditions").insert({
                    "id": condition_id,
                    "description": condition.description
                }).execute()
                
                if response.data and response.data[0].get('id'):
                    self.condition_id_mapping[condition.id] = condition_id
                    logger.info(f"✅ Condición creada: ID original {condition.id} -> nuevo ID {condition_id}")
                else:
                    logger.error(f"❌ Error creando condición {condition.id}")
                    return None

            # 3. Crear fases (primero sin success/failure phases)
            logger.info("3. Creando fases...")
            for phase in scenario_data.phases:
                phase_id = ids["phase_ids"][phase.id]
                response = self.service.client.table("phases").insert({
                    "id": phase_id,
                    "name": phase.name,
                    "system_prompt": phase.system_prompt,
                    "success_phases": [],  # Array vacío de números
                    "failure_phases": [],  # Array vacío de números
                    "scenario_id": scenario_id
                }).execute()
                
                if response.data and response.data[0].get('id'):
                    self.phase_id_mapping[phase.id] = phase_id
                    logger.info(f"✅ Fase creada: {phase.name} (ID original {phase.id} -> nuevo ID {phase_id})")
                else:
                    logger.error(f"❌ Error creando fase {phase.id}")
                    return None

            # 4. Actualizar las referencias de las fases
            logger.info("4. Actualizando referencias entre fases...")
            for phase in scenario_data.phases:
                original_id = phase.id
                new_id = ids["phase_ids"][original_id]
                
                # Mapear los IDs de success_phases y failure_phases
                mapped_success = [ids["phase_ids"][pid] for pid in phase.success_phases]
                mapped_failure = [ids["phase_ids"][pid] for pid in phase.failure_phases]
                
                logger.info(f"Actualizando fase {new_id}:")
                logger.info(f"  - Success phases: {phase.success_phases} -> {mapped_success}")
                logger.info(f"  - Failure phases: {phase.failure_phases} -> {mapped_failure}")
                
                response = self.service.client.table("phases").update({
                    "success_phases": mapped_success,
                    "failure_phases": mapped_failure
                }).eq("id", new_id).execute()
                
                if not response.data:
                    logger.error(f"❌ Error actualizando referencias de la fase {new_id}")
                    return None

            # 5. Crear relaciones fase-condición
            logger.info("5. Creando relaciones fase-condición...")
            for i, pc in enumerate(scenario_data.phase_conditions):
                phase_id = ids["phase_ids"][pc.phase_id]
                condition_id = ids["condition_ids"][pc.conditions_id]
                next_id = ids["phase_condition_ids"][i]
                
                logger.info(f"Creando relación: Fase {pc.phase_id}->{phase_id} con Condición {pc.conditions_id}->{condition_id}")
                
                response = self.service.client.table("phase_conditions").insert({
                    "id": next_id,
                    "phase_id": phase_id,
                    "conditions_id": condition_id
                }).execute()
                
                if not response.data:
                    logger.error(f"❌ Error creando relación fase {phase_id} - condición {condition_id}")
                    return None
                
                logger.info(f"✅ Relación creada: Fase {phase_id} -> Condición {condition_id}")

            logger.info("✅ Escenario creado exitosamente")
            return scenario_id

        except Exception as e:
            logger.error(f"❌ Error creando escenario: {str(e)}")
            return None 