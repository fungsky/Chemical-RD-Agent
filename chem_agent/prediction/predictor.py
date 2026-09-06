"""配方性能预测模块 - 基于机器学习的性能预测"""

import logging
import pickle
from pathlib import Path
from typing import Optional

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import cross_val_score, cross_validate
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from chem_agent.models import (
    FormulaItem,
    MaterialFunction,
    PredictionRequest,
    PredictionResult,
    ProductCategory,
    RawMaterial,
)

logger = logging.getLogger(__name__)


class FormulaPredictor:
    """配方性能预测器

    基于历史配方数据训练 ML 模型，预测新配方的性能指标。

    特征工程:
      - 每种原料的质量百分比（稀疏向量）
      - 原料功能分类统计
      - 工艺条件数值
      - 产品类别 one-hot
    """

    def __init__(self, model_dir: Optional[str] = None):
        self._model_dir = Path(model_dir) if model_dir else Path("models")
        self._models: dict[str, GradientBoostingRegressor] = {}
        self._scalers: dict[str, StandardScaler] = {}
        self._material_index: dict[str, int] = {}
        self._function_index: dict[str, int] = {}
        self._category_index: dict[str, int] = {}
        self._is_fitted = False

    # ========== 特征工程 ==========

    def _build_feature_indices(self, formulas: list[dict]) -> None:
        """根据训练数据构建特征索引"""
        materials = set()
        functions = set()
        categories = set()

        for f in formulas:
            categories.add(f.get("category", "其他"))
            for item in f.get("items", []):
                materials.add(item["material_name"])
                functions.add(item.get("material_function", "其他"))

        self._material_index = {name: i for i, name in enumerate(sorted(materials))}
        self._function_index = {name: i for i, name in enumerate(sorted(functions))}
        self._category_index = {name: i for i, name in enumerate(sorted(categories))}

    def _formula_to_features(self, items: list[FormulaItem], category: str, process: Optional[dict] = None) -> np.ndarray:
        """将配方转换为特征向量"""
        n_materials = len(self._material_index)
        n_functions = len(self._function_index)
        n_categories = len(self._category_index)
        n_process = 6  # mixing_speed, mixing_time, temperature, pressure, curing_temp, curing_time

        features = np.zeros(n_materials + n_functions + n_categories + n_process)

        # 原料比例特征
        for item in items:
            name = item.material.name
            if name in self._material_index:
                features[self._material_index[name]] = item.weight_percent

        # 功能分类统计
        offset = n_materials
        for item in items:
            func = item.material.function.value
            if func in self._function_index:
                features[offset + self._function_index[func]] += item.weight_percent

        # 产品类别 one-hot
        offset += n_functions
        if category in self._category_index:
            features[offset + self._category_index[category]] = 1.0

        # 工艺条件
        offset += n_categories
        if process:
            process_fields = [
                "mixing_speed", "mixing_time", "temperature",
                "pressure", "curing_temperature", "curing_time",
            ]
            for i, field in enumerate(process_fields):
                val = process.get(field)
                if val is not None:
                    features[offset + i] = val

        return features

    # ========== 训练 ==========

    def train(self, training_data: list[dict], target_properties: list[str]) -> dict:
        """训练预测模型

        Args:
            training_data: 训练数据列表，每个元素格式:
                {
                    "category": "涂料",
                    "items": [{"material_name": "...", "material_function": "...", "weight_percent": 30.0}],
                    "process": {"temperature": 80, ...},
                    "performance": {"硬度": 85, "光泽度": 92, ...}
                }
            target_properties: 要预测的性能指标名称列表

        Returns:
            训练结果摘要
        """
        if not training_data:
            raise ValueError("训练数据不能为空")

        self._build_feature_indices(training_data)

        # 构建特征矩阵
        X_list = []
        y_dict = {prop: [] for prop in target_properties}
        valid_indices = {prop: [] for prop in target_properties}

        for idx, f_data in enumerate(training_data):
            items = [
                FormulaItem(
                    material=RawMaterial(
                        name=it["material_name"],
                        function=it.get("material_function", "其他"),
                    ),
                    weight_percent=it["weight_percent"],
                )
                for it in f_data.get("items", [])
            ]
            features = self._formula_to_features(
                items, f_data.get("category", "其他"), f_data.get("process")
            )
            X_list.append(features)

            for prop in target_properties:
                val = f_data.get("performance", {}).get(prop)
                if val is not None:
                    y_dict[prop].append(val)
                    valid_indices[prop].append(idx)

        X_all = np.array(X_list)
        results = {}

        for prop in target_properties:
            if len(y_dict[prop]) < 5:
                logger.warning("性能指标 '%s' 样本数不足 (%d)，跳过训练", prop, len(y_dict[prop]))
                results[prop] = {"status": "skipped", "reason": "样本不足", "count": len(y_dict[prop])}
                continue

            X_prop = X_all[valid_indices[prop]]
            y_prop = np.array(y_dict[prop])

            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X_prop)

            model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.1,
                random_state=42,
            )
            # 交叉验证评估
            cv_results = cross_validate(
                model, X_scaled, y_prop, cv=min(5, len(y_prop)),
                scoring=("r2", "neg_mean_absolute_error", "neg_root_mean_squared_error"),
                return_train_score=True,
            )
            model.fit(X_scaled, y_prop)

            # 训练集预测（用于完整评估）
            y_pred = model.predict(X_scaled)
            train_r2 = r2_score(y_prop, y_pred)
            train_mae = mean_absolute_error(y_prop, y_pred)
            train_rmse = float(mean_squared_error(y_prop, y_pred)) ** 0.5

            self._models[prop] = model
            self._scalers[prop] = scaler

            results[prop] = {
                "status": "trained",
                "samples": len(y_prop),
                "r2": round(float(train_r2), 4),
                "mae": round(float(train_mae), 4),
                "rmse": round(float(train_rmse), 4),
                "cv_r2_mean": round(float(cv_results["test_r2"].mean()), 4),
                "cv_r2_std": round(float(cv_results["test_r2"].std()), 4),
                "cv_mae_mean": round(float(-cv_results["test_neg_mean_absolute_error"].mean()), 4),
                "cv_rmse_mean": round(float(-cv_results["test_neg_root_mean_squared_error"].mean()), 4),
            }
            logger.info(
                "模型训练完成 - %s: R2=%.4f, MAE=%.4f, RMSE=%.4f, CV-R2=%.4f, 样本=%d",
                prop, train_r2, train_mae, train_rmse,
                cv_results["test_r2"].mean(), len(y_prop),
            )

        self._is_fitted = True
        return results

    # ========== 预测 ==========

    def predict(self, request: PredictionRequest) -> list[PredictionResult]:
        """预测配方性能"""
        if not self._is_fitted:
            raise RuntimeError("模型尚未训练，请先调用 train() 方法")

        features = self._formula_to_features(
            request.items,
            request.category.value,
            request.process.model_dump() if request.process else None,
        )

        results = []
        for prop in request.target_properties:
            if prop not in self._models:
                results.append(
                    PredictionResult(
                        property_name=prop,
                        predicted_value=0.0,
                        confidence=0.0,
                        explanation=f"没有 '{prop}' 的训练模型",
                    )
                )
                continue

            scaler = self._scalers[prop]
            model = self._models[prop]

            X = scaler.transform(features.reshape(1, -1))
            predicted = model.predict(X)[0]

            # 用各棵树的预测方差估算置信度
            tree_predictions = np.array(
                [tree[0].predict(X)[0] for tree in model.estimators_]
            )
            std = tree_predictions.std()
            mean_val = abs(predicted) if abs(predicted) > 1e-6 else 1.0
            cv = std / mean_val
            confidence = max(0.0, min(1.0, 1.0 - cv))

            results.append(
                PredictionResult(
                    property_name=prop,
                    predicted_value=round(float(predicted), 4),
                    confidence=round(float(confidence), 4),
                    explanation=f"基于 {len(model.estimators_)} 棵树的集成预测，变异系数 {cv:.4f}",
                )
            )

        return results

    # ========== 模型评估 ==========

    def evaluate(self, test_data: list[dict], target_properties: list[str]) -> dict:
        """在独立测试集上评估模型性能。

        Args:
            test_data: 测试数据，格式同 train()
            target_properties: 要评估的性能指标

        Returns:
            {property_name: {r2, mae, rmse, samples, predictions: [...]}}
        """
        if not self._is_fitted:
            raise RuntimeError("模型尚未训练，请先调用 train() 方法")

        # 构建测试特征
        X_list = []
        y_dict = {prop: [] for prop in target_properties}
        valid_indices = {prop: [] for prop in target_properties}

        for idx, f_data in enumerate(test_data):
            items = [
                FormulaItem(
                    material=RawMaterial(
                        name=it["material_name"],
                        function=it.get("material_function", "其他"),
                    ),
                    weight_percent=it["weight_percent"],
                )
                for it in f_data.get("items", [])
            ]
            features = self._formula_to_features(
                items, f_data.get("category", "其他"), f_data.get("process")
            )
            X_list.append(features)
            for prop in target_properties:
                val = f_data.get("performance", {}).get(prop)
                if val is not None:
                    y_dict[prop].append(val)
                    valid_indices[prop].append(idx)

        X_all = np.array(X_list)
        results = {}

        for prop in target_properties:
            if prop not in self._models:
                results[prop] = {"status": "no_model", "error": f"没有 '{prop}' 的模型"}
                continue

            if len(y_dict[prop]) < 2:
                results[prop] = {"status": "skipped", "reason": "测试样本不足"}
                continue

            X_prop = X_all[valid_indices[prop]]
            y_true = np.array(y_dict[prop])
            scaler = self._scalers[prop]
            X_scaled = scaler.transform(X_prop)
            y_pred = self._models[prop].predict(X_scaled)

            results[prop] = {
                "status": "evaluated",
                "samples": len(y_true),
                "r2": round(float(r2_score(y_true, y_pred)), 4),
                "mae": round(float(mean_absolute_error(y_true, y_pred)), 4),
                "rmse": round(float(mean_squared_error(y_true, y_pred, squared=False)), 4),
                "y_true": [round(float(v), 4) for v in y_true],
                "y_pred": [round(float(v), 4) for v in y_pred],
            }
            logger.info(
                "评估 %s: R2=%.4f, MAE=%.4f, RMSE=%.4f (n=%d)",
                prop, results[prop]["r2"], results[prop]["mae"],
                results[prop]["rmse"], len(y_true),
            )

        return results

    # ========== 持久化 ==========

    def save(self, path: Optional[str] = None) -> str:
        """保存模型到磁盘"""
        save_dir = Path(path) if path else self._model_dir
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = save_dir / "formula_predictor.pkl"

        data = {
            "models": self._models,
            "scalers": self._scalers,
            "material_index": self._material_index,
            "function_index": self._function_index,
            "category_index": self._category_index,
        }
        with open(save_path, "wb") as f:
            pickle.dump(data, f)

        logger.info("模型已保存至: %s", save_path)
        return str(save_path)

    def load(self, path: Optional[str] = None) -> None:
        """从磁盘加载模型"""
        load_dir = Path(path) if path else self._model_dir
        load_path = load_dir / "formula_predictor.pkl"

        if not load_path.exists():
            raise FileNotFoundError(f"模型文件不存在: {load_path}")

        with open(load_path, "rb") as f:
            data = pickle.load(f)

        self._models = data["models"]
        self._scalers = data["scalers"]
        self._material_index = data["material_index"]
        self._function_index = data["function_index"]
        self._category_index = data["category_index"]
        self._is_fitted = True

        logger.info("模型已加载: %s (包含 %d 个预测模型)", load_path, len(self._models))
