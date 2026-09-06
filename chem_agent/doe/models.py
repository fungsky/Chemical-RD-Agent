"""DOE实验设计数据模型。"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class DesignMethod(str, Enum):
    FULL_FACTORIAL = "full_factorial"
    TWO_LEVEL_FACTORIAL = "2k_factorial"
    PLACKETT_BURMAN = "plackett_burman"
    LATIN_HYPERCUBE = "latin_hypercube"
    CENTRAL_COMPOSITE = "central_composite"


class Factor(BaseModel):
    name: str = Field(..., description="因子名称")
    unit: str = Field("", description="单位")
    low: float = Field(..., description="低水平值")
    high: float = Field(..., description="高水平值")
    center: Optional[float] = Field(None, description="中心点值")
    category: str = Field("continuous", description="因子类型: continuous/categorical")


class DesignRequest(BaseModel):
    method: DesignMethod = Field(DesignMethod.FULL_FACTORIAL)
    factors: list[Factor] = Field(..., min_length=1, max_length=10)
    replicates: int = Field(1, ge=1, le=5, description="重复次数")
    center_points: int = Field(0, ge=0, le=10, description="中心点数量")
    randomize: bool = Field(True, description="是否随机化运行顺序")


class DesignRun(BaseModel):
    run_order: int
    standard_order: int
    block: int = 1
    factor_levels: dict[str, float]


class DesignResult(BaseModel):
    method: DesignMethod
    factors: list[Factor]
    total_runs: int
    runs: list[DesignRun]
    summary: str
