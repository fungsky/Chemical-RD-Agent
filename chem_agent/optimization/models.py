"""优化模型定义。"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class OptimizationMethod(str, Enum):
    WEIGHTED_SCORE = "weighted_score"
    PARETO_FRONTIER = "pareto_frontier"
    CONSTRAINED_SINGLE = "constrained_single"


class ObjectiveDirection(str, Enum):
    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"


class OptimizationObjective(BaseModel):
    """优化目标：性能指标或成本等。"""
    name: str = Field(..., description="目标名称")
    direction: ObjectiveDirection = Field(..., description="最大化/最小化")
    weight: float = Field(1.0, ge=0, description="权重（加权评分模式）")
    target_value: Optional[float] = Field(None, description="目标值（可选）")
    hard_min: Optional[float] = Field(None, description="硬性下限")
    hard_max: Optional[float] = Field(None, description="硬性上限")


class OptimizationConstraint(BaseModel):
    """约束条件。"""
    name: str = Field(..., description="约束名称")
    constraint_type: str = Field("range", description="类型: range, fixed, ratio")
    min_value: Optional[float] = Field(None)
    max_value: Optional[float] = Field(None)
    target_value: Optional[float] = Field(None)


class FactorRange(BaseModel):
    """搜索空间中因子的取值范围。"""
    name: str = Field(..., description="因子名称")
    type: str = Field("continuous", description="continuous / categorical")
    min_value: float = Field(..., description="最小值")
    max_value: float = Field(..., description="最大值")
    step: Optional[float] = Field(None, description="搜索步长")


class OptimizationRequest(BaseModel):
    """优化请求。"""
    method: OptimizationMethod = Field(OptimizationMethod.WEIGHTED_SCORE)
    factor_ranges: list[FactorRange] = Field(..., min_length=1, max_length=15)
    objectives: list[OptimizationObjective] = Field(..., min_length=1, max_length=10)
    constraints: list[OptimizationConstraint] = Field(default_factory=list)
    total_weight_constraint: float = Field(100.0, description="总重量约束(%)")

    # 搜索参数
    population_size: int = Field(1000, ge=100, le=100000, description="搜索点数(网格)或种群大小(遗传)")
    top_n: int = Field(10, ge=1, le=50, description="返回最优解数量")
    random_seed: int = Field(42)

    # 使用哪个预测模型
    use_predictor: bool = Field(True, description="使用ML预测模型")
    performance_data_source: str = Field("experiments", description="数据来源: experiments / knowledge_graph / both")


class ParetoSolution(BaseModel):
    """单个帕累托最优解。"""
    rank: int = Field(..., description="排名")
    factors: dict[str, float] = Field(..., description="因子取值")
    objectives: dict[str, float] = Field(..., description="各目标值")
    score: float = Field(0, description="综合评分")
    is_pareto_optimal: bool = Field(False, description="是否在帕累托前沿上")
    dominated_count: int = Field(0, description="被多少解支配")
    notes: Optional[str] = Field(None)


class OptimizationResult(BaseModel):
    """优化结果。"""
    method: OptimizationMethod
    total_evaluated: int = Field(0, description="评估总数")
    pareto_front_size: int = Field(0, description="帕累托前沿解数量")
    solutions: list[ParetoSolution] = Field(default_factory=list)
    best_solution: Optional[ParetoSolution] = Field(None, description="最优解")
    summary: str = ""
    pareto_front: list[dict] = Field(default_factory=list, description="帕累托前沿（用于可视化）")
