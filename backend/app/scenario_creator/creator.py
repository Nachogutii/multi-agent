from typing import Dict, List, Optional, Any
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

        try:
            # 1. Crear escenario
            logger.info("1. Creando escenario...")
            scenario_id = self._get_next_id("scenarios")
            
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
                condition_id = self._get_next_id("conditions")
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
                phase_id = self._get_next_id("phases")
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
                new_id = self.phase_id_mapping[original_id]
                
                # Mapear los IDs de success_phases
                mapped_success = [self.phase_id_mapping[pid] for pid in phase.success_phases]
                mapped_failure = [self.phase_id_mapping[pid] for pid in phase.failure_phases]
                
                logger.info(f"Actualizando fase {new_id}:")
                logger.info(f"  - Success phases: {phase.success_phases} -> {mapped_success}")
                logger.info(f"  - Failure phases: {phase.failure_phases} -> {mapped_failure}")
                
                response = self.service.client.table("phases").update({
                    "success_phases": mapped_success,  # Array de números directamente
                    "failure_phases": mapped_failure   # Array de números directamente
                }).eq("id", new_id).execute()
                
                if not response.data:
                    logger.error(f"❌ Error actualizando referencias de la fase {new_id}")
                    return None

            # 5. Crear relaciones fase-condición
            logger.info("5. Creando relaciones fase-condición...")
            logger.info("Mapeo de IDs actual:")
            logger.info("Fases:")
            for original_id, new_id in self.phase_id_mapping.items():
                logger.info(f"  - Fase ID original {original_id} -> nuevo ID {new_id}")
            logger.info("Condiciones:")
            for original_id, new_id in self.condition_id_mapping.items():
                logger.info(f"  - Condición ID original {original_id} -> nuevo ID {new_id}")

            for pc in scenario_data.phase_conditions:
                # Verificar que tenemos los IDs mapeados
                if pc.phase_id not in self.phase_id_mapping:
                    logger.error(f"❌ Error: No se encontró mapeo para la fase {pc.phase_id}")
                    return None
                if pc.conditions_id not in self.condition_id_mapping:
                    logger.error(f"❌ Error: No se encontró mapeo para la condición {pc.conditions_id}")
                    return None

                phase_id = self.phase_id_mapping[pc.phase_id]
                condition_id = self.condition_id_mapping[pc.conditions_id]
                
                logger.info(f"Creando relación: Fase {pc.phase_id}->{phase_id} con Condición {pc.conditions_id}->{condition_id}")
                
                next_id = self._get_next_id("phase_conditions")
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