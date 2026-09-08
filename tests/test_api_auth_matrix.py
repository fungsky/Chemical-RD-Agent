"""第二代 router 鉴权回归矩阵：无 token 时一律 401。"""

import pytest
from fastapi.testclient import TestClient

from chem_agent.api.main import app


@pytest.mark.parametrize(
    "method,path",
    [
        ("GET", "/api/doe/methods"),
        ("POST", "/api/doe/generate"),
        ("POST", "/api/cost/calculate"),
        ("GET", "/api/compliance/domains"),
        ("GET", "/api/experiments/stats"),
        ("GET", "/api/formula-versions/TEST-CODE"),
        ("GET", "/api/materials?keyword="),
        ("GET", "/api/optimization/methods"),
        ("POST", "/api/process/spc/analyze"),
        ("GET", "/api/quality/templates/list/all"),
        ("POST", "/api/scaleup/calculate"),
        ("POST", "/api/stability/predict"),
        ("POST", "/api/sustainability/assess"),
        ("GET", "/api/kb/wiki/pages"),
        ("POST", "/api/kb/wiki/compile"),
        ("GET", "/api/risk/methods"),
    ],
)
def test_second_generation_routes_require_auth(method, path):
    client = TestClient(app)
    response = client.request(method, path, json={})
    assert response.status_code == 401
