"""LLM 服务 - 统一多 Provider 支持（12+ 主流 LLM 提供商）"""

import asyncio
import logging
from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings as LCOpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser

from chem_agent.config import settings
from chem_agent.models import Formula, FormulaSearchResult

logger = logging.getLogger(__name__)


def _normalize_recommended_formula(data: dict) -> Optional[dict]:
    """把 LLM 输出的松散配方 JSON 规整为 Formula 可接受的字段。"""
    import re

    function_fix = {
        "助剂": "其他",
        "表面活性剂": "其他",
        "单体": "其他",
        "树脂": "基础树脂",
        "基料": "基础树脂",
        "成膜物": "基础树脂",
        "树脂基料": "基础树脂",
        "颜料和填料": "颜料",
        "颜填料": "颜料",
        "溶剂/水": "溶剂",
        "功能助剂": "其他",
        "成膜助剂": "其他",
        "润湿分散剂": "分散剂",
        "交联剂": "固化剂",
        "": "其他",
    }
    valid_functions = {
        "基础树脂", "溶剂", "填料", "颜料", "固化剂", "催化剂",
        "分散剂", "流平剂", "消泡剂", "增稠剂", "增塑剂",
        "抗氧化剂", "紫外稳定剂", "阻燃剂", "偶联剂", "润湿剂", "其他",
    }
    raw_items = data.get("items") if isinstance(data.get("items"), list) else []
    items = []
    for it in raw_items:
        if not isinstance(it, dict):
            continue
        material = it.get("material")
        if not isinstance(material, dict):
            continue
        try:
            weight = float(it.get("weight_percent"))
        except (TypeError, ValueError):
            continue
        name = str(material.get("name", "")).strip()
        if not name:
            continue
        func_raw = str(material.get("function", "其他")).strip()
        func = function_fix.get(func_raw, func_raw)
        if func not in valid_functions:
            func = "其他"
        mat = {"name": name, "function": func}
        if material.get("cas_number"):
            mat["cas_number"] = material.get("cas_number")
        items.append({"material": mat, "weight_percent": round(weight, 2)})

    if not items:
        return None

    total = sum(i["weight_percent"] for i in items)
    if not 95.0 <= total <= 105.0:
        factor = 100.0 / total if total > 0 else 1.0
        for i in items:
            i["weight_percent"] = round(i["weight_percent"] * factor, 2)

    process = {}
    if isinstance(data.get("process"), dict):
        for key in ("temperature", "mixing_speed", "mixing_time", "pressure", "curing_temperature", "curing_time"):
            val = data["process"].get(key)
            try:
                if val is not None:
                    process[key] = float(val)
            except (TypeError, ValueError):
                process[key] = None

    performance = []
    raw_perf = data.get("performance") if isinstance(data.get("performance"), list) else []
    for p in raw_perf:
        if not isinstance(p, dict):
            continue
        test_name = str(p.get("test_name") or p.get("metric") or "").strip()
        val = p.get("value")
        if isinstance(val, str):
            m = re.search(r"[-+]?\d*\.?\d+", val)
            val = float(m.group()) if m else None
        try:
            value = float(val)
        except (TypeError, ValueError):
            continue
        if test_name:
            performance.append({"test_name": test_name, "value": value, "unit": str(p.get("unit") or "")})

    return {
        "name": str(data.get("name") or "AI推荐配方"),
        "code": None,
        "category": data.get("category") or "其他",
        "description": data.get("description") or "",
        "items": items,
        "process": process or None,
        "performance": performance,
        "tags": [],
    }

# ============ Prompt 模板 ============

SYSTEM_PROMPT = """你是一个专业的化工研发智能助手（ChemAgent），专注于帮助研发人员进行配方开发工作。

你的能力包括：
1. 分析和解读化工配方，包括组分、工艺条件和性能指标
2. 基于知识图谱检索历史配方案例
3. 基于知识库文档提供专业参考
4. 提供配方优化建议
5. 解释原材料的功能和特性
6. 预测配方性能趋势

在回答时请遵循以下原则：
- 使用专业但易懂的中文回答
- 如果提供了参考资料，请优先基于参考资料回答，并在回答中注明引用来源（文档名称）
- 引用具体的数据和案例来支撑观点
- 如果不确定，明确告知用户并提供参考方向
- 注意安全性提醒，尤其是涉及危险化学品时
- 不要编造不存在的数据或案例

当前知识库统计: {graph_stats}
{rag_context}"""

FORMULA_ANALYSIS_PROMPT = """请对以下配方进行专业分析：

配方名称: {formula_name}
产品类别: {category}
配方描述: {description}

配方组分:
{formula_items}

工艺条件:
{process_conditions}

性能测试结果:
{performance_data}

请从以下维度进行分析：
1. 配方组成合理性分析
2. 各组分的功能作用说明
3. 工艺条件适配性评价
4. 性能指标达标情况
5. 可能的优化方向和建议
"""

FORMULA_RECOMMENDATION_PROMPT = """基于以下需求和参考案例，请给出配方推荐建议：

需求描述: {requirement}
产品类别: {category}
目标性能指标:
{target_performance}

参考的历史配方案例:
{reference_formulas}

请提供：
1. 推荐的基础配方方案
2. 关键组分选择理由
3. 建议的工艺条件范围
4. 预期性能评估
5. 需要注意的风险点
"""

MATERIAL_SUBSTITUTE_PROMPT = """请分析以下原材料的替代方案：

原材料: {material_name}
功能分类: {material_function}
当前用途: {current_usage}

在知识库中该原料的使用情况:
{usage_stats}

请提供：
1. 可能的替代材料列表及其特性比较
2. 替代后对配方性能的可能影响
3. 替代方案的成本考量
4. 切换替代材料时的注意事项
"""


class LLMService:
    """LLM 智能服务 — 统一支持 12+ 主流 LLM 提供商"""

    def __init__(self):
        self._llm: Optional[BaseChatModel] = None
        self._embeddings: Optional[Embeddings] = None

    # ---------- 工厂方法 ----------

    @staticmethod
    def _create_chat_model() -> BaseChatModel:
        """根据 settings.llm_provider 创建 Chat 模型实例

        路由逻辑:
          - ollama        → ChatOllama
          - azure_openai  → AzureChatOpenAI
          - 其他全部       → ChatOpenAI (OpenAI 兼容 API)
        """
        provider = settings.llm_provider
        if not provider:
            raise RuntimeError("LLM 尚未配置，请在管理后台设置 LLM 提供商")

        if provider == "ollama":
            logger.info("创建 Ollama Chat 模型: %s @ %s",
                        settings.llm_model, settings.llm_base_url)
            return ChatOllama(
                base_url=settings.llm_base_url,
                model=settings.llm_model,
                temperature=settings.llm_temperature,
                num_predict=settings.llm_max_tokens,
            )

        if provider == "azure_openai":
            from langchain_openai import AzureChatOpenAI
            logger.info("创建 Azure OpenAI Chat 模型: deployment=%s @ %s",
                        settings.azure_deployment_name, settings.llm_base_url)
            return AzureChatOpenAI(
                azure_endpoint=settings.llm_base_url,
                azure_deployment=settings.azure_deployment_name,
                api_version=settings.azure_api_version,
                api_key=settings.llm_api_key,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
            )

        # 所有 OpenAI 兼容 Provider (openai, deepseek, zhipu, qwen, moonshot, ...)
        logger.info("创建 OpenAI 兼容 Chat 模型 [%s]: %s @ %s",
                    provider, settings.llm_model, settings.llm_base_url)
        return ChatOpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key or "not-needed",
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
        )

    @staticmethod
    def _create_embedding_model() -> Embeddings:
        """根据 settings.embedding_provider 创建 Embedding 模型实例

        特殊: embedding_provider == "same_as_llm" 时复用 LLM 的连接配置。
        """
        provider = settings.embedding_provider
        base_url = settings.embedding_base_url
        api_key = settings.embedding_api_key
        model = settings.embedding_model

        # "同 LLM 提供商" — 复用 LLM 的 base_url / api_key
        if provider == "same_as_llm" or not provider:
            if not settings.llm_provider:
                raise RuntimeError(
                    "Embedding 使用「同 LLM 提供商」模式，但 LLM 尚未配置。"
                    "请先在管理后台配置 LLM 设置。"
                )
            provider = settings.llm_provider
            base_url = settings.llm_base_url
            api_key = settings.llm_api_key

        if not provider:
            raise RuntimeError("Embedding 尚未配置，请在管理后台设置提供商")

        if provider == "ollama":
            logger.info("创建 Ollama Embedding 模型: %s @ %s", model, base_url)
            return OllamaEmbeddings(
                base_url=base_url,
                model=model,
            )

        if provider == "azure_openai":
            from langchain_openai import AzureOpenAIEmbeddings
            logger.info("创建 Azure OpenAI Embedding: deployment=%s @ %s",
                        settings.azure_deployment_name, base_url)
            return AzureOpenAIEmbeddings(
                azure_endpoint=base_url,
                azure_deployment=settings.azure_deployment_name,
                api_version=settings.azure_api_version,
                api_key=api_key,
            )

        # 所有 OpenAI 兼容 Provider
        logger.info("创建 OpenAI 兼容 Embedding [%s]: %s @ %s", provider, model, base_url)
        return LCOpenAIEmbeddings(
            base_url=base_url,
            api_key=api_key or "not-needed",
            model=model,
        )

    # ---------- 属性（懒加载）----------

    @property
    def llm(self) -> BaseChatModel:
        if self._llm is None:
            self._llm = self._create_chat_model()
        return self._llm

    @property
    def embeddings(self) -> Embeddings:
        if self._embeddings is None:
            self._embeddings = self._create_embedding_model()
        return self._embeddings

    def reload(self):
        """清空缓存实例，下次访问时根据最新 settings 重建"""
        self._llm = None
        self._embeddings = None
        logger.info("LLM 服务已重载，llm_provider=%s, embedding_provider=%s",
                    settings.llm_provider, settings.embedding_provider)

    # ========== 对话能力 ==========

    async def chat(
        self,
        user_message: str,
        graph_stats: str = "",
        rag_context: str = "",
        chat_history: Optional[list] = None,
    ) -> str:
        """通用对话"""
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT.format(
                    graph_stats=graph_stats,
                    rag_context=rag_context,
                )),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}"),
            ]
        )
        chain = prompt | self.llm | StrOutputParser()

        history = chat_history or []
        response = await asyncio.wait_for(
            chain.ainvoke({"input": user_message, "history": history}),
            timeout=settings.llm_timeout_seconds,
        )
        return response

    async def analyze_formula(self, formula: Formula) -> str:
        """配方分析"""
        items_text = "\n".join(
            f"  - {item.material.name} ({item.material.function.value}): "
            f"{item.weight_percent}%"
            for item in formula.items
        )
        process_text = "未提供工艺条件"
        if formula.process:
            parts = []
            if formula.process.temperature:
                parts.append(f"温度: {formula.process.temperature}°C")
            if formula.process.mixing_speed:
                parts.append(f"搅拌速度: {formula.process.mixing_speed} rpm")
            if formula.process.mixing_time:
                parts.append(f"搅拌时间: {formula.process.mixing_time} min")
            if formula.process.curing_temperature:
                parts.append(f"固化温度: {formula.process.curing_temperature}°C")
            if formula.process.curing_time:
                parts.append(f"固化时间: {formula.process.curing_time} h")
            process_text = "\n".join(f"  - {p}" for p in parts) if parts else "未提供"

        perf_text = "\n".join(
            f"  - {p.test_name}: {p.value} {p.unit}"
            + (f" (合格)" if p.is_qualified else f" (不合格)" if p.is_qualified is not None else "")
            for p in formula.performance
        ) or "无测试数据"

        prompt_text = FORMULA_ANALYSIS_PROMPT.format(
            formula_name=formula.name,
            category=formula.category.value,
            description=formula.description or "无描述",
            formula_items=items_text,
            process_conditions=process_text,
            performance_data=perf_text,
        )

        chain = self.llm | StrOutputParser()
        response = await asyncio.wait_for(
            chain.ainvoke(prompt_text),
            timeout=settings.llm_timeout_seconds,
        )
        return response

    async def recommend_formula(
        self,
        requirement: str,
        category: str,
        target_performance: dict,
        reference_results: list[FormulaSearchResult],
    ) -> str:
        """配方推荐"""
        target_text = "\n".join(
            f"  - {k}: {v}" for k, v in target_performance.items()
        ) or "未指定"

        ref_texts = []
        for i, r in enumerate(reference_results[:5], 1):
            f = r.formula
            items = ", ".join(
                f"{item.material.name}({item.weight_percent}%)"
                for item in f.items[:8]
            )
            ref_texts.append(
                f"案例{i}: {f.name} (相似度: {r.similarity_score:.2f})\n"
                f"    组分: {items}\n"
                f"    匹配原因: {r.match_reason}"
            )
        ref_text = "\n".join(ref_texts) or "无参考案例"

        prompt_text = FORMULA_RECOMMENDATION_PROMPT.format(
            requirement=requirement,
            category=category,
            target_performance=target_text,
            reference_formulas=ref_text,
        )

        chain = self.llm | StrOutputParser()
        response = await asyncio.wait_for(
            chain.ainvoke(prompt_text),
            timeout=settings.llm_timeout_seconds,
        )
        return response

    async def extract_recommendation_formula(
        self,
        requirement: str,
        category: str,
        target_performance: dict,
        recommendation: str,
        reference_results: list[FormulaSearchResult],
    ) -> Optional[dict]:
        """把 AI 推荐文本转成结构化配方 JSON，供一键入库。"""
        ref_texts = []
        for i, r in enumerate(reference_results[:3], 1):
            f = r.formula
            items = ", ".join(
                f"{item.material.name}({item.weight_percent}%)"
                for item in f.items[:8]
            )
            ref_texts.append(f"案例{i}: {f.name}\n    组分: {items}")
        ref_text = "\n".join(ref_texts) or "无"
        target_text = "\n".join(f"  - {k}: {v}" for k, v in target_performance.items()) or "未指定"
        prompt = (
            "你是化工配方结构化提取器。根据下面的需求、性能目标和 AI 推荐结果，"
            "输出一个可保存到配方库的配方 JSON。\n"
            "必须输出合法 JSON（不要 Markdown 代码块），结构：\n"
            '{"name":"配方名称","code":null,"category":"涂料或胶粘剂等已有类别",'
            '"description":"一句话说明","items":[{"material":{"name":"原料名",'
            '"function":"基础树脂或溶剂等已有功能"},"weight_percent":数值}],'
            '"process":{"temperature":null,"mixing_speed":null,"mixing_time":null},'
            '"performance":[]}\n'
            "要求：组分百分比总和在 95-105 之间；只使用 AI 推荐或参考案例中出现的材料；"
            "不要编造材料；不要输出其他文字。\n\n"
            f"需求：{requirement}\n"
            f"类别：{category}\n"
            f"目标性能：{target_text}\n"
            f"参考案例：\n{ref_text}\n\n"
            f"AI 推荐文本：\n{recommendation}"
        )
        try:
            response = await asyncio.wait_for(
                (self.llm | StrOutputParser()).ainvoke(prompt),
                timeout=settings.llm_timeout_seconds,
            )
            text = (response or "").strip()
            if text.startswith("```"):
                text = text.strip("`")
                if text.startswith("json"):
                    text = text[4:].strip()
            import json
            data = json.loads(text)
            if not isinstance(data, dict):
                return None
            return _normalize_recommended_formula(data)
        except Exception as e:
            logger.warning("推荐配方结构化提取失败: %s", e)
            return None

    async def suggest_substitute(
        self,
        material_name: str,
        material_function: str,
        current_usage: str,
        usage_stats: dict,
    ) -> str:
        """原材料替代建议"""
        stats_text = (
            f"使用该原料的配方数: {usage_stats.get('count', 0)}\n"
            f"平均用量: {usage_stats.get('avg_percent', 0)}%\n"
            f"涉及配方: {', '.join(f['formula_name'] for f in usage_stats.get('formulas', [])[:5])}"
        )

        prompt_text = MATERIAL_SUBSTITUTE_PROMPT.format(
            material_name=material_name,
            material_function=material_function,
            current_usage=current_usage,
            usage_stats=stats_text,
        )

        chain = self.llm | StrOutputParser()
        response = await asyncio.wait_for(
            chain.ainvoke(prompt_text),
            timeout=settings.llm_timeout_seconds,
        )
        return response

    # ========== 向量嵌入 ==========

    async def get_embedding(self, text: str) -> list[float]:
        """获取文本向量嵌入"""
        return await self.embeddings.aembed_query(text)

    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """批量获取文本向量嵌入"""
        return await self.embeddings.aembed_documents(texts)
