"""研发上下文数据模型。"""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ClientRequest(BaseModel):
    id: str = Field(..., description="需求编号")
    customer: str = Field(..., description="客户/内部项目")
    title: str = Field(..., description="需求标题")
    requirement: str = Field("", description="需求描述")
    target_specs: dict = Field(default_factory=dict, description="目标规格")
    formula_codes: list[str] = Field(default_factory=list, description="关联配方")
    status: str = Field("open", description="open/sampling/review/done")
    created_at: str = Field(default_factory=_now)
    updated_at: str = Field(default_factory=_now)


class SampleRecord(BaseModel):
    sample_id: str = Field(..., description="样品编号")
    request_id: str = Field(..., description="所属需求")
    formula_code: str = Field("", description="配方编号")
    formula_name: str = Field("", description="配方名称")
    batch_number: str = Field("", description="批次号")
    sent_at: str = Field(default_factory=_now, description="寄出时间")
    feedback_status: str = Field("pending", description="pending/received")
    feedback: str = Field("", description="客户反馈")
    created_at: str = Field(default_factory=_now)


class TimelineEvent(BaseModel):
    event_id: str = Field(..., description="事件 ID")
    request_id: str = Field("", description="需求编号")
    event_type: str = Field(..., description="version/experiment/sample/feedback/note")
    summary: str = Field(..., description="摘要")
    ref: str = Field("", description="关联记录")
    created_at: str = Field(default_factory=_now)
