"""配方安全风险分析 API 路由。"""

import logging

from fastapi import APIRouter, Depends, HTTPException

from chem_agent.auth.dependencies import require_permission
from chem_agent.auth.models import UserOut
from chem_agent.risk.analyzer import RiskLevel, RiskRequest, analyze_formula_risks

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/risk", tags=["Risk"])


@router.post("/analyze", summary="配方安全风险分析")
async def analyze_risks(req: RiskRequest, _user: UserOut = Depends(require_permission("risk:read"))):
    """基于 SDS/工艺条件分析配方的物料危害、不相容组合与闪点风险。"""
    try:
        return analyze_formula_risks(req)
    except Exception as e:
        logger.error("Risk analysis failed: %s", e)
        raise HTTPException(status_code=500, detail=f"风险分析失败: {e}")


@router.get("/methods", summary="获取风险等级与检查项")
async def list_risk_methods(_user: UserOut = Depends(require_permission("risk:read"))):
    """返回支持的风险等级与检查类型。"""
    return {
        "levels": [level.value for level in RiskLevel],
        "risk_types": [
            "material_hazard",
            "flash_point",
            "incompatible_materials",
            "process_condition",
        ],
    }
