"""数据库后端抽象基类。"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class AuthDBBackendBase(ABC):
    """认证数据库后端的抽象接口。"""

    SCHEMA_SQL: str = ""  # 子类覆盖：建表 DDL

    @abstractmethod
    def connect(self):
        """获取数据库连接（支持上下文管理器）。"""

    @abstractmethod
    def execute(self, sql: str, params: tuple = None):
        """执行 SQL，返回 cursor。"""

    @abstractmethod
    def execute_many(self, sql: str, params_list: list[tuple]):
        """批量执行 SQL。"""

    @abstractmethod
    def commit(self):
        """提交事务。"""

    @abstractmethod
    def rollback(self):
        """回滚事务。"""

    @abstractmethod
    def close(self):
        """关闭连接。"""

    def fetchone(self, sql: str, params: tuple = None) -> Optional[dict]:
        """执行查询并返回一行。"""
        cursor = self.execute(sql, params)
        return self._row_to_dict(cursor.fetchone()) if cursor else None

    def fetchall(self, sql: str, params: tuple = None) -> list[dict]:
        """执行查询并返回所有行。"""
        cursor = self.execute(sql, params)
        return [self._row_to_dict(r) for r in cursor.fetchall()]

    @abstractmethod
    def _row_to_dict(self, row: Any) -> dict:
        """将数据库行转换为字典。"""

    @abstractmethod
    def last_row_id(self, cursor) -> int:
        """返回最后插入行的 ID。"""

    @abstractmethod
    def init_schema(self):
        """初始化数据库表结构。"""

    @abstractmethod
    def dispose(self):
        """释放连接池等资源。"""

    @property
    @abstractmethod
    def param_placeholder(self) -> str:
        """参数占位符：SQLite 用 ?，PostgreSQL/MySQL 用 %s。"""

    def format_sql(self, template: str) -> str:
        """将 SQL 模板中的 {param} 替换为实际占位符。"""
        return template.replace("?", self.param_placeholder)