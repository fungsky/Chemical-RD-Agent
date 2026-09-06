"""工艺放大 API。"""
import logging
from fastapi import APIRouter, HTTPException
from chem_agent.scaleup import ScaleUpRequest, ScaleUpResult, ScaleUpCalculator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/scaleup", tags=["ScaleUp"])

@router.post("/calculate", response_model=ScaleUpResult)
async def calc_scaleup(req: ScaleUpRequest):
    try: return ScaleUpCalculator().calculate(req)
    except Exception as e: raise HTTPException(500, str(e))
