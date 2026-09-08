"""配方快照去重比较测试。"""

import json

from chem_agent.api.main import _snapshot_semantic_equal


def _snap(name="涂料A", weight=26.0, created="2026-01-01T00:00:00"):
    return {
        "id": "f1",
        "code": "F-001",
        "name": name,
        "category": "涂料",
        "created_at": created,
        "updated_at": None,
        "items": [
            {
                "material": {"name": "环氧树脂E-51", "function": "基础树脂"},
                "weight_percent": weight,
            }
        ],
    }


def test_runtime_fields_ignored():
    assert _snapshot_semantic_equal(
        _snap(created="2026-01-01T00:00:00"),
        json.dumps(_snap(created="2026-09-01T00:00:00"), ensure_ascii=False),
    )


def test_content_change_is_not_equal():
    assert not _snapshot_semantic_equal(_snap(weight=26.0), _snap(weight=28.0))


def test_none_handling():
    assert _snapshot_semantic_equal(None, None)
    assert not _snapshot_semantic_equal(None, _snap())
