"""知识库 API 路由。"""

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from chem_agent.auth.dependencies import require_permission
from chem_agent.auth.models import UserOut
from chem_agent.config import settings
from chem_agent.api.error_handler import ChemAgentError, ErrorCode
from chem_agent.knowledge_base.document_parser import (
    DocumentParseError,
    parse_docx,
    parse_excel,
    parse_pdf,
    parse_txt,
    scrape_url,
)
from chem_agent.knowledge_base.models import (
    DocumentMeta,
    KBStats,
    SearchRequest,
    SearchResult,
    UrlRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/kb", tags=["知识库"])


def _get_kb_service():
    """获取全局 kb_service 实例，在 main.py 中注入。"""
    from chem_agent.api.main import kb_service

    if kb_service is None:
        raise ChemAgentError(
            error_code=ErrorCode.NOT_INITIALIZED,
            user_message="知识库服务未初始化，请检查 Ollama 是否运行",
            status_code=503,
        )
    return kb_service


# ============ 文档上传 ============


@router.post("/upload", response_model=dict)
async def upload_document(
    file: UploadFile = File(...),
    current_user: UserOut = Depends(require_permission("knowledge:write")),
):
    """上传文档到知识库（PDF/Word/TXT/Excel）。"""
    kb = _get_kb_service()
    filename = file.filename or "unknown"
    content_bytes = await file.read()

    # 检查文件大小
    size_mb = len(content_bytes) / (1024 * 1024)
    if size_mb > settings.max_file_size_mb:
        raise HTTPException(
            status_code=413,
            detail=f"文件大小 {size_mb:.1f}MB 超过限制 {settings.max_file_size_mb}MB",
        )

    # 根据扩展名解析
    try:
        if filename.lower().endswith(".pdf"):
            text = parse_pdf(content_bytes)
            source_type = "pdf"
        elif filename.lower().endswith(".docx"):
            text = parse_docx(content_bytes)
            source_type = "docx"
        elif filename.lower().endswith(".txt"):
            text = parse_txt(content_bytes)
            source_type = "txt"
        elif filename.lower().endswith(".xlsx"):
            text = parse_excel(content_bytes)
            source_type = "excel"
        else:
            raise HTTPException(status_code=400, detail="不支持的文件格式，请上传 .pdf / .docx / .txt / .xlsx")
    except DocumentParseError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        meta = await kb.add_document(
            filename=filename,
            content=text,
            source_type=source_type,
            uploader=current_user.username,
            file_size=len(content_bytes),
        )
        # 审计日志
        from chem_agent.auth import database as auth_db

        auth_db.log_audit(
            action="kb_upload",
            user_id=current_user.id,
            username=current_user.username,
            resource_type="knowledge",
            details={"filename": filename, "chunks": meta.num_chunks},
        )
        return {"doc_id": meta.doc_id, "message": f"上传成功，共 {meta.num_chunks} 个片段", "num_chunks": meta.num_chunks}
    except Exception as e:
        logger.error("文档入库失败: %s", e)
        raise ChemAgentError(error_code=ErrorCode.DB_QUERY_FAILED, internal_detail=str(e))


# ============ 网页抓取 ============


@router.post("/url", response_model=dict)
async def import_from_url(
    request: UrlRequest,
    current_user: UserOut = Depends(require_permission("knowledge:write")),
):
    """从网页 URL 抓取内容并存入知识库。"""
    kb = _get_kb_service()

    try:
        text, title = scrape_url(request.url)
    except DocumentParseError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        meta = await kb.add_document(
            filename=title,
            content=text,
            source_type="url",
            uploader=current_user.username,
            file_size=len(text.encode("utf-8")),
        )
        from chem_agent.auth import database as auth_db

        auth_db.log_audit(
            action="kb_import_url",
            user_id=current_user.id,
            username=current_user.username,
            resource_type="knowledge",
            details={"url": request.url, "title": title, "chunks": meta.num_chunks},
        )
        return {"doc_id": meta.doc_id, "message": f"抓取成功，共 {meta.num_chunks} 个片段", "num_chunks": meta.num_chunks}
    except Exception as e:
        logger.error("URL 导入失败: %s", e)
        raise ChemAgentError(error_code=ErrorCode.DB_QUERY_FAILED, internal_detail=str(e))


# ============ 文档列表 ============


@router.get("/documents", response_model=list[DocumentMeta])
async def list_documents(
    _user: UserOut = Depends(require_permission("knowledge:read")),
):
    """获取知识库文档列表。"""
    kb = _get_kb_service()
    return kb.list_documents()


@router.get("/documents/{doc_id}/chunks")
async def get_document_chunks(
    doc_id: str,
    _user: UserOut = Depends(require_permission("knowledge:read")),
):
    """查看某个文档的原文分块（用于查阅/核验 AI 引用）。"""
    kb = _get_kb_service()
    chunks = kb.get_document_chunks(doc_id, limit=10000)
    if not chunks:
        raise HTTPException(status_code=404, detail="文档不存在或无内容")
    return {"doc_id": doc_id, "chunks": chunks, "total": len(chunks)}


# ============ 删除文档 ============


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    current_user: UserOut = Depends(require_permission("knowledge:write")),
):
    """删除知识库中的指定文档。"""
    kb = _get_kb_service()
    ok = kb.delete_document(doc_id)
    if not ok:
        raise HTTPException(status_code=404, detail="文档不存在或删除失败")

    from chem_agent.auth import database as auth_db

    auth_db.log_audit(
        action="kb_delete",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="knowledge",
        details={"doc_id": doc_id},
    )
    return {"message": "删除成功"}


# ============ 文档摘要 ============


@router.post("/documents/{doc_id}/summary")
async def generate_summary(
    doc_id: str,
    _user: UserOut = Depends(require_permission("knowledge:read")),
):
    """为指定文档生成 AI 摘要。"""
    kb = _get_kb_service()

    # 取出前几个 chunk 拼接作为摘要素材
    chunks = kb.get_document_chunks(doc_id, limit=5)
    if not chunks:
        raise HTTPException(status_code=404, detail="文档不存在或无内容")

    text = "\n".join(chunks)
    from chem_agent.api.main import llm_service
    try:
        import asyncio
        from chem_agent.config import settings as _settings
        prompt = f"请用简洁的中文对以下文档内容生成一段 100-200 字的摘要:\n\n{text[:3000]}"
        from langchain_core.output_parsers import StrOutputParser
        chain = llm_service.llm | StrOutputParser()
        summary = await asyncio.wait_for(
            chain.ainvoke(prompt),
            timeout=_settings.llm_timeout_seconds,
        )
        return {"doc_id": doc_id, "summary": summary}
    except Exception as e:
        logger.error("生成摘要失败: %s", e)
        raise ChemAgentError(error_code=ErrorCode.LLM_UNAVAILABLE, internal_detail=str(e))


# ============ 语义检索 ============


@router.post("/search", response_model=list[SearchResult])
async def search_knowledge(
    request: SearchRequest,
    _user: UserOut = Depends(require_permission("knowledge:read")),
):
    """语义检索知识库。"""
    kb = _get_kb_service()
    return await kb.search(request.query, top_k=request.top_k)


# ============ 统计 ============


@router.get("/stats", response_model=KBStats)
async def get_stats(
    _user: UserOut = Depends(require_permission("knowledge:read")),
):
    """知识库统计信息。"""
    kb = _get_kb_service()
    return kb.get_stats()
