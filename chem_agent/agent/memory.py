"""Agent 经验记忆服务 - 基于 ChromaDB 的跨会话经验存储与检索。"""

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import chromadb

from chem_agent.config import settings

logger = logging.getLogger(__name__)

_COLLECTION_NAME = "agent_memories"


class AgentMemoryService:
    """Agent 经验记忆：存储成功的问答对，检索相似历史经验。"""

    def __init__(self, llm_service, persist_dir: Optional[str] = None):
        """
        Parameters
        ----------
        llm_service : chem_agent.llm.LLMService
            复用其 get_embedding() 能力做向量化。
        persist_dir : str, optional
            ChromaDB 持久化目录，默认使用 settings.chroma_persist_dir。
        """
        self._llm = llm_service
        base_dir = Path(persist_dir or settings.chroma_persist_dir)
        mem_dir = base_dir / "agent_memories"
        mem_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(mem_dir))
        self._collection = self._client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "Agent 记忆服务已初始化, 当前记忆条数: %d", self._collection.count()
        )

    async def store_success(
        self,
        query: str,
        answer: str,
        tools_used: list[str],
        iterations: int,
    ) -> Optional[str]:
        """存储一次成功的 Agent 交互。

        Returns
        -------
        str or None
            记忆 ID，若跳过存储则返回 None。
        """
        # 答案过短则不值得存储
        if len(answer.strip()) < 20:
            return None

        memory_id = f"mem_{uuid.uuid4().hex[:12]}"

        try:
            query_embedding = await self._llm.get_embedding(query)
        except Exception as e:
            logger.warning("记忆向量化失败，跳过存储: %s", e)
            return None

        # 精炼答案，截断到 500 字符
        refined_answer = answer[:500] if len(answer) > 500 else answer

        try:
            self._collection.add(
                ids=[memory_id],
                embeddings=[query_embedding],
                documents=[query],
                metadatas=[{
                    "query": query[:300],
                    "answer": refined_answer,
                    "tools": ",".join(tools_used),
                    "iterations": iterations,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }],
            )
        except Exception as e:
            logger.warning("记忆存储失败: %s", e)
            return None

        # 超过最大容量时清理旧记录
        self._prune_if_needed()

        logger.debug("已存储 Agent 记忆: %s (query=%s)", memory_id, query[:50])
        return memory_id

    async def retrieve_similar(
        self,
        query: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
    ) -> list[dict]:
        """检索与 query 相似的历史经验。

        Returns
        -------
        list[dict]
            每项包含 query, answer, tools, similarity 字段。
        """
        top_k = top_k or settings.agent_memory_top_k
        threshold = threshold or settings.agent_memory_threshold

        count = self._collection.count()
        if count == 0:
            return []

        try:
            query_embedding = await self._llm.get_embedding(query)
        except Exception as e:
            logger.warning("记忆检索向量化失败: %s", e)
            return []

        try:
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, count),
                include=["metadatas", "distances"],
            )
        except Exception as e:
            logger.warning("记忆检索失败: %s", e)
            return []

        memories = []
        if results and results.get("metadatas"):
            for meta, dist in zip(results["metadatas"][0], results["distances"][0]):
                similarity = max(0.0, 1.0 - dist)
                if similarity >= threshold:
                    memories.append({
                        "query": meta.get("query", ""),
                        "answer": meta.get("answer", ""),
                        "tools": meta.get("tools", ""),
                        "similarity": round(similarity, 3),
                    })

        return memories

    def get_stats(self) -> dict:
        """返回记忆统计信息。"""
        return {"total_memories": self._collection.count()}

    def clear_all(self) -> dict:
        """清空所有 Agent 经验记忆。"""
        count = self._collection.count()
        self._client.delete_collection(name=_COLLECTION_NAME)
        self._collection = self._client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("Agent 记忆已清空，共删除 %d 条", count)
        return {"deleted_memories": count, "status": "success"}

    def _prune_if_needed(self):
        """当超过最大容量时，删除最旧的记录。"""
        max_size = settings.agent_memory_max_size
        count = self._collection.count()
        if count <= max_size:
            return

        try:
            # 获取所有记录的 ID 和时间戳
            all_data = self._collection.get(include=["metadatas"])
            if not all_data or not all_data["ids"]:
                return

            # 按时间戳排序，删除最旧的
            items = list(zip(all_data["ids"], all_data["metadatas"]))
            items.sort(key=lambda x: x[1].get("timestamp", ""), reverse=True)

            # 保留最新的 max_size 条，删除其余
            to_delete = [item_id for item_id, _ in items[max_size:]]
            if to_delete:
                self._collection.delete(ids=to_delete)
                logger.info("清理 Agent 记忆: 删除 %d 条旧记录", len(to_delete))
        except Exception as e:
            logger.warning("记忆清理失败: %s", e)
