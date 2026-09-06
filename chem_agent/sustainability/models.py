"""可持续性模型。"""
from pydantic import BaseModel, Field

class SustainabilityMetric(BaseModel):
    name: str; value: float = 0; unit: str = ""
    threshold: str = ""; status: str = "ok"; score: float = Field(0, ge=0, le=100)

class SustainabilityRequest(BaseModel):
    formula_name: str = ""
    components: list[dict] = Field(default_factory=list, description="[{name, weight_percent, voc_content_percent, bio_based_percent, carbon_footprint_kgCO2_per_kg}]")
    batch_size_kg: float = 1.0; energy_kwh_per_kg: float = 0
    water_l_per_kg: float = 0; waste_percent: float = Field(0, ge=0, le=100)

class SustainabilityResult(BaseModel):
    formula_name: str
    overall_score: float = Field(0, ge=0, le=100)
    grade: str = "C"
    metrics: list[SustainabilityMetric] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    summary: str = ""
