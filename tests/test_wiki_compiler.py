"""LLM Wiki 编译测试。"""

import json

import pytest
from langchain_core.messages import AIMessage

from chem_agent.wiki.compiler import compile_to_page


class _FakeLLM:
    def __init__(self, content: str):
        self._content = content

    async def ainvoke(self, messages):
        return AIMessage(content=self._content)


@pytest.mark.asyncio
async def test_compile_parses_json_page():
    payload = {
        "title": "水性丙烯酸外墙涂料知识页",
        "aliases": ["外墙涂料"],
        "summary": "用于外墙的水性丙烯酸涂料。",
        "sections": [
            {"heading": "用途", "body": "建筑外墙装饰与保护。"},
            {"heading": "注意事项", "body": "施工温度不低于 5℃。"},
        ],
        "links": ["丙烯酸树脂"],
    }
    llm = _FakeLLM(json.dumps(payload, ensure_ascii=False))
    page = await compile_to_page(llm, "外墙涂料.docx", ["涂料应避免低温施工。"])

    assert page.title == payload["title"]
    assert page.aliases == payload["aliases"]
    assert len(page.sections) == 2
    assert page.source_docs == ["外墙涂料.docx"]


@pytest.mark.asyncio
async def test_compile_falls_back_on_invalid_json():
    llm = _FakeLLM("not json at all")
    page = await compile_to_page(llm, "坏文档.txt", ["只有一行原文。"])

    assert page.title == "坏文档.txt"
    assert page.sections
    assert "只有一行原文" in page.to_markdown()
