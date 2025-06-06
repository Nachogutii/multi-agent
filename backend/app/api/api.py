from fastapi import APIRouter
from .endpoints import scenarios

api_router = APIRouter()
api_router.include_router(scenarios.router, prefix="/api", tags=["scenarios"]) 