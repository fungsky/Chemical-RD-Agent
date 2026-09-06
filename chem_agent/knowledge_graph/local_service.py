"""本地数据知识服务 —— Neo4j 不可用时的降级实现。

接口签名与 KnowledgeGraphService 保持一致，数据源为项目内置样例数据
(18 个配方 / 78 种原料)。仅支持内存读写，重启后恢复样例数据。
"""

import logging
from typing import Optional

from chem_agent.models import (
    Formula,
    FormulaItem,
    FormulaSearchResult,
    PerformanceTest,
    ProcessCondition,
    RawMaterial,
)

logger = logging.getLogger(__name__)


class LocalKnowledgeService:
    """基于内置样例数据的轻量知识服务（无 Neo4j / 无 Java）。"""

    def __init__(self):
        from data.sample_data import get_all_sample_data
        sample = get_all_sample_data()
        self._materials: dict[str, RawMaterial] = {}
        for m_data in sample["materials"]:
            self._materials[m_data["name"]] = RawMaterial(**m_data)
        self._formulas: dict[str, Formula] = {}
        self._load_formulas(sample["formulas"])
        logger.info(
            "LocalKnowledgeService 就绪: %d 配方 / %d 原料（本地模式，数据不持久化）",
            len(self._formulas), len(self._materials),
        )

    def _load_formulas(self, formulas: list[dict]) -> None:
        for f_data in formulas:
            items = []
            for item_data in f_data.get("items", []):
                mat_name = item_data["material"]["name"]
                mat = self._materials.get(mat_name)
                if mat is None:
                    mat = RawMaterial(
                        name=mat_name,
                        function=item_data["material"].get("function", "其他"),
                    )
                items.append(
                    FormulaItem(
                        material=mat,
                        weight_percent=item_data["weight_percent"],
                        addition_order=item_data.get("addition_order"),
                    )
                )
            perfs = [PerformanceTest(**p) for p in f_data.get("performance", [])]
            process = ProcessCondition(**f_data["process"]) if f_data.get("process") else None
            formula = Formula.model_construct(
                name=f_data["name"],
                code=f_data["code"],
                version=f_data.get("version", "1.0"),
                category=f_data["category"],
                description=f_data.get("description"),
                items=items,
                process=process,
                performance=perfs,
                target_application=f_data.get("target_application"),
                creator=f_data.get("creator"),
                tags=f_data.get("tags", []),
                notes=f_data.get("notes"),
                status=f_data.get("status", "draft"),
            )
            self._formulas[formula.code] = formula

    # ========== 生命周期 ==========

    def connect(self) -> None:
        pass

    def close(self) -> None:
        pass

    def init_schema(self) -> None:
        pass

    def clear_all_data(self) -> dict:
        """本地模式不支持清库，直接返回 0。"""
        return {"deleted": 0}

    # ========== 原料 ==========

    def upsert_material(self, material: RawMaterial) -> str:
        self._materials[material.name] = material
        return material.name

    def get_material(self, name: str) -> Optional[RawMaterial]:
        return self._materials.get(name)

    def search_materials(
        self, keyword: str, function_filter: Optional[str] = None, limit: int = 20
    ) -> list[RawMaterial]:
        results = []
        for m in self._materials.values():
            if keyword:
                hay = " ".join(filter(None, [m.name, m.chemical_name, m.cas_number]))
                if keyword.lower() not in hay.lower():
                    continue
            if function_filter and m.function != function_filter:
                continue
            results.append(m)
        return results[:limit]

    def get_material_detail(self, name: str) -> Optional[dict]:
        m = self._materials.get(name)
        if m is None:
            return None
        related = [
            {
                "code": f.code,
                "name": f.name,
                "weight_percent": next(
                    (i.weight_percent for i in f.items if i.material.name == name), None
                ),
            }
            for f in self._formulas.values()
            if any(i.material.name == name for i in f.items)
        ]
        props = {
            k: (m.properties or {}).get(k)
            for k in ["density", "viscosity", "boiling_point", "flash_point"]
        }
        return {
            "name": m.name,
            "cas_number": m.cas_number,
            "chemical_name": m.chemical_name,
            "function": m.function,
            "supplier": m.supplier,
            "properties": {k: v for k, v in props.items() if v is not None},
            "related_formulas": related,
        }

    def get_material_usage_stats(self, material_name: str) -> dict:
        stats = {"material": material_name, "formulas": [], "avg_percent": 0.0, "count": 0}
        total = 0.0
        for f in self._formulas.values():
            for i in f.items:
                if i.material.name == material_name:
                    stats["formulas"].append(
                        {
                            "formula_name": f.name,
                            "formula_code": f.code,
                            "category": f.category,
                            "weight_percent": i.weight_percent,
                        }
                    )
                    total += i.weight_percent
        stats["count"] = len(stats["formulas"])
        if stats["count"] > 0:
            stats["avg_percent"] = round(total / stats["count"], 2)
        return stats

    # ========== 配方 ==========

    def upsert_formula(self, formula: Formula) -> str:
        self._formulas[formula.code] = formula
        for i in formula.items:
            if i.material.name not in self._materials:
                self._materials[i.material.name] = i.material
        return formula.code

    def get_formula(self, code: str) -> Optional[Formula]:
        return self._formulas.get(code)

    def update_formula_status(self, code: str, status: str) -> None:
        f = self._formulas.get(code)
        if f is not None:
            f.status = status

    def search_formulas(
        self,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        materials: Optional[list[str]] = None,
        performance_filter: Optional[dict] = None,
        limit: int = 20,
    ) -> list[FormulaSearchResult]:
        results = []
        for formula in self._formulas.values():
            if category and formula.category != category:
                continue
            if keyword:
                hay = " ".join(
                    filter(None, [formula.name, formula.description, " ".join(formula.tags)])
                )
                if keyword.lower() not in hay.lower():
                    continue
            if materials:
                formula_materials = {i.material.name for i in formula.items}
                if not set(materials).issubset(formula_materials):
                    continue
            if performance_filter:
                skip = False
                for test_name, bounds in performance_filter.items():
                    matched = [p for p in formula.performance if p.test_name == test_name]
                    if matched:
                        val = matched[0].value
                        if "min" in bounds and val < bounds["min"]:
                            skip = True
                        if "max" in bounds and val > bounds["max"]:
                            skip = True
                if skip:
                    continue
            score = self._calc_search_score(formula, keyword, materials)
            results.append(
                FormulaSearchResult(
                    formula=formula,
                    similarity_score=score,
                    match_reason=self._build_match_reason(keyword, materials, category),
                )
            )
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:limit]

    def find_similar_formulas(
        self, formula_code: str, top_k: int = 5
    ) -> list[FormulaSearchResult]:
        base = self._formulas.get(formula_code)
        if base is None:
            return []
        base_mats = {i.material.name for i in base.items}
        scored = []
        for f in self._formulas.values():
            if f.code == formula_code:
                continue
            f_mats = {i.material.name for i in f.items}
            shared = base_mats & f_mats
            if not shared:
                continue
            jaccard = len(shared) / (len(base_mats) + len(f_mats) - len(shared))
            scored.append(
                FormulaSearchResult(
                    formula=Formula(
                        name=f.name,
                        code=f.code,
                        category=f.category,
                        description=f.description,
                    ),
                    similarity_score=round(jaccard, 4),
                    match_reason=f"共同原料: {chr(44).join(sorted(shared))}",
                )
            )
        scored.sort(key=lambda x: x.similarity_score, reverse=True)
        return scored[:top_k]

    # ========== 统计 ==========

    def get_graph_stats(self) -> dict:
        rels = sum(len(f.items) for f in self._formulas.values())
        perfs = sum(len(f.performance) for f in self._formulas.values())
        return {
            "formulas": len(self._formulas),
            "materials": len(self._materials),
            "categories": len({f.category for f in self._formulas.values()}),
            "contains_rels": rels,
            "performance_tests": perfs,
        }

    def get_category_distribution(self) -> list[dict]:
        counts: dict[str, int] = {}
        for f in self._formulas.values():
            counts[f.category] = counts.get(f.category, 0) + 1
        return [
            {"category": k, "count": v}
            for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True)
        ]

    def get_top_materials(self, limit: int = 10) -> list[dict]:
        usage: dict[str, list[float]] = {}
        funcs: dict[str, str] = {}
        for f in self._formulas.values():
            for i in f.items:
                usage.setdefault(i.material.name, []).append(i.weight_percent)
                funcs.setdefault(i.material.name, i.material.function)
        rows = [
            {
                "name": name,
                "function": funcs[name],
                "usage_count": len(weights),
                "avg_percent": round(sum(weights) / len(weights), 1),
            }
            for name, weights in usage.items()
        ]
        rows.sort(key=lambda x: x["usage_count"], reverse=True)
        return rows[:limit]

    # ========== 辅助 ==========

    @staticmethod
    def _calc_search_score(
        formula: Formula,
        keyword: Optional[str] = None,
        materials: Optional[list[str]] = None,
    ) -> float:
        score = 0.5
        if keyword:
            if keyword in (formula.name or ""):
                score += 0.2
            if keyword in (formula.description or ""):
                score += 0.1
            if any(keyword in t for t in formula.tags):
                score += 0.1
        if materials:
            formula_materials = {i.material.name for i in formula.items}
            score += 0.1 * len(set(materials) & formula_materials)
        return min(score, 1.0)

    @staticmethod
    def _build_match_reason(
        keyword: Optional[str] = None,
        materials: Optional[list[str]] = None,
        category: Optional[str] = None,
    ) -> str:
        reasons = []
        if keyword:
            reasons.append(f"关键词: {keyword}")
        if materials:
            reasons.append(f"包含原料: {chr(44).join(materials)}")
        if category:
            reasons.append(f"类别: {category}")
        return "; ".join(reasons) if reasons else "基础匹配"

