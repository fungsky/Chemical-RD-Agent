"""测试 - 化学语义版本差异对比"""

import pytest
import json

# Import the diff function directly (it's a pure function, no deps)
from chem_agent.api.formula_version_router import _compute_diff


def make_snap(items=None, process=None, performance=None, name=None, category=None):
    return {
        "name": name or "Test Formula",
        "category": category or "Coating",
        "items": items or [],
        "process": process or {},
        "performance": performance or [],
    }


class TestChemicalDiff:
    def test_no_changes(self):
        snap = make_snap(
            items=[{"material": {"name": "A", "function": "resin"}, "weight_percent": 50.0}],
            process={"temperature": 25},
            performance=[{"test_name": "hardness", "value": 85}],
        )
        result = _compute_diff(snap, snap)
        assert result["summary"] == "无显著变化"
        assert len(result["material_changes"]) == 0
        assert len(result["process_changes"]) == 0

    def test_material_added(self):
        v1 = make_snap(items=[
            {"material": {"name": "A", "function": "resin"}, "weight_percent": 50.0},
        ])
        v2 = make_snap(items=[
            {"material": {"name": "A", "function": "resin"}, "weight_percent": 50.0},
            {"material": {"name": "B", "function": "filler"}, "weight_percent": 30.0},
        ])
        result = _compute_diff(v1, v2)
        added = [c for c in result["material_changes"] if c["type"] == "added"]
        assert len(added) == 1
        assert added[0]["material"] == "B"

    def test_material_removed(self):
        v1 = make_snap(items=[
            {"material": {"name": "A", "function": "resin"}, "weight_percent": 50.0},
            {"material": {"name": "B", "function": "filler"}, "weight_percent": 30.0},
        ])
        v2 = make_snap(items=[
            {"material": {"name": "A", "function": "resin"}, "weight_percent": 50.0},
        ])
        result = _compute_diff(v1, v2)
        removed = [c for c in result["material_changes"] if c["type"] == "removed"]
        assert len(removed) == 1
        assert removed[0]["material"] == "B"

    def test_weight_shift_detected(self):
        v1 = make_snap(items=[
            {"material": {"name": "A", "function": "resin"}, "weight_percent": 30.0},
        ])
        v2 = make_snap(items=[
            {"material": {"name": "A", "function": "resin"}, "weight_percent": 35.0},
        ])
        result = _compute_diff(v1, v2)
        modified = [c for c in result["material_changes"] if c["type"] == "modified"]
        assert len(modified) == 1
        assert modified[0]["weight_delta"] == 5.0

    def test_small_weight_shift_ignored(self):
        v1 = make_snap(items=[
            {"material": {"name": "A", "function": "resin"}, "weight_percent": 30.0},
        ])
        v2 = make_snap(items=[
            {"material": {"name": "A", "function": "resin"}, "weight_percent": 31.0},
        ])
        result = _compute_diff(v1, v2)
        modified = [c for c in result["material_changes"] if c["type"] == "modified"]
        assert len(modified) == 0  # 1% < 2% threshold

    def test_process_temperature_change(self):
        v1 = make_snap(process={"temperature": 25})
        v2 = make_snap(process={"temperature": 35})
        result = _compute_diff(v1, v2)
        temp_change = [c for c in result["process_changes"] if c["field"] == "反应温度"]
        assert len(temp_change) == 1
        assert temp_change[0]["delta"] == 10.0
        assert temp_change[0]["direction"] == "increase"

    def test_process_small_change_ignored(self):
        v1 = make_snap(process={"temperature": 25})
        v2 = make_snap(process={"temperature": 27})
        result = _compute_diff(v1, v2)
        temp_change = [c for c in result["process_changes"] if c["field"] == "反应温度"]
        assert len(temp_change) == 0  # 2C < 5C threshold

    def test_performance_improvement(self):
        v1 = make_snap(performance=[{"test_name": "耐盐雾", "value": 800}])
        v2 = make_snap(performance=[{"test_name": "耐盐雾", "value": 1000}])
        result = _compute_diff(v1, v2)
        assert len(result["performance_changes"]) == 1
        assert result["performance_changes"][0]["improved"] is True

    def test_info_change(self):
        v1 = make_snap(name="Old Name")
        v2 = make_snap(name="New Name")
        result = _compute_diff(v1, v2)
        assert len(result["info_changes"]) == 1
        assert result["info_changes"][0]["field"] == "name"

    def test_summary_generation(self):
        v1 = make_snap(
            items=[{"material": {"name": "A", "function": "resin"}, "weight_percent": 50.0}],
            process={"temperature": 25},
        )
        v2 = make_snap(
            items=[
                {"material": {"name": "A", "function": "resin"}, "weight_percent": 45.0},
                {"material": {"name": "B", "function": "filler"}, "weight_percent": 30.0},
            ],
            process={"temperature": 35, "mixing_speed": 1500},
        )
        result = _compute_diff(v1, v2)
        assert "变更" in result["summary"] or "调整" in result["summary"]
        assert len(result["material_changes"]) >= 1
        assert len(result["process_changes"]) >= 1
