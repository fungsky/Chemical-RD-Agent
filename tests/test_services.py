"""测试 - 知识图谱服务 (Mock Neo4j)"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from chem_agent.models import (
    Formula, FormulaItem, RawMaterial, FormulaSearchResult,
    MaterialFunction, ProductCategory, ProcessCondition, PerformanceTest,
)


class TestGraphService:
    def test_init_creates_driver(self):
        """测试服务初始化时创建Neo4j驱动。"""
        with patch("chem_agent.knowledge_graph.graph_service.GraphDatabase") as mock_db:
            from chem_agent.knowledge_graph import KnowledgeGraphService
            svc = KnowledgeGraphService()
            assert svc._driver is None
            mock_db.driver.assert_not_called()
            svc.connect()
            mock_db.driver.assert_called_once()

    def test_search_formulas_mock(self):
        """测试配方搜索返回格式正确。"""
        with patch("chem_agent.knowledge_graph.graph_service.GraphDatabase") as mock_db:
            from chem_agent.knowledge_graph import KnowledgeGraphService
            svc = KnowledgeGraphService()

            # Mock session
            class _Node(dict):
                def __getattr__(self, item):
                    try:
                        return self[item]
                    except KeyError:
                        raise AttributeError(item)

            mock_session = MagicMock()
            mock_db.driver.return_value.session.return_value = mock_session
            mock_result = MagicMock()
            mock_record = MagicMock()
            mock_record.__getitem__.side_effect = lambda key: {
                "f": _Node(
                    element_id="node-1",
                    name="测试配方",
                    code="F-001",
                    category="涂料",
                    tags=[],
                ),
                "items": [],
                "perfs": [],
            }[key]
            mock_result.__iter__.return_value = [mock_record]
            mock_session.run.return_value = mock_result

            # We can't easily test the real driver, but we can test the module loads
            svc.connect()
            results = svc.search_formulas(keyword="测试")
            assert len(results) == 1
            assert results[0].formula.code == "F-001"
            assert results[0].similarity_score > 0.5

    def test_module_imports(self):
        """测试知识图谱模块可导入。"""
        from chem_agent.knowledge_graph import KnowledgeGraphService
        from chem_agent.knowledge_graph.graph_service import KnowledgeGraphService as KGS
        assert KnowledgeGraphService is KGS


class TestFormulaSearchResult:
    def test_search_result(self):
        mat = RawMaterial(name="test", function=MaterialFunction.OTHER)
        item = FormulaItem(material=mat, weight_percent=100.0)
        # Need to skip weight validation for single-component
        import pydantic
        formula = Formula(
            name="Test", code="T-001",
            category=ProductCategory.OTHER,
            items=[item],
        )
        result = FormulaSearchResult(
            formula=formula,
            similarity_score=0.88,
            match_reason="原料匹配: test",
        )
        assert result.similarity_score == 0.88
        assert "test" in result.match_reason


class TestKnowledgeBaseService:
    def test_imports_ok(self):
        """测试知识库模块可导入。"""
        from chem_agent.knowledge_base import kb_service
        assert hasattr(kb_service, "KnowledgeBaseService")

    def test_document_parser_imports(self):
        """测试文档解析模块可导入。"""
        from chem_agent.knowledge_base.document_parser import (
            parse_pdf, parse_docx, parse_txt, parse_excel, scrape_url,
        )
        assert callable(parse_pdf)
        assert callable(parse_docx)
        assert callable(parse_txt)
        assert callable(parse_excel)
        assert callable(scrape_url)
