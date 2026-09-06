# Changelog

## [0.1.0] - 2025-06-23

### Added
- ReAct 智能体引擎，支持反思纠错、经验记忆、任务规划
- 10 个 Agent 工具：配方搜索/详情/相似/分析、原材料搜索/统计/替代、知识库检索、性能预测、图谱统计
- Neo4j 知识图谱存储配方和原材料关系
- ChromaDB 向量检索知识库
- 多 LLM 服务商支持（OpenAI / DeepSeek / Ollama / GLM / Qwen 等 12+）
- ML 性能预测（GradientBoosting）
- JWT 认证 + RBAC 权限管理
- 多数据库后端支持（SQLite / PostgreSQL / MySQL）
- 配方版本管理（快照保存、历史列表、版本对比）
- Docker Compose 一键部署
- 跨平台部署脚本（Windows .bat + Linux/macOS .sh）
- GitHub Actions CI/CD 流水线
- 中英文国际化
- 实验设计（DOE）模块

### Changed
- 数据库层抽象重构，支持多后端切换
- 配置项补全（30+ -> 60+）

### Fixed
- README 路径与实际结构不一致
- 硬编码密钥提取到环境变量