"""SPC模型。"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class ProcessCapability(BaseModel):
    cp: float = 0; cpk: float = 0; pp: float = 0; ppk: float = 0
    sigma_level: float = 0; grade: str = "D"; out_of_spec_percent: float = 0

class SPCChartData(BaseModel):
    labels: list[int] = Field(default_factory=list)
    values: list[float] = Field(default_factory=list)
    mean: float = 0; ucl: float = 0; lcl: float = 0
    usl: Optional[float] = None; lsl: Optional[float] = None
    violations: list[int] = Field(default_factory=list)

class SPCRequest(BaseModel):
    process_name: str = ""
    measurements: list[float] = Field(..., min_length=5)
    subgroup_size: int = Field(1, ge=1, le=25)
    usl: Optional[float] = None; lsl: Optional[float] = None; target: Optional[float] = None

class SPCResult(BaseModel):
    process_name: str
    capability: ProcessCapability
    xbar_chart: SPCChartData
    r_chart: Optional[SPCChartData] = None
    summary: str = ""
    alerts: list[str] = Field(default_factory=list)
