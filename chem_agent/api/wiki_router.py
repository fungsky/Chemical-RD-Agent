"""LLM Wiki API：编译、检索、管理知识页。"""

import logging

from fastapi import APIRouter, Depends, HTTPException

from chem_agent.auth.dependencies import require_permission
from chem_agent.auth.models import UserOut
from chem_agent.wiki.models import WikiCompileRequest, WikiSearchRequest, WikiSearchResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/kb/wiki", tags=["LLM Wiki"])


def _get_services():
    from chem_agent.api import main

    if main.kb_service is None or main.wiki_service is None:
        raise HTTPException(status_code=503, detail="知识库/Wiki 服务未初始化")
    return main.kb_service, main.wiki_service


@router.get("/pages", summary="Wiki 页面列表")
async def list_wiki_pages(_user: UserOut = Depends(require_permission("knowledge:read"))):
    _, wiki = _get_services()
    return {"total": wiki.count(), "pages": wiki.list_pages()}


@router.post("/compile", summary="把文档编译成 Wiki 页面")
async def compile_document(req: WikiCompileRequest, _user: UserOut = Depends(require_permission("knowledge:write"))):
    kb, wiki = _get_services()
    chunks = kb.get_document_chunks(req.doc_id, limit=10000)
    if not chunks:
        raise HTTPException(status_code=404, detail=f"文档 {req.doc_id} 不存在或无内容")
    filename = req.doc_id
    for doc in kb.list_documents():
        if doc.doc_id == req.doc_id:
            filename = doc.filename or req.doc_id
            break
    try:
        page = await wiki.compile_document(filename, chunks)
    except Exception as e:
        logger.error("Wiki 编译失败: %s", e)
        raise HTTPException(status_code=500, detail=f"Wiki 编译失败: {e}")
    return {"success": True, "page_id": page.page_id, "title": page.title, "summary": page.summary}


@router.post("/search", response_model=list[WikiSearchResult], summary="检索 Wiki 页面")
async def search_wiki(req: WikiSearchRequest, _user: UserOut = Depends(require_permission("knowledge:read"))):
    _, wiki = _get_services()
    try:
        return await wiki.search(req.query, top_k=req.top_k)
    except Exception as e:
        logger.error("Wiki 检索失败: %s", e)
        raise HTTPException(status_code=500, detail=f"Wiki 检索失败: {e}")


@router.delete("/pages/{page_id}", summary="删除 Wiki 页面")
async def delete_wiki_page(page_id: str, _user: UserOut = Depends(require_permission("knowledge:write"))):
    _, wiki = _get_services()
    wiki.delete_page(page_id)
    return {"success": True, "page_id": page_id}
