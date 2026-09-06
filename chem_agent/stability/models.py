"""稳定性预测模型。"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class AgingModel(str, Enum):
    ARRHENIUS = "arrhenius"; Q10 = "q10"; LINEAR = "linear"

class AgingTestPoint(BaseModel):
    temperature_c: float; time_hours: float
    property_value: float; property_name: str = "performance"; property_unit: str = ""

class StabilityRequest(BaseModel):
    formula_name: str = ""
    aging_data: list[AgingTestPoint] = Field(..., min_length=3)
    activation_energy_kj_mol: float = 80.0
    q10_value: float = Field(2.0, ge=1.5, le=5.0)
    failure_threshold: float = Field(...)
    model: AgingModel = AgingModel.ARRHENIUS
    storage_temperature_c: float = Field(25.0)

class StabilityResult(BaseModel):
    formula_name: str
    model: AgingModel; storage_temperature_c: float
    predicted_shelf_life_days: float = 0; predicted_shelf_life_years: float = 0
    confidence: str = ""; degradation_rate_per_day: float = 0
    time_to_failure_at_temp: dict[int, float] = Field(default_factory=dict)
    summary: str = ""; warnings: list[str] = Field(default_factory=list)
