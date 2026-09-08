"""统一状态中英文标签（仅用于展示，不改变存储值）。"""

REQUEST_STATUS_ZH = {
    "open": "待处理",
    "sampling": "打样中",
    "review": "评审中",
    "done": "已完成",
}

SAMPLE_STATUS_ZH = {
    "pending": "待反馈",
    "received": "已反馈",
}

EXPERIMENT_STATUS_ZH = {
    "planned": "计划中",
    "running": "进行中",
    "completed": "已完成",
    "failed": "失败",
    "cancelled": "已取消",
}

FORMULA_STATUS_ZH = {
    "draft": "草稿",
    "review": "审核中",
    "approved": "已通过",
    "archived": "已归档",
}


def translate(value, mapping: dict) -> str:
    """返回中文标签；未知值原样返回。"""
    if value is None:
        return ""
    return mapping.get(str(value), str(value))
