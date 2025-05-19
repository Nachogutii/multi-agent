import random
import sys
import os
from typing import Dict
from openai import AzureOpenAI
from dotenv import load_dotenv

from agents.customer import CustomerAgent
from agents.evaluator import ObserverCoach
from agents.conversation_phase import ConversationPhaseManager
from agents.Orchestrator import Orchestrator
from phase_config import ConversationPhaseConfig
from utils.supabase_service import get_scenarios, get_scenario_by_id, get_phases_for_scenario, get_aspects_for_phase

class AzureConnection:
    def __init__(self):
        load_dotenv()
        self.endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        self.api_key = os.environ.get("AZURE_OPENAI_KEY")
        self.deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
        self.client = None
        print(f"Deployment set to: {self.deployment}")

    def initialize(self) -> bool:
        try:
            if not self.endpoint or not self.api_key:
                raise ValueError("Azure OpenAI credentials not found in environment variables")

            self.client = AzureOpenAI(
                api_key=self.api_key,
                api_version="2024-10-21",
                azure_endpoint=self.endpoint
            )

            self.test_connection()
            return True

        except Exception as e:
            print("\n❌ Error initializing Azure OpenAI:")
            print(f"Error: {str(e)}")
            return False

    def test_connection(self) -> bool:
        try:
            if not self.client:
                raise ValueError("Azure OpenAI client not initialized")

            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "You are a test assistant."},
                    {"role": "user", "content": "Say 'hello'"}
                ],
                max_tokens=10
            )

            print("\n✅ Successfully connected to Azure OpenAI!")
            print(f"Test response: {response.choices[0].message.content}")
            return True

        except Exception as e:
            print("\n❌ Error connecting to Azure OpenAI:")
            print(f"Error: {str(e)}")
            return False

    def get_client(self) -> AzureOpenAI:
        if not self.client:
            raise ValueError("Azure OpenAI client not initialized")
        return self.client

def load_scenario_from_supabase(scenario_id=None):
    """Carga un escenario completo (con fases y aspectos) desde Supabase"""
    try:
        print("\n📋 INICIANDO CARGA DE ESCENARIO DESDE SUPABASE...")
        
        # Si no se proporciona ID, obtén el primer escenario
        if not scenario_id:
            print("🔍 No se proporcionó ID de escenario, buscando el primero disponible...")
            scenarios = get_scenarios()
            if not scenarios:
                print("⚠️ No hay escenarios en la base de datos. Usando escenario por defecto.")
                return None
            
            print(f"✅ Encontrados {len(scenarios)} escenarios")
            scenario_id = scenarios[0]["id"]
            print(f"✅ Usando el primer escenario encontrado: ID={scenario_id}")
        
        # Carga el escenario
        print(f"🔍 Cargando detalles del escenario ID={scenario_id}...")
        scenario = get_scenario_by_id(scenario_id)
        if not scenario:
            print(f"⚠️ No se encontró el escenario con ID: {scenario_id}")
            return None
        
        # Verificar que el escenario tenga todos los campos necesarios
        required_scenario_fields = ["name", "description", "initial_prompt"]
        missing_fields = [field for field in required_scenario_fields if field not in scenario]
        if missing_fields:
            print(f"⚠️ El escenario no tiene todos los campos requeridos. Falta: {missing_fields}")
            # Intentar reparar campos faltantes
            for field in missing_fields:
                if field == "name":
                    scenario["name"] = "Default Scenario"
                elif field == "description":
                    scenario["description"] = "No description provided"
                elif field == "initial_prompt":
                    scenario["initial_prompt"] = "Hello, how can I help you?"
            print("  🔧 Campos faltantes reparados en el escenario")
            
        # Verificar si el escenario tiene contexto
        if "context" not in scenario or not scenario["context"]:
            print("⚠️ El escenario no tiene contexto definido en Supabase")
            # Añadir un contexto por defecto
            scenario["context"] = """
            **B. Customer Profile:**
            - Customer is Rachel Sanchez, using Microsoft 365 and interested in Copilot.
            - She's a marketing professional looking to improve workflow efficiency.
            - Has some experience with Microsoft 365 but is curious about new Copilot features.
            """
            print("  🔧 Se ha añadido un contexto por defecto al escenario")
        else:
            print(f"✅ Contexto del escenario cargado: {len(scenario['context'])} caracteres")
            preview = scenario['context'][:200] + "..." if len(scenario['context']) > 200 else scenario['context']
            print(f"📄 PREVIEW DEL CONTEXTO DE SUPABASE:\n{preview}")
        
        # Carga las fases
        print(f"🔍 Cargando fases del escenario...")
        phases = get_phases_for_scenario(scenario_id)
        if not phases:
            print(f"⚠️ El escenario no tiene fases configuradas.")
            return None
        
        print(f"✅ Encontradas {len(phases)} fases para el escenario")
        
        # Para cada fase, añade los aspectos
        print(f"🔍 Cargando aspectos para {len(phases)} fases...")
        valid_phases = []
        
        for i, phase in enumerate(phases):
            phase_id = phase.get("id")
            if not phase_id:
                print(f"⚠️ Fase #{i+1} no tiene ID, saltando...")
                continue
                
            print(f"  - Cargando aspectos para fase '{phase.get('name', 'Sin nombre')}' (ID={phase_id})...")
            aspects = get_aspects_for_phase(phase_id)
            
            # Verificar campos obligatorios en la fase
            required_fields = ["name", "system_prompt", "on_success", "on_failure"]
            missing = [k for k in required_fields if k not in phase]
            
            if missing:
                print(f"⚠️ La fase {phase.get('name', 'Sin nombre')} no tiene todos los campos requeridos. Falta: {missing}")
                # Intenta reparar los campos faltantes
                for field in missing:
                    if field == "name":
                        phase["name"] = f"Phase_{i+1}"
                    elif field == "system_prompt":
                        phase["system_prompt"] = "You are a helpful assistant."
                    elif field == "on_success":
                        # Si es la última fase, transiciona a sí misma, sino a la siguiente
                        phase["on_success"] = phase.get("name", f"Phase_{i+1}") if i == len(phases) - 1 else phases[i+1].get("name", f"Phase_{i+2}")
                    elif field == "on_failure":
                        # Por defecto, transiciona a sí misma
                        phase["on_failure"] = phase.get("name", f"Phase_{i+1}")
                
                print(f"  🔧 Campos faltantes reparados para fase '{phase.get('name', 'Sin nombre')}'")
            
            # Agrupar aspectos por tipo
            phase["critical_aspects"] = [a["name"] for a in aspects if a["type"] == "critical"]
            phase["optional_aspects"] = [a["name"] for a in aspects if a["type"] == "optional"]
            phase["red_flags"] = [a["name"] for a in aspects if a["type"] == "red_flag"]
            
            print(f"    ✅ Cargados aspectos: {len(phase['critical_aspects'])} críticos, " +
                  f"{len(phase['optional_aspects'])} opcionales, {len(phase['red_flags'])} red flags")
            
            # Solo añadir fases válidas
            valid_phases.append(phase)
        
        if not valid_phases:
            print("⚠️ No se pudo cargar ninguna fase válida para el escenario.")
            return None
        
        print("📋 CARGA DE ESCENARIO COMPLETA")
        
        return {
            "scenario": scenario,
            "phases": valid_phases
        }
    except Exception as e:
        print(f"❌ Error cargando escenario desde Supabase: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

class RoleplaySystem:
    def __init__(self):
        self.scenario = None
        self.customer_agent = None
        self.observer = None
        self.conversation_history = []
        self.azure = AzureConnection()

    def initialize(self) -> bool:
        return self.azure.initialize()

    def setup_scenario(self, scenario_id=None):
        # Intentar cargar desde Supabase
        scenario_data = load_scenario_from_supabase(scenario_id)
        
        # Variables para almacenar el contexto del escenario y la configuración de fases
        scenario_context = None
        phases_config = None
        
        # Si falla, usar escenario predeterminado
        if not scenario_data:
            print("⚠️ Usando escenario predeterminado.")
            self.scenario = {
                "title": "Copilot Welcome",
                "description": "Customer is already using Microsoft 365 and is exploring how Copilot can improve her workflow.",
                "initial_query": "Hi, I'm Rachel. I just got Copilot and was curious how to get the most out of it."
            }
        else:
            # Usa el escenario de Supabase
            scenario = scenario_data["scenario"]
            self.scenario = {
                "title": scenario["name"],
                "description": scenario["description"],
                "initial_query": scenario["initial_prompt"]
            }
            
            # Guardar el contexto del escenario
            scenario_context = scenario.get("context", "")
            if scenario_context:
                print(f"✅ Contexto del escenario cargado ({len(scenario_context)} caracteres)")
            else:
                print("⚠️ El escenario no tiene contexto definido en Supabase")
            
            # Crear la configuración de fases
            print("🔧 Creando configuración de fases desde datos del escenario...")
            phases_config = ConversationPhaseConfig(scenario_data["phases"])
            print(f"✅ Configuración de fases creada con {len(phases_config.phases)} fases")
        
        # IMPORTANTE: Primero crear la configuración de fases y luego inicializar los agentes
        if not phases_config and scenario_data and scenario_data["phases"]:
            # Si tenemos datos de fases pero no se creó la configuración, intentarlo de nuevo
            try:
                phases_config = ConversationPhaseConfig(scenario_data["phases"])
                print(f"✅ Configuración de fases re-creada con {len(phases_config.phases)} fases")
            except Exception as e:
                print(f"❌ Error al crear la configuración de fases: {str(e)}")
                # Si falla, crear una configuración vacía
                phases_config = ConversationPhaseConfig()
                
        # Inicializar el observer con la configuración de fases si la tenemos
        self.observer = ObserverCoach(
            azure_client=self.azure.get_client(),
            deployment=self.azure.deployment
        )
        
        # Si tenemos la configuración de fases, establecerla en el phase_manager
        if phases_config:
            print(f"🔧 Estableciendo configuración de fases en phase_manager con {len(phases_config.phases)} fases...")
            self.observer.phase_manager.config = phases_config
            # Verificar que se estableció correctamente
            print(f"✅ Configuración establecida. Fases disponibles: {self.observer.phase_manager.config.phase_order}")
        
        # Luego inicializa el customer agent, para que use el mismo phase_manager
        self.customer_agent = CustomerAgent(
            azure_client=self.azure.get_client(),
            deployment=self.azure.deployment,
            scenario_context=scenario_context,
            phase_config=self.observer.phase_manager.config
        )

        # Crear el orchestrator después de los otros agentes
        self.orchestrator = Orchestrator(
            azure_client=self.azure.get_client(),
            deployment=self.azure.deployment,
            shared_observer=self.observer,
            scenario_context=scenario_context
        )

        self.conversation_history = []

        return {
            "scenario": self.scenario["title"],
            "description": self.scenario["description"],
            "initial_query": self.scenario["initial_query"]
        }

    def process_user_message(self, message: str) -> str:
        customer_response = self.customer_agent.generate_response(message)
        self.observer.add_interaction(message, customer_response)
        return customer_response

# === FASTAPI MODE ===

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    text: str

roleplay_system = RoleplaySystem()
roleplay_system.initialize()
roleplay_system.setup_scenario()

# Ya no es necesario crear un nuevo orchestrator aquí porque ya se crea en setup_scenario
# orchestrator = Orchestrator(
#    azure_client=roleplay_system.azure.get_client(),
#    deployment=roleplay_system.azure.deployment,
#    shared_observer=roleplay_system.observer
# )

@app.post("/api/chat")
def chat(msg: Message):
    response = roleplay_system.orchestrator.process_user_input(msg.text)
    # Get the phase directly from the orchestrator for consistency
    # Note: observer and phase_manager may be out of sync
    current_phase = roleplay_system.orchestrator.phase_manager.get_current_phase()
    print(f"🚨 PHASE RETURNED TO FRONTEND: {current_phase}")
    return {
        "response": response,
        "phase": current_phase,
        "feedback": roleplay_system.observer.summarize_conversation()
    }

@app.get("/api/feedback/structured")
def get_structured_feedback():
    # Ensure we use the observer from the Orchestrator for consistency
    observer = roleplay_system.observer
    
    all_phases_in_history = list({m.get("phase") for m in observer.conversation_history})
    for phase in all_phases_in_history:
        if phase and phase not in observer.phase_scores:
            context = "\n".join([
                f"User: {m['user']}\nCustomer: {m['customer']}"
                for m in observer.conversation_history
                if m.get("phase") == phase
            ])
            if context.strip():
                observer.evaluate_phase(phase, context)

    result = observer.summarize_conversation()
    phase_scores = result.get("phase_scores", {})
    feedback_data = result.get("feedback", {})
    
    # Get the custom score based on fulfilled aspects
    custom_score_data = result.get("custom_score", {})
    custom_score = custom_score_data.get("score", 0)
    custom_score_explanation = custom_score_data.get("explanation", "")
    score_details = custom_score_data.get("details", {})
    
    # Get aspect counters
    aspect_counts = result.get("aspect_counts", {})
    total_critical_aspects = aspect_counts.get("critical_aspects", 0)
    total_optional_aspects = aspect_counts.get("optional_aspects", 0)
    total_red_flags = aspect_counts.get("red_flags", 0)

    suggestions = []
    strengths = []
    opportunities = []
    trainings = []

    if isinstance(feedback_data, dict):
        for f in feedback_data.values():
            if isinstance(f, dict):
                if f.get("suggestion"):
                    suggestions.append(f["suggestion"])
                if f.get("strength"):
                    strengths.append(f["strength"])
                if f.get("opportunity"):
                    opportunities.append(f["opportunity"])
                if f.get("training"):
                    trainings.append(f["training"])

    return {
        "metrics": phase_scores,
        "custom_score": custom_score,
        "custom_score_explanation": custom_score_explanation,
        "score_details": score_details,
        "aspect_counts": {
            "critical": total_critical_aspects,
            "optional": total_optional_aspects,
            "red_flags": total_red_flags
        },
        "suggestions": suggestions,
        "strength": strengths,
        "opportunity": opportunities,
        "training": trainings,
        "issues": opportunities
    }

@app.post("/api/reset")
def reset():
    # Reset the entire RoleplaySystem (agent + observer + scenario)
    new_scenario = roleplay_system.setup_scenario()
    
    # Ya no es necesario crear un nuevo orchestrator aquí porque ya se crea en setup_scenario
    # Verificamos que todo esté correctamente sincronizado
    observer_phase = roleplay_system.observer.phase_manager.get_current_phase()
    orchestrator_phase = roleplay_system.orchestrator.phase_manager.get_current_phase()
    print(f"🔄 RESET - Observer phase: {observer_phase}")
    print(f"🔄 RESET - Orchestrator phase: {orchestrator_phase}")
    print(f"🔄 RESET - Same instance: {roleplay_system.observer.phase_manager is roleplay_system.orchestrator.phase_manager}")

    return {
        "scenario": new_scenario["scenario"],
        "description": new_scenario["description"],
        "initial_query": new_scenario["initial_query"]
    }

@app.get("/api/scenario")
def get_scenario():
    # Devuelve el escenario actualmente cargado
    return {
        "title": roleplay_system.scenario["title"],
        "description": roleplay_system.scenario["description"],
        "initial_query": roleplay_system.scenario["initial_query"]
    }

# Nuevo endpoint para listar todos los escenarios disponibles
@app.get("/api/scenarios")
def list_scenarios():
    scenarios = get_scenarios()
    return scenarios

# Nuevo endpoint para cargar un escenario específico
@app.post("/api/scenario/{scenario_id}")
def load_specific_scenario(scenario_id: str):
    result = roleplay_system.setup_scenario(scenario_id)
    
    # Ya no es necesario crear un nuevo orchestrator aquí porque ya se crea en setup_scenario
    # Verificamos que todo esté correctamente sincronizado
    observer_phase = roleplay_system.observer.phase_manager.get_current_phase()
    orchestrator_phase = roleplay_system.orchestrator.phase_manager.get_current_phase()
    print(f"🔄 SCENARIO LOAD - Observer phase: {observer_phase}")
    print(f"🔄 SCENARIO LOAD - Orchestrator phase: {orchestrator_phase}")
    print(f"🔄 SCENARIO LOAD - Same instance: {roleplay_system.observer.phase_manager is roleplay_system.orchestrator.phase_manager}")
    
    return result

def run_api():
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    run_api()