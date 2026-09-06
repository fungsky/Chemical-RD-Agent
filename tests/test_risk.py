"""风险评估模块测试。"""
import pytest
from chem_agent.models.formula import (
    Formula, FormulaItem, RawMaterial, SafetyData, HazardClass, MaterialFunction
)
from chem_agent.risk.analyzer import (
    RiskLevel, RiskRequest, RiskResult, RiskItem, analyze_formula_risks,
)


def _make_formula(name="Test", items=None):
    return Formula(name=name, items=items or [], category="涂料")


def _make_item(name, weight, hazards=None, flash_point=None, storage_max=None):
    mat = RawMaterial(
        name=name,
        function=MaterialFunction.OTHER,
        safety=SafetyData(
            hazard_class=hazards or [],
            flash_point_c=flash_point,
            storage_temp_max_c=storage_max,
        ),
    )
    return FormulaItem(material=mat, weight_percent=weight)


class TestRiskModels:
    def test_risk_level_enum(self):
        assert RiskLevel.CRITICAL.value == "critical"
        assert RiskLevel.LOW.value == "low"

    def test_risk_request(self):
        f = _make_formula()
        req = RiskRequest(formula=f, batch_size_kg=10)
        assert req.batch_size_kg == 10


class TestRiskAnalysis:
    def test_safe_formula(self):
        f = _make_formula(items=[
            _make_item("水", 50),
            _make_item("树脂A", 50, hazards=[]),
        ])
        result = analyze_formula_risks(RiskRequest(formula=f))
        assert result.overall_level == RiskLevel.NEGLIGIBLE
        assert result.attention_required is False

    def test_flammable_material(self):
        f = _make_formula(items=[
            _make_item("乙醇", 60, hazards=[HazardClass.FLAMMABLE], flash_point=13),
            _make_item("水", 40),
        ])
        result = analyze_formula_risks(RiskRequest(
            formula=f, process_temperature_c=50,
        ))
        assert result.attention_required is True
        assert result.overall_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)

    def test_toxic_high_ratio(self):
        f = _make_formula(items=[
            _make_item("甲苯", 40, hazards=[HazardClass.TOXIC]),
            _make_item("水", 60),
        ])
        result = analyze_formula_risks(RiskRequest(formula=f))
        assert any(it.risk_type == "high_toxic_ratio" for it in result.items)

    def test_explosive_material(self):
        f = _make_formula(items=[
            _make_item("过氧化物", 5, hazards=[HazardClass.EXPLOSIVE]),
            _make_item("水", 95),
        ])
        result = analyze_formula_risks(RiskRequest(formula=f))
        assert result.overall_level == RiskLevel.CRITICAL

    def test_scale_up_warning(self):
        f = _make_formula(items=[
            _make_item("甲苯", 30, hazards=[HazardClass.TOXIC]),
            _make_item("水", 70),
        ])
        result = analyze_formula_risks(RiskRequest(formula=f, batch_size_kg=500))
        assert any(it.risk_type == "scale_up" for it in result.items)

    def test_storage_temp_exceeded(self):
        f = _make_formula(items=[
            _make_item("物料X", 50, storage_max=40),
            _make_item("水", 50),
        ])
        result = analyze_formula_risks(RiskRequest(
            formula=f, process_temperature_c=80,
        ))
        assert any(it.risk_type == "storage_temperature" for it in result.items)

    def test_no_hazards(self):
        f = _make_formula(items=[
            _make_item("填料", 100),
        ])
        result = analyze_formula_risks(RiskRequest(formula=f))
        assert result.overall_level == RiskLevel.NEGLIGIBLE
        assert result.summary == "未识别到显著安全风险"


print("test_risk done")
