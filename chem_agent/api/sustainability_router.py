"""可持续性评估 API。"""
import logging
from fastapi import APIRouter, HTTPException
from chem_agent.sustainability import SustainabilityRequest, SustainabilityResult, SustainabilityCalculator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/sustainability", tags=["Sustainability"])

@router.post("/assess", response_model=SustainabilityResult)
async def assess_sustainability(req: SustainabilityRequest):
    try: return SustainabilityCalculator().calculate(req)
    except Exception as e: raise HTTPException(500, str(e))
