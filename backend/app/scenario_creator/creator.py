from typing import Dict, List, Optional, Any
from ..services.supabase import SupabasePhasesService

class ScenarioCreator:
    """Clase para crear escenarios completos en Supabase."""

    def __init__(self):
        self.service = SupabasePhasesService()
        self.initialized = self.service.initialize()
        self.id_mapping = {}  # Para mapear IDs originales a los nuevos IDs generados
        
        if not self.initialized:
            print("❌ Error: No se pudo inicializar el servicio de Supabase")
            print(f"URL: {'*' * 5}{self.service.url[-4:] if self.service.url else 'No URL'}")
            print(f"Key: {'*' * 5}{self.service.key[-4:] if self.service.key else 'No Key'}")
        else:
            print("✅ Servicio de Supabase inicializado correctamente")
            self._check_table_structure()

    def _check_table_structure(self):
        """Verifica la estructura de las tablas necesarias."""
        try:
            # Verificar que podemos leer de la tabla scenarios
            response = self.service.client.table("scenarios").select("*").limit(1).execute()
            print("✅ Tabla 'scenarios' accesible")
            print(f"Estructura de la respuesta: {response}")
            if response.data:
                print(f"Ejemplo de registro: {response.data[0]}")
        except Exception as e:
            print(f"❌ Error accediendo a la tabla 'scenarios': {str(e)}")
            if hasattr(e, 'message'):
                print(f"Mensaje de error: {e.message}")
            if hasattr(e, 'code'):
                print(f"Código de error: {e.code}")

    def _get_next_id(self, table_name: str) -> int:
        """
        Obtiene el siguiente ID disponible para una tabla, asegurando que no exista.
        
        Args:
            table_name (str): Nombre de la tabla
            
        Returns:
            int: Siguiente ID disponible
        """
        try:
            # Obtener todos los IDs existentes
            response = self.service.client.table(table_name).select("id").execute()
            existing_ids = set(item['id'] for item in response.data if item.get('id') is not None)
            
            if not existing_ids:
                return 1
                
            # Encontrar el primer ID disponible
            next_id = 1
            while next_id in existing_ids:
                next_id += 1
                
            return next_id
        except Exception as e:
            print(f"❌ Error obteniendo siguiente ID para {table_name}: {str(e)}")
            return 1

    def create_scenario(self, scenario_data: Dict[str, Any]) -> Optional[int]:
        """
        Crea un nuevo escenario en Supabase.

        Args:
            scenario_data (Dict[str, Any]): Datos del escenario que incluye nombre y system_prompt

        Returns:
            Optional[int]: ID del escenario creado o None si hay error
        """
        if not self.initialized or not self.service.client:
            print("⚠️ Supabase client not initialized")
            return None

        try:
            # Obtener el siguiente ID disponible
            next_id = self._get_next_id("scenarios")
            print(f"Siguiente ID disponible para scenarios: {next_id}")

            print(f"Intentando crear escenario con datos: {scenario_data}")
            response = self.service.client.table("scenarios").insert({
                "id": next_id,
                "name": scenario_data["name"],
                "system_prompt": scenario_data["system_prompt"]
            }).execute()
            
            print(f"Respuesta completa de Supabase: {response}")
            print(f"Datos de la respuesta: {response.data}")
            
            if response.data and len(response.data) > 0:
                scenario_id = response.data[0].get('id')
                if scenario_id:
                    print(f"✅ Escenario creado exitosamente con ID: {scenario_id}")
                    return scenario_id
                else:
                    print("❌ El escenario se creó pero no se recibió ID")
                    return None
            print("❌ No se recibieron datos en la respuesta de Supabase")
            return None
        except Exception as e:
            print(f"❌ Error creando escenario: {str(e)}")
            if hasattr(e, 'message'):
                print(f"Mensaje de error: {e.message}")
            if hasattr(e, 'code'):
                print(f"Código de error: {e.code}")
            return None

    def create_condition(self, condition_data: Dict[str, Any]) -> Optional[int]:
        """
        Crea una nueva condición en Supabase.

        Args:
            condition_data (Dict[str, Any]): Datos de la condición

        Returns:
            Optional[int]: ID de la condición creada o None si hay error
        """
        if not self.initialized or not self.service.client:
            print("⚠️ Supabase client not initialized")
            return None

        try:
            # Obtener el siguiente ID disponible
            next_id = self._get_next_id("conditions")
            print(f"Siguiente ID disponible para conditions: {next_id}")

            # Omitimos el ID del JSON y usamos el siguiente disponible
            response = self.service.client.table("conditions").insert({
                "id": next_id,
                "description": condition_data["description"]
            }).execute()
            
            if response.data and len(response.data) > 0:
                new_id = response.data[0].get('id')
                if new_id:
                    self.id_mapping[condition_data["id"]] = new_id
                    print(f"✅ Condición creada: ID original {condition_data['id']} -> nuevo ID {new_id}")
                    return new_id
                else:
                    print("❌ La condición se creó pero no se recibió ID")
                    return None
            print("❌ No se recibieron datos en la respuesta de Supabase")
            return None
        except Exception as e:
            print(f"❌ Error creando condición: {str(e)}")
            if hasattr(e, 'message'):
                print(f"Mensaje de error: {e.message}")
            if hasattr(e, 'code'):
                print(f"Código de error: {e.code}")
            return None

    def create_phase(self, phase_data: Dict[str, Any], scenario_id: int) -> Optional[int]:
        """
        Crea una nueva fase en Supabase.

        Args:
            phase_data (Dict[str, Any]): Datos de la fase
            scenario_id (int): ID del escenario al que pertenece la fase

        Returns:
            Optional[int]: ID de la fase creada o None si hay error
        """
        if not self.initialized or not self.service.client:
            print("⚠️ Supabase client not initialized")
            return None

        try:
            # Verificar que todas las condiciones necesarias existen
            for condition_id in phase_data["conditions"]:
                if condition_id not in self.id_mapping:
                    print(f"❌ Error: La condición {condition_id} no existe en el mapeo")
                    return None

            # Obtener el siguiente ID disponible
            next_id = self._get_next_id("phases")
            print(f"Siguiente ID disponible para phases: {next_id}")

            # Crear la fase primero sin los success/failure phases
            response = self.service.client.table("phases").insert({
                "id": next_id,
                "name": phase_data["name"],
                "system_prompt": phase_data["system_prompt"],
                "success_phases": "[]",  # Inicialmente vacío
                "failure_phases": "[]",  # Inicialmente vacío
                "scenario_id": scenario_id
            }).execute()
            
            if response.data and len(response.data) > 0:
                phase_id = response.data[0].get('id')
                if phase_id:
                    self.id_mapping[phase_data["id"]] = phase_id
                    print(f"✅ Fase creada: {phase_data['name']} (ID: {phase_id})")

                    # Crear las relaciones entre fase y condiciones
                    for condition_id in phase_data["conditions"]:
                        mapped_condition_id = self.id_mapping[condition_id]
                        try:
                            self.service.client.table("phase_conditions").insert({
                                "phase_id": phase_id,
                                "conditions_id": mapped_condition_id  # Volvemos a usar conditions_id
                            }).execute()
                            print(f"✅ Relación creada: Fase {phase_id} -> Condición {mapped_condition_id}")
                        except Exception as e:
                            print(f"❌ Error creando relación fase-condición: {str(e)}")
                            return None

                    # Actualizar los arrays de success/failure phases después de que todas las fases estén creadas
                    if "success_phases" in phase_data and phase_data["success_phases"]:
                        success_phases = [self.id_mapping.get(phase_id, phase_id) for phase_id in phase_data["success_phases"]]
                        success_phases_str = "[" + ",".join(map(str, success_phases)) + "]"
                        try:
                            self.service.client.table("phases").update({
                                "success_phases": success_phases_str
                            }).eq("id", phase_id).execute()
                            print(f"✅ Success phases actualizadas para fase {phase_id}: {success_phases_str}")
                        except Exception as e:
                            print(f"❌ Error actualizando success phases: {str(e)}")

                    if "failure_phases" in phase_data and phase_data["failure_phases"]:
                        failure_phases = [self.id_mapping.get(phase_id, phase_id) for phase_id in phase_data["failure_phases"]]
                        failure_phases_str = "[" + ",".join(map(str, failure_phases)) + "]"
                        try:
                            self.service.client.table("phases").update({
                                "failure_phases": failure_phases_str
                            }).eq("id", phase_id).execute()
                            print(f"✅ Failure phases actualizadas para fase {phase_id}: {failure_phases_str}")
                        except Exception as e:
                            print(f"❌ Error actualizando failure phases: {str(e)}")

                    return phase_id
                else:
                    print("❌ La fase se creó pero no se recibió ID")
                    return None
            print("❌ No se recibieron datos en la respuesta de Supabase")
            return None
        except Exception as e:
            print(f"❌ Error creando fase: {str(e)}")
            if hasattr(e, 'message'):
                print(f"Mensaje de error: {e.message}")
            if hasattr(e, 'code'):
                print(f"Código de error: {e.code}")
            return None

    def create_scenario_from_json(self, json_data: Dict[str, Any]) -> Optional[int]:
        """
        Crea un escenario completo a partir de un JSON que incluye escenario, condiciones y fases.

        Args:
            json_data (Dict[str, Any]): Datos completos del escenario en formato JSON

        Returns:
            Optional[int]: ID del escenario creado o None si hay error
        """
        if not self.initialized or not self.service.client:
            print("⚠️ Supabase client not initialized")
            return None

        try:
            # Limpiar el mapeo de IDs al inicio de cada creación
            self.id_mapping = {}

            # 1. Crear escenario
            print("\n1. Creando escenario...")
            scenario_id = self.create_scenario(json_data["scenario"])
            if not scenario_id:
                print("❌ Error: No se pudo crear el escenario")
                return None

            # 2. Crear todas las condiciones primero
            print("\n2. Creando condiciones...")
            all_conditions_created = True
            for condition in json_data["conditions"]:
                condition_id = self.create_condition(condition)
                if not condition_id:
                    print(f"❌ Error: No se pudo crear la condición {condition['id']}")
                    all_conditions_created = False
                    break

            if not all_conditions_created:
                print("❌ Error: No se pudieron crear todas las condiciones")
                return None

            # Imprimir el mapeo de IDs de condiciones para debug
            print("\nMapeo de IDs de condiciones:")
            for original_id, mapped_id in self.id_mapping.items():
                print(f"Condición original {original_id} -> nuevo ID {mapped_id}")

            # 3. Crear todas las fases primero (sin success/failure phases)
            print("\n3. Creando fases...")
            phase_id_mapping = {}  # Mapeo separado para las fases
            all_phases_created = True
            for phase in json_data["phases"]:
                # Crear la fase con arrays vacíos inicialmente
                next_id = self._get_next_id("phases")
                response = self.service.client.table("phases").insert({
                    "id": next_id,
                    "name": phase["name"],
                    "system_prompt": phase["system_prompt"],
                    "success_phases": "[]",
                    "failure_phases": "[]",
                    "scenario_id": scenario_id
                }).execute()

                if response.data and len(response.data) > 0:
                    phase_id = response.data[0].get('id')
                    if phase_id:
                        phase_id_mapping[phase["id"]] = phase_id
                        print(f"✅ Fase creada: {phase['name']} (ID: {phase_id})")
                    else:
                        all_phases_created = False
                        break
                else:
                    all_phases_created = False
                    break

            if not all_phases_created:
                print("❌ Error: No se pudieron crear todas las fases")
                return None

            # 4. Crear las relaciones fase-condición y actualizar success/failure phases
            print("\n4. Creando relaciones y actualizando fases...")
            for phase in json_data["phases"]:
                phase_id = phase_id_mapping[phase["id"]]

                # Crear relaciones fase-condición usando los IDs mapeados correctos
                for condition_id in phase["conditions"]:
                    mapped_condition_id = self.id_mapping[condition_id]  # ID real de la condición
                    try:
                        next_id = self._get_next_id("phase_conditions")
                        print(f"Creando relación: Fase {phase_id} -> Condición {mapped_condition_id} (ID: {next_id})")
                        self.service.client.table("phase_conditions").insert({
                            "id": next_id,
                            "phase_id": phase_id,
                            "conditions_id": mapped_condition_id
                        }).execute()
                        print(f"✅ Relación creada: Fase {phase_id} -> Condición {mapped_condition_id}")
                    except Exception as e:
                        print(f"❌ Error creando relación fase-condición: {str(e)}")
                        return None

                # Actualizar success/failure phases usando el mapeo de fases
                success_phases = [phase_id_mapping[pid] for pid in phase["success_phases"]]
                failure_phases = [phase_id_mapping[pid] for pid in phase["failure_phases"]]
                
                success_phases_str = "[" + ",".join(map(str, success_phases)) + "]"
                failure_phases_str = "[" + ",".join(map(str, failure_phases)) + "]"
                
                try:
                    self.service.client.table("phases").update({
                        "success_phases": success_phases_str,
                        "failure_phases": failure_phases_str
                    }).eq("id", phase_id).execute()
                    print(f"✅ Success/Failure phases actualizadas para fase {phase_id}")
                except Exception as e:
                    print(f"❌ Error actualizando success/failure phases: {str(e)}")
                    return None

            # Actualizar el id_mapping con las fases
            self.id_mapping.update(phase_id_mapping)
            print("\n✅ Escenario creado exitosamente")
            return scenario_id
        except Exception as e:
            print(f"❌ Error creando escenario desde JSON: {str(e)}")
            return None 