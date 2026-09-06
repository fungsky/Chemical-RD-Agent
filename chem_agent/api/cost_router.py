"""BOM成本核算 API 路由。"""

import logging

from fastapi import APIRouter, HTTPException

from chem_agent.cost.cost_calculator import CostRequest, CostResult, calculate_formula_cost

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cost", tags=["Cost"])


@router.post("/calculate", response_model=CostResult, summary="计算配方BOM成本")
async def calculate_cost(req: CostRequest):
    """根据配方组分和物料单价计算总成本和单位成本。

    输出包含:
    - 各物料明细成本
    - 物料成本/包装/人工/能耗/管理费分项
    - 缺少单价的物料清单
    """
    try:
        result = calculate_formula_cost(req)
        return result
    except Exception as e:
        logger.error("Cost calculation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"成本核算失败: {e}")

print("cost_router done")
