"""BOM成本核算模块测试。"""
import pytest
from chem_agent.models.formula import (
    Formula, FormulaItem, RawMaterial, MaterialFunction
)
from chem_agent.cost.cost_calculator import (
    CostRequest, CostResult, MaterialCost, CostBreakdown, calculate_formula_cost,
)


def _make_formula(name="Test", items=None):
    return Formula(name=name, items=items or [], category="涂料")


def _make_item(name, weight):
    mat = RawMaterial(name=name, function=MaterialFunction.BASE_RESIN)
    return FormulaItem(material=mat, weight_percent=weight)


class TestCostModels:
    def test_cost_request_defaults(self):
        f = _make_formula()
        req = CostRequest(formula=f)
        assert req.batch_size_kg == 1.0
        assert req.overhead_rate == 0.15

    def test_cost_breakdown(self):
        cb = CostBreakdown(materials_total=100, packaging=10, total=110)
        assert cb.materials_total == 100


class TestCostCalculation:
    def test_simple_cost(self):
        f = _make_formula(items=[
            _make_item("树脂A", 50),
            _make_item("溶剂B", 50),
        ])
        result = calculate_formula_cost(CostRequest(
            formula=f,
            batch_size_kg=100,
            price_map={"树脂A": 20, "溶剂B": 5},
        ))
        # 树脂A: 50kg * 20 = 1000, 溶剂B: 50kg * 5 = 250
        # materials_total = 1250, overhead = 1250 * 0.15 = 187.5
        # total = 1250 + 187.5 = 1437.5
        # unit = 1437.5 / 100 = 14.375 -> 14.38
        assert result.breakdown.materials_total == 1250.0
        assert result.breakdown.overhead == 187.5
        assert result.breakdown.total == 1437.5
        assert result.unit_cost_per_kg == 14.38

    def test_missing_prices(self):
        f = _make_formula(items=[
            _make_item("未知物料", 100),
        ])
        result = calculate_formula_cost(CostRequest(formula=f, price_map={}))
        assert "未知物料" in result.missing_prices
        assert result.breakdown.materials_total == 0

    def test_full_breakdown(self):
        f = _make_formula(items=[
            _make_item("树脂", 100),
        ])
        result = calculate_formula_cost(CostRequest(
            formula=f,
            batch_size_kg=10,
            price_map={"树脂": 30},
            packaging_cost_per_kg=2,
            labor_cost_per_kg=3,
            energy_cost_per_kg=1.5,
        ))
        assert result.breakdown.materials_total == 300
        assert result.breakdown.packaging == 20
        assert result.breakdown.labor == 30
        assert result.breakdown.energy == 15
        assert result.breakdown.overhead == 45  # 300 * 0.15

    def test_item_detail(self):
        f = _make_formula(items=[
            _make_item("树脂", 100),
        ])
        result = calculate_formula_cost(CostRequest(
            formula=f,
            batch_size_kg=10,
            price_map={"树脂": 10},
        ))
        assert len(result.items) == 1
        assert result.items[0].material_name == "树脂"
        assert result.items[0].weight_kg == 10.0
        assert result.items[0].cost == 100.0


print("test_cost done")
