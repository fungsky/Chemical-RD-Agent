"""配方版本管理 UI 页面。"""

import json
import logging

import streamlit as st
import requests
import pandas as pd

from chem_agent.ui.i18n import t

logger = logging.getLogger(__name__)


def _api_base() -> str:
    import os
    return os.environ.get("API_BASE", "http://localhost:8000")


def render_formula_versions_page():
    """渲染配方版本历史与对比页面。"""
    st.title(t("formula_versions_title", "配方版本管理"))

    # 输入配方编号
    formula_code = st.text_input(
        t("formula_versions_code_label", "配方编号"),
        placeholder="例如: TEST-001",
    )

    if not formula_code:
        st.info(t("formula_versions_enter_code", "请输入配方编号查看版本历史。"))
        return

    # 获取版本列表
    try:
        resp = requests.get(f"{_api_base()}/api/formula-versions/{formula_code}", timeout=10)
        if resp.status_code == 404:
            st.warning(t("formula_versions_no_record", "该配方尚无版本记录。"))
            return
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        st.error(f"API 请求失败: {e}")
        return

    versions = data.get("versions", [])
    total = data.get("total_versions", 0)

    st.subheader(f"{formula_code} — {total} 个版本")

    if not versions:
        st.info(t("formula_versions_empty", "暂无版本记录。"))
        return

    # 版本列表表格
    df = pd.DataFrame([{
        "版本号": v["version_number"],
        "变更摘要": v.get("change_summary", "-"),
        "操作人": v.get("changed_by", "-"),
        "保存时间": v.get("created_at", "-"),
    } for v in versions])

    st.dataframe(df, use_container_width=True, hide_index=True)

    # 版本对比
    st.divider()
    st.subheader(t("formula_versions_diff_title", "版本对比"))

    col1, col2 = st.columns(2)
    version_numbers = [v["version_number"] for v in versions]
    max_ver = max(version_numbers) if version_numbers else 1
    min_ver = min(version_numbers) if version_numbers else 1

    with col1:
        v1 = st.selectbox(
            t("formula_versions_v1", "版本 A"),
            version_numbers,
            index=version_numbers.index(max_ver) if max_ver in version_numbers else 0,
        )
    with col2:
        v2 = st.selectbox(
            t("formula_versions_v2", "版本 B"),
            version_numbers,
            index=version_numbers.index(max_ver - 1) if (max_ver - 1) in version_numbers else 0,
        )

    if st.button(t("formula_versions_compare", "对比"), type="primary"):
        if v1 == v2:
            st.warning(t("formula_versions_same", "请选择两个不同版本进行对比。"))
        else:
            with st.spinner(t("formula_versions_loading", "正在对比...")):
                try:
                    diff_resp = requests.get(
                        f"{_api_base()}/api/formula-versions/{formula_code}/diff",
                        params={"v1": v1, "v2": v2},
                        timeout=15,
                    )
                    diff_resp.raise_for_status()
                    diff_data = diff_resp.json()
                    differences = diff_data.get("differences", [])

                    if not differences:
                        st.success(t("formula_versions_no_diff", "两个版本完全相同。"))
                    else:
                        diff_df = pd.DataFrame([{
                            "字段": d["field"],
                            "旧值": d.get("old_value", "(无)"),
                            "新值": d.get("new_value", "(无)"),
                            "变更类型": "修改" if d.get("changed") else ("新增" if d.get("added") else "删除"),
                        } for d in differences])
                        st.dataframe(diff_df, use_container_width=True, hide_index=True)

                except requests.RequestException as e:
                    st.error(f"对比请求失败: {e}")

    # 查看具体版本快照
    st.divider()
    st.subheader(t("formula_versions_snapshot", "版本快照查看"))

    selected_ver = st.selectbox(
        t("formula_versions_select", "选择版本"),
        version_numbers,
        key="snapshot_select",
    )

    if st.button(t("formula_versions_view", "查看快照"), type="secondary"):
        with st.spinner():
            try:
                snap_resp = requests.get(
                    f"{_api_base()}/api/formula-versions/{formula_code}/{selected_ver}",
                    timeout=10,
                )
                snap_resp.raise_for_status()
                snap_data = snap_resp.json()
                snapshot = snap_data.get("snapshot_data", {})
                if isinstance(snapshot, str):
                    snapshot = json.loads(snapshot)

                st.json(snapshot)

            except requests.RequestException as e:
                st.error(f"获取快照失败: {e}")