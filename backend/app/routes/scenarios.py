from fastapi import APIRouter, HTTPException
from ..schemas.scenario import ScenarioCreate
from ..services.scenario_service import create_scenario_from_json

router = APIRouter()

@router.post("/scenarios")
async def create_scenario(scenario_data: ScenarioCreate):
    try:
        # Los datos ya están validados por Pydantic en este punto
        result = await create_scenario_from_json(scenario_data.dict())
        if result is None:
            raise HTTPException(status_code=400, detail="Error creating scenario")
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 