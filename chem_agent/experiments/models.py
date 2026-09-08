"""实验数据模型。"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ExperimentStatus(str, Enum):
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExperimentCondition(BaseModel):
    """单组实验的配方条件（对应 DOE 一个 Run）。"""
    items: list[dict] = Field(
        default_factory=list,
        description="组分列表: [{material_name, weight_percent, addition_order}]",
    )
    process: dict = Field(
        default_factory=dict,
        description="工艺条件: {temperature, mixing_speed, mixing_time, ...}",
    )


class ExperimentResult(BaseModel):
    """单组实验结果。"""
    id: Optional[str] = None
    experiment_id: str = Field(..., description="实验编号（唯一）")
    formula_name: str = Field(..., description="配方名称")
    formula_code: Optional[str] = Field(None, description="关联配方编号")
    formula_version: Optional[str] = Field(None, description="关联配方版本")
    project: str = Field("", description="所属项目")
    batch_number: Optional[str] = Field(None, description="批次号")
    status: ExperimentStatus = Field(ExperimentStatus.COMPLETED)

    # 关联 DOE
    doe_method: Optional[str] = Field(None, description="DOE方法名称")
    doe_run_order: Optional[int] = Field(None, description="DOE运行序号")
    doe_design_id: Optional[str] = Field(None, description="DOE方案ID")

    # 配方条件
    condition: ExperimentCondition = Field(default_factory=ExperimentCondition)

    # 实测性能
    measurements: dict[str, float] = Field(
        default_factory=dict,
        description="性能实测值: {盐雾时间: 520, 附着力: 5.2, ...}",
    )
    measurement_units: dict[str, str] = Field(
        default_factory=dict,
        description="性能单位: {盐雾时间: h, 附着力: MPa, ...}",
    )
    spec_targets: dict[str, dict] = Field(
        default_factory=dict,
        description="目标规格: {硬度: {min: 80, max: 100, unit: H}}",
    )

    # 元数据
    operator: Optional[str] = Field(None, description="实验员")
    lab_location: Optional[str] = Field(None, description="实验室")
    notes: Optional[str] = Field(None, description="备注")
    attachments: list[str] = Field(default_factory=list, description="附件路径列表")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    # 异常标记
    is_outlier: bool = Field(False, description="是否为统计异常值")
    outlier_reason: Optional[str] = Field(None, description="异常原因说明")


class ExperimentBatch(BaseModel):
    """批量实验结果。"""
    batch_name: str = Field(..., description="批次名称")
    project: str = Field("", description="所属项目")
    results: list[ExperimentResult] = Field(..., min_length=1)
    summary: Optional[str] = Field(None, description="批次总结")


class ExperimentQuery(BaseModel):
    """实验查询条件。"""
    project: Optional[str] = None
    formula_name: Optional[str] = None
    status: Optional[ExperimentStatus] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    has_measurement: Optional[str] = Field(None, description="筛选包含指定性能指标的实验")
    include_outliers: bool = Field(True, description="是否包含异常值")
    limit: int = Field(100, ge=1, le=1000)


class TrainingDataExport(BaseModel):
    """从实验结果导出的训练数据。"""
    total_experiments: int
    total_measurements: int
    target_properties: list[str]
    training_data: list[dict] = Field(
        default_factory=list,
        description="训练数据列表，格式同 FormulaPredictor.train()",
    )
    excluded_outliers: int = 0
    excluded_incomplete: int = 0
