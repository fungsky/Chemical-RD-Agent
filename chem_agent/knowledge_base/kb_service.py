"""知识库服务：基于 ChromaDB 的文档向量存储与检索。"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import chromadb

from chem_agent.config import settings
from chem_agent.knowledge_base.document_parser import chunk_text
from chem_agent.knowledge_base.models import DocumentMeta, KBStats, SearchResult

logger = logging.getLogger(__name__)

_COLLECTION_NAME = "chem_documents"


class KnowledgeBaseService:
    """ChromaDB 知识库服务。"""

    def __init__(self, llm_service):
        """
        Parameters
        ----------
        llm_service : chem_agent.llm.LLMService
            复用其 embedding 能力（get_embedding / get_embeddings）。
        """
        self._llm = llm_service
        persist_dir = Path(settings.chroma_persist_dir)
        persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(persist_dir))
        self._collection = self._client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "知识库服务已初始化, 持久化目录: %s, 当前片段数: %d",
            persist_dir,
            self._collection.count(),
        )

    # ============ 文档管理 ============

    async def add_document(
        self,
        filename: str,
        content: str,
        source_type: str,
        uploader: Optional[str] = None,
        file_size: int = 0,
    ) -> DocumentMeta:
        """解析文本、分块、向量化并存入 ChromaDB。"""
        doc_id = uuid.uuid4().hex
        chunks = chunk_text(content)
        if not chunks:
            raise ValueError("文档内容为空，无法分块")

        # 批量向量化
        embeddings = await self._llm.get_embeddings(chunks)

        # 准备 ChromaDB 数据
        ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "doc_id": doc_id,
                "filename": filename,
                "source_type": source_type,
                "chunk_index": i,
                "uploader": uploader or "",
            }
            for i in range(len(chunks))
        ]

        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )

        meta = DocumentMeta(
            doc_id=doc_id,
            filename=filename,
            source_type=source_type,
            upload_time=datetime.now(timezone.utc).isoformat(),
            file_size=file_size,
            num_chunks=len(chunks),
            uploader=uploader,
        )
        logger.info("文档已入库: %s (%s), %d 片段", filename, doc_id, len(chunks))
        return meta

    async def search(self, query: str, top_k: Optional[int] = None) -> list[SearchResult]:
        """语义检索，返回相似度最高的片段。"""
        k = top_k or settings.rag_top_k
        if self._collection.count() == 0:
            return []

        query_embedding = await self._llm.get_embedding(query)
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(k, self._collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        search_results = []
        if results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0]
            for doc, meta, dist in zip(docs, metas, distances):
                # ChromaDB cosine distance → similarity = 1 - distance
                similarity = max(0.0, 1.0 - dist)
                search_results.append(
                    SearchResult(
                        content=doc,
                        doc_id=meta.get("doc_id", ""),
                        filename=meta.get("filename", ""),
                        source_type=meta.get("source_type", ""),
                        similarity_score=similarity,
                        chunk_index=meta.get("chunk_index", 0),
                    )
                )
        return search_results

    def list_documents(self) -> list[DocumentMeta]:
        """列出所有文档（按 doc_id 聚合）。"""
        total = self._collection.count()
        if total == 0:
            return []

        # 获取所有 metadata
        all_data = self._collection.get(include=["metadatas"])
        metas = all_data.get("metadatas", [])

        # 按 doc_id 聚合
        doc_map: dict[str, dict] = {}
        for m in metas:
            did = m.get("doc_id", "")
            if did not in doc_map:
                doc_map[did] = {
                    "doc_id": did,
                    "filename": m.get("filename", ""),
                    "source_type": m.get("source_type", ""),
                    "uploader": m.get("uploader", ""),
                    "num_chunks": 0,
                }
            doc_map[did]["num_chunks"] += 1

        return [
            DocumentMeta(
                doc_id=d["doc_id"],
                filename=d["filename"],
                source_type=d["source_type"],
                upload_time="",
                num_chunks=d["num_chunks"],
                uploader=d["uploader"] or None,
            )
            for d in doc_map.values()
        ]

    def get_document_chunks(self, doc_id: str, limit: int = 5) -> list[str]:
        """获取指定文档的前 N 个 chunk 文本。"""
        try:
            results = self._collection.get(
                where={"doc_id": doc_id},
                limit=limit,
                include=["documents"],
            )
            return results.get("documents", []) or []
        except Exception as e:
            logger.error("获取文档 chunks 失败: %s", e)
            return []

    def delete_document(self, doc_id: str) -> bool:
        """删除指定文档的所有片段。"""
        try:
            all_data = self._collection.get(
                where={"doc_id": doc_id},
                include=[],
            )
            ids = all_data.get("ids", [])
            if not ids:
                return False
            self._collection.delete(ids=ids)
            logger.info("文档已删除: %s, 共 %d 片段", doc_id, len(ids))
            return True
        except Exception as e:
            logger.error("删除文档失败 %s: %s", doc_id, e)
            return False

    def get_stats(self) -> KBStats:
        """知识库统计。"""
        total_chunks = self._collection.count()
        docs = self.list_documents()
        return KBStats(total_documents=len(docs), total_chunks=total_chunks)

    def clear_all(self) -> dict:
        """清空知识库中的所有文档。"""
        count = self._collection.count()
        self._client.delete_collection(name=_COLLECTION_NAME)
        self._collection = self._client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("知识库已清空，共删除 %d 个片段", count)
        return {"deleted_chunks": count, "status": "success"}
