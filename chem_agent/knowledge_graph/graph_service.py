"""Neo4j 知识图谱服务 - 配方知识图谱的构建、查询和管理"""

import logging
from typing import Optional
from contextlib import contextmanager

from neo4j import GraphDatabase, Driver

from chem_agent.config import settings
from chem_agent.models import (
    RawMaterial,
    Formula,
    FormulaItem,
    PerformanceTest,
    FormulaSearchResult,
)

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """配方知识图谱服务

    节点类型:
      - Formula: 配方
      - RawMaterial: 原材料
      - PerformanceTest: 性能测试
      - ProductCategory: 产品类别
      - Application: 应用场景

    关系类型:
      - CONTAINS: 配方 -> 原材料 (weight_percent, addition_order)
      - HAS_PERFORMANCE: 配方 -> 性能测试
      - BELONGS_TO: 配方 -> 产品类别
      - TARGETS: 配方 -> 应用场景
      - SIMILAR_TO: 配方 -> 配方 (similarity)
      - SUBSTITUTE_OF: 原材料 -> 原材料 (替代关系)
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self._uri = uri or settings.neo4j_uri
        self._user = user or settings.neo4j_user
        self._password = password or settings.neo4j_password
        self._driver: Optional[Driver] = None

    def connect(self) -> None:
        """建立 Neo4j 连接"""
        self._driver = GraphDatabase.driver(
            self._uri, auth=(self._user, self._password)
        )
        self._driver.verify_connectivity()
        logger.info("已连接到 Neo4j: %s", self._uri)

    def close(self) -> None:
        """关闭连接"""
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j 连接已关闭")

    @contextmanager
    def _session(self):
        """获取会话的上下文管理器"""
        if not self._driver:
            self.connect()
        session = self._driver.session(database=settings.neo4j_database)
        try:
            yield session
        finally:
            session.close()

    # ========== Schema 初始化 ==========

    def init_schema(self) -> None:
        """初始化图数据库 Schema（约束和索引）"""
        constraints = [
            "CREATE CONSTRAINT formula_code IF NOT EXISTS FOR (f:Formula) REQUIRE f.code IS UNIQUE",
            "CREATE CONSTRAINT material_name IF NOT EXISTS FOR (m:RawMaterial) REQUIRE m.name IS UNIQUE",
            "CREATE INDEX formula_name IF NOT EXISTS FOR (f:Formula) ON (f.name)",
            "CREATE INDEX formula_category IF NOT EXISTS FOR (f:Formula) ON (f.category)",
            "CREATE INDEX material_cas IF NOT EXISTS FOR (m:RawMaterial) ON (m.cas_number)",
            "CREATE INDEX material_function IF NOT EXISTS FOR (m:RawMaterial) ON (m.function)",
        ]
        with self._session() as session:
            for stmt in constraints:
                try:
                    session.run(stmt)
                except Exception as e:
                    logger.warning("Schema 语句执行警告: %s - %s", stmt[:60], e)
        logger.info("知识图谱 Schema 初始化完成")

    def clear_all_data(self) -> dict:
        """清空所有节点和关系，然后重新初始化 Schema。"""
        with self._session() as session:
            result = session.run("MATCH (n) DETACH DELETE n")
            summary = result.consume()
            deleted = summary.counters.nodes_deleted
        logger.info("知识图谱已清空，共删除 %d 个节点", deleted)
        self.init_schema()
        return {"deleted_nodes": deleted, "status": "success"}

    # ========== 原材料操作 ==========

    def upsert_material(self, material: RawMaterial) -> str:
        """创建或更新原材料节点"""
        query = """
        MERGE (m:RawMaterial {name: $name})
        SET m.cas_number = $cas_number,
            m.chemical_name = $chemical_name,
            m.supplier = $supplier,
            m.function = $function,
            m.safety_info = $safety_info,
            m.density = $density,
            m.viscosity = $viscosity,
            m.boiling_point = $boiling_point,
            m.flash_point = $flash_point
        RETURN elementId(m) AS id
        """
        props = material.properties or {}
        with self._session() as session:
            result = session.run(
                query,
                name=material.name,
                cas_number=material.cas_number,
                chemical_name=material.chemical_name,
                supplier=material.supplier,
                function=material.function.value,
                safety_info=material.safety_info,
                density=props.get("density"),
                viscosity=props.get("viscosity"),
                boiling_point=props.get("boiling_point"),
                flash_point=props.get("flash_point"),
            )
            record = result.single()
            return record["id"]

    def get_material(self, name: str) -> Optional[RawMaterial]:
        """根据名称获取原材料"""
        query = "MATCH (m:RawMaterial {name: $name}) RETURN m"
        with self._session() as session:
            result = session.run(query, name=name)
            record = result.single()
            if record:
                node = record["m"]
                return RawMaterial(
                    id=str(node.element_id),
                    name=node["name"],
                    cas_number=node.get("cas_number"),
                    chemical_name=node.get("chemical_name"),
                    supplier=node.get("supplier"),
                    function=node.get("function", "其他"),
                    safety_info=node.get("safety_info"),
                )
        return None

    def search_materials(
        self, keyword: str, function_filter: Optional[str] = None, limit: int = 20
    ) -> list[RawMaterial]:
        """搜索原材料"""
        where_clauses = ["m.name CONTAINS $keyword OR m.chemical_name CONTAINS $keyword"]
        params = {"keyword": keyword, "limit": limit}

        if function_filter:
            where_clauses.append("m.function = $function_filter")
            params["function_filter"] = function_filter

        query = f"""
        MATCH (m:RawMaterial)
        WHERE {' AND '.join(where_clauses)}
        RETURN m
        LIMIT $limit
        """
        materials = []
        with self._session() as session:
            result = session.run(query, **params)
            for record in result:
                node = record["m"]
                materials.append(
                    RawMaterial(
                        id=str(node.element_id),
                        name=node["name"],
                        cas_number=node.get("cas_number"),
                        chemical_name=node.get("chemical_name"),
                        supplier=node.get("supplier"),
                        function=node.get("function", "其他"),
                        safety_info=node.get("safety_info"),
                    )
                )
        return materials

    # ========== 配方操作 ==========

    def upsert_formula(self, formula: Formula) -> str:
        """创建或更新配方（含组分关系和性能数据）"""
        with self._session() as session:
            # 1) 创建/更新配方节点
            formula_query = """
            MERGE (f:Formula {code: $code})
            SET f.name = $name,
                f.version = $version,
                f.category = $category,
                f.description = $description,
                f.target_application = $target_application,
                f.creator = $creator,
                f.created_at = $created_at,
                f.tags = $tags,
                f.notes = $notes,
                f.status = $status
            RETURN elementId(f) AS id
            """
            status_val = formula.status.value if hasattr(formula.status, "value") else str(formula.status)
            result = session.run(
                formula_query,
                code=formula.code or formula.name,
                name=formula.name,
                version=formula.version,
                category=formula.category.value,
                description=formula.description,
                target_application=formula.target_application,
                creator=formula.creator,
                created_at=formula.created_at.isoformat(),
                tags=formula.tags,
                notes=formula.notes,
                status=status_val,
            )
            formula_id = result.single()["id"]

            # 2) 创建类别节点和关系
            session.run(
                """
                MERGE (c:ProductCategory {name: $category})
                WITH c
                MATCH (f:Formula {code: $code})
                MERGE (f)-[:BELONGS_TO]->(c)
                """,
                category=formula.category.value,
                code=formula.code or formula.name,
            )

            # 3) 创建应用场景节点和关系
            if formula.target_application:
                session.run(
                    """
                    MERGE (a:Application {name: $app})
                    WITH a
                    MATCH (f:Formula {code: $code})
                    MERGE (f)-[:TARGETS]->(a)
                    """,
                    app=formula.target_application,
                    code=formula.code or formula.name,
                )

            # 4) 清除旧的 CONTAINS 关系后批量创建新的
            session.run(
                "MATCH (f:Formula {code: $code})-[r:CONTAINS]->() DELETE r",
                code=formula.code or formula.name,
            )
            
            # 先确保所有原材料节点存在
            for item in formula.items:
                self.upsert_material(item.material)
            
            # 使用 UNWIND 批量创建 CONTAINS 关系
            if formula.items:
                items_data = [
                    {
                        "material_name": item.material.name,
                        "weight_percent": item.weight_percent,
                        "addition_order": item.addition_order,
                        "notes": item.notes,
                    }
                    for item in formula.items
                ]
                session.run(
                    """
                    MATCH (f:Formula {code: $code})
                    UNWIND $items AS item
                    MATCH (m:RawMaterial {name: item.material_name})
                    CREATE (f)-[:CONTAINS {
                        weight_percent: item.weight_percent,
                        addition_order: item.addition_order,
                        notes: item.notes
                    }]->(m)
                    """,
                    code=formula.code or formula.name,
                    items=items_data,
                )

            # 5) 存储工艺条件
            if formula.process:
                session.run(
                    """
                    MATCH (f:Formula {code: $code})
                    SET f.mixing_speed = $mixing_speed,
                        f.mixing_time = $mixing_time,
                        f.temperature = $temperature,
                        f.pressure = $pressure,
                        f.curing_temperature = $curing_temperature,
                        f.curing_time = $curing_time,
                        f.process_notes = $process_notes
                    """,
                    code=formula.code or formula.name,
                    mixing_speed=formula.process.mixing_speed,
                    mixing_time=formula.process.mixing_time,
                    temperature=formula.process.temperature,
                    pressure=formula.process.pressure,
                    curing_temperature=formula.process.curing_temperature,
                    curing_time=formula.process.curing_time,
                    process_notes=formula.process.notes,
                )

            # 6) 清除旧性能数据并创建新的
            session.run(
                "MATCH (f:Formula {code: $code})-[r:HAS_PERFORMANCE]->(p) DETACH DELETE p",
                code=formula.code or formula.name,
            )
            for perf in formula.performance:
                session.run(
                    """
                    MATCH (f:Formula {code: $code})
                    CREATE (p:PerformanceTest {
                        test_name: $test_name,
                        test_method: $test_method,
                        value: $value,
                        unit: $unit,
                        target_min: $target_min,
                        target_max: $target_max,
                        is_qualified: $is_qualified
                    })
                    CREATE (f)-[:HAS_PERFORMANCE]->(p)
                    """,
                    code=formula.code or formula.name,
                    test_name=perf.test_name,
                    test_method=perf.test_method,
                    value=perf.value,
                    unit=perf.unit,
                    target_min=perf.target_min,
                    target_max=perf.target_max,
                    is_qualified=perf.is_qualified,
                )

            return formula_id

    def get_formula(self, code: str) -> Optional[Formula]:
        """根据编号获取完整配方"""
        query = """
        MATCH (f:Formula {code: $code})
        OPTIONAL MATCH (f)-[r:CONTAINS]->(m:RawMaterial)
        OPTIONAL MATCH (f)-[:HAS_PERFORMANCE]->(p:PerformanceTest)
        RETURN f,
               collect(DISTINCT {material: m, rel: r}) AS items,
               collect(DISTINCT p) AS perfs
        """
        with self._session() as session:
            result = session.run(query, code=code)
            record = result.single()
            if not record:
                return None
            node = record["f"]
            items = []
            for item_data in record["items"]:
                m = item_data["material"]
                r = item_data["rel"]
                if m is not None:
                    items.append(
                        FormulaItem(
                            material=RawMaterial(
                                id=str(m.element_id),
                                name=m["name"],
                                cas_number=m.get("cas_number"),
                                function=m.get("function", "其他"),
                            ),
                            weight_percent=r["weight_percent"],
                            addition_order=r.get("addition_order"),
                            notes=r.get("notes"),
                        )
                    )
            perfs = []
            for p in record["perfs"]:
                if p is not None:
                    perfs.append(
                        PerformanceTest(
                            test_name=p["test_name"],
                            test_method=p.get("test_method"),
                            value=p["value"],
                            unit=p.get("unit", ""),
                            target_min=p.get("target_min"),
                            target_max=p.get("target_max"),
                            is_qualified=p.get("is_qualified"),
                        )
                    )
            return Formula(
                id=str(node.element_id),
                name=node["name"],
                code=node["code"],
                version=node.get("version", "1.0"),
                category=node.get("category", "其他"),
                description=node.get("description"),
                items=items,
                performance=perfs,
                target_application=node.get("target_application"),
                creator=node.get("creator"),
                tags=node.get("tags", []),
                notes=node.get("notes"),
                status=node.get("status", "draft"),
            )

    def search_formulas(
        self,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        materials: Optional[list[str]] = None,
        performance_filter: Optional[dict] = None,
        limit: int = 20,
    ) -> list[FormulaSearchResult]:
        """多条件检索配方

        Args:
            keyword: 关键词（匹配名称、描述、标签）
            category: 产品类别筛选
            materials: 必须包含的原材料名称列表
            performance_filter: 性能筛选条件 {"test_name": {"min": x, "max": y}}
            limit: 返回结果数量上限
        """
        where_clauses = []
        params: dict = {"limit": limit}

        if keyword:
            where_clauses.append(
                "(f.name CONTAINS $keyword OR f.description CONTAINS $keyword "
                "OR any(t IN f.tags WHERE t CONTAINS $keyword))"
            )
            params["keyword"] = keyword

        if category:
            where_clauses.append("f.category = $category")
            params["category"] = category

        where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        query = f"""
        MATCH (f:Formula)
        {where_str}
        OPTIONAL MATCH (f)-[r:CONTAINS]->(m:RawMaterial)
        OPTIONAL MATCH (f)-[:HAS_PERFORMANCE]->(p:PerformanceTest)
        RETURN f,
               collect(DISTINCT {{material: m, rel: r}}) AS items,
               collect(DISTINCT p) AS perfs
        LIMIT $limit
        """

        results = []
        with self._session() as session:
            records = session.run(query, **params)
            for record in records:
                node = record["f"]
                item_list = []
                for item_data in record["items"]:
                    m = item_data["material"]
                    r = item_data["rel"]
                    if m is not None:
                        item_list.append(
                            FormulaItem(
                                material=RawMaterial(
                                    name=m["name"],
                                    function=m.get("function", "其他"),
                                ),
                                weight_percent=r["weight_percent"],
                            )
                        )
                perfs = []
                for p in record["perfs"]:
                    if p is not None:
                        perfs.append(
                            PerformanceTest(
                                test_name=p["test_name"],
                                value=p["value"],
                                unit=p.get("unit", ""),
                            )
                        )

                formula = Formula(
                    id=str(node.element_id),
                    name=node["name"],
                    code=node["code"],
                    category=node.get("category", "其他"),
                    description=node.get("description"),
                    items=item_list,
                    performance=perfs,
                    tags=node.get("tags", []),
                )

                # 材料匹配过滤
                if materials:
                    formula_materials = {i.material.name for i in item_list}
                    if not set(materials).issubset(formula_materials):
                        continue

                # 性能过滤
                if performance_filter:
                    skip = False
                    for test_name, bounds in performance_filter.items():
                        matched = [p for p in perfs if p.test_name == test_name]
                        if matched:
                            val = matched[0].value
                            if "min" in bounds and val < bounds["min"]:
                                skip = True
                            if "max" in bounds and val > bounds["max"]:
                                skip = True
                    if skip:
                        continue

                # 计算相似度评分
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

    def find_similar_formulas(self, formula_code: str, top_k: int = 5) -> list[FormulaSearchResult]:
        """查找与给定配方相似的配方（基于共同原料）"""
        query = """
        MATCH (f1:Formula {code: $code})-[:CONTAINS]->(m:RawMaterial)<-[:CONTAINS]-(f2:Formula)
        WHERE f1 <> f2
        WITH f2, count(m) AS shared_materials,
             collect(m.name) AS shared_material_names
        MATCH (f1:Formula {code: $code})-[:CONTAINS]->(m1:RawMaterial)
        WITH f2, shared_materials, shared_material_names, count(m1) AS total_m1
        MATCH (f2)-[:CONTAINS]->(m2:RawMaterial)
        WITH f2, shared_materials, shared_material_names, total_m1, count(m2) AS total_m2
        WITH f2, shared_materials, shared_material_names,
             toFloat(shared_materials) / (total_m1 + total_m2 - shared_materials) AS jaccard
        ORDER BY jaccard DESC
        LIMIT $top_k
        RETURN f2, jaccard, shared_material_names
        """
        results = []
        with self._session() as session:
            records = session.run(query, code=formula_code, top_k=top_k)
            for record in records:
                node = record["f2"]
                jaccard = record["jaccard"]
                shared = record["shared_material_names"]
                formula = Formula(
                    id=str(node.element_id),
                    name=node["name"],
                    code=node["code"],
                    category=node.get("category", "其他"),
                    description=node.get("description"),
                )
                results.append(
                    FormulaSearchResult(
                        formula=formula,
                        similarity_score=round(jaccard, 4),
                        match_reason=f"共同原料: {', '.join(shared)}",
                    )
                )
        return results

    def get_material_usage_stats(self, material_name: str) -> dict:
        """获取原材料在各配方中的使用统计"""
        query = """
        MATCH (m:RawMaterial {name: $name})<-[r:CONTAINS]-(f:Formula)
        RETURN f.name AS formula_name,
               f.code AS formula_code,
               f.category AS category,
               r.weight_percent AS weight_percent
        ORDER BY r.weight_percent DESC
        """
        stats = {"material": material_name, "formulas": [], "avg_percent": 0.0, "count": 0}
        with self._session() as session:
            records = session.run(query, name=material_name)
            total = 0.0
            for record in records:
                stats["formulas"].append(
                    {
                        "formula_name": record["formula_name"],
                        "formula_code": record["formula_code"],
                        "category": record["category"],
                        "weight_percent": record["weight_percent"],
                    }
                )
                total += record["weight_percent"]
            stats["count"] = len(stats["formulas"])
            if stats["count"] > 0:
                stats["avg_percent"] = round(total / stats["count"], 2)
        return stats

    def get_graph_stats(self) -> dict:
        """获取图数据库统计信息"""
        queries = {
            "formulas": "MATCH (f:Formula) RETURN count(f) AS cnt",
            "materials": "MATCH (m:RawMaterial) RETURN count(m) AS cnt",
            "categories": "MATCH (c:ProductCategory) RETURN count(c) AS cnt",
            "contains_rels": "MATCH ()-[r:CONTAINS]->() RETURN count(r) AS cnt",
            "performance_tests": "MATCH (p:PerformanceTest) RETURN count(p) AS cnt",
        }
        stats = {}
        with self._session() as session:
            for key, query in queries.items():
                result = session.run(query)
                stats[key] = result.single()["cnt"]
        return stats

    def get_category_distribution(self) -> list[dict]:
        """获取配方类别分布统计，返回 [{"category": str, "count": int}, ...]"""
        query = """
        MATCH (f:Formula)
        RETURN f.category AS category, count(f) AS count
        ORDER BY count DESC
        """
        with self._session() as session:
            result = session.run(query)
            return [{"category": r["category"] or "未分类", "count": r["count"]} for r in result]

    def get_top_materials(self, limit: int = 10) -> list[dict]:
        """获取使用频次最高的原材料 TOP N"""
        query = """
        MATCH (m:RawMaterial)<-[r:CONTAINS]-(f:Formula)
        RETURN m.name AS name, m.function AS function, count(f) AS usage_count,
               avg(r.weight_percent) AS avg_percent
        ORDER BY usage_count DESC
        LIMIT $limit
        """
        with self._session() as session:
            result = session.run(query, limit=limit)
            return [
                {
                    "name": r["name"],
                    "function": r["function"] or "其他",
                    "usage_count": r["usage_count"],
                    "avg_percent": round(r["avg_percent"] or 0, 1),
                }
                for r in result
            ]

    def update_formula_status(self, code: str, status: str) -> None:
        """更新配方状态"""
        with self._session() as session:
            session.run(
                "MATCH (f:Formula {code: $code}) SET f.status = $status",
                code=code, status=status,
            )

    def get_material_detail(self, name: str) -> dict | None:
        """获取原材料详情，包括理化性质和关联配方"""
        with self._session() as session:
            result = session.run(
                """
                MATCH (m:RawMaterial {name: $name})
                OPTIONAL MATCH (f:Formula)-[r:CONTAINS]->(m)
                RETURN m, collect({
                    code: f.code, name: f.name, weight_percent: r.weight_percent
                }) AS related_formulas
                """,
                name=name,
            )
            record = result.single()
            if not record:
                return None
            m = dict(record["m"])
            related = [r for r in record["related_formulas"] if r.get("code")]
            return {
                "name": m.get("name"),
                "cas_number": m.get("cas_number"),
                "chemical_name": m.get("chemical_name"),
                "function": m.get("function"),
                "supplier": m.get("supplier"),
                "properties": {
                    k: m.get(k) for k in ["density", "viscosity", "boiling_point", "flash_point"]
                    if m.get(k) is not None
                },
                "related_formulas": related,
            }

    # ========== 辅助方法 ==========

    @staticmethod
    def _calc_search_score(
        formula: Formula,
        keyword: Optional[str] = None,
        materials: Optional[list[str]] = None,
    ) -> float:
        """计算检索匹配评分"""
        score = 0.5  # 基础分

        if keyword:
            if keyword in (formula.name or ""):
                score += 0.2
            if keyword in (formula.description or ""):
                score += 0.1
            if any(keyword in t for t in formula.tags):
                score += 0.1

        if materials:
            formula_materials = {i.material.name for i in formula.items}
            matched = len(set(materials) & formula_materials)
            score += 0.1 * matched

        return min(score, 1.0)

    @staticmethod
    def _build_match_reason(
        keyword: Optional[str] = None,
        materials: Optional[list[str]] = None,
        category: Optional[str] = None,
    ) -> str:
        """生成匹配原因描述"""
        reasons = []
        if keyword:
            reasons.append(f"关键词匹配: {keyword}")
        if materials:
            reasons.append(f"包含原料: {', '.join(materials)}")
        if category:
            reasons.append(f"产品类别: {category}")
        return "; ".join(reasons) if reasons else "综合匹配"
