"""多目标优化 API 路由。"""

import logging

from fastapi import APIRouter, Depends, HTTPException

from chem_agent.optimization.models import (
    OptimizationMethod,
    OptimizationRequest,
    OptimizationResult,
)
from chem_agent.optimization.engine import OptimizationEngine
from chem_agent.auth.dependencies import require_permission
from chem_agent.auth.models import UserOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/optimization", tags=["Optimization"])

_engine = OptimizationEngine()


@router.post("/run", response_model=OptimizationResult, summary="执行多目标配方优化")
async def run_optimization(req: OptimizationRequest, _user: UserOut = Depends(require_permission("optimization:read"))):
    """在因子空间中搜索最优配方。

    支持三种模式：
    - weighted_score: 加权综合评分
    - pareto_frontier: 帕累托前沿（展示所有非支配解）
    - constrained_single: 约束单目标优化

    输入因子范围、优化目标和约束条件，返回最优配方集合。
    """
    try:
        result = _engine.optimize(req)
        return result
    except Exception as e:
        logger.error("Optimization failed: %s", e)
        raise HTTPException(status_code=500, detail=f"优化失败: {e}")


@router.get("/methods", summary="获取支持的优化方法")
async def list_methods(_user: UserOut = Depends(require_permission("optimization:read"))):
    """返回优化方法说明。"""
    return {
        "methods": [
            {
                "name": OptimizationMethod.WEIGHTED_SCORE.value,
                "description": "加权评分 — 为各目标分配权重，计算综合评分排序",
                "use_case": "目标优先级明确的场景",
            },
            {
                "name": OptimizationMethod.PARETO_FRONTIER.value,
                "description": "帕累托前沿 — 找到所有非支配解，展示性能-成本等维度的最优折衷",
                "use_case": "需要在多个互相冲突的目标间做权衡",
            },
            {
                "name": OptimizationMethod.CONSTRAINED_SINGLE.value,
                "description": "约束单目标 — 在其他目标满足约束的前提下，优化单一目标",
                "use_case": "给定最低性能要求，最小化成本",
            },
        ],
    }


@router.get("/example", summary="获取优化示例请求")
async def get_example(_user: UserOut = Depends(require_permission("optimization:read"))):
    """返回一个典型的优化请求示例，帮助理解 API 用法。"""
    return {
        "example": {
            "method": "pareto_frontier",
            "factor_ranges": [
                {"name": "环氧树脂", "type": "continuous", "min_value": 40, "max_value": 60},
                {"name": "固化剂", "type": "continuous", "min_value": 10, "max_value": 25},
                {"name": "防锈颜料", "type": "continuous", "min_value": 5, "max_value": 15},
                {"name": "固化温度", "type": "continuous", "min_value": 60, "max_value": 120, "step": 5},
            ],
            "objectives": [
                {"name": "盐雾时间", "direction": "maximize", "weight": 1.0, "target_value": 500, "hard_min": 300},
                {"name": "附着力", "direction": "maximize", "weight": 0.8, "target_value": 5, "hard_min": 3},
                {"name": "成本", "direction": "minimize", "weight": 0.6, "target_value": 15, "hard_max": 25},
            ],
            "constraints": [
                {"name": "固化温度", "constraint_type": "range", "max_value": 110}
            ],
            "population_size": 2000,
            "top_n": 10,
        },
        "description": "水性防腐涂料多目标优化示例 — 最大化盐雾和附着力，最小化成本",
    }

