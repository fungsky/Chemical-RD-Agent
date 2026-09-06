"""测试 - 数据模型"""

import pytest
from datetime import datetime

from chem_agent.models import (
    RawMaterial,
    FormulaItem,
    Formula,
    PerformanceTest,
    ProcessCondition,
    PredictionRequest,
    PredictionResult,
    ProductCategory,
    MaterialFunction,
)


class TestRawMaterial:
    def test_create_basic(self):
        mat = RawMaterial(name="环氧树脂E-51", function=MaterialFunction.BASE_RESIN)
        assert mat.name == "环氧树脂E-51"
        assert mat.function == MaterialFunction.BASE_RESIN

    def test_create_full(self):
        mat = RawMaterial(
            name="二氧化钛R-706",
            cas_number="13463-67-7",
            chemical_name="金红石型二氧化钛",
            supplier="科慕",
            function=MaterialFunction.PIGMENT,
            properties={"density": 4.2},
            safety_info="无毒",
        )
        assert mat.cas_number == "13463-67-7"
        assert mat.properties["density"] == 4.2


class TestFormula:
    def test_create_formula(self):
        mat = RawMaterial(name="环氧树脂E-51", function=MaterialFunction.BASE_RESIN)
        item = FormulaItem(material=mat, weight_percent=100.0, addition_order=1)
        perf = PerformanceTest(
            test_name="铅笔硬度", value=3, unit="H", is_qualified=True
        )
        formula = Formula(
            name="测试配方",
            code="TEST-001",
            category=ProductCategory.COATING,
            items=[item],
            performance=[perf],
        )
        assert formula.name == "测试配方"
        assert len(formula.items) == 1
        assert formula.items[0].weight_percent == 100.0
        assert len(formula.performance) == 1

    def test_formula_weight_validation(self):
        mat = RawMaterial(name="test", function=MaterialFunction.OTHER)
        with pytest.raises(Exception):
            FormulaItem(material=mat, weight_percent=150.0)

    def test_process_condition(self):
        process = ProcessCondition(
            mixing_speed=1200,
            mixing_time=30,
            temperature=25,
            curing_temperature=80,
            curing_time=2,
        )
        assert process.mixing_speed == 1200
        assert process.curing_time == 2


class TestPrediction:
    def test_prediction_result(self):
        result = PredictionResult(
            property_name="硬度",
            predicted_value=85.0,
            unit="HV",
            confidence=0.85,
            explanation="基于100棵树预测",
        )
        assert result.confidence == 0.85

    def test_prediction_request(self):
        mat = RawMaterial(name="test", function=MaterialFunction.BASE_RESIN)
        item = FormulaItem(material=mat, weight_percent=50.0)
        req = PredictionRequest(
            items=[item],
            category=ProductCategory.COATING,
            target_properties=["硬度", "光泽度"],
        )
        assert len(req.target_properties) == 2
