"""可持续性评估 API。"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from chem_agent.sustainability import SustainabilityRequest, SustainabilityResult, SustainabilityCalculator
from chem_agent.auth.dependencies import require_permission
from chem_agent.auth.models import UserOut

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/sustainability", tags=["Sustainability"])

@router.post("/assess", response_model=SustainabilityResult)
async def assess_sustainability(req: SustainabilityRequest, _user: UserOut = Depends(require_permission("sustainability:read"))):
    try: return SustainabilityCalculator().calculate(req)
    except Exception as e: raise HTTPException(500, str(e))
