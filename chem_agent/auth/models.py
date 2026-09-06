"""Auth Pydantic models for request/response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ============ User ============

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=4)


class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserOut(UserBase):
    id: int
    is_active: bool = True
    is_superadmin: bool = False
    created_at: Optional[str] = None
    last_login: Optional[str] = None
    roles: list[str] = []
    permissions: list[str] = []


class UserWithToken(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


# ============ Role ============

class RoleBase(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None


class RoleOut(RoleBase):
    id: int
    is_system: bool = False
    created_at: Optional[str] = None
    permissions: list[str] = []
    user_count: int = 0


# ============ Permission ============

class PermissionOut(BaseModel):
    id: int
    code: str
    resource: str
    action: str
    description: Optional[str] = None


# ============ Category ============

class CategoryBase(BaseModel):
    type: str  # "product" or "function"
    code: str
    display_zh: str
    display_en: str
    sort_order: int = 0
    is_enabled: bool = True


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    display_zh: Optional[str] = None
    display_en: Optional[str] = None
    sort_order: Optional[int] = None
    is_enabled: Optional[bool] = None


class CategoryOut(CategoryBase):
    id: int


# ============ Config ============

class ConfigItem(BaseModel):
    key: str
    value: str
    description: Optional[str] = None


class ConfigUpdate(BaseModel):
    configs: list[ConfigItem]


# ============ Audit Log ============

class AuditLogOut(BaseModel):
    id: int
    timestamp: Optional[str] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[str] = None
    status: str = "success"


class AuditLogQuery(BaseModel):
    user_id: Optional[int] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    page: int = 1
    limit: int = 50


# ============ Auth Requests ============

class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=4)


class RoleAssignRequest(BaseModel):
    role_ids: list[int]


class PermissionAssignRequest(BaseModel):
    permission_ids: list[int]
