"""实验数据管理 API 路由。"""

import logging

from fastapi import APIRouter, HTTPException, Query

from chem_agent.experiments import (
    ExperimentResult,
    ExperimentBatch,
    ExperimentQuery,
    ExperimentStatus,
    TrainingDataExport,
    ExperimentManager,
)
from chem_agent.experiments.manager import get_experiment_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/experiments", tags=["Experiments"])


def _manager() -> ExperimentManager:
    return get_experiment_manager()


@router.post("/results", response_model=ExperimentResult, summary="录入单条实验结果")
async def add_result(result: ExperimentResult):
    """录入一组实验的结果（可关联 DOE 运行序号）。"""
    try:
        return _manager().add_result(result)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error("添加实验结果失败: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/results/batch", summary="批量录入实验结果")
async def add_batch(batch: ExperimentBatch):
    """批量录入实验结果，如 DOE 全部运行的实测数据。"""
    try:
        results = _manager().add_batch(batch)
        return {
            "success": True,
            "batch_name": batch.batch_name,
            "count": len(results),
            "experiment_ids": [r.experiment_id for r in results],
        }
    except Exception as e:
        logger.error("批量添加失败: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/{experiment_id}", response_model=ExperimentResult, summary="查询单条实验结果")
async def get_result(experiment_id: str):
    result = _manager().get_result(experiment_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"实验 {experiment_id} 不存在")
    return result


@router.patch("/results/{experiment_id}", response_model=ExperimentResult, summary="更新实验结果")
async def update_result(experiment_id: str, updates: dict):
    try:
        return _manager().update_result(experiment_id, updates)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"实验 {experiment_id} 不存在")


@router.delete("/results/{experiment_id}", summary="删除实验结果")
async def delete_result(experiment_id: str):
    ok = _manager().delete_result(experiment_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"实验 {experiment_id} 不存在")
    return {"success": True}


@router.patch("/results/{experiment_id}/outlier", summary="标记/取消异常值")
async def mark_outlier(experiment_id: str, is_outlier: bool = True, reason: str = ""):
    try:
        result = _manager().mark_outlier(experiment_id, reason if is_outlier else "")
        return {"success": True, "is_outlier": result.is_outlier}
    except KeyError:
        raise HTTPException(status_code=404, detail=f"实验 {experiment_id} 不存在")


@router.post("/query", summary="条件查询实验记录")
async def query_experiments(q: ExperimentQuery):
    results = _manager().query(q)
    return {
        "total": len(results),
        "query": q.model_dump(exclude_none=True),
        "results": results,
    }


@router.get("/stats", summary="实验数据概览")
async def experiment_stats():
    return _manager().get_stats()


@router.get("/export/training-data", response_model=TrainingDataExport, summary="导出训练数据")
async def export_training_data(
    exclude_outliers: bool = Query(True, description="是否排除异常值"),
):
    """将实验数据导出为预测模型训练格式，可直接用于 POST /api/predict/train。"""
    return _manager().export_training_data(exclude_outliers=exclude_outliers)


@router.post("/reset", summary="清空所有实验数据")
async def reset_experiments():
    n = _manager().clear_all()
    return {"success": True, "deleted": n}

print("experiment_router done")
