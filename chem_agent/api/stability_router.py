"""稳定性预测 API。"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from chem_agent.stability import StabilityRequest, StabilityResult, StabilityPredictor
from chem_agent.auth.dependencies import require_permission
from chem_agent.auth.models import UserOut

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/stability", tags=["Stability"])

@router.post("/predict", response_model=StabilityResult)
async def predict_stability(req: StabilityRequest, _user: UserOut = Depends(require_permission("stability:read"))):
    try: return StabilityPredictor().predict(req)
    except Exception as e: raise HTTPException(500, str(e))
