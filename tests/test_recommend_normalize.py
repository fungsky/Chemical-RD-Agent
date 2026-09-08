"""AI 推荐配方规整测试。"""

from chem_agent.llm.llm_service import _normalize_recommended_formula


def test_normalize_recommended_formula():
    raw = {
        "name": "水性外墙漆",
        "category": "涂料",
        "items": [
            {"material": {"name": "丙烯酸树脂", "function": "基础树脂"}, "weight_percent": "45"},
            {"material": {"name": "钛白粉", "function": "颜料"}, "weight_percent": "20"},
            {"material": {"name": "消泡剂", "function": "助剂"}, "weight_percent": "35"},
        ],
        "process": {"mixing_speed": "低速", "temperature": 30},
        "performance": [
            {"metric": "附着力", "value": "≤1级"},
            {"test_name": "耐候性", "value": "≥500h"},
        ],
    }
    out = _normalize_recommended_formula(raw)

    assert out is not None
    assert out["items"][2]["material"]["function"] == "其他"
    assert out["process"]["mixing_speed"] is None
    assert out["process"]["temperature"] == 30
    assert out["performance"][0]["value"] == 1
    assert out["performance"][1]["value"] == 500
    assert 95 <= sum(i["weight_percent"] for i in out["items"]) <= 105
