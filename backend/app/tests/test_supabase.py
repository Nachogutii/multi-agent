#!/usr/bin/env python
"""
Test script for Supabase connection and phase condition retrieval
"""

import sys
import os

# Add parent directory to path to allow importing from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from backend.app.services.supabase import SupabasePhasesService
from backend.app.orchestrator.orchestrator import SimpleOrchestrator

def test_supabase_service():
    """Test direct Supabase service functionality"""
    print("\n=== Testing Supabase Service ===")
    service = SupabasePhasesService()
    
    # Test connection
    if service.initialize():
        print("✅ Supabase connection successful")
    else:
        print("❌ Supabase connection failed")
        return False
    
    # Test red flags retrieval
    red_flags = service.get_red_flags()
    print(f"Red flags retrieved: {len(red_flags)}")
    for flag in red_flags:
        print(f"  - {flag}")
    
    # Test phases retrieval
    all_phases = service.get_all_phases()
    print(f"\nPhases retrieved: {len(all_phases)}")
    for phase in all_phases:
        print(f"  - {phase['name']}")
    
    # Test retrieval of specific phase
    welcome_phase = service.get_phase_by_name("welcome")
    if welcome_phase:
        print(f"\nWelcome phase data: {welcome_phase}")
        
        # Test conditions retrieval
        if "id" in welcome_phase:
            phase_id = welcome_phase["id"]
            conditions = service.get_phase_conditions(phase_id)
            print(f"\nConditions for 'welcome' phase (ID: {phase_id}):")
            for condition in conditions:
                print(f"  - {condition}")
    
    return True

def test_orchestrator():
    """Test the orchestrator with Supabase integration"""
    print("\n=== Testing Orchestrator with Supabase Integration ===")
    orchestrator = SimpleOrchestrator()
    
    # Test initial phase conditions
    print("\nInitial phase and conditions:")
    result = orchestrator.process_message("Hello, I'm calling from Microsoft.")
    
    print(f"Current phase: {result['phase']}")
    print(f"Conditions: {result['accumulated_conditions']}")
    print(f"Customer response: {result['customer_response']}")
    
    # Test phase transition
    print("\nTesting phase transition:")
    result = orchestrator.process_message("I'm calling to discuss your business needs and how Microsoft Copilot can help.")
    
    print(f"Current phase: {result['phase']}")
    print(f"New conditions: {result['accumulated_conditions']}")
    print(f"Customer response: {result['customer_response']}")
    
    return True

if __name__ == "__main__":
    # You can set environment variables here if not using .env
    # import os
    # os.environ["SUPABASE_URL"] = "your-supabase-url"  
    # os.environ["SUPABASE_KEY"] = "your-supabase-key"
    
    supabase_test = test_supabase_service()
    if supabase_test:
        test_orchestrator()
    else:
        print("\n❌ Skipping orchestrator test due to Supabase connection failure") 