"""测试 - 配方模型验证 & 安全数据"""

import pytest
from pydantic import ValidationError

from chem_agent.models import (
    Formula, FormulaItem, RawMaterial, SafetyData, HazardClass,
    MaterialFunction, ProductCategory, ProcessCondition, PerformanceTest,
)


def make_material(name="test", func=MaterialFunction.OTHER):
    return RawMaterial(name=name, function=func)


class TestWeightValidation:
    def test_weight_too_low_raises(self):
        item = FormulaItem(material=make_material(), weight_percent=80.0)
        with pytest.raises(ValidationError, match="低于95"):
            Formula(name="Bad", code="B-001", category=ProductCategory.COATING, items=[item])

    def test_weight_too_high_raises(self):
        items = [
            FormulaItem(material=make_material("A"), weight_percent=60.0),
            FormulaItem(material=make_material("B"), weight_percent=60.0),
        ]
        with pytest.raises(ValidationError, match="超过105"):
            Formula(name="Bad", code="B-002", category=ProductCategory.COATING, items=items)

    def test_weight_in_range_passes(self):
        items = [
            FormulaItem(material=make_material("A"), weight_percent=50.0),
            FormulaItem(material=make_material("B"), weight_percent=50.0),
        ]
        f = Formula(name="Good", code="G-001", category=ProductCategory.COATING, items=items)
        assert f.name == "Good"

    def test_no_items_passes(self):
        f = Formula(name="Empty", code="E-001", category=ProductCategory.OTHER, items=[])
        assert len(f.items) == 0

    def test_weight_percent_boundary(self):
        # 95% 恰好过线
        items = [FormulaItem(material=make_material("X"), weight_percent=95.0)]
        f = Formula(name="Boundary", code="B-001", category=ProductCategory.OTHER, items=items)
        assert f.name == "Boundary"

    def test_weight_percent_individual_bounds(self):
        with pytest.raises(ValidationError):
            FormulaItem(material=make_material(), weight_percent=-1)
        with pytest.raises(ValidationError):
            FormulaItem(material=make_material(), weight_percent=150)


class TestSafetyData:
    def test_empty_safety(self):
        sd = SafetyData()
        assert sd.hazard_class == []
        assert sd.flash_point_c is None

    def test_full_safety(self):
        sd = SafetyData(
            hazard_class=[HazardClass.FLAMMABLE, HazardClass.TOXIC],
            hazard_statement="H225-H301",
            precaution="P210-P264",
            flash_point_c=25.0,
            explosive_limit_lower=1.0,
            explosive_limit_upper=7.0,
            ld50_oral_mgkg=4300.0,
            storage_temp_min_c=5.0,
            storage_temp_max_c=35.0,
            storage_condition="避光、通风、远离火源",
            incompatible_materials=["强氧化剂", "强酸"],
            personal_protection="防护手套、护目镜、防毒面具",
            emergency_response="用干砂或泡沫灭火，避免用水",
            regulatory_notes="符合 ROHS 2.0 要求",
        )
        assert len(sd.hazard_class) == 2
        assert sd.flash_point_c == 25.0
        assert "强氧化剂" in sd.incompatible_materials

    def test_material_with_safety(self):
        sd = SafetyData(
            hazard_class=[HazardClass.FLAMMABLE],
            flash_point_c=25.0,
            storage_condition="远离火源",
        )
        mat = RawMaterial(
            name="二甲苯",
            function=MaterialFunction.SOLVENT,
            safety=sd,
            safety_info="易燃液体",
        )
        assert mat.safety.flash_point_c == 25.0
        assert mat.safety_info == "易燃液体"


class TestProcessAndPerformance:
    def test_process_condition(self):
        proc = ProcessCondition(
            mixing_speed=1200, mixing_time=45, temperature=25,
            curing_temperature=80, curing_time=2,
        )
        assert proc.mixing_speed == 1200
        assert proc.curing_temperature == 80

    def test_performance_test_qualified(self):
        pt = PerformanceTest(
            test_name="铅笔硬度", value=3, unit="H",
            target_min=2, is_qualified=True,
        )
        assert pt.is_qualified


class TestFullFormula:
    def test_complete_formula(self):
        sd = SafetyData(hazard_class=[HazardClass.FLAMMABLE], flash_point_c=25.0)
        items = [
            FormulaItem(
                material=RawMaterial(
                    name="环氧树脂E-51", function=MaterialFunction.BASE_RESIN,
                    safety=sd,
                ),
                weight_percent=50.0, addition_order=1,
            ),
            FormulaItem(
                material=RawMaterial(name="聚酰胺650", function=MaterialFunction.CURING_AGENT),
                weight_percent=50.0, addition_order=2,
            ),
        ]
        proc = ProcessCondition(mixing_speed=600, curing_temperature=80, curing_time=2)
        perf = [PerformanceTest(test_name="拉伸剪切强度", value=22.5, unit="MPa", target_min=18, is_qualified=True)]

        f = Formula(
            name="环氧结构胶 EA-001", code="EA-001", version="1.2",
            status="approved", category=ProductCategory.ADHESIVE,
            description="高强度结构胶", items=items, process=proc,
            performance=perf, target_application="金属粘接",
            creator="赵工", tags=["环氧", "结构胶"],
        )

        assert f.code == "EA-001"
        assert sum(i.weight_percent for i in f.items) == 100.0
        assert f.items[0].material.safety.flash_point_c == 25.0
        assert f.performance[0].is_qualified
