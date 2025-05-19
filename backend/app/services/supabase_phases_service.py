from typing import Dict, List, Optional, Any
from supabase import create_client, Client
import os
from dotenv import load_dotenv
load_dotenv()

class SupabasePhasesService:
    """Service for interacting with phases and red_flags tables in Supabase."""

    def __init__(self):
        """Initialize the Supabase service."""
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
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
            print("✅ Supabase client initialized successfully")
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
            print(f"✅ Retrieved {len(red_flags)} red flags from Supabase")
            return red_flags
        except Exception as e:
            print(f"❌ Error getting red flags: {str(e)}")
            return []

    def get_all_phases(self) -> List[Dict[str, Any]]:
        """
        Get all phases from Supabase.

        Returns:
            List[Dict[str, Any]]: List of phases
        """
        if not self.client:
            print("⚠️ Supabase client not initialized")
            return []

        try:
            response = self.client.table("phases").select("*").execute()
            phases = response.data
            print(f"✅ Retrieved {len(phases)} phases from Supabase")
            return phases
        except Exception as e:
            print(f"❌ Error getting phases: {str(e)}")
            return []

    def get_phase_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a phase by its name.

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
                print(f"⚠️ No phase found with name '{name}'")
                return None
            print(f"✅ Phase '{name}' retrieved successfully")
            return response.data[0]
        except Exception as e:
            print(f"❌ Error getting phase by name: {str(e)}")
            return None

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