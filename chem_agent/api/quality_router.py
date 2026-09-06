"""质量管理 API。"""
import logging
from fastapi import APIRouter, HTTPException
from chem_agent.quality import COATemplate, COAResult, QualityManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/quality", tags=["Quality"])
_qm = QualityManager()

@router.post("/templates", response_model=COATemplate)
async def add_template(tpl: COATemplate): return _qm.add_template(tpl)

@router.get("/templates/{name}", response_model=COATemplate)
async def get_template(name: str):
    r = _qm.get_template(name)
    if not r: raise HTTPException(404)
    return r

@router.get("/templates/list/all")
async def list_templates(): return _qm.list_templates()

@router.post("/coa/generate", response_model=COAResult)
async def generate_coa(template_name: str, report_id: str, batch_number: str, measurements: dict[str, float], inspector: str = ""):
    try: return _qm.create_coa(template_name, report_id, batch_number, measurements, inspector or None)
    except KeyError as e: raise HTTPException(404, str(e))

@router.get("/coa/{report_id}", response_model=COAResult)
async def get_coa(report_id: str):
    r = _qm.get_coa(report_id)
    if not r: raise HTTPException(404)
    return r

@router.get("/coa/list/all")
async def list_coas(): return _qm.list_coas()
