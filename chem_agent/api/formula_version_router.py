"""配方版本管理 API 路由。"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from chem_agent.auth import database as db
from chem_agent.auth.dependencies import require_permission
from chem_agent.auth.models import UserOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/formula-versions", tags=["Formula Versions"])


class SaveVersionRequest(BaseModel):
    formula_code: str = Field(..., description="配方编号")
    snapshot_data: dict = Field(..., description="配方快照数据")
    change_summary: Optional[str] = Field(None, description="变更摘要")
    changed_by: Optional[str] = Field(None, description="操作人")


class VersionResponse(BaseModel):
    id: int
    formula_code: str
    version_number: int
    snapshot_data: dict
    change_summary: Optional[str] = None
    changed_by: Optional[str] = None
    created_at: Optional[str] = None


@router.post("/save", summary="保存配方版本")
async def save_version(req: SaveVersionRequest, current_user: UserOut = Depends(require_permission("formula:write"))):
    """保存配方快照，自动递增版本号。"""
    try:
        version_number = db.save_formula_version(
            formula_code=req.formula_code,
            snapshot_data=req.snapshot_data,
            change_summary=req.change_summary,
            changed_by=current_user.username,
        )
        return {
            "success": True,
            "formula_code": req.formula_code,
            "version_number": version_number,
        }
    except Exception as e:
        logger.error("Failed to save version: %s", e)
        raise HTTPException(status_code=500, detail=f"保存版本失败: {e}")


@router.get("/{formula_code}", summary="获取配方版本历史")
async def list_versions(formula_code: str, _user: UserOut = Depends(require_permission("formula:read"))):
    """获取指定配方的所有版本历史。"""
    try:
        versions = db.get_formula_versions(formula_code)
        return {
            "formula_code": formula_code,
            "total_versions": len(versions),
            "versions": versions,
        }
    except Exception as e:
        logger.error("Failed to get versions: %s", e)
        raise HTTPException(status_code=500, detail=f"获取版本历史失败: {e}")


@router.get("/{formula_code}/{version_number}", summary="获取配方指定版本")
async def get_version(formula_code: str, version_number: int, _user: UserOut = Depends(require_permission("formula:read"))):
    """获取配方某个版本的快照。"""
    try:
        version = db.get_formula_version(formula_code, version_number)
        if not version:
            raise HTTPException(status_code=404, detail=f"版本 {version_number} 不存在")
        return version
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get version: %s", e)
        raise HTTPException(status_code=500, detail=f"获取版本失败: {e}")


@router.get("/{formula_code}/latest", summary="获取配方最新版本")
async def get_latest_version(formula_code: str, _user: UserOut = Depends(require_permission("formula:read"))):
    """获取配方最新版本的快照。"""
    try:
        version = db.get_latest_formula_version(formula_code)
        if not version:
            raise HTTPException(status_code=404, detail="该配方尚无版本记录")
        return version
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get latest version: %s", e)
        raise HTTPException(status_code=500, detail=f"获取最新版本失败: {e}")


@router.get("/{formula_code}/diff", summary="配方版本对比")
async def diff_versions(
    formula_code: str,
    v1: int = Query(..., description="版本号 A"),
    v2: int = Query(..., description="版本号 B"),
    _user: UserOut = Depends(require_permission("formula:read")),
):
    """对比两个版本的配方差异。"""
    try:
        ver1 = db.get_formula_version(formula_code, v1)
        ver2 = db.get_formula_version(formula_code, v2)
        if not ver1:
            raise HTTPException(status_code=404, detail=f"版本 {v1} 不存在")
        if not ver2:
            raise HTTPException(status_code=404, detail=f"版本 {v2} 不存在")

        snap1 = json.loads(ver1["snapshot_data"]) if isinstance(ver1["snapshot_data"], str) else ver1["snapshot_data"]
        snap2 = json.loads(ver2["snapshot_data"]) if isinstance(ver2["snapshot_data"], str) else ver2["snapshot_data"]

        diffs = _compute_diff(snap1, snap2)

        return {
            "formula_code": formula_code,
            "version_a": {"number": v1, "created_at": ver1.get("created_at")},
            "version_b": {"number": v2, "created_at": ver2.get("created_at")},
            "differences": diffs,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to diff versions: %s", e)
        raise HTTPException(status_code=500, detail=f"版本对比失败: {e}")


def _compute_diff(snap1: dict, snap2: dict) -> dict:
    """化工配方语义差异对比。

    对比两个配方版本的：
    - 组分变化（新增/删除/替换/比例漂移）
    - 工艺条件漂移（温度/时间/转速变化）
    - 性能指标变化
    - 基础信息变更

    Returns:
        {
            "summary": "一句话变化摘要",
            "material_changes": [...],
            "process_changes": [...],
            "performance_changes": [...],
            "info_changes": [...],
        }
    """
    items1 = {it["material"]["name"]: it for it in snap1.get("items", [])}
    items2 = {it["material"]["name"]: it for it in snap2.get("items", [])}

    material_changes = []
    all_mats = set(items1.keys()) | set(items2.keys())

    for mat_name in sorted(all_mats):
        in_v1 = mat_name in items1
        in_v2 = mat_name in items2

        if in_v1 and not in_v2:
            material_changes.append({
                "type": "removed",
                "material": mat_name,
                "function": items1[mat_name]["material"].get("function", ""),
                "old_weight": items1[mat_name]["weight_percent"],
                "new_weight": 0,
                "weight_delta": -items1[mat_name]["weight_percent"],
            })
        elif not in_v1 and in_v2:
            material_changes.append({
                "type": "added",
                "material": mat_name,
                "function": items2[mat_name]["material"].get("function", ""),
                "old_weight": 0,
                "new_weight": items2[mat_name]["weight_percent"],
                "weight_delta": +items2[mat_name]["weight_percent"],
            })
        else:
            w1 = items1[mat_name]["weight_percent"]
            w2 = items2[mat_name]["weight_percent"]
            delta = w2 - w1
            if abs(delta) > 2.0:
                material_changes.append({
                    "type": "modified",
                    "material": mat_name,
                    "function": items1[mat_name]["material"].get("function", ""),
                    "old_weight": round(w1, 1),
                    "new_weight": round(w2, 1),
                    "weight_delta": round(delta, 1),
                    "delta_pct": round(delta / max(w1, 0.1) * 100, 1),
                })

    # 检测功能替换
    funcs1 = {items1[m]["material"].get("function", "") for m in items1}
    funcs2 = {items2[m]["material"].get("function", "") for m in items2}
    func_added = funcs2 - funcs1
    func_removed = funcs1 - funcs2
    if func_added:
        material_changes.append({
            "type": "function_added",
            "material": ", ".join(func_added),
            "old_weight": 0, "new_weight": 0, "weight_delta": 0,
        })
    if func_removed:
        material_changes.append({
            "type": "function_removed",
            "material": ", ".join(func_removed),
            "old_weight": 0, "new_weight": 0, "weight_delta": 0,
        })

    # 工艺变化
    process_changes = []
    p1 = snap1.get("process") or {}
    p2 = snap2.get("process") or {}
    proc_fields = {
        "mixing_speed": ("搅拌速度", "rpm", 50),
        "mixing_time": ("搅拌时间", "min", 5),
        "temperature": ("反应温度", "°C", 5),
        "curing_temperature": ("固化温度", "°C", 5),
        "curing_time": ("固化时间", "h", 0.5),
    }
    for key, (label, unit, threshold) in proc_fields.items():
        v1 = p1.get(key)
        v2 = p2.get(key)
        if v1 is not None and v2 is not None and abs(v2 - v1) > threshold:
            process_changes.append({
                "field": label,
                "unit": unit,
                "old_value": v1,
                "new_value": v2,
                "delta": round(v2 - v1, 1),
                "direction": "increase" if v2 > v1 else "decrease",
            })
        elif v1 is not None and v2 is None:
            process_changes.append({
                "field": label, "unit": unit,
                "old_value": v1, "new_value": None,
                "type": "removed",
            })
        elif v1 is None and v2 is not None:
            process_changes.append({
                "field": label, "unit": unit,
                "old_value": None, "new_value": v2,
                "type": "added",
            })

    # 性能变化
    performance_changes = []
    perf1 = {p.get("test_name", ""): p for p in (snap1.get("performance") or [])}
    perf2 = {p.get("test_name", ""): p for p in (snap2.get("performance") or [])}
    for test_name in set(perf1.keys()) | set(perf2.keys()):
        if test_name in perf1 and test_name in perf2:
            v1 = perf1[test_name].get("value")
            v2 = perf2[test_name].get("value")
            if v1 is not None and v2 is not None and abs(v2 - v1) > 0.01:
                performance_changes.append({
                    "test": test_name,
                    "old_value": v1,
                    "new_value": v2,
                    "delta": round(v2 - v1, 2),
                    "improved": v2 > v1,
                })

    # 基础信息变化
    info_changes = []
    for key in ["name", "description", "category", "version", "target_application"]:
        v1 = snap1.get(key)
        v2 = snap2.get(key)
        if v1 != v2 and (v1 or v2):
            info_changes.append({
                "field": key,
                "old_value": str(v1)[:200] if v1 else None,
                "new_value": str(v2)[:200] if v2 else None,
            })

    # 生成摘要
    parts = []
    if material_changes:
        n = len([c for c in material_changes if c["type"] in ("added", "removed", "modified")])
        parts.append(f"{n} 个组分变更")
    if process_changes:
        parts.append(f"{len(process_changes)} 个工艺参数调整")
    if performance_changes:
        improved = sum(1 for c in performance_changes if c["improved"])
        parts.append(f"{len(performance_changes)} 个性能指标变化 ({improved} 改善)")
    summary = "；".join(parts) if parts else "无显著变化"

    return {
        "summary": summary,
        "material_changes": material_changes,
        "process_changes": process_changes,
        "performance_changes": performance_changes,
        "info_changes": info_changes,
    }
