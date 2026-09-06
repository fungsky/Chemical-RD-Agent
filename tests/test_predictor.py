"""测试 - 配方性能预测器"""

import pytest
import numpy as np

from chem_agent.prediction import FormulaPredictor
from chem_agent.models import (
    FormulaItem,
    RawMaterial,
    PredictionRequest,
    ProductCategory,
    MaterialFunction,
)


def make_training_data(n=30):
    """生成模拟训练数据"""
    rng = np.random.RandomState(42)
    data = []
    materials = ["树脂A", "填料B", "溶剂C", "助剂D", "固化剂E"]
    functions = ["基础树脂", "填料", "溶剂", "其他", "固化剂"]

    for i in range(n):
        percents = rng.dirichlet(np.ones(5)) * 100
        items = [
            {
                "material_name": materials[j],
                "material_function": functions[j],
                "weight_percent": round(float(percents[j]), 1),
            }
            for j in range(5)
        ]
        # 模拟：硬度与树脂含量正相关，光泽与填料负相关
        hardness = 40 + 0.8 * percents[0] - 0.2 * percents[1] + rng.normal(0, 3)
        gloss = 90 - 0.5 * percents[1] + 0.3 * percents[0] + rng.normal(0, 4)

        data.append({
            "category": "涂料",
            "items": items,
            "performance": {"硬度": round(hardness, 1), "光泽度": round(gloss, 1)},
        })
    return data


class TestFormulaPredictor:
    def test_train_and_predict(self, tmp_path):
        predictor = FormulaPredictor(model_dir=str(tmp_path))

        training_data = make_training_data(30)
        results = predictor.train(training_data, ["硬度", "光泽度"])

        assert "硬度" in results
        assert results["硬度"]["status"] == "trained"
        assert results["光泽度"]["status"] == "trained"

        # 预测
        items = [
            FormulaItem(
                material=RawMaterial(name="树脂A", function=MaterialFunction.BASE_RESIN),
                weight_percent=40.0,
            ),
            FormulaItem(
                material=RawMaterial(name="填料B", function=MaterialFunction.FILLER),
                weight_percent=20.0,
            ),
        ]
        request = PredictionRequest(
            items=items,
            category=ProductCategory.COATING,
            target_properties=["硬度", "光泽度"],
        )
        predictions = predictor.predict(request)
        assert len(predictions) == 2
        assert predictions[0].property_name == "硬度"
        assert predictions[0].predicted_value > 0

    def test_save_and_load(self, tmp_path):
        predictor = FormulaPredictor(model_dir=str(tmp_path))
        training_data = make_training_data(30)
        predictor.train(training_data, ["硬度"])
        predictor.save()

        predictor2 = FormulaPredictor(model_dir=str(tmp_path))
        predictor2.load()
        assert predictor2._is_fitted

    def test_insufficient_data(self):
        predictor = FormulaPredictor()
        data = make_training_data(3)  # 太少
        results = predictor.train(data, ["硬度"])
        assert results["硬度"]["status"] == "skipped"

    def test_predict_without_training(self):
        predictor = FormulaPredictor()
        items = [
            FormulaItem(
                material=RawMaterial(name="test", function=MaterialFunction.OTHER),
                weight_percent=50.0,
            ),
        ]
        request = PredictionRequest(
            items=items,
            category=ProductCategory.OTHER,
            target_properties=["硬度"],
        )
        with pytest.raises(RuntimeError, match="尚未训练"):
            predictor.predict(request)
