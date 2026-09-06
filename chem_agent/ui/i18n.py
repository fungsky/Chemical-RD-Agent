"""ChemAgent UI 国际化翻译字典"""

TRANSLATIONS = {
    # ============ 通用 ============
    "app_title": {
        "zh": "ChemAgent - 化工研发智能体",
        "en": "ChemAgent - Chemical R&D Agent",
    },
    "app_subtitle": {
        "zh": "化工研发智能体",
        "en": "Chemical R&D Intelligent Agent",
    },
    "language": {
        "zh": "语言 / Language",
        "en": "Language / 语言",
    },
    "nav_title": {
        "zh": "功能导航",
        "en": "Navigation",
    },
    "system_status": {
        "zh": "系统状态",
        "en": "System Status",
    },
    "api_ok": {
        "zh": "API 服务: v{}",
        "en": "API Service: v{}",
    },
    "kg_connected": {
        "zh": "知识图谱: 已连接",
        "en": "Knowledge Graph: Connected",
    },
    "kg_disconnected": {
        "zh": "知识图谱: 未连接",
        "en": "Knowledge Graph: Disconnected",
    },
    "backend_down": {
        "zh": "后端服务未启动",
        "en": "Backend service not running",
    },
    "conn_error": {
        "zh": "无法连接到后端服务，请确认 API 服务已启动 ({})",
        "en": "Cannot connect to backend. Please confirm API is running ({})",
    },
    "api_error": {
        "zh": "API 错误: {}",
        "en": "API Error: {}",
    },
    "request_failed": {
        "zh": "请求失败: {}",
        "en": "Request failed: {}",
    },

    # ============ 导航菜单 ============
    "nav_dashboard": {
        "zh": "📊 总览仪表板",
        "en": "📊 Dashboard",
    },
    "nav_chat": {
        "zh": "💬 智能问答",
        "en": "💬 AI Chat",
    },
    "nav_search": {
        "zh": "🔍 配方检索",
        "en": "🔍 Formula Search",
    },
    "nav_manage": {
        "zh": "📝 配方管理",
        "en": "📝 Formula Management",
    },
    "nav_analysis": {
        "zh": "🔬 配方分析",
        "en": "🔬 Formula Analysis",
    },
    "nav_predict": {
        "zh": "🎯 性能预测",
        "en": "🎯 Performance Prediction",
    },
    "nav_recommend": {
        "zh": "💡 配方推荐",
        "en": "💡 Formula Recommendation",
    },
    "nav_materials": {
        "zh": "🧪 原材料管理",
        "en": "🧪 Material Management",
    },
    "nav_knowledge": {
        "zh": "📚 知识库",
        "en": "📚 Knowledge Base",
    },

    # ============ 仪表板 ============
    "dashboard_title": {
        "zh": "📊 研发数据总览",
        "en": "📊 R&D Data Overview",
    },
    "stat_formulas": {
        "zh": "配方总数",
        "en": "Formulas",
    },
    "stat_materials": {
        "zh": "原材料种类",
        "en": "Materials",
    },
    "stat_categories": {
        "zh": "产品类别",
        "en": "Categories",
    },
    "stat_relations": {
        "zh": "组分关系",
        "en": "Relations",
    },
    "stat_tests": {
        "zh": "性能测试",
        "en": "Perf. Tests",
    },
    "quick_actions": {
        "zh": "快速操作",
        "en": "Quick Actions",
    },
    "qa_chat_desc": {
        "zh": "**智能问答** - 向 AI 提问化工研发问题",
        "en": "**AI Chat** - Ask AI about chemical R&D",
    },
    "qa_search_desc": {
        "zh": "**配方检索** - 多条件检索历史配方",
        "en": "**Formula Search** - Multi-criteria search",
    },
    "qa_predict_desc": {
        "zh": "**性能预测** - 预测新配方性能指标",
        "en": "**Prediction** - Predict formula performance",
    },

    # ============ 智能问答 ============
    "chat_title": {
        "zh": "💬 智能问答助手",
        "en": "💬 AI Chat Assistant",
    },
    "chat_desc": {
        "zh": "向化工研发 AI 助手提问，获取专业的配方开发建议。",
        "en": "Ask our AI assistant for professional formula development advice.",
    },
    "chat_placeholder": {
        "zh": "请输入您的问题，例如：如何提高水性涂料的耐水性？",
        "en": "Enter your question, e.g.: How to improve water resistance of coatings?",
    },
    "chat_thinking": {
        "zh": "AI 思考中...",
        "en": "AI is thinking...",
    },
    "chat_unavailable": {
        "zh": "抱歉，服务暂时不可用。",
        "en": "Sorry, the service is temporarily unavailable.",
    },
    "chat_llm_unavailable": {
        "zh": "无法连接到 AI 服务，请在管理后台检查 LLM 配置。",
        "en": "Cannot connect to AI service. Please check LLM settings in admin panel.",
    },
    "chat_clear": {
        "zh": "清除对话历史",
        "en": "Clear Chat History",
    },

    # ============ 配方检索 ============
    "search_title": {
        "zh": "🔍 配方智能检索",
        "en": "🔍 Intelligent Formula Search",
    },
    "search_keyword": {
        "zh": "关键词搜索",
        "en": "Keyword Search",
    },
    "search_keyword_ph": {
        "zh": "输入配方名称、描述等关键词",
        "en": "Enter formula name, description keywords",
    },
    "search_category": {
        "zh": "产品类别",
        "en": "Product Category",
    },
    "search_all": {
        "zh": "全部",
        "en": "All",
    },
    "search_materials": {
        "zh": "包含原料（逗号分隔）",
        "en": "Contains materials (comma-separated)",
    },
    "search_materials_ph": {
        "zh": "例如: 环氧树脂, 二氧化钛",
        "en": "e.g.: Epoxy Resin, Titanium Dioxide",
    },
    "search_limit": {
        "zh": "结果数量",
        "en": "Result Limit",
    },
    "search_btn": {
        "zh": "搜索配方",
        "en": "Search Formulas",
    },
    "search_searching": {
        "zh": "正在检索...",
        "en": "Searching...",
    },
    "search_found": {
        "zh": "找到 {} 个匹配配方",
        "en": "Found {} matching formulas",
    },
    "search_empty": {
        "zh": "未找到匹配的配方",
        "en": "No matching formulas found",
    },
    "search_unnamed": {
        "zh": "未命名",
        "en": "Unnamed",
    },
    "search_similarity": {
        "zh": "相似度",
        "en": "Similarity",
    },
    "search_code": {
        "zh": "编号",
        "en": "Code",
    },
    "search_cat_label": {
        "zh": "类别",
        "en": "Category",
    },
    "search_description": {
        "zh": "描述",
        "en": "Description",
    },
    "search_match_reason": {
        "zh": "匹配原因",
        "en": "Match Reason",
    },
    "search_components": {
        "zh": "配方组分",
        "en": "Formula Components",
    },
    "search_perf_data": {
        "zh": "性能数据",
        "en": "Performance Data",
    },

    # ============ 表格列名 ============
    "col_material_name": {
        "zh": "原料名称",
        "en": "Material Name",
    },
    "col_function": {
        "zh": "功能分类",
        "en": "Function",
    },
    "col_weight_pct": {
        "zh": "质量百分比 (%)",
        "en": "Weight %",
    },
    "col_test_name": {
        "zh": "测试项目",
        "en": "Test Item",
    },
    "col_value": {
        "zh": "数值",
        "en": "Value",
    },
    "col_unit": {
        "zh": "单位",
        "en": "Unit",
    },
    "col_name": {
        "zh": "名称",
        "en": "Name",
    },
    "col_cas": {
        "zh": "CAS号",
        "en": "CAS No.",
    },
    "col_chemical_name": {
        "zh": "化学名",
        "en": "Chemical Name",
    },
    "col_supplier": {
        "zh": "供应商",
        "en": "Supplier",
    },

    # ============ 配方管理 ============
    "manage_title": {
        "zh": "📝 配方管理",
        "en": "📝 Formula Management",
    },
    "manage_tab_new": {
        "zh": "录入新配方",
        "en": "New Formula",
    },
    "manage_tab_view": {
        "zh": "查看配方",
        "en": "View Formula",
    },
    "manage_basic_info": {
        "zh": "配方基本信息",
        "en": "Basic Information",
    },
    "manage_name": {
        "zh": "配方名称",
        "en": "Formula Name",
    },
    "manage_code": {
        "zh": "配方编号",
        "en": "Formula Code",
    },
    "manage_category": {
        "zh": "产品类别",
        "en": "Product Category",
    },
    "manage_application": {
        "zh": "目标应用场景",
        "en": "Target Application",
    },
    "manage_desc": {
        "zh": "配方描述",
        "en": "Formula Description",
    },
    "manage_components": {
        "zh": "配方组分",
        "en": "Formula Components",
    },
    "manage_components_hint": {
        "zh": "在下方表格中添加、编辑或删除配方组分：",
        "en": "Add, edit or delete formula components in the table below:",
    },
    "manage_performance": {
        "zh": "性能测试数据",
        "en": "Performance Test Data",
    },
    "manage_perf_hint": {
        "zh": "在下方表格中添加性能测试结果：",
        "en": "Add performance test results in the table below:",
    },
    "manage_save": {
        "zh": "保存配方",
        "en": "Save Formula",
    },
    "manage_save_ok": {
        "zh": "保存成功",
        "en": "Saved successfully",
    },
    "manage_view_code": {
        "zh": "输入配方编号查看详情",
        "en": "Enter formula code to view details",
    },
    "manage_view_btn": {
        "zh": "查看",
        "en": "View",
    },
    "manage_add_row": {
        "zh": "点击表格左下角 '+' 添加行",
        "en": "Click '+' at the bottom-left of the table to add rows",
    },
    "manage_total_pct": {
        "zh": "组分合计: {:.1f}%",
        "en": "Total: {:.1f}%",
    },
    "manage_pct_warning": {
        "zh": "组分百分比合计不等于 100%，当前合计: {:.1f}%",
        "en": "Component percentages do not sum to 100%. Current total: {:.1f}%",
    },
    "manage_no_components": {
        "zh": "请至少添加一个配方组分",
        "en": "Please add at least one component",
    },
    "manage_no_name": {
        "zh": "请填写配方名称",
        "en": "Please enter a formula name",
    },

    # ============ 配方分析 ============
    "analysis_title": {
        "zh": "🔬 AI 配方分析",
        "en": "🔬 AI Formula Analysis",
    },
    "analysis_desc": {
        "zh": "输入配方编号，AI 将从多维度分析配方的组成、工艺和性能。",
        "en": "Enter formula code. AI will analyze composition, process and performance.",
    },
    "analysis_code": {
        "zh": "配方编号",
        "en": "Formula Code",
    },
    "analysis_start": {
        "zh": "开始分析",
        "en": "Start Analysis",
    },
    "analysis_fetching": {
        "zh": "正在获取配方数据...",
        "en": "Fetching formula data...",
    },
    "analysis_running": {
        "zh": "AI 正在分析配方...",
        "en": "AI is analyzing the formula...",
    },
    "analysis_formula": {
        "zh": "配方: {}",
        "en": "Formula: {}",
    },
    "analysis_result": {
        "zh": "分析结果",
        "en": "Analysis Result",
    },
    "analysis_failed": {
        "zh": "分析失败",
        "en": "Analysis failed",
    },

    # ============ 性能预测 ============
    "predict_title": {
        "zh": "🎯 配方性能预测",
        "en": "🎯 Formula Performance Prediction",
    },
    "predict_tab_predict": {
        "zh": "性能预测",
        "en": "Predict",
    },
    "predict_tab_train": {
        "zh": "模型训练",
        "en": "Train Model",
    },
    "predict_desc": {
        "zh": "输入配方组分，预测目标性能指标。",
        "en": "Enter formula components to predict target performance indicators.",
    },
    "predict_components_hint": {
        "zh": "在下方表格中输入配方组分：",
        "en": "Enter formula components in the table below:",
    },
    "predict_category": {
        "zh": "产品类别",
        "en": "Product Category",
    },
    "predict_target_props": {
        "zh": "预测性能指标（逗号分隔）",
        "en": "Target properties (comma-separated)",
    },
    "predict_btn": {
        "zh": "开始预测",
        "en": "Start Prediction",
    },
    "predict_running": {
        "zh": "正在预测...",
        "en": "Predicting...",
    },
    "predict_result": {
        "zh": "预测结果",
        "en": "Prediction Results",
    },
    "predict_confidence": {
        "zh": "置信度: {:.2%}",
        "en": "Confidence: {:.2%}",
    },
    "predict_train_desc": {
        "zh": "使用知识图谱中的历史数据训练预测模型。",
        "en": "Train prediction models using historical data from knowledge graph.",
    },
    "predict_train_props": {
        "zh": "训练目标指标（逗号分隔）",
        "en": "Target indicators (comma-separated)",
    },
    "predict_train_btn": {
        "zh": "开始训练",
        "en": "Start Training",
    },
    "predict_training": {
        "zh": "正在训练模型...",
        "en": "Training model...",
    },
    "predict_train_ok": {
        "zh": "模型训练完成",
        "en": "Model training completed",
    },

    # ============ 配方推荐 ============
    "recommend_title": {
        "zh": "💡 AI 配方推荐",
        "en": "💡 AI Formula Recommendation",
    },
    "recommend_requirement": {
        "zh": "需求描述",
        "en": "Requirement Description",
    },
    "recommend_requirement_ph": {
        "zh": "例如：需要一款高硬度、高光泽的汽车面漆配方",
        "en": "e.g.: Need a high-hardness, high-gloss automotive topcoat formula",
    },
    "recommend_category": {
        "zh": "产品类别",
        "en": "Product Category",
    },
    "recommend_target_perf": {
        "zh": "目标性能指标:",
        "en": "Target Performance:",
    },
    "recommend_prop_name": {
        "zh": "指标{}名称",
        "en": "Property {} Name",
    },
    "recommend_prop_value": {
        "zh": "指标{}要求",
        "en": "Property {} Requirement",
    },
    "recommend_btn": {
        "zh": "获取推荐",
        "en": "Get Recommendation",
    },
    "recommend_running": {
        "zh": "AI 正在分析历史案例并生成推荐方案...",
        "en": "AI is analyzing historical cases and generating recommendations...",
    },
    "recommend_result": {
        "zh": "推荐方案",
        "en": "Recommendation",
    },
    "recommend_refs": {
        "zh": "参考历史配方",
        "en": "Reference Formulas",
    },

    # ============ 原材料管理 ============
    "materials_title": {
        "zh": "🧪 原材料管理",
        "en": "🧪 Material Management",
    },
    "materials_tab_search": {
        "zh": "搜索原材料",
        "en": "Search Materials",
    },
    "materials_tab_new": {
        "zh": "录入原材料",
        "en": "New Material",
    },
    "materials_tab_sub": {
        "zh": "替代建议",
        "en": "Substitution Advice",
    },
    "materials_search_label": {
        "zh": "搜索原材料",
        "en": "Search Materials",
    },
    "materials_search_ph": {
        "zh": "输入名称或化学名关键词",
        "en": "Enter name or chemical name keyword",
    },
    "materials_func_filter": {
        "zh": "功能分类",
        "en": "Function Category",
    },
    "materials_search_btn": {
        "zh": "搜索",
        "en": "Search",
    },
    "materials_empty": {
        "zh": "未找到匹配的原材料",
        "en": "No matching materials found",
    },
    "materials_new_title": {
        "zh": "录入新原材料",
        "en": "Add New Material",
    },
    "materials_name": {
        "zh": "原料名称",
        "en": "Material Name",
    },
    "materials_cas": {
        "zh": "CAS 编号",
        "en": "CAS Number",
    },
    "materials_chemical": {
        "zh": "化学名称",
        "en": "Chemical Name",
    },
    "materials_supplier": {
        "zh": "供应商",
        "en": "Supplier",
    },
    "materials_function": {
        "zh": "功能分类",
        "en": "Function Category",
    },
    "materials_save": {
        "zh": "保存原材料",
        "en": "Save Material",
    },
    "materials_sub_title": {
        "zh": "AI 原材料替代建议",
        "en": "AI Material Substitution Advice",
    },
    "materials_sub_name": {
        "zh": "需要替代的原材料",
        "en": "Material to Replace",
    },
    "materials_sub_func": {
        "zh": "原料功能分类",
        "en": "Material Function",
    },
    "materials_sub_usage": {
        "zh": "当前使用情况说明",
        "en": "Current Usage Description",
    },
    "materials_sub_btn": {
        "zh": "获取替代建议",
        "en": "Get Substitution Advice",
    },
    "materials_sub_running": {
        "zh": "AI 正在分析替代方案...",
        "en": "AI is analyzing substitution options...",
    },
    "materials_sub_result": {
        "zh": "替代建议",
        "en": "Substitution Advice",
    },
    "materials_sub_stats": {
        "zh": "当前使用统计",
        "en": "Current Usage Statistics",
    },

    # ============ 产品类别 (value -> display) ============
    "cat_coating": {"zh": "涂料", "en": "Coating"},
    "cat_adhesive": {"zh": "胶粘剂", "en": "Adhesive"},
    "cat_sealant": {"zh": "密封剂", "en": "Sealant"},
    "cat_resin": {"zh": "树脂", "en": "Resin"},
    "cat_surfactant": {"zh": "表面活性剂", "en": "Surfactant"},
    "cat_catalyst": {"zh": "催化剂", "en": "Catalyst"},
    "cat_additive": {"zh": "助剂", "en": "Additive"},
    "cat_plastic": {"zh": "塑料", "en": "Plastic"},
    "cat_rubber": {"zh": "橡胶", "en": "Rubber"},
    "cat_ink": {"zh": "油墨", "en": "Ink"},
    "cat_other": {"zh": "其他", "en": "Other"},

    # ============ 功能分类 ============
    "func_base_resin": {"zh": "基础树脂", "en": "Base Resin"},
    "func_solvent": {"zh": "溶剂", "en": "Solvent"},
    "func_filler": {"zh": "填料", "en": "Filler"},
    "func_pigment": {"zh": "颜料", "en": "Pigment"},
    "func_curing_agent": {"zh": "固化剂", "en": "Curing Agent"},
    "func_catalyst": {"zh": "催化剂", "en": "Catalyst"},
    "func_dispersant": {"zh": "分散剂", "en": "Dispersant"},
    "func_leveling": {"zh": "流平剂", "en": "Leveling Agent"},
    "func_defoamer": {"zh": "消泡剂", "en": "Defoamer"},
    "func_thickener": {"zh": "增稠剂", "en": "Thickener"},
    "func_plasticizer": {"zh": "增塑剂", "en": "Plasticizer"},
    "func_antioxidant": {"zh": "抗氧化剂", "en": "Antioxidant"},
    "func_uv_stabilizer": {"zh": "紫外稳定剂", "en": "UV Stabilizer"},
    "func_flame_retardant": {"zh": "阻燃剂", "en": "Flame Retardant"},
    "func_coupling_agent": {"zh": "偶联剂", "en": "Coupling Agent"},
    "func_wetting_agent": {"zh": "润湿剂", "en": "Wetting Agent"},
    "func_other": {"zh": "其他", "en": "Other"},

    # ============ 登录 / 认证 ============
    "login_title": {"zh": "用户登录", "en": "User Login"},
    "login_username": {"zh": "用户名", "en": "Username"},
    "login_password": {"zh": "密码", "en": "Password"},
    "login_btn": {"zh": "登录", "en": "Login"},
    "login_failed": {"zh": "登录失败：用户名或密码错误", "en": "Login failed: invalid username or password"},
    "login_error": {"zh": "登录异常: {}", "en": "Login error: {}"},
    "login_welcome": {"zh": "欢迎回来, {}", "en": "Welcome back, {}"},
    "logout_btn": {"zh": "退出登录", "en": "Logout"},
    "current_user": {"zh": "当前用户", "en": "Current User"},
    "role_label": {"zh": "角色", "en": "Roles"},
    "change_password": {"zh": "修改密码", "en": "Change Password"},
    "new_password": {"zh": "新密码", "en": "New Password"},
    "confirm_password": {"zh": "确认密码", "en": "Confirm Password"},
    "password_mismatch": {"zh": "两次输入的密码不一致", "en": "Passwords do not match"},
    "password_changed": {"zh": "密码修改成功", "en": "Password changed successfully"},
    "session_expired": {"zh": "会话已过期，请重新登录", "en": "Session expired, please login again"},

    # ============ 后台管理导航 ============
    "nav_admin": {"zh": "⚙️ 后台管理", "en": "⚙️ Admin Panel"},
    "admin_title": {"zh": "⚙️ 后台管理", "en": "⚙️ Administration"},
    "admin_tab_users": {"zh": "用户管理", "en": "User Management"},
    "admin_tab_roles": {"zh": "角色管理", "en": "Role Management"},
    "admin_tab_categories": {"zh": "分类管理", "en": "Category Management"},
    "admin_tab_config": {"zh": "系统配置", "en": "System Config"},
    "admin_tab_audit": {"zh": "审计日志", "en": "Audit Logs"},
    "admin_tab_data": {"zh": "数据管理", "en": "Data Management"},
    # ---------- 数据管理 ----------
    "data_mgmt_warning": {
        "zh": "⚠️ 以下为危险操作，清空后数据无法恢复，请谨慎！",
        "en": "⚠️ Danger zone: data cannot be recovered after clearing!",
    },
    "data_section_graph": {"zh": "知识图谱 (Neo4j)", "en": "Knowledge Graph (Neo4j)"},
    "data_section_kb": {"zh": "知识库文档 (ChromaDB)", "en": "Knowledge Base (ChromaDB)"},
    "data_section_memory": {"zh": "Agent 经验记忆", "en": "Agent Experience Memory"},
    "data_section_sample": {"zh": "样例数据导入", "en": "Sample Data Import"},
    "data_confirm_clear_graph": {
        "zh": "我确认要清空所有知识图谱数据",
        "en": "I confirm to clear all graph data",
    },
    "data_confirm_clear_kb": {
        "zh": "我确认要清空所有知识库文档",
        "en": "I confirm to clear all KB documents",
    },
    "data_confirm_clear_memory": {
        "zh": "我确认要清空所有 Agent 记忆",
        "en": "I confirm to clear all agent memories",
    },
    "data_btn_clear_graph": {"zh": "清空知识图谱", "en": "Clear Knowledge Graph"},
    "data_btn_clear_kb": {"zh": "清空知识库", "en": "Clear Knowledge Base"},
    "data_btn_clear_memory": {"zh": "清空 Agent 记忆", "en": "Clear Agent Memory"},
    "data_btn_import_sample": {"zh": "导入样例数据", "en": "Import Sample Data"},
    "data_cleared_graph": {"zh": "知识图谱已清空", "en": "Knowledge graph cleared"},
    "data_cleared_kb": {"zh": "知识库已清空", "en": "Knowledge base cleared"},
    "data_cleared_memory": {"zh": "Agent 记忆已清空", "en": "Agent memory cleared"},
    "data_imported_sample": {"zh": "样例数据已导入", "en": "Sample data imported"},
    "data_sample_desc": {
        "zh": "导入 20 种原材料和 5 个示例配方到知识图谱",
        "en": "Import 20 materials and 5 sample formulas into the knowledge graph",
    },
    "data_stat_formulas": {"zh": "配方", "en": "Formulas"},
    "data_stat_materials": {"zh": "原材料", "en": "Materials"},
    "data_stat_tests": {"zh": "性能测试", "en": "Tests"},
    "data_stat_docs": {"zh": "文档", "en": "Documents"},
    "data_stat_chunks": {"zh": "片段", "en": "Chunks"},
    "data_stat_memories": {"zh": "记忆条数", "en": "Memories"},
    "admin_no_permission": {"zh": "您没有管理权限", "en": "You do not have admin permission"},

    # ============ LLM / Embedder 配置 ============

    # --- 管理后台菜单分组 ---
    "admin_menu_ai_providers": {"zh": "AI 提供商", "en": "AI Providers"},
    "admin_menu_llm": {"zh": "大语言模型", "en": "LLM"},
    "admin_menu_embedder": {"zh": "嵌入模型", "en": "Embedder"},
    "admin_menu_users_perms": {"zh": "用户与权限", "en": "Users & Permissions"},
    "admin_menu_system": {"zh": "系统", "en": "System"},

    # --- LLM 设置页 ---
    "llm_settings_title": {"zh": "大语言模型 (LLM)", "en": "Large Language Model (LLM)"},
    "llm_settings_desc": {
        "zh": "选择你的 LLM 提供商并配置连接参数。所有对话和智能体功能将使用此模型。",
        "en": "Choose your LLM provider and configure connection. All chat and agent features will use this model.",
    },
    "llm_select_provider": {"zh": "选择提供商", "en": "Select Provider"},
    "llm_provider": {"zh": "提供商", "en": "Provider"},
    "llm_base_url": {"zh": "Base URL", "en": "Base URL"},
    "llm_model_name": {"zh": "模型名称", "en": "Model Name"},
    "llm_api_key": {"zh": "API Key", "en": "API Key"},
    "llm_api_key_optional": {"zh": "API Key (可选)", "en": "API Key (Optional)"},
    "llm_azure_deployment": {"zh": "Deployment Name", "en": "Deployment Name"},
    "llm_azure_api_version": {"zh": "API Version", "en": "API Version"},
    "llm_test_btn": {"zh": "测试连接", "en": "Test Connection"},
    "llm_testing": {"zh": "正在测试连接...", "en": "Testing connection..."},
    "llm_test_success": {"zh": "连接成功！延迟: {}ms", "en": "Connected! Latency: {}ms"},
    "llm_test_failed": {"zh": "连接失败: {}", "en": "Connection failed: {}"},
    "llm_save_btn": {"zh": "保存 LLM 配置", "en": "Save LLM Config"},
    "llm_config_saved": {"zh": "LLM 配置已保存并生效", "en": "LLM config saved and applied"},
    "llm_config_save_failed": {"zh": "保存失败: {}", "en": "Save failed: {}"},
    "llm_not_configured": {
        "zh": "LLM 尚未配置。请选择一个提供商并填写配置。",
        "en": "LLM is not configured. Please select a provider and fill in the settings.",
    },

    # --- Embedder 设置页 ---
    "emb_settings_title": {"zh": "嵌入模型 (Embedder)", "en": "Embedding Model (Embedder)"},
    "emb_settings_desc": {
        "zh": "嵌入模型用于将文本转换为向量，支持知识库检索和语义搜索功能。",
        "en": "The embedding model converts text to vectors for knowledge base retrieval and semantic search.",
    },
    "emb_save_btn": {"zh": "保存 Embedding 配置", "en": "Save Embedding Config"},
    "emb_config_saved": {"zh": "Embedding 配置已保存并生效", "en": "Embedding config saved and applied"},
    "emb_model_required": {"zh": "请输入 Embedding 模型名称", "en": "Please enter the embedding model name"},

    # --- 搜索 / 状态 ---
    "search_providers": {"zh": "搜索提供商...", "en": "Search providers..."},
    "no_providers_found": {"zh": "未找到匹配的提供商", "en": "No matching providers"},
    "status_configured": {"zh": "已配置", "en": "Configured"},
    "status_not_configured": {"zh": "未配置", "en": "Not configured"},

    # --- Token / Temperature / 高级设置 ---
    "llm_max_tokens": {"zh": "Token 上下文窗口", "en": "Token Context Window"},
    "llm_max_tokens_help": {
        "zh": "模型单次请求可处理的最大 Token 数量。不同模型支持不同上限。",
        "en": "Maximum number of tokens the model can process per request. Different models support different limits.",
    },
    "llm_temperature": {"zh": "温度 (Temperature)", "en": "Temperature"},
    "llm_temperature_help": {
        "zh": "控制生成文本的随机性。值越低越确定，值越高越有创意。推荐 0.3-0.7。",
        "en": "Controls randomness of generated text. Lower = more deterministic, higher = more creative. Recommended: 0.3-0.7.",
    },
    "llm_advanced_settings": {"zh": "显示高级设置", "en": "Show Advanced Settings"},
    "llm_azure_endpoint": {"zh": "Azure Endpoint", "en": "Azure Endpoint"},
    "emb_same_as_llm_hint": {
        "zh": "复用 LLM 提供商的连接配置，仅需指定 Embedding 模型名称",
        "en": "Reuses LLM provider connection settings, only specify the embedding model name",
    },

    # --- 向量数据库 ---
    "admin_menu_vectordb": {"zh": "向量数据库", "en": "Vector Database"},
    "vectordb_settings_title": {"zh": "向量数据库", "en": "Vector Database"},
    "vectordb_settings_desc": {
        "zh": "向量数据库用于存储文档嵌入向量，支持知识库的语义检索功能。",
        "en": "The vector database stores document embedding vectors for semantic search in the knowledge base.",
    },
    "vectordb_chroma_desc": {
        "zh": "轻量级嵌入式向量数据库，开箱即用，适合中小规模部署",
        "en": "Lightweight embedded vector database, works out of the box for small-to-medium deployments",
    },
    "vectordb_stat_collections": {"zh": "集合数", "en": "Collections"},
    "vectordb_config_title": {"zh": "当前配置", "en": "Current Configuration"},
    "vectordb_config_hint": {
        "zh": "以下配置通过环境变量或 .env 文件设置，在此仅作展示。",
        "en": "These settings are configured via environment variables or .env file, shown here for reference.",
    },
    "vectordb_persist_dir": {"zh": "持久化目录", "en": "Persist Directory"},
    "vectordb_embedding_dim": {"zh": "嵌入维度", "en": "Embedding Dimension"},
    "vectordb_similarity_topk": {"zh": "检索 Top-K", "en": "Similarity Top-K"},
    "vectordb_chunk_size": {"zh": "文本分块大小", "en": "Chunk Size"},

    # --- Provider 名称与描述 (12 个) ---
    "provider_ollama": {"zh": "Ollama (本地)", "en": "Ollama (Local)"},
    "provider_ollama_desc": {
        "zh": "本地部署的开源模型运行环境，无需 API 密钥",
        "en": "Run open-source models locally, no API key needed",
    },
    "provider_lm_studio": {"zh": "LM Studio", "en": "LM Studio"},
    "provider_lm_studio_desc": {
        "zh": "图形化本地模型管理工具，OpenAI 兼容 API",
        "en": "GUI for local models with OpenAI-compatible API",
    },
    "provider_openai": {"zh": "OpenAI", "en": "OpenAI"},
    "provider_openai_desc": {
        "zh": "GPT-4o / GPT-4 / GPT-3.5 系列官方 API",
        "en": "Official GPT-4o / GPT-4 / GPT-3.5 API",
    },
    "provider_azure_openai": {"zh": "Azure OpenAI", "en": "Azure OpenAI"},
    "provider_azure_openai_desc": {
        "zh": "微软 Azure 托管的 OpenAI 企业版服务",
        "en": "Enterprise OpenAI service hosted on Microsoft Azure",
    },
    "provider_deepseek": {"zh": "DeepSeek", "en": "DeepSeek"},
    "provider_deepseek_desc": {
        "zh": "深度求索，高性能推理模型",
        "en": "High-performance reasoning model by DeepSeek",
    },
    "provider_zhipu": {"zh": "智谱AI (GLM)", "en": "Zhipu AI (GLM)"},
    "provider_zhipu_desc": {
        "zh": "智谱 ChatGLM 系列大模型",
        "en": "Zhipu ChatGLM series large language models",
    },
    "provider_qwen": {"zh": "通义千问", "en": "Qwen (Tongyi)"},
    "provider_qwen_desc": {
        "zh": "阿里云通义千问系列模型",
        "en": "Alibaba Cloud Qwen series models",
    },
    "provider_moonshot": {"zh": "月之暗面 (Kimi)", "en": "Moonshot (Kimi)"},
    "provider_moonshot_desc": {
        "zh": "Kimi 长文本理解大模型",
        "en": "Kimi long-context language model",
    },
    "provider_yi": {"zh": "零一万物 (Yi)", "en": "Yi (01.AI)"},
    "provider_yi_desc": {
        "zh": "零一万物 Yi 系列大模型",
        "en": "Yi series models by 01.AI",
    },
    "provider_gemini": {"zh": "Google Gemini", "en": "Google Gemini"},
    "provider_gemini_desc": {
        "zh": "Google Gemini 系列多模态模型",
        "en": "Google Gemini multimodal models",
    },
    "provider_anthropic": {"zh": "Anthropic Claude", "en": "Anthropic Claude"},
    "provider_anthropic_desc": {
        "zh": "Claude 系列对话模型",
        "en": "Claude series conversational models",
    },
    "provider_custom_openai": {"zh": "自定义 (OpenAI 兼容)", "en": "Custom (OpenAI-compatible)"},
    "provider_custom_openai_desc": {
        "zh": "任何兼容 OpenAI API 格式的服务",
        "en": "Any service compatible with OpenAI API format",
    },
    "provider_same_as_llm": {"zh": "同 LLM 提供商", "en": "Same as LLM Provider"},
    "provider_same_as_llm_desc": {
        "zh": "复用 LLM 的连接配置，仅需指定 Embedding 模型名",
        "en": "Reuse LLM connection settings, only specify embedding model name",
    },

    # ============ 用户管理 ============
    "user_list_title": {"zh": "用户列表", "en": "User List"},
    "user_create_title": {"zh": "创建用户", "en": "Create User"},
    "user_col_id": {"zh": "ID", "en": "ID"},
    "user_col_username": {"zh": "用户名", "en": "Username"},
    "user_col_fullname": {"zh": "姓名", "en": "Full Name"},
    "user_col_email": {"zh": "邮箱", "en": "Email"},
    "user_col_roles": {"zh": "角色", "en": "Roles"},
    "user_col_active": {"zh": "状态", "en": "Status"},
    "user_col_last_login": {"zh": "最后登录", "en": "Last Login"},
    "user_col_actions": {"zh": "操作", "en": "Actions"},
    "user_active": {"zh": "启用", "en": "Active"},
    "user_inactive": {"zh": "禁用", "en": "Disabled"},
    "user_btn_create": {"zh": "创建用户", "en": "Create User"},
    "user_btn_edit": {"zh": "编辑", "en": "Edit"},
    "user_btn_delete": {"zh": "删除", "en": "Delete"},
    "user_btn_reset_pwd": {"zh": "重置密码", "en": "Reset Password"},
    "user_btn_toggle": {"zh": "启用/禁用", "en": "Enable/Disable"},
    "user_created": {"zh": "用户 {} 创建成功", "en": "User {} created successfully"},
    "user_updated": {"zh": "用户信息已更新", "en": "User updated"},
    "user_deleted": {"zh": "用户已删除", "en": "User deleted"},
    "user_pwd_reset": {"zh": "密码已重置", "en": "Password reset"},
    "user_confirm_delete": {"zh": "确认删除用户 {} ？", "en": "Confirm delete user {}?"},
    "user_assign_roles": {"zh": "分配角色", "en": "Assign Roles"},

    # ============ 角色管理 ============
    "role_list_title": {"zh": "角色列表", "en": "Role List"},
    "role_create_title": {"zh": "创建角色", "en": "Create Role"},
    "role_col_name": {"zh": "角色名", "en": "Role Name"},
    "role_col_display": {"zh": "显示名称", "en": "Display Name"},
    "role_col_desc": {"zh": "描述", "en": "Description"},
    "role_col_system": {"zh": "系统角色", "en": "System Role"},
    "role_col_users": {"zh": "用户数", "en": "User Count"},
    "role_col_perms": {"zh": "权限数", "en": "Permissions"},
    "role_btn_create": {"zh": "创建角色", "en": "Create Role"},
    "role_btn_edit_perms": {"zh": "编辑权限", "en": "Edit Permissions"},
    "role_created": {"zh": "角色 {} 创建成功", "en": "Role {} created successfully"},
    "role_deleted": {"zh": "角色已删除", "en": "Role deleted"},
    "role_perms_updated": {"zh": "权限已更新", "en": "Permissions updated"},
    "role_system_hint": {"zh": "系统角色不可删除", "en": "System roles cannot be deleted"},
    "role_name_field": {"zh": "角色标识 (英文)", "en": "Role Key (English)"},
    "role_display_field": {"zh": "显示名称", "en": "Display Name"},
    "role_desc_field": {"zh": "描述", "en": "Description"},
    "perm_select_title": {"zh": "选择权限", "en": "Select Permissions"},

    # ============ 分类管理 ============
    "cat_mgmt_title": {"zh": "分类管理", "en": "Category Management"},
    "cat_tab_product": {"zh": "产品类别", "en": "Product Categories"},
    "cat_tab_function": {"zh": "功能分类", "en": "Function Categories"},
    "cat_col_code": {"zh": "编码", "en": "Code"},
    "cat_col_zh": {"zh": "中文名", "en": "Chinese Name"},
    "cat_col_en": {"zh": "英文名", "en": "English Name"},
    "cat_col_order": {"zh": "排序", "en": "Sort Order"},
    "cat_col_enabled": {"zh": "启用", "en": "Enabled"},
    "cat_btn_add": {"zh": "添加分类", "en": "Add Category"},
    "cat_created": {"zh": "分类已创建", "en": "Category created"},
    "cat_updated": {"zh": "分类已更新", "en": "Category updated"},
    "cat_deleted": {"zh": "分类已删除", "en": "Category deleted"},

    # ============ 系统配置 ============
    "config_title": {"zh": "系统配置", "en": "System Configuration"},
    "config_key": {"zh": "配置键", "en": "Config Key"},
    "config_value": {"zh": "配置值", "en": "Config Value"},
    "config_desc": {"zh": "说明", "en": "Description"},
    "config_save": {"zh": "保存配置", "en": "Save Config"},
    "config_saved": {"zh": "配置已保存", "en": "Configuration saved"},
    "config_add": {"zh": "添加配置项", "en": "Add Config Item"},

    # ============ 审计日志 ============
    "audit_title": {"zh": "审计日志", "en": "Audit Logs"},
    "audit_col_time": {"zh": "时间", "en": "Time"},
    "audit_col_user": {"zh": "用户", "en": "User"},
    "audit_col_action": {"zh": "操作", "en": "Action"},
    "audit_col_resource": {"zh": "资源类型", "en": "Resource"},
    "audit_col_detail": {"zh": "详情", "en": "Details"},
    "audit_col_status": {"zh": "状态", "en": "Status"},
    "audit_filter_user": {"zh": "按用户筛选", "en": "Filter by User"},
    "audit_filter_action": {"zh": "按操作筛选", "en": "Filter by Action"},
    "audit_filter_resource": {"zh": "按资源筛选", "en": "Filter by Resource"},
    "audit_total": {"zh": "共 {} 条记录", "en": "{} records total"},
    "audit_page": {"zh": "第 {} 页", "en": "Page {}"},

    # ============ 配方导入导出 ============
    "manage_tab_import": {"zh": "批量导入", "en": "Batch Import"},
    "manage_tab_export": {"zh": "批量导出", "en": "Batch Export"},
    "import_title": {"zh": "批量导入配方", "en": "Batch Import Formulas"},
    "import_upload": {"zh": "上传文件", "en": "Upload File"},
    "import_upload_hint": {"zh": "支持 Excel (.xlsx) 和 JSON (.json) 格式", "en": "Supports Excel (.xlsx) and JSON (.json) formats"},
    "import_download_template": {"zh": "下载 Excel 模板", "en": "Download Excel Template"},
    "import_btn": {"zh": "开始导入", "en": "Start Import"},
    "import_running": {"zh": "正在导入配方数据...", "en": "Importing formula data..."},
    "import_result": {"zh": "导入结果", "en": "Import Result"},
    "import_summary": {"zh": "共 {} 条：成功 {} / 跳过 {} / 失败 {}", "en": "Total {}: Success {} / Skipped {} / Failed {}"},
    "import_col_code": {"zh": "配方编号", "en": "Formula Code"},
    "import_col_status": {"zh": "状态", "en": "Status"},
    "import_col_message": {"zh": "说明", "en": "Message"},
    "import_no_file": {"zh": "请先上传文件", "en": "Please upload a file first"},
    "export_title": {"zh": "批量导出配方", "en": "Batch Export Formulas"},
    "export_scope": {"zh": "导出范围", "en": "Export Scope"},
    "export_all": {"zh": "导出全部配方", "en": "Export All Formulas"},
    "export_filtered": {"zh": "按条件筛选", "en": "Filter by Conditions"},
    "export_single": {"zh": "指定配方编号", "en": "By Formula Code"},
    "export_format": {"zh": "导出格式", "en": "Export Format"},
    "export_filter_category": {"zh": "产品类别", "en": "Product Category"},
    "export_filter_keyword": {"zh": "关键词", "en": "Keyword"},
    "export_code_input": {"zh": "输入配方编号", "en": "Enter Formula Code"},
    "export_btn": {"zh": "生成导出文件", "en": "Generate Export File"},
    "export_running": {"zh": "正在导出...", "en": "Exporting..."},
    "export_download": {"zh": "下载文件", "en": "Download File"},
    "export_no_data": {"zh": "没有找到配方数据", "en": "No formula data found"},
    "export_error": {"zh": "导出失败: {}", "en": "Export failed: {}"},
    "export_single_btn": {"zh": "导出此配方", "en": "Export This Formula"},

    # ============ 知识库 ============
    "kb_title": {"zh": "📚 知识库管理", "en": "📚 Knowledge Base"},
    "kb_tab_manage": {"zh": "文档管理", "en": "Document Management"},
    "kb_tab_search": {"zh": "知识检索", "en": "Knowledge Search"},
    "kb_stat_docs": {"zh": "文档总数", "en": "Documents"},
    "kb_stat_chunks": {"zh": "文本块数", "en": "Chunks"},
    "kb_upload_title": {"zh": "上传文档", "en": "Upload Document"},
    "kb_upload_hint": {"zh": "支持 PDF、Word (.docx)、TXT 文件", "en": "Supports PDF, Word (.docx), TXT files"},
    "kb_btn_upload": {"zh": "上传并解析", "en": "Upload & Parse"},
    "kb_uploading": {"zh": "正在上传并解析文档...", "en": "Uploading and parsing document..."},
    "kb_upload_ok": {"zh": "文档 '{}' 已成功入库，生成 {} 个文本块", "en": "Document '{}' imported, {} chunks created"},
    "kb_url_title": {"zh": "网页抓取", "en": "Web Scraping"},
    "kb_url_hint": {"zh": "输入网页 URL", "en": "Enter web page URL"},
    "kb_btn_fetch": {"zh": "抓取并入库", "en": "Fetch & Import"},
    "kb_fetching": {"zh": "正在抓取网页内容...", "en": "Fetching web content..."},
    "kb_doc_list": {"zh": "文档列表", "en": "Document List"},
    "kb_no_docs": {"zh": "知识库为空，请先上传文档", "en": "Knowledge base is empty, please upload documents first"},
    "kb_col_source": {"zh": "来源", "en": "Source"},
    "kb_col_uploader": {"zh": "上传者", "en": "Uploader"},
    "kb_col_chunks": {"zh": "文本块", "en": "Chunks"},
    "kb_col_similarity": {"zh": "相似度", "en": "Similarity"},
    "kb_btn_delete": {"zh": "删除", "en": "Delete"},
    "kb_doc_deleted": {"zh": "文档已删除", "en": "Document deleted"},
    "kb_search_title": {"zh": "语义检索", "en": "Semantic Search"},
    "kb_search_hint": {"zh": "输入检索内容", "en": "Enter search query"},
    "kb_search_placeholder": {"zh": "例如：环氧树脂固化条件", "en": "e.g. epoxy resin curing conditions"},
    "kb_search_topk": {"zh": "返回条数", "en": "Top K results"},
    "kb_btn_search": {"zh": "检索", "en": "Search"},
    "kb_searching": {"zh": "正在检索...", "en": "Searching..."},
    "kb_search_found": {"zh": "找到 {} 条相关结果", "en": "Found {} relevant results"},
    "kb_no_results": {"zh": "未找到相关内容", "en": "No relevant content found"},

    # ============ Agent 智能体 ============
    "agent_mode_label": {"zh": "智能体模式", "en": "Agent Mode"},
    "agent_reasoning": {"zh": "智能体推理中...", "en": "Agent reasoning..."},
    "agent_thought": {"zh": "思考", "en": "Thinking"},
    "agent_tool": {"zh": "调用工具", "en": "Using tool"},
    "agent_params": {"zh": "查看参数", "en": "View parameters"},
    "agent_observation": {"zh": "执行结果", "en": "Result"},
    "agent_done": {"zh": "推理完成", "en": "Reasoning complete"},
    "agent_error": {"zh": "推理失败", "en": "Reasoning failed"},
    "agent_max_iter": {"zh": "已达最大推理步数", "en": "Max iterations reached"},
    "agent_no_permission": {"zh": "权限不足", "en": "Permission denied"},
    "agent_reflection": {"zh": "反思", "en": "Reflection"},
    "agent_planning": {"zh": "任务规划", "en": "Task Planning"},
    "agent_step_number": {"zh": "步骤 {}", "en": "Step {}"},
    "agent_answer": {"zh": "答案", "en": "Answer"},
    "agent_unknown": {"zh": "未知步骤", "en": "Unknown Step"},

    # ============ 功能介绍与使用说明 ============
    "nav_guide": {"zh": "📖 功能介绍", "en": "📖 User Guide"},
    "guide_title": {"zh": "📖 功能介绍与使用说明", "en": "📖 Feature Guide & Instructions"},
    "guide_overview_title": {"zh": "系统简介", "en": "System Overview"},
    "guide_overview_body": {
        "zh": (
            "**ChemAgent** 是一款面向化工研发人员的 AI 智能体系统，"
            "整合知识图谱、大语言模型、机器学习和向量检索技术，"
            "覆盖配方开发全流程——从检索、分析、预测到推荐。"
        ),
        "en": (
            "**ChemAgent** is an AI agent system for chemical R&D engineers, "
            "integrating knowledge graphs, LLMs, machine learning, and vector search "
            "to cover the full formula development workflow — from search, analysis, prediction to recommendation."
        ),
    },
    "guide_features_title": {"zh": "功能模块", "en": "Feature Modules"},
    "guide_feat_dashboard": {
        "zh": "<strong>📊 总览仪表板</strong> — 展示知识图谱统计数据：配方总数、原材料种类、产品类别、组分关系和性能测试数量。一目了然掌握数据库全貌。",
        "en": "<strong>📊 Dashboard</strong> — Displays knowledge graph statistics: total formulas, material types, product categories, relations, and performance tests. Get a full picture at a glance.",
    },
    "guide_feat_chat": {
        "zh": (
            "<strong>💬 智能问答</strong> — 支持两种对话模式：<br>"
            "- 普通模式：基于知识库文档的 RAG 检索增强问答，自动引用来源<br>"
            "- 智能体模式：ReAct 推理循环，自动调用工具搜索数据、分析配方，推理过程完整可见。"
            "支持任务规划（复杂问题自动拆解）、经验记忆（跨会话学习）和反思自纠错"
        ),
        "en": (
            "<strong>💬 AI Chat</strong> — Two modes available:<br>"
            "- Normal mode: RAG-enhanced Q&A with knowledge base documents, auto-cites sources<br>"
            "- Agent mode: ReAct reasoning loop that automatically invokes tools to search data and analyze formulas. "
            "Supports task planning, experience memory, and self-reflection"
        ),
    },
    "guide_feat_search": {
        "zh": "<strong>🔍 配方检索</strong> — 按关键词、产品类别、原料名称多维度检索历史配方，支持相似配方查找（基于共同原料 Jaccard 相似度）。",
        "en": "<strong>🔍 Formula Search</strong> — Multi-dimensional search by keyword, category, and material name. Supports similar formula discovery via Jaccard similarity.",
    },
    "guide_feat_manage": {
        "zh": "<strong>📝 配方管理</strong> — 在线创建/编辑配方（组分、工艺条件、性能指标）。支持 Excel (4-Sheet) / JSON 批量导入导出，可下载空白模板。",
        "en": "<strong>📝 Formula Management</strong> — Create/edit formulas online (components, process, performance). Supports Excel (4-Sheet) / JSON batch import/export with downloadable templates.",
    },
    "guide_feat_analysis": {
        "zh": "<strong>🔬 配方分析</strong> — 输入配方编号，AI 从组成合理性、组分功能、工艺适配、性能达标、优化方向五个维度进行深度分析。",
        "en": "<strong>🔬 Formula Analysis</strong> — Enter a formula code, and AI performs deep analysis on composition, component functions, process compatibility, performance, and optimization suggestions.",
    },
    "guide_feat_predict": {
        "zh": "<strong>🎯 性能预测</strong> — 基于机器学习（GradientBoosting）预测配方性能指标（如硬度、光泽度）。支持在线训练模型，预测结果附带置信度。",
        "en": "<strong>🎯 Performance Prediction</strong> — ML-based (GradientBoosting) prediction of formula properties (hardness, gloss, etc.). Supports online model training with confidence scores.",
    },
    "guide_feat_recommend": {
        "zh": "<strong>💡 配方推荐</strong> — 描述需求和目标性能，系统搜索历史案例并由 AI 生成推荐配方方案、关键组分选择理由及风险提示。",
        "en": "<strong>💡 Formula Recommendation</strong> — Describe requirements and target performance; the system searches historical cases and generates AI-powered recommendations with rationale.",
    },
    "guide_feat_materials": {
        "zh": "<strong>🧪 原材料管理</strong> — 原材料增删改查、使用统计（在哪些配方中使用、平均用量），AI 替代建议（推荐替代材料 + 性能影响 + 成本分析）。",
        "en": "<strong>🧪 Material Management</strong> — Material CRUD, usage statistics (which formulas, average dosage), and AI substitution suggestions with performance impact and cost analysis.",
    },
    "guide_feat_knowledge": {
        "zh": "<strong>📚 知识库</strong> — 上传 PDF / Word / TXT 文档或抓取网页内容，自动分块向量化存储。为智能问答和 Agent 工具提供语义检索能力。",
        "en": "<strong>📚 Knowledge Base</strong> — Upload PDF / Word / TXT documents or crawl web pages. Auto-chunked and vectorized for semantic retrieval by AI Chat and Agent tools.",
    },
    "guide_feat_admin": {
        "zh": "<strong>⚙️ 后台管理</strong> — 用户管理、角色权限（RBAC）、产品类别管理、系统配置、操作审计日志。仅管理员可见。",
        "en": "<strong>⚙️ Admin Panel</strong> — User management, role-based access control (RBAC), category management, system config, and audit logs. Admin-only.",
    },
    "guide_quickstart_title": {"zh": "快速上手", "en": "Quick Start"},
    "guide_quickstart_body": {
        "zh": (
            "1. **上传数据** — 在「配方管理」页面导入 Excel/JSON 配方数据，或手动创建配方\n"
            "2. **上传文档** — 在「知识库」页面上传技术文档（PDF/Word/TXT），为 AI 提供参考资料\n"
            "3. **训练模型** — 在「性能预测」页面的「模型训练」标签页，输入目标指标后点击训练\n"
            "4. **开始使用** — 在「智能问答」页面提问，开启智能体模式可获得更强大的多步推理能力\n"
            "5. **探索功能** — 尝试配方检索、AI 分析、性能预测、配方推荐等各项功能"
        ),
        "en": (
            "1. **Import data** — Go to Formula Management to import Excel/JSON data or create formulas manually\n"
            "2. **Upload docs** — Go to Knowledge Base to upload technical documents (PDF/Word/TXT) as AI reference\n"
            "3. **Train model** — Go to Performance Prediction > Model Training tab, enter target properties and train\n"
            "4. **Start using** — Go to AI Chat and ask questions; enable Agent mode for powerful multi-step reasoning\n"
            "5. **Explore** — Try Formula Search, AI Analysis, Performance Prediction, and Recommendation features"
        ),
    },
    "guide_tips_title": {"zh": "使用技巧", "en": "Tips"},
    "guide_tips_body": {
        "zh": (
            "- 智能体模式下，AI 可自动调用 10 个工具完成复杂任务（如「帮我找一个涂料配方并分析优缺点」）\n"
            "- 配方导入时，重复编号会自动跳过，不会覆盖已有数据\n"
            "- 性能预测需要至少 5 条含对应指标的配方数据才能训练\n"
            "- 知识库支持多次上传，新文档会累加到已有检索库中\n"
            "- 所有操作记录均可在后台审计日志中查看"
        ),
        "en": (
            "- In Agent mode, AI can automatically invoke 10 tools for complex tasks (e.g., 'Find a coating formula and analyze its pros and cons')\n"
            "- Duplicate formula codes are auto-skipped during import\n"
            "- Performance prediction requires at least 5 formulas with the target property for training\n"
            "- Knowledge base supports multiple uploads; new documents accumulate in the retrieval index\n"
            "- All operations are logged in the admin audit log"
        ),
    },

    # ============ 版权与品牌 ============
    "copyright_text": {
        "zh": "© 2026 MartinHung 保留所有权利",
        "en": "© 2026 MartinHung. All rights reserved.",
    },
    "brand_slogan": {
        "zh": "AI 驱动的化工研发创新平台",
        "en": "AI-Powered Chemical R&D Innovation Platform",
    },
    "version_label": {"zh": "版本", "en": "Version"},

    # ============ 登录页增强 ============
    "login_welcome": {
        "zh": "欢迎使用 ChemAgent",
        "en": "Welcome to ChemAgent",
    },

    # ============ Dashboard 增强 ============
    "dashboard_welcome": {
        "zh": "欢迎回来，{}！",
        "en": "Welcome back, {}!",
    },
    "dashboard_stats_title": {
        "zh": "知识库概览",
        "en": "Knowledge Base Overview",
    },
    "dashboard_features_title": {
        "zh": "核心功能",
        "en": "Core Features",
    },

    # ============ 各页面描述 ============
    "page_desc_chat": {
        "zh": "与 AI 助手对话，获取配方建议、技术问答和智能推理分析",
        "en": "Chat with AI for formula advice, technical Q&A, and intelligent reasoning",
    },
    "page_desc_search": {
        "zh": "通过关键词、类别、原料等多维度条件精准检索历史配方数据",
        "en": "Search historical formulas by keywords, categories, and materials",
    },
    "page_desc_manage": {
        "zh": "在线创建、编辑配方，支持 Excel / JSON 批量导入导出",
        "en": "Create and edit formulas online, with Excel / JSON batch import & export",
    },
    "page_desc_analysis": {
        "zh": "AI 深度分析配方的优劣势、成本结构和改进建议",
        "en": "AI-powered deep analysis of formula strengths, costs, and improvements",
    },
    "page_desc_predict": {
        "zh": "基于机器学习模型预测配方性能指标",
        "en": "Predict formula performance metrics using machine learning models",
    },
    "page_desc_recommend": {
        "zh": "根据需求目标，AI 智能推荐最优配方方案",
        "en": "AI-powered formula recommendations based on your requirements",
    },
    "page_desc_materials": {
        "zh": "搜索、管理原材料信息，获取替代材料建议",
        "en": "Search and manage raw materials, get substitution suggestions",
    },
    "page_desc_knowledge": {
        "zh": "管理技术文档，利用语义搜索检索专业知识",
        "en": "Manage technical documents and retrieve knowledge via semantic search",
    },
    "page_desc_admin": {
        "zh": "管理用户、角色、权限、产品分类和系统配置",
        "en": "Manage users, roles, permissions, categories, and system settings",
    },

    # ============ Dashboard 功能卡片 ============
    "feat_short_chat_name": {"zh": "智能问答", "en": "AI Chat"},
    "feat_short_chat_desc": {
        "zh": "与 AI 对话，获取专业配方建议",
        "en": "Chat with AI for professional formula advice",
    },
    "feat_short_search_name": {"zh": "配方检索", "en": "Formula Search"},
    "feat_short_search_desc": {
        "zh": "多维度精准检索历史配方",
        "en": "Multi-dimensional search for formulas",
    },
    "feat_short_analysis_name": {"zh": "配方分析", "en": "Analysis"},
    "feat_short_analysis_desc": {
        "zh": "AI 深度分析配方优劣势",
        "en": "AI-powered formula analysis",
    },
    "feat_short_predict_name": {"zh": "性能预测", "en": "Prediction"},
    "feat_short_predict_desc": {
        "zh": "ML 模型预测配方性能",
        "en": "ML-based performance prediction",
    },
    "feat_short_recommend_name": {"zh": "配方推荐", "en": "Recommend"},
    "feat_short_recommend_desc": {
        "zh": "根据需求智能推荐配方",
        "en": "Smart formula recommendations",
    },
    "feat_short_materials_name": {"zh": "原材料管理", "en": "Materials"},
    "feat_short_materials_desc": {
        "zh": "管理原材料与替代建议",
        "en": "Manage materials & substitutions",
    },

    # ============ Visualization ============
    "chart_category_dist": {
        "zh": "产品类别分布",
        "en": "Category Distribution",
    },
    "chart_material_top": {
        "zh": "原材料使用 TOP10",
        "en": "Top 10 Materials Usage",
    },
    "chart_composition": {
        "zh": "组分组成",
        "en": "Composition",
    },
    "chart_performance_radar": {
        "zh": "性能指标雷达图",
        "en": "Performance Radar",
    },
    "chart_confidence": {
        "zh": "预测置信度",
        "en": "Prediction Confidence",
    },
    "chart_no_data": {
        "zh": "暂无数据",
        "en": "No data available",
    },

    # ============ Comparison ============
    "compare_select": {
        "zh": "选择对比",
        "en": "Select",
    },
    "compare_btn": {
        "zh": "对比选中配方",
        "en": "Compare Selected",
    },
    "compare_title": {
        "zh": "配方对比",
        "en": "Formula Comparison",
    },
    "compare_tab_table": {
        "zh": "表格对比",
        "en": "Table View",
    },
    "compare_tab_chart": {
        "zh": "图表对比",
        "en": "Chart View",
    },
    "compare_basic_info": {
        "zh": "基本信息对比",
        "en": "Basic Info",
    },
    "compare_composition": {
        "zh": "组分对比",
        "en": "Composition",
    },
    "compare_performance": {
        "zh": "性能对比",
        "en": "Performance",
    },
    "compare_min_hint": {
        "zh": "请至少选择 2 个配方",
        "en": "Select at least 2 formulas",
    },
    "compare_none": {
        "zh": "未找到配方数据",
        "en": "No formula data found",
    },

    # ============ Search enhancement ============
    "search_view_mode": {
        "zh": "显示方式",
        "en": "View Mode",
    },
    "search_view_card": {
        "zh": "卡片视图",
        "en": "Card View",
    },
    "search_view_table": {
        "zh": "表格视图",
        "en": "Table View",
    },
    "search_sort_by": {
        "zh": "排序方式",
        "en": "Sort By",
    },
    "search_sort_similarity": {
        "zh": "相似度降序",
        "en": "Similarity Desc",
    },
    "search_sort_name": {
        "zh": "名称升序",
        "en": "Name Asc",
    },
    "search_sort_category": {
        "zh": "按类别",
        "en": "By Category",
    },

    # ============ Knowledge base enhancement ============
    "kb_excel_support": {
        "zh": "支持 Excel 文件",
        "en": "Excel files supported",
    },
    "kb_summary_label": {
        "zh": "文档摘要",
        "en": "Document Summary",
    },
    "kb_generating_summary": {
        "zh": "正在生成摘要...",
        "en": "Generating summary...",
    },

    # ============ Report generation ============
    "report_btn": {
        "zh": "生成研发报告",
        "en": "Generate R&D Report",
    },
    "report_generating": {
        "zh": "正在生成报告...",
        "en": "Generating report...",
    },
    "report_download": {
        "zh": "下载报告",
        "en": "Download Report",
    },
    "report_include_analysis": {
        "zh": "包含 AI 分析",
        "en": "Include AI Analysis",
    },

    # ============ Lifecycle management ============
    "formula_status": {
        "zh": "配方状态",
        "en": "Formula Status",
    },
    "status_draft": {
        "zh": "草稿",
        "en": "Draft",
    },
    "status_review": {
        "zh": "评审中",
        "en": "In Review",
    },
    "status_approved": {
        "zh": "已批准",
        "en": "Approved",
    },
    "status_archived": {
        "zh": "已归档",
        "en": "Archived",
    },
    "status_filter": {
        "zh": "状态筛选",
        "en": "Status Filter",
    },
    "status_all": {
        "zh": "全部状态",
        "en": "All Status",
    },
    "status_updated": {
        "zh": "状态已更新",
        "en": "Status updated",
    },

    # ============ Materials enhancement ============
    "material_detail": {
        "zh": "原材料详情",
        "en": "Material Detail",
    },
    "material_properties": {
        "zh": "理化性质",
        "en": "Physical Properties",
    },
    "material_density": {
        "zh": "密度 (g/cm³)",
        "en": "Density (g/cm³)",
    },
    "material_viscosity": {
        "zh": "粘度 (mPa·s)",
        "en": "Viscosity (mPa·s)",
    },
    "material_boiling_point": {
        "zh": "沸点 (°C)",
        "en": "Boiling Point (°C)",
    },
    "material_flash_point": {
        "zh": "闪点 (°C)",
        "en": "Flash Point (°C)",
    },
    "material_related": {
        "zh": "关联配方",
        "en": "Related Formulas",
    },

    # ============ Recommendation enhancement ============
    "recommend_structured": {
        "zh": "推荐方案详情",
        "en": "Recommendation Details",
    },
    "recommend_apply": {
        "zh": "应用到新配方",
        "en": "Apply to New Formula",
    },
    "recommend_view_ref": {
        "zh": "查看详情",
        "en": "View Details",
    },

    # ============ DOE experiment design ============
    "nav_experiment": {
        "zh": "🔬 实验设计",
        "en": "🔬 Experiment Design",
    },
    "page_desc_experiment": {
        "zh": "基于 DOE 方法设计和优化实验方案",
        "en": "Design and optimize experiments using DOE methods",
    },
    "exp_title": {
        "zh": "实验设计 (DOE)",
        "en": "Experiment Design (DOE)",
    },
    "exp_tab_design": {
        "zh": "实验设计",
        "en": "Design",
    },
    "exp_tab_virtual": {
        "zh": "虚拟实验",
        "en": "Virtual Experiment",
    },
    "exp_method": {
        "zh": "实验方法",
        "en": "Method",
    },
    "exp_full_factorial": {
        "zh": "全因子设计",
        "en": "Full Factorial",
    },
    "exp_latin_hypercube": {
        "zh": "拉丁超立方",
        "en": "Latin Hypercube",
    },
    "exp_factors": {
        "zh": "实验因子",
        "en": "Factors",
    },
    "exp_factor_name": {
        "zh": "因子名称",
        "en": "Factor Name",
    },
    "exp_factor_min": {
        "zh": "最小值",
        "en": "Min",
    },
    "exp_factor_max": {
        "zh": "最大值",
        "en": "Max",
    },
    "exp_levels": {
        "zh": "水平数",
        "en": "Levels",
    },
    "exp_samples": {
        "zh": "样本数",
        "en": "Samples",
    },
    "exp_generate": {
        "zh": "生成实验方案",
        "en": "Generate Design",
    },
    "exp_matrix": {
        "zh": "实验矩阵",
        "en": "Experiment Matrix",
    },
    "exp_run_virtual": {
        "zh": "运行虚拟预测",
        "en": "Run Virtual Prediction",
    },
    "exp_running": {
        "zh": "正在运行虚拟实验...",
        "en": "Running virtual experiments...",
    },
    "exp_export": {
        "zh": "导出实验方案",
        "en": "Export Design",
    },
    "exp_no_factors": {
        "zh": "请至少添加一个因子",
        "en": "Add at least one factor",
    },


    # ============ 配方版本管理 ============
    "nav_versions": {
        "zh": "📋 版本历史",
        "en": "📋 Version History",
    },
    "formula_versions_title": {
        "zh": "配方版本管理",
        "en": "Formula Version Management",
    },
    "formula_versions_code_label": {
        "zh": "配方编号",
        "en": "Formula Code",
    },
    "formula_versions_enter_code": {
        "zh": "请输入配方编号查看版本历史。",
        "en": "Enter a formula code to view version history.",
    },
    "formula_versions_no_record": {
        "zh": "该配方尚无版本记录。",
        "en": "No version records for this formula.",
    },
    "formula_versions_empty": {
        "zh": "暂无版本记录。",
        "en": "No version records yet.",
    },
    "formula_versions_diff_title": {
        "zh": "版本对比",
        "en": "Version Diff",
    },
    "formula_versions_v1": {
        "zh": "版本 A",
        "en": "Version A",
    },
    "formula_versions_v2": {
        "zh": "版本 B",
        "en": "Version B",
    },
    "formula_versions_compare": {
        "zh": "对比",
        "en": "Compare",
    },
    "formula_versions_same": {
        "zh": "请选择两个不同版本进行对比。",
        "en": "Please select two different versions to compare.",
    },
    "formula_versions_loading": {
        "zh": "正在对比...",
        "en": "Comparing...",
    },
    "formula_versions_no_diff": {
        "zh": "两个版本完全相同。",
        "en": "The two versions are identical.",
    },
    "formula_versions_snapshot": {
        "zh": "版本快照查看",
        "en": "Version Snapshot",
    },
    "formula_versions_select": {
        "zh": "选择版本",
        "en": "Select Version",
    },
    "formula_versions_view": {
        "zh": "查看快照",
        "en": "View Snapshot",
    },
}

# 产品类别：显示名称 -> 后端 API 值（中文）
CATEGORY_KEYS = [
    "cat_coating", "cat_adhesive", "cat_sealant", "cat_resin",
    "cat_surfactant", "cat_catalyst", "cat_additive", "cat_plastic",
    "cat_rubber", "cat_ink", "cat_other",
]

# 功能分类键列表
FUNCTION_KEYS = [
    "func_base_resin", "func_solvent", "func_filler", "func_pigment",
    "func_curing_agent", "func_catalyst", "func_dispersant", "func_leveling",
    "func_defoamer", "func_thickener", "func_plasticizer", "func_antioxidant",
    "func_uv_stabilizer", "func_flame_retardant", "func_coupling_agent",
    "func_wetting_agent", "func_other",
]
