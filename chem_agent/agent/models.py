"""Agent 数据模型。"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class AgentStep(BaseModel):
    """单个推理步骤。"""

    type: Literal["thought", "action", "observation", "answer", "error", "reflection", "planning"]
    content: str
    tool_name: Optional[str] = None
    tool_input: Optional[dict] = None
    plan_steps: Optional[list[str]] = None


class AgentResponse(BaseModel):
    """Agent 完整响应。"""

    reply: str = ""
    steps: list[AgentStep] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)
    iterations: int = 0


class ParsedAction(BaseModel):
    """从 LLM 输出中解析的动作。"""

    tool_name: str
    tool_input: dict = Field(default_factory=dict)


class ToolDef(BaseModel):
    """工具定义。"""

    name: str
    description: str
    parameters: dict = Field(default_factory=dict)
    permission: str = "chat:access"

    class Config:
        arbitrary_types_allowed = True
