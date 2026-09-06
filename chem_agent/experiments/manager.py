"""实验数据管理器 — 内存存储 + JSON持久化，不依赖外部数据库。"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from chem_agent.experiments.models import (
    ExperimentResult,
    ExperimentBatch,
    ExperimentQuery,
    ExperimentStatus,
    TrainingDataExport,
)

logger = logging.getLogger(__name__)


class ExperimentManager:
    """实验数据管理器。

    数据存储: JSON 文件持久化（data/experiments.json）
    生产环境可替换为 PostgreSQL/MySQL backend。
    """

    def __init__(self, data_dir: Optional[str] = None):
        self._data_dir = Path(data_dir or "data")
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._file = self._data_dir / "experiments.json"
        self._results: dict[str, ExperimentResult] = {}
        self._load()

    def _load(self):
        if self._file.exists():
            try:
                with open(self._file, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                self._results = {}
                for k, v in raw.items():
                    self._results[k] = ExperimentResult(**v)
                logger.info("加载了 %d 条实验记录", len(self._results))
            except Exception as e:
                logger.warning("加载实验数据失败: %s，使用空数据集", e)
                self._results = {}
        else:
            logger.info("实验数据文件不存在，初始化空数据集")

    def _save(self):
        raw = {k: v.model_dump(mode="json") for k, v in self._results.items()}
        with open(self._file, "w", encoding="utf-8") as f:
            json.dump(raw, f, ensure_ascii=False, indent=2, default=str)

    # ========== CRUD ==========

    def add_result(self, result: ExperimentResult) -> ExperimentResult:
        """添加单条实验结果。"""
        if result.experiment_id in self._results:
            raise ValueError(f"实验编号 {result.experiment_id} 已存在")
        self._results[result.experiment_id] = result
        self._save()
        logger.info("实验记录已保存: %s (%d 项测量)", result.experiment_id, len(result.measurements))
        return result

    def add_batch(self, batch: ExperimentBatch) -> list[ExperimentResult]:
        """批量添加实验结果。"""
        added = []
        for result in batch.results:
            result.project = batch.project or result.project
            result.batch_number = batch.batch_name or result.batch_number
            self.add_result(result)
            added.append(result)
        logger.info("批次 %s: 已录入 %d 条实验记录", batch.batch_name, len(added))
        return added

    def get_result(self, experiment_id: str) -> Optional[ExperimentResult]:
        return self._results.get(experiment_id)

    def update_result(self, experiment_id: str, updates: dict) -> ExperimentResult:
        """更新实验结果（部分字段）。"""
        if experiment_id not in self._results:
            raise KeyError(f"实验编号 {experiment_id} 不存在")
        current = self._results[experiment_id]
        update_data = current.model_dump()
        update_data.update(updates)
        update_data["updated_at"] = datetime.now()
        self._results[experiment_id] = ExperimentResult(**update_data)
        self._save()
        return self._results[experiment_id]

    def delete_result(self, experiment_id: str) -> bool:
        if experiment_id in self._results:
            del self._results[experiment_id]
            self._save()
            return True
        return False

    def mark_outlier(self, experiment_id: str, reason: str) -> ExperimentResult:
        return self.update_result(experiment_id, {
            "is_outlier": True,
            "outlier_reason": reason,
        })

    # ========== 查询 ==========

    def query(self, q: ExperimentQuery) -> list[ExperimentResult]:
        """按条件查询实验记录。"""
        results = list(self._results.values())

        if q.project:
            results = [r for r in results if q.project.lower() in r.project.lower()]
        if q.formula_name:
            results = [r for r in results if q.formula_name.lower() in r.formula_name.lower()]
        if q.status:
            results = [r for r in results if r.status == q.status]
        if q.date_from:
            results = [r for r in results if r.created_at >= q.date_from]
        if q.date_to:
            results = [r for r in results if r.created_at <= q.date_to]
        if q.has_measurement:
            results = [r for r in results if q.has_measurement in r.measurements]
        if not q.include_outliers:
            results = [r for r in results if not r.is_outlier]

        return results[:q.limit]

    def list_all(self) -> list[ExperimentResult]:
        return list(self._results.values())

    def count(self) -> int:
        return len(self._results)

    def clear_all(self) -> int:
        n = len(self._results)
        self._results.clear()
        self._save()
        return n

    # ========== 统计 ==========

    def get_stats(self) -> dict:
        """获取实验数据概览。"""
        all_results = list(self._results.values())
        if not all_results:
            return {"total": 0}

        projects = set(r.project for r in all_results if r.project)
        statuses = {}
        for r in all_results:
            statuses[r.status.value] = statuses.get(r.status.value, 0) + 1

        all_measurements = set()
        for r in all_results:
            all_measurements.update(r.measurements.keys())

        outliers = sum(1 for r in all_results if r.is_outlier)

        return {
            "total": len(all_results),
            "projects": sorted(projects),
            "status_breakdown": statuses,
            "measurement_types": sorted(all_measurements),
            "outliers": outliers,
            "latest_entry": max(r.created_at for r in all_results).isoformat() if all_results else None,
        }

    # ========== 训练数据导出 ==========

    def export_training_data(self, exclude_outliers: bool = True) -> TrainingDataExport:
        """将实验数据导出为预测模型训练格式。"""
        training_data = []
        excluded_outliers = 0
        excluded_incomplete = 0
        target_properties = set()

        for result in self._results.values():
            if exclude_outliers and result.is_outlier:
                excluded_outliers += 1
                continue

            if not result.measurements:
                excluded_incomplete += 1
                continue

            items = []
            for item in result.condition.items:
                items.append({
                    "material_name": item.get("material_name", ""),
                    "material_function": item.get("material_function", "其他"),
                    "weight_percent": item.get("weight_percent", 0),
                })

            if not items:
                excluded_incomplete += 1
                continue

            target_properties.update(result.measurements.keys())

            training_data.append({
                "category": "",
                "items": items,
                "process": result.condition.process,
                "performance": result.measurements,
                "source": "experiment",
                "experiment_id": result.experiment_id,
            })

        return TrainingDataExport(
            total_experiments=len(self._results),
            total_measurements=len(training_data),
            target_properties=sorted(target_properties),
            training_data=training_data,
            excluded_outliers=excluded_outliers,
            excluded_incomplete=excluded_incomplete,
        )


# 全局单例
_experiment_manager: Optional[ExperimentManager] = None


def get_experiment_manager() -> ExperimentManager:
    global _experiment_manager
    if _experiment_manager is None:
        _experiment_manager = ExperimentManager()
    return _experiment_manager
