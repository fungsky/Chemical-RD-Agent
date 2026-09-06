"""MySQL 数据库后端。

需要: pip install pymysql>=1.1.0
"""

import logging
from typing import Optional

from chem_agent.config import settings
from chem_agent.auth.db_backends.base import AuthDBBackendBase

logger = logging.getLogger(__name__)

MYSQL_SCHEMA = '''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(128) UNIQUE NOT NULL,
    email VARCHAR(256),
    hashed_password TEXT NOT NULL,
    full_name VARCHAR(256),
    is_active BOOLEAN DEFAULT TRUE,
    is_superadmin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS roles (
    id INTEGER AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(128) UNIQUE NOT NULL,
    display_name VARCHAR(256) NOT NULL,
    description TEXT,
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS permissions (
    id INTEGER AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(128) UNIQUE NOT NULL,
    resource VARCHAR(128) NOT NULL,
    action VARCHAR(64) NOT NULL,
    description TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS user_roles (
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS category_configs (
    id INTEGER AUTO_INCREMENT PRIMARY KEY,
    type VARCHAR(64) NOT NULL,
    code VARCHAR(128) NOT NULL,
    display_zh VARCHAR(256) NOT NULL,
    display_en VARCHAR(256) NOT NULL,
    sort_order INTEGER DEFAULT 0,
    is_enabled BOOLEAN DEFAULT TRUE,
    UNIQUE KEY uq_type_code (type, code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS system_configs (
    key VARCHAR(256) PRIMARY KEY,
    alue TEXT,
    description TEXT,
    updated_at TIMESTAMP NULL,
    updated_by INTEGER
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER AUTO_INCREMENT PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER,
    username VARCHAR(128),
    action VARCHAR(128) NOT NULL,
    resource_type VARCHAR(64),
    resource_id VARCHAR(256),
    details TEXT,
    status VARCHAR(32) DEFAULT 'success'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS formula_versions (
    id INTEGER AUTO_INCREMENT PRIMARY KEY,
    formula_code VARCHAR(128) NOT NULL,
    version_number INTEGER NOT NULL,
    snapshot_data JSON NOT NULL,
    change_summary TEXT,
    changed_by VARCHAR(128),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_fv (formula_code, version_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_category_type ON category_configs(type);
CREATE INDEX IF NOT EXISTS idx_fv_formula ON formula_versions(formula_code);
'''


class MySQLAuthDB(AuthDBBackendBase):
    SCHEMA_SQL = MYSQL_SCHEMA
    param_placeholder = '%s'

    def __init__(self):
        self._pool = None
        self._conn = None
        self._import_pymysql()

    @staticmethod
    def _import_pymysql():
        try:
            import pymysql
            return pymysql
        except ImportError:
            raise ImportError(
                "MySQL backend requires pymysql. Install with: pip install pymysql>=1.1.0"
            )

    @property
    def _pymysql(self):
        return self._import_pymysql()

    def _create_pool(self):
        pymysql = self._pymysql
        self._pool = pymysql.connect(
            host=settings.mysql_host,
            port=settings.mysql_port,
            database=settings.mysql_db,
            user=settings.mysql_user,
            password=settings.mysql_password,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
        )
        logger.info("MySQL connected to %s:%d", settings.mysql_host, settings.mysql_port)

    def connect(self):
        if self._pool is None:
            self._create_pool()
        if self._conn is None:
            self._conn = self._pool
        self._pool.ping(reconnect=True)
        return self._conn

    def execute(self, sql: str, params: tuple = None):
        conn = self.connect()
        cursor = conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        return cursor

    def execute_many(self, sql: str, params_list: list[tuple]):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.executemany(sql, params_list)
        return cursor

    def commit(self):
        if self._conn:
            self._conn.commit()

    def rollback(self):
        if self._conn:
            self._conn.rollback()

    def close(self):
        pass  # Pool managed

    def _row_to_dict(self, row) -> dict:
        if row is None:
            return None
        if isinstance(row, dict):
            return row
        cursor = self.execute("SELECT 1")
        cols = [desc[0] for desc in cursor.description]
        return dict(zip(cols, row))

    def last_row_id(self, cursor) -> int:
        return cursor.lastrowid

    def init_schema(self):
        conn = self.connect()
        cursor = conn.cursor()
        for statement in self.SCHEMA_SQL.split(';'):
            stmt = statement.strip()
            if stmt:
                cursor.execute(stmt)
        conn.commit()
        logger.info("MySQL schema initialized")

    def dispose(self):
        if self._pool:
            self._pool.close()
            self._pool = None
        self._conn = None

    @property
    def param_placeholder(self) -> str:
        return '%s'