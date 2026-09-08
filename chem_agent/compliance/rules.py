"""化工配方合规检查引擎 -- 按法规领域检查配方合规性。

规则库覆盖国际法规(EU/EN/ISO/RoHS)与中国标准(GB/GB-T 国标、行标)的常用限量。
注意: 本规则库为研发阶段合规初筛的参考实现，限值以质量占比近似换算；
正式合规判定请以最新正式发布的标准文本及监管要求为准。
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from chem_agent.models.formula import Formula


class RegulationDomain(str, Enum):
    FOOD_CONTACT = "food_contact"
    TOYS = "toys"
    AUTOMOTIVE = "automotive"
    CONSTRUCTION = "construction"
    ELECTRONICS = "electronics"
    MEDICAL = "medical"
    COSMETICS = "cosmetics"
    TEXTILE = "textile"


class Violation(BaseModel):
    material_name: str
    domain: RegulationDomain
    rule_name: str = Field("", description="违反的具体法规条目")
    limit_value: Optional[str] = Field(None, description="法规限值")
    actual_value: Optional[str] = Field(None, description="实际值")
    severity: str = Field("warning", description="严重程度: info/warning/error/critical")


class ComplianceRequest(BaseModel):
    formula: Formula
    domains: list[RegulationDomain] = Field(..., min_length=1)


class ComplianceResult(BaseModel):
    formula_name: str
    domains_checked: list[RegulationDomain]
    passed: bool = True
    violations: list[Violation] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    summary: str = ""


# 法规限制规则库
# 格式: domain -> [ {name_pattern, cas, max_percent, rule_name} ]
_RULES: dict[RegulationDomain, list[dict]] = {
    RegulationDomain.FOOD_CONTACT: [
        {"name_pattern": "邻苯二甲酸", "rule_name": "EU 10/2011", "max_percent": 0.1, "note": "塑化剂总迁移量<10mg/dm\u00b2"},
        {"name_pattern": "双酚A", "rule_name": "EU 10/2011", "cas": "80-05-7", "max_percent": 0.05, "note": "BPA特定迁移限值0.05mg/kg"},
        {"name_pattern": "铅|Pb|铬酸铅|铅铬", "rule_name": "EU 10/2011 Annex II", "max_percent": 0.01, "note": "重金属限值Pb<0.01%"},
        {"name_pattern": "镉|Cd", "rule_name": "EU 10/2011 Annex II", "max_percent": 0.01, "note": "重金属限值Cd<0.01%"},
        {"name_pattern": "汞|Hg", "rule_name": "EU 10/2011 Annex II", "max_percent": 0.01, "note": "重金属限值Hg<0.01%"},
        {"name_pattern": "六价铬|Cr6", "rule_name": "EU 10/2011 Annex II", "max_percent": 0.01, "note": "重金属限值Cr(VI)<0.01%"},
        {"name_pattern": "甲醛", "rule_name": "EU 10/2011", "max_percent": 15.0, "note": "SML=15mg/kg"},
        {"name_pattern": "三聚氰胺", "rule_name": "EU 10/2011", "max_percent": 2.5, "note": "SML=2.5mg/kg"},
    ],
    RegulationDomain.TOYS: [
        {"name_pattern": "邻苯二甲酸", "rule_name": "EN 71-3 / 2009/48/EC", "max_percent": 0.1, "note": "6种邻苯总量<0.1%"},
        {"name_pattern": "铅|Pb", "rule_name": "EN 71-3", "max_percent": 0.009, "note": "迁移限值: 干燥/液态/刮取 2.0/0.5/23mg/kg"},
        {"name_pattern": "甲醛", "rule_name": "EN 71-9", "max_percent": 0.1, "note": "游离甲醛<0.1%"},
        {"name_pattern": "苯", "rule_name": "EN 71-9", "max_percent": 0.1, "note": "苯含量<0.1%"},
        {"name_pattern": "偶氮|芳香胺", "rule_name": "EN 71-11 / 1907/2006", "max_percent": 0.003, "note": "致癌芳香胺<30mg/kg"},
        {"name_pattern": "铅|Pb", "rule_name": "GB 6675.4-2014", "max_percent": 0.009, "note": "玩具特定元素迁移: Pb≤90mg/kg"},
        {"name_pattern": "镉|Cd", "rule_name": "GB 6675.4-2014", "max_percent": 0.0075, "note": "Cd≤75mg/kg"},
        {"name_pattern": "汞|Hg", "rule_name": "GB 6675.4-2014", "max_percent": 0.006, "note": "Hg≤60mg/kg"},
        {"name_pattern": "砷|As", "rule_name": "GB 6675.4-2014", "max_percent": 0.0025, "note": "As≤25mg/kg"},
        {"name_pattern": "锑|Sb", "rule_name": "GB 6675.4-2014", "max_percent": 0.006, "note": "Sb≤60mg/kg"},
    ],
    RegulationDomain.AUTOMOTIVE: [
        {"name_pattern": "铅|Pb", "rule_name": "ELV 2000/53/EC", "max_percent": 0.1, "note": "均质材料<0.1%"},
        {"name_pattern": "镉|Cd", "rule_name": "ELV 2000/53/EC", "max_percent": 0.01, "note": "均质材料<0.01%"},
        {"name_pattern": "汞|Hg", "rule_name": "ELV 2000/53/EC", "max_percent": 0.1, "note": "均质材料<0.1%"},
        {"name_pattern": "六价铬|Cr6", "rule_name": "ELV 2000/53/EC", "max_percent": 0.1, "note": "均质材料<0.1%"},
        {"name_pattern": "甲醛|VOC|挥发性有机", "rule_name": "VDA 278 / GBT 27630", "max_percent": 5, "note": "VOC限值"},
        {"name_pattern": "铅|Pb", "rule_name": "GB 30512-2014", "max_percent": 0.1, "note": "汽车禁用物质: Pb≤0.1%(均质材料)"},
        {"name_pattern": "镉|Cd", "rule_name": "GB 30512-2014", "max_percent": 0.01, "note": "Cd≤0.01%(均质材料)"},
        {"name_pattern": "汞|Hg", "rule_name": "GB 30512-2014", "max_percent": 0.1, "note": "Hg≤0.1%(均质材料)"},
        {"name_pattern": "六价铬|Cr6", "rule_name": "GB 30512-2014", "max_percent": 0.1, "note": "Cr(VI)≤0.1%(均质材料)"},
    ],
    RegulationDomain.CONSTRUCTION: [
        {"name_pattern": "甲醛", "rule_name": "GB 18580 / GB 18582", "max_percent": 0.01, "note": "室内装饰装修材料甲醛限值"},
        {"name_pattern": "VOC|挥发性有机", "rule_name": "GB 18582", "max_percent": 100, "note": "VOC限值(g/L看具体品类)"},
        {"name_pattern": "苯|甲苯|二甲苯", "rule_name": "GB 18581", "max_percent": 1.0, "note": "苯系物总量限值"},
        {"name_pattern": "甲醛", "rule_name": "GB 18582-2020", "max_percent": 0.005, "note": "建筑用墙面涂料: 甲醛≤50mg/kg"},
        {"name_pattern": "苯|甲苯|二甲苯|乙苯", "rule_name": "GB 18582-2020", "max_percent": 0.01, "note": "建筑用墙面涂料: 苯系物总和≤100mg/kg"},
        {"name_pattern": "乙二醇醚", "rule_name": "GB 18582-2020", "max_percent": 0.01, "note": "建筑用墙面涂料: 乙二醇醚及醚酯总和≤100mg/kg"},
        {"name_pattern": "铅|Pb", "rule_name": "GB 18582-2020", "max_percent": 0.009, "note": "可溶性重金属 Pb≤90mg/kg"},
        {"name_pattern": "镉|Cd", "rule_name": "GB 18582-2020", "max_percent": 0.0075, "note": "可溶性重金属 Cd≤75mg/kg"},
        {"name_pattern": "铬|Cr", "rule_name": "GB 18582-2020", "max_percent": 0.006, "note": "可溶性重金属 Cr≤60mg/kg"},
        {"name_pattern": "汞|Hg", "rule_name": "GB 18582-2020", "max_percent": 0.006, "note": "可溶性重金属 Hg≤60mg/kg"},
        {"name_pattern": "甲醛", "rule_name": "GB 24410-2009", "max_percent": 0.01, "note": "水性木器涂料: 游离甲醛≤100mg/kg"},
        {"name_pattern": "苯|甲苯|二甲苯|乙苯", "rule_name": "GB 24410-2009", "max_percent": 0.03, "note": "水性木器涂料: 苯系物总和≤300mg/kg"},
        {"name_pattern": "乙二醇醚", "rule_name": "GB 24410-2009", "max_percent": 0.03, "note": "水性木器涂料: 乙二醇醚及醚酯总和≤300mg/kg"},
        {"name_pattern": "甲醛", "rule_name": "GB 18580-2017", "max_percent": 0.005, "note": "人造板甲醛释放量≤0.124mg/m³(气候箱法), 此处按质量占比近似参考"},
    ],
    RegulationDomain.ELECTRONICS: [
        {"name_pattern": "铅|Pb", "rule_name": "RoHS 2011/65/EU", "max_percent": 0.1, "note": "均质材料Pb<0.1%"},
        {"name_pattern": "镉|Cd", "rule_name": "RoHS 2011/65/EU", "max_percent": 0.01, "note": "均质材料Cd<0.01%"},
        {"name_pattern": "汞|Hg", "rule_name": "RoHS 2011/65/EU", "max_percent": 0.1, "note": "均质材料Hg<0.1%"},
        {"name_pattern": "六价铬|Cr6", "rule_name": "RoHS 2011/65/EU", "max_percent": 0.1, "note": "均质材料Cr(VI)<0.1%"},
        {"name_pattern": "多溴联苯|多溴二苯醚|PBB|PBDE", "rule_name": "RoHS 2011/65/EU", "max_percent": 0.1, "note": "PBB/PBDE<0.1%"},
        {"name_pattern": "邻苯二甲酸", "rule_name": "RoHS 2015/863", "max_percent": 0.1, "note": "4种邻苯<0.1%"},
        {"name_pattern": "铅|Pb", "rule_name": "GB/T 26572-2011", "max_percent": 0.1, "note": "电子电气产品限用物质: Pb≤0.1%(均质材料)"},
        {"name_pattern": "镉|Cd", "rule_name": "GB/T 26572-2011", "max_percent": 0.01, "note": "Cd≤0.01%(均质材料)"},
        {"name_pattern": "汞|Hg", "rule_name": "GB/T 26572-2011", "max_percent": 0.1, "note": "Hg≤0.1%(均质材料)"},
        {"name_pattern": "六价铬|Cr6", "rule_name": "GB/T 26572-2011", "max_percent": 0.1, "note": "Cr(VI)≤0.1%(均质材料)"},
        {"name_pattern": "多溴联苯|多溴二苯醚|PBB|PBDE", "rule_name": "GB/T 26572-2011", "max_percent": 0.1, "note": "PBB/PBDE≤0.1%(均质材料)"},
    ],
    RegulationDomain.MEDICAL: [
        {"name_pattern": "邻苯二甲酸", "rule_name": "ISO 10993 / MDR 2017/745", "max_percent": 0.1, "note": "生物相容性评估"},
        {"name_pattern": "乳胶|天然橡胶", "rule_name": "ISO 10993-10", "max_percent": 0, "note": "致敏性评估"},
        {"name_pattern": "铅|Pb|镉|Cd|汞|Hg", "rule_name": "ISO 10993", "max_percent": 0.01, "note": "重金属可沥出物限值"},
    ],
    RegulationDomain.COSMETICS: [
        {"name_pattern": "铅|Pb", "rule_name": "化妆品安全技术规范(2015)", "max_percent": 0.001, "note": "铅<10mg/kg"},
        {"name_pattern": "砷|As", "rule_name": "化妆品安全技术规范(2015)", "max_percent": 0.0002, "note": "砷<2mg/kg"},
        {"name_pattern": "汞|Hg", "rule_name": "化妆品安全技术规范(2015)", "max_percent": 0.0001, "note": "汞<1mg/kg"},
        {"name_pattern": "镉|Cd", "rule_name": "化妆品安全技术规范(2015)", "max_percent": 0.0005, "note": "镉<5mg/kg"},
        {"name_pattern": "甲醛", "rule_name": "EU 1223/2009", "max_percent": 0.2, "note": "游离甲醛<0.2%(口腔产品<0.1%)"},
        {"name_pattern": "对羟基苯甲酸", "rule_name": "EU 1223/2009", "max_percent": 0.4, "note": "单酯<0.4%,混合酯<0.8%"},
        {"name_pattern": "甲醇", "rule_name": "化妆品安全技术规范(2015)", "max_percent": 0.2, "note": "甲醇≤0.2%(2000mg/kg)"},
        {"name_pattern": "二噁烷|1,4-二氧杂环己烷", "rule_name": "化妆品安全技术规范(2015)", "max_percent": 0.003, "note": "二噁烷≤30mg/kg(表面活性剂等原料带入)"},
        {"name_pattern": "石棉", "rule_name": "化妆品安全技术规范(2015)", "max_percent": 0, "note": "石棉为禁用成分(滑石粉类原料不得检出)"},
        {"name_pattern": "氢醌|对苯二酚", "rule_name": "化妆品安全技术规范(2015)", "max_percent": 0, "note": "氢醌为禁用成分"},
        {"name_pattern": "维A酸|维甲酸|视黄酸|异维A酸", "rule_name": "化妆品安全技术规范(2015)", "max_percent": 0, "note": "维A酸类为禁用成分"},
        {"name_pattern": "糖皮质激素|氯倍他索|地塞米松|倍他米松|氢化可的松|曲安奈德", "rule_name": "化妆品安全技术规范(2015)", "max_percent": 0, "note": "糖皮质激素为禁用成分(非法添加重点监测)"},
        {"name_pattern": "尼泊金丙酯|尼泊金丁酯|对羟基苯甲酸丙酯|对羟基苯甲酸丁酯", "rule_name": "化妆品安全技术规范(2015)", "max_percent": 0.14, "note": "丙酯/丁酯单一≤0.14%, 混合酯≤0.8%"},
        {"name_pattern": "二苯酮-3|BP-3|氧苯酮", "rule_name": "化妆品安全技术规范(2015)", "max_percent": 10, "note": "防晒剂二苯酮-3≤10%"},
        {"name_pattern": "甲氧基肉桂酸乙基己酯|奥克立林", "rule_name": "化妆品安全技术规范(2015)", "max_percent": 10, "note": "防晒剂≤10%"},
        {"name_pattern": "水杨酸乙基己酯", "rule_name": "化妆品安全技术规范(2015)", "max_percent": 5, "note": "防晒剂水杨酸乙基己酯≤5%"},
        {"name_pattern": "二氧化钛", "rule_name": "化妆品安全技术规范(2015)", "max_percent": 25, "note": "作防晒剂时≤25%(作着色剂用途不限)"},
        {"name_pattern": "氧化锌", "rule_name": "化妆品安全技术规范(2015)", "max_percent": 25, "note": "作防晒剂时≤25%(作着色剂用途不限)"},
        {"name_pattern": "氟化钠|单氟磷酸钠|氟化亚锡", "rule_name": "GB/T 8372-2017", "max_percent": 0.15, "note": "牙膏总氟: 成人0.05%~0.15%, 儿童0.05%~0.11%"},
    ],
    RegulationDomain.TEXTILE: [
        {"name_pattern": "甲醛", "rule_name": "GB 18401-2010", "max_percent": 0.0075, "note": "直接接触皮肤类≤75mg/kg, A类婴幼儿≤20mg/kg"},
        {"name_pattern": "偶氮|芳香胺|联苯胺", "rule_name": "GB 18401-2010", "max_percent": 0.002, "note": "可分解致癌芳香胺≤20mg/kg"},
    ],
}


def _clean_name(name: str) -> str:
    import re
    return re.sub(r"\s+", "", name.lower())


def check_compliance(req: ComplianceRequest) -> ComplianceResult:
    """对配方进行多领域合规检查。"""
    violations: list[Violation] = []
    warnings: list[str] = []

    for domain in req.domains:
        rules = _RULES.get(domain, [])
        if not rules:
            warnings.append(f"领域 {domain.value} 暂无预置法规规则，建议人工审查")
            continue

        for item in req.formula.items:
            name = _clean_name(item.material.name)
            percent = item.weight_percent

            for rule in rules:
                pattern = rule["name_pattern"]
                import re
                name_match = re.search(pattern, name, re.IGNORECASE)
                cas_match = False
                if not name_match and rule.get("cas"):
                    item_cas = item.material.cas_number or ""
                    cas_match = rule["cas"] in item_cas
                if not name_match and not cas_match:
                    continue

                # Got a match
                max_pct = rule.get("max_percent")
                if max_pct is not None and percent > max_pct:
                    severity = "error" if percent >= max_pct * 2 else "warning"
                    violations.append(Violation(
                        material_name=item.material.name,
                        domain=domain,
                        rule_name=rule["rule_name"],
                        limit_value=f"<= {max_pct}%",
                        actual_value=f"{percent}%",
                        severity=severity,
                    ))
                else:
                    # Within limit, just note it
                    import textwrap
                    violations.append(Violation(
                        material_name=item.material.name,
                        domain=domain,
                        rule_name=rule["rule_name"],
                        limit_value=f"<= {max_pct}%" if max_pct else "判定",
                        actual_value=f"{percent}%",
                        severity="info",
                    ))

    passed = not any(v.severity in ("error", "critical") for v in violations)
    error_count = sum(1 for v in violations if v.severity == "error")
    warn_count = sum(1 for v in violations if v.severity == "warning")

    return ComplianceResult(
        formula_name=req.formula.name,
        domains_checked=req.domains,
        passed=passed,
        violations=violations,
        warnings=warnings,
        summary=f"检查 {len(req.domains)} 个领域，{len(violations)} 条记录（不合规:{error_count}, 提醒:{warn_count}）",
    )

