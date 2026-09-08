"""研发上下文 API：需求、样品、工作台聚合、AI 下一步建议。"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from chem_agent.auth.dependencies import require_permission
from chem_agent.auth.models import UserOut

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/rd", tags=["R&D Context"])


def _mgr():
    from chem_agent.rd.manager import RDManager
    return RDManager()


class CreateRequestPayload(BaseModel):
    customer: str
    title: str
    requirement: str = ""
    target_specs: dict = {}


class UpdateRequestPayload(BaseModel):
    customer: str | None = None
    title: str | None = None
    requirement: str | None = None
    status: str | None = None
    target_specs: dict | None = None


class AddFormulaPayload(BaseModel):
    code: str


class CreateSamplePayload(BaseModel):
    request_id: str
    formula_code: str = ""
    formula_name: str = ""
    batch_number: str = ""


class UpdateSamplePayload(BaseModel):
    feedback_status: str | None = None
    feedback: str | None = None


class NextStepRequest(BaseModel):
    request_id: str


@router.get("/requests")
async def list_requests(_user: UserOut = Depends(require_permission("formula:read"))):
    return {"requests": _mgr().list_requests()}


@router.post("/requests")
async def create_request(payload: CreateRequestPayload, _user: UserOut = Depends(require_permission("formula:write"))):
    req = _mgr().create_request(payload.customer, payload.title, payload.requirement, payload.target_specs)
    return {"request": req.model_dump(mode="json")}


@router.patch("/requests/{request_id}")
async def update_request(request_id: str, payload: UpdateRequestPayload, _user: UserOut = Depends(require_permission("formula:write"))):
    req = _mgr().update_request(request_id, **payload.model_dump(exclude_none=True))
    if not req:
        raise HTTPException(status_code=404, detail="需求不存在")
    return {"request": req.model_dump(mode="json")}


@router.post("/requests/{request_id}/formulas")
async def add_formula(request_id: str, payload: AddFormulaPayload, _user: UserOut = Depends(require_permission("formula:write"))):
    req = _mgr().add_formula(request_id, payload.code)
    if not req:
        raise HTTPException(status_code=404, detail="需求不存在")
    return {"request": req.model_dump(mode="json")}


@router.get("/samples")
async def list_samples(_user: UserOut = Depends(require_permission("formula:read"))):
    return {"samples": _mgr().list_samples()}


@router.post("/samples")
async def create_sample(payload: CreateSamplePayload, _user: UserOut = Depends(require_permission("formula:write"))):
    sample = _mgr().add_sample(payload.request_id, payload.formula_code, payload.formula_name, payload.batch_number)
    return {"sample": sample.model_dump(mode="json")}


@router.patch("/samples/{sample_id}")
async def update_sample(sample_id: str, payload: UpdateSamplePayload, _user: UserOut = Depends(require_permission("formula:write"))):
    sample = _mgr().update_sample(sample_id, payload.feedback_status, payload.feedback)
    if not sample:
        raise HTTPException(status_code=404, detail="样品不存在")
    return {"sample": sample.model_dump(mode="json")}


def _todos_for(mgr, request):
    todos = []
    try:
        from chem_agent.api.main import kg_service
        for code in request.get("formula_codes") or []:
            formula = kg_service.get_formula(code)
            if formula and formula.status.value in ("review", "draft"):
                todos.append({"type": "formula_review", "title": f"配方 {code} 状态：{formula.status.value}，待复核", "ref": code})
    except Exception:
        pass

    samples = [s for s in mgr.list_samples() if s.get("request_id") == request.get("id")]
    for s in samples:
        if s.get("feedback_status") == "pending":
            todos.append({"type": "sample_feedback", "title": f"样品 {s.get('sample_id')} 已寄出，等待客户反馈", "ref": s.get("sample_id")})

    try:
        from chem_agent.experiments.manager import get_experiment_manager
        exps = get_experiment_manager().list_all()
        planned = [e for e in exps if e.project in (request.get("id"), request.get("title")) and e.status.value == "planned"]
        for e in planned:
            todos.append({"type": "experiment", "title": f"实验计划 {e.experiment_id}（{e.formula_name}）待完成", "ref": e.experiment_id})
    except Exception:
        pass
    return todos


def _timeline_for(mgr, request):
    events = [e for e in mgr.events() if e.get("request_id") == request.get("id")]
    try:
        from chem_agent.auth import database as db
        for code in request.get("formula_codes") or []:
            versions = db.get_formula_versions(code)
            if versions:
                v = versions[0]
                events.append({
                    "event_id": f"version-{v['id']}",
                    "request_id": request.get("id"),
                    "event_type": "version",
                    "summary": f"配方 {code} 生成版本 {v['version_number']}：{v.get('change_summary') or ''}",
                    "ref": code,
                    "created_at": v.get("created_at", ""),
                })
    except Exception:
        pass
    events.sort(key=lambda e: e.get("created_at", ""), reverse=True)
    return events[:50]


@router.get("/dashboard")
async def dashboard(request_id: str = Query(...), _user: UserOut = Depends(require_permission("formula:read"))):
    mgr = _mgr()
    request = mgr.get_request(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="需求不存在")
    req = request.model_dump(mode="json")
    return {
        "request": req,
        "samples": [s for s in mgr.list_samples() if s.get("request_id") == request_id],
        "todos": _todos_for(mgr, req),
        "timeline": _timeline_for(mgr, req),
    }


@router.post("/next-step")
async def next_step(payload: NextStepRequest, _user: UserOut = Depends(require_permission("formula:analyze"))):
    mgr = _mgr()
    request = mgr.get_request(payload.request_id)
    if not request:
        raise HTTPException(status_code=404, detail="需求不存在")
    req = request.model_dump(mode="json")
    todos = _todos_for(mgr, req)
    timeline = _timeline_for(mgr, req)
    samples = [s for s in mgr.list_samples() if s.get("request_id") == payload.request_id]

    prompt_parts = [
        f"需求：{req.get('title')}",
        f"要求：{req.get('requirement') or '无'}",
        f"关联配方：{', '.join(req.get('formula_codes') or [])}",
        f"最近样品反馈：{json_dump(samples[-3:]) if samples else '无'}",
        f"待办：{json_dump(todos)}",
        f"最近动态：{json_dump(timeline[:10])}",
    ]
    prompt = "\n".join(prompt_parts) + "\n请作为资深研发专家给出下一步建议（2-4 条，含理由与验证方法）。"

    from chem_agent.api.main import llm_service
    from langchain_core.output_parsers import StrOutputParser
    try:
        import asyncio
        from chem_agent.config import settings
        suggestion = await asyncio.wait_for(
            (llm_service.llm | StrOutputParser()).ainvoke(prompt),
            timeout=settings.llm_timeout_seconds,
        )
    except Exception as e:
        logger.warning("AI 下一步建议失败: %s", e)
        suggestion = "当前数据不足，无法生成建议。请先补充实验记录或客户反馈。"
    return {"request_id": payload.request_id, "suggestion": suggestion}


def json_dump(obj) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False, default=str)
