"""配方风险评估引擎 -- 基于SDS数据和工艺条件识别安全风险。"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from chem_agent.models.formula import Formula, FormulaItem, HazardClass


class RiskLevel(str, Enum):
    NEGLIGIBLE = "negligible"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class RiskItem(BaseModel):
    risk_type: str = Field(..., description="风险类别")
    description: str = Field(..., description="风险描述")
    level: RiskLevel = Field(..., description="风险等级")
    related_material: Optional[str] = Field(None, description="关联物料")
    mitigation: str = Field("", description="缓解措施建议")


class RiskRequest(BaseModel):
    formula: Formula
    batch_size_kg: float = Field(1.0, ge=0.1, description="批次规模(kg)")
    process_temperature_c: Optional[float] = Field(None, description="工艺最高温度(℃)")


class RiskResult(BaseModel):
    formula_name: str
    overall_level: RiskLevel = RiskLevel.NEGLIGIBLE
    items: list[RiskItem] = Field(default_factory=list)
    summary: str = ""
    attention_required: bool = False


# 严重性映射
_HAZARD_SEVERITY = {
    HazardClass.EXPLOSIVE: RiskLevel.CRITICAL,
    HazardClass.TOXIC: RiskLevel.HIGH,
    HazardClass.FLAMMABLE: RiskLevel.HIGH,
    HazardClass.CORROSIVE: RiskLevel.MODERATE,
    HazardClass.OXIDIZING: RiskLevel.MODERATE,
    HazardClass.IRRITANT: RiskLevel.LOW,
    HazardClass.ENVIRONMENTAL: RiskLevel.LOW,
    HazardClass.COMPRESSED_GAS: RiskLevel.MODERATE,
    HazardClass.NONE: RiskLevel.NEGLIGIBLE,
}

# 不相容物质组合 (简化版)
_INCOMPATIBLE_PAIRS = [
    ({"酸", "酸性"}, {"碱", "碱性", "胺", "氨"}),
    ({"氧化剂", "过氧化物"}, {"还原剂", "有机溶剂", "醇"}),
    ({"水"}, {"异氰酸酯", "金属钠", "钾"}),
    ({"强酸", "浓硫酸", "浓硝酸"}, {"有机物", "醇", "酮"}),
]


def _hazard_level(hazards: list[HazardClass]) -> RiskLevel:
    if not hazards:
        return RiskLevel.NEGLIGIBLE
    levels = [_HAZARD_SEVERITY.get(h, RiskLevel.LOW) for h in hazards]
    order = [RiskLevel.NEGLIGIBLE, RiskLevel.LOW, RiskLevel.MODERATE, RiskLevel.HIGH, RiskLevel.CRITICAL]
    return max(levels, key=lambda l: order.index(l))


def _check_incompatibility(items: list[FormulaItem]) -> list[RiskItem]:
    risks = []
    for i, item_a in enumerate(items):
        name_a = item_a.material.name
        func_a = item_a.material.function.value if item_a.material.function else ""
        for j, item_b in enumerate(items):
            if j <= i:
                continue
            name_b = item_b.material.name
            func_b = item_b.material.function.value if item_b.material.function else ""
            for set_a, set_b in _INCOMPATIBLE_PAIRS:
                match_a = any(t in name_a or t in func_a for t in set_a)
                match_b = any(t in name_b or t in func_b for t in set_b)
                if match_a and match_b:
                    risks.append(RiskItem(
                        risk_type="incompatible_materials",
                        description=f"{name_a} 与 {name_b} 可能存在不相容风险",
                        level=RiskLevel.HIGH,
                        related_material=f"{name_a}, {name_b}",
                        mitigation=f"确认 {name_a} 和 {name_b} 的相容性，必要时调整加料顺序或隔离储存",
                    ))
    return risks


def analyze_formula_risks(req: RiskRequest) -> RiskResult:
    """分析配方的综合安全风险。"""
    items: list[RiskItem] = []
    formula = req.formula

    # 1. 单物料危害分析
    for item in formula.items:
        safety = item.material.safety
        if safety:
            # 有害物质识别（含 MODERATE 级别）
            if safety.hazard_class:
                haz_level = _hazard_level(safety.hazard_class)
                if haz_level in (RiskLevel.MODERATE, RiskLevel.HIGH, RiskLevel.CRITICAL):
                    items.append(RiskItem(
                        risk_type="material_hazard",
                        description=f"物料 {item.material.name} 存在 {', '.join(h.value for h in safety.hazard_class)} 危险",
                        level=haz_level,
                        related_material=item.material.name,
                        mitigation=f"加强通风和个人防护(PPE)，控制 {item.material.name} 使用量",
                    ))
            # 闪点检查（独立于 hazard_class）
            if safety.flash_point_c is not None and req.process_temperature_c:
                if req.process_temperature_c > safety.flash_point_c - 10:
                    items.append(RiskItem(
                        risk_type="flash_point",
                        description=f"工艺温度({req.process_temperature_c}℃)接近 {item.material.name} 闪点({safety.flash_point_c}℃)",
                        level=RiskLevel.CRITICAL,
                        related_material=item.material.name,
                        mitigation="降低工艺温度或增加惰性气体保护",
                    ))
            # 储存温度（独立于 hazard_class）
            if safety.storage_temp_max_c and req.process_temperature_c:
                if req.process_temperature_c > safety.storage_temp_max_c:
                    items.append(RiskItem(
                        risk_type="storage_temperature",
                        description=f"工艺温度({req.process_temperature_c}℃)超过 {item.material.name} 储存上限({safety.storage_temp_max_c}℃)",
                        level=RiskLevel.HIGH,
                        related_material=item.material.name,
                        mitigation="缩短高温停留时间或改用耐热容器",
                    ))

    # 2. 不相容检查
    items.extend(_check_incompatibility(formula.items))

    # 3. 高比例危险品
    for item in formula.items:
        safety = item.material.safety
        if safety and safety.hazard_class:
            if HazardClass.TOXIC in safety.hazard_class and item.weight_percent > 30:
                items.append(RiskItem(
                    risk_type="high_toxic_ratio",
                    description=f"有毒物料 {item.material.name} 占比 {item.weight_percent}%，超过30%",
                    level=RiskLevel.HIGH,
                    related_material=item.material.name,
                    mitigation="评估是否可降低用量或使用低毒替代品",
                ))
            if HazardClass.FLAMMABLE in safety.hazard_class and item.weight_percent > 50:
                items.append(RiskItem(
                    risk_type="high_flammable_ratio",
                    description=f"易燃物料 {item.material.name} 占比 {item.weight_percent}%，超过50%",
                    level=RiskLevel.MODERATE,
                    related_material=item.material.name,
                    mitigation="确保防爆设备和静电接地",
                ))

    # 4. 批次规模放大风险
    if req.batch_size_kg > 100:
        has_hazard = any(
            it.material.safety and it.material.safety.hazard_class
            and any(h in (HazardClass.EXPLOSIVE, HazardClass.TOXIC, HazardClass.FLAMMABLE)
                    for h in it.material.safety.hazard_class)
            for it in formula.items
        )
        if has_hazard:
            items.append(RiskItem(
                risk_type="scale_up",
                description=f"批次规模 {req.batch_size_kg}kg 超过100kg，且含危险物料，放大风险需评估",
                level=RiskLevel.MODERATE,
                mitigation="建议先进行小试/中试验证，逐步放大",
            ))

    # 汇总
    if not items:
        return RiskResult(
            formula_name=formula.name,
            overall_level=RiskLevel.NEGLIGIBLE,
            summary="未识别到显著安全风险",
            attention_required=False,
        )

    order = [RiskLevel.NEGLIGIBLE, RiskLevel.LOW, RiskLevel.MODERATE, RiskLevel.HIGH, RiskLevel.CRITICAL]
    overall = max(items, key=lambda it: order.index(it.level)).level
    critical_count = sum(1 for it in items if it.level == RiskLevel.CRITICAL)
    high_count = sum(1 for it in items if it.level == RiskLevel.HIGH)

    return RiskResult(
        formula_name=formula.name,
        overall_level=overall,
        items=items,
        summary=f"共识别 {len(items)} 个风险项（严重:{critical_count}, 高:{high_count}）",
        attention_required=overall in (RiskLevel.HIGH, RiskLevel.CRITICAL),
    )
