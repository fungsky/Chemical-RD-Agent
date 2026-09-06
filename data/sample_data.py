"""化工配方知识图谱初始数据

包含 78 种常见化工原料（含CAS号、供应商、理化性质）和 18 个行业配方，
覆盖涂料(8)、胶粘剂(4)、密封剂(1)、橡胶(2)、塑料(2)、油墨(1)六大类。
"""

from data.materials_data import MATERIALS
from data.formulas_data import SAMPLE_FORMULAS

SAMPLE_MATERIALS = [{"name": m["name"], "cas_number": m.get("cas_number"), "chemical_name": m.get("chemical_name"), "supplier": m.get("supplier"), "function": m["function"]} for m in MATERIALS]

def get_all_sample_data() -> dict:
    """返回所有示例数据"""
    return {
        "materials": SAMPLE_MATERIALS,
        "formulas": SAMPLE_FORMULAS,
    }
