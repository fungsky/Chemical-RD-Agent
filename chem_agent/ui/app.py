"""ChemAgent Streamlit 前端界面 - 支持中英文切换 & 结构化表格录入 & 认证"""

import os

import pandas as pd
import requests
import streamlit as st
import plotly.graph_objects as go
import numpy as np

from chem_agent.ui.i18n import (
    CATEGORY_KEYS,
    FUNCTION_KEYS,
    TRANSLATIONS,
)

# ============ 配置 ============

API_BASE = os.environ.get("API_BASE", "http://localhost:8000")

st.set_page_config(
    page_title="ChemAgent",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============ 样式 ============

st.markdown(
    """
<style>
    .main-header {
        font-size: 2em;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5em;
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.2em;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .stat-number { font-size: 2em; font-weight: bold; }
    .stat-label { font-size: 0.9em; opacity: 0.9; }
    .formula-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1em;
        margin: 0.5em 0;
        background: #fafafa;
    }
    /* Agent 推理步骤卡片 */
    .agent-step-card {
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
        border-left: 4px solid;
        font-size: 0.95em;
        line-height: 1.6;
    }
    .agent-step-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 6px;
        font-weight: 600;
        font-size: 0.92em;
    }
    .agent-step-number {
        background: rgba(0,0,0,0.55);
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8em;
        font-weight: 500;
    }
    .step-thought {
        border-left-color: #9333ea;
        background: rgba(147,51,234,0.08);
    }
    .step-action {
        border-left-color: #f97316;
        background: rgba(249,115,22,0.08);
    }
    .step-observation {
        border-left-color: #10b981;
        background: rgba(16,185,129,0.08);
    }
    .step-reflection {
        border-left-color: #f59e0b;
        background: rgba(245,158,11,0.08);
    }
    .step-planning {
        border-left-color: #3b82f6;
        background: rgba(59,130,246,0.08);
    }
    .step-error {
        border-left-color: #ef4444;
        background: rgba(239,68,68,0.08);
    }
    .step-answer {
        border-left-color: #6366f1;
        background: rgba(99,102,241,0.08);
    }
    .step-default {
        border-left-color: #6b7280;
        background: rgba(107,114,128,0.08);
    }
    .planning-list {
        margin: 8px 0 0 0;
        padding-left: 24px;
        list-style-type: none;
        counter-reset: plan-counter;
    }
    .planning-list li {
        counter-increment: plan-counter;
        position: relative;
        padding-left: 8px;
        margin-bottom: 6px;
    }
    .planning-list li::before {
        content: counter(plan-counter) ".";
        position: absolute;
        left: -20px;
        font-weight: 600;
        color: #3b82f6;
    }

    /* ====== Hero 品牌区域 ====== */
    .hero-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5em 2em;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 1.5em;
        color: white;
    }
    .hero-title { font-size: 2.5em; font-weight: 700; margin-bottom: 0.2em; }
    .hero-subtitle { font-size: 1.15em; opacity: 0.92; }

    /* ====== 页面描述区 ====== */
    .page-desc {
        background: #f0f4ff;
        border-left: 4px solid #667eea;
        padding: 0.8em 1.2em;
        border-radius: 0 8px 8px 0;
        margin-bottom: 1.2em;
        color: #4a5568 !important;
        font-size: 0.95em;
        line-height: 1.6;
    }

    /* ====== 功能卡片 ====== */
    .feature-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1.2em;
        text-align: center;
        transition: all 0.2s ease;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        min-height: 140px;
        margin-bottom: 0.8em;
        color: #2d3748 !important;
    }
    .feature-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border-color: #667eea;
    }
    .feature-icon { font-size: 2em; margin-bottom: 0.3em; }
    .feature-name { font-weight: 600; font-size: 1em; margin-bottom: 0.3em; color: #2d3748 !important; }
    .feature-desc { font-size: 0.85em; color: #718096 !important; line-height: 1.4; }

    /* ====== 侧边栏品牌 ====== */
    .sidebar-brand {
        text-align: center;
        padding: 0.5em 0 0.8em;
    }
    .sidebar-brand-name {
        font-size: 1.6em;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .sidebar-brand-slogan { font-size: 0.8em; color: #718096; margin-top: 0.2em; }

    /* ====== 侧边栏版权 ====== */
    .sidebar-copyright {
        text-align: center;
        color: #a0aec0;
        font-size: 0.75em;
        padding: 1em 0 0.5em;
        border-top: 1px solid #e2e8f0;
        margin-top: 1em;
    }

    /* ====== 登录页版权 ====== */
    .login-copyright {
        text-align: center;
        color: #a0aec0;
        font-size: 0.82em;
        margin-top: 2em;
    }

    /* ====== Section 标题 ====== */
    .section-title {
        font-size: 1.15em;
        font-weight: 600;
        color: #667eea !important;
        padding-bottom: 0.4em;
        border-bottom: 2px solid #667eea;
        margin-bottom: 0.8em;
        display: inline-block;
    }

    /* ====== 渐入动画 ====== */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .fade-in { animation: fadeInUp 0.4s ease-out; }

    /* ====== Guide 功能卡片（左对齐） ====== */
    .guide-feature-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1em 1.2em;
        text-align: left;
        transition: all 0.2s ease;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        margin-bottom: 0.8em;
        line-height: 1.6;
        color: #2d3748 !important;
    }
    .guide-feature-card strong {
        color: #2d3748 !important;
    }
    .guide-feature-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border-color: #667eea;
    }
</style>
""",
    unsafe_allow_html=True,
)


# ============ i18n 工具 ============


def _get_lang() -> str:
    return st.session_state.get("lang", "zh")


def t(key: str) -> str:
    """获取当前语言的翻译文本"""
    entry = TRANSLATIONS.get(key)
    if entry is None:
        return key
    return entry.get(_get_lang(), entry.get("zh", key))


def t_fmt(key: str, *args) -> str:
    """获取翻译文本并格式化"""
    return t(key).format(*args)


def _fetch_dynamic_categories(cat_type: str) -> list[dict] | None:
    """从后端获取动态分类列表，返回 [{display_zh, display_en, code}, ...] 或 None。"""
    cache_key = f"_dyn_cats_{cat_type}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]
    try:
        result = api_call("get", f"/api/admin/categories?type={cat_type}")
        if result and isinstance(result, list):
            enabled = [c for c in result if c.get("is_enabled", True)]
            enabled.sort(key=lambda c: c.get("sort_order", 0))
            st.session_state[cache_key] = enabled
            return enabled
    except Exception:
        pass
    return None


def _category_options(include_all: bool = False) -> list[str]:
    """返回当前语言的产品类别显示列表（优先后端动态数据）"""
    opts = []
    if include_all:
        opts.append(t("search_all"))
    dynamic = _fetch_dynamic_categories("product")
    if dynamic:
        lang = _get_lang()
        for c in dynamic:
            opts.append(c.get(f"display_{lang}") or c.get("display_zh", c.get("code", "")))
    else:
        for k in CATEGORY_KEYS:
            opts.append(t(k))
    return opts


def _category_to_api(display: str) -> str:
    """将显示名称转换为后端 API 值（始终为中文）"""
    dynamic = _fetch_dynamic_categories("product")
    if dynamic:
        lang = _get_lang()
        for c in dynamic:
            if display == c.get(f"display_{lang}") or display == c.get("display_zh"):
                return c.get("display_zh", display)
        return display
    for k in CATEGORY_KEYS:
        entry = TRANSLATIONS[k]
        if display == entry.get(_get_lang()):
            return entry["zh"]
    return display


def _function_options(include_all: bool = False) -> list[str]:
    """返回当前语言的功能分类显示列表（优先后端动态数据）"""
    opts = []
    if include_all:
        opts.append(t("search_all"))
    dynamic = _fetch_dynamic_categories("function")
    if dynamic:
        lang = _get_lang()
        for c in dynamic:
            opts.append(c.get(f"display_{lang}") or c.get("display_zh", c.get("code", "")))
    else:
        for k in FUNCTION_KEYS:
            opts.append(t(k))
    return opts


def _function_to_api(display: str) -> str:
    """将功能分类显示名称转换为后端 API 值"""
    dynamic = _fetch_dynamic_categories("function")
    if dynamic:
        lang = _get_lang()
        for c in dynamic:
            if display == c.get(f"display_{lang}") or display == c.get("display_zh"):
                return c.get("display_zh", display)
        return display
    for k in FUNCTION_KEYS:
        entry = TRANSLATIONS[k]
        if display == entry.get(_get_lang()):
            return entry["zh"]
    return display


# ============ API 工具 ============


def api_call(method: str, endpoint: str, **kwargs) -> dict | list | None:
    """调用后端 API（自动附带认证 token）"""
    try:
        url = f"{API_BASE}{endpoint}"
        headers = kwargs.pop("headers", {})
        # LLM 密集型接口使用更长超时
        _llm_endpoints = ("/chat", "/analyze", "/recommend", "/substitute", "/report", "/summary")
        default_timeout = 180 if any(p in endpoint for p in _llm_endpoints) else 60
        timeout = kwargs.pop("timeout", default_timeout)
        token = st.session_state.get("access_token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        resp = getattr(requests, method)(url, timeout=timeout, headers=headers, **kwargs)
        # 如果 401 且有 refresh_token，尝试刷新
        if resp.status_code == 401 and st.session_state.get("refresh_token"):
            new_tokens = _try_refresh_token()
            if new_tokens:
                headers["Authorization"] = f"Bearer {new_tokens['access_token']}"
                resp = getattr(requests, method)(url, timeout=timeout, headers=headers, **kwargs)
            else:
                _clear_auth()
                st.warning(t("session_expired"))
                st.rerun()
                return None
        resp.raise_for_status()
        return resp.json()
    except requests.ConnectionError:
        st.error(t_fmt("conn_error", API_BASE))
        return None
    except requests.HTTPError as e:
        detail = ""
        try:
            err_body = e.response.json()
            # 优先使用统一错误处理返回的 message
            detail = err_body.get("message") or err_body.get("detail", e.response.text)
        except Exception:
            detail = e.response.text
        st.error(t_fmt("api_error", detail))
        return None
    except Exception as e:
        st.error(t_fmt("request_failed", e))
        return None


def _try_refresh_token() -> dict | None:
    """尝试用 refresh_token 获取新令牌"""
    try:
        resp = requests.post(
            f"{API_BASE}/api/auth/refresh",
            json={"refresh_token": st.session_state.get("refresh_token", "")},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            st.session_state["access_token"] = data["access_token"]
            st.session_state["refresh_token"] = data["refresh_token"]
            st.session_state["user_info"] = data["user"]
            return data
    except Exception:
        pass
    return None


def _clear_auth():
    """清除认证状态"""
    for key in ("access_token", "refresh_token", "user_info"):
        st.session_state.pop(key, None)


def get_graph_stats() -> dict:
    return api_call("get", "/api/graph/stats") or {}


# ============ 结构化表格编辑器 ============


def _component_editor(key_prefix: str, defaults: list[dict] | None = None) -> pd.DataFrame:
    """可编辑的配方组分表格"""
    func_opts = _function_options()
    if defaults is None:
        defaults = [
            {t("col_material_name"): "", t("col_function"): func_opts[0], t("col_weight_pct"): 0.0},
        ]

    df = pd.DataFrame(defaults)
    edited = st.data_editor(
        df,
        column_config={
            t("col_material_name"): st.column_config.TextColumn(
                t("col_material_name"), width="large", required=True
            ),
            t("col_function"): st.column_config.SelectboxColumn(
                t("col_function"), options=func_opts, required=True
            ),
            t("col_weight_pct"): st.column_config.NumberColumn(
                t("col_weight_pct"), min_value=0.0, max_value=100.0, step=0.1, format="%.1f"
            ),
        },
        num_rows="dynamic",
        use_container_width=True,
        key=f"{key_prefix}_comp_editor",
    )
    return edited


def _performance_editor(key_prefix: str, defaults: list[dict] | None = None) -> pd.DataFrame:
    """可编辑的性能测试表格"""
    if defaults is None:
        defaults = [
            {t("col_test_name"): "", t("col_value"): 0.0, t("col_unit"): ""},
        ]

    df = pd.DataFrame(defaults)
    edited = st.data_editor(
        df,
        column_config={
            t("col_test_name"): st.column_config.TextColumn(
                t("col_test_name"), width="medium", required=True
            ),
            t("col_value"): st.column_config.NumberColumn(
                t("col_value"), format="%.2f"
            ),
            t("col_unit"): st.column_config.TextColumn(
                t("col_unit"), width="small"
            ),
        },
        num_rows="dynamic",
        use_container_width=True,
        key=f"{key_prefix}_perf_editor",
    )
    return edited


def _components_df_to_api(df: pd.DataFrame) -> list[dict]:
    """将组分 DataFrame 转换为 API 格式"""
    items = []
    for _, row in df.iterrows():
        name = str(row.get(t("col_material_name"), "")).strip()
        if not name:
            continue
        func_display = str(row.get(t("col_function"), ""))
        func_api = _function_to_api(func_display)
        weight = float(row.get(t("col_weight_pct"), 0))
        items.append({
            "material": {"name": name, "function": func_api},
            "weight_percent": weight,
        })
    return items


def _performance_df_to_api(df: pd.DataFrame) -> list[dict]:
    """将性能 DataFrame 转换为 API 格式"""
    perfs = []
    for _, row in df.iterrows():
        name = str(row.get(t("col_test_name"), "")).strip()
        if not name:
            continue
        perfs.append({
            "test_name": name,
            "value": float(row.get(t("col_value"), 0)),
            "unit": str(row.get(t("col_unit"), "")),
        })
    return perfs


# ============ 导出辅助函数 ============


def _fetch_export_bytes(endpoint: str, params: dict | None = None) -> bytes | None:
    """调用导出 API 获取文件二进制内容，失败返回 None。"""
    try:
        token = st.session_state.get("access_token", "")
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = requests.get(f"{API_BASE}{endpoint}", params=params, headers=headers, timeout=120)
        if resp.status_code == 200:
            return resp.content
        return None
    except Exception:
        return None


def _render_single_export(code: str):
    """渲染单条配方的 Excel / JSON 导出下载按钮。"""
    ec1, ec2 = st.columns(2)
    with ec1:
        data_xlsx = _fetch_export_bytes("/api/formulas/export", params={"format": "excel", "code": code})
        if data_xlsx:
            st.download_button(
                f"{t('export_single_btn')} (Excel)",
                data=data_xlsx,
                file_name=f"{code}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"dl_single_xlsx_{code}",
            )
    with ec2:
        data_json = _fetch_export_bytes("/api/formulas/export", params={"format": "json", "code": code})
        if data_json:
            st.download_button(
                f"{t('export_single_btn')} (JSON)",
                data=data_json,
                file_name=f"{code}.json",
                mime="application/json",
                key=f"dl_single_json_{code}",
            )


# ============ 侧边栏 ============

with st.sidebar:
    lang = st.selectbox(
        "🌐 语言 / Language",
        ["中文", "English"],
        index=0 if _get_lang() == "zh" else 1,
        key="lang_selector",
    )
    st.session_state["lang"] = "zh" if lang == "中文" else "en"

    st.markdown(
        f'<div class="sidebar-brand">'
        f'<div class="sidebar-brand-name">🧪 ChemAgent</div>'
        f'<div class="sidebar-brand-slogan">{t("brand_slogan")}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")


# ============ 登录门控 ============


def _auth_bypass_enabled() -> bool:
    """本地免登录模式（CHEM_AUTH_BYPASS=true 时跳过登录门禁）。"""
    return os.environ.get("CHEM_AUTH_BYPASS", "").strip().lower() in ("1", "true", "yes", "on")


def _is_logged_in() -> bool:
    if _auth_bypass_enabled():
        return True
    return bool(st.session_state.get("access_token"))


def _show_login_page():
    """显示登录界面"""
    st.markdown(
        f'<div class="hero-section fade-in">'
        f'<div class="hero-title">🧪 ChemAgent</div>'
        f'<div class="hero-subtitle">{t("brand_slogan")}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        with st.form("login_form"):
            username = st.text_input(t("login_username"))
            password = st.text_input(t("login_password"), type="password")
            submitted = st.form_submit_button(t("login_btn"), type="primary", use_container_width=True)

        if submitted and username and password:
            try:
                resp = requests.post(
                    f"{API_BASE}/api/auth/login",
                    json={"username": username, "password": password},
                    timeout=10,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state["access_token"] = data["access_token"]
                    st.session_state["refresh_token"] = data["refresh_token"]
                    st.session_state["user_info"] = data["user"]
                    st.rerun()
                else:
                    st.error(t("login_failed"))
            except requests.ConnectionError:
                st.error(t_fmt("conn_error", API_BASE))
            except Exception as e:
                st.error(t_fmt("login_error", str(e)))

    st.markdown(
        f'<div class="login-copyright">{t("copyright_text")}</div>',
        unsafe_allow_html=True,
    )


if not _is_logged_in():
    _show_login_page()
    st.stop()


# ============ 已登录：侧边栏用户信息 + 导航 ============

if _auth_bypass_enabled() and "user_info" not in st.session_state:
    st.session_state["user_info"] = {
        "id": 1,
        "username": "local",
        "full_name": "本地模式（免登录）",
        "roles": ["superadmin"],
        "permissions": ["*"],
        "is_superadmin": True,
    }

user_info = st.session_state.get("user_info", {})
user_perms = user_info.get("permissions", [])
is_admin = "*" in user_perms or any(p.startswith("user:") or p.startswith("role:") for p in user_perms)

with st.sidebar:
    # 用户信息
    st.markdown(f"**{t('current_user')}:** {user_info.get('full_name') or user_info.get('username', '?')}")
    st.caption(f"{t('role_label')}: {', '.join(user_info.get('roles', []))}")
    if not _auth_bypass_enabled():
        if st.button(t("logout_btn"), use_container_width=True):
            _clear_auth()
            st.rerun()

    st.markdown("---")

    nav_items = [
        t("nav_dashboard"),
        t("nav_guide"),
        t("nav_chat"),
        t("nav_search"),
        t("nav_manage"),
        t("nav_versions"),
        t("nav_analysis"),
        t("nav_predict"),
        t("nav_recommend"),
        t("nav_materials"),
        t("nav_knowledge"),
        t("nav_experiment"),
    ]
    if is_admin:
        nav_items.append(t("nav_admin"))

    page = st.radio(t("nav_title"), nav_items)

    st.markdown("---")
    st.markdown(f"### {t('system_status')}")
    health = api_call("get", "/health")
    if health:
        st.success(t_fmt("api_ok", health.get("version", "?")))
        kg = health.get("knowledge_graph", {})
        if kg.get("connected"):
            st.success(t("kg_connected"))
        else:
            st.warning(t("kg_disconnected"))
    else:
        st.error(t("backend_down"))

    # 侧边栏底部版权
    st.markdown(
        f'<div class="sidebar-copyright">{t("copyright_text")}</div>',
        unsafe_allow_html=True,
    )

# ============ Agent 步骤渲染 ============


def _render_agent_step(step: dict, index: int) -> None:
    """渲染单个 Agent 推理步骤（颜色编码 + 步骤序号）"""
    import html as _html

    step_type = step.get("type", "unknown")

    # 类型 -> (emoji, css_class, i18n_key)
    type_map = {
        "thought":     ("\U0001f914", "step-thought",     "agent_thought"),
        "action":      ("\U0001f527", "step-action",      "agent_tool"),
        "observation": ("\U0001f4ca", "step-observation",  "agent_observation"),
        "reflection":  ("\U0001f4ad", "step-reflection",   "agent_reflection"),
        "planning":    ("\U0001f4cb", "step-planning",     "agent_planning"),
        "error":       ("\u26a0\ufe0f", "step-error",      "agent_error"),
        "answer":      ("\u2728",     "step-answer",       "agent_answer"),
    }

    emoji, css_class, label_key = type_map.get(
        step_type, ("\u2139\ufe0f", "step-default", "agent_unknown")
    )
    label = t(label_key)
    step_num = t_fmt("agent_step_number", index)

    # 构建内容 HTML
    content = step.get("content", "")

    if step_type == "planning":
        if step.get("plan_steps"):
            items = "".join(
                f"<li>{_html.escape(ps)}</li>" for ps in step["plan_steps"]
            )
            content_html = f'<ol class="planning-list">{items}</ol>'
        else:
            content_html = f"<div>{_html.escape(content)}</div>"
    elif step_type == "action":
        tool_name = _html.escape(step.get("tool_name", "?"))
        content_html = (
            f'<code style="background:#f3f4f6;padding:2px 6px;'
            f'border-radius:4px;">{tool_name}</code>'
        )
    elif step_type == "observation":
        preview = content[:100] + "..." if len(content) > 100 else content
        content_html = (
            f'<div style="color:#6b7280;font-size:0.9em;">'
            f"{_html.escape(preview)}</div>"
        )
    else:
        content_html = f"<div>{_html.escape(content)}</div>"

    # 渲染卡片
    st.markdown(
        f'<div class="agent-step-card {css_class}">'
        f'<div class="agent-step-header">'
        f'<span class="agent-step-number">{step_num}</span>'
        f"<span>{emoji} {label}</span>"
        f"</div>"
        f"{content_html}"
        f"</div>",
        unsafe_allow_html=True,
    )

    # 额外原生组件
    if step_type == "action" and step.get("tool_input"):
        with st.expander(t("agent_params"), expanded=False):
            st.json(step["tool_input"])
    elif step_type == "observation":
        with st.expander(t("agent_observation"), expanded=False):
            st.code(content[:500], language="json")


# ============ 页面: 总览仪表板 ============

if page == t("nav_dashboard"):
    st.markdown(
        f'<div class="main-header">{t("dashboard_title")}</div>',
        unsafe_allow_html=True,
    )

    # 欢迎 Hero
    _user_display = user_info.get("full_name") or user_info.get("username", "")
    st.markdown(
        f'<div class="hero-section fade-in">'
        f'<div class="hero-title">{t_fmt("dashboard_welcome", _user_display)}</div>'
        f'<div class="hero-subtitle">{t("brand_slogan")}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # 知识库概览
    st.markdown(
        f'<div class="section-title">{t("dashboard_stats_title")}</div>',
        unsafe_allow_html=True,
    )
    stats = get_graph_stats()
    if stats:
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.metric(t("stat_formulas"), stats.get("formulas", 0))
        with c2:
            st.metric(t("stat_materials"), stats.get("materials", 0))
        with c3:
            st.metric(t("stat_categories"), stats.get("categories", 0))
        with c4:
            st.metric(t("stat_relations"), stats.get("contains_rels", 0))
        with c5:
            st.metric(t("stat_tests"), stats.get("performance_tests", 0))

    st.markdown("---")

    # 数据可视化：类别分布 + 原材料 TOP10
    st.markdown(
        f'<div class="section-title">{t("dashboard_stats_title")}</div>',
        unsafe_allow_html=True,
    )
    _viz_c1, _viz_c2 = st.columns(2)
    with _viz_c1:
        cat_dist = api_call("get", "/api/graph/category-distribution")
        if cat_dist and len(cat_dist) > 0:
            fig_pie = go.Figure(data=[go.Pie(
                labels=[d["category"] for d in cat_dist],
                values=[d["count"] for d in cat_dist],
                hole=0.4,
                textinfo="label+percent",
                textposition="outside",
            )])
            fig_pie.update_layout(
                title=t("chart_category_dist"),
                showlegend=False,
                margin=dict(t=40, b=20, l=20, r=20),
                height=350,
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info(t("chart_no_data"))
    with _viz_c2:
        top_mats = api_call("get", "/api/graph/top-materials", params={"limit": 10})
        if top_mats and len(top_mats) > 0:
            fig_bar = go.Figure(data=[go.Bar(
                y=[m["name"] for m in reversed(top_mats)],
                x=[m["usage_count"] for m in reversed(top_mats)],
                orientation="h",
                marker_color="#667eea",
                text=[f'{m["usage_count"]}' for m in reversed(top_mats)],
                textposition="outside",
            )])
            fig_bar.update_layout(
                title=t("chart_material_top"),
                xaxis_title="",
                yaxis_title="",
                margin=dict(t=40, b=20, l=20, r=20),
                height=350,
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info(t("chart_no_data"))

    st.markdown("---")

    # 核心功能卡片
    st.markdown(
        f'<div class="section-title">{t("dashboard_features_title")}</div>',
        unsafe_allow_html=True,
    )
    _features = [
        ("\U0001f4ac", "feat_short_chat"),
        ("\U0001f50d", "feat_short_search"),
        ("\U0001f4ca", "feat_short_analysis"),
        ("\U0001f3af", "feat_short_predict"),
        ("\U0001f9e9", "feat_short_recommend"),
        ("\U0001f9ea", "feat_short_materials"),
    ]
    for _row_start in range(0, 6, 3):
        _fcols = st.columns(3)
        for _fi, _fcol in enumerate(_fcols):
            _fidx = _row_start + _fi
            _ficon, _fkey = _features[_fidx]
            with _fcol:
                st.markdown(
                    f'<div class="feature-card fade-in">'
                    f'<div class="feature-icon">{_ficon}</div>'
                    f'<div class="feature-name">{t(f"{_fkey}_name")}</div>'
                    f'<div class="feature-desc">{t(f"{_fkey}_desc")}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )


# ============ 页面: 功能介绍 ============

elif page == t("nav_guide"):
    st.markdown(
        f'<div class="main-header">{t("guide_title")}</div>',
        unsafe_allow_html=True,
    )

    # 系统简介
    st.markdown(
        f'<div class="section-title">{t("guide_overview_title")}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(t("guide_overview_body"))

    st.markdown("---")

    # 功能模块 - 2列卡片布局
    st.markdown(
        f'<div class="section-title">{t("guide_features_title")}</div>',
        unsafe_allow_html=True,
    )
    _feat_keys = [
        "guide_feat_dashboard",
        "guide_feat_chat",
        "guide_feat_search",
        "guide_feat_manage",
        "guide_feat_analysis",
        "guide_feat_predict",
        "guide_feat_recommend",
        "guide_feat_materials",
        "guide_feat_knowledge",
        "guide_feat_admin",
    ]
    for _gf_row in range(0, len(_feat_keys), 2):
        _gcols = st.columns(2)
        for _gi, _gcol in enumerate(_gcols):
            _gidx = _gf_row + _gi
            if _gidx < len(_feat_keys):
                with _gcol:
                    st.markdown(
                        f'<div class="guide-feature-card">{t(_feat_keys[_gidx])}</div>',
                        unsafe_allow_html=True,
                    )

    st.markdown("---")

    # 快速上手
    st.markdown(
        f'<div class="section-title">{t("guide_quickstart_title")}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(t("guide_quickstart_body"))

    st.markdown("---")

    # 使用技巧
    st.markdown(
        f'<div class="section-title">{t("guide_tips_title")}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(t("guide_tips_body"))


# ============ 页面: 智能问答 ============

elif page == t("nav_chat"):
    st.markdown(
        f'<div class="main-header">{t("chat_title")}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="page-desc">{t("page_desc_chat")}</div>', unsafe_allow_html=True)

    # 智能体模式开关
    agent_mode = st.sidebar.toggle(t("agent_mode_label"), value=False, key="agent_mode_toggle")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    def _build_history_payload(max_turns: int = 5) -> list[dict]:
        """从 session_state 提取最近 N 轮对话，转为后端 history 格式。"""
        history = st.session_state.get("chat_history", [])
        # 仅保留 role 和 content，去除 steps 等 UI 专用字段
        clean = [{"role": m["role"], "content": m["content"]} for m in history]
        # 限制为最近 max_turns * 2 条消息（每轮 = 1 user + 1 assistant）
        return clean[-(max_turns * 2):]

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            # 如果有推理步骤，展示推理过程
            if msg.get("steps"):
                with st.status(t("agent_done"), state="complete", expanded=False):
                    for idx, step in enumerate(msg["steps"], start=1):
                        _render_agent_step(step, idx)
            st.markdown(msg["content"])

    user_input = st.chat_input(t("chat_placeholder"))
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            if agent_mode:
                # Agent 模式
                with st.status(t("agent_reasoning"), expanded=True) as status_widget:
                    result = api_call(
                        "post", "/api/chat",
                        json={"message": user_input, "history": _build_history_payload(), "use_agent": True},
                    )
                    if result and result.get("steps"):
                        for idx, step in enumerate(result["steps"], start=1):
                            _render_agent_step(step, idx)
                        status_widget.update(label=t("agent_done"), state="complete")
                        reply = result.get("reply", t("chat_unavailable"))
                        steps_data = result.get("steps", [])
                    elif result:
                        reply = result.get("reply", t("chat_unavailable"))
                        steps_data = []
                        status_widget.update(label=t("agent_done"), state="complete")
                    else:
                        reply = t("chat_llm_unavailable")
                        steps_data = []
                        status_widget.update(label=t("agent_error"), state="error")
                st.markdown(reply)
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": reply, "steps": steps_data}
                )
            else:
                # 普通 RAG 模式
                with st.spinner(t("chat_thinking")):
                    result = api_call(
                        "post", "/api/chat",
                        json={"message": user_input, "history": _build_history_payload()},
                    )
                    if result:
                        reply = result.get("reply", t("chat_unavailable"))
                    else:
                        reply = t("chat_llm_unavailable")
                    st.markdown(reply)
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": reply}
                    )

    if st.sidebar.button(t("chat_clear")):
        st.session_state.chat_history = []
        st.rerun()


# ============ 页面: 配方检索 ============

elif page == t("nav_search"):
    st.markdown(
        f'<div class="main-header">{t("search_title")}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="page-desc">{t("page_desc_search")}</div>', unsafe_allow_html=True)

    sc1, sc2 = st.columns([2, 1])
    with sc1:
        keyword = st.text_input(t("search_keyword"), placeholder=t("search_keyword_ph"))
    with sc2:
        cat_opts = _category_options(include_all=True)
        category = st.selectbox(t("search_category"), cat_opts)

    materials_input = st.text_input(
        t("search_materials"), placeholder=t("search_materials_ph")
    )
    limit = st.slider(t("search_limit"), 5, 50, 20)

    if st.button(t("search_btn"), type="primary"):
        params: dict = {"limit": limit}
        if keyword:
            params["keyword"] = keyword
        if category != t("search_all"):
            params["category"] = _category_to_api(category)
        if materials_input:
            params["materials"] = materials_input

        with st.spinner(t("search_searching")):
            results = api_call("get", "/api/formulas", params=params)

        if results:
            st.success(t_fmt("search_found", len(results)))

            # 视图模式 & 排序
            _vc1, _vc2 = st.columns([1, 1])
            with _vc1:
                view_mode = st.radio(
                    t("search_view_mode"),
                    [t("search_view_card"), t("search_view_table")],
                    horizontal=True, key="search_view_mode",
                )
            with _vc2:
                sort_by = st.selectbox(
                    t("search_sort_by"),
                    [t("search_sort_similarity"), t("search_sort_name"), t("search_sort_category")],
                    key="search_sort_by",
                )

            # 排序
            if sort_by == t("search_sort_name"):
                results = sorted(results, key=lambda r: r.get("formula", {}).get("name", ""))
            elif sort_by == t("search_sort_category"):
                results = sorted(results, key=lambda r: r.get("formula", {}).get("category", ""))
            # 默认已按相似度降序

            # 初始化对比选择列表
            if "compare_codes" not in st.session_state:
                st.session_state.compare_codes = []

            # ---------- 表格视图 ----------
            if view_mode == t("search_view_table"):
                table_data = []
                for r in results:
                    f = r.get("formula", {})
                    score = r.get("similarity_score", 0)
                    items = f.get("items", [])
                    main_materials = ", ".join(
                        it.get("material", {}).get("name", "") for it in items[:3]
                    )
                    table_data.append({
                        t("search_code"): f.get("code", ""),
                        t("manage_name"): f.get("name", ""),
                        t("search_cat_label"): f.get("category", ""),
                        t("search_similarity"): f"{score:.2f}",
                        t("search_components"): main_materials or "-",
                    })
                st.dataframe(
                    pd.DataFrame(table_data),
                    use_container_width=True,
                    hide_index=True,
                )

            # ---------- 卡片视图 ----------
            if view_mode == t("search_view_card"):
                for r in results:
                    f = r.get("formula", {})
                    score = r.get("similarity_score", 0)
                    reason = r.get("match_reason", "")
                    code = f.get("code", "")

                    # 添加复选框用于选择对比
                    col_checkbox, col_expander = st.columns([0.5, 9.5])
                    with col_checkbox:
                        is_selected = st.checkbox(
                            t("compare_select"),
                            value=code in st.session_state.compare_codes,
                            key=f"compare_cb_{code}",
                            label_visibility="collapsed"
                        )
                        if is_selected and code not in st.session_state.compare_codes:
                            st.session_state.compare_codes.append(code)
                        elif not is_selected and code in st.session_state.compare_codes:
                            st.session_state.compare_codes.remove(code)

                    with col_expander:
                        with st.expander(
                            f"📋 {f.get('name', t('search_unnamed'))} "
                            f"({t('search_similarity')}: {score:.2f})"
                        ):
                            st.markdown(f"**{t('search_code')}:** {code}")
                            st.markdown(f"**{t('search_cat_label')}:** {f.get('category', '-')}")
                            st.markdown(f"**{t('search_description')}:** {f.get('description', '-')}")
                            st.markdown(f"**{t('search_match_reason')}:** {reason}")

                            items = f.get("items", [])
                            if items:
                                st.markdown(f"**{t('search_components')}:**")
                                df = pd.DataFrame([
                                    {
                                        t("col_material_name"): it.get("material", {}).get("name", ""),
                                        t("col_function"): it.get("material", {}).get("function", ""),
                                        t("col_weight_pct"): it.get("weight_percent", 0),
                                    }
                                    for it in items
                                ])
                                st.dataframe(df, use_container_width=True)

                            perfs = f.get("performance", [])
                            if perfs:
                                st.markdown(f"**{t('search_perf_data')}:**")
                                pdf = pd.DataFrame([
                                    {
                                        t("col_test_name"): p.get("test_name", ""),
                                        t("col_value"): p.get("value", 0),
                                        t("col_unit"): p.get("unit", ""),
                                    }
                                    for p in perfs
                                ])
                                st.dataframe(pdf, use_container_width=True)
            
            # 配方对比功能
            st.markdown("---")
            compare_codes = st.session_state.get("compare_codes", [])
            
            if len(compare_codes) < 2:
                st.info(t("compare_min_hint"))
            else:
                st.info(t_fmt("compare_select", len(compare_codes)))
                
                if st.button(t("compare_btn"), type="primary"):
                    with st.spinner(t("search_searching")):
                        compare_result = api_call(
                            "post", "/api/formulas/compare",
                            json={"codes": compare_codes}
                        )
                    
                    if compare_result:
                        st.markdown(f"### {t('compare_title')}")
                        
                        # 创建对比视图标签页
                        tab_table, tab_chart = st.tabs([
                            t("compare_tab_table"),
                            t("compare_tab_chart")
                        ])
                        
                        with tab_table:
                            formulas = compare_result.get("formulas", [])
                            
                            if formulas:
                                # 基本信息表格
                                st.markdown(f"#### {t('compare_basic_info')}")
                                basic_data = []
                                for formula in formulas:
                                    basic_data.append({
                                        t("search_code"): formula.get("code", "-"),
                                        t("manage_name"): formula.get("name", "-"),
                                        t("search_cat_label"): formula.get("category", "-"),
                                        t("search_description"): formula.get("description", "-")
                                    })
                                st.dataframe(pd.DataFrame(basic_data), use_container_width=True)
                                
                                # 组分对比表格
                                st.markdown(f"#### {t('compare_composition')}")
                                
                                # 收集所有原材料
                                all_materials = set()
                                for formula in formulas:
                                    for item in formula.get("items", []):
                                        mat_name = item.get("material", {}).get("name", "")
                                        if mat_name:
                                            all_materials.add(mat_name)
                                
                                # 构建组分对比表格
                                comp_data = []
                                for mat_name in sorted(all_materials):
                                    row = {t("col_material_name"): mat_name}
                                    for formula in formulas:
                                        code = formula.get("code", "?")
                                        weight = 0.0
                                        for item in formula.get("items", []):
                                            if item.get("material", {}).get("name") == mat_name:
                                                weight = item.get("weight_percent", 0)
                                                break
                                        row[code] = f"{weight:.1f}%"
                                    comp_data.append(row)
                                
                                if comp_data:
                                    st.dataframe(pd.DataFrame(comp_data), use_container_width=True)
                                else:
                                    st.info(t("compare_none"))
                                
                                # 性能对比表格
                                st.markdown(f"#### {t('compare_performance')}")
                                
                                # 收集所有性能测试
                                all_tests = set()
                                for formula in formulas:
                                    for perf in formula.get("performance", []):
                                        test_name = perf.get("test_name", "")
                                        if test_name:
                                            all_tests.add(test_name)
                                
                                # 构建性能对比表格
                                perf_data = []
                                for test_name in sorted(all_tests):
                                    row = {t("col_test_name"): test_name}
                                    for formula in formulas:
                                        code = formula.get("code", "?")
                                        value_str = "-"
                                        for perf in formula.get("performance", []):
                                            if perf.get("test_name") == test_name:
                                                value = perf.get("value", 0)
                                                unit = perf.get("unit", "")
                                                value_str = f"{value:.2f} {unit}".strip()
                                                break
                                        row[code] = value_str
                                    perf_data.append(row)
                                
                                if perf_data:
                                    st.dataframe(pd.DataFrame(perf_data), use_container_width=True)
                                else:
                                    st.info(t("compare_none"))
                        
                        with tab_chart:
                            formulas = compare_result.get("formulas", [])
                            
                            if formulas:
                                # 组分对比柱状图
                                st.markdown(f"#### {t('compare_composition')}")
                                
                                # 收集所有原材料和各配方的含量
                                all_materials = set()
                                for formula in formulas:
                                    for item in formula.get("items", []):
                                        mat_name = item.get("material", {}).get("name", "")
                                        if mat_name:
                                            all_materials.add(mat_name)
                                
                                if all_materials:
                                    fig_comp = go.Figure()
                                    for formula in formulas:
                                        code = formula.get("code", "?")
                                        weights = []
                                        for mat_name in sorted(all_materials):
                                            weight = 0.0
                                            for item in formula.get("items", []):
                                                if item.get("material", {}).get("name") == mat_name:
                                                    weight = item.get("weight_percent", 0)
                                                    break
                                            weights.append(weight)
                                        
                                        fig_comp.add_trace(go.Bar(
                                            name=code,
                                            x=sorted(all_materials),
                                            y=weights,
                                            text=[f"{w:.1f}%" for w in weights],
                                            textposition="outside"
                                        ))
                                    
                                    fig_comp.update_layout(
                                        barmode="group",
                                        xaxis_title=t("col_material_name"),
                                        yaxis_title=t("col_weight_pct"),
                                        height=400,
                                        margin=dict(t=20, b=100, l=40, r=40),
                                        xaxis_tickangle=-45
                                    )
                                    st.plotly_chart(fig_comp, use_container_width=True)
                                else:
                                    st.info(t("compare_none"))
                                
                                # 性能对比柱状图
                                st.markdown(f"#### {t('compare_performance')}")
                                
                                # 收集所有性能测试
                                all_tests = set()
                                for formula in formulas:
                                    for perf in formula.get("performance", []):
                                        test_name = perf.get("test_name", "")
                                        if test_name:
                                            all_tests.add(test_name)
                                
                                if all_tests:
                                    fig_perf = go.Figure()
                                    for formula in formulas:
                                        code = formula.get("code", "?")
                                        values = []
                                        for test_name in sorted(all_tests):
                                            value = 0.0
                                            for perf in formula.get("performance", []):
                                                if perf.get("test_name") == test_name:
                                                    value = perf.get("value", 0)
                                                    break
                                            values.append(value)
                                        
                                        fig_perf.add_trace(go.Bar(
                                            name=code,
                                            x=sorted(all_tests),
                                            y=values,
                                            text=[f"{v:.2f}" for v in values],
                                            textposition="outside"
                                        ))
                                    
                                    fig_perf.update_layout(
                                        barmode="group",
                                        xaxis_title=t("col_test_name"),
                                        yaxis_title=t("col_value"),
                                        height=400,
                                        margin=dict(t=20, b=100, l=40, r=40),
                                        xaxis_tickangle=-45
                                    )
                                    st.plotly_chart(fig_perf, use_container_width=True)
                                else:
                                    st.info(t("compare_none"))
                    else:
                        st.error(t("search_empty"))
                
                # 清除对比选择按钮
                if st.button(t("chat_clear")):
                    st.session_state.compare_codes = []
                    st.rerun()
        else:
            st.info(t("search_empty"))


# ============ 页面: 配方管理 ============

elif page == t("nav_manage"):
    st.markdown(
        f'<div class="main-header">{t("manage_title")}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="page-desc">{t("page_desc_manage")}</div>', unsafe_allow_html=True)

    tab_new, tab_view, tab_import, tab_export = st.tabs([
        t("manage_tab_new"), t("manage_tab_view"), t("manage_tab_import"), t("manage_tab_export"),
    ])

    with tab_new:
        st.markdown(f"### {t('manage_basic_info')}")
        fc1, fc2 = st.columns(2)
        with fc1:
            f_name = st.text_input(t("manage_name"))
            f_code = st.text_input(t("manage_code"))
        with fc2:
            f_category = st.selectbox(
                t("manage_category"), _category_options(), key="manage_cat"
            )
            f_app = st.text_input(t("manage_application"))
        f_desc = st.text_area(t("manage_desc"))

        # ---- 结构化组分表格 ----
        st.markdown(f"### {t('manage_components')}")
        st.caption(t("manage_components_hint"))

        func_opts = _function_options()
        default_items = [
            {
                t("col_material_name"): "",
                t("col_function"): func_opts[0] if func_opts else "",
                t("col_weight_pct"): 0.0,
            },
        ]
        comp_df = _component_editor("manage", default_items)

        # 显示合计百分比
        total_pct = comp_df[t("col_weight_pct")].sum()
        if total_pct > 0:
            st.info(t_fmt("manage_total_pct", total_pct))
            if abs(total_pct - 100.0) > 0.5:
                st.warning(t_fmt("manage_pct_warning", total_pct))

        # ---- 结构化性能表格 ----
        st.markdown(f"### {t('manage_performance')}")
        st.caption(t("manage_perf_hint"))

        default_perfs = [
            {t("col_test_name"): "", t("col_value"): 0.0, t("col_unit"): ""},
        ]
        perf_df = _performance_editor("manage", default_perfs)

        if st.button(t("manage_save"), type="primary"):
            if not f_name:
                st.error(t("manage_no_name"))
            else:
                items_api = _components_df_to_api(comp_df)
                if not items_api:
                    st.error(t("manage_no_components"))
                else:
                    perfs_api = _performance_df_to_api(perf_df)
                    formula_data = {
                        "name": f_name,
                        "code": f_code or f_name,
                        "category": _category_to_api(f_category),
                        "description": f_desc,
                        "target_application": f_app,
                        "items": items_api,
                        "performance": perfs_api,
                        "tags": [],
                    }
                    result = api_call("post", "/api/formulas", json=formula_data)
                    if result:
                        st.success(result.get("message", t("manage_save_ok")))

    with tab_view:
        code_input = st.text_input(t("manage_view_code"))
        if code_input and st.button(t("manage_view_btn")):
            formula = api_call("get", f"/api/formulas/{code_input}")
            if formula:
                # 状态管理
                _sc1, _sc2 = st.columns([2, 1])
                with _sc1:
                    current_status = formula.get("status", "draft")
                    status_labels = {
                        "draft": t("status_draft"),
                        "review": t("status_review"),
                        "approved": t("status_approved"),
                        "archived": t("status_archived"),
                    }
                    st.markdown(f"**{t('formula_status')}:** {status_labels.get(current_status, current_status)}")
                with _sc2:
                    new_status = st.selectbox(
                        t("formula_status"),
                        ["draft", "review", "approved", "archived"],
                        index=["draft", "review", "approved", "archived"].index(current_status) if current_status in ["draft", "review", "approved", "archived"] else 0,
                        format_func=lambda s: status_labels.get(s, s),
                        key="status_select",
                        label_visibility="collapsed",
                    )
                    if new_status != current_status:
                        if st.button(t("manage_save"), key="btn_status_update"):
                            result = api_call("patch", f"/api/formulas/{code_input}/status", params={"status": new_status})
                            if result:
                                st.success(t("status_updated"))
                                st.rerun()

                st.json(formula)
                # 单条导出按钮
                _render_single_export(code_input)

    # ---- 批量导入 Tab ----
    with tab_import:
        st.markdown(f"### {t('import_title')}")
        st.caption(t("import_upload_hint"))

        # 下载模板
        template_data = _fetch_export_bytes("/api/formulas/export/template")
        if template_data:
            st.download_button(
                t("import_download_template"),
                data=template_data,
                file_name="formula_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_template",
            )

        uploaded = st.file_uploader(
            t("import_upload"),
            type=["xlsx", "json"],
            key="import_uploader",
        )

        if st.button(t("import_btn"), type="primary", key="btn_import"):
            if uploaded is None:
                st.warning(t("import_no_file"))
            else:
                with st.spinner(t("import_running")):
                    import requests as _req
                    token = st.session_state.get("access_token", "")
                    try:
                        resp = _req.post(
                            f"{API_BASE}/api/formulas/import",
                            files={"file": (uploaded.name, uploaded.getvalue(), uploaded.type)},
                            headers={"Authorization": f"Bearer {token}"},
                            timeout=120,
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            s = data.get("summary", {})
                            st.markdown(f"### {t('import_result')}")
                            total, ok, skip, fail = s.get("total", 0), s.get("success", 0), s.get("skipped", 0), s.get("failed", 0)
                            if fail == 0 and skip == 0:
                                st.success(t_fmt("import_summary", total, ok, skip, fail))
                            elif fail > 0:
                                st.error(t_fmt("import_summary", total, ok, skip, fail))
                            else:
                                st.warning(t_fmt("import_summary", total, ok, skip, fail))

                            details = data.get("details", [])
                            if details:
                                import pandas as _pd
                                df = _pd.DataFrame([
                                    {
                                        t("import_col_code"): d.get("code", ""),
                                        t("import_col_status"): d.get("status", ""),
                                        t("import_col_message"): d.get("message", ""),
                                    }
                                    for d in details
                                ])
                                st.dataframe(df, use_container_width=True, hide_index=True)
                        else:
                            detail = ""
                            try:
                                detail = resp.json().get("detail", resp.text)
                            except Exception:
                                detail = resp.text
                            st.error(t_fmt("api_error", detail))
                    except Exception as e:
                        st.error(t_fmt("request_failed", e))

    # ---- 批量导出 Tab ----
    with tab_export:
        st.markdown(f"### {t('export_title')}")

        scope = st.radio(
            t("export_scope"),
            [t("export_all"), t("export_filtered"), t("export_single")],
            horizontal=True,
            key="export_scope_radio",
        )

        export_params: dict = {}
        if scope == t("export_filtered"):
            ec1, ec2 = st.columns(2)
            with ec1:
                ex_cat_opts = _category_options(include_all=True)
                ex_cat = st.selectbox(t("export_filter_category"), ex_cat_opts, key="export_cat")
                if ex_cat != t("search_all"):
                    export_params["category"] = _category_to_api(ex_cat)
            with ec2:
                ex_kw = st.text_input(t("export_filter_keyword"), key="export_kw")
                if ex_kw:
                    export_params["keyword"] = ex_kw
        elif scope == t("export_single"):
            ex_code = st.text_input(t("export_code_input"), key="export_code")
            if ex_code:
                export_params["code"] = ex_code

        fmt = st.radio(t("export_format"), ["Excel (.xlsx)", "JSON (.json)"], horizontal=True, key="export_fmt")
        export_params["format"] = "json" if "JSON" in fmt else "excel"

        if st.button(t("export_btn"), type="primary", key="btn_export"):
            with st.spinner(t("export_running")):
                file_bytes = _fetch_export_bytes("/api/formulas/export", params=export_params)
            if file_bytes:
                ext = "json" if export_params["format"] == "json" else "xlsx"
                mime = "application/json" if ext == "json" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                st.download_button(
                    t("export_download"),
                    data=file_bytes,
                    file_name=f"formulas_export.{ext}",
                    mime=mime,
                    key="dl_export_file",
                )
            else:
                st.warning(t("export_no_data"))


# ============ 页面: 配方分析 ============

elif page == t("nav_analysis"):
    st.markdown(
        f'<div class="main-header">{t("analysis_title")}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="page-desc">{t("page_desc_analysis")}</div>', unsafe_allow_html=True)

    analysis_code = st.text_input(t("analysis_code"), key="analysis_code")
    if st.button(t("analysis_start"), type="primary") and analysis_code:
        with st.spinner(t("analysis_fetching")):
            formula = api_call("get", f"/api/formulas/{analysis_code}")

        if formula:
            st.markdown("---")
            st.markdown(f"### {t_fmt('analysis_formula', formula.get('name', analysis_code))}")

            # 可视化：组分饼图 + 性能雷达图
            _items = formula.get("items", [])
            _perfs = formula.get("performance", [])
            if _items or _perfs:
                _ac1, _ac2 = st.columns(2)
                with _ac1:
                    if _items:
                        _names = [it.get("material", {}).get("name", "?") for it in _items]
                        _pcts = [it.get("weight_percent", 0) for it in _items]
                        fig_comp = go.Figure(data=[go.Pie(
                            labels=_names, values=_pcts, hole=0.35,
                            textinfo="label+percent", textposition="outside",
                        )])
                        fig_comp.update_layout(
                            title=t("chart_composition"), showlegend=False,
                            margin=dict(t=40, b=20, l=20, r=20), height=320,
                        )
                        st.plotly_chart(fig_comp, use_container_width=True)
                with _ac2:
                    if _perfs and len(_perfs) >= 3:
                        _pnames = [p.get("test_name", "") for p in _perfs]
                        _pvals = [p.get("value", 0) for p in _perfs]
                        fig_radar = go.Figure(data=go.Scatterpolar(
                            r=_pvals + [_pvals[0]],
                            theta=_pnames + [_pnames[0]],
                            fill="toself", fillcolor="rgba(102,126,234,0.2)",
                            line_color="#667eea",
                        ))
                        fig_radar.update_layout(
                            title=t("chart_performance_radar"),
                            polar=dict(radialaxis=dict(visible=True)),
                            margin=dict(t=40, b=20, l=40, r=40), height=320,
                            showlegend=False,
                        )
                        st.plotly_chart(fig_radar, use_container_width=True)
                    elif _perfs:
                        _pnames = [p.get("test_name", "") for p in _perfs]
                        _pvals = [p.get("value", 0) for p in _perfs]
                        fig_pbar = go.Figure(data=[go.Bar(
                            x=_pnames, y=_pvals, marker_color="#667eea",
                        )])
                        fig_pbar.update_layout(
                            title=t("chart_performance_radar"),
                            margin=dict(t=40, b=20, l=20, r=20), height=320,
                        )
                        st.plotly_chart(fig_pbar, use_container_width=True)

            with st.spinner(t("analysis_running")):
                result = api_call("post", "/api/formulas/analyze", json=formula)

            if result:
                st.markdown(f"### {t('analysis_result')}")
                st.markdown(result.get("analysis", t("analysis_failed")))

                # 生成研发报告
                st.markdown("---")
                _rpt_include_ai = st.checkbox(t("report_include_analysis"), value=True, key="rpt_ai")
                if st.button(t("report_btn"), key="btn_report"):
                    with st.spinner(t("report_generating")):
                        report_result = api_call(
                            "post", f"/api/formulas/{analysis_code}/report",
                            params={"include_analysis": str(_rpt_include_ai).lower()},
                        )
                    if report_result:
                        report_md = report_result.get("report", "")
                        st.download_button(
                            t("report_download"),
                            data=report_md.encode("utf-8"),
                            file_name=f"report_{analysis_code}.md",
                            mime="text/markdown",
                            key="dl_report",
                        )


# ============ 页面: 性能预测 ============

elif page == t("nav_predict"):
    st.markdown(
        f'<div class="main-header">{t("predict_title")}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="page-desc">{t("page_desc_predict")}</div>', unsafe_allow_html=True)

    tab_pred, tab_train = st.tabs([t("predict_tab_predict"), t("predict_tab_train")])

    with tab_pred:
        st.markdown(t("predict_desc"))
        st.caption(t("predict_components_hint"))

        func_opts = _function_options()
        pred_defaults = [
            {
                t("col_material_name"): "",
                t("col_function"): func_opts[0] if func_opts else "",
                t("col_weight_pct"): 0.0,
            },
        ]
        pred_comp_df = _component_editor("predict", pred_defaults)

        pred_category = st.selectbox(
            t("predict_category"), _category_options(), key="pred_cat"
        )

        default_props = {"zh": "硬度, 光泽度, 附着力", "en": "Hardness, Gloss, Adhesion"}
        target_props = st.text_input(
            t("predict_target_props"),
            default_props.get(_get_lang(), default_props["zh"]),
        )

        if st.button(t("predict_btn"), type="primary"):
            items_api = _components_df_to_api(pred_comp_df)
            if items_api:
                props = [p.strip() for p in target_props.split(",")]
                req = {
                    "items": items_api,
                    "category": _category_to_api(pred_category),
                    "target_properties": props,
                }
                with st.spinner(t("predict_running")):
                    results = api_call("post", "/api/predict", json=req)
                if results:
                    st.markdown(f"### {t('predict_result')}")
                    for r in results:
                        pc1, pc2, pc3 = st.columns(3)
                        with pc1:
                            st.metric(
                                r["property_name"],
                                f"{r['predicted_value']:.2f} {r.get('unit', '')}",
                            )
                        with pc2:
                            st.progress(r.get("confidence", 0))
                            st.caption(
                                t_fmt("predict_confidence", r.get("confidence", 0))
                            )
                        with pc3:
                            st.caption(r.get("explanation", ""))

                    # 可视化：雷达图 + 置信度条形图
                    if len(results) >= 2:
                        _pred_c1, _pred_c2 = st.columns(2)
                        with _pred_c1:
                            _rnames = [r["property_name"] for r in results]
                            _rvals = [r["predicted_value"] for r in results]
                            if len(results) >= 3:
                                fig_pred_radar = go.Figure(data=go.Scatterpolar(
                                    r=_rvals + [_rvals[0]],
                                    theta=_rnames + [_rnames[0]],
                                    fill="toself", fillcolor="rgba(102,126,234,0.2)",
                                    line_color="#667eea",
                                ))
                                fig_pred_radar.update_layout(
                                    title=t("chart_performance_radar"),
                                    polar=dict(radialaxis=dict(visible=True)),
                                    margin=dict(t=40, b=20, l=40, r=40), height=300,
                                    showlegend=False,
                                )
                                st.plotly_chart(fig_pred_radar, use_container_width=True)
                            else:
                                fig_pred_bar = go.Figure(data=[go.Bar(
                                    x=_rnames, y=_rvals, marker_color="#667eea",
                                )])
                                fig_pred_bar.update_layout(
                                    title=t("chart_performance_radar"),
                                    margin=dict(t=40, b=20, l=20, r=20), height=300,
                                )
                                st.plotly_chart(fig_pred_bar, use_container_width=True)
                        with _pred_c2:
                            _cnames = [r["property_name"] for r in results]
                            _cvals = [r.get("confidence", 0) * 100 for r in results]
                            fig_conf = go.Figure(data=[go.Bar(
                                x=_cnames, y=_cvals, marker_color="#10b981",
                                text=[f"{v:.0f}%" for v in _cvals], textposition="outside",
                            )])
                            fig_conf.update_layout(
                                title=t("chart_confidence"),
                                yaxis=dict(range=[0, 110], title="%"),
                                margin=dict(t=40, b=20, l=20, r=20), height=300,
                            )
                            st.plotly_chart(fig_conf, use_container_width=True)

    with tab_train:
        st.markdown(t("predict_train_desc"))
        default_train = {
            "zh": "硬度, 光泽度, 附着力, 耐冲击性",
            "en": "Hardness, Gloss, Adhesion, Impact Resistance",
        }
        train_props = st.text_input(
            t("predict_train_props"),
            default_train.get(_get_lang(), default_train["zh"]),
        )
        if st.button(t("predict_train_btn")):
            props = [p.strip() for p in train_props.split(",")]
            with st.spinner(t("predict_training")):
                result = api_call(
                    "post", "/api/predict/train",
                    json={"target_properties": props},
                )
            if result:
                st.success(t("predict_train_ok"))
                st.json(result.get("results", {}))


# ============ 页面: 配方推荐 ============

elif page == t("nav_recommend"):
    st.markdown(
        f'<div class="main-header">{t("recommend_title")}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="page-desc">{t("page_desc_recommend")}</div>', unsafe_allow_html=True)

    rec_requirement = st.text_area(
        t("recommend_requirement"), placeholder=t("recommend_requirement_ph")
    )
    rec_category = st.selectbox(
        t("recommend_category"), _category_options(), key="rec_cat"
    )

    st.markdown(f"**{t('recommend_target_perf')}**")
    rc1, rc2, rc3 = st.columns(3)
    default_props_data = {
        "zh": [("硬度", ">= 3H"), ("光泽度", ">= 85"), ("附着力", "<= 1级")],
        "en": [("Hardness", ">= 3H"), ("Gloss", ">= 85"), ("Adhesion", "<= Grade 1")],
    }
    dp = default_props_data.get(_get_lang(), default_props_data["zh"])
    with rc1:
        p1_name = st.text_input(t_fmt("recommend_prop_name", 1), dp[0][0])
        p1_value = st.text_input(t_fmt("recommend_prop_value", 1), dp[0][1])
    with rc2:
        p2_name = st.text_input(t_fmt("recommend_prop_name", 2), dp[1][0])
        p2_value = st.text_input(t_fmt("recommend_prop_value", 2), dp[1][1])
    with rc3:
        p3_name = st.text_input(t_fmt("recommend_prop_name", 3), dp[2][0])
        p3_value = st.text_input(t_fmt("recommend_prop_value", 3), dp[2][1])

    if st.button(t("recommend_btn"), type="primary") and rec_requirement:
        target_perf = {}
        if p1_name:
            target_perf[p1_name] = p1_value
        if p2_name:
            target_perf[p2_name] = p2_value
        if p3_name:
            target_perf[p3_name] = p3_value

        with st.spinner(t("recommend_running")):
            result = api_call(
                "post", "/api/formulas/recommend",
                json={
                    "requirement": rec_requirement,
                    "category": _category_to_api(rec_category),
                    "target_performance": target_perf,
                },
            )
        if result:
            st.markdown(f"### {t('recommend_result')}")
            st.markdown(result.get("recommendation", ""))

            refs = result.get("reference_formulas", [])
            if refs:
                st.markdown(f"### {t('recommend_refs')}")
                for _ri, r in enumerate(refs):
                    f = r.get("formula", {})
                    with st.expander(
                        f"📋 {f.get('name', '?')} "
                        f"({t('search_similarity')}: {r.get('similarity_score', 0):.2f})"
                    ):
                        st.markdown(f"**{t('search_code')}:** {f.get('code', '-')}")
                        st.markdown(f"**{t('search_cat_label')}:** {f.get('category', '-')}")
                        st.markdown(f"**{t('search_description')}:** {f.get('description', '-')}")
                        _ref_items = f.get("items", [])
                        if _ref_items:
                            st.markdown(f"**{t('search_components')}:**")
                            _ref_df = pd.DataFrame([
                                {
                                    t("col_material_name"): it.get("material", {}).get("name", ""),
                                    t("col_function"): it.get("material", {}).get("function", ""),
                                    t("col_weight_pct"): it.get("weight_percent", 0),
                                }
                                for it in _ref_items
                            ])
                            st.dataframe(_ref_df, use_container_width=True)


# ============ 页面: 原材料管理 ============

elif page == t("nav_materials"):
    st.markdown(
        f'<div class="main-header">{t("materials_title")}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="page-desc">{t("page_desc_materials")}</div>', unsafe_allow_html=True)

    mtab1, mtab2, mtab3 = st.tabs([
        t("materials_tab_search"),
        t("materials_tab_new"),
        t("materials_tab_sub"),
    ])

    with mtab1:
        mat_keyword = st.text_input(
            t("materials_search_label"), placeholder=t("materials_search_ph")
        )
        mat_func = st.selectbox(
            t("materials_func_filter"), _function_options(include_all=True)
        )
        if mat_keyword and st.button(t("materials_search_btn"), key="search_mat"):
            params: dict = {"keyword": mat_keyword, "limit": 30}
            if mat_func != t("search_all"):
                params["function"] = _function_to_api(mat_func)
            results = api_call("get", "/api/materials", params=params)
            if results:
                df = pd.DataFrame([
                    {
                        t("col_name"): m.get("name", ""),
                        t("col_cas"): m.get("cas_number", "-"),
                        t("col_chemical_name"): m.get("chemical_name", "-"),
                        t("col_function"): m.get("function", "-"),
                        t("col_supplier"): m.get("supplier", "-"),
                    }
                    for m in results
                ])
                st.dataframe(df, use_container_width=True)

                # 原材料详情查看
                st.markdown(f"#### {t('material_detail')}")
                mat_names = [m.get("name", "") for m in results if m.get("name")]
                if mat_names:
                    selected_mat = st.selectbox(
                        t("col_name"), mat_names, key="mat_detail_select"
                    )
                    if st.button(t("recommend_view_ref"), key="btn_mat_detail"):
                        detail = api_call("get", f"/api/materials/{selected_mat}/detail")
                        if detail:
                            _md1, _md2 = st.columns(2)
                            with _md1:
                                st.markdown(f"**{t('material_properties')}**")
                                props = detail.get("properties", {})
                                if any(v is not None for v in props.values()):
                                    for k, v in props.items():
                                        if v is not None:
                                            label_map = {
                                                "density": t("material_density"),
                                                "viscosity": t("material_viscosity"),
                                                "boiling_point": t("material_boiling_point"),
                                                "flash_point": t("material_flash_point"),
                                            }
                                            st.markdown(f"- {label_map.get(k, k)}: {v}")
                                else:
                                    st.caption("-")
                            with _md2:
                                st.markdown(f"**{t('material_related')}**")
                                related = detail.get("related_formulas", [])
                                if related:
                                    for rf in related[:10]:
                                        st.markdown(
                                            f"- {rf.get('name', '?')} ({rf.get('code', '?')}) "
                                            f"— {rf.get('weight_percent', 0):.1f}%"
                                        )
                                else:
                                    st.caption("-")
            else:
                st.info(t("materials_empty"))

    with mtab2:
        st.markdown(f"### {t('materials_new_title')}")
        mc1, mc2 = st.columns(2)
        with mc1:
            m_name = st.text_input(t("materials_name"), key="new_mat_name")
            m_cas = st.text_input(t("materials_cas"), key="new_mat_cas")
            m_chem = st.text_input(t("materials_chemical"), key="new_mat_chem")
        with mc2:
            m_supplier = st.text_input(t("materials_supplier"), key="new_mat_supplier")
            m_function = st.selectbox(
                t("materials_function"), _function_options(), key="new_mat_func"
            )

        # 理化性质
        st.markdown(f"**{t('material_properties')}**")
        _mp1, _mp2, _mp3, _mp4 = st.columns(4)
        with _mp1:
            m_density = st.number_input(t("material_density"), value=0.0, step=0.01, key="mat_density")
        with _mp2:
            m_viscosity = st.number_input(t("material_viscosity"), value=0.0, step=0.1, key="mat_viscosity")
        with _mp3:
            m_boiling_point = st.number_input(t("material_boiling_point"), value=0.0, step=1.0, key="mat_bp")
        with _mp4:
            m_flash_point = st.number_input(t("material_flash_point"), value=0.0, step=1.0, key="mat_fp")

        if st.button(t("materials_save")) and m_name:
            _props = {}
            if m_density > 0:
                _props["density"] = m_density
            if m_viscosity > 0:
                _props["viscosity"] = m_viscosity
            if m_boiling_point != 0:
                _props["boiling_point"] = m_boiling_point
            if m_flash_point != 0:
                _props["flash_point"] = m_flash_point
            mat_data = {
                "name": m_name,
                "cas_number": m_cas or None,
                "chemical_name": m_chem or None,
                "supplier": m_supplier or None,
                "function": _function_to_api(m_function),
                "properties": _props,
            }
            result = api_call("post", "/api/materials", json=mat_data)
            if result:
                st.success(result.get("message", t("manage_save_ok")))

    with mtab3:
        st.markdown(f"### {t('materials_sub_title')}")
        sub_name = st.text_input(t("materials_sub_name"), key="sub_name")
        sub_func = st.text_input(
            t("materials_sub_func"), key="sub_func",
            value=t("func_base_resin"),
        )
        sub_usage = st.text_area(t("materials_sub_usage"), key="sub_usage")

        if st.button(t("materials_sub_btn")) and sub_name:
            with st.spinner(t("materials_sub_running")):
                result = api_call(
                    "post", "/api/materials/substitute",
                    json={
                        "material_name": sub_name,
                        "material_function": sub_func,
                        "current_usage": sub_usage,
                    },
                )
            if result:
                st.markdown(f"### {t('materials_sub_result')}")
                st.markdown(result.get("suggestion", ""))
                stats = result.get("usage_stats", {})
                if stats.get("count", 0) > 0:
                    st.markdown(f"### {t('materials_sub_stats')}")
                    st.json(stats)


# ============ 页面: 知识库 ============

elif page == t("nav_knowledge"):
    from chem_agent.ui.kb_pages import render_knowledge_base_page
    render_knowledge_base_page(api_call, t, t_fmt)


# ============ 页面: 实验设计 ============

elif page == t("nav_versions"):
    from chem_agent.ui.version_pages import render_formula_versions_page
    render_formula_versions_page()
elif page == t("nav_experiment"):
    st.markdown(
        f'<div class="main-header">{t("exp_title")}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="page-desc">{t("page_desc_experiment")}</div>', unsafe_allow_html=True)

    tab_design, tab_virtual = st.tabs([t("exp_tab_design"), t("exp_tab_virtual")])

    with tab_design:
        method = st.radio(
            t("exp_method"),
            [t("exp_full_factorial"), t("exp_latin_hypercube")],
            horizontal=True, key="doe_method",
        )

        st.markdown(f"### {t('exp_factors')}")

        if "doe_factors" not in st.session_state:
            st.session_state.doe_factors = [{"name": "", "min": 0.0, "max": 100.0}]

        factors = st.session_state.doe_factors
        for i, factor in enumerate(factors):
            _fc1, _fc2, _fc3, _fc4 = st.columns([3, 2, 2, 1])
            with _fc1:
                factors[i]["name"] = st.text_input(
                    t("exp_factor_name"), value=factor["name"], key=f"doe_fn_{i}"
                )
            with _fc2:
                factors[i]["min"] = st.number_input(
                    t("exp_factor_min"), value=factor["min"], key=f"doe_min_{i}"
                )
            with _fc3:
                factors[i]["max"] = st.number_input(
                    t("exp_factor_max"), value=factor["max"], key=f"doe_max_{i}"
                )
            with _fc4:
                if len(factors) > 1 and st.button("✕", key=f"doe_del_{i}"):
                    factors.pop(i)
                    st.rerun()

        if st.button("➕", key="doe_add_factor"):
            factors.append({"name": "", "min": 0.0, "max": 100.0})
            st.rerun()

        if method == t("exp_full_factorial"):
            levels = st.slider(t("exp_levels"), 2, 5, 3, key="doe_levels")
        else:
            samples = st.slider(t("exp_samples"), 5, 100, 20, key="doe_samples")

        if st.button(t("exp_generate"), type="primary", key="btn_doe_gen"):
            valid_factors = [f for f in factors if f["name"].strip()]
            if not valid_factors:
                st.warning(t("exp_no_factors"))
            else:
                import itertools
                import numpy as np

                if method == t("exp_full_factorial"):
                    # 全因子设计
                    factor_levels = []
                    for f in valid_factors:
                        factor_levels.append(
                            np.linspace(f["min"], f["max"], levels).tolist()
                        )
                    combos = list(itertools.product(*factor_levels))
                    matrix = pd.DataFrame(
                        combos, columns=[f["name"] for f in valid_factors]
                    )
                else:
                    # 拉丁超立方
                    n_factors = len(valid_factors)
                    rng = np.random.default_rng(42)
                    lhs_matrix = np.zeros((samples, n_factors))
                    for j in range(n_factors):
                        perm = rng.permutation(samples)
                        lhs_matrix[:, j] = (perm + rng.random(samples)) / samples
                    # 缩放到实际范围
                    for j, f in enumerate(valid_factors):
                        lhs_matrix[:, j] = f["min"] + lhs_matrix[:, j] * (f["max"] - f["min"])
                    matrix = pd.DataFrame(
                        lhs_matrix, columns=[f["name"] for f in valid_factors]
                    )

                st.session_state.doe_matrix = matrix
                st.markdown(f"### {t('exp_matrix')}")
                st.dataframe(matrix, use_container_width=True)

                # 导出按钮
                csv_data = matrix.to_csv(index=False).encode("utf-8")
                st.download_button(
                    t("exp_export"),
                    data=csv_data,
                    file_name="doe_matrix.csv",
                    mime="text/csv",
                    key="dl_doe",
                )

    with tab_virtual:
        st.markdown(t("exp_run_virtual"))
        if "doe_matrix" in st.session_state and st.session_state.doe_matrix is not None:
            matrix = st.session_state.doe_matrix
            st.dataframe(matrix.head(10), use_container_width=True)

            pred_cat_doe = st.selectbox(
                t("predict_category"), _category_options(), key="doe_pred_cat"
            )
            default_props_doe = {"zh": "硬度, 光泽度", "en": "Hardness, Gloss"}
            target_props_doe = st.text_input(
                t("predict_target_props"),
                default_props_doe.get(_get_lang(), default_props_doe["zh"]),
                key="doe_target_props",
            )

            if st.button(t("exp_run_virtual"), type="primary", key="btn_doe_virtual"):
                with st.spinner(t("exp_running")):
                    props = [p.strip() for p in target_props_doe.split(",")]
                    pred_results = []
                    for _, row in matrix.iterrows():
                        items_api = [
                            {
                                "material": {"name": col, "function": "其他"},
                                "weight_percent": float(row[col]),
                            }
                            for col in matrix.columns
                        ]
                        req = {
                            "items": items_api,
                            "category": _category_to_api(pred_cat_doe),
                            "target_properties": props,
                        }
                        result = api_call("post", "/api/predict", json=req)
                        if result:
                            row_result = {col: float(row[col]) for col in matrix.columns}
                            for pr in result:
                                row_result[pr["property_name"]] = pr["predicted_value"]
                            pred_results.append(row_result)
                    if pred_results:
                        pred_df = pd.DataFrame(pred_results)
                        st.dataframe(pred_df, use_container_width=True)

                        csv_data = pred_df.to_csv(index=False).encode("utf-8")
                        st.download_button(
                            t("exp_export"),
                            data=csv_data,
                            file_name="doe_virtual_results.csv",
                            mime="text/csv",
                            key="dl_doe_virtual",
                        )
        else:
            st.info(t("exp_no_factors"))


# ============ 页面: 后台管理 ============

elif page == t("nav_admin"):
    from chem_agent.ui.admin_pages import render_admin_panel
    render_admin_panel(api_call, t, t_fmt, user_info)
