"""桌面 API 客户端契约测试。"""

import desktop.api_client as api


def test_search_formulas_flattens_backend_result(monkeypatch):
    payload = [
        {
            "formula": {
                "code": "HF-001",
                "name": "高防腐环氧底漆",
                "category": "涂料",
                "items": [
                    {"material": {"name": "环氧树脂E-51"}, "weight_percent": 26.0},
                    {"material": {"name": "二甲苯"}, "weight_percent": 16.0},
                ],
            },
            "similarity_score": 0.9,
        }
    ]
    monkeypatch.setattr(api, "_get", lambda *a, **k: payload)

    rows = api.search_formulas("环氧")

    assert len(rows) == 1
    assert rows[0]["code"] == "HF-001"
    assert rows[0]["name"] == "高防腐环氧底漆"
    assert rows[0]["category"] == "涂料"
    assert "环氧树脂E-51" in rows[0]["components"]
    assert rows[0]["similarity"] == 0.9


def test_search_formulas_returns_empty_on_no_result(monkeypatch):
    monkeypatch.setattr(api, "_get", lambda *a, **k: None)
    assert api.search_formulas() == []


def test_chat_uses_use_agent_field(monkeypatch):
    captured = {}
    monkeypatch.setattr(api, "_post", lambda url, data: captured.update(url=url, data=data))
    api.chat("测试消息", agent_mode=True)
    assert captured["url"] == "/api/chat"
    assert captured["data"]["use_agent"] is True
    assert "agent_mode" not in captured["data"]


def test_material_calls_target_kg_api(monkeypatch):
    calls = {}
    monkeypatch.setattr(api, "_post", lambda url, data: calls.update(post=(url, data)))
    monkeypatch.setattr(api, "_get", lambda url, params=None: calls.update(get=(url, params)))

    api.mat_add({"name": "测试料"})
    assert calls["post"][0] == "/api/materials"

    api.mat_get("测试料")
    assert calls["get"][0] == "/api/materials/测试料/detail"

    api.mat_list()
    assert calls["get"][0] == "/api/materials"
    assert calls["get"][1] == {"keyword": "", "limit": 100}

    api.mat_categories()
    assert calls["get"][0] == "/api/materials/categories"
