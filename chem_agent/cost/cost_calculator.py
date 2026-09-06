"""BOM 成本核算引擎 -- 基于物料单价计算配方成本和利润空间。"""

from typing import Optional

from pydantic import BaseModel, Field

from chem_agent.models.formula import Formula, FormulaItem


class MaterialCost(BaseModel):
    material_name: str = Field(..., description="物料名称")
    unit_price: float = Field(..., ge=0, description="单价(元/kg)")
    weight_kg: float = Field(..., ge=0, description="配方中用量(kg)")
    cost: float = Field(..., ge=0, description="该物料成本(元)")


class CostRequest(BaseModel):
    formula: Formula
    batch_size_kg: float = Field(1.0, ge=0.1, description="批次规模(kg)")
    price_map: dict[str, float] = Field(
        default_factory=dict,
        description="物料名称->单价(元/kg)的映射表",
    )
    packaging_cost_per_kg: float = Field(0, ge=0, description="包装成本(元/kg)")
    labor_cost_per_kg: float = Field(0, ge=0, description="人工成本(元/kg)")
    energy_cost_per_kg: float = Field(0, ge=0, description="能耗成本(元/kg)")
    overhead_rate: float = Field(0.15, ge=0, le=1, description="管理费率(占物料成本比例)")


class CostBreakdown(BaseModel):
    materials_total: float = Field(0, description="物料总成本")
    packaging: float = Field(0, description="包装成本")
    labor: float = Field(0, description="人工成本")
    energy: float = Field(0, description="能耗成本")
    overhead: float = Field(0, description="管理费用")
    total: float = Field(0, description="总成本")


class CostResult(BaseModel):
    formula_name: str
    batch_size_kg: float
    unit_cost_per_kg: float = Field(0, description="单位成本(元/kg)")
    items: list[MaterialCost] = Field(default_factory=list)
    breakdown: CostBreakdown = Field(default_factory=CostBreakdown)
    missing_prices: list[str] = Field(default_factory=list, description="缺少单价的物料")


def calculate_formula_cost(req: CostRequest) -> CostResult:
    """计算配方的BOM成本和单位成本。"""
    items: list[MaterialCost] = []
    materials_total = 0.0
    missing: list[str] = []

    scale = req.batch_size_kg

    for formula_item in req.formula.items:
        name = formula_item.material.name
        weight_kg = formula_item.weight_percent / 100.0 * scale
        unit_price = req.price_map.get(name)

        if unit_price is None:
            missing.append(name)
            cost_val = 0.0
        else:
            cost_val = round(weight_kg * unit_price, 2)

        materials_total += cost_val

        items.append(MaterialCost(
            material_name=name,
            unit_price=unit_price or 0,
            weight_kg=round(weight_kg, 3),
            cost=cost_val,
        ))

    packaging = round(req.packaging_cost_per_kg * scale, 2)
    labor = round(req.labor_cost_per_kg * scale, 2)
    energy = round(req.energy_cost_per_kg * scale, 2)
    overhead = round(materials_total * req.overhead_rate, 2)
    total = round(materials_total + packaging + labor + energy + overhead, 2)

    unit_cost = round(total / scale, 2) if scale > 0 else 0

    return CostResult(
        formula_name=req.formula.name,
        batch_size_kg=scale,
        unit_cost_per_kg=unit_cost,
        items=items,
        breakdown=CostBreakdown(
            materials_total=round(materials_total, 2),
            packaging=packaging,
            labor=labor,
            energy=energy,
            overhead=overhead,
            total=total,
        ),
        missing_prices=missing,
    )

print("cost done")
