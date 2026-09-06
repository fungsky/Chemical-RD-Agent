"""测试 - FastAPI 接口（不依赖外部服务的部分）"""

import pytest
from fastapi.testclient import TestClient

from chem_agent.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoint:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestAuthBypass:
    """本地免登录模式（CHEM_AUTH_BYPASS=true）测试。"""

    def test_protected_endpoint_requires_auth(self, client):
        resp = client.get("/api/admin/llm/config")
        assert resp.status_code == 401

    def test_auth_bypass_allows_no_login(self, client, monkeypatch):
        from chem_agent.config import settings
        monkeypatch.setattr(settings, "auth_bypass", True)
        # get_current_user 直通：未带令牌也不应返回 401
        resp = client.get("/api/graph/stats")
        assert resp.status_code != 401

    def test_auth_bypass_passes_permission_check(self, client, monkeypatch):
        from chem_agent.config import settings
        monkeypatch.setattr(settings, "auth_bypass", True)
        # require_permission 依赖 get_current_user，通配符权限应放行
        resp = client.get("/api/admin/llm/config")
        assert resp.status_code == 200
        assert "provider" in resp.json()
