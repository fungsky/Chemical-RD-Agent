"""原材料管理系统 --- CAS查询、供应商比价、批次追溯、保质期预警。"""

from chem_agent.materials.models import (
    MaterialRecord, MaterialQuery, SupplierInfo, MaterialPrice,
    MaterialBatch, ShelfLifeStatus, MaterialCategory,
)
from chem_agent.materials.manager import MaterialManager, get_material_manager
