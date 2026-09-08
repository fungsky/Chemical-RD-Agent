"""Wiki 页面存储与检索服务（ChromaDB，独立 collection）。"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

import chromadb

from chem_agent.config import settings
from chem_agent.wiki.compiler import compile_to_page
from chem_agent.wiki.models import WikiPage, WikiSearchResult

logger = logging.getLogger(__name__)

_COLLECTION_NAME = "chem_wiki_pages"


class WikiService:
    def __init__(self, llm_service, persist_dir: Optional[str] = None):
        self._llm = llm_service
        persist_path = persist_dir or settings.chroma_persist_dir
        import pathlib
        pathlib.Path(persist_path).mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(persist_path))
        self._collection = self._client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    async def compile_document(self, filename: str, chunks: list[str]) -> WikiPage:
        page = await compile_to_page(self._llm.llm, filename, chunks)
        page.page_id = uuid.uuid4().hex
        page.updated_at = datetime.now(timezone.utc).isoformat()
        embedding = await self._llm.get_embedding(page.to_markdown())
        self._collection.upsert(
            ids=[page.page_id],
            embeddings=[embedding],
            documents=[page.to_markdown()],
            metadatas=[{
                "page_id": page.page_id,
                "title": page.title,
                "aliases": json.dumps(page.aliases, ensure_ascii=False),
                "source_docs": json.dumps(page.source_docs, ensure_ascii=False),
                "status": page.status,
                "created_at": page.created_at,
                "updated_at": page.updated_at,
            }],
        )
        logger.info("Wiki 页面已生成: %s (%s)", page.title, page.page_id)
        return page

    async def search(self, query: str, top_k: int = 3) -> list[WikiSearchResult]:
        if self._collection.count() == 0:
            return []
        query_embedding = await self._llm.get_embedding(query)
        k = min(top_k, self._collection.count())
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )
        items = []
        if not results or not results["documents"]:
            return items
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            items.append(WikiSearchResult(
                page_id=meta.get("page_id", meta.get("doc_id", "")),
                title=meta.get("title", "未命名"),
                content=doc,
                similarity_score=max(0.0, 1.0 - dist),
            ))
        return items

    def list_pages(self) -> list[dict]:
        total = self._collection.count()
        if total == 0:
            return []
        data = self._collection.get(include=["metadatas"])
        metas = data.get("metadatas", [])
        ids = data.get("ids", [])
        pages = []
        for pid, meta in zip(ids, metas):
            pages.append({
                "page_id": pid,
                "title": meta.get("title", ""),
                "status": meta.get("status", ""),
                "created_at": meta.get("created_at", ""),
                "updated_at": meta.get("updated_at", ""),
            })
        return pages

    def get_page(self, page_id: str) -> Optional[dict]:
        data = self._collection.get(ids=[page_id], include=["documents", "metadatas"])
        if not data.get("ids"):
            return None
        meta = (data.get("metadatas") or [{}])[0]
        docs = data.get("documents") or [""]
        return {
            "page_id": page_id,
            "title": meta.get("title", ""),
            "status": meta.get("status", "draft"),
            "content": docs[0] if docs else "",
            "source_docs": json.loads(meta.get("source_docs", "[]")),
            "aliases": json.loads(meta.get("aliases", "[]")),
            "created_at": meta.get("created_at", ""),
            "updated_at": meta.get("updated_at", ""),
            "revision_log": json.loads(meta.get("revision_log", "[]")),
        }

    async def update_page(
        self,
        page_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        status: Optional[str] = None,
        changed_by: Optional[str] = None,
    ) -> dict:
        current = self.get_page(page_id)
        if not current:
            raise ValueError("Wiki 页面不存在")

        new_title = (title or current["title"]).strip()
        new_content = (content or current["content"]).strip()
        if not new_title or not new_content:
            raise ValueError("标题和内容不能为空")

        old_log = current.get("revision_log") or []
        revision = {
            "changed_by": changed_by,
            "changed_at": datetime.now(timezone.utc).isoformat(),
            "old_title": current["title"],
            "old_preview": (current["content"] or "")[:200],
        }
        old_log.insert(0, revision)
        old_log = old_log[:5]
        now = datetime.now(timezone.utc).isoformat()
        embedding = await self._llm.get_embedding(new_content)
        self._collection.upsert(
            ids=[page_id],
            embeddings=[embedding],
            documents=[new_content],
            metadatas=[{
                "page_id": page_id,
                "title": new_title,
                "aliases": json.dumps(current.get("aliases") or [], ensure_ascii=False),
                "source_docs": json.dumps(current.get("source_docs") or [], ensure_ascii=False),
                "status": (status or current["status"]).strip() or "draft",
                "created_at": current.get("created_at", now),
                "updated_at": now,
                "revision_log": json.dumps(old_log, ensure_ascii=False),
            }],
        )
        return self.get_page(page_id) or {}

    def delete_page(self, page_id: str) -> bool:
        self._collection.delete(ids=[page_id])
        return True

    def count(self) -> int:
        return self._collection.count()
