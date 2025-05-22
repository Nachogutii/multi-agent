from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from app.orchestrator.orchestrator import SimpleOrchestrator

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

# Inicializar el orquestrador
orchestrator = SimpleOrchestrator()

@app.post("/api/chat")
def chat(msg: Message):
    result = orchestrator.process_message(msg.text)
    return {
        "response": result["customer_response"],
        "phase": result["phase"],
        "feedback": {
            "observations": result["phase_observations"],
            "accumulated_conditions": result["accumulated_conditions"]
        }
    }

@app.post("/api/reset")
def reset():
    global orchestrator
    # Reiniciar el orquestrador creando una nueva instancia
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
    # Implementación básica para devolver feedback estructurado
    # Esto se puede ampliar según sea necesario
    return {
        "metrics": {},
        "custom_score": 0,
        "custom_score_explanation": "Feedback not yet implemented",
        "score_details": {},
        "aspect_counts": {
            "critical": 0,
            "optional": 0,
            "red_flags": 0
        },
        "suggestions": [],
        "strength": [],
        "opportunity": [],
        "training": [],
        "issues": []
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
