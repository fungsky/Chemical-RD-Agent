"""后台管理页面：AnythingLLM 风格分类导航 + 卡片式 Provider 选择"""

from typing import Callable, Optional

import pandas as pd
import streamlit as st


# ============================================================
# 全局 Admin CSS
# ============================================================

_ADMIN_CSS = """
<style>
/* ---- 侧边栏分组标题 ---- */
.admin-grp {
    font-size: 0.72em; font-weight: 700; color: #9ca3af;
    text-transform: uppercase; letter-spacing: 0.1em;
    margin: 1.2em 0 0.3em 0.2em; padding: 0;
}
.admin-grp:first-child { margin-top: 0.3em; }

/* ---- 状态指示器栏 ---- */
.admin-status-bar {
    display: flex; flex-wrap: wrap; gap: 1.5em;
    background: #f8fafc; border: 1px solid #e2e8f0;
    border-radius: 8px; padding: 0.8em 1.2em; margin-bottom: 1.2em;
}
.admin-si { display: flex; align-items: center; gap: 0.5em; }
.admin-dot {
    width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
}
.admin-dot-ok  { background: #10b981; box-shadow: 0 0 0 3px rgba(16,185,129,0.15); }
.admin-dot-err { background: #ef4444; box-shadow: 0 0 0 3px rgba(239,68,68,0.12); }
.admin-si-label { font-size: 0.82em; color: #6b7280; }
.admin-si-val   { font-size: 0.88em; font-weight: 600; color: #1f2937; }

/* ---- Provider 卡片 ---- */
.pcard {
    text-align: center; padding: 0.8em 0.4em 0.3em;
    border: 1px solid #e5e7eb; border-radius: 10px;
    background: #fafbfc; transition: all 0.15s;
    min-height: 90px; cursor: default;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
}
.pcard:hover { border-color: #a5b4fc; background: #f8f9ff; }
.pcard-sel {
    text-align: center; padding: 0.8em 0.4em 0.3em;
    border: 2px solid #667eea; border-radius: 10px;
    background: rgba(102,126,234,0.05);
    min-height: 90px;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
}
.pcard-icon { font-size: 1.6em; line-height: 1; }
.pcard-name { font-weight: 600; font-size: 0.88em; margin: 0.2em 0; color: #1f2937; }
.pcard-desc { font-size: 0.72em; color: #9ca3af; line-height: 1.3; }
</style>
"""


# ============================================================
# Provider 预设数据
# ============================================================

PROVIDER_PRESETS = {
    "ollama": {
        "base_url": "http://localhost:11434",
        "default_chat_model": "qwen3:4b",
        "default_emb_model": "nomic-embed-text",
        "needs_api_key": False,
    },
    "lm_studio": {
        "base_url": "http://localhost:1234/v1",
        "default_chat_model": "",
        "default_emb_model": "",
        "needs_api_key": False,
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "default_chat_model": "gpt-4o-mini",
        "default_emb_model": "text-embedding-3-small",
        "needs_api_key": True,
    },
    "azure_openai": {
        "base_url": "",
        "default_chat_model": "",
        "default_emb_model": "",
        "needs_api_key": True,
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "default_chat_model": "deepseek-chat",
        "default_emb_model": "",
        "needs_api_key": True,
    },
    "zhipu": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "default_chat_model": "glm-4-flash",
        "default_emb_model": "embedding-3",
        "needs_api_key": True,
    },
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_chat_model": "qwen-plus",
        "default_emb_model": "text-embedding-v3",
        "needs_api_key": True,
    },
    "moonshot": {
        "base_url": "https://api.moonshot.cn/v1",
        "default_chat_model": "moonshot-v1-8k",
        "default_emb_model": "",
        "needs_api_key": True,
    },
    "yi": {
        "base_url": "https://api.lingyiwanwu.com/v1",
        "default_chat_model": "yi-lightning",
        "default_emb_model": "",
        "needs_api_key": True,
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "default_chat_model": "gemini-2.0-flash",
        "default_emb_model": "text-embedding-004",
        "needs_api_key": True,
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com/v1",
        "default_chat_model": "claude-3-5-sonnet-20241022",
        "default_emb_model": "",
        "needs_api_key": True,
    },
    "custom_openai": {
        "base_url": "",
        "default_chat_model": "",
        "default_emb_model": "",
        "needs_api_key": False,
    },
}

_PROVIDER_CODES = list(PROVIDER_PRESETS.keys())

_PROVIDER_ICONS = {
    "ollama": "\U0001f999",        # 🦙
    "lm_studio": "\U0001f5a5",    # 🖥
    "openai": "\U0001f916",        # 🤖
    "azure_openai": "\u2601",      # ☁
    "deepseek": "\U0001f50d",      # 🔍
    "zhipu": "\u2728",             # ✨
    "qwen": "\U0001f31f",          # 🌟
    "moonshot": "\U0001f319",      # 🌙
    "yi": "\U0001f52e",            # 🔮
    "gemini": "\U0001f48e",        # 💎
    "anthropic": "\U0001f9e0",     # 🧠
    "custom_openai": "\u2699",     # ⚙
    "same_as_llm": "\U0001f517",   # 🔗
}


def _provider_display(code: str, t: Callable) -> str:
    return t(f"provider_{code}")


def _provider_desc(code: str, t: Callable) -> str:
    return t(f"provider_{code}_desc")


# ============================================================
# 每个 Provider 需要的 LLM 字段定义
# ============================================================
# field_order: 按顺序渲染的字段列表
# "base_url", "model", "api_key", "api_key_optional",
# "azure_deployment", "azure_api_version", "max_tokens"

_LLM_FIELD_ORDER: dict[str, list[str]] = {
    "ollama":       ["base_url", "model", "max_tokens"],
    "lm_studio":    ["base_url", "model", "max_tokens"],
    "openai":       ["api_key", "model", "base_url", "max_tokens"],
    "azure_openai": ["base_url", "api_key", "azure_deployment", "azure_api_version", "max_tokens"],
    "deepseek":     ["api_key", "model", "base_url", "max_tokens"],
    "zhipu":        ["api_key", "model", "base_url", "max_tokens"],
    "qwen":         ["api_key", "model", "base_url", "max_tokens"],
    "moonshot":     ["api_key", "model", "base_url", "max_tokens"],
    "yi":           ["api_key", "model", "base_url", "max_tokens"],
    "gemini":       ["api_key", "model", "base_url", "max_tokens"],
    "anthropic":    ["api_key", "model", "base_url", "max_tokens"],
    "custom_openai": ["base_url", "model", "api_key_optional", "max_tokens"],
}

# 每个 Provider 需要的 Embedder 字段 (不含 same_as_llm)
_EMB_FIELD_ORDER: dict[str, list[str]] = {
    "ollama":       ["base_url", "model"],
    "lm_studio":    ["base_url", "model"],
    "openai":       ["api_key", "model", "base_url"],
    "azure_openai": ["base_url", "api_key", "model"],
    "deepseek":     ["api_key", "model", "base_url"],
    "zhipu":        ["api_key", "model", "base_url"],
    "qwen":         ["api_key", "model", "base_url"],
    "moonshot":     ["api_key", "model", "base_url"],
    "yi":           ["api_key", "model", "base_url"],
    "gemini":       ["api_key", "model", "base_url"],
    "anthropic":    ["api_key", "model", "base_url"],
    "custom_openai": ["base_url", "model", "api_key_optional"],
}


# ============================================================
# 菜单分组结构
# ============================================================

_MENU_GROUPS = [
    ("admin_menu_ai_providers", [
        ("llm_settings",        "admin_menu_llm",        "\U0001f916"),   # 🤖
        ("embedder_settings",   "admin_menu_embedder",   "\U0001f4d0"),   # 📐
        ("vectordb_settings",   "admin_menu_vectordb",   "\U0001f5c4"),   # 🗄
    ]),
    ("admin_menu_users_perms", [
        ("user_management",     "admin_tab_users",       "\U0001f465"),   # 👥
        ("role_management",     "admin_tab_roles",       "\U0001f6e1"),   # 🛡
        ("category_management", "admin_tab_categories",  "\U0001f4c1"),   # 📁
    ]),
    ("admin_menu_system", [
        ("system_config",       "admin_tab_config",      "\u2699"),       # ⚙
        ("audit_logs",          "admin_tab_audit",       "\U0001f4cb"),   # 📋
        ("data_management",     "admin_tab_data",        "\U0001f5c4"),   # 🗄
    ]),
]


# ============================================================
# 主入口
# ============================================================

def render_admin_panel(
    api_call: Callable,
    t: Callable[[str], str],
    t_fmt: Callable,
    user_info: dict,
):
    """渲染后台管理面板 (AnythingLLM 风格左右分栏 + 分组导航)"""
    # 注入全局 CSS
    st.markdown(_ADMIN_CSS, unsafe_allow_html=True)

    st.markdown(
        f'<div class="main-header">{t("admin_title")}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="page-desc">{t("page_desc_admin")}</div>',
        unsafe_allow_html=True,
    )

    # 左右分栏 (1:4)
    left_col, right_col = st.columns([1, 4])

    with left_col:
        selected_page = _render_sidebar_nav(t)

    with right_col:
        _PAGE_DISPATCH = {
            "llm_settings":        lambda: _render_llm_settings(api_call, t, t_fmt),
            "embedder_settings":   lambda: _render_embedder_settings(api_call, t, t_fmt),
            "vectordb_settings":   lambda: _render_vectordb_settings(api_call, t, t_fmt),
            "user_management":     lambda: _render_user_management(api_call, t, t_fmt),
            "role_management":     lambda: _render_role_management(api_call, t, t_fmt),
            "category_management": lambda: _render_category_management(api_call, t, t_fmt),
            "system_config":       lambda: _render_config_management(api_call, t, t_fmt),
            "audit_logs":          lambda: _render_audit_logs(api_call, t, t_fmt),
            "data_management":     lambda: _render_data_management(api_call, t),
        }
        handler = _PAGE_DISPATCH.get(selected_page)
        if handler:
            handler()


# ============================================================
# 侧边栏分组导航
# ============================================================

def _render_sidebar_nav(t: Callable) -> str:
    """渲染 AnythingLLM 风格分组导航按钮，返回选中的 page key"""
    current = st.session_state.get("admin_menu_sel", "llm_settings")

    for group_key, items in _MENU_GROUPS:
        # 分组标题
        st.markdown(
            f'<p class="admin-grp">{t(group_key)}</p>',
            unsafe_allow_html=True,
        )
        # 菜单项按钮
        for page_key, label_key, icon in items:
            is_active = (page_key == current)
            label = f"{icon}  {t(label_key)}"
            if st.button(
                label,
                key=f"nav_{page_key}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                if page_key != current:
                    st.session_state["admin_menu_sel"] = page_key
                    st.rerun()

    return current


# ============================================================
# 状态指示器栏
# ============================================================

def _render_status_bar(api_call: Callable, t: Callable):
    """渲染 LLM / Embedding 配置状态"""
    llm_cfg = api_call("get", "/api/admin/llm/config") or {}
    emb_cfg = api_call("get", "/api/admin/embedding/config") or {}

    llm_prov = llm_cfg.get("provider", "")
    emb_prov = emb_cfg.get("provider", "")

    def _item(label: str, is_ok: bool, value: str) -> str:
        dot = "admin-dot-ok" if is_ok else "admin-dot-err"
        return (
            f'<div class="admin-si">'
            f'<span class="admin-dot {dot}"></span>'
            f'<span class="admin-si-label">{label}:</span>'
            f'<span class="admin-si-val">{value}</span>'
            f'</div>'
        )

    llm_val = (
        f"{_provider_display(llm_prov, t)} / {llm_cfg.get('model', '?')}"
        if llm_prov else t("status_not_configured")
    )
    emb_val = (
        f"{_provider_display(emb_prov, t)} / {emb_cfg.get('model', '?')}"
        if emb_prov else t("status_not_configured")
    )

    html = (
        f'<div class="admin-status-bar">'
        f'{_item("LLM", bool(llm_prov), llm_val)}'
        f'{_item("Embedding", bool(emb_prov), emb_val)}'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ============================================================
# Provider 卡片式选择器
# ============================================================

def _render_provider_grid(
    t: Callable,
    providers: list[str],
    selected: str,
    key_prefix: str,
) -> Optional[str]:
    """渲染 Provider 卡片网格 (3列)。

    返回被点击的 provider code (如果有), 否则 None.
    """
    # 搜索/过滤
    search = st.text_input(
        t("search_providers"),
        key=f"{key_prefix}_search",
        placeholder=t("search_providers"),
        label_visibility="collapsed",
    )
    if search:
        search_lower = search.lower()
        filtered = [
            p for p in providers
            if search_lower in _provider_display(p, t).lower()
            or search_lower in _provider_desc(p, t).lower()
            or search_lower in p.lower()
        ]
    else:
        filtered = providers

    if not filtered:
        st.info(t("no_providers_found"))
        return None

    clicked = None

    for row_start in range(0, len(filtered), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            idx = row_start + j
            if idx >= len(filtered):
                break
            code = filtered[idx]
            icon = _PROVIDER_ICONS.get(code, "\u2699")
            name = _provider_display(code, t)
            desc = _provider_desc(code, t)
            is_sel = (code == selected)

            with col:
                # 视觉卡片
                cls = "pcard-sel" if is_sel else "pcard"
                st.markdown(
                    f'<div class="{cls}">'
                    f'<div class="pcard-icon">{icon}</div>'
                    f'<div class="pcard-name">{name}</div>'
                    f'<div class="pcard-desc">{desc}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                # 选择按钮
                btn_label = f"\u2714 {name}" if is_sel else name
                if st.button(
                    btn_label,
                    key=f"{key_prefix}_{code}",
                    use_container_width=True,
                    type="primary" if is_sel else "secondary",
                ):
                    clicked = code

    return clicked


# ============================================================
# LLM 设置页 (动态字段 + Token 窗口 + 高级设置)
# ============================================================

def _render_llm_settings(api_call, t, t_fmt):
    # 状态栏
    _render_status_bar(api_call, t)

    st.markdown(f"### {t('llm_settings_title')}")
    st.caption(t("llm_settings_desc"))

    # 加载当前保存的配置
    llm_cfg = api_call("get", "/api/admin/llm/config") or {}
    saved_provider = llm_cfg.get("provider", "")

    # 确定当前选中的 provider (session_state 优先于 API 返回值)
    if "_llm_sel_prov" not in st.session_state:
        st.session_state["_llm_sel_prov"] = saved_provider or ""
    selected_provider = st.session_state["_llm_sel_prov"]

    # Provider 选择
    st.markdown(f"**{t('llm_select_provider')}**")
    clicked = _render_provider_grid(t, _PROVIDER_CODES, selected_provider, "llm_card")
    if clicked and clicked != selected_provider:
        st.session_state["_llm_sel_prov"] = clicked
        st.rerun()

    if not selected_provider:
        st.warning(t("llm_not_configured"))
        return

    preset = PROVIDER_PRESETS.get(selected_provider, {})
    is_saved = (saved_provider == selected_provider)

    # 配置表单 — 根据 Provider 动态渲染字段
    st.markdown("---")
    with st.container(border=True):
        st.markdown(f"**{_PROVIDER_ICONS.get(selected_provider, '')}  "
                    f"{_provider_display(selected_provider, t)}** — "
                    f"{_provider_desc(selected_provider, t)}")

        fields = _LLM_FIELD_ORDER.get(
            selected_provider,
            ["base_url", "model", "api_key", "max_tokens"],
        )

        # 收集表单值
        base_url = ""
        model = ""
        api_key = ""
        azure_deployment = ""
        azure_api_version = ""
        max_tokens = 4096

        for field in fields:
            if field == "base_url":
                default_url = (
                    llm_cfg.get("base_url", "")
                    if is_saved
                    else preset.get("base_url", "")
                )
                label = (
                    t("llm_azure_endpoint")
                    if selected_provider == "azure_openai"
                    else t("llm_base_url")
                )
                base_url = st.text_input(
                    label,
                    value=default_url,
                    key="llm_base_url_input",
                    help=(
                        f"Default: {preset['base_url']}"
                        if preset.get("base_url")
                        else None
                    ),
                )

            elif field == "model":
                default_model = (
                    llm_cfg.get("model", "")
                    if is_saved
                    else preset.get("default_chat_model", "")
                )
                model = st.text_input(
                    t("llm_model_name"),
                    value=default_model,
                    key="llm_model_input",
                )

            elif field == "api_key":
                api_key = st.text_input(
                    t("llm_api_key"),
                    value="",
                    type="password",
                    key="llm_api_key_input",
                    placeholder=llm_cfg.get("api_key", "") or "",
                )

            elif field == "api_key_optional":
                api_key = st.text_input(
                    t("llm_api_key_optional"),
                    value="",
                    type="password",
                    key="llm_api_key_input_opt",
                    placeholder=llm_cfg.get("api_key", "") or "",
                )

            elif field == "azure_deployment":
                azure_deployment = st.text_input(
                    t("llm_azure_deployment"),
                    value=(
                        llm_cfg.get("azure_deployment", "")
                        if is_saved else ""
                    ),
                    key="llm_azure_dep_input",
                )

            elif field == "azure_api_version":
                azure_api_version = st.text_input(
                    t("llm_azure_api_version"),
                    value=(
                        llm_cfg.get("azure_api_version", "2024-02-01")
                        if is_saved else "2024-02-01"
                    ),
                    key="llm_azure_ver_input",
                )

            elif field == "max_tokens":
                default_mt = (
                    int(llm_cfg.get("max_tokens", 4096))
                    if is_saved else 4096
                )
                max_tokens = st.number_input(
                    t("llm_max_tokens"),
                    value=default_mt,
                    min_value=256,
                    max_value=128000,
                    step=256,
                    key="llm_max_tokens_input",
                    help=t("llm_max_tokens_help"),
                )

    # 高级设置折叠区
    with st.expander(t("llm_advanced_settings"), expanded=False):
        default_temp = (
            float(llm_cfg.get("temperature", 0.7))
            if is_saved else 0.7
        )
        temperature = st.slider(
            t("llm_temperature"),
            min_value=0.0,
            max_value=2.0,
            value=default_temp,
            step=0.1,
            key="llm_temperature_input",
            help=t("llm_temperature_help"),
        )

    # 测试 & 保存按钮
    btn_col1, btn_col2, _ = st.columns([1, 1, 2])
    with btn_col1:
        if st.button(t("llm_test_btn"), key="btn_test_llm", use_container_width=True):
            with st.spinner(t("llm_testing")):
                test_result = api_call("post", "/api/admin/llm/test", json={
                    "provider": selected_provider,
                    "base_url": base_url,
                    "model": model,
                    "api_key": api_key or llm_cfg.get("api_key", ""),
                    "test_type": "chat",
                })
            if test_result and test_result.get("success"):
                st.success(t_fmt("llm_test_success", test_result.get("latency_ms", 0)))
            else:
                st.error(t_fmt("llm_test_failed", (test_result or {}).get("error", "Unknown")))

    with btn_col2:
        if st.button(t("llm_save_btn"), type="primary", key="btn_save_llm", use_container_width=True):
            payload = {
                "provider": selected_provider,
                "base_url": base_url,
                "model": model,
                "api_key": api_key or llm_cfg.get("api_key", ""),
                "azure_deployment": azure_deployment,
                "azure_api_version": azure_api_version,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            result = api_call("post", "/api/admin/llm/config", json=payload)
            if result and result.get("message"):
                st.success(t("llm_config_saved"))
                st.session_state.pop("_llm_sel_prov", None)
                st.rerun()
            else:
                st.error(t_fmt("llm_config_save_failed", str(result)))


# ============================================================
# Embedder 设置页 (动态字段)
# ============================================================

def _render_embedder_settings(api_call, t, t_fmt):
    # 状态栏
    _render_status_bar(api_call, t)

    st.markdown(f"### {t('emb_settings_title')}")
    st.caption(t("emb_settings_desc"))

    # 加载当前配置
    emb_cfg = api_call("get", "/api/admin/embedding/config") or {}
    saved_provider = emb_cfg.get("provider", "")

    # Embedder Provider 列表: "同LLM提供商" + 所有标准 Provider
    emb_provider_codes = ["same_as_llm"] + _PROVIDER_CODES

    if "_emb_sel_prov" not in st.session_state:
        st.session_state["_emb_sel_prov"] = saved_provider or "same_as_llm"
    selected_provider = st.session_state["_emb_sel_prov"]

    # Provider 选择
    st.markdown(f"**{t('llm_select_provider')}**")
    clicked = _render_provider_grid(t, emb_provider_codes, selected_provider, "emb_card")
    if clicked and clicked != selected_provider:
        st.session_state["_emb_sel_prov"] = clicked
        st.rerun()

    if not selected_provider:
        return

    is_saved = (saved_provider == selected_provider)

    # 配置表单 — 根据 Provider 动态渲染字段
    st.markdown("---")
    with st.container(border=True):
        icon = _PROVIDER_ICONS.get(selected_provider, "")
        st.markdown(f"**{icon}  {_provider_display(selected_provider, t)}** — "
                    f"{_provider_desc(selected_provider, t)}")

        emb_model = ""
        emb_base_url = ""
        emb_api_key = ""

        if selected_provider == "same_as_llm":
            # "同LLM提供商" 模式: 只需模型名
            default_model = emb_cfg.get("model", "") if is_saved else ""
            emb_model = st.text_input(
                t("llm_model_name"),
                value=default_model,
                key="emb_model_input",
                help=t("emb_same_as_llm_hint"),
            )
        else:
            # 按 Provider 动态渲染字段
            preset = PROVIDER_PRESETS.get(selected_provider, {})
            fields = _EMB_FIELD_ORDER.get(
                selected_provider,
                ["base_url", "model", "api_key"],
            )

            for field in fields:
                if field == "base_url":
                    default_url = (
                        emb_cfg.get("base_url", "")
                        if is_saved
                        else preset.get("base_url", "")
                    )
                    emb_base_url = st.text_input(
                        t("llm_base_url"),
                        value=default_url,
                        key="emb_base_url_input",
                    )

                elif field == "model":
                    default_model = (
                        emb_cfg.get("model", "")
                        if is_saved
                        else preset.get("default_emb_model", "")
                    )
                    emb_model = st.text_input(
                        t("llm_model_name"),
                        value=default_model,
                        key="emb_model_input",
                    )

                elif field == "api_key":
                    emb_api_key = st.text_input(
                        t("llm_api_key"),
                        value="",
                        type="password",
                        key="emb_api_key_input",
                        placeholder=emb_cfg.get("api_key", "") or "",
                    )

                elif field == "api_key_optional":
                    emb_api_key = st.text_input(
                        t("llm_api_key_optional"),
                        value="",
                        type="password",
                        key="emb_api_key_input_opt",
                        placeholder=emb_cfg.get("api_key", "") or "",
                    )

    # 测试 & 保存按钮
    btn_col1, btn_col2, _ = st.columns([1, 1, 2])
    with btn_col1:
        if st.button(t("llm_test_btn"), key="btn_test_emb", use_container_width=True):
            test_provider = selected_provider
            test_url = emb_base_url
            test_key = emb_api_key or emb_cfg.get("api_key", "")
            if selected_provider == "same_as_llm":
                llm_cfg = api_call("get", "/api/admin/llm/config") or {}
                test_provider = llm_cfg.get("provider", "ollama")
                test_url = llm_cfg.get("base_url", "")
                test_key = llm_cfg.get("api_key", "")

            with st.spinner(t("llm_testing")):
                test_result = api_call("post", "/api/admin/llm/test", json={
                    "provider": test_provider,
                    "base_url": test_url,
                    "model": emb_model,
                    "api_key": test_key,
                    "test_type": "embedding",
                })
            if test_result and test_result.get("success"):
                st.success(t_fmt("llm_test_success", test_result.get("latency_ms", 0)))
            else:
                st.error(t_fmt("llm_test_failed", (test_result or {}).get("error", "Unknown")))

    with btn_col2:
        if st.button(t("emb_save_btn"), type="primary", key="btn_save_emb", use_container_width=True):
            # 验证模型名必填
            if not emb_model:
                st.error(t("emb_model_required"))
                return
            payload = {
                "provider": selected_provider,
                "base_url": emb_base_url,
                "model": emb_model,
                "api_key": emb_api_key or emb_cfg.get("api_key", ""),
            }
            result = api_call("post", "/api/admin/embedding/config", json=payload)
            if result and result.get("message"):
                st.success(t("emb_config_saved"))
                st.session_state.pop("_emb_sel_prov", None)
                st.rerun()
            else:
                st.error(t_fmt("llm_config_save_failed", str(result)))


# ============================================================
# 向量数据库设置页
# ============================================================

def _render_vectordb_settings(api_call, t, t_fmt):
    st.markdown(f"### {t('vectordb_settings_title')}")
    st.caption(t("vectordb_settings_desc"))

    # 当前仅支持 ChromaDB
    with st.container(border=True):
        st.markdown(
            f'<div class="pcard-sel">'
            f'<div class="pcard-icon">\U0001f7e2</div>'
            f'<div class="pcard-name">ChromaDB</div>'
            f'<div class="pcard-desc">{t("vectordb_chroma_desc")}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # 知识库统计
    kb_stats = api_call("get", "/api/kb/stats")
    if kb_stats:
        c1, c2, c3 = st.columns(3)
        c1.metric(t("data_stat_docs"), kb_stats.get("total_documents", 0))
        c2.metric(t("data_stat_chunks"), kb_stats.get("total_chunks", 0))
        c3.metric(t("vectordb_stat_collections"), kb_stats.get("collections", 1))

    # 配置信息 (只读 — 通过环境变量/settings 配置)
    with st.container(border=True):
        st.markdown(f"**{t('vectordb_config_title')}**")
        st.caption(t("vectordb_config_hint"))

        # 从系统配置获取当前值
        configs = api_call("get", "/api/admin/config") or []
        config_map = {c["key"]: c["value"] for c in configs}

        vdb_c1, vdb_c2 = st.columns(2)
        with vdb_c1:
            st.text_input(
                t("vectordb_persist_dir"),
                value=config_map.get("chroma_persist_dir", "./data/chromadb"),
                disabled=True,
                key="vdb_persist_dir",
            )
            st.text_input(
                t("vectordb_embedding_dim"),
                value=str(config_map.get("embedding_dim", "768")),
                disabled=True,
                key="vdb_emb_dim",
            )
        with vdb_c2:
            st.text_input(
                t("vectordb_similarity_topk"),
                value=str(config_map.get("similarity_top_k", "5")),
                disabled=True,
                key="vdb_topk",
            )
            st.text_input(
                t("vectordb_chunk_size"),
                value=str(config_map.get("chunk_size", "1000")),
                disabled=True,
                key="vdb_chunk_size",
            )


# ============================================================
# 用户管理
# ============================================================

def _render_user_management(api_call, t, t_fmt):
    st.markdown(f"### {t('user_list_title')}")

    users = api_call("get", "/api/admin/users") or []

    # 创建用户表单
    with st.expander(t("user_create_title"), expanded=False):
        with st.form("create_user_form"):
            cu_col1, cu_col2 = st.columns(2)
            with cu_col1:
                new_username = st.text_input(t("login_username"), key="cu_username")
                new_password = st.text_input(t("login_password"), type="password", key="cu_password")
            with cu_col2:
                new_fullname = st.text_input(t("user_col_fullname"), key="cu_fullname")
                new_email = st.text_input(t("user_col_email"), key="cu_email")
            if st.form_submit_button(t("user_btn_create"), type="primary"):
                if new_username and new_password:
                    result = api_call("post", "/api/admin/users", json={
                        "username": new_username,
                        "password": new_password,
                        "full_name": new_fullname or None,
                        "email": new_email or None,
                    })
                    if result:
                        st.success(t_fmt("user_created", new_username))
                        st.rerun()

    if not users:
        return

    # 用户列表表格
    rows = []
    for u in users:
        rows.append({
            t("user_col_id"): u["id"],
            t("user_col_username"): u["username"],
            t("user_col_fullname"): u.get("full_name") or "-",
            t("user_col_email"): u.get("email") or "-",
            t("user_col_roles"): ", ".join(u.get("roles", [])),
            t("user_col_active"): t("user_active") if u.get("is_active") else t("user_inactive"),
            t("user_col_last_login"): (u.get("last_login") or "-")[:19],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # 用户操作区
    st.markdown("---")
    op_col1, op_col2 = st.columns(2)

    with op_col1:
        user_ids = [u["id"] for u in users]
        user_labels = [f"{u['id']} - {u['username']}" for u in users]
        selected_label = st.selectbox(t("user_col_actions"), user_labels, key="user_action_sel")
        selected_uid = user_ids[user_labels.index(selected_label)] if selected_label else None

    with op_col2:
        act_col1, act_col2, act_col3 = st.columns(3)
        with act_col1:
            if st.button(t("user_btn_toggle"), key="btn_toggle_user"):
                if selected_uid:
                    result = api_call("post", f"/api/admin/users/{selected_uid}/toggle-active")
                    if result:
                        st.success(t("user_updated"))
                        st.rerun()
        with act_col2:
            if st.button(t("user_btn_delete"), key="btn_delete_user"):
                if selected_uid:
                    result = api_call("delete", f"/api/admin/users/{selected_uid}")
                    if result:
                        st.success(t("user_deleted"))
                        st.rerun()
        with act_col3:
            if st.button(t("user_btn_reset_pwd"), key="btn_reset_pwd"):
                if selected_uid:
                    st.session_state["show_reset_pwd"] = selected_uid

    # 重置密码对话框
    if st.session_state.get("show_reset_pwd"):
        uid = st.session_state["show_reset_pwd"]
        with st.form("reset_pwd_form"):
            new_pwd = st.text_input(t("new_password"), type="password", key="reset_pwd_input")
            if st.form_submit_button(t("user_btn_reset_pwd")):
                if new_pwd:
                    result = api_call("post", f"/api/admin/users/{uid}/reset-password", json={"new_password": new_pwd})
                    if result:
                        st.success(t("user_pwd_reset"))
                        st.session_state.pop("show_reset_pwd", None)
                        st.rerun()

    # 分配角色
    if selected_uid:
        with st.expander(t("user_assign_roles"), expanded=False):
            roles_data = api_call("get", "/api/admin/roles") or []
            if roles_data:
                target_user = next((u for u in users if u["id"] == selected_uid), {})
                current_role_names = target_user.get("roles", [])
                role_options = {r["id"]: f"{r['display_name']} ({r['name']})" for r in roles_data}
                current_ids = [r["id"] for r in roles_data if r["name"] in current_role_names]

                selected_roles = st.multiselect(
                    t("role_label"),
                    options=list(role_options.keys()),
                    default=current_ids,
                    format_func=lambda x: role_options.get(x, str(x)),
                    key="assign_roles_sel",
                )
                if st.button(t("user_assign_roles"), key="btn_assign_roles"):
                    api_call("put", f"/api/admin/users/{selected_uid}/roles", json={"role_ids": selected_roles})
                    st.success(t("user_updated"))
                    st.rerun()


# ============================================================
# 角色管理
# ============================================================

def _render_role_management(api_call, t, t_fmt):
    st.markdown(f"### {t('role_list_title')}")

    roles = api_call("get", "/api/admin/roles") or []
    perms_data = api_call("get", "/api/admin/roles/permissions") or []

    # 创建角色
    with st.expander(t("role_create_title"), expanded=False):
        with st.form("create_role_form"):
            cr_col1, cr_col2 = st.columns(2)
            with cr_col1:
                new_role_name = st.text_input(t("role_name_field"), key="cr_name")
                new_role_display = st.text_input(t("role_display_field"), key="cr_display")
            with cr_col2:
                new_role_desc = st.text_input(t("role_desc_field"), key="cr_desc")
            if st.form_submit_button(t("role_btn_create"), type="primary"):
                if new_role_name and new_role_display:
                    result = api_call("post", "/api/admin/roles", json={
                        "name": new_role_name,
                        "display_name": new_role_display,
                        "description": new_role_desc or None,
                    })
                    if result:
                        st.success(t_fmt("role_created", new_role_display))
                        st.rerun()

    if not roles:
        return

    rows = []
    for r in roles:
        rows.append({
            "ID": r["id"],
            t("role_col_name"): r["name"],
            t("role_col_display"): r["display_name"],
            t("role_col_desc"): r.get("description") or "-",
            t("role_col_system"): "\u2713" if r.get("is_system") else "-",
            t("role_col_users"): r.get("user_count", 0),
            t("role_col_perms"): len(r.get("permissions", [])),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    role_labels = {r["id"]: f"{r['display_name']} ({r['name']})" for r in roles}
    selected_role_id = st.selectbox(
        t("role_btn_edit_perms"),
        options=list(role_labels.keys()),
        format_func=lambda x: role_labels.get(x, str(x)),
        key="role_perm_sel",
    )

    if selected_role_id and perms_data:
        role_detail = next((r for r in roles if r["id"] == selected_role_id), {})
        current_perm_codes = role_detail.get("permissions", [])
        current_perm_ids = [p["id"] for p in perms_data if p["code"] in current_perm_codes]

        resources = sorted(set(p["resource"] for p in perms_data))
        selected_perm_ids = []

        cols = st.columns(min(len(resources), 4))
        for i, resource in enumerate(resources):
            with cols[i % len(cols)]:
                st.markdown(f"**{resource}**")
                res_perms = [p for p in perms_data if p["resource"] == resource]
                for p in res_perms:
                    checked = st.checkbox(
                        f"{p['action']} - {p.get('description', '')}",
                        value=p["id"] in current_perm_ids,
                        key=f"perm_{selected_role_id}_{p['id']}",
                    )
                    if checked:
                        selected_perm_ids.append(p["id"])

        if st.button(t("role_perms_updated"), key="btn_save_perms", type="primary"):
            api_call("put", f"/api/admin/roles/{selected_role_id}/permissions", json={"permission_ids": selected_perm_ids})
            st.success(t("role_perms_updated"))
            st.rerun()

        if not role_detail.get("is_system"):
            if st.button(t("user_btn_delete"), key="btn_delete_role"):
                api_call("delete", f"/api/admin/roles/{selected_role_id}")
                st.success(t("role_deleted"))
                st.rerun()
        else:
            st.info(t("role_system_hint"))


# ============================================================
# 分类管理
# ============================================================

def _render_category_management(api_call, t, t_fmt):
    st.markdown(f"### {t('cat_mgmt_title')}")

    cat_tab1, cat_tab2 = st.tabs([t("cat_tab_product"), t("cat_tab_function")])

    for cat_type, tab in [("product", cat_tab1), ("function", cat_tab2)]:
        with tab:
            cats = api_call("get", f"/api/admin/categories?type={cat_type}") or []

            if cats:
                rows = []
                for c in cats:
                    rows.append({
                        "ID": c["id"],
                        t("cat_col_code"): c["code"],
                        t("cat_col_zh"): c["display_zh"],
                        t("cat_col_en"): c["display_en"],
                        t("cat_col_order"): c.get("sort_order", 0),
                        t("cat_col_enabled"): "\u2713" if c.get("is_enabled", True) else "\u2717",
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            with st.expander(t("cat_btn_add"), expanded=False):
                with st.form(f"add_cat_{cat_type}_form"):
                    cc1, cc2 = st.columns(2)
                    with cc1:
                        new_code = st.text_input(t("cat_col_code"), key=f"nc_code_{cat_type}")
                        new_zh = st.text_input(t("cat_col_zh"), key=f"nc_zh_{cat_type}")
                    with cc2:
                        new_en = st.text_input(t("cat_col_en"), key=f"nc_en_{cat_type}")
                        new_order = st.number_input(t("cat_col_order"), value=0, key=f"nc_order_{cat_type}")
                    if st.form_submit_button(t("cat_btn_add"), type="primary"):
                        if new_code and new_zh and new_en:
                            result = api_call("post", "/api/admin/categories", json={
                                "type": cat_type,
                                "code": new_code,
                                "display_zh": new_zh,
                                "display_en": new_en,
                                "sort_order": new_order,
                            })
                            if result:
                                st.session_state.pop("_dyn_cats_product", None)
                                st.session_state.pop("_dyn_cats_function", None)
                                st.success(t("cat_created"))
                                st.rerun()

            if cats:
                cat_labels = {c["id"]: f"{c['code']} - {c['display_zh']}" for c in cats}
                del_cat_id = st.selectbox(
                    t("user_btn_delete"),
                    options=list(cat_labels.keys()),
                    format_func=lambda x: cat_labels.get(x, str(x)),
                    key=f"del_cat_sel_{cat_type}",
                )
                if st.button(t("user_btn_delete"), key=f"btn_del_cat_{cat_type}"):
                    api_call("delete", f"/api/admin/categories/{del_cat_id}")
                    st.session_state.pop("_dyn_cats_product", None)
                    st.session_state.pop("_dyn_cats_function", None)
                    st.success(t("cat_deleted"))
                    st.rerun()


# ============================================================
# 系统配置
# ============================================================

def _render_config_management(api_call, t, t_fmt):
    st.markdown(f"### {t('config_title')}")

    configs = api_call("get", "/api/admin/config") or []
    # 过滤掉 llm.* 和 emb.* 前缀的配置（已由 LLM/Embedder 页面管理）
    configs = [c for c in configs if not c["key"].startswith(("llm.", "emb."))]

    edited_configs = []
    if configs:
        for cfg in configs:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.text(cfg["key"])
            with col2:
                new_val = st.text_input(
                    cfg.get("description") or cfg["key"],
                    value=cfg["value"],
                    key=f"cfg_{cfg['key']}",
                    label_visibility="collapsed",
                )
                edited_configs.append({"key": cfg["key"], "value": new_val, "description": cfg.get("description")})

    with st.expander(t("config_add"), expanded=False):
        with st.form("add_config_form"):
            ac1, ac2, ac3 = st.columns(3)
            with ac1:
                add_key = st.text_input(t("config_key"), key="add_cfg_key")
            with ac2:
                add_val = st.text_input(t("config_value"), key="add_cfg_val")
            with ac3:
                add_desc = st.text_input(t("config_desc"), key="add_cfg_desc")
            if st.form_submit_button(t("config_add")):
                if add_key and add_val:
                    edited_configs.append({"key": add_key, "value": add_val, "description": add_desc or None})

    if st.button(t("config_save"), type="primary", key="btn_save_config"):
        if edited_configs:
            api_call("put", "/api/admin/config", json={"configs": edited_configs})
            st.success(t("config_saved"))
            st.rerun()


# ============================================================
# 审计日志
# ============================================================

def _render_audit_logs(api_call, t, t_fmt):
    st.markdown(f"### {t('audit_title')}")

    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        filter_action = st.text_input(t("audit_filter_action"), key="audit_f_action")
    with fc2:
        filter_resource = st.text_input(t("audit_filter_resource"), key="audit_f_resource")
    with fc3:
        filter_page = st.number_input(t("audit_page"), value=1, min_value=1, key="audit_page")
    with fc4:
        filter_limit = st.selectbox("Limit", [20, 50, 100], index=1, key="audit_limit")

    params = {"page": filter_page, "limit": filter_limit}
    if filter_action:
        params["action"] = filter_action
    if filter_resource:
        params["resource_type"] = filter_resource

    data = api_call("get", "/api/admin/audit", params=params)
    if data:
        items = data.get("items", [])
        total = data.get("total", 0)
        st.caption(t_fmt("audit_total", total))

        if items:
            rows = []
            for log in items:
                rows.append({
                    t("audit_col_time"): (log.get("timestamp") or "-")[:19],
                    t("audit_col_user"): log.get("username") or "-",
                    t("audit_col_action"): log.get("action", "-"),
                    t("audit_col_resource"): log.get("resource_type") or "-",
                    t("audit_col_detail"): (log.get("details") or "-")[:80],
                    t("audit_col_status"): log.get("status", "-"),
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ============================================================
# 数据管理
# ============================================================

def _render_data_management(api_call, t):
    st.warning(t("data_mgmt_warning"))

    # ---- 知识图谱 ----
    st.markdown(f"### {t('data_section_graph')}")
    graph_stats = api_call("get", "/api/graph/stats")
    if graph_stats:
        c1, c2, c3 = st.columns(3)
        c1.metric(t("data_stat_formulas"), graph_stats.get("formulas", 0))
        c2.metric(t("data_stat_materials"), graph_stats.get("materials", 0))
        c3.metric(t("data_stat_tests"), graph_stats.get("performance_tests", 0))

    confirm_graph = st.checkbox(t("data_confirm_clear_graph"), key="confirm_clear_graph")
    if confirm_graph:
        if st.button(t("data_btn_clear_graph"), type="primary", key="btn_clear_graph"):
            result = api_call("post", "/api/admin/reset/graph")
            if result and result.get("status") == "success":
                st.success(t("data_cleared_graph"))
                st.rerun()
            else:
                st.error(str(result))

    st.markdown("---")

    # ---- 知识库 ----
    st.markdown(f"### {t('data_section_kb')}")
    kb_stats = api_call("get", "/api/kb/stats")
    if kb_stats:
        c1, c2 = st.columns(2)
        c1.metric(t("data_stat_docs"), kb_stats.get("total_documents", 0))
        c2.metric(t("data_stat_chunks"), kb_stats.get("total_chunks", 0))

    confirm_kb = st.checkbox(t("data_confirm_clear_kb"), key="confirm_clear_kb")
    if confirm_kb:
        if st.button(t("data_btn_clear_kb"), type="primary", key="btn_clear_kb"):
            result = api_call("post", "/api/admin/reset/knowledge-base")
            if result and result.get("status") == "success":
                st.success(t("data_cleared_kb"))
                st.rerun()
            else:
                st.error(str(result))

    st.markdown("---")

    # ---- Agent 记忆 ----
    st.markdown(f"### {t('data_section_memory')}")
    mem_stats = api_call("get", "/api/admin/agent-memory/stats")
    if mem_stats:
        st.metric(t("data_stat_memories"), mem_stats.get("total_memories", 0))

    confirm_mem = st.checkbox(t("data_confirm_clear_memory"), key="confirm_clear_memory")
    if confirm_mem:
        if st.button(t("data_btn_clear_memory"), type="primary", key="btn_clear_memory"):
            result = api_call("post", "/api/admin/reset/agent-memory")
            if result and result.get("status") == "success":
                st.success(t("data_cleared_memory"))
                st.rerun()
            else:
                st.error(str(result))

    st.markdown("---")

    # ---- 样例数据导入 ----
    st.markdown(f"### {t('data_section_sample')}")
    st.info(t("data_sample_desc"))
    if st.button(t("data_btn_import_sample"), key="btn_import_sample"):
        with st.spinner("..."):
            result = api_call("post", "/api/admin/import-sample-data")
        if result and result.get("status") == "success":
            st.success(t("data_imported_sample"))
            st.rerun()
        else:
            st.error(str(result))
