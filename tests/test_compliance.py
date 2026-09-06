"""合规检查模块测试。"""
import pytest
from chem_agent.models.formula import (
    Formula, FormulaItem, RawMaterial, MaterialFunction
)
from chem_agent.compliance.rules import (
    RegulationDomain, Violation, ComplianceRequest, ComplianceResult, check_compliance,
)


def _make_formula(name="Test", items=None):
    return Formula(name=name, items=items or [], category="涂料")


def _make_item(name, weight, cas=None):
    mat = RawMaterial(name=name, function=MaterialFunction.OTHER, cas_number=cas)
    return FormulaItem(material=mat, weight_percent=weight)


class TestComplianceModels:
    def test_regulation_domains(self):
        assert RegulationDomain.FOOD_CONTACT.value == "food_contact"
        assert RegulationDomain.ELECTRONICS.value == "electronics"

    def test_compliance_request(self):
        f = _make_formula()
        req = ComplianceRequest(formula=f, domains=[RegulationDomain.TOYS])
        assert len(req.domains) == 1


class TestComplianceCheck:
    def test_no_violation(self):
        f = _make_formula(items=[
            _make_item("聚丙烯", 100),
        ])
        result = check_compliance(ComplianceRequest(
            formula=f, domains=[RegulationDomain.FOOD_CONTACT],
        ))
        assert result.passed is True
        assert len(result.violations) == 0

    def test_lead_in_food_contact(self):
        f = _make_formula(items=[
            _make_item("铅铬黄颜料", 0.5, cas="7758-97-6"),
            _make_item("水", 99.5),
        ])
        result = check_compliance(ComplianceRequest(
            formula=f, domains=[RegulationDomain.FOOD_CONTACT],
        ))
        violations = [v for v in result.violations if v.severity == "error"]
        assert len(violations) > 0

    def test_lead_under_limit_ok(self):
        f = _make_formula(items=[
            _make_item("铅化合物", 0.005),
            _make_item("水", 99.995),
        ])
        result = check_compliance(ComplianceRequest(
            formula=f, domains=[RegulationDomain.FOOD_CONTACT],
        ))
        errors = [v for v in result.violations if v.severity == "error"]
        assert len(errors) == 0

    def test_formaldehyde_toys(self):
        f = _make_formula(items=[
            _make_item("甲醛溶液", 2),
            _make_item("水", 98),
        ])
        result = check_compliance(ComplianceRequest(
            formula=f, domains=[RegulationDomain.TOYS],
        ))
        assert any(v.severity == "error" for v in result.violations)

    def test_rohs_electronics(self):
        f = _make_formula(items=[
            _make_item("铅焊料", 0.5),
            _make_item("镉镀层", 0.05),
            _make_item("水", 99.45),
        ])
        result = check_compliance(ComplianceRequest(
            formula=f, domains=[RegulationDomain.ELECTRONICS],
        ))
        errors = [v for v in result.violations if v.severity == "error"]
        assert len(errors) >= 1

    def test_multiple_domains(self):
        f = _make_formula(items=[
            _make_item("铅铬黄", 0.2),
            _make_item("水", 99.8),
        ])
        result = check_compliance(ComplianceRequest(
            formula=f,
            domains=[RegulationDomain.FOOD_CONTACT, RegulationDomain.TOYS, RegulationDomain.ELECTRONICS],
        ))
        assert len(result.domains_checked) == 3

    def test_cosmetics_compliance(self):
        f = _make_formula(items=[
            _make_item("铅化合物", 0.002),  # 0.002% > 0.001% limit
            _make_item("水", 99.998),
        ])
        result = check_compliance(ComplianceRequest(
            formula=f, domains=[RegulationDomain.COSMETICS],
        ))
        assert any(v.severity == "error" for v in result.violations)

    def test_formaldehyde_under_limit(self):
        f = _make_formula(items=[
            _make_item("甲醛", 0.05),
            _make_item("水", 99.95),
        ])
        result = check_compliance(ComplianceRequest(
            formula=f, domains=[RegulationDomain.FOOD_CONTACT],
        ))
        errors = [v for v in result.violations if v.severity == "error"]
        assert len(errors) == 0

    def test_phthalates_in_toys(self):
        f = _make_formula(items=[
            _make_item("邻苯二甲酸二辛酯", 0.5),
            _make_item("水", 99.5),
        ])
        result = check_compliance(ComplianceRequest(
            formula=f, domains=[RegulationDomain.TOYS],
        ))
        assert any(v.severity == "error" for v in result.violations)

    def test_gb_rohs_electronics(self):
        """国标 RoHS: GB/T 26572-2011 铅限量。"""
        f = _make_formula(items=[
            _make_item("铅焊料", 0.5),
            _make_item("水", 99.5),
        ])
        result = check_compliance(ComplianceRequest(
            formula=f, domains=[RegulationDomain.ELECTRONICS],
        ))
        gb = [v for v in result.violations if v.rule_name == "GB/T 26572-2011"]
        assert any(v.severity == "error" for v in gb)

    def test_gb_6675_toys_lead(self):
        """国标玩具: GB 6675.4-2014 铅迁移限量。"""
        f = _make_formula(items=[
            _make_item("铅铬黄颜料", 0.5, cas="7758-97-6"),
            _make_item("水", 99.5),
        ])
        result = check_compliance(ComplianceRequest(
            formula=f, domains=[RegulationDomain.TOYS],
        ))
        gb = [v for v in result.violations if v.rule_name == "GB 6675.4-2014"]
        assert any(v.severity == "error" for v in gb)

    def test_gb_18401_textile_formaldehyde(self):
        """国标纺织品: GB 18401-2010 甲醛限量。"""
        f = _make_formula(items=[
            _make_item("甲醛树脂", 0.5),
            _make_item("水", 99.5),
        ])
        result = check_compliance(ComplianceRequest(
            formula=f, domains=[RegulationDomain.TEXTILE],
        ))
        assert result.domains_checked == [RegulationDomain.TEXTILE]
        assert any(v.severity == "error" for v in result.violations)

    def test_cosmetics_banned_hydroquinone(self):
        """化妆品禁用成分: 氢醌。"""
        f = _make_formula(items=[
            _make_item("氢醌", 1.0),
            _make_item("水", 99.0),
        ])
        result = check_compliance(ComplianceRequest(
            formula=f, domains=[RegulationDomain.COSMETICS],
        ))
        assert any(v.material_name == "氢醌" and v.severity == "error" for v in result.violations)

    def test_cosmetics_methanol_limit(self):
        """化妆品限用: 甲醇≤0.2%。"""
        f = _make_formula(items=[
            _make_item("甲醇", 0.5),
            _make_item("水", 99.5),
        ])
        result = check_compliance(ComplianceRequest(
            formula=f, domains=[RegulationDomain.COSMETICS],
        ))
        assert any(v.material_name == "甲醇" and v.severity == "error" for v in result.violations)

    def test_toothpaste_fluoride_limit(self):
        """牙膏氟化物: GB/T 8372-2017 限量。"""
        f = _make_formula(items=[
            _make_item("氟化钠", 0.2),
            _make_item("水", 99.8),
        ])
        result = check_compliance(ComplianceRequest(
            formula=f, domains=[RegulationDomain.COSMETICS],
        ))
        gb = [v for v in result.violations if v.rule_name == "GB/T 8372-2017"]
        assert any(v.severity in ("warning", "error") for v in gb)

    def test_textile_domain_enum(self):
        """纺织品领域枚举。"""
        assert RegulationDomain.TEXTILE.value == "textile"


print("test_compliance done")
