"""数据库后端工厂模块。"""

from chem_agent.config import settings, AuthDBBackend
from chem_agent.auth.db_backends.base import AuthDBBackendBase
from chem_agent.auth.db_backends.sqlite_backend import SQLiteAuthDB
from chem_agent.auth.db_backends.postgres_backend import PostgresAuthDB
from chem_agent.auth.db_backends.mysql_backend import MySQLAuthDB

__all__ = ["AuthDBBackendBase", "SQLiteAuthDB", "PostgresAuthDB", "MySQLAuthDB", "create_backend"]


def create_backend() -> AuthDBBackendBase:
    """根据配置创建对应的数据库后端实例。"""
    backend_type = settings.auth_db_backend

    if backend_type == AuthDBBackend.SQLITE:
        return SQLiteAuthDB()
    elif backend_type == AuthDBBackend.POSTGRESQL:
        return PostgresAuthDB()
    elif backend_type == AuthDBBackend.MYSQL:
        return MySQLAuthDB()
    else:
        raise ValueError(f"Unsupported auth_db_backend: {backend_type}")
