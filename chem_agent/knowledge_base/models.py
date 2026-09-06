"""知识库数据模型。"""

from typing import Optional

from pydantic import BaseModel, Field


class DocumentMeta(BaseModel):
    """文档元数据。"""
    doc_id: str
    filename: str
    source_type: str  # pdf / docx / txt / url
    upload_time: str
    file_size: int = 0  # bytes
    num_chunks: int = 0
    uploader: Optional[str] = None


class SearchResult(BaseModel):
    """语义检索结果。"""
    content: str
    doc_id: str
    filename: str
    source_type: str
    similarity_score: float = 0.0
    chunk_index: int = 0


class KBStats(BaseModel):
    """知识库统计信息。"""
    total_documents: int = 0
    total_chunks: int = 0


class UrlRequest(BaseModel):
    """网页抓取请求。"""
    url: str = Field(..., description="网页 URL")


class SearchRequest(BaseModel):
    """语义检索请求。"""
    query: str = Field(..., description="检索查询")
    top_k: int = Field(5, ge=1, le=20, description="返回结果数量")
