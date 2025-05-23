from typing import Dict, List, Optional, Any
from supabase import create_client, Client
import os
from dotenv import load_dotenv
class SupabasePhasesService:
    """Service for interacting with phases and red_flags tables in Supabase."""

    def __init__(self):
        """Initialize the Supabase service."""
        load_dotenv()
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        self.url = supabase_url
        self.key = supabase_key
        self.client: Optional[Client] = None

    def initialize(self) -> bool:
        """
        Initialize the Supabase client.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            if not self.url or not self.key:
                print("⚠️ Supabase credentials not found in environment variables")
                return False

            self.client = create_client(self.url, self.key)
            return True

        except Exception as e:
            print(f"❌ Error initializing Supabase: {str(e)}")
            return False

    def get_red_flags(self) -> List[str]:
        """
        Get all red flags from Supabase.

        Returns:
            List[str]: List of red flag descriptions
        """
        if not self.client:
            print("⚠️ Supabase client not initialized")
            return []

        try:
            response = self.client.table("red_flags").select("*").execute()
            red_flags = [item["description"] for item in response.data]
            return red_flags
        except Exception as e:
            print(f"❌ Error getting red flags: {str(e)}")
            return []

    def get_all_phases(self) -> List[Dict[str, Any]]:
        """
        Get all phases from Supabase.

        Returns:
            List[Dict[str, Any]]: List of phases with their success and failure phases
        """
        if not self.client:
            print("⚠️ Supabase client not initialized")
            return []

        try:
            response = self.client.table("phases").select("*").execute()
            phases = response.data
            return phases
        except Exception as e:
            print(f"❌ Error getting phases: {str(e)}")
            return []

    def get_phase_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a phase by its name including success_phases and failure_phases IDs.

        Args:
            name (str): Name of the phase

        Returns:
            Optional[Dict[str, Any]]: Phase data or None if not found
        """
        if not self.client:
            print("⚠️ Supabase client not initialized")
            return None

        try:
            response = self.client.table("phases").select("*").eq("name", name).execute()
            if not response.data:
                return None
            phase_data = response.data[0]
            return phase_data
        except Exception as e:
            print(f"❌ Error getting phase by name: {str(e)}")
            return None

    def get_phase_conditions(self, phase_id: int) -> List[str]:
        """
        Get conditions for a specific phase.

        Args:
            phase_id (int): ID of the phase

        Returns:
            List[str]: List of condition descriptions
        """
        if not self.client:
            print("⚠️ Supabase client not initialized")
            return []

        try:
            # First, get condition IDs linked to this phase from phase_conditions table
            response = self.client.table("phase_conditions").select("conditions_id").eq("phase_id", phase_id).execute()
            if not response.data:
                return []
            
            # Extract condition IDs
            condition_ids = [item["conditions_id"] for item in response.data]
            
            # If no conditions found, return empty list
            if not condition_ids:
                return []
                
            # Get condition descriptions from conditions table
            conditions_response = self.client.table("conditions").select("description").in_("id", condition_ids).execute()
            
            # Extract descriptions
            conditions = [item["description"] for item in conditions_response.data]
            return conditions
        except Exception as e:
            print(f"❌ Error getting conditions for phase {phase_id}: {str(e)}")
            return []

    def get_success_phase_conditions(self, phase_name: str) -> List[str]:
        """
        Get conditions from success phases of the given phase.

        Args:
            phase_name (str): Name of the current phase

        Returns:
            List[str]: List of conditions from all success phases
        """
        if not self.client:
            print("⚠️ Supabase client not initialized")
            return []

        try:
            # Get the current phase data
            current_phase = self.get_phase_by_name(phase_name)
            if not current_phase:
                print(f"⚠️ Phase '{phase_name}' not found")
                return []
            
            # Get success phase IDs
            success_phases = current_phase.get("success_phases", [])
            
            # If success_phases is a string (like "{4,5}"), parse it
            if isinstance(success_phases, str):
                success_phases = self._parse_phase_ids(success_phases)
            
            print(f"[DEBUG] Success phases for '{phase_name}': {success_phases}")
            
            # Get conditions for all success phases
            all_conditions = []
            for phase_id in success_phases:
                conditions = self.get_phase_conditions(phase_id)
                all_conditions.extend(conditions)
            
            return all_conditions
        except Exception as e:
            print(f"❌ Error getting success phase conditions for {phase_name}: {str(e)}")
            return []

    def _parse_phase_ids(self, phase_ids_str: str) -> List[int]:
        """
        Parse phase IDs from string format "{1,2,3}" to list of integers.

        Args:
            phase_ids_str (str): String representation of phase IDs

        Returns:
            List[int]: List of phase IDs as integers
        """
        try:
            # Remove curly braces and split by comma
            if not phase_ids_str or phase_ids_str == "{}":
                return []
            
            # Handle various formats like "{1,2}", "{1,2]", etc.
            clean_str = phase_ids_str.replace("{", "").replace("}", "").replace("[", "").replace("]", "")
            if not clean_str:
                return []
                
            return [int(id_str) for id_str in clean_str.split(",") if id_str.strip()]
        except Exception as e:
            print(f"❌ Error parsing phase IDs '{phase_ids_str}': {str(e)}")
            return []
        
    def get_scenario_context(self) -> str:
        """
        Obtiene el contexto del escenario desde la columna system_prompt de la tabla scenarios.

        Returns:
            str: El system_prompt del escenario o un string vacío si no se encuentra.
        """
        if not self.client:
            print("⚠️ Supabase client not initialized")
            return ""

        try:
            # Obtener el primer escenario disponible
            response = self.client.table("scenarios").select("system_prompt").limit(1).execute()
            
            if not response.data:
                print("⚠️ No se encontraron escenarios en la base de datos")
                return ""
                
            return response.data[0].get("system_prompt", "")
            
        except Exception as e:
            print(f"❌ Error obteniendo el contexto del escenario: {str(e)}")
            return ""

# Example usage
if __name__ == "__main__":
    service = SupabasePhasesService()
    if service.initialize():
        print("Red Flags:")
        print(service.get_red_flags())
        print("\nAll Phases:")
        for phase in service.get_all_phases():
            print(phase)
        print("\nWelcome Phase:")
        print(service.get_phase_by_name("welcome"))
        print("\nSuccess Phase Conditions for Welcome Phase:")
        print(service.get_success_phase_conditions("welcome"))
