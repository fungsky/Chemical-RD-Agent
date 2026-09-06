from .auth_router import router as auth_router
from .user_router import router as user_router
from .role_router import router as role_router
from .category_router import router as category_router
from .config_router import router as config_router
from .audit_router import router as audit_router

__all__ = [
    "auth_router",
    "user_router",
    "role_router",
    "category_router",
    "config_router",
    "audit_router",
]
