"""工具注册表：将现有服务包装为 Agent 可调用的工具。"""

import json
import logging
from typing import Any, Callable, Coroutine

from chem_agent.agent.models import ToolDef

logger = logging.getLogger(__name__)


# 工具执行函数类型: async (input_dict) -> str
ToolExecutor = Callable[[dict], Coroutine[Any, Any, str]]

# 全局工具注册表: name -> (ToolDef, ToolExecutor)
_REGISTRY: dict[str, tuple[ToolDef, ToolExecutor]] = {}


def _json_safe(obj: Any) -> str:
    """将对象序列化为 JSON 字符串，处理 Pydantic 和 Enum。"""
    if hasattr(obj, "model_dump"):
        obj = obj.model_dump()
    elif hasattr(obj, "__iter__") and not isinstance(obj, (str, dict)):
        obj = [o.model_dump() if hasattr(o, "model_dump") else o for o in obj]
    return json.dumps(obj, ensure_ascii=False, default=str)


def _truncate(text: str, max_len: int = 2000) -> str:
    """截断过长的文本。"""
    if len(text) > max_len:
        return text[:max_len] + f"\n...(结果已截断，共 {len(text)} 字符)"
    return text


def register_tools(kg_service, kb_service, llm_service, predictor) -> dict[str, tuple[ToolDef, ToolExecutor]]:
    """注册全部工具，绑定服务实例。返回 {name: (ToolDef, executor)}。"""
    global _REGISTRY
    _REGISTRY = {}

    # ====== 1. search_formulas ======
    async def _search_formulas(params: dict) -> str:
        keyword = params.get("keyword")
        category = params.get("category")
        materials_str = params.get("materials")
        limit = params.get("limit", 10)
        material_list = [m.strip() for m in materials_str.split(",")] if materials_str else None
        results = kg_service.search_formulas(
            keyword=keyword, category=category, materials=material_list, limit=limit,
        )
        if not results:
            return "未找到匹配的配方。"
        summaries = []
        for r in results:
            f = r.formula
            items_brief = ", ".join(
                f"{it.material.name}({it.weight_percent}%)" for it in f.items[:5]
            )
            summaries.append({
                "code": f.code,
                "name": f.name,
                "category": f.category.value if hasattr(f.category, "value") else str(f.category),
                "components": items_brief,
                "similarity": round(r.similarity_score, 2),
            })
        return _truncate(json.dumps(summaries, ensure_ascii=False, indent=2))

    _REGISTRY["search_formulas"] = (
        ToolDef(
            name="search_formulas",
            description="搜索配方数据库。根据关键词、产品类别、原料名称等条件检索配方。",
            parameters={
                "keyword": {"type": "string", "description": "搜索关键词（可选）"},
                "category": {"type": "string", "description": "产品类别，如 涂料/胶粘剂/树脂 等（可选）"},
                "materials": {"type": "string", "description": "逗号分隔的原料名称（可选）"},
                "limit": {"type": "integer", "description": "返回数量上限，默认 10"},
            },
            permission="formula:read",
        ),
        _search_formulas,
    )

    # ====== 2. get_formula_detail ======
    async def _get_formula_detail(params: dict) -> str:
        code = params.get("code", "")
        if not code:
            return "错误：请提供配方编号 code。"
        formula = kg_service.get_formula(code)
        if not formula:
            return f"未找到编号为 '{code}' 的配方。"
        return _truncate(_json_safe(formula))

    _REGISTRY["get_formula_detail"] = (
        ToolDef(
            name="get_formula_detail",
            description="获取配方详情。根据配方编号查询完整的配方信息，包含组分、工艺、性能数据。",
            parameters={
                "code": {"type": "string", "description": "配方编号（必填）"},
            },
            permission="formula:read",
        ),
        _get_formula_detail,
    )

    # ====== 3. find_similar_formulas ======
    async def _find_similar(params: dict) -> str:
        code = params.get("formula_code", "")
        top_k = params.get("top_k", 5)
        if not code:
            return "错误：请提供配方编号 formula_code。"
        results = kg_service.find_similar_formulas(code, top_k=top_k)
        if not results:
            return f"未找到与 '{code}' 相似的配方。"
        summaries = []
        for r in results:
            f = r.formula
            summaries.append({
                "code": f.code,
                "name": f.name,
                "category": f.category.value if hasattr(f.category, "value") else str(f.category),
                "similarity": round(r.similarity_score, 2),
                "match_reason": r.match_reason,
            })
        return _truncate(json.dumps(summaries, ensure_ascii=False, indent=2))

    _REGISTRY["find_similar_formulas"] = (
        ToolDef(
            name="find_similar_formulas",
            description="查找相似配方。根据配方编号，基于共同原料的 Jaccard 相似度查找最相似的配方。",
            parameters={
                "formula_code": {"type": "string", "description": "基准配方编号（必填）"},
                "top_k": {"type": "integer", "description": "返回数量，默认 5"},
            },
            permission="formula:read",
        ),
        _find_similar,
    )

    # ====== 4. search_materials ======
    async def _search_materials(params: dict) -> str:
        keyword = params.get("keyword", "")
        function_filter = params.get("function")
        limit = params.get("limit", 20)
        if not keyword:
            return "错误：请提供搜索关键词 keyword。"
        results = kg_service.search_materials(keyword, function_filter=function_filter, limit=limit)
        if not results:
            return f"未找到关键词为 '{keyword}' 的原材料。"
        summaries = []
        for m in results:
            summaries.append({
                "name": m.name,
                "cas_number": m.cas_number,
                "chemical_name": m.chemical_name,
                "function": m.function.value if hasattr(m.function, "value") else str(m.function),
                "supplier": m.supplier,
            })
        return _truncate(json.dumps(summaries, ensure_ascii=False, indent=2))

    _REGISTRY["search_materials"] = (
        ToolDef(
            name="search_materials",
            description="搜索原材料数据库。根据关键词和功能分类查找原材料信息。",
            parameters={
                "keyword": {"type": "string", "description": "搜索关键词（必填）"},
                "function": {"type": "string", "description": "功能分类筛选，如 基础树脂/溶剂/填料 等（可选）"},
                "limit": {"type": "integer", "description": "返回数量上限，默认 20"},
            },
            permission="material:read",
        ),
        _search_materials,
    )

    # ====== 5. get_material_usage ======
    async def _get_material_usage(params: dict) -> str:
        name = params.get("material_name", "")
        if not name:
            return "错误：请提供原料名称 material_name。"
        stats = kg_service.get_material_usage_stats(name)
        return _truncate(json.dumps(stats, ensure_ascii=False, indent=2))

    _REGISTRY["get_material_usage"] = (
        ToolDef(
            name="get_material_usage",
            description="获取原材料使用统计。查看某种原料在多少个配方中使用、平均用量百分比及具体使用情况。",
            parameters={
                "material_name": {"type": "string", "description": "原料名称（必填）"},
            },
            permission="material:read",
        ),
        _get_material_usage,
    )

    # ====== 6. search_knowledge_base ======
    async def _search_kb(params: dict) -> str:
        query = params.get("query", "")
        top_k = params.get("top_k", 3)
        if not query:
            return "错误：请提供检索内容 query。"
        if kb_service is None:
            return "知识库服务未初始化。"
        results = await kb_service.search(query, top_k=top_k)
        if not results:
            return "知识库中未找到相关内容。"
        summaries = []
        for r in results:
            summaries.append({
                "filename": r.filename,
                "similarity": round(r.similarity_score, 2),
                "content": r.content[:500],
                "source_type": r.source_type,
            })
        return _truncate(json.dumps(summaries, ensure_ascii=False, indent=2))

    _REGISTRY["search_knowledge_base"] = (
        ToolDef(
            name="search_knowledge_base",
            description="语义检索知识库。在上传的文档（PDF/Word/TXT/网页）中进行向量相似度搜索，返回最相关的内容片段。",
            parameters={
                "query": {"type": "string", "description": "检索内容（必填）"},
                "top_k": {"type": "integer", "description": "返回条数，默认 3"},
            },
            permission="knowledge:read",
        ),
        _search_kb,
    )

    # ====== 7. predict_performance ======
    async def _predict_performance(params: dict) -> str:
        code = params.get("formula_code", "")
        target_props = params.get("target_properties", [])
        if not code:
            return "错误：请提供配方编号 formula_code。"
        formula = kg_service.get_formula(code)
        if not formula:
            return f"未找到编号为 '{code}' 的配方，无法进行预测。"
        if not predictor._models:
            return "预测模型尚未训练，请先在性能预测页面训练模型。"
        from chem_agent.models import PredictionRequest
        req = PredictionRequest(
            items=formula.items,
            category=formula.category,
            process=formula.process,
            target_properties=target_props if target_props else list(predictor._models.keys()),
        )
        try:
            results = predictor.predict(req)
            summaries = []
            for r in results:
                summaries.append({
                    "property": r.property_name,
                    "predicted_value": round(r.predicted_value, 3),
                    "unit": r.unit,
                    "confidence": round(r.confidence, 2),
                    "explanation": r.explanation,
                })
            return json.dumps(summaries, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"预测失败: {e}"

    _REGISTRY["predict_performance"] = (
        ToolDef(
            name="predict_performance",
            description="预测配方性能。根据配方编号查询配方数据，使用机器学习模型预测性能指标（如硬度、光泽度等）。",
            parameters={
                "formula_code": {"type": "string", "description": "配方编号（必填）"},
                "target_properties": {"type": "array", "description": "要预测的性能名称列表（可选，为空则预测全部可用指标）"},
            },
            permission="prediction:read",
        ),
        _predict_performance,
    )

    # ====== 8. analyze_formula ======
    async def _analyze_formula(params: dict) -> str:
        code = params.get("formula_code", "")
        if not code:
            return "错误：请提供配方编号 formula_code。"
        formula = kg_service.get_formula(code)
        if not formula:
            return f"未找到编号为 '{code}' 的配方。"
        try:
            analysis = await llm_service.analyze_formula(formula)
            return _truncate(analysis)
        except Exception as e:
            return f"配方分析失败: {e}"

    _REGISTRY["analyze_formula"] = (
        ToolDef(
            name="analyze_formula",
            description="AI 深度分析配方。根据配方编号获取配方详情，然后用 AI 对配方的组分配比、工艺条件和性能进行专业分析。",
            parameters={
                "formula_code": {"type": "string", "description": "配方编号（必填）"},
            },
            permission="formula:analyze",
        ),
        _analyze_formula,
    )

    # ====== 9. suggest_substitute ======
    async def _suggest_substitute(params: dict) -> str:
        material_name = params.get("material_name", "")
        function = params.get("function", "其他")
        usage = params.get("current_usage", "")
        if not material_name:
            return "错误：请提供原料名称 material_name。"
        stats = kg_service.get_material_usage_stats(material_name)
        try:
            suggestion = await llm_service.suggest_substitute(
                material_name=material_name,
                material_function=function,
                current_usage=usage,
                usage_stats=stats,
            )
            return _truncate(suggestion)
        except Exception as e:
            return f"替代建议生成失败: {e}"

    _REGISTRY["suggest_substitute"] = (
        ToolDef(
            name="suggest_substitute",
            description="AI 原材料替代建议。为指定原料推荐替代材料，并分析替代后对配方性能的影响。",
            parameters={
                "material_name": {"type": "string", "description": "原料名称（必填）"},
                "function": {"type": "string", "description": "原料功能分类（可选）"},
                "current_usage": {"type": "string", "description": "当前用途描述（可选）"},
            },
            permission="material:substitute",
        ),
        _suggest_substitute,
    )

    # ====== 10. get_graph_stats ======
    async def _get_graph_stats(params: dict) -> str:
        try:
            stats = kg_service.get_graph_stats()
            return json.dumps(stats, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"获取统计失败: {e}"

    _REGISTRY["get_graph_stats"] = (
        ToolDef(
            name="get_graph_stats",
            description="获取知识图谱统计信息。查看配方总数、原材料种类数、关系数量等数据库概况。",
            parameters={},
            permission="chat:access",
        ),
        _get_graph_stats,
    )

    logger.info("已注册 %d 个 Agent 工具: %s", len(_REGISTRY), list(_REGISTRY.keys()))
    return _REGISTRY


def get_registry() -> dict[str, tuple[ToolDef, ToolExecutor]]:
    """获取当前工具注册表。"""
    return _REGISTRY
