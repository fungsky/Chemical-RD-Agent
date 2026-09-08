"""应用配置管理"""

from enum import Enum
from typing import Optional

from pydantic_settings import BaseSettings


class AuthDBBackend(str, Enum):
    """认证数据库后端枚举"""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"


class Settings(BaseSettings):
    """全局配置"""

    # 应用设置
    app_name: str = "ChemAgent - 化工研发智能体"
    app_version: str = "0.1.0"
    debug: bool = True

    # Neo4j 配置
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "chemagent2024"
    neo4j_database: str = "neo4j"

    # === LLM 配置 ===
    llm_provider: str = ""              # Provider 代码 (空=未配置)
    llm_base_url: str = ""              # API Base URL
    llm_model: str = ""                 # Chat 模型名
    llm_api_key: str = ""               # API Key
    llm_max_tokens: int = 4096          # Token 上下文窗口
    llm_temperature: float = 0.7        # 生成温度
    llm_reasoning_effort: str = "medium"  # 推理强度: none/minimal/low/medium/high/xhigh/max/ultra

    # === Embedder 配置 ===
    embedding_provider: str = ""        # "same_as_llm" 或 Provider 代码
    embedding_base_url: str = ""
    embedding_model: str = ""
    embedding_api_key: str = ""

    # Azure OpenAI 专用字段
    azure_deployment_name: str = ""
    azure_api_version: str = "2024-02-01"

    # 向量检索配置
    embedding_dim: int = 768
    similarity_top_k: int = 5

    # API 服务配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Streamlit 配置
    streamlit_port: int = 8501

    # === 认证 & 数据库配置 ===
    auth_db_backend: AuthDBBackend = AuthDBBackend.SQLITE
    auth_db_path: str = "./data/chemagent_auth.db"
    # 本地免登录模式：True 时所有接口跳过 JWT 校验（仅限本地/内网使用）
    auth_bypass: bool = False

    # PostgreSQL 连接配置
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "chemagent"
    postgres_user: str = "chemagent"
    postgres_password: str = "chemagent2024"
    postgres_min_conn: int = 2
    postgres_max_conn: int = 10

    # MySQL 连接配置
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_db: str = "chemagent"
    mysql_user: str = "chemagent"
    mysql_password: str = "chemagent2024"
    mysql_min_conn: int = 2
    mysql_max_conn: int = 10

    jwt_secret_key: str = "chemagent-dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_expire_minutes: int = 60
    jwt_refresh_expire_days: int = 7

    # 知识库配置
    chroma_persist_dir: str = "./data/chromadb"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    rag_top_k: int = 3
    max_file_size_mb: int = 10

    # Agent 智能体配置
    agent_max_iterations: int = 10
    agent_tool_timeout: int = 30
    agent_enabled: bool = True

    # Agent 反思配置
    agent_reflection_enabled: bool = True
    agent_max_reflections: int = 2

    # Agent 记忆配置
    agent_memory_enabled: bool = True
    agent_memory_top_k: int = 2
    agent_memory_threshold: float = 0.75
    agent_memory_max_size: int = 200

    # Agent 规划配置
    agent_planning_enabled: bool = True

    # 性能优化配置
    llm_timeout_seconds: int = 60
    cache_ttl_seconds: int = 60

    model_config = {
        "env_file": ".env",
        "env_prefix": "CHEM_",
        "case_sensitive": False,
    }


settings = Settings()
