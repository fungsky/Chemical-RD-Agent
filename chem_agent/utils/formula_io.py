"""配方数据导入导出：Excel (4-Sheet) / JSON 格式转换。"""

import json
import logging
from io import BytesIO
from typing import Optional

import pandas as pd

from chem_agent.models.formula import (
    Formula,
    FormulaItem,
    MaterialFunction,
    PerformanceTest,
    ProcessCondition,
    ProductCategory,
    RawMaterial,
)

logger = logging.getLogger(__name__)

# ============ Excel 列定义 ============

_FORMULA_COLS = [
    "code", "name", "version", "category", "description",
    "target_application", "creator", "tags", "notes",
]
_ITEM_COLS = [
    "code", "material_name", "cas_number", "chemical_name",
    "supplier", "function", "weight_percent", "addition_order", "notes",
]
_PROCESS_COLS = [
    "code", "mixing_speed", "mixing_time", "temperature",
    "pressure", "curing_temperature", "curing_time", "notes",
]
_PERF_COLS = [
    "code", "test_name", "test_method", "value",
    "unit", "target_min", "target_max", "is_qualified",
]


# ============ 导出 ============


def formulas_to_excel(formulas: list[Formula]) -> BytesIO:
    """将配方列表转为 4-Sheet Excel 字节流。"""
    f_rows, i_rows, p_rows, perf_rows = [], [], [], []

    for f in formulas:
        code = f.code or f.name
        f_rows.append({
            "code": code,
            "name": f.name,
            "version": f.version,
            "category": f.category.value if isinstance(f.category, ProductCategory) else str(f.category),
            "description": f.description or "",
            "target_application": f.target_application or "",
            "creator": f.creator or "",
            "tags": ",".join(f.tags) if f.tags else "",
            "notes": f.notes or "",
        })
        for idx, item in enumerate(f.items):
            mat = item.material
            func_val = mat.function.value if isinstance(mat.function, MaterialFunction) else str(mat.function)
            i_rows.append({
                "code": code,
                "material_name": mat.name,
                "cas_number": mat.cas_number or "",
                "chemical_name": mat.chemical_name or "",
                "supplier": mat.supplier or "",
                "function": func_val,
                "weight_percent": item.weight_percent,
                "addition_order": item.addition_order if item.addition_order is not None else idx + 1,
                "notes": item.notes or "",
            })
        if f.process:
            proc = f.process
            p_rows.append({
                "code": code,
                "mixing_speed": proc.mixing_speed,
                "mixing_time": proc.mixing_time,
                "temperature": proc.temperature,
                "pressure": proc.pressure,
                "curing_temperature": proc.curing_temperature,
                "curing_time": proc.curing_time,
                "notes": proc.notes or "",
            })
        for pt in f.performance:
            perf_rows.append({
                "code": code,
                "test_name": pt.test_name,
                "test_method": pt.test_method or "",
                "value": pt.value,
                "unit": pt.unit or "",
                "target_min": pt.target_min,
                "target_max": pt.target_max,
                "is_qualified": pt.is_qualified,
            })

    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        pd.DataFrame(f_rows, columns=_FORMULA_COLS).to_excel(writer, sheet_name="formulas", index=False)
        pd.DataFrame(i_rows, columns=_ITEM_COLS).to_excel(writer, sheet_name="items", index=False)
        pd.DataFrame(p_rows, columns=_PROCESS_COLS).to_excel(writer, sheet_name="process", index=False)
        pd.DataFrame(perf_rows, columns=_PERF_COLS).to_excel(writer, sheet_name="performance", index=False)

        # 设置列宽
        for ws in writer.book.worksheets:
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = 18
            ws.freeze_panes = "A2"

    buf.seek(0)
    return buf


def formulas_to_json(formulas: list[Formula]) -> str:
    """将配方列表序列化为 JSON 字符串。"""
    data = []
    for f in formulas:
        d = f.model_dump(mode="json", exclude={"id"})
        # category / function 用 value
        if isinstance(f.category, ProductCategory):
            d["category"] = f.category.value
        for item in d.get("items", []):
            mat = item.get("material", {})
            func = mat.get("function")
            if isinstance(func, MaterialFunction):
                mat["function"] = func.value
        data.append(d)
    return json.dumps(data, ensure_ascii=False, indent=2)


# ============ 导入 ============


def excel_to_formulas(file_bytes: bytes) -> list[dict]:
    """解析 4-Sheet Excel 为配方字典列表（可直接传入 Formula 构造）。"""
    sheets = pd.read_excel(BytesIO(file_bytes), sheet_name=None, engine="openpyxl")

    df_formulas = sheets.get("formulas")
    if df_formulas is None or df_formulas.empty:
        raise ValueError("Excel 缺少 'formulas' Sheet 或内容为空")

    df_items = sheets.get("items", pd.DataFrame())
    df_process = sheets.get("process", pd.DataFrame())
    df_perf = sheets.get("performance", pd.DataFrame())

    # 按 code 分组
    items_map: dict[str, list] = {}
    if not df_items.empty:
        for _, row in df_items.iterrows():
            code = str(row.get("code", "")).strip()
            if not code:
                continue
            items_map.setdefault(code, []).append({
                "material": {
                    "name": str(row.get("material_name", "")).strip(),
                    "cas_number": _str_or_none(row.get("cas_number")),
                    "chemical_name": _str_or_none(row.get("chemical_name")),
                    "supplier": _str_or_none(row.get("supplier")),
                    "function": str(row.get("function", "其他")).strip(),
                },
                "weight_percent": float(row.get("weight_percent", 0)),
                "addition_order": _int_or_none(row.get("addition_order")),
                "notes": _str_or_none(row.get("notes")),
            })

    process_map: dict[str, dict] = {}
    if not df_process.empty:
        for _, row in df_process.iterrows():
            code = str(row.get("code", "")).strip()
            if not code:
                continue
            process_map[code] = {
                "mixing_speed": _float_or_none(row.get("mixing_speed")),
                "mixing_time": _float_or_none(row.get("mixing_time")),
                "temperature": _float_or_none(row.get("temperature")),
                "pressure": _float_or_none(row.get("pressure")),
                "curing_temperature": _float_or_none(row.get("curing_temperature")),
                "curing_time": _float_or_none(row.get("curing_time")),
                "notes": _str_or_none(row.get("notes")),
            }

    perf_map: dict[str, list] = {}
    if not df_perf.empty:
        for _, row in df_perf.iterrows():
            code = str(row.get("code", "")).strip()
            if not code:
                continue
            perf_map.setdefault(code, []).append({
                "test_name": str(row.get("test_name", "")).strip(),
                "test_method": _str_or_none(row.get("test_method")),
                "value": float(row.get("value", 0)),
                "unit": str(row.get("unit", "")),
                "target_min": _float_or_none(row.get("target_min")),
                "target_max": _float_or_none(row.get("target_max")),
                "is_qualified": _bool_or_none(row.get("is_qualified")),
            })

    result = []
    for _, row in df_formulas.iterrows():
        code = str(row.get("code", "")).strip()
        if not code:
            continue
        tags_raw = str(row.get("tags", "")).strip()
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []

        formula_dict = {
            "name": str(row.get("name", "")).strip(),
            "code": code,
            "version": str(row.get("version", "1.0")).strip(),
            "category": str(row.get("category", "其他")).strip(),
            "description": _str_or_none(row.get("description")),
            "target_application": _str_or_none(row.get("target_application")),
            "creator": _str_or_none(row.get("creator")),
            "tags": tags,
            "notes": _str_or_none(row.get("notes")),
            "items": items_map.get(code, []),
            "process": process_map.get(code),
            "performance": perf_map.get(code, []),
        }
        result.append(formula_dict)

    return result


def json_to_formulas(content: str) -> list[dict]:
    """解析 JSON 字符串为配方字典列表。"""
    data = json.loads(content)
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise ValueError("JSON 格式错误: 应为配方数组或单个配方对象")
    return data


# ============ 验证 ============


def validate_formula_data(data: dict) -> tuple[bool, Optional[str]]:
    """校验单条配方数据，返回 (is_valid, error_message)。"""
    name = data.get("name", "").strip()
    code = data.get("code", "").strip()
    if not name:
        return False, "缺少配方名称 (name)"
    if not code:
        return False, "缺少配方编号 (code)"

    items = data.get("items", [])
    if not items:
        return False, "配方组分为空 (items)"

    # 校验组分百分比
    total = sum(float(it.get("weight_percent", 0)) for it in items)
    if total > 0 and abs(total - 100.0) > 1.0:
        return False, f"组分百分比合计 {total:.1f}%，偏差超过 1%"

    # 校验组分原料名
    for i, it in enumerate(items):
        mat = it.get("material", {})
        if not mat.get("name", "").strip():
            return False, f"第 {i + 1} 个组分缺少原料名称"

    return True, None


# ============ 内部工具 ============


def _str_or_none(val) -> Optional[str]:
    if pd.isna(val) or val is None:
        return None
    s = str(val).strip()
    return s if s else None


def _float_or_none(val) -> Optional[float]:
    if pd.isna(val) or val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _int_or_none(val) -> Optional[int]:
    if pd.isna(val) or val is None:
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def _bool_or_none(val) -> Optional[bool]:
    if pd.isna(val) or val is None:
        return None
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    if s in ("true", "1", "是", "yes"):
        return True
    if s in ("false", "0", "否", "no"):
        return False
    return None
