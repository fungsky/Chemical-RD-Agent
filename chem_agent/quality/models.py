"""质量管理模型。"""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class SpecDirection(str, Enum):
    MIN = "min"; MAX = "max"; RANGE = "range"; TARGET = "target"

class QualitySpec(BaseModel):
    name: str; direction: SpecDirection
    min_value: Optional[float] = None; max_value: Optional[float] = None
    target_value: Optional[float] = None; unit: str = ""
    test_method: Optional[str] = None; is_critical: bool = False

class COATemplate(BaseModel):
    name: str; product_name: str = ""; product_code: Optional[str] = None
    specs: list[QualitySpec] = Field(default_factory=list)
    version: str = "1.0"; created_at: datetime = Field(default_factory=datetime.now)

class InspectionResult(BaseModel):
    spec_name: str; measured_value: float; unit: str = ""
    is_pass: bool = True; deviation: Optional[float] = None; notes: Optional[str] = None

class COAResult(BaseModel):
    report_id: str; template_name: str; product_name: str
    batch_number: str = ""; production_date: datetime = Field(default_factory=datetime.now)
    inspector: Optional[str] = None; results: list[InspectionResult] = Field(default_factory=list)
    overall_pass: bool = True; remarks: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    approved_by: Optional[str] = None; approved_at: Optional[datetime] = None
