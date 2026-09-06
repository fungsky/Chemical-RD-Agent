"""系统配置管理 API"""

from fastapi import APIRouter, Depends

from chem_agent.auth import database as db
from chem_agent.auth.dependencies import require_permission
from chem_agent.auth.models import ConfigItem, ConfigUpdate, UserOut

router = APIRouter(prefix="/api/admin/config", tags=["系统配置"])


@router.get("", response_model=list[ConfigItem])
async def get_configs(_user: UserOut = Depends(require_permission("config:read"))):
    """获取所有系统配置。"""
    configs = db.get_all_configs()
    return [ConfigItem(key=c["key"], value=c["value"] or "", description=c.get("description")) for c in configs]


@router.put("")
async def update_configs(
    body: ConfigUpdate,
    current_user: UserOut = Depends(require_permission("config:write")),
):
    """批量更新系统配置。"""
    for item in body.configs:
        db.set_config(
            key=item.key,
            value=item.value,
            description=item.description,
            user_id=current_user.id,
        )
    db.log_audit(
        action="update_config",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="config",
        details={"keys": [c.key for c in body.configs]},
    )
    return {"message": f"已更新 {len(body.configs)} 项配置"}
