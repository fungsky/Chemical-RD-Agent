"""风险 API 测试（auth_bypass 模式）。"""

import os

os.environ.setdefault("CHEM_AUTH_BYPASS", "true")

from fastapi import FastAPI
from fastapi.testclient import TestClient

from chem_agent.api.risk_router import router
from chem_agent.models import Formula, FormulaItem, ProductCategory, RawMaterial


def _client() -> TestClient:
    from chem_agent.config import settings
    settings.auth_bypass = True
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_analyze_simple_formula_ok():
    resp = _client().post(
        "/api/risk/analyze",
        json={
            "formula": {
                "name": "无危害测试配方",
                "code": "RISK-OK-1",
                "category": ProductCategory.OTHER.value,
                "items": [
                    {
                        "material": {"name": "水", "function": "其他"},
                        "weight_percent": 100.0,
                    }
                ],
            },
            "batch_size_kg": 1.0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "overall_level" in data
    assert "attention_required" in data


def test_risk_methods_ok():
    resp = _client().get("/api/risk/methods")
    assert resp.status_code == 200
    data = resp.json()
    assert "levels" in data
    assert "risk_types" in data


def test_risk_request_model():
    item = FormulaItem(
        material=RawMaterial(name="水", function="其他"),
        weight_percent=100.0,
    )
    formula = Formula(
        name="模型测试",
        code="RISK-MODEL-1",
        category=ProductCategory.OTHER,
        items=[item],
    )
    from chem_agent.risk.analyzer import RiskRequest, analyze_formula_risks

    result = analyze_formula_risks(RiskRequest(formula=formula))
    assert result.attention_required is False
