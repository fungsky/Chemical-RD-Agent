"""化工配方领域数据模型"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, model_validator


class ProductCategory(str, Enum):
    """产品类别"""
    COATING = "涂料"
    ADHESIVE = "胶粘剂"
    SEALANT = "密封剂"
    RESIN = "树脂"
    SURFACTANT = "表面活性剂"
    CATALYST = "催化剂"
    ADDITIVE = "助剂"
    PLASTIC = "塑料"
    RUBBER = "橡胶"
    INK = "油墨"
    OTHER = "其他"


class MaterialFunction(str, Enum):
    """原料功能分类"""
    BASE_RESIN = "基础树脂"
    SOLVENT = "溶剂"
    FILLER = "填料"
    PIGMENT = "颜料"
    CURING_AGENT = "固化剂"
    CATALYST = "催化剂"
    DISPERSANT = "分散剂"
    LEVELING_AGENT = "流平剂"
    DEFOAMER = "消泡剂"
    THICKENER = "增稠剂"
    PLASTICIZER = "增塑剂"
    ANTIOXIDANT = "抗氧化剂"
    UV_STABILIZER = "紫外稳定剂"
    FLAME_RETARDANT = "阻燃剂"
    COUPLING_AGENT = "偶联剂"
    WETTING_AGENT = "润湿剂"
    OTHER = "其他"


class FormulaStatus(str, Enum):
    """配方状态"""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    ARCHIVED = "archived"


class HazardClass(str, Enum):
    """GHS 危险类别"""
    NONE = "无"
    FLAMMABLE = "易燃液体/固体"
    TOXIC = "有毒"
    CORROSIVE = "腐蚀性"
    OXIDIZING = "氧化性"
    EXPLOSIVE = "爆炸性"
    IRRITANT = "刺激性"
    ENVIRONMENTAL = "环境危害"
    COMPRESSED_GAS = "压缩气体"


class SafetyData(BaseModel):
    """化学品安全数据 (SDS摘要)"""
    hazard_class: list[HazardClass] = Field(default_factory=list, description="GHS危险类别")
    hazard_statement: Optional[str] = Field(None, description="GHS危险性说明(H-code)")
    precaution: Optional[str] = Field(None, description="GHS防范说明(P-code)")
    flash_point_c: Optional[float] = Field(None, description="闪点(℃)")
    explosive_limit_lower: Optional[float] = Field(None, description="爆炸下限(%)")
    explosive_limit_upper: Optional[float] = Field(None, description="爆炸上限(%)")
    ld50_oral_mgkg: Optional[float] = Field(None, description="LD50 经口(mg/kg)")
    storage_temp_min_c: Optional[float] = Field(None, description="储存温度下限(℃)")
    storage_temp_max_c: Optional[float] = Field(None, description="储存温度上限(℃)")
    storage_condition: Optional[str] = Field(None, description="储存条件(避光/干燥/通风等)")
    incompatible_materials: list[str] = Field(default_factory=list, description="不相容物料")
    personal_protection: Optional[str] = Field(None, description="个人防护(PPE)要求")
    emergency_response: Optional[str] = Field(None, description="应急处理措施")
    regulatory_notes: Optional[str] = Field(None, description="法规备注(ROHS/REACH/食品接触等)")


class RawMaterial(BaseModel):
    """原材料"""
    id: Optional[str] = None
    name: str = Field(..., description="原料名称")
    cas_number: Optional[str] = Field(None, description="CAS 编号")
    chemical_name: Optional[str] = Field(None, description="化学名称")
    supplier: Optional[str] = Field(None, description="供应商")
    function: MaterialFunction = Field(MaterialFunction.OTHER, description="功能分类")
    properties: dict = Field(default_factory=dict, description="理化性质")
    safety: Optional[SafetyData] = Field(None, description="安全数据")
    safety_info: Optional[str] = Field(None, description="安全信息(纯文本，向后兼容)")


class FormulaItem(BaseModel):
    """配方组分"""
    material: RawMaterial
    weight_percent: float = Field(..., ge=0, le=100, description="质量百分比 (%)")
    addition_order: Optional[int] = Field(None, description="加料顺序")
    notes: Optional[str] = Field(None, description="备注")


class ProcessCondition(BaseModel):
    """工艺条件"""
    mixing_speed: Optional[float] = Field(None, description="搅拌速度 (rpm)")
    mixing_time: Optional[float] = Field(None, description="搅拌时间 (min)")
    temperature: Optional[float] = Field(None, description="反应温度 (°C)")
    pressure: Optional[float] = Field(None, description="反应压力 (MPa)")
    curing_temperature: Optional[float] = Field(None, description="固化温度 (°C)")
    curing_time: Optional[float] = Field(None, description="固化时间 (h)")
    notes: Optional[str] = Field(None, description="工艺备注")


class PerformanceTest(BaseModel):
    """性能测试结果"""
    test_name: str = Field(..., description="测试项目名称")
    test_method: Optional[str] = Field(None, description="测试标准/方法")
    value: float = Field(..., description="测试值")
    unit: str = Field("", description="单位")
    target_min: Optional[float] = Field(None, description="目标下限")
    target_max: Optional[float] = Field(None, description="目标上限")
    is_qualified: Optional[bool] = Field(None, description="是否合格")


class Formula(BaseModel):
    """配方"""
    id: Optional[str] = None
    name: str = Field(..., description="配方名称")
    code: Optional[str] = Field(None, description="配方编号")
    version: str = Field("1.0", description="版本号")
    status: FormulaStatus = Field(FormulaStatus.DRAFT, description="配方状态")
    category: ProductCategory = Field(ProductCategory.OTHER, description="产品类别")
    description: Optional[str] = Field(None, description="配方描述")
    items: list[FormulaItem] = Field(default_factory=list, description="配方组分列表")
    process: Optional[ProcessCondition] = Field(None, description="工艺条件")
    performance: list[PerformanceTest] = Field(default_factory=list, description="性能测试结果")
    target_application: Optional[str] = Field(None, description="目标应用场景")
    creator: Optional[str] = Field(None, description="创建人")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    tags: list[str] = Field(default_factory=list, description="标签")
    notes: Optional[str] = Field(None, description="备注")

    @model_validator(mode="after")
    def validate_weight_percent(self):
        """校验配方组分重量百分比总和在合理范围内(95%~105%)。"""
        if not self.items:
            return self
        total = sum(item.weight_percent for item in self.items)
        if total < 95.0:
            raise ValueError(
                f"配方 '{self.name}' 组分重量百分比总和为 {total:.1f}%，低于95%。"
                f"请补充差额组分(如水、稀释剂)或调整比例。"
            )
        if total > 105.0:
            raise ValueError(
                f"配方 '{self.name}' 组分重量百分比总和为 {total:.1f}%，超过105%。"
                f"请检查各组分比例是否合理。"
            )
        return self


class FormulaSearchResult(BaseModel):
    """配方检索结果"""
    formula: Formula
    similarity_score: float = Field(0.0, ge=0.0, le=1.0, description="相似度评分")
    match_reason: str = Field("", description="匹配原因说明")


class PredictionRequest(BaseModel):
    """性能预测请求"""
    items: list[FormulaItem] = Field(..., description="配方组分")
    category: ProductCategory = Field(..., description="产品类别")
    process: Optional[ProcessCondition] = Field(None, description="工艺条件")
    target_properties: list[str] = Field(default_factory=list, description="需要预测的性能指标")


class PredictionResult(BaseModel):
    """性能预测结果"""
    property_name: str = Field(..., description="性能指标名称")
    predicted_value: float = Field(..., description="预测值")
    unit: str = Field("", description="单位")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="置信度")
    reference_formulas: list[str] = Field(default_factory=list, description="参考配方ID列表")
    explanation: Optional[str] = Field(None, description="预测解释")
