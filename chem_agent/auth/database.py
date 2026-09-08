"""认证数据库操作层：统一接口，根据配置分发到不同后端 (SQLite/PostgreSQL/MySQL)。"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from chem_agent.config import settings
from chem_agent.auth.security import hash_password
from chem_agent.auth.db_backends import create_backend, AuthDBBackendBase

logger = logging.getLogger(__name__)

# ============ 后端单例 ============

_backend: Optional[AuthDBBackendBase] = None


def _get_backend() -> AuthDBBackendBase:
    """获取数据库后端实例（懒加载）。"""
    global _backend
    if _backend is None:
        _backend = create_backend()
    return _backend


def _close_backend():
    """关闭数据库后端连接。"""
    global _backend
    if _backend:
        _backend.dispose()
        _backend = None


# ============ System permission definitions ============

SYSTEM_PERMISSIONS = [
    ("formula:read", "formula", "read", "View formulas"),
    ("formula:write", "formula", "write", "Create/edit formulas"),
    ("formula:delete", "formula", "delete", "Delete formulas"),
    ("formula:analyze", "formula", "analyze", "AI analyze formulas"),
    ("formula:recommend", "formula", "recommend", "AI formula recommendation"),
    ("material:read", "material", "read", "View materials"),
    ("material:write", "material", "write", "Create/edit materials"),
    ("material:delete", "material", "delete", "Delete materials"),
    ("material:substitute", "material", "substitute", "AI material substitution"),
    ("prediction:read", "prediction", "read", "View predictions"),
    ("prediction:train", "prediction", "train", "Train prediction models"),
    ("chat:access", "chat", "access", "Use AI chat"),
    ("user:read", "user", "read", "View users"),
    ("user:write", "user", "write", "Create/edit users"),
    ("user:delete", "user", "delete", "Delete users"),
    ("role:read", "role", "read", "View roles"),
    ("role:write", "role", "write", "Create/edit roles"),
    ("role:delete", "role", "delete", "Delete roles"),
    ("category:read", "category", "read", "View categories"),
    ("category:write", "category", "write", "Create/edit categories"),
    ("category:delete", "category", "delete", "Delete categories"),
    ("config:read", "config", "read", "View system config"),
    ("config:write", "config", "write", "Modify system config"),
    ("audit:read", "audit", "read", "View audit logs"),
    ("knowledge:read", "knowledge", "read", "View knowledge base"),
    ("knowledge:write", "knowledge", "write", "Upload/delete KB documents"),
    ("data:reset", "data", "reset", "Reset system data"),
    ("doe:read", "doe", "read", "Generate DOE designs and list methods"),
    ("cost:read", "cost", "read", "Calculate formula BOM cost"),
    ("compliance:read", "compliance", "read", "Run compliance screening"),
    ("optimization:read", "optimization", "read", "Run formula optimization"),
    ("process:read", "process", "read", "Analyze process SPC data"),
    ("scaleup:read", "scaleup", "read", "Calculate scale-up recommendations"),
    ("stability:read", "stability", "read", "Predict formula stability/shelf life"),
    ("sustainability:read", "sustainability", "read", "Assess sustainability metrics"),
    ("quality:read", "quality", "read", "View quality specs and COA reports"),
    ("quality:write", "quality", "write", "Create/update quality templates and COA"),
    ("experiment:read", "experiment", "read", "View experiment records"),
    ("experiment:write", "experiment", "write", "Create/update experiment records"),
    ("experiment:delete", "experiment", "delete", "Delete or reset experiment records"),
    ("risk:read", "risk", "read", "Run formula safety risk analysis"),
]

DEFAULT_ROLES = {
    "admin": {
        "display_name": "管理员",
        "description": "Business admin with full management access",
        "permissions": [p[0] for p in SYSTEM_PERMISSIONS],
    },
    "researcher": {
        "display_name": "研发人员",
        "description": "R&D personnel with formula and material access",
        "permissions": [
            "formula:read", "formula:write", "formula:analyze", "formula:recommend",
            "material:read", "material:write", "material:substitute",
            "prediction:read", "prediction:train",
            "chat:access",
            "knowledge:read", "knowledge:write",
            "doe:read", "cost:read", "compliance:read",
            "optimization:read", "process:read", "scaleup:read",
            "stability:read", "sustainability:read",
            "quality:read", "quality:write",
            "experiment:read", "experiment:write",
            "risk:read",
        ],
    },
    "viewer": {
        "display_name": "只读用户",
        "description": "Read-only access to formulas and materials",
        "permissions": [
            "formula:read", "material:read", "chat:access",
            "knowledge:read",
            "doe:read", "cost:read", "compliance:read",
            "optimization:read", "process:read", "scaleup:read",
            "stability:read", "sustainability:read",
            "quality:read", "experiment:read", "risk:read",
        ],
    },
}

DEFAULT_PRODUCT_CATEGORIES = [
    ("cat_coating", "涂料", "Coating"),
    ("cat_adhesive", "胶粘剂", "Adhesive"),
    ("cat_sealant", "密封剂", "Sealant"),
    ("cat_resin", "树脂", "Resin"),
    ("cat_surfactant", "表面活性剂", "Surfactant"),
    ("cat_catalyst", "催化剂", "Catalyst"),
    ("cat_additive", "助剂", "Additive"),
    ("cat_plastic", "塑料", "Plastic"),
    ("cat_rubber", "橡胶", "Rubber"),
    ("cat_ink", "油墨", "Ink"),
    ("cat_other", "其他", "Other"),
]

DEFAULT_FUNCTION_CATEGORIES = [
    ("func_base_resin", "基础树脂", "Base Resin"),
    ("func_solvent", "溶剂", "Solvent"),
    ("func_filler", "填料", "Filler"),
    ("func_pigment", "颜料", "Pigment"),
    ("func_curing_agent", "固化剂", "Curing Agent"),
    ("func_catalyst", "催化剂", "Catalyst"),
    ("func_dispersant", "分散剂", "Dispersant"),
    ("func_leveling", "流平剂", "Leveling Agent"),
    ("func_defoamer", "消泡剂", "Defoamer"),
    ("func_thickener", "增稠剂", "Thickener"),
    ("func_plasticizer", "增塑剂", "Plasticizer"),
    ("func_antioxidant", "抗氧化剂", "Antioxidant"),
    ("func_uv_stabilizer", "紫外稳定剂", "UV Stabilizer"),
    ("func_flame_retardant", "阻燃剂", "Flame Retardant"),
    ("func_coupling_agent", "偶联剂", "Coupling Agent"),
    ("func_wetting_agent", "润湿剂", "Wetting Agent"),
    ("func_other", "其他", "Other"),
]


# ============ Connection ============

def get_db_connection():
    """获取数据库连接（兼容旧接口）。"""
    return _get_backend()


# ============ Schema Init ============

def init_db() -> None:
    """初始化数据库表结构和默认数据。"""
    db = _get_backend()
    db.init_schema()

    for code, resource, action, desc in SYSTEM_PERMISSIONS:
        try:
            db.execute(
                "INSERT INTO permissions (code, resource, action, description) VALUES (?, ?, ?, ?)",
                (code, resource, action, desc),
            )
            db.commit()
        except Exception:
            db.rollback()

    now = datetime.now(timezone.utc).isoformat()
    for role_name, info in DEFAULT_ROLES.items():
        db.execute(
            "INSERT OR IGNORE INTO roles (name, display_name, description, is_system) VALUES (?, ?, ?, 1)",
            (role_name, info["display_name"], info["description"]),
        )
        db.commit()
        role = db.fetchone("SELECT id FROM roles WHERE name = ?", (role_name,))
        if role:
            for perm_code in info["permissions"]:
                perm = db.fetchone("SELECT id FROM permissions WHERE code = ?", (perm_code,))
                if perm:
                    try:
                        db.execute(
                            "INSERT INTO role_permissions (role_id, permission_id) VALUES (?, ?)",
                            (role["id"], perm["id"]),
                        )
                        db.commit()
                    except Exception:
                        db.rollback()

    for code, zh, en in DEFAULT_PRODUCT_CATEGORIES:
        try:
            db.execute(
                "INSERT INTO category_configs (type, code, display_zh, display_en) VALUES ('product', ?, ?, ?)",
                (code, zh, en),
            )
            db.commit()
        except Exception:
            db.rollback()
    for code, zh, en in DEFAULT_FUNCTION_CATEGORIES:
        try:
            db.execute(
                "INSERT INTO category_configs (type, code, display_zh, display_en) VALUES ('function', ?, ?, ?)",
                (code, zh, en),
            )
            db.commit()
        except Exception:
            db.rollback()

    existing = db.fetchone("SELECT id FROM users WHERE username = ?", ("admin",))
    if not existing:
        db.execute(
            "INSERT INTO users (username, hashed_password, full_name, is_superadmin) VALUES (?, ?, ?, 1)",
            ("admin", hash_password("admin123"), "系统管理员"),
        )
        db.commit()
        admin = db.fetchone("SELECT id FROM users WHERE username = ?", ("admin",))
        admin_role = db.fetchone("SELECT id FROM roles WHERE name = ?", ("admin",))
        if admin and admin_role:
            db.execute(
                "INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)",
                (admin["id"], admin_role["id"]),
            )
            db.commit()

    logger.info("Database initialized with default data")


# ============ User CRUD ============

def create_user(username, password, role_ids=None, email=None, full_name=None):
    db = _get_backend()
    db.execute(
        "INSERT INTO users (username, hashed_password, email, full_name) VALUES (?, ?, ?, ?)",
        (username, hash_password(password), email, full_name),
    )
    db.commit()
    user = db.fetchone("SELECT id FROM users WHERE username = ?", (username,))
    user_id = user["id"]
    if role_ids:
        now = datetime.now(timezone.utc).isoformat()
        for rid in role_ids:
            db.execute(
                "INSERT INTO user_roles (user_id, role_id, assigned_at) VALUES (?, ?, ?)",
                (user_id, rid, now),
            )
        db.commit()
    return user_id


def get_user_by_username(username):
    return _get_backend().fetchone("SELECT * FROM users WHERE username = ?", (username,))


def get_user_by_id(user_id):
    return _get_backend().fetchone("SELECT * FROM users WHERE id = ?", (user_id,))


def list_users(page=1, limit=20):
    db = _get_backend()
    total = db.fetchone("SELECT COUNT(*) as cnt FROM users")["cnt"]
    offset = (page - 1) * limit
    rows = db.fetchall(
        "SELECT * FROM users ORDER BY id DESC LIMIT ? OFFSET ?",
        (limit, offset),
    )
    return rows or [], total


def update_user(user_id, **kwargs):
    allowed = {"email", "full_name", "is_active"}
    fields = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if not fields:
        return False
    db = _get_backend()
    set_parts = [f"{k} = ?" for k in fields]
    values = list(fields.values()) + [user_id]
    db.execute(
        f"UPDATE users SET {', '.join(set_parts)} WHERE id = ?",
        tuple(values),
    )
    db.commit()
    return True


def change_password(user_id, new_password):
    db = _get_backend()
    db.execute(
        "UPDATE users SET hashed_password = ? WHERE id = ?",
        (hash_password(new_password), user_id),
    )
    db.commit()
    return True


def update_last_login(user_id):
    db = _get_backend()
    now = datetime.now(timezone.utc).isoformat()
    db.execute("UPDATE users SET last_login = ? WHERE id = ?", (now, user_id))
    db.commit()


def delete_user(user_id):
    db = _get_backend()
    db.execute("DELETE FROM user_roles WHERE user_id = ?", (user_id,))
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    return True


def get_user_permissions(user_id):
    db = _get_backend()
    sql = (
        "SELECT DISTINCT p.code FROM permissions p "
        "JOIN role_permissions rp ON p.id = rp.permission_id "
        "JOIN user_roles ur ON rp.role_id = ur.role_id "
        "WHERE ur.user_id = ?"
    )
    rows = db.fetchall(sql, (user_id,))
    return [r["code"] for r in (rows or [])]


# ============ Role CRUD ============

def list_roles():
    return _get_backend().fetchall("SELECT * FROM roles ORDER BY id") or []


def get_role_by_id(role_id):
    return _get_backend().fetchone("SELECT * FROM roles WHERE id = ?", (role_id,))


def create_role(name, display_name, description=None, permission_ids=None):
    db = _get_backend()
    db.execute(
        "INSERT INTO roles (name, display_name, description) VALUES (?, ?, ?)",
        (name, display_name, description),
    )
    db.commit()
    role = db.fetchone("SELECT id FROM roles WHERE name = ?", (name,))
    role_id = role["id"]
    if permission_ids:
        for pid in permission_ids:
            db.execute(
                "INSERT INTO role_permissions (role_id, permission_id) VALUES (?, ?)",
                (role_id, pid),
            )
        db.commit()
    return role_id


def update_role(role_id, **kwargs):
    allowed = {"display_name", "description"}
    fields = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if not fields:
        return False
    db = _get_backend()
    set_parts = [f"{k} = ?" for k in fields]
    values = list(fields.values()) + [role_id]
    db.execute(
        f"UPDATE roles SET {', '.join(set_parts)} WHERE id = ?",
        tuple(values),
    )
    db.commit()
    return True


def delete_role(role_id):
    db = _get_backend()
    db.execute("DELETE FROM role_permissions WHERE role_id = ?", (role_id,))
    db.execute("DELETE FROM user_roles WHERE role_id = ?", (role_id,))
    db.execute("DELETE FROM roles WHERE id = ?", (role_id,))
    db.commit()
    return True


def set_role_permissions(role_id, permission_ids):
    db = _get_backend()
    db.execute("DELETE FROM role_permissions WHERE role_id = ?", (role_id,))
    for pid in permission_ids:
        db.execute(
            "INSERT INTO role_permissions (role_id, permission_id) VALUES (?, ?)",
            (role_id, pid),
        )
    db.commit()


def get_role_permissions(role_id):
    sql = (
        "SELECT p.* FROM permissions p "
        "JOIN role_permissions rp ON p.id = rp.permission_id "
        "WHERE rp.role_id = ?"
    )
    return _get_backend().fetchall(sql, (role_id,)) or []


def list_all_permissions():
    return _get_backend().fetchall("SELECT * FROM permissions ORDER BY resource, action") or []


def set_user_roles(user_id, role_ids):
    db = _get_backend()
    db.execute("DELETE FROM user_roles WHERE user_id = ?", (user_id,))
    now = datetime.now(timezone.utc).isoformat()
    for rid in role_ids:
        db.execute(
            "INSERT INTO user_roles (user_id, role_id, assigned_at) VALUES (?, ?, ?)",
            (user_id, rid, now),
        )
    db.commit()


def get_user_roles(user_id):
    sql = (
        "SELECT r.* FROM roles r "
        "JOIN user_roles ur ON r.id = ur.role_id "
        "WHERE ur.user_id = ?"
    )
    return _get_backend().fetchall(sql, (user_id,)) or []


# ============ Category CRUD ============

def list_categories(cat_type=None):
    db = _get_backend()
    if cat_type:
        rows = db.fetchall(
            "SELECT * FROM category_configs WHERE type = ? ORDER BY sort_order",
            (cat_type,),
        )
    else:
        rows = db.fetchall("SELECT * FROM category_configs ORDER BY type, sort_order")
    return rows or []


def create_category(cat_type, code, display_zh, display_en, sort_order=0):
    db = _get_backend()
    db.execute(
        "INSERT INTO category_configs (type, code, display_zh, display_en, sort_order) VALUES (?, ?, ?, ?, ?)",
        (cat_type, code, display_zh, display_en, sort_order),
    )
    db.commit()
    row = db.fetchone(
        "SELECT id FROM category_configs WHERE type = ? AND code = ?",
        (cat_type, code),
    )
    return row["id"] if row else 0


def update_category(cat_id, **kwargs):
    allowed = {"display_zh", "display_en", "sort_order", "is_enabled"}
    fields = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if not fields:
        return False
    db = _get_backend()
    set_parts = [f"{k} = ?" for k in fields]
    values = list(fields.values()) + [cat_id]
    db.execute(
        f"UPDATE category_configs SET {', '.join(set_parts)} WHERE id = ?",
        tuple(values),
    )
    db.commit()
    return True


def delete_category(cat_id):
    db = _get_backend()
    db.execute("DELETE FROM category_configs WHERE id = ?", (cat_id,))
    db.commit()
    return True


# ============ System Config ============

def get_all_configs():
    return _get_backend().fetchall("SELECT * FROM system_configs ORDER BY key") or []


def get_config(key):
    row = _get_backend().fetchone("SELECT value FROM system_configs WHERE key = ?", (key,))
    return row["value"] if row else None


def set_config(key, value, description=None, user_id=None):
    db = _get_backend()
    now = datetime.now(timezone.utc).isoformat()
    backend_type = settings.auth_db_backend.value
    if backend_type == "sqlite":
        db.execute(
            "INSERT INTO system_configs (key, value, description, updated_at, updated_by) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = ?, updated_by = ?",
            (key, value, description, now, user_id, value, now, user_id),
        )
    elif backend_type == "postgresql":
        db.execute(
            "INSERT INTO system_configs (key, value, description, updated_at, updated_by) "
            "VALUES (%s, %s, %s, %s, %s) "
            "ON CONFLICT (key) DO UPDATE SET value = %s, updated_at = %s, updated_by = %s",
            (key, value, description, now, user_id, value, now, user_id),
        )
    else:
        try:
            db.execute(
                "INSERT INTO system_configs (key, value, description, updated_at, updated_by) "
                "VALUES (%s, %s, %s, %s, %s)",
                (key, value, description, now, user_id),
            )
            db.commit()
        except Exception:
            db.rollback()
            db.execute(
                "UPDATE system_configs SET value = %s, updated_at = %s, updated_by = %s WHERE key = %s",
                (value, now, user_id, key),
            )
    db.commit()


# ============ Audit Log ============

def log_audit(action, user_id=None, username=None, resource_type=None,
              resource_id=None, details=None, status="success"):
    try:
        db = _get_backend()
        db.execute(
            "INSERT INTO audit_logs (user_id, username, action, resource_type, resource_id, details, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, username, action, resource_type, resource_id,
             json.dumps(details, ensure_ascii=False) if details else None, status),
        )
        db.commit()
    except Exception as e:
        logger.warning("Failed to write audit log: %s", e)


def query_audit_logs(user_id=None, action=None, resource_type=None, page=1, limit=50):
    db = _get_backend()
    where_parts = []
    params = []
    if user_id is not None:
        where_parts.append("user_id = ?")
        params.append(user_id)
    if action:
        where_parts.append("action = ?")
        params.append(action)
    if resource_type:
        where_parts.append("resource_type = ?")
        params.append(resource_type)

    where_sql = "WHERE " + " AND ".join(where_parts) if where_parts else ""

    total = db.fetchone(
        f"SELECT COUNT(*) as cnt FROM audit_logs {where_sql}",
        tuple(params),
    )["cnt"]
    offset = (page - 1) * limit
    rows = db.fetchall(
        f"SELECT * FROM audit_logs {where_sql} ORDER BY id DESC LIMIT ? OFFSET ?",
        tuple(params + [limit, offset]),
    )
    return rows or [], total


# ============ Formula Version Management ============

def save_formula_version(formula_code, snapshot_data, change_summary=None, changed_by=None):
    """保存配方快照版本，返回版本号。"""
    db = _get_backend()
    row = db.fetchone(
        "SELECT COALESCE(MAX(version_number), 0) + 1 as next_ver "
        "FROM formula_versions WHERE formula_code = ?",
        (formula_code,),
    )
    next_ver = row["next_ver"] if row else 1
    db.execute(
        "INSERT INTO formula_versions (formula_code, version_number, snapshot_data, change_summary, changed_by) "
        "VALUES (?, ?, ?, ?, ?)",
        (formula_code, next_ver, json.dumps(snapshot_data, ensure_ascii=False),
         change_summary, changed_by),
    )
    db.commit()
    return next_ver


def get_formula_versions(formula_code):
    """获取配方的所有版本历史。"""
    rows = _get_backend().fetchall(
        "SELECT * FROM formula_versions WHERE formula_code = ? ORDER BY version_number DESC",
        (formula_code,),
    )
    return rows or []


def get_formula_version(formula_code, version_number):
    """获取配方指定版本的快照。"""
    return _get_backend().fetchone(
        "SELECT * FROM formula_versions WHERE formula_code = ? AND version_number = ?",
        (formula_code, version_number),
    )


def get_latest_formula_version(formula_code):
    """获取配方的最新版本快照。"""
    return _get_backend().fetchone(
        "SELECT * FROM formula_versions WHERE formula_code = ? ORDER BY version_number DESC LIMIT 1",
        (formula_code,),
    )
