"""测试 - Agent 工具注册与执行。"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from chem_agent.agent.models import ToolDef
from chem_agent.agent.tools import register_tools, get_registry


class TestToolRegistration:
    def test_all_tools_registered(self):
        """验证 10 个工具全部注册。"""
        kg = MagicMock()
        kb = AsyncMock()
        llm = MagicMock()
        predictor = MagicMock()

        registry = register_tools(kg, kb, llm, predictor)
        assert len(registry) == 10

        expected_tools = [
            "search_formulas",
            "get_formula_detail",
            "find_similar_formulas",
            "search_materials",
            "get_material_usage",
            "search_knowledge_base",
            "predict_performance",
            "analyze_formula",
            "suggest_substitute",
            "get_graph_stats",
        ]
        for tool_name in expected_tools:
            assert tool_name in registry
            tool_def, executor = registry[tool_name]
            assert isinstance(tool_def, ToolDef)
            assert callable(executor)

    def test_search_formulas_tool(self):
        """测试 search_formulas 工具执行。"""
        from chem_agent.models import Formula, FormulaSearchResult, ProductCategory

        kg = MagicMock()
        formula = Formula(
            name="测试配方",
            code="T-001",
            category=ProductCategory.COATING,
            items=[],
        )
        kg.search_formulas.return_value = [
            FormulaSearchResult(formula=formula, similarity_score=0.95, match_reason="keyword match")
        ]
        kb = AsyncMock()
        llm = MagicMock()
        predictor = MagicMock()

        registry = register_tools(kg, kb, llm, predictor)
        _, executor = registry["search_formulas"]

        import asyncio
        result = asyncio.run(executor({"keyword": "测试", "limit": 5}))
        assert "T-001" in result
        assert "测试配方" in result

    def test_search_materials_tool(self):
        """测试 search_materials 工具执行。"""
        from chem_agent.models import RawMaterial, MaterialFunction

        kg = MagicMock()
        kg.search_materials.return_value = [
            RawMaterial(name="环氧树脂E-51", function=MaterialFunction.BASE_RESIN, cas_number="25068-38-6")
        ]
        kb = AsyncMock()
        llm = MagicMock()
        predictor = MagicMock()

        registry = register_tools(kg, kb, llm, predictor)
        _, executor = registry["search_materials"]

        import asyncio
        result = asyncio.run(executor({"keyword": "环氧"}))
        assert "环氧树脂E-51" in result
        assert "25068-38-6" in result

    def test_search_formulas_empty_result(self):
        """测试搜索无结果。"""
        kg = MagicMock()
        kg.search_formulas.return_value = []
        kb = AsyncMock()
        llm = MagicMock()
        predictor = MagicMock()

        registry = register_tools(kg, kb, llm, predictor)
        _, executor = registry["search_formulas"]

        import asyncio
        result = asyncio.run(executor({"keyword": "不存在"}))
        assert "未找到" in result

    def test_get_formula_detail_missing_code(self):
        """测试缺少必填参数。"""
        kg = MagicMock()
        kb = AsyncMock()
        llm = MagicMock()
        predictor = MagicMock()

        registry = register_tools(kg, kb, llm, predictor)
        _, executor = registry["get_formula_detail"]

        import asyncio
        result = asyncio.run(executor({}))
        assert "错误" in result

    def test_search_kb_uninitialized(self):
        """测试知识库未初始化。"""
        kg = MagicMock()
        kb = None
        llm = MagicMock()
        predictor = MagicMock()

        registry = register_tools(kg, kb, llm, predictor)
        _, executor = registry["search_knowledge_base"]

        import asyncio
        result = asyncio.run(executor({"query": "test"}))
        assert "未初始化" in result

    def test_predict_without_training(self):
        """测试预测模型未训练。"""
        kg = MagicMock()
        kg.get_formula.return_value = None
        kb = AsyncMock()
        llm = MagicMock()
        predictor = MagicMock()
        predictor._models = {}  # 空模型

        registry = register_tools(kg, kb, llm, predictor)
        _, executor = registry["predict_performance"]

        import asyncio
        result = asyncio.run(executor({"formula_code": "T-001"}))
        assert "未找到" in result

    def test_get_graph_stats(self):
        """测试图谱统计。"""
        kg = MagicMock()
        kg.get_graph_stats.return_value = {"formulas": 100, "materials": 50}
        kb = AsyncMock()
        llm = MagicMock()
        predictor = MagicMock()

        registry = register_tools(kg, kb, llm, predictor)
        _, executor = registry["get_graph_stats"]

        import asyncio
        result = asyncio.run(executor({}))
        assert "100" in result
        assert "50" in result