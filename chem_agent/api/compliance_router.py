"""合规检查 API 路由。"""

import logging
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from chem_agent.compliance.rules import (
    RegulationDomain,
    ComplianceRequest,
    ComplianceResult,
    check_compliance,
)
from chem_agent.auth.dependencies import require_permission
from chem_agent.auth.models import UserOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/compliance", tags=["Compliance"])

_STANDARDS_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "standards_registry.json"


@router.post("/check", response_model=ComplianceResult, summary="配方合规检查")
async def check_compliance_endpoint(req: ComplianceRequest, _user: UserOut = Depends(require_permission("compliance:read"))):
    """对配方进行指定法规领域的合规检查。

    支持的法规领域:
    - food_contact: 食品接触材料(GB 4806系列 / EU 10/2011)
    - toys: 玩具安全(GB 6675-2014 / EN 71-3)
    - automotive: 汽车材料(GB 30512-2014 / ELV)
    - construction: 建筑材料与涂料(GB 18582-2020系列)
    - electronics: 电子电器(GB/T 26572-2011 / RoHS)
    - medical: 医疗器械(ISO 10993 / MDR)
    - cosmetics: 化妆品与牙膏(安全技术规范2015 / GB/T 8372)
    - textile: 纺织品(GB 18401-2010)
    """
    try:
        result = check_compliance(req)
        return result
    except Exception as e:
        logger.error("Compliance check failed: %s", e)
        raise HTTPException(status_code=500, detail=f"合规检查失败: {e}")


@router.get("/domains", summary="获取支持的法规领域")
async def list_domains(_user: UserOut = Depends(require_permission("compliance:read"))):
    """返回所有支持的法规领域及说明。"""
    descriptions = {
        RegulationDomain.FOOD_CONTACT: "食品接触材料 — GB 4806 系列 / GB 9685, EU 10/2011",
        RegulationDomain.TOYS: "玩具安全 — GB 6675.4-2014, EN 71-3",
        RegulationDomain.AUTOMOTIVE: "汽车材料 — GB 30512-2014, ELV 2000/53/EC",
        RegulationDomain.CONSTRUCTION: "建筑材料与涂料 — GB 18582-2020, GB 24410, GB 18580",
        RegulationDomain.ELECTRONICS: "电子电器 — GB/T 26572-2011, RoHS 2011/65/EU",
        RegulationDomain.MEDICAL: "医疗器械 — ISO 10993, MDR 2017/745",
        RegulationDomain.COSMETICS: "化妆品与牙膏 — 安全技术规范(2015), GB/T 8372-2017, EU 1223/2009",
        RegulationDomain.TEXTILE: "纺织品 — GB 18401-2010 基本安全技术规范",
    }
    return {
        "domains": [
            {"code": d.value, "description": descriptions.get(d, "")}
            for d in RegulationDomain
        ],
    }


@router.get("/standards", summary="获取国标/行标标准登记表")
async def list_standards(_user: UserOut = Depends(require_permission("compliance:read"))):
    """返回内置的中国国家标准(GB/GB-T)与行业标准(行标)登记索引。"""
    try:
        with open(_STANDARDS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("标准登记表读取失败: %s", e)
        raise HTTPException(status_code=500, detail=f"标准登记表读取失败: {e}")

