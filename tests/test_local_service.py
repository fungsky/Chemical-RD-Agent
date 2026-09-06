"""测试 - LocalKnowledgeService（无 Neo4j 本地数据模式）。"""

import pytest

from chem_agent.knowledge_graph.local_service import LocalKnowledgeService


@pytest.fixture
def local_kg():
    return LocalKnowledgeService()


class TestLocalSearch:
    def test_graph_stats(self, local_kg):
        stats = local_kg.get_graph_stats()
        assert stats["formulas"] == 18
        assert stats["materials"] >= 78

    def test_search_formulas_keyword(self, local_kg):
        results = local_kg.search_formulas("环氧")
        assert results
        assert any(r.formula.code == "HF-001" for r in results)

    def test_search_formulas_category(self, local_kg):
        results = local_kg.search_formulas(category="涂料", limit=100)
        assert len(results) >= 8
        assert all(r.formula.category == "涂料" for r in results)

    def test_get_formula(self, local_kg):
        f = local_kg.get_formula("HF-001")
        assert f is not None
        assert f.name == "高防腐环氧底漆 HF-001"
        assert f.items
        assert local_kg.get_formula("NOPE") is None

    def test_find_similar_formulas(self, local_kg):
        results = local_kg.find_similar_formulas("HF-001", top_k=3)
        assert results
        assert all(r.formula.code != "HF-001" for r in results)
        assert results[0].similarity_score > 0

    def test_search_materials(self, local_kg):
        mats = local_kg.search_materials("环氧", limit=10)
        assert mats
        assert all("环氧" in (m.name or "") + (m.chemical_name or "") for m in mats)

    def test_material_detail_and_stats(self, local_kg):
        detail = local_kg.get_material_detail("环氧树脂E-51")
        assert detail is not None
        assert detail["name"] == "环氧树脂E-51"
        assert detail["related_formulas"]
        stats = local_kg.get_material_usage_stats("环氧树脂E-51")
        assert stats["count"] >= 1
        assert stats["avg_percent"] > 0

    def test_top_materials_and_distribution(self, local_kg):
        top = local_kg.get_top_materials(5)
        assert len(top) <= 5
        assert top[0]["usage_count"] >= top[-1]["usage_count"]
        dist = local_kg.get_category_distribution()
        assert sum(d["count"] for d in dist) == 18

