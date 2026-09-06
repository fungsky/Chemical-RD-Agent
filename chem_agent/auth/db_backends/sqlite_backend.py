"""SQLite 数据库后端。"""

import json
import logging
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from chem_agent.config import settings
from chem_agent.auth.db_backends.base import AuthDBBackendBase
from chem_agent.auth.security import hash_password

logger = logging.getLogger(__name__)

SQLITE_SCHEMA = '''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT,
    hashed_password TEXT NOT NULL,
    full_name TEXT,
    is_active INTEGER DEFAULT 1,
    is_superadmin INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    last_login TEXT
);

CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT,
    is_system INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    resource TEXT NOT NULL,
    action TEXT NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS user_roles (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE IF NOT EXISTS category_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    code TEXT NOT NULL,
    display_zh TEXT NOT NULL,
    display_en TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0,
    is_enabled INTEGER DEFAULT 1,
    UNIQUE(type, code)
);

CREATE TABLE IF NOT EXISTS system_configs (
    key TEXT PRIMARY KEY,
    value TEXT,
    description TEXT,
    updated_at TEXT,
    updated_by INTEGER
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT DEFAULT (datetime('now')),
    user_id INTEGER,
    username TEXT,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    details TEXT,
    status TEXT DEFAULT 'success'
);

CREATE TABLE IF NOT EXISTS formula_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    formula_code TEXT NOT NULL,
    version_number INTEGER NOT NULL,
    snapshot_data TEXT NOT NULL,
    change_summary TEXT,
    changed_by TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(formula_code, version_number)
);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_category_type ON category_configs(type);
CREATE INDEX IF NOT EXISTS idx_fv_formula ON formula_versions(formula_code);
'''


class SQLiteAuthDB(AuthDBBackendBase):
    SCHEMA_SQL = SQLITE_SCHEMA
    param_placeholder = "?"

    def __init__(self, db_path: str = None):
        self._db_path = db_path or settings.auth_db_path
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self):
        if self._conn is None:
            self._conn = sqlite3.connect(self._db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    def execute(self, sql: str, params: tuple = None):
        conn = self.connect()
        if params:
            return conn.execute(sql, params)
        return conn.execute(sql)

    def execute_many(self, sql: str, params_list: list[tuple]):
        conn = self.connect()
        return conn.executemany(sql, params_list)

    def commit(self):
        if self._conn:
            self._conn.commit()

    def rollback(self):
        if self._conn:
            self._conn.rollback()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def _row_to_dict(self, row) -> dict:
        return dict(row) if row else None

    def last_row_id(self, cursor) -> int:
        return cursor.lastrowid

    def init_schema(self):
        conn = self.connect()
        conn.executescript(self.SCHEMA_SQL)
        conn.commit()
        logger.info("SQLite schema initialized at %s", self._db_path)

    def dispose(self):
        self.close()

    @property
    def param_placeholder(self) -> str:
        return "?"