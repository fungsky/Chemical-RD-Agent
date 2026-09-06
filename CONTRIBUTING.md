# 贡献指南

感谢你对 ChemAgent 的关注！以下是参与贡献的指引。

## 开发环境搭建

```bash
git clone https://github.com/<org>/chem-ai-agent.git
cd chem-ai-agent
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
pip install -e ".[dev]"
```

## 代码规范

- Python 3.10+，使用 `ruff` 进行代码检查
- 遵循现有代码风格（100 字符行宽）
- 函数和类添加中文 docstring
- 提交前运行测试：`pytest tests/ -v`

## 提交流程

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feat/your-feature`
3. 提交变更：`git commit -m "feat: 添加某某功能"`
4. 推送分支：`git push origin feat/your-feature`
5. 提交 Pull Request

### Commit 规范

使用 [Conventional Commits](https://www.conventionalcommits.org/)：

- `feat:` 新功能
- `fix:` 修复 Bug
- `docs:` 文档更新
- `refactor:` 重构
- `test:` 测试相关
- `chore:` 构建/工具变动

## 项目结构

```
chem_agent/
├── agent/          # ReAct 智能体
├── api/            # FastAPI 路由
├── auth/           # 认证 & 数据库
│   └── db_backends/  # 多数据库后端
├── config/         # 配置管理
├── knowledge_base/ # 知识库 RAG
├── knowledge_graph/# 知识图谱 Neo4j
├── llm/            # LLM 服务
├── models/         # 数据模型
├── prediction/     # ML 预测
├── ui/             # Streamlit 界面
└── utils/          # 工具函数
```

## 添加新的数据库后端

1. 在 `chem_agent/auth/db_backends/` 创建新文件
2. 继承 `AuthDBBackendBase`，实现全部抽象方法
3. 在 `db_backends/__init__.py` 注册
4. 在 `settings.py` 添加配置项
5. 在 `docker-compose.yml` 添加服务（可选）

## 问题反馈

- Bug 报告：[Issues](https://github.com/<org>/chem-ai-agent/issues/new?template=bug_report.md)
- 功能建议：[Issues](https://github.com/<org>/chem-ai-agent/issues/new?template=feature_request.md)