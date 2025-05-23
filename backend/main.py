from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging
from typing import Optional

from app.orchestrator.orchestrator import SimpleOrchestrator
from app.agents.feedback import FeedbackAgent

# Configure logging
logging.basicConfig(level=logging.WARNING)
# Set uvicorn access logs to warning level only
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
# Set specific loggers to higher levels
logging.getLogger("uvicorn.error").setLevel(logging.ERROR)

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
    phase: Optional[str] = None

class ResetRequest(BaseModel):
    id: Optional[int] = None

# Inicializar el orquestrador
orchestrator = SimpleOrchestrator()

@app.post("/api/chat")
def chat(msg: Message):
    print(f"[INFO] Received message: {msg.text}, phase: {msg.phase}")
    result = orchestrator.process_message(msg.text)
    
    # Handle red flag case
    if result.get("end"):
        return {
            "response": result.get("customer_response", "This conversation has ended."),
            "phase": result.get("phase", "abrupt_closure"),
            "feedback": {
                "observations": result.get("details", []),
                "accumulated_conditions": []
            }
        }
    
    # Normal case
    return {
        "response": result["customer_response"],
        "phase": result["phase"],
        "feedback": {
            "observations": result["phase_observations"],
            "accumulated_conditions": result["accumulated_conditions"]
        }
    }

@app.post("/api/reset")
def reset(request: ResetRequest):
    global orchestrator
    # Reiniciar el orquestrador creando una nueva instancia, pasando el id si se proporciona
    if request.id is not None:
        orchestrator = SimpleOrchestrator(scenario_id=request.id)
    else:
        orchestrator = SimpleOrchestrator()
    return {
        "scenario": "Customer conversation",
        "description": "Conversation with a potential customer",
        "initial_query": "Hello, how can I help you today?"
    }

@app.get("/api/scenario")
def get_scenario():
    # Devuelve información sobre el escenario actual
    return {
        "title": "Customer conversation",
        "description": "Conversation with a potential customer",
        "initial_query": "Hello, how can I help you today?"
    }

@app.get("/api/feedback/structured")
def get_structured_feedback():
    # Obtener todas las condiciones acumuladas del orquestador
    global_conditions = orchestrator.global_conditions_history
    
    # Obtener todas las condiciones posibles del servicio de fases
    all_conditions = []
    phases = orchestrator.supabase_service.get_all_phases()
    for phase in phases:
        phase_id = phase.get('id')
        if phase_id is not None:
            phase_conditions = orchestrator.supabase_service.get_phase_conditions(phase_id)
            all_conditions.extend(phase_conditions)
    
    # Crear instancia del agente de feedback
    feedback_agent = FeedbackAgent()
    
    # Obtener el historial de conversación del agente del cliente
    conversation_history = orchestrator.customer_agent.conversation_history
    
    # Generar feedback usando todas las condiciones acumuladas
    feedback = feedback_agent.generate_feedback(
        conversation_history="\n".join([msg["content"] for msg in conversation_history]) if conversation_history else "",
        conditions=all_conditions,
        accumulated_conditions=global_conditions,
        optional_aspects=orchestrator.optional_aspects,
        red_flags=orchestrator.red_flags
    )
    
    # Agregar información adicional al feedback
    feedback["conversation_history"] = conversation_history
    feedback["global_conditions"] = global_conditions
    
    return feedback

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="warning")
