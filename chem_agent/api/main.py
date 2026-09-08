"""FastAPI 后端 API 服务"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from io import BytesIO
from typing import Optional

from fastapi import FastAPI, Depends, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from chem_agent.config import settings
from chem_agent.api.error_handler import (
    ChemAgentError, ErrorCode, register_error_handlers,
)
from chem_agent.knowledge_graph import KnowledgeGraphService
from chem_agent.llm import LLMService
from chem_agent.prediction import FormulaPredictor
from chem_agent.models import (
    Formula,
    FormulaItem,
    PerformanceTest,
    RawMaterial,
    FormulaSearchResult,
    PredictionRequest,
    PredictionResult,
)
from chem_agent.auth.database import init_db
from chem_agent.auth.dependencies import get_current_user, require_permission
from chem_agent.auth.models import UserOut
from chem_agent.admin.auth_router import router as auth_router
from chem_agent.admin.user_router import router as user_router
from chem_agent.admin.role_router import router as role_router
from chem_agent.admin.category_router import router as category_router
from chem_agent.admin.config_router import router as config_router
from chem_agent.admin.audit_router import router as audit_router
from chem_agent.api.formula_version_router import router as formula_version_router
from chem_agent.api.doe_router import router as doe_router
from chem_agent.api.cost_router import router as cost_router
from chem_agent.api.compliance_router import router as compliance_router
from chem_agent.api.experiment_router import router as experiment_router
from chem_agent.api.optimization_router import router as optimization_router
from chem_agent.api.scaleup_router import router as scaleup_router
from chem_agent.api.stability_router import router as stability_router
from chem_agent.api.sustainability_router import router as sustainability_router
from chem_agent.api.quality_router import router as quality_router
from chem_agent.api.process_router import router as process_router
from chem_agent.api.risk_router import router as risk_router
from chem_agent.api.wiki_router import router as wiki_router
from chem_agent.api.rd_router import router as rd_router

logger = logging.getLogger(__name__)


class _TTLCache:
    """Simple TTL cache for API responses."""
    def __init__(self):
        self._data = {}
    
    def get(self, key: str, ttl: int = 60):
        entry = self._data.get(key)
        if entry and (time.time() - entry["ts"]) < ttl:
            return entry["value"]
        return None
    
    def set(self, key: str, value):
        self._data[key] = {"value": value, "ts": time.time()}
    
    def clear(self):
        self._data.clear()

_cache = _TTLCache()


def _risk_warnings(formula) -> list[str]:
    """保存配方时附带安全风险提示（只提示，不阻断）。"""
    try:
        from chem_agent.risk.analyzer import RiskRequest, analyze_formula_risks
        result = analyze_formula_risks(RiskRequest(formula=formula))
        return [
            f"{item.risk_type}: {item.description}（缓解建议: {item.mitigation}）"
            for item in result.items
            if item.level.value in ("moderate", "high", "critical")
        ]
    except Exception as e:
        logger.debug("风险提示计算跳过: %s", e)
        return []


_SNAPSHOT_IGNORED_FIELDS = {"id", "created_at", "updated_at"}


def _clean_snapshot(value):
    """去掉运行时字段，用于判断配方内容是否真实变化。"""
    if isinstance(value, dict):
        return {
            k: _clean_snapshot(v)
            for k, v in value.items()
            if k not in _SNAPSHOT_IGNORED_FIELDS
        }
    if isinstance(value, list):
        return [_clean_snapshot(v) for v in value]
    return value


def _snapshot_semantic_equal(a, b) -> bool:
    """比较两个配方快照（容忍字符串/对象混合），忽略运行时字段。"""
    import json

    def _as_dict(value):
        if isinstance(value, str):
            return json.loads(value)
        return value

    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return _clean_snapshot(_as_dict(a)) == _clean_snapshot(_as_dict(b))


# 全局服务实例
kg_service = KnowledgeGraphService()
kg_local_mode = False  # True 表示 Neo4j 不可用，已切换到本地数据模式
llm_service = LLMService()
predictor = FormulaPredictor()
kb_service = None  # 知识库服务，在 lifespan 中初始化
react_agent = None  # ReAct 智能体，在 lifespan 中初始化
agent_memory = None  # Agent 记忆服务，在 lifespan 中初始化
wiki_service = None  # LLM Wiki 服务，在 lifespan 中初始化


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    logger.info("正在启动 ChemAgent API 服务...")

    # 初始化认证数据库
    try:
        init_db()
        logger.info("认证数据库初始化完成")
    except Exception as e:
        logger.error("认证数据库初始化失败: %s", e)

    # 从数据库恢复 LLM 配置
    _load_llm_config_from_db()

    global kg_service, kg_local_mode
    try:
        kg_service.connect()
        kg_service.init_schema()
        logger.info("Neo4j 知识图谱服务就绪")
    except Exception as e:
        logger.warning("Neo4j 连接失败，切换到本地数据模式: %s", e)
        from chem_agent.knowledge_graph.local_service import LocalKnowledgeService
        kg_service = LocalKnowledgeService()
        kg_local_mode = True

    try:
        predictor.load()
        logger.info("预测模型已加载")
    except FileNotFoundError:
        logger.info("未找到预训练模型，预测功能需先训练")
    except Exception as e:
        logger.warning("预测模型加载失败: %s", e)

    # 初始化知识库服务
    global kb_service
    try:
        from chem_agent.knowledge_base import KnowledgeBaseService
        kb_service = KnowledgeBaseService(llm_service=llm_service)
        logger.info("知识库服务已初始化")
    except Exception as e:
        logger.warning("知识库服务初始化失败（知识库功能不可用）: %s", e)

    global wiki_service
    try:
        from chem_agent.wiki import WikiService
        wiki_service = WikiService(llm_service=llm_service)
        logger.info("LLM Wiki 服务已初始化")
    except Exception as e:
        logger.warning("LLM Wiki 服务初始化失败: %s", e)

    # 初始化 ReAct 智能体
    global react_agent, agent_memory
    if settings.agent_enabled:
        try:
            from chem_agent.agent import ReActAgent, register_tools

            # 初始化 Agent 记忆服务
            if settings.agent_memory_enabled:
                try:
                    from chem_agent.agent.memory import AgentMemoryService
                    agent_memory = AgentMemoryService(
                        llm_service=llm_service,
                        persist_dir=settings.chroma_persist_dir,
                    )
                    logger.info("Agent 记忆服务已初始化")
                except Exception as e:
                    logger.warning("Agent 记忆服务初始化失败: %s", e)

            tool_registry = register_tools(kg_service, kb_service, llm_service, predictor)
            react_agent = ReActAgent(
                llm=llm_service.llm,
                tools=tool_registry,
                max_iterations=settings.agent_max_iterations,
                memory_service=agent_memory,
                enable_planning=settings.agent_planning_enabled,
                enable_reflection=settings.agent_reflection_enabled,
                max_reflections=settings.agent_max_reflections,
                llm_timeout=settings.llm_timeout_seconds,
            )
            logger.info("ReAct 智能体已初始化，注册 %d 个工具", len(tool_registry))
        except Exception as e:
            logger.warning("ReAct 智能体初始化失败: %s", e)

    yield

    # 关闭
    kg_service.close()
    logger.info("ChemAgent API 服务已关闭")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="化工研发智能体 API - 配方知识图谱 & AI 辅助开发",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册统一错误处理器
register_error_handlers(app)

# 注册认证路由（公开，无需 token）
app.include_router(auth_router)
# 注册管理后台路由
app.include_router(user_router)
app.include_router(role_router)
app.include_router(category_router)
app.include_router(config_router)
app.include_router(audit_router)
app.include_router(formula_version_router)

# 注册知识库路由
from chem_agent.api.kb_router import router as kb_router
app.include_router(kb_router)
app.include_router(doe_router)
app.include_router(cost_router)
app.include_router(compliance_router)
app.include_router(experiment_router)
app.include_router(optimization_router)
app.include_router(scaleup_router)
app.include_router(stability_router)
app.include_router(sustainability_router)
app.include_router(quality_router)
app.include_router(process_router)
app.include_router(risk_router)
app.include_router(wiki_router)
app.include_router(rd_router)


# ============ 请求/响应模型 ============


class ChatRequest(BaseModel):
    message: str
    history: Optional[list] = None
    use_agent: bool = False


class SaveFormulaFromTextRequest(BaseModel):
    requirement: str = ""
    text: str = Field(..., description="AI 回复的配方文本")
    category: str = "其他"
    target_performance: dict = {}


class ChatResponse(BaseModel):
    reply: str


class FormulaAnalysisResponse(BaseModel):
    analysis: str


class RecommendationRequest(BaseModel):
    requirement: str
    category: str
    target_performance: dict = {}


class RecommendationResponse(BaseModel):
    recommendation: str
    reference_formulas: list[FormulaSearchResult] = []
    suggested_formula: Optional[dict] = None


class SubstituteRequest(BaseModel):
    material_name: str
    material_function: str = "其他"
    current_usage: str = ""


class TrainRequest(BaseModel):
    target_properties: list[str]


class TrainResponse(BaseModel):
    results: dict


# ============ 健康检查 ============


@app.get("/health")
async def health_check():
    """健康检查"""
    status = {"status": "ok", "version": settings.app_version}
    try:
        stats = kg_service.get_graph_stats()
        status["knowledge_graph"] = {
            "connected": not kg_local_mode,
            "local_mode": kg_local_mode,
            **stats,
        }
    except Exception:
        status["knowledge_graph"] = {"connected": False}
    status["llm"] = {
        "provider": settings.llm_provider or "(未配置)",
        "embedding_provider": settings.embedding_provider or "(未配置)",
    }
    return status


@app.get("/api/health")
async def api_health_check():
    """健康检查别名（供 `/api` 前缀的前端调用）。"""
    return await health_check()


# ============ LLM 配置管理 API ============

_VALID_PROVIDERS = {
    "ollama", "lm_studio", "openai", "azure_openai",
    "deepseek", "zhipu", "qwen", "moonshot", "yi",
    "gemini", "anthropic", "custom_openai",
}
# API Key 必填的 Provider
_API_KEY_REQUIRED = {
    "openai", "azure_openai", "deepseek", "zhipu", "qwen",
    "moonshot", "yi", "gemini", "anthropic",
}


class LLMConfigPayload(BaseModel):
    provider: str
    base_url: str = ""
    model: str = ""
    api_key: str = ""
    azure_deployment: str = ""
    azure_api_version: str = ""
    max_tokens: int = 4096
    temperature: float = 0.7
    reasoning_effort: str = "medium"


class LLMTestRequest(BaseModel):
    provider: str
    base_url: str
    model: str
    api_key: str = ""
    test_type: str = "chat"  # "chat" 或 "embedding"


class EmbeddingConfigPayload(BaseModel):
    provider: str               # "same_as_llm" 或具体 provider
    base_url: str = ""
    model: str = ""
    api_key: str = ""


def _mask_api_key(key: str) -> str:
    """脱敏 API 密钥"""
    if not key or len(key) <= 8:
        return "***" if key else ""
    return key[:4] + "***" + key[-4:]


# --- DB 配置键映射 ---
_LLM_DB_KEYS = {
    "llm.provider": "llm_provider",
    "llm.base_url": "llm_base_url",
    "llm.model": "llm_model",
    "llm.api_key": "llm_api_key",
    "llm.azure_deployment": "azure_deployment_name",
    "llm.azure_api_version": "azure_api_version",
    "llm.max_tokens": "llm_max_tokens",
    "llm.temperature": "llm_temperature",
    "llm.reasoning_effort": "llm_reasoning_effort",
}
_EMB_DB_KEYS = {
    "emb.provider": "embedding_provider",
    "emb.base_url": "embedding_base_url",
    "emb.model": "embedding_model",
    "emb.api_key": "embedding_api_key",
}
# 旧键 → 新键的迁移映射 (向后兼容)
_OLD_DB_KEY_MIGRATION = {
    "llm.chat_provider": "llm.provider",
    "llm.ollama_base_url": "llm.base_url",
    "llm.ollama_model": "llm.model",
    "llm.embedding_provider": "emb.provider",
    "llm.ollama_embedding_model": "emb.model",
    "llm.openai_api_base_url": "llm.base_url",
    "llm.openai_api_key": "llm.api_key",
    "llm.openai_chat_model": "llm.model",
    "llm.openai_embedding_model": "emb.model",
}


def _load_llm_config_from_db():
    """从数据库加载 LLM/Embedding 配置覆盖 settings（启动时调用）"""
    try:
        from chem_agent.auth import database as db
        all_configs = db.get_all_configs()
        config_map = {c["key"]: c["value"] for c in all_configs}

        # 先尝试新键
        loaded = 0
        all_db_keys = {**_LLM_DB_KEYS, **_EMB_DB_KEYS}
        # 需要类型转换的字段
        _NUMERIC_ATTRS = {"llm_max_tokens": int, "llm_temperature": float}
        for db_key, settings_attr in all_db_keys.items():
            if db_key in config_map and config_map[db_key]:
                val = config_map[db_key]
                converter = _NUMERIC_ATTRS.get(settings_attr)
                if converter:
                    try:
                        val = converter(val)
                    except (ValueError, TypeError) as e:
                        logger.warning(
                            "配置 %s 类型转换失败（原始值=%r），跳过此项: %s",
                            settings_attr, val, e
                        )
                        continue
                setattr(settings, settings_attr, val)
                loaded += 1

        # 若新键不存在，尝试旧键迁移
        if loaded == 0:
            for old_key, new_key in _OLD_DB_KEY_MIGRATION.items():
                if old_key in config_map and config_map[old_key]:
                    new_settings_attr = all_db_keys.get(new_key)
                    if new_settings_attr and not getattr(settings, new_settings_attr, ""):
                        setattr(settings, new_settings_attr, config_map[old_key])
                        loaded += 1
            if loaded:
                logger.info("从旧格式数据库迁移了 %d 项 LLM 配置", loaded)

        if loaded:
            logger.info("从数据库加载了 %d 项 LLM/Embedding 配置", loaded)
    except Exception as e:
        logger.warning("从数据库加载 LLM 配置失败（使用环境变量默认值）: %s", e)


def _save_config_to_db(db_keys: dict, user_id: int, desc_prefix: str):
    """通用: 将 settings 中指定字段持久化到数据库"""
    from chem_agent.auth import database as db
    for db_key, settings_attr in db_keys.items():
        val = getattr(settings, settings_attr, "")
        db.set_config(
            key=db_key,
            value=str(val) if val else "",
            description=f"{desc_prefix}: {settings_attr}",
            user_id=user_id,
        )


@app.get("/api/admin/llm/config")
async def get_llm_config(
    _user: UserOut = Depends(require_permission("config:read")),
):
    """获取当前 LLM 配置（API Key 脱敏）"""
    return {
        "provider": settings.llm_provider,
        "base_url": settings.llm_base_url,
        "model": settings.llm_model,
        "api_key": _mask_api_key(settings.llm_api_key),
        "azure_deployment": settings.azure_deployment_name,
        "azure_api_version": settings.azure_api_version,
        "max_tokens": settings.llm_max_tokens,
        "temperature": settings.llm_temperature,
        "reasoning_effort": settings.llm_reasoning_effort,
    }


@app.post("/api/admin/llm/config")
async def save_llm_config(
    payload: LLMConfigPayload,
    current_user: UserOut = Depends(require_permission("config:write")),
):
    """保存 LLM 配置（持久化到数据库 + 运行时生效）"""
    if payload.provider not in _VALID_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"不支持的 provider: {payload.provider}")

    if payload.provider in _API_KEY_REQUIRED and not payload.api_key:
        # 若是脱敏值 (***) 或空，检查是否已有旧 key
        if not settings.llm_api_key:
            raise HTTPException(status_code=400, detail="该提供商需要填写 API Key")

    if payload.provider != "ollama" and not payload.model:
        raise HTTPException(status_code=400, detail="请填写模型名称")

    # 写入 settings
    settings.llm_provider = payload.provider
    settings.llm_base_url = payload.base_url
    settings.llm_model = payload.model
    if payload.api_key and "***" not in payload.api_key:
        settings.llm_api_key = payload.api_key
    if payload.provider == "azure_openai":
        settings.azure_deployment_name = payload.azure_deployment
        settings.azure_api_version = payload.azure_api_version or "2024-02-01"

    settings.llm_max_tokens = payload.max_tokens
    settings.llm_temperature = payload.temperature
    settings.llm_reasoning_effort = (payload.reasoning_effort or "medium").strip() or "medium"

    # 持久化到数据库
    _save_config_to_db(_LLM_DB_KEYS, current_user.id, "LLM 配置")

    # 重载 LLM 服务实例
    llm_service.reload()

    # 同步更新 ReAct Agent 的 LLM 引用
    if react_agent is not None:
        try:
            react_agent.reload_llm(llm_service.llm)
            logger.info("ReAct Agent LLM 已同步更新")
        except Exception as e:
            logger.warning("更新 Agent LLM 失败: %s", e)

    # 审计日志
    from chem_agent.auth import database as auth_db
    auth_db.log_audit(
        action="update_llm_config",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="llm_config",
        details={"provider": payload.provider, "model": payload.model},
    )

    return {"message": "LLM 配置已保存并生效"}


@app.get("/api/admin/embedding/config")
async def get_embedding_config(
    _user: UserOut = Depends(require_permission("config:read")),
):
    """获取当前 Embedding 配置（API Key 脱敏）"""
    return {
        "provider": settings.embedding_provider,
        "base_url": settings.embedding_base_url,
        "model": settings.embedding_model,
        "api_key": _mask_api_key(settings.embedding_api_key),
    }


@app.post("/api/admin/embedding/config")
async def save_embedding_config(
    payload: EmbeddingConfigPayload,
    current_user: UserOut = Depends(require_permission("config:write")),
):
    """保存 Embedding 配置"""
    if payload.provider != "same_as_llm" and payload.provider not in _VALID_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"不支持的 provider: {payload.provider}")

    if not payload.model:
        raise HTTPException(status_code=400, detail="请填写 Embedding 模型名称")

    settings.embedding_provider = payload.provider
    settings.embedding_base_url = payload.base_url
    settings.embedding_model = payload.model
    if payload.api_key and "***" not in payload.api_key:
        settings.embedding_api_key = payload.api_key

    _save_config_to_db(_EMB_DB_KEYS, current_user.id, "Embedding 配置")

    llm_service.reload()

    from chem_agent.auth import database as auth_db
    auth_db.log_audit(
        action="update_embedding_config",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="embedding_config",
        details={"provider": payload.provider, "model": payload.model},
    )

    return {"message": "Embedding 配置已保存并生效"}


@app.post("/api/admin/llm/test")
async def test_llm_connection(
    req: LLMTestRequest,
    _user: UserOut = Depends(require_permission("config:write")),
):
    """测试 LLM/Embedding 连接（临时创建实例测试）"""
    import time as _time

    if req.provider not in _VALID_PROVIDERS:
        return {"success": False, "latency_ms": 0, "error": f"不支持的 provider: {req.provider}"}

    try:
        start = _time.time()

        if req.test_type == "embedding":
            if req.provider == "ollama":
                from langchain_ollama import OllamaEmbeddings as _OE
                emb = _OE(base_url=req.base_url, model=req.model)
            else:
                from langchain_openai import OpenAIEmbeddings as _OAIE
                emb = _OAIE(
                    base_url=req.base_url,
                    api_key=req.api_key or "not-needed",
                    model=req.model,
                )
            await asyncio.wait_for(emb.aembed_query("test"), timeout=15)
        else:
            if req.provider == "ollama":
                from langchain_ollama import ChatOllama as _CO
                chat = _CO(base_url=req.base_url, model=req.model, temperature=0)
            else:
                from langchain_openai import ChatOpenAI as _COAI
                chat = _COAI(
                    base_url=req.base_url,
                    api_key=req.api_key or "not-needed",
                    model=req.model,
                    temperature=0,
                )
            from langchain_core.messages import HumanMessage as _HM
            await asyncio.wait_for(chat.ainvoke([_HM(content="Hi")]), timeout=15)

        latency = int((_time.time() - start) * 1000)
        return {"success": True, "latency_ms": latency, "error": None}

    except asyncio.TimeoutError:
        return {"success": False, "latency_ms": 0, "error": "连接超时（15秒）"}
    except Exception as e:
        error_msg = str(e)
        if len(error_msg) > 200:
            error_msg = error_msg[:200] + "..."
        return {"success": False, "latency_ms": 0, "error": error_msg}


# ============ 对话 API ============


@app.post("/api/chat")
async def chat(request: ChatRequest, _user: UserOut = Depends(require_permission("chat:access"))):
    """智能对话（支持 Agent 模式）"""
    try:
        # Agent 模式：使用 ReAct 工具调用智能体
        if request.use_agent and react_agent is not None:
            result = await react_agent.run(
                query=request.message,
                user_permissions=_user.permissions,
                chat_history=request.history,
            )
            return {
                "reply": result.reply,
                "steps": [s.model_dump() for s in result.steps],
                "tools_used": result.tools_used,
                "iterations": result.iterations,
            }

        # 普通模式：RAG + LLM 直接对话
        graph_stats = ""
        try:
            stats = kg_service.get_graph_stats()
            graph_stats = f"配方 {stats['formulas']} 个, 原材料 {stats['materials']} 种"
        except Exception:
            pass

        rag_context = ""
        # LLM Wiki 优先：命中结构化知识页时整页引用
        if wiki_service is not None:
            try:
                wiki_results = await wiki_service.search(request.message, top_k=settings.rag_top_k)
                if wiki_results:
                    lines = ["\n=== 知识Wiki ==="]
                    for i, r in enumerate(wiki_results, 1):
                        lines.append(f"\n[Wiki{i}: {r.title}]")
                        lines.append(r.content[:1500])
                    rag_context = "\n".join(lines)
            except Exception as e:
                logger.debug("Wiki 检索跳过: %s", e)

        # 回退：无 Wiki 命中时检索原文分块
        if kb_service is not None and not rag_context:
            try:
                rag_results = await kb_service.search(request.message, top_k=settings.rag_top_k)
                if rag_results:
                    lines = ["\n=== 参考资料 ==="]
                    for i, r in enumerate(rag_results, 1):
                        lines.append(f"\n[文档{i}: {r.filename}]")
                        snippet = r.content[:500] + "..." if len(r.content) > 500 else r.content
                        lines.append(snippet)
                    rag_context = "\n".join(lines)
            except Exception as e:
                logger.debug("RAG 检索跳过: %s", e)

        reply = await llm_service.chat(
            user_message=request.message,
            graph_stats=graph_stats,
            rag_context=rag_context,
            chat_history=request.history,
        )
        return ChatResponse(reply=reply)
    except Exception as e:
        logger.error("对话失败: %s", e)
        raise ChemAgentError(
            error_code=ErrorCode.LLM_UNAVAILABLE,
            internal_detail=str(e),
        )


# ============ 配方 API ============


@app.post("/api/formulas", response_model=dict)
async def create_formula(
    formula: Formula,
    domains: Optional[str] = Query(None, description="可选：合规检查领域，逗号分隔（如 construction,toys）"),
    current_user: UserOut = Depends(require_permission("formula:write")),
):
    """创建/更新配方；自动保存版本快照并返回安全/合规提示（不阻断保存）。"""
    try:
        existing = kg_service.get_formula(formula.code) if formula.code else None
        formula_id = kg_service.upsert_formula(formula)
        _cache.clear()
        warnings = _risk_warnings(formula)
        compliance_warnings: list[str] = []
        if domains:
            from chem_agent.compliance.rules import (
                ComplianceRequest,
                RegulationDomain,
                check_compliance,
            )
            try:
                domain_list = [RegulationDomain(d.strip()) for d in domains.split(",") if d.strip()]
            except ValueError as exc:
                raise ChemAgentError(
                    error_code=ErrorCode.INPUT_INVALID,
                    internal_detail=str(exc),
                    status_code=400,
                )
            comp = check_compliance(ComplianceRequest(formula=formula, domains=domain_list))
            compliance_warnings = [
                f"{v.rule_name}: {v.material_name} 实际 {v.actual_value}，限值 {v.limit_value}"
                for v in comp.violations
                if v.severity in ("error", "critical")
            ]

        version_info = {"version_saved": False}
        if formula.code:
            try:
                from chem_agent.auth import database as auth_db
                current_snapshot = formula.model_dump(mode="json")
                latest = auth_db.get_latest_formula_version(formula.code)
                if existing is not None and _snapshot_semantic_equal(
                    (latest or {}).get("snapshot_data"), current_snapshot
                ):
                    version_info = {
                        "version_saved": False,
                        "version_note": "配方内容未变化，未生成新版本",
                    }
                else:
                    version_number = auth_db.save_formula_version(
                        formula_code=formula.code,
                        snapshot_data=current_snapshot,
                        change_summary="创建配方" if existing is None else "更新配方",
                        changed_by=current_user.username,
                    )
                    version_info = {"version_saved": True, "version_number": version_number}
            except Exception as e:
                logger.warning("配方版本快照保存失败: %s", e)

        try:
            from chem_agent.auth import database as auth_db
            auth_db.log_audit(
                action="create_formula" if existing is None else "update_formula",
                user_id=current_user.id,
                username=current_user.username,
                resource_type="formula",
                resource_id=formula.code or formula.name,
                details={"name": formula.name, "version": formula.version},
            )
        except Exception as e:
            logger.warning("配方审计日志写入失败: %s", e)

        return {
            "id": formula_id,
            "message": f"配方 '{formula.name}' 已保存",
            **version_info,
            "warnings": warnings,
            "compliance_warnings": compliance_warnings,
        }
    except ChemAgentError:
        raise
    except Exception as e:
        logger.error("保存配方失败: %s", e)
        raise ChemAgentError(error_code=ErrorCode.DB_QUERY_FAILED, internal_detail=str(e))


@app.post("/api/formulas/save-from-text", response_model=dict)
async def save_formula_from_text(
    request: SaveFormulaFromTextRequest,
    current_user: UserOut = Depends(require_permission("formula:write")),
):
    """把 AI 回答/推荐文本解析成配方并一键保存为草稿。"""
    try:
        raw = await llm_service.extract_recommendation_formula(
            requirement=request.requirement or request.text,
            category=request.category,
            target_performance=request.target_performance,
            recommendation=request.text,
            reference_results=[],
        )
        if not raw:
            raise ChemAgentError(
                error_code=ErrorCode.INPUT_INVALID,
                user_message="无法从回答中识别出可保存的配方，请描述明确的组分/比例或改用『配方推荐』页面",
                status_code=400,
            )
        raw.setdefault(
            "code",
            "AI-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
        )
        formula = Formula(**raw)
        existing = kg_service.get_formula(formula.code) if formula.code else None
        formula_id = kg_service.upsert_formula(formula)
        _cache.clear()

        warnings = _risk_warnings(formula)
        if formula.code:
            try:
                from chem_agent.auth import database as auth_db
                latest = auth_db.get_latest_formula_version(formula.code)
                if existing is None or not _snapshot_semantic_equal(
                    (latest or {}).get("snapshot_data"), formula.model_dump(mode="json")
                ):
                    auth_db.save_formula_version(
                        formula_code=formula.code,
                        snapshot_data=formula.model_dump(mode="json"),
                        change_summary="AI 推荐配方保存",
                        changed_by=current_user.username,
                    )
            except Exception as e:
                logger.warning("AI 配方版本快照保存失败: %s", e)

        return {
            "success": True,
            "id": formula_id,
            "code": formula.code,
            "name": formula.name,
            "warnings": warnings,
        }
    except ChemAgentError:
        raise
    except Exception as e:
        logger.error("AI 配方保存失败: %s", e)
        raise ChemAgentError(error_code=ErrorCode.INTERNAL, internal_detail=str(e))


@app.get("/api/formulas", response_model=list[FormulaSearchResult])
async def search_formulas(
    keyword: Optional[str] = Query(None, description="关键词"),
    category: Optional[str] = Query(None, description="产品类别"),
    materials: Optional[str] = Query(None, description="原料名称，逗号分隔"),
    limit: int = Query(20, ge=1, le=100),
    _user: UserOut = Depends(require_permission("formula:read")),
):
    """检索配方"""
    material_list = [m.strip() for m in materials.split(",")] if materials else None
    results = kg_service.search_formulas(
        keyword=keyword,
        category=category,
        materials=material_list,
        limit=limit,
    )
    return results


# ============ 配方导入导出 ============
# 注意: export/import/template 路由必须在 {code} 路由之前定义，
# 否则 FastAPI 会将 "export" 等路径匹配为 {code} 参数。


@app.get("/api/formulas/export")
async def export_formulas(
    format: str = Query("excel", description="导出格式: excel / json"),
    code: Optional[str] = Query(None, description="单条配方编号"),
    category: Optional[str] = Query(None, description="产品类别"),
    keyword: Optional[str] = Query(None, description="关键词"),
    _user: UserOut = Depends(require_permission("formula:read")),
):
    """导出配方数据（Excel / JSON）"""
    from chem_agent.utils.formula_io import formulas_to_excel, formulas_to_json

    try:
        # 获取配方数据
        if code:
            f = kg_service.get_formula(code)
            if not f:
                raise HTTPException(status_code=404, detail=f"配方 '{code}' 不存在")
            formulas = [f]
        else:
            results = kg_service.search_formulas(
                keyword=keyword, category=category, limit=9999,
            )
            formulas = [r.formula for r in results]

        if not formulas:
            raise HTTPException(status_code=404, detail="没有找到配方数据")

        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        if format == "json":
            content = formulas_to_json(formulas)
            return StreamingResponse(
                BytesIO(content.encode("utf-8")),
                media_type="application/json",
                headers={"Content-Disposition": f'attachment; filename="formulas_{ts}.json"'},
            )
        else:
            buf = formulas_to_excel(formulas)
            return StreamingResponse(
                buf,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f'attachment; filename="formulas_{ts}.xlsx"'},
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("导出配方失败: %s", e)
        raise ChemAgentError(error_code=ErrorCode.DB_QUERY_FAILED, internal_detail=str(e))


@app.get("/api/formulas/export/template")
async def export_template(
    _user: UserOut = Depends(require_permission("formula:read")),
):
    """下载空白 Excel 导入模板"""
    from chem_agent.utils.formula_io import formulas_to_excel

    sample = Formula(
        name="示例配方", code="SAMPLE-001", category="涂料",
        items=[FormulaItem(material=RawMaterial(name="示例原料", function="基础树脂"), weight_percent=100.0)],
        performance=[PerformanceTest(test_name="硬度", value=3.0, unit="H")],
    )
    buf = formulas_to_excel([sample])
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="formula_template.xlsx"'},
    )


@app.post("/api/formulas/import")
async def import_formulas(
    file: UploadFile = File(...),
    current_user: UserOut = Depends(require_permission("formula:write")),
):
    """批量导入配方（Excel / JSON），重复编号跳过"""
    from chem_agent.utils.formula_io import excel_to_formulas, json_to_formulas, validate_formula_data

    try:
        content = await file.read()
        filename = file.filename or ""

        if filename.endswith(".json"):
            formula_dicts = json_to_formulas(content.decode("utf-8"))
        elif filename.endswith(".xlsx"):
            formula_dicts = excel_to_formulas(content)
        else:
            raise HTTPException(status_code=400, detail="不支持的文件格式，请上传 .xlsx 或 .json")

        total = len(formula_dicts)
        success, skipped, failed = 0, 0, 0
        details = []

        for fd in formula_dicts:
            code = fd.get("code", "").strip()
            valid, err = validate_formula_data(fd)
            if not valid:
                failed += 1
                details.append({"code": code or "?", "status": "failed", "message": err})
                continue

            # 检查是否已存在
            existing = kg_service.get_formula(code)
            if existing:
                skipped += 1
                details.append({"code": code, "status": "skipped", "message": "配方编码已存在"})
                continue

            try:
                formula = Formula(**fd)
                kg_service.upsert_formula(formula)
                success += 1
                details.append({"code": code, "status": "success", "message": "导入成功"})
            except Exception as e:
                failed += 1
                details.append({"code": code, "status": "failed", "message": str(e)})

        # 审计日志
        from chem_agent.auth import database as auth_db
        auth_db.log_audit(
            action="import_formulas",
            user_id=current_user.id,
            username=current_user.username,
            resource_type="formula",
            details={"total": total, "success": success, "skipped": skipped, "failed": failed},
        )

        return {
            "success": True,
            "summary": {"total": total, "success": success, "skipped": skipped, "failed": failed},
            "details": details,
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise ChemAgentError(error_code=ErrorCode.INPUT_INVALID, internal_detail=str(e), status_code=400)
    except Exception as e:
        logger.error("导入配方失败: %s", e)
        raise ChemAgentError(error_code=ErrorCode.DB_QUERY_FAILED, internal_detail=str(e))


# ============ 配方详情（{code} 路由放在固定路径之后） ============


@app.get("/api/formulas/{code}")
async def get_formula(code: str, _user: UserOut = Depends(require_permission("formula:read"))):
    """获取配方详情"""
    formula = kg_service.get_formula(code)
    if not formula:
        raise HTTPException(status_code=404, detail=f"配方 '{code}' 不存在")
    return formula


@app.patch("/api/formulas/{code}/status")
async def update_formula_status(
    code: str,
    status: str = Query(..., description="新状态: draft/review/approved/archived"),
    _user: UserOut = Depends(require_permission("formula:write")),
):
    """更新配方状态"""
    valid_statuses = ["draft", "review", "approved", "archived"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"无效状态，可选: {', '.join(valid_statuses)}")
    try:
        kg_service.update_formula_status(code, status)
        return {"code": code, "status": status, "message": "状态已更新"}
    except Exception as e:
        raise ChemAgentError(error_code=ErrorCode.DB_QUERY_FAILED, internal_detail=str(e))


@app.get("/api/formulas/{code}/similar", response_model=list[FormulaSearchResult])
async def find_similar(code: str, top_k: int = Query(5, ge=1, le=20), _user: UserOut = Depends(require_permission("formula:read"))):
    """查找相似配方"""
    return kg_service.find_similar_formulas(code, top_k=top_k)


@app.post("/api/formulas/analyze", response_model=FormulaAnalysisResponse)
async def analyze_formula(formula: Formula, _user: UserOut = Depends(require_permission("formula:analyze"))):
    """AI 分析配方"""
    try:
        analysis = await llm_service.analyze_formula(formula)
        return FormulaAnalysisResponse(analysis=analysis)
    except Exception as e:
        logger.error("配方分析失败: %s", e)
        raise ChemAgentError(error_code=ErrorCode.LLM_UNAVAILABLE, internal_detail=str(e))


@app.post("/api/formulas/recommend", response_model=RecommendationResponse)
async def recommend_formula(request: RecommendationRequest, _user: UserOut = Depends(require_permission("formula:recommend"))):
    """AI 配方推荐"""
    try:
        # 先搜索相关历史配方
        references = kg_service.search_formulas(
            keyword=request.requirement, category=request.category, limit=5
        )
        recommendation = await llm_service.recommend_formula(
            requirement=request.requirement,
            category=request.category,
            target_performance=request.target_performance,
            reference_results=references,
        )
        suggested_formula = None
        try:
            raw = await llm_service.extract_recommendation_formula(
                requirement=request.requirement,
                category=request.category,
                target_performance=request.target_performance,
                recommendation=recommendation,
                reference_results=references,
            )
            if raw:
                validated = Formula(**raw)
                suggested_formula = validated.model_dump(mode="json")
        except Exception as e:
            logger.warning("推荐配方结构校验失败: %s", e)
        return RecommendationResponse(
            recommendation=recommendation,
            reference_formulas=references,
            suggested_formula=suggested_formula,
        )
    except Exception as e:
        logger.error("配方推荐失败: %s", e)
        raise ChemAgentError(error_code=ErrorCode.LLM_UNAVAILABLE, internal_detail=str(e))


@app.post("/api/formulas/{code}/report")
async def generate_report(
    code: str,
    include_analysis: bool = Query(True),
    _user: UserOut = Depends(require_permission("formula:analyze")),
):
    """生成配方研发报告（Markdown 格式）。"""
    formula = kg_service.get_formula(code)
    if not formula:
        raise HTTPException(status_code=404, detail=f"配方 '{code}' 不存在")

    import asyncio

    # 构建报告内容
    lines = [
        f"# 配方研发报告: {formula.name}",
        f"\n**配方编号:** {formula.code}",
        f"**产品类别:** {formula.category.value if hasattr(formula.category, 'value') else formula.category}",
        f"**描述:** {formula.description or '无'}",
        f"**创建时间:** {formula.created_at}",
        "",
        "## 配方组分",
        "",
        "| 原材料 | 功能 | 含量(%) |",
        "| --- | --- | --- |",
    ]
    for item in formula.items:
        func_val = item.material.function.value if hasattr(item.material.function, 'value') else str(item.material.function)
        lines.append(f"| {item.material.name} | {func_val} | {item.weight_percent:.1f} |")

    if formula.performance:
        lines.extend(["", "## 性能测试", "", "| 测试项 | 值 | 单位 |", "| --- | --- | --- |"])
        for p in formula.performance:
            lines.append(f"| {p.test_name} | {p.value:.2f} | {p.unit} |")

    if formula.process:
        lines.extend(["", "## 工艺条件", ""])
        proc = formula.process
        if proc.temperature:
            lines.append(f"- 反应温度: {proc.temperature}°C")
        if proc.mixing_speed:
            lines.append(f"- 搅拌速度: {proc.mixing_speed} rpm")
        if proc.mixing_time:
            lines.append(f"- 搅拌时间: {proc.mixing_time} min")
        if proc.curing_temperature:
            lines.append(f"- 固化温度: {proc.curing_temperature}°C")
        if proc.curing_time:
            lines.append(f"- 固化时间: {proc.curing_time} h")

    # AI 分析
    if include_analysis:
        try:
            analysis = await asyncio.wait_for(
                llm_service.analyze_formula(formula),
                timeout=settings.llm_timeout_seconds,
            )
            lines.extend(["", "## AI 分析", "", analysis])
        except Exception as e:
            logger.warning("报告中 AI 分析失败: %s", e)
            lines.extend(["", "## AI 分析", "", "AI 分析暂不可用"])

    report_md = "\n".join(lines)
    return {"code": code, "report": report_md}


# ============ 原材料 API ============


@app.post("/api/materials", response_model=dict)
async def create_material(material: RawMaterial, _user: UserOut = Depends(require_permission("material:write"))):
    """创建/更新原材料"""
    try:
        mat_id = kg_service.upsert_material(material)
        _cache.clear()
        return {"id": mat_id, "message": f"原材料 '{material.name}' 已保存"}
    except Exception as e:
        raise ChemAgentError(error_code=ErrorCode.DB_QUERY_FAILED, internal_detail=str(e))


@app.get("/api/materials", response_model=list[RawMaterial])
async def search_materials(
    keyword: str = Query("", description="搜索关键词"),
    function: Optional[str] = Query(None, description="功能分类"),
    limit: int = Query(20, ge=1, le=100),
    _user: UserOut = Depends(require_permission("material:read")),
):
    """搜索原材料（keyword 为空时返回全部）"""
    return kg_service.search_materials(keyword, function_filter=function, limit=limit)


@app.get("/api/materials/categories")
async def material_function_stats(
    _user: UserOut = Depends(require_permission("material:read")),
):
    """原材料功能分类统计（知识图谱主数据源）"""
    from collections import Counter

    materials = kg_service.search_materials("", limit=1000)
    counts = Counter(
        m.function.value if hasattr(m.function, "value") else str(m.function)
        for m in materials
    )
    return {
        "categories": [
            {"name": name, "count": count}
            for name, count in counts.most_common()
        ]
    }


@app.get("/api/materials/{name}/detail")
async def material_detail(name: str, _user: UserOut = Depends(require_permission("material:read"))):
    """原材料详情（理化性质 + 关联配方）"""
    detail = kg_service.get_material_detail(name)
    if not detail:
        raise HTTPException(status_code=404, detail=f"原材料 '{name}' 不存在")
    return detail


@app.get("/api/materials/{name}/stats")
async def material_stats(name: str, _user: UserOut = Depends(require_permission("material:read"))):
    """原材料使用统计"""
    return kg_service.get_material_usage_stats(name)


@app.post("/api/materials/substitute")
async def suggest_substitute(request: SubstituteRequest, _user: UserOut = Depends(require_permission("material:substitute"))):
    """AI 原材料替代建议"""
    try:
        stats = kg_service.get_material_usage_stats(request.material_name)
        suggestion = await llm_service.suggest_substitute(
            material_name=request.material_name,
            material_function=request.material_function,
            current_usage=request.current_usage,
            usage_stats=stats,
        )
        return {"suggestion": suggestion, "usage_stats": stats}
    except Exception as e:
        raise ChemAgentError(error_code=ErrorCode.LLM_UNAVAILABLE, internal_detail=str(e))


# ============ 预测 API ============


@app.post("/api/predict", response_model=list[PredictionResult])
async def predict_performance(request: PredictionRequest, _user: UserOut = Depends(require_permission("prediction:read"))):
    """预测配方性能"""
    try:
        results = predictor.predict(request)
        return results
    except RuntimeError as e:
        raise ChemAgentError(error_code=ErrorCode.INPUT_INVALID, internal_detail=str(e), status_code=400)
    except Exception as e:
        raise ChemAgentError(error_code=ErrorCode.INTERNAL, internal_detail=str(e))


@app.post("/api/predict/train", response_model=TrainResponse)
async def train_predictor(request: TrainRequest, _user: UserOut = Depends(require_permission("prediction:train"))):
    """训练预测模型（使用知识图谱中的数据）"""
    try:
        # 从知识图谱获取所有配方数据
        all_formulas = kg_service.search_formulas(limit=1000)
        training_data = []
        for result in all_formulas:
            f = result.formula
            items = [
                {
                    "material_name": item.material.name,
                    "material_function": item.material.function.value
                    if hasattr(item.material.function, "value")
                    else str(item.material.function),
                    "weight_percent": item.weight_percent,
                }
                for item in f.items
            ]
            perf = {p.test_name: p.value for p in f.performance}
            if items and perf:
                training_data.append(
                    {
                        "category": f.category.value
                        if hasattr(f.category, "value")
                        else str(f.category),
                        "items": items,
                        "performance": perf,
                    }
                )

        if not training_data:
            training_data = []

        # 合并实验记录导出的训练数据（DOE→实验→模型 闭环）
        try:
            from chem_agent.experiments.manager import get_experiment_manager
            experiment_export = get_experiment_manager().export_training_data()
            if experiment_export.training_data:
                training_data.extend(experiment_export.training_data)
        except Exception as e:
            logger.warning("实验训练数据合并跳过: %s", e)

        if not training_data:
            raise HTTPException(status_code=400, detail="知识图谱和实验记录中都没有足够的训练数据")

        results = predictor.train(training_data, request.target_properties)
        predictor.save()
        return TrainResponse(results=results)
    except HTTPException:
        raise
    except Exception as e:
        raise ChemAgentError(error_code=ErrorCode.INTERNAL, internal_detail=str(e))


# ============ 知识图谱统计 ============


@app.get("/api/graph/stats")
async def graph_stats(_user: UserOut = Depends(get_current_user)):
    """知识图谱统计信息"""
    try:
        cached = _cache.get("graph_stats", settings.cache_ttl_seconds)
        if cached is not None:
            return cached
        result = kg_service.get_graph_stats()
        _cache.set("graph_stats", result)
        return result
    except Exception as e:
        raise ChemAgentError(error_code=ErrorCode.DB_QUERY_FAILED, internal_detail=str(e))


@app.get("/api/graph/category-distribution")
async def category_distribution(_user: UserOut = Depends(get_current_user)):
    """配方类别分布统计"""
    try:
        return kg_service.get_category_distribution()
    except Exception as e:
        raise ChemAgentError(error_code=ErrorCode.DB_QUERY_FAILED, internal_detail=str(e))


@app.get("/api/graph/top-materials")
async def top_materials(limit: int = Query(10, ge=1, le=50), _user: UserOut = Depends(get_current_user)):
    """原材料使用频次 TOP N"""
    try:
        return kg_service.get_top_materials(limit=limit)
    except Exception as e:
        raise ChemAgentError(error_code=ErrorCode.DB_QUERY_FAILED, internal_detail=str(e))


@app.post("/api/formulas/compare")
async def compare_formulas(
    request: dict,
    _user: UserOut = Depends(require_permission("formula:read")),
):
    """配方对比：传入 {"codes": ["F001", "F002", ...]}，返回多个完整配方"""
    codes = request.get("codes", [])
    if len(codes) < 2:
        raise HTTPException(status_code=400, detail="至少选择 2 个配方进行对比")
    formulas = []
    for code in codes[:10]:  # 限制最多 10 个
        f = kg_service.get_formula(code)
        if f:
            formulas.append(f)
    return {"formulas": formulas}
# ============ 数据管理（管理员专用） ============


@app.get("/api/admin/agent-memory/stats")
async def agent_memory_stats(_user: UserOut = Depends(require_permission("data:reset"))):
    """Agent 记忆统计"""
    if agent_memory is None:
        return {"total_memories": 0}
    return agent_memory.get_stats()


@app.post("/api/admin/reset/graph")
async def reset_graph(current_user: UserOut = Depends(require_permission("data:reset"))):
    """清空知识图谱所有数据"""
    try:
        result = kg_service.clear_all_data()
        from chem_agent.auth import database as auth_db
        auth_db.log_audit(
            action="clear_graph",
            user_id=current_user.id,
            username=current_user.username,
            resource_type="knowledge_graph",
            details=result,
        )
        return result
    except Exception as e:
        logger.error("清空知识图谱失败: %s", e)
        raise ChemAgentError(error_code=ErrorCode.DB_QUERY_FAILED, internal_detail=str(e))


@app.post("/api/admin/reset/knowledge-base")
async def reset_knowledge_base(current_user: UserOut = Depends(require_permission("data:reset"))):
    """清空知识库所有文档"""
    if kb_service is None:
        raise HTTPException(status_code=503, detail="知识库服务未初始化")
    try:
        result = kb_service.clear_all()
        from chem_agent.auth import database as auth_db
        auth_db.log_audit(
            action="clear_kb",
            user_id=current_user.id,
            username=current_user.username,
            resource_type="knowledge_base",
            details=result,
        )
        return result
    except Exception as e:
        logger.error("清空知识库失败: %s", e)
        raise ChemAgentError(error_code=ErrorCode.DB_QUERY_FAILED, internal_detail=str(e))


@app.post("/api/admin/reset/agent-memory")
async def reset_agent_memory(current_user: UserOut = Depends(require_permission("data:reset"))):
    """清空 Agent 经验记忆"""
    if agent_memory is None:
        raise HTTPException(status_code=503, detail="Agent 记忆服务未初始化")
    try:
        result = agent_memory.clear_all()
        from chem_agent.auth import database as auth_db
        auth_db.log_audit(
            action="clear_agent_memory",
            user_id=current_user.id,
            username=current_user.username,
            resource_type="agent_memory",
            details=result,
        )
        return result
    except Exception as e:
        logger.error("清空 Agent 记忆失败: %s", e)
        raise ChemAgentError(error_code=ErrorCode.DB_QUERY_FAILED, internal_detail=str(e))


@app.post("/api/admin/import-sample-data")
async def import_sample_data(current_user: UserOut = Depends(require_permission("data:reset"))):
    """重新导入样例数据到知识图谱"""
    try:
        from data.sample_data import get_all_sample_data
        from chem_agent.models import (
            RawMaterial as RM,
            Formula as FM,
            FormulaItem as FI,
            PerformanceTest as PT,
            ProcessCondition as PC,
        )

        sample = get_all_sample_data()
        mat_count = 0
        formula_count = 0

        # 导入原材料
        for mat_data in sample["materials"]:
            kg_service.upsert_material(RM(**mat_data))
            mat_count += 1

        # 导入配方
        for f_data in sample["formulas"]:
            items = []
            for item_data in f_data.get("items", []):
                mat = RM(
                    name=item_data["material"]["name"],
                    function=item_data["material"]["function"],
                )
                items.append(
                    FI(
                        material=mat,
                        weight_percent=item_data["weight_percent"],
                        addition_order=item_data.get("addition_order"),
                    )
                )
            process = PC(**f_data["process"]) if f_data.get("process") else None
            perfs = [PT(**p) for p in f_data.get("performance", [])]
            formula = FM(
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
            )
            kg_service.upsert_formula(formula)
            formula_count += 1

        result = {
            "status": "success",
            "imported_materials": mat_count,
            "imported_formulas": formula_count,
        }

        from chem_agent.auth import database as auth_db
        auth_db.log_audit(
            action="import_sample_data",
            user_id=current_user.id,
            username=current_user.username,
            resource_type="knowledge_graph",
            details=result,
        )
        return result
    except Exception as e:
        logger.error("导入样例数据失败: %s", e)
        raise ChemAgentError(error_code=ErrorCode.DB_QUERY_FAILED, internal_detail=str(e))
