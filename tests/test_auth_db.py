"""测试 - 认证数据库层 (SQLite 后端)。"""

import os
import tempfile
import pytest

# 强制使用 SQLite 后端
os.environ["CHEM_AUTH_DB_BACKEND"] = "sqlite"


@pytest.fixture(autouse=True)
def _reset_backend():
    """每个测试前后重置后端单例。"""
    from chem_agent.auth.database import _close_backend
    _close_backend()
    yield
    _close_backend()


@pytest.fixture
def db_path(monkeypatch):
    """创建临时 SQLite 数据库。"""
    from chem_agent.config import settings
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = os.path.join(tmpdir, "test_auth.db")
        # settings 单例在模块导入时已实例化，环境变量已无效，需直接改写配置
        monkeypatch.setattr(settings, "auth_db_path", db_file)
        yield db_file
        # 先关闭后端连接再删除临时目录，避免 Windows 文件锁
        from chem_agent.auth.database import _close_backend
        _close_backend()


@pytest.fixture
def init_db(db_path):
    """初始化数据库。"""
    from chem_agent.auth.database import init_db
    init_db()


class TestUserCRUD:
    def test_create_user(self, db_path, init_db):
        from chem_agent.auth import database as db
        user_id = db.create_user("testuser", "testpass", email="test@test.com", full_name="Test User")
        assert user_id > 0

        user = db.get_user_by_username("testuser")
        assert user is not None
        assert user["username"] == "testuser"
        assert user["email"] == "test@test.com"

    def test_get_user_not_found(self, db_path, init_db):
        from chem_agent.auth import database as db
        user = db.get_user_by_username("nonexistent")
        assert user is None

    def test_list_users(self, db_path, init_db):
        from chem_agent.auth import database as db
        # admin already exists
        users, total = db.list_users()
        assert total >= 1

    def test_update_user(self, db_path, init_db):
        from chem_agent.auth import database as db
        user_id = db.create_user("update_test", "pass")
        result = db.update_user(user_id, full_name="Updated Name", email="new@test.com")
        assert result is True
        user = db.get_user_by_id(user_id)
        assert user["full_name"] == "Updated Name"

    def test_change_password(self, db_path, init_db):
        from chem_agent.auth import database as db
        from chem_agent.auth.security import verify_password
        user_id = db.create_user("pwtest", "oldpass")
        db.change_password(user_id, "newpass")
        user = db.get_user_by_id(user_id)
        assert verify_password("newpass", user["hashed_password"])

    def test_delete_user(self, db_path, init_db):
        from chem_agent.auth import database as db
        user_id = db.create_user("deleteme", "pass")
        db.delete_user(user_id)
        user = db.get_user_by_id(user_id)
        assert user is None


class TestRoleCRUD:
    def test_list_roles(self, db_path, init_db):
        from chem_agent.auth import database as db
        roles = db.list_roles()
        assert len(roles) >= 3  # admin, researcher, viewer

    def test_create_and_delete_role(self, db_path, init_db):
        from chem_agent.auth import database as db
        role_id = db.create_role("tester", "测试角色", "Test role")
        assert role_id > 0
        role = db.get_role_by_id(role_id)
        assert role["name"] == "tester"
        db.delete_role(role_id)
        assert db.get_role_by_id(role_id) is None

    def test_set_role_permissions(self, db_path, init_db):
        from chem_agent.auth import database as db
        role_id = db.create_role("perm_test", "权限测试")
        perms = db.list_all_permissions()
        perm_ids = [p["id"] for p in perms[:2]]
        db.set_role_permissions(role_id, perm_ids)
        role_perms = db.get_role_permissions(role_id)
        assert len(role_perms) == 2


class TestCategoryCRUD:
    def test_list_categories(self, db_path, init_db):
        from chem_agent.auth import database as db
        cats = db.list_categories()
        assert len(cats) > 0

    def test_list_by_type(self, db_path, init_db):
        from chem_agent.auth import database as db
        product_cats = db.list_categories("product")
        assert len(product_cats) >= 11

    def test_create_update_delete_category(self, db_path, init_db):
        from chem_agent.auth import database as db
        cat_id = db.create_category("test_type", "test_code", "测试", "Test")
        assert cat_id > 0
        db.update_category(cat_id, display_zh="已更新")
        cats = db.list_categories("test_type")
        assert cats[0]["display_zh"] == "已更新"
        db.delete_category(cat_id)
        cats = db.list_categories("test_type")
        assert len(cats) == 0


class TestConfigAndAudit:
    def test_set_and_get_config(self, db_path, init_db):
        from chem_agent.auth import database as db
        db.set_config("test_key", "test_value", "test desc")
        val = db.get_config("test_key")
        assert val == "test_value"

    def test_audit_log(self, db_path, init_db):
        from chem_agent.auth import database as db
        db.log_audit("test_action", user_id=1, username="admin", resource_type="formula")
        logs, total = db.query_audit_logs(action="test_action")
        assert total >= 1
        assert logs[0]["action"] == "test_action"


class TestFormulaVersions:
    def test_save_and_get_versions(self, db_path, init_db):
        from chem_agent.auth import database as db
        v1 = db.save_formula_version("F-001", {"name": "v1", "items": ["A", "B"]}, change_summary="初始版本")
        v2 = db.save_formula_version("F-001", {"name": "v2", "items": ["A", "C"]}, change_summary="替换B为C")
        assert v1 == 1
        assert v2 == 2

        versions = db.get_formula_versions("F-001")
        assert len(versions) == 2
        assert versions[0]["version_number"] == 2  # latest first

        latest = db.get_latest_formula_version("F-001")
        assert latest["version_number"] == 2

        snap = db.get_formula_version("F-001", 1)
        assert snap["version_number"] == 1

    def test_no_versions(self, db_path, init_db):
        from chem_agent.auth import database as db
        versions = db.get_formula_versions("NONEXIST")
        assert versions == []

        latest = db.get_latest_formula_version("NONEXIST")
        assert latest is None
