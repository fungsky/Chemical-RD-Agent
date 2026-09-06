"""审计日志 API"""

from fastapi import APIRouter, Depends, Query
from typing import Optional

from chem_agent.auth import database as db
from chem_agent.auth.dependencies import require_permission
from chem_agent.auth.models import AuditLogOut, UserOut

router = APIRouter(prefix="/api/admin/audit", tags=["审计日志"])


@router.get("")
async def query_logs(
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    _user: UserOut = Depends(require_permission("audit:read")),
):
    """查询审计日志（分页）。"""
    logs, total = db.query_audit_logs(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        page=page,
        limit=limit,
    )
    return {
        "items": [AuditLogOut(**log) for log in logs],
        "total": total,
        "page": page,
        "limit": limit,
    }
