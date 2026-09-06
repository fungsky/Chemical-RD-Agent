"""Auth router: login, token refresh, current user info, change password."""

from fastapi import APIRouter, Depends, HTTPException, status

from chem_agent.auth.models import (
    LoginRequest,
    RefreshRequest,
    ResetPasswordRequest,
    UserOut,
    UserWithToken,
)
from chem_agent.auth.service import authenticate_user, refresh_access_token, get_user_info
from chem_agent.auth.dependencies import get_current_user
from chem_agent.auth import database as db

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/login", response_model=UserWithToken)
async def login(request: LoginRequest):
    """用户登录，返回 JWT 令牌。"""
    result = authenticate_user(request.username, request.password)
    if result is None:
        db.log_audit(
            action="login_failed",
            username=request.username,
            resource_type="auth",
            details={"reason": "invalid credentials"},
            status="failure",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    db.log_audit(
        action="login",
        user_id=result.user.id,
        username=result.user.username,
        resource_type="auth",
        status="success",
    )
    return result


@router.post("/refresh", response_model=UserWithToken)
async def refresh_token(request: RefreshRequest):
    """使用 refresh_token 获取新令牌对。"""
    result = refresh_access_token(request.refresh_token)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="刷新令牌无效或已过期",
        )
    return result


@router.get("/me", response_model=UserOut)
async def get_me(current_user: UserOut = Depends(get_current_user)):
    """获取当前登录用户信息。"""
    return current_user


@router.post("/me/password")
async def change_my_password(
    request: ResetPasswordRequest,
    current_user: UserOut = Depends(get_current_user),
):
    """修改当前用户密码。"""
    ok = db.reset_user_password(current_user.id, request.new_password)
    if not ok:
        raise HTTPException(status_code=500, detail="密码修改失败")
    db.log_audit(
        action="change_password",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="user",
        resource_id=str(current_user.id),
    )
    return {"message": "密码修改成功"}
