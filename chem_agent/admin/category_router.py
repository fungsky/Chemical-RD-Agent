"""分类管理 API（产品类别 / 材料功能）"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from chem_agent.auth import database as db
from chem_agent.auth.dependencies import require_permission
from chem_agent.auth.models import CategoryCreate, CategoryUpdate, CategoryOut, UserOut

router = APIRouter(prefix="/api/admin/categories", tags=["分类管理"])


@router.get("", response_model=list[CategoryOut])
async def list_categories(
    type: str = Query(None, description="product 或 function"),
    _user: UserOut = Depends(require_permission("category:read")),
):
    """获取分类列表，可按类型筛选。"""
    cats = db.list_categories(cat_type=type)
    return [CategoryOut(**c) for c in cats]


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(
    body: CategoryCreate,
    current_user: UserOut = Depends(require_permission("category:write")),
):
    """创建新分类。"""
    cat_id = db.create_category(
        cat_type=body.type,
        code=body.code,
        display_zh=body.display_zh,
        display_en=body.display_en,
        sort_order=body.sort_order,
    )
    db.log_audit(
        action="create_category",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="category",
        resource_id=str(cat_id),
        details={"type": body.type, "code": body.code},
    )
    cat = {"id": cat_id, **body.model_dump()}
    return CategoryOut(**cat)


@router.put("/{cat_id}", response_model=CategoryOut)
async def update_category(
    cat_id: int,
    body: CategoryUpdate,
    current_user: UserOut = Depends(require_permission("category:write")),
):
    """更新分类信息。"""
    ok = db.update_category(cat_id, **body.model_dump(exclude_unset=True))
    if not ok:
        raise HTTPException(status_code=404, detail="分类不存在")
    db.log_audit(
        action="update_category",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="category",
        resource_id=str(cat_id),
    )
    # Re-fetch to return updated data
    cats = db.list_categories()
    for c in cats:
        if c["id"] == cat_id:
            return CategoryOut(**c)
    raise HTTPException(status_code=404, detail="分类不存在")


@router.delete("/{cat_id}")
async def delete_category(
    cat_id: int,
    current_user: UserOut = Depends(require_permission("category:delete")),
):
    """删除分类。"""
    ok = db.delete_category(cat_id)
    if not ok:
        raise HTTPException(status_code=404, detail="分类不存在")
    db.log_audit(
        action="delete_category",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="category",
        resource_id=str(cat_id),
    )
    return {"message": "分类已删除"}
