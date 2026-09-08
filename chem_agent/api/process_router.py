"""SPC过程控制 API。"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from chem_agent.process import SPCRequest, SPCResult, SPCEngine
from chem_agent.auth.dependencies import require_permission
from chem_agent.auth.models import UserOut

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/process", tags=["Process SPC"])
_engine = SPCEngine()

@router.post("/spc/analyze", response_model=SPCResult)
async def analyze_spc(req: SPCRequest, _user: UserOut = Depends(require_permission("process:read"))):
    try: return _engine.analyze(req)
    except Exception as e: raise HTTPException(500, str(e))
