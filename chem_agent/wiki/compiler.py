"""文档→Wiki 页面编译：LLM 生成结构化知识页，失败时降级为摘要页。"""

import json
import logging
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage

from chem_agent.wiki.models import WikiPage, WikiSection

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """你是一名化工研发知识编译引擎。任务：把提供的技术文档编译成结构化 Wiki 页面，供后续 LLM 检索与引用。
必须输出合法 JSON（不要 Markdown 代码块、不要多余文字），字段：
{
  "title": "简短标题",
  "aliases": ["别名1", "别名2"],
  "summary": "不超过 300 字、可直接注入 LLM 上下文的综述",
  "sections": [{"heading": "章节名", "body": "章节内容"}],
  "links": ["相关词条"],
  "key_facts": [{"claim": "结论", "source_index": 0}]
}
要求：
1. 只依据文档内容，禁止编造数据；
2. 涉及法规限量/SDS 安全数据时原文照录并注明来源序号；
3. sections 用 markdown 正文，配方含量、标准号、工艺条件保持原样；
4. 化学物质使用标准名称，保留 CAS 号。"""


def _truncate_chunks(chunks: list[str], max_chars: int = 30000) -> list[str]:
    parts = []
    total = 0
    for chunk in chunks:
        if total >= max_chars:
            break
        parts.append(chunk)
        total += len(chunk)
    return parts


async def compile_to_page(llm, filename: str, chunks: list[str], chunk_size: int = 1200) -> WikiPage:
    """用 LLM 编译文档；LLM 不可用或输出非法时生成原文摘要降级页。"""
    fallback = _fallback_page(filename, chunks)
    limited = _truncate_chunks(chunks)
    if not limited:
        return fallback

    source_text = "\n\n".join(
        f"[{i}] {c[:chunk_size]}" for i, c in enumerate(limited)
    )
    human = (
        f"文档名：{filename}\n"
        f"文档共 {len(chunks)} 个分块，以下展示前 {len(limited)} 个：\n\n"
        f"{source_text}\n\n"
        "请输出上述 JSON。"
    )
    try:
        response = await llm.ainvoke(
            [
                SystemMessage(content=_SYSTEM_PROMPT),
                HumanMessage(content=human),
            ]
        )
        content = getattr(response, "content", "") or ""
        text = content.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:].strip()
        data = json.loads(text)
        sections = [
            WikiSection(heading=str(s.get("heading", "正文")).strip() or "正文",
                        body=str(s.get("body", "")).strip())
            for s in data.get("sections", [])
            if isinstance(s, dict)
        ]
        return WikiPage(
            page_id="",
            title=str(data.get("title") or filename)[:200],
            aliases=[str(a)[:100] for a in data.get("aliases", [])][:8],
            summary=str(data.get("summary") or "")[:1000],
            sections=sections or [WikiSection(heading="摘要", body=str(data.get("summary") or "")[:2000])],
            links=[str(l)[:100] for l in data.get("links", [])][:20],
            source_docs=[filename],
            status="draft",
        )
    except Exception as e:
        logger.warning("Wiki 编译失败，使用降级摘要页: %s", e)
        return fallback


def _fallback_page(filename: str, chunks: list[str]) -> WikiPage:
    body = "\n\n".join(chunks)[:6000]
    return WikiPage(
        page_id="",
        title=filename,
        aliases=[],
        summary=body[:300],
        sections=[WikiSection(heading="原文摘录", body=body)],
        source_docs=[filename],
        status="draft",
    )
