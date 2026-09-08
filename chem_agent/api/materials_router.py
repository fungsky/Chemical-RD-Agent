"""原材料管理 API（已停用：材料主数据统一走知识图谱 API，勿重新挂载）。"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from chem_agent.materials import (MaterialRecord, MaterialQuery, SupplierInfo, MaterialPrice, MaterialBatch, get_material_manager)
from chem_agent.auth.dependencies import require_permission
from chem_agent.auth.models import UserOut

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/materials", tags=["Materials"])

@router.post("/", response_model=MaterialRecord)
async def add_material(rec: MaterialRecord, _user: UserOut = Depends(require_permission("material:write"))):
    try: return get_material_manager().add(rec)
    except ValueError as e: raise HTTPException(409, str(e))

@router.get("/{name}", response_model=MaterialRecord)
async def get_material(name: str, _user: UserOut = Depends(require_permission("material:read"))):
    r = get_material_manager().get(name)
    if not r: raise HTTPException(404, f"{name} not found")
    return r

@router.patch("/{name}")
async def update_material(name: str, updates: dict, _user: UserOut = Depends(require_permission("material:write"))):
    try: return get_material_manager().update(name, updates)
    except KeyError: raise HTTPException(404)

@router.delete("/{name}")
async def delete_material(name: str, _user: UserOut = Depends(require_permission("material:delete"))):
    if not get_material_manager().delete(name): raise HTTPException(404)
    return {"success": True}

@router.post("/{name}/suppliers")
async def add_supplier(name: str, sup: SupplierInfo, _user: UserOut = Depends(require_permission("material:write"))):
    try: return get_material_manager().add_supplier(name, sup)
    except KeyError: raise HTTPException(404)

@router.post("/{name}/prices")
async def add_price(name: str, price: MaterialPrice, _user: UserOut = Depends(require_permission("material:write"))):
    try: return get_material_manager().add_price(name, price)
    except KeyError: raise HTTPException(404)

@router.post("/{name}/batches")
async def add_batch(name: str, batch: MaterialBatch, _user: UserOut = Depends(require_permission("material:write"))):
    try: return get_material_manager().add_batch(name, batch)
    except KeyError: raise HTTPException(404)

@router.post("/query")
async def query_materials(q: MaterialQuery, _user: UserOut = Depends(require_permission("material:read"))):
    r = get_material_manager().query(q)
    return {"total": len(r), "results": r}

@router.get("/list/all")
async def list_all(_user: UserOut = Depends(require_permission("material:read"))): return get_material_manager().list_all()
@router.get("/stats/categories")
async def stats(_user: UserOut = Depends(require_permission("material:read"))): return get_material_manager().get_by_category()
