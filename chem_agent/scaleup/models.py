"""放大计算模型。"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class ScaleUpMethod(str, Enum):
    CONSTANT_TIP_SPEED = "constant_tip_speed"
    CONSTANT_POWER_PER_VOLUME = "constant_power_per_volume"
    CONSTANT_REYNOLDS = "constant_reynolds"
    CONSTANT_MIXING_TIME = "constant_mixing_time"
    GEOMETRIC_SIMILARITY = "geometric_similarity"

class ScaleUpRequest(BaseModel):
    formula_name: str = ""
    lab_volume_l: float = Field(1.0, ge=0.1, le=10)
    target_volume_l: float = Field(..., ge=10, le=50000)
    lab_speed_rpm: float = Field(..., ge=10, le=3000)
    impeller_diameter_m: float = Field(0.05, ge=0.01)
    fluid_density: float = Field(1000, ge=500)
    fluid_viscosity: float = Field(0.001, ge=0.0001)
    methods: list[ScaleUpMethod] = Field(default_factory=lambda: [ScaleUpMethod.CONSTANT_TIP_SPEED, ScaleUpMethod.CONSTANT_POWER_PER_VOLUME])

class ScaleUpResult(BaseModel):
    formula_name: str
    lab_volume_l: float
    target_volume_l: float
    scale_ratio: float = 0
    recommendations: list[dict] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    summary: str = ""
