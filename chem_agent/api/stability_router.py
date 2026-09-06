"""稳定性预测 API。"""
import logging
from fastapi import APIRouter, HTTPException
from chem_agent.stability import StabilityRequest, StabilityResult, StabilityPredictor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/stability", tags=["Stability"])

@router.post("/predict", response_model=StabilityResult)
async def predict_stability(req: StabilityRequest):
    try: return StabilityPredictor().predict(req)
    except Exception as e: raise HTTPException(500, str(e))
