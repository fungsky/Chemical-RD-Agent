"""数据初始化脚本 - 将示例数据导入知识图谱"""

import sys
import logging
from pathlib import Path

# 将项目根目录添加到 path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from chem_agent.knowledge_graph import KnowledgeGraphService
from chem_agent.models import (
    RawMaterial,
    Formula,
    FormulaItem,
    PerformanceTest,
    ProcessCondition,
)
from data.sample_data import get_all_sample_data

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def init_knowledge_graph():
    """初始化知识图谱"""
    kg = KnowledgeGraphService()
    kg.connect()
    kg.init_schema()

    sample = get_all_sample_data()

    # 1) 导入原材料
    logger.info("正在导入 %d 种原材料...", len(sample["materials"]))
    for mat_data in sample["materials"]:
        material = RawMaterial(**mat_data)
        kg.upsert_material(material)
    logger.info("原材料导入完成")

    # 2) 导入配方
    logger.info("正在导入 %d 个配方...", len(sample["formulas"]))
    for f_data in sample["formulas"]:
        items = []
        for item_data in f_data.get("items", []):
            mat = RawMaterial(
                name=item_data["material"]["name"],
                function=item_data["material"]["function"],
            )
            items.append(
                FormulaItem(
                    material=mat,
                    weight_percent=item_data["weight_percent"],
                    addition_order=item_data.get("addition_order"),
                )
            )

        process = None
        if f_data.get("process"):
            process = ProcessCondition(**f_data["process"])

        perfs = []
        for p_data in f_data.get("performance", []):
            perfs.append(PerformanceTest(**p_data))

        formula = Formula(
            name=f_data["name"],
            code=f_data["code"],
            version=f_data.get("version", "1.0"),
            category=f_data["category"],
            description=f_data.get("description"),
            items=items,
            process=process,
            performance=perfs,
            target_application=f_data.get("target_application"),
            creator=f_data.get("creator"),
            tags=f_data.get("tags", []),
        )
        kg.upsert_formula(formula)
        logger.info("已导入配方: %s", formula.name)

    logger.info("配方导入完成")

    # 3) 打印统计
    stats = kg.get_graph_stats()
    logger.info("知识图谱统计: %s", stats)

    kg.close()
    logger.info("初始化完成！")


if __name__ == "__main__":
    init_knowledge_graph()
