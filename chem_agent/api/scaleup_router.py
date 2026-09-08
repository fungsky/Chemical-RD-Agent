"""工艺放大 API。"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from chem_agent.scaleup import ScaleUpRequest, ScaleUpResult, ScaleUpCalculator
from chem_agent.auth.dependencies import require_permission
from chem_agent.auth.models import UserOut

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/scaleup", tags=["ScaleUp"])

@router.post("/calculate", response_model=ScaleUpResult)
async def calc_scaleup(req: ScaleUpRequest, _user: UserOut = Depends(require_permission("scaleup:read"))):
    try: return ScaleUpCalculator().calculate(req)
    except Exception as e: raise HTTPException(500, str(e))
