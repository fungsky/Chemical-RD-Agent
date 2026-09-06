"""PostgreSQL 数据库后端。

需要: pip install psycopg2-binary>=2.9.9
"""

import logging
from contextlib import contextmanager
from typing import Optional

from chem_agent.config import settings
from chem_agent.auth.db_backends.base import AuthDBBackendBase

logger = logging.getLogger(__name__)

PG_SCHEMA = '''
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(128) UNIQUE NOT NULL,
    email VARCHAR(256),
    hashed_password TEXT NOT NULL,
    full_name VARCHAR(256),
    is_active BOOLEAN DEFAULT TRUE,
    is_superadmin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(128) UNIQUE NOT NULL,
    display_name VARCHAR(256) NOT NULL,
    description TEXT,
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    code VARCHAR(128) UNIQUE NOT NULL,
    resource VARCHAR(128) NOT NULL,
    action VARCHAR(64) NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS user_roles (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE IF NOT EXISTS category_configs (
    id SERIAL PRIMARY KEY,
    type VARCHAR(64) NOT NULL,
    code VARCHAR(128) NOT NULL,
    display_zh VARCHAR(256) NOT NULL,
    display_en VARCHAR(256) NOT NULL,
    sort_order INTEGER DEFAULT 0,
    is_enabled BOOLEAN DEFAULT TRUE,
    UNIQUE(type, code)
);

CREATE TABLE IF NOT EXISTS system_configs (
    key VARCHAR(256) PRIMARY KEY,
    value TEXT,
    description TEXT,
    updated_at TIMESTAMP,
    updated_by INTEGER
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),
    user_id INTEGER,
    username VARCHAR(128),
    action VARCHAR(128) NOT NULL,
    resource_type VARCHAR(64),
    resource_id VARCHAR(256),
    details TEXT,
    status VARCHAR(32) DEFAULT 'success'
);

CREATE TABLE IF NOT EXISTS formula_versions (
    id SERIAL PRIMARY KEY,
    formula_code VARCHAR(128) NOT NULL,
    version_number INTEGER NOT NULL,
    snapshot_data JSONB NOT NULL,
    change_summary TEXT,
    changed_by VARCHAR(128),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(formula_code, version_number)
);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_category_type ON category_configs(type);
CREATE INDEX IF NOT EXISTS idx_fv_formula ON formula_versions(formula_code);
'''


class PostgresAuthDB(AuthDBBackendBase):
    SCHEMA_SQL = PG_SCHEMA
    param_placeholder = '%s'

    def __init__(self):
        self._pool = None
        self._conn = None
        self._import_psycopg2()

    @staticmethod
    def _import_psycopg2():
        try:
            import psycopg2
            import psycopg2.pool
            return psycopg2
        except ImportError:
            raise ImportError(
                "PostgreSQL backend requires psycopg2-binary. Install with: pip install psycopg2-binary>=2.9.9"
            )

    @property
    def _psycopg2(self):
        return self._import_psycopg2()

    def _create_pool(self):
        psycopg2 = self._psycopg2
        self._pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=settings.postgres_min_conn,
            maxconn=settings.postgres_max_conn,
            host=settings.postgres_host,
            port=settings.postgres_port,
            dbname=settings.postgres_db,
            user=settings.postgres_user,
            password=settings.postgres_password,
        )
        logger.info("PostgreSQL pool created (%d-%d connections)",
                     settings.postgres_min_conn, settings.postgres_max_conn)

    def connect(self):
        if self._pool is None:
            self._create_pool()
        if self._conn is None or self._conn.closed:
            self._conn = self._pool.getconn()
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
        if self._conn and not self._conn.closed:
            self._conn.commit()

    def rollback(self):
        if self._conn and not self._conn.closed:
            self._conn.rollback()

    def close(self):
        if self._pool and self._conn and not self._conn.closed:
            self._pool.putconn(self._conn)
            self._conn = None

    def _row_to_dict(self, row) -> dict:
        if row is None:
            return None
        cursor = self.execute("SELECT 1")
        cols = [desc[0] for desc in cursor.description]
        return dict(zip(cols, row))

    def last_row_id(self, cursor) -> int:
        return cursor.fetchone()[0] if cursor.description else 0

    def init_schema(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(self.SCHEMA_SQL)
        conn.commit()
        logger.info("PostgreSQL schema initialized")

    def dispose(self):
        if self._pool:
            self._pool.closeall()
            self._pool = None
        self._conn = None

    @property
    def param_placeholder(self) -> str:
        return '%s'

    # Override: PG doesn't have lastrowid, use RETURNING
    def last_row_id(self, cursor) -> int:
        row = cursor.fetchone()
        return row[0] if row else 0