"""质量管理 API。"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from chem_agent.quality import COATemplate, COAResult, QualityManager
from chem_agent.auth.dependencies import require_permission
from chem_agent.auth.models import UserOut

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/quality", tags=["Quality"])
_qm = QualityManager()

@router.post("/templates", response_model=COATemplate)
async def add_template(tpl: COATemplate, _user: UserOut = Depends(require_permission("quality:write"))): return _qm.add_template(tpl)

@router.get("/templates/{name}", response_model=COATemplate)
async def get_template(name: str, _user: UserOut = Depends(require_permission("quality:read"))):
    r = _qm.get_template(name)
    if not r: raise HTTPException(404)
    return r

@router.get("/templates/list/all")
async def list_templates(_user: UserOut = Depends(require_permission("quality:read"))): return _qm.list_templates()

@router.post("/coa/generate", response_model=COAResult)
async def generate_coa(template_name: str, report_id: str, batch_number: str, measurements: dict[str, float], inspector: str = "", _user: UserOut = Depends(require_permission("quality:write"))):
    try: return _qm.create_coa(template_name, report_id, batch_number, measurements, inspector or None)
    except KeyError as e: raise HTTPException(404, str(e))

@router.get("/coa/{report_id}", response_model=COAResult)
async def get_coa(report_id: str, _user: UserOut = Depends(require_permission("quality:read"))):
    r = _qm.get_coa(report_id)
    if not r: raise HTTPException(404)
    return r

@router.get("/coa/list/all")
async def list_coas(_user: UserOut = Depends(require_permission("quality:read"))): return _qm.list_coas()
