"""用户管理 API"""

from fastapi import APIRouter, Depends, HTTPException, status

from chem_agent.auth import database as db
from chem_agent.auth.dependencies import require_permission
from chem_agent.auth.models import (
    UserCreate,
    UserUpdate,
    UserOut,
    ResetPasswordRequest,
    RoleAssignRequest,
)
from chem_agent.auth.service import _build_user_out

router = APIRouter(prefix="/api/admin/users", tags=["用户管理"])


@router.get("", response_model=list[UserOut])
async def list_users(_user: UserOut = Depends(require_permission("user:read"))):
    """获取所有用户列表。"""
    users, _total = db.list_users(limit=1000)
    return [_build_user_out(u) for u in users]


@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: int, _user: UserOut = Depends(require_permission("user:read"))):
    """获取指定用户详情。"""
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return _build_user_out(user)


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    current_user: UserOut = Depends(require_permission("user:write")),
):
    """创建新用户。"""
    existing = db.get_user_by_username(body.username)
    if existing:
        raise HTTPException(status_code=409, detail="用户名已存在")
    user_id = db.create_user(
        username=body.username,
        password=body.password,
        email=body.email,
        full_name=body.full_name,
    )
    db.log_audit(
        action="create_user",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="user",
        resource_id=str(user_id),
        details={"new_username": body.username},
    )
    user = db.get_user_by_id(user_id)
    return _build_user_out(user)


@router.put("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    body: UserUpdate,
    current_user: UserOut = Depends(require_permission("user:write")),
):
    """更新用户信息。"""
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.update_user(user_id, **body.model_dump(exclude_unset=True))
    db.log_audit(
        action="update_user",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="user",
        resource_id=str(user_id),
    )
    updated = db.get_user_by_id(user_id)
    return _build_user_out(updated)


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: UserOut = Depends(require_permission("user:delete")),
):
    """删除用户（超级管理员不可删除）。"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    ok = db.delete_user(user_id)
    if not ok:
        raise HTTPException(status_code=400, detail="删除失败（用户不存在或为超级管理员）")
    db.log_audit(
        action="delete_user",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="user",
        resource_id=str(user_id),
    )
    return {"message": "用户已删除"}


@router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: int,
    body: ResetPasswordRequest,
    current_user: UserOut = Depends(require_permission("user:write")),
):
    """重置用户密码。"""
    ok = db.reset_user_password(user_id, body.new_password)
    if not ok:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.log_audit(
        action="reset_password",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="user",
        resource_id=str(user_id),
    )
    return {"message": "密码已重置"}


@router.post("/{user_id}/toggle-active")
async def toggle_active(
    user_id: int,
    current_user: UserOut = Depends(require_permission("user:write")),
):
    """启用/禁用用户。"""
    new_state = db.toggle_user_active(user_id)
    if new_state is None:
        raise HTTPException(status_code=400, detail="操作失败（用户不存在或为超级管理员）")
    db.log_audit(
        action="toggle_user_active",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="user",
        resource_id=str(user_id),
        details={"is_active": new_state},
    )
    return {"is_active": new_state}


@router.put("/{user_id}/roles")
async def assign_roles(
    user_id: int,
    body: RoleAssignRequest,
    current_user: UserOut = Depends(require_permission("user:write")),
):
    """设置用户角色。"""
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.set_user_roles(user_id, body.role_ids)
    db.log_audit(
        action="assign_roles",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="user",
        resource_id=str(user_id),
        details={"role_ids": body.role_ids},
    )
    return {"message": "角色已更新"}
