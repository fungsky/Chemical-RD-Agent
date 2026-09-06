"""原材料数据模型。"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MaterialCategory(str, Enum):
    RESIN = "树脂"; SOLVENT = "溶剂"; PIGMENT = "颜料"; FILLER = "填料"
    ADDITIVE = "助剂"; CURING_AGENT = "固化剂"; MONOMER = "单体"
    CATALYST = "催化剂"; PLASTICIZER = "增塑剂"; SURFACTANT = "表面活性剂"
    OTHER = "其他"


class ShelfLifeStatus(str, Enum):
    VALID = "valid"; EXPIRING_SOON = "expiring_soon"
    EXPIRED = "expired"; UNKNOWN = "unknown"


class SupplierInfo(BaseModel):
    name: str = Field(..., description="供应商名称")
    contact: Optional[str] = None
    region: str = Field("中国")
    is_preferred: bool = False
    min_order_kg: float = Field(1.0, ge=0)
    lead_time_days: int = Field(7, ge=1)
    notes: Optional[str] = None


class MaterialPrice(BaseModel):
    supplier_name: str
    unit_price: float = Field(..., ge=0, description="单价(元/kg)")
    currency: str = "CNY"
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    min_order_kg: float = 1.0
    is_current: bool = True


class MaterialBatch(BaseModel):
    batch_number: str = Field(..., description="批号")
    quantity_kg: float = Field(..., ge=0)
    received_date: datetime = Field(default_factory=datetime.now)
    expiry_date: Optional[datetime] = None
    coa_available: bool = False
    coa_file: Optional[str] = None
    storage_location: Optional[str] = None
    status: str = Field("available")


class MaterialRecord(BaseModel):
    id: Optional[str] = None
    name: str = Field(..., description="商品名/通用名")
    cas_number: Optional[str] = None
    chemical_name: Optional[str] = None
    category: MaterialCategory = MaterialCategory.OTHER
    function: Optional[str] = None
    suppliers: list[SupplierInfo] = Field(default_factory=list)
    prices: list[MaterialPrice] = Field(default_factory=list)
    batches: list[MaterialBatch] = Field(default_factory=list)
    density_g_ml: Optional[float] = None
    viscosity_mPa_s: Optional[float] = None
    boiling_point_c: Optional[float] = None
    melting_point_c: Optional[float] = None
    flash_point_c: Optional[float] = None
    molecular_weight: Optional[float] = None
    solubility: Optional[str] = None
    hazard_class: list[str] = Field(default_factory=list)
    storage_condition: Optional[str] = None
    shelf_life_months: Optional[int] = None
    notes: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    @property
    def current_price(self) -> Optional[float]:
        current = [p for p in self.prices if p.is_current]
        return min(p.unit_price for p in current) if current else None

    @property
    def total_stock_kg(self) -> float:
        return sum(b.quantity_kg for b in self.batches if b.status in ("available", "in_use"))

    @property
    def shelf_life_status(self) -> ShelfLifeStatus:
        if not self.batches: return ShelfLifeStatus.UNKNOWN
        now = datetime.now()
        statuses = []
        for b in self.batches:
            if not b.expiry_date: continue
            days = (b.expiry_date - now).days
            if days < 0: statuses.append(ShelfLifeStatus.EXPIRED)
            elif days < 90: statuses.append(ShelfLifeStatus.EXPIRING_SOON)
            else: statuses.append(ShelfLifeStatus.VALID)
        if not statuses: return ShelfLifeStatus.UNKNOWN
        if ShelfLifeStatus.EXPIRED in statuses: return ShelfLifeStatus.EXPIRED
        if ShelfLifeStatus.EXPIRING_SOON in statuses: return ShelfLifeStatus.EXPIRING_SOON
        return ShelfLifeStatus.VALID


class MaterialQuery(BaseModel):
    name: Optional[str] = None
    cas_number: Optional[str] = None
    category: Optional[MaterialCategory] = None
    function: Optional[str] = None
    supplier: Optional[str] = None
    shelf_life_status: Optional[ShelfLifeStatus] = None
    has_price: Optional[bool] = None
    limit: int = Field(100, ge=1, le=1000)
