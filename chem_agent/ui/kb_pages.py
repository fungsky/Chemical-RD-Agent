"""知识库管理页面：文档上传、URL 抓取、文档列表、知识检索"""

from typing import Callable

import streamlit as st


def render_knowledge_base_page(
    api_call: Callable,
    t: Callable[[str], str],
    t_fmt: Callable,
):
    """渲染知识库管理页面（2 个 Tab）"""
    st.markdown(
        f'<div class="main-header">{t("kb_title")}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="page-desc">{t("page_desc_knowledge")}</div>', unsafe_allow_html=True)

    # 统计概览
    stats = api_call("get", "/api/kb/stats")
    if stats:
        c1, c2 = st.columns(2)
        with c1:
            st.metric(t("kb_stat_docs"), stats.get("total_documents", 0))
        with c2:
            st.metric(t("kb_stat_chunks"), stats.get("total_chunks", 0))

    tabs = st.tabs([t("kb_tab_manage"), t("kb_tab_search")])

    with tabs[0]:
        _render_doc_management(api_call, t, t_fmt)

    with tabs[1]:
        _render_knowledge_search(api_call, t, t_fmt)


# ============================================================
# 文档管理
# ============================================================

def _render_doc_management(api_call, t, t_fmt):
    st.markdown(f"### {t('kb_upload_title')}")

    # 文件上传
    uploaded = st.file_uploader(
        t("kb_upload_hint"),
        type=["pdf", "docx", "txt", "xlsx"],
        key="kb_file_upload",
    )
    if uploaded is not None:
        if st.button(t("kb_btn_upload"), type="primary", key="btn_kb_upload"):
            with st.spinner(t("kb_uploading")):
                files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type)}
                result = api_call("post", "/api/kb/upload", files=files)
                if result:
                    st.success(t_fmt("kb_upload_ok", uploaded.name, result.get("num_chunks", 0)))
                    st.rerun()

    st.caption(t("kb_excel_support"))

    # URL 抓取
    st.markdown(f"### {t('kb_url_title')}")
    url_input = st.text_input(t("kb_url_hint"), key="kb_url_input", placeholder="https://example.com/article")
    if url_input:
        if st.button(t("kb_btn_fetch"), type="primary", key="btn_kb_fetch"):
            with st.spinner(t("kb_fetching")):
                result = api_call("post", "/api/kb/url", json={"url": url_input})
                if result:
                    st.success(t_fmt("kb_upload_ok", url_input, result.get("num_chunks", 0)))
                    st.rerun()

    # 文档列表
    st.markdown("---")
    st.markdown(f"### {t('kb_doc_list')}")

    docs = api_call("get", "/api/kb/documents")
    if not docs:
        st.info(t("kb_no_docs"))
        return

    for doc in docs:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])
            with col1:
                st.markdown(f"**{doc.get('filename', '-')}**")
            with col2:
                source = doc.get("source_type", "-")
                uploader = doc.get("uploader", "-")
                st.caption(f"{t('kb_col_source')}: {source} | {t('kb_col_uploader')}: {uploader}")
            with col3:
                chunks = doc.get("num_chunks", 0)
                st.caption(f"{t('kb_col_chunks')}: {chunks}")
            with col4:
                doc_id = doc.get("doc_id", "")
                if st.button(t("kb_summary_label"), key=f"sum_doc_{doc_id}"):
                    with st.spinner(t("kb_generating_summary")):
                        summary = api_call("post", f"/api/kb/documents/{doc_id}/summary")
                    if summary:
                        st.session_state[f"doc_summary_{doc_id}"] = summary.get("summary", "")
            with col5:
                doc_id = doc.get("doc_id", "")
                if st.button(t("kb_btn_delete"), key=f"del_doc_{doc_id}"):
                    result = api_call("delete", f"/api/kb/documents/{doc_id}")
                    if result:
                        st.success(t("kb_doc_deleted"))
                        st.rerun()
            # 显示摘要
            doc_id = doc.get("doc_id", "")
            if f"doc_summary_{doc_id}" in st.session_state:
                st.info(st.session_state[f"doc_summary_{doc_id}"])
            st.markdown("---")


# ============================================================
# 知识检索
# ============================================================

def _render_knowledge_search(api_call, t, t_fmt):
    st.markdown(f"### {t('kb_search_title')}")

    query = st.text_input(t("kb_search_hint"), key="kb_search_query", placeholder=t("kb_search_placeholder"))
    col1, col2 = st.columns([3, 1])
    with col2:
        top_k = st.slider(t("kb_search_topk"), min_value=1, max_value=10, value=3, key="kb_topk")

    if query:
        if st.button(t("kb_btn_search"), type="primary", key="btn_kb_search"):
            with st.spinner(t("kb_searching")):
                results = api_call("post", "/api/kb/search", json={"query": query, "top_k": top_k})
                if results:
                    st.session_state["kb_search_results"] = results
                else:
                    st.session_state["kb_search_results"] = []

    # 显示搜索结果
    results = st.session_state.get("kb_search_results")
    if results:
        st.markdown(f"#### {t_fmt('kb_search_found', len(results))}")
        for i, r in enumerate(results, 1):
            score = r.get("similarity_score", 0)
            pct = f"{score * 100:.1f}%"
            filename = r.get("filename", "-")
            with st.expander(f"#{i} - {filename} ({t('kb_col_similarity')}: {pct})", expanded=(i <= 2)):
                st.markdown(r.get("content", ""))
                st.caption(
                    f"{t('kb_col_source')}: {r.get('source_type', '-')} | "
                    f"Chunk: {r.get('chunk_index', '-')}"
                )
    elif results is not None and len(results) == 0:
        st.info(t("kb_no_results"))
