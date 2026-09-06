"""FastAPI dependency injection: extract current user, check permissions."""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from chem_agent.auth.security import verify_token
from chem_agent.auth import database as db
from chem_agent.auth.models import UserOut
from chem_agent.auth.service import _build_user_out
from chem_agent.config import settings

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> UserOut:
    """Extract and validate the current user from the Authorization header."""
    # 本地免登录模式：跳过 JWT 校验，直接以超级管理员身份放行（仅限本地/内网）
    if settings.auth_bypass:
        return UserOut(
            id=1,
            username="local",
            email=None,
            full_name="Local (auth bypass)",
            is_active=True,
            is_superadmin=True,
            created_at=None,
            last_login=None,
            roles=["superadmin"],
            permissions=["*"],
        )
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或过期的令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = int(payload.get("sub", 0))
    user = db.get_user_by_id(user_id)
    if user is None or not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已禁用",
        )
    return _build_user_out(user)


def require_permission(*permission_codes: str):
    """Return a dependency that checks if the current user has ALL specified permissions.

    Usage:
        @router.get("/users", dependencies=[Depends(require_permission("user:read"))])
        async def list_users(): ...

    Or inject user directly:
        async def list_users(user: UserOut = Depends(require_permission("user:read"))): ...
    """

    async def _checker(
        current_user: UserOut = Depends(get_current_user),
    ) -> UserOut:
        # Superadmin has wildcard
        if "*" in current_user.permissions:
            return current_user
        for code in permission_codes:
            if code not in current_user.permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"权限不足，需要: {code}",
                )
        return current_user

    return _checker
