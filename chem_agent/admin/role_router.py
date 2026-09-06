"""角色管理 API"""

from fastapi import APIRouter, Depends, HTTPException, status

from chem_agent.auth import database as db
from chem_agent.auth.dependencies import require_permission
from chem_agent.auth.models import (
    RoleCreate,
    RoleUpdate,
    RoleOut,
    PermissionOut,
    PermissionAssignRequest,
    UserOut,
)

router = APIRouter(prefix="/api/admin/roles", tags=["角色管理"])


@router.get("", response_model=list[RoleOut])
async def list_roles(_user: UserOut = Depends(require_permission("role:read"))):
    """获取所有角色。"""
    roles = db.list_roles()
    return [RoleOut(**r) for r in roles]


@router.get("/permissions", response_model=list[PermissionOut])
async def list_permissions(_user: UserOut = Depends(require_permission("role:read"))):
    """获取所有系统权限定义。"""
    perms = db.list_permissions()
    return [PermissionOut(**p) for p in perms]


@router.get("/{role_id}", response_model=RoleOut)
async def get_role(role_id: int, _user: UserOut = Depends(require_permission("role:read"))):
    """获取指定角色详情。"""
    role = db.get_role_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    return RoleOut(**role)


@router.post("", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
async def create_role(
    body: RoleCreate,
    current_user: UserOut = Depends(require_permission("role:write")),
):
    """创建自定义角色。"""
    role_id = db.create_role(
        name=body.name,
        display_name=body.display_name,
        description=body.description,
    )
    db.log_audit(
        action="create_role",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="role",
        resource_id=str(role_id),
        details={"role_name": body.name},
    )
    role = db.get_role_by_id(role_id)
    return RoleOut(**role)


@router.put("/{role_id}", response_model=RoleOut)
async def update_role(
    role_id: int,
    body: RoleUpdate,
    current_user: UserOut = Depends(require_permission("role:write")),
):
    """更新角色信息（系统角色只能改显示名和描述）。"""
    role = db.get_role_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    db.update_role(role_id, display_name=body.display_name, description=body.description)
    db.log_audit(
        action="update_role",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="role",
        resource_id=str(role_id),
    )
    updated = db.get_role_by_id(role_id)
    return RoleOut(**updated)


@router.delete("/{role_id}")
async def delete_role(
    role_id: int,
    current_user: UserOut = Depends(require_permission("role:delete")),
):
    """删除自定义角色（系统角色不可删除）。"""
    ok = db.delete_role(role_id)
    if not ok:
        raise HTTPException(status_code=400, detail="删除失败（角色不存在或为系统角色）")
    db.log_audit(
        action="delete_role",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="role",
        resource_id=str(role_id),
    )
    return {"message": "角色已删除"}


@router.put("/{role_id}/permissions")
async def assign_permissions(
    role_id: int,
    body: PermissionAssignRequest,
    current_user: UserOut = Depends(require_permission("role:write")),
):
    """设置角色权限。"""
    role = db.get_role_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    db.set_role_permissions(role_id, body.permission_ids)
    db.log_audit(
        action="assign_permissions",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="role",
        resource_id=str(role_id),
        details={"permission_ids": body.permission_ids},
    )
    return {"message": "权限已更新"}
