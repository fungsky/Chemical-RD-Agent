"""Auth business logic: login, refresh, user info assembly."""

from typing import Optional

from chem_agent.auth import database as db
from chem_agent.auth.security import verify_password, create_access_token, create_refresh_token, verify_token
from chem_agent.auth.models import UserOut, UserWithToken


def authenticate_user(username: str, password: str) -> Optional[UserWithToken]:
    """Verify credentials and return user with tokens, or None."""
    user = db.get_user_by_username(username)
    if not user:
        return None
    if not user["is_active"]:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None

    db.update_last_login(user["id"])

    user_out = _build_user_out(user)
    access_token = _create_token_for_user(user_out)
    refresh_token = create_refresh_token(user["id"])

    return UserWithToken(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_out,
    )


def refresh_access_token(refresh_token: str) -> Optional[UserWithToken]:
    """Validate refresh token and issue new token pair."""
    payload = verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        return None

    user_id = int(payload["sub"])
    user = db.get_user_by_id(user_id)
    if not user or not user["is_active"]:
        return None

    user_out = _build_user_out(user)
    new_access = _create_token_for_user(user_out)
    new_refresh = create_refresh_token(user_id)

    return UserWithToken(
        access_token=new_access,
        refresh_token=new_refresh,
        user=user_out,
    )


def get_user_info(user_id: int) -> Optional[UserOut]:
    """Get full user info by id."""
    user = db.get_user_by_id(user_id)
    if not user:
        return None
    return _build_user_out(user)


def _build_user_out(user: dict) -> UserOut:
    """Assemble UserOut with roles and permissions."""
    roles = db.get_user_roles(user["id"])
    permissions = db.get_user_permissions(user["id"])
    return UserOut(
        id=user["id"],
        username=user["username"],
        email=user.get("email"),
        full_name=user.get("full_name"),
        is_active=bool(user["is_active"]),
        is_superadmin=bool(user["is_superadmin"]),
        created_at=user.get("created_at"),
        last_login=user.get("last_login"),
        roles=[r["name"] for r in roles],
        permissions=permissions,
    )


def _create_token_for_user(user_out: UserOut) -> str:
    """Create JWT access token with user claims."""
    return create_access_token({
        "sub": str(user_out.id),
        "username": user_out.username,
        "permissions": user_out.permissions,
        "is_superadmin": user_out.is_superadmin,
    })
