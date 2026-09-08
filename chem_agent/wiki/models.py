"""LLM Wiki 数据模型。"""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class WikiSection(BaseModel):
    heading: str = Field(..., description="章节标题")
    body: str = Field(..., description="章节内容")


class WikiSourceRef(BaseModel):
    source_doc: str = Field(..., description="来源文档名")
    chunk_index: Optional[int] = None


class WikiPage(BaseModel):
    page_id: str = Field(..., description="Wiki 页面 ID")
    title: str = Field(..., description="页面标题")
    aliases: list[str] = Field(default_factory=list, description="别名")
    summary: str = Field("", description="可注入 LLM 的摘要")
    sections: list[WikiSection] = Field(default_factory=list, description="结构化章节")
    links: list[str] = Field(default_factory=list, description="关联词条")
    source_docs: list[str] = Field(default_factory=list, description="来源文档名")
    status: str = Field("draft", description="draft/approved")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Optional[str] = None

    def to_markdown(self) -> str:
        lines = [f"# {self.title}", "", self.summary or ""]
        for sec in self.sections:
            lines.extend(["", f"## {sec.heading}", "", sec.body])
        if self.source_docs:
            lines.extend(["", "### 来源", ""] + [f"- {s}" for s in self.source_docs])
        return "\n".join(lines).strip()


class WikiSearchResult(BaseModel):
    page_id: str
    title: str
    content: str = ""
    similarity_score: float = 0.0


class WikiCompileRequest(BaseModel):
    doc_id: str = Field(..., description="知识库文档 ID")


class WikiSearchRequest(BaseModel):
    query: str = Field(..., description="检索查询")
    top_k: int = Field(3, ge=1, le=10, description="返回页面数")
