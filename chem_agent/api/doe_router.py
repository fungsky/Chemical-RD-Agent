"""DOE实验设计 API 路由。"""

import logging

from fastapi import APIRouter, Depends, HTTPException

from chem_agent.doe.models import DesignRequest, DesignResult
from chem_agent.doe.designs import generate_design
from chem_agent.auth.dependencies import require_permission
from chem_agent.auth.models import UserOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/doe", tags=["DOE"])


@router.post("/generate", response_model=DesignResult, summary="生成实验设计方案")
async def generate_doe_design(req: DesignRequest, _user: UserOut = Depends(require_permission("doe:read"))):
    """根据指定方法和因子生成实验设计方案。

    支持5种设计方法：
    - full_factorial: 全因子设计
    - 2k_factorial: 2k因子设计
    - plackett_burman: Plackett-Burman筛选设计
    - latin_hypercube: 拉丁超立方采样
    - central_composite: 中心复合设计(CCD)
    """
    try:
        result = generate_design(req)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("DOE design generation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"实验设计生成失败: {e}")


@router.get("/methods", summary="获取支持的实验设计方法")
async def list_doe_methods(_user: UserOut = Depends(require_permission("doe:read"))):
    """返回所有支持的DOE设计方法及说明。"""
    from chem_agent.doe.models import DesignMethod
    descriptions = {
        DesignMethod.FULL_FACTORIAL: "全因子设计 — 所有因子所有水平的全组合，适合2-4个因子",
        DesignMethod.TWO_LEVEL_FACTORIAL: "2k因子设计 — 每个因子2个水平，高效筛选主效应",
        DesignMethod.PLACKETT_BURMAN: "Plackett-Burman — 筛选设计，用最少实验识别关键因子",
        DesignMethod.LATIN_HYPERCUBE: "拉丁超立方 — 空间填充采样，适合计算机实验和响应面",
        DesignMethod.CENTRAL_COMPOSITE: "中心复合设计(CCD) — 响应面优化，含立方点+轴向点+中心点",
    }
    return {
        "methods": [
            {"name": m.value, "description": descriptions.get(m, "")}
            for m in DesignMethod
        ],
    }

