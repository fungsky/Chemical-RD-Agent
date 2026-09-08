<div align="center">

# Chemical R&D Agent

### 化工研发智能体系统

**AI-Powered Chemical R&D Intelligent Agent**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/<org>/chem-ai-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/<org>/chem-ai-agent/actions/workflows/ci.yml)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

[功能特性](#功能特性) | [技术架构](#技术架构) | [快速开始](#快速开始) | [使用指南](#使用指南) | [截图展示](#截图展示)

</div>

---

## 项目简介

**Chemical R&D Agent** 是一款面向化工研发人员的 AI 智能体系统，整合知识图谱、大语言模型、机器学习和向量检索技术，覆盖配方开发全流程——从检索、分析、预测到推荐。

### 核心价值

- **智能问答** — 基于 RAG 增强检索和 ReAct 智能体，精准回答化工领域专业问题
- **知识沉淀** — 将企业配方数据、技术文档结构化存储，形成可复用的知识资产
- **辅助决策** — AI 分析配方优劣、预测性能指标、推荐优化方案，加速研发迭代
- **降本增效** — 减少重复实验，缩短配方开发周期，降低研发成本

---

## 功能特性

### 智能问答 (AI Chat)

| 模式 | 说明 |
|------|------|
| **普通模式** | 基于知识库文档的 RAG 检索增强问答，自动引用来源 |
| **智能体模式** | ReAct 推理循环，自动调用 10+ 工具搜索数据、分析配方，推理过程完整可见 |

智能体支持：
- **任务规划** — 复杂问题自动拆解为可执行步骤
- **经验记忆** — 跨会话学习，持续优化回答质量
- **反思纠错** — 自动检测并修正推理错误

### 配方管理

- **在线编辑** — 创建/编辑配方（组分、工艺条件、性能指标）
- **批量导入** — 支持 Excel (4-Sheet) / JSON 格式，提供空白模板下载
- **批量导出** — 按条件筛选导出，支持多种格式
- **配方对比** — 多配方并排对比组分和性能差异

### 配方检索

- **多维搜索** — 按关键词、产品类别、原料名称检索
- **相似配方** — 基于 Jaccard 相似度发现关联配方
- **卡片/表格** — 灵活切换展示视图

### AI 配方分析

输入配方编号，AI 从五个维度深度分析：
1. 组成合理性
2. 组分功能定位
3. 工艺适配性
4. 性能达标评估
5. 优化改进方向

### 性能预测

- **机器学习** — 基于 GradientBoosting 预测配方性能（硬度、光泽度等）
- **在线训练** — 使用历史数据训练专属模型
- **置信度** — 预测结果附带可信度评分

### 配方推荐

- 描述需求和目标性能
- 系统搜索历史案例
- AI 生成推荐方案 + 关键组分理由 + 风险提示

### 原材料管理

- **信息维护** — 原材料 CRUD、CAS 号、供应商信息
- **使用统计** — 在哪些配方中使用、平均用量
- **AI 替代建议** — 推荐替代材料 + 性能影响 + 成本分析

### 知识库

- **文档支持** — PDF / Word / TXT / Excel
- **网页抓取** — 输入 URL 自动提取内容
- **语义检索** — 向量化存储，支持自然语言查询

### 实验设计 (DOE)

- **全因子设计** — 系统性覆盖所有因子组合
- **拉丁超立方** — 高效采样策略
- **虚拟实验** — 结合 ML 模型预测实验结果

### 后台管理

- **用户管理** — 创建/编辑/禁用用户账户
- **角色权限** — RBAC 细粒度权限控制
- **LLM 配置** — 支持 12+ 主流 AI 服务商，可视化配置
- **审计日志** — 完整操作记录，合规审计

---

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Streamlit UI                           │
│         (响应式界面 / 多语言支持 / AnythingLLM 风格)          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                        │
│              (RESTful API / JWT 认证 / RBAC)                │
└─────────────────────────────────────────────────────────────┘
          │              │              │              │
          ▼              ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Neo4j      │ │  ChromaDB    │ │  LangChain   │ │ scikit-learn │
│ 知识图谱      │ │  向量数据库   │ │  LLM 服务    │ │   ML 预测    │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

### 技术栈

| 层级 | 技术选型 |
|------|----------|
| **前端** | Streamlit 1.30+ |
| **后端** | FastAPI + Uvicorn |
| **知识图谱** | Neo4j 5.x |
| **向量数据库** | ChromaDB |
| **LLM 框架** | LangChain |
| **机器学习** | scikit-learn |
| **认证** | JWT + SQLite |
| **部署** | Docker Compose |

> **本地免登录模式**：仅本地/内网使用（如对接 Codex 技能版）时，可设
> `CHEM_AUTH_BYPASS=true` 跳过 JWT 登录（所有接口以本地超级管理员放行）。
> 切勿在公网部署下开启该模式。

> **无 Neo4j 本地模式**：未启动 Neo4j 时后端自动切换为内置样例数据
> （18 个配方 / 78 种原料），配方检索、原料查询、图谱统计可用，无需安装
> Java/Neo4j/Docker；写入操作不持久化。

### 支持的 LLM 服务商

| 本地部署 | 云端服务 |
|----------|----------|
| Ollama | OpenAI (GPT-4o/4/3.5) |
| LM Studio | Azure OpenAI |
| | DeepSeek |
| | 智谱 AI (GLM) |
| | 通义千问 (Qwen) |
| | 月之暗面 (Kimi) |
| | 零一万物 (Yi) |
| | Google Gemini |
| | Anthropic Claude |

---


## 快速开始

### 环境要求

- **Docker & Docker Compose**（推荐）或
- **Python 3.10+** + Neo4j 5.x（本地开发）

### 方式一：Docker Compose（推荐，全平台通用）

```bash
# 克隆项目
git clone https://github.com/<org>/chem-ai-agent.git
cd chem-ai-agent

# 配置环境变量
cp .env.example .env
# 编辑 .env 填写 LLM API Key 等配置

# 一键启动
# Linux / macOS:
./deploy.sh docker

# Windows (PowerShell):
.\deploy.bat

# 指定数据库后端
./deploy.sh docker postgres    # SQLite + PostgreSQL
./deploy.sh docker full        # 全部服务
```

**访问地址：**
- 前端 UI: http://localhost:8501
- API 文档: http://localhost:8000/docs
- Neo4j: http://localhost:7474

### 方式二：本地开发（全平台）

`ash
# Linux / macOS:
./deploy.sh local
``n
### 方式三：Windows 原生一键安装（无需 Docker）

```powershell
# PowerShell 中运行（右键 → 以管理员身份运行）
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
.\install.ps1
```

**自动完成：**
1. 检测 Python / Docker / Git 环境
2. 自动安装缺失组件（通过 winget）
3. 创建虚拟环境 + 安装全部依赖
4. 交互式选择大模型（12 个提供商可选）
5. 配置 API Key 写入 `.env`
6. 启动服务 + 自动打开浏览器

```powershell
# 跳过 Docker，纯本地模式
.\install.ps1 -SkipDocker

# 仅安装依赖，不启动
.\install.ps1 -InstallOnly
```
### 服务管理

```bash
# 查看状态
./deploy.sh status      # Linux/macOS
.\logs.bat              # Windows

# 查看日志
./deploy.sh logs        # Linux/macOS
.\logs.bat              # Windows

# 停止服务
./deploy.sh stop        # Linux/macOS
.\stop.bat              # Windows
```## 默认账户

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |
| user | user123 | 普通用户 |

> 首次登录后请修改默认密码

---

## 使用指南

### 1. 配置 LLM

登录后进入 **后台管理 → 大语言模型**：
1. 选择 LLM 提供商（如 Ollama / OpenAI）
2. 填写 Base URL 和 API Key
3. 点击「测试连接」验证
4. 保存配置

### 2. 导入数据

进入 **配方管理 → 批量导入**：
1. 下载 Excel 模板
2. 按模板格式填写配方数据
3. 上传文件完成导入

### 3. 上传知识库

进入 **知识库 → 文档管理**：
1. 上传 PDF/Word/TXT 技术文档
2. 系统自动分块向量化
3. 文档内容将被智能问答引用

### 4. 开始使用

进入 **智能问答**：
- 开启「智能体模式」获得更强大的多步推理能力
- 提问示例：「帮我找一个耐候性好的水性涂料配方并分析优缺点」

---

## 项目结构

```
chem-ai-agent/
├── chem_agent/
│   ├── api/            # FastAPI 后端
│   │   ├── main.py     # 主入口 & 路由
│   │   └── routers/    # 模块化路由
│   ├── ui/             # Streamlit 前端
│   │   ├── app.py      # UI 主入口
│   │   ├── admin_pages.py  # 后台管理
│   │   └── i18n.py     # 多语言翻译
│   ├── knowledge_graph/           # 核心服务
│   │   ├── kg_service.py   # 知识图谱
│   │   └── kb_service.py   # 知识库
│   ├── llm/            # LLM 服务
│   │   └── llm_service.py
│   ├── agent/          # ReAct 智能体
│   │   └── react_agent.py
│   ├── auth/           # 认证授权
│   └── config/         # 配置管理
├── data/               # 数据目录
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。

---

## 联系方式

- **Email**:188230680@qq.com

---

<div align="center">

**Chemical R&D Agent** — 让 AI 成为化工研发的得力助手

</div>

---

## 发布到 GitHub

### 首次发布步骤

```bash
# 1. 在 GitHub 创建新仓库 chem-ai-agent

# 2. 初始化本地仓库并推送
cd chem-ai-agent
git init
git add .
git commit -m "feat: ChemAgent initial release - cross-platform AI chemistry agent"
git branch -M main
git remote add origin https://github.com/<your-org>/chem-ai-agent.git
git push -u origin main

# 3. 创建版本标签（触发自动 Release）
git tag v0.1.0
git push --tags
```

### CI/CD 流水线

推送后 GitHub Actions 自动运行：
- **CI**：Python 3.10/3.11/3.12 × Ubuntu/macOS/Windows 全矩阵测试
- **Docker Build**：验证镜像可构建
- **Release**：推送 `v*` 标签后自动创建 GitHub Release

### 仓库设置建议

1. **Settings → Actions → General**：允许 Actions 读写仓库
2. **Settings → Environments**：可添加 `production` 环境保护规则
3. **Settings → Secrets**：如需推送到 Docker Hub，添加 `DOCKER_USERNAME` / `DOCKER_PASSWORD`

### 项目文件结构

```
chem-ai-agent/
├── chem_agent/             # 核心代码
│   ├── agent/              # ReAct 智能体
│   ├── api/                # FastAPI 路由
│   ├── auth/               # 认证 & 多数据库后端
│   │   └── db_backends/    # SQLite / PostgreSQL / MySQL
│   ├── config/             # 配置 + 日志
│   ├── knowledge_base/     # RAG 知识库
│   ├── knowledge_graph/    # Neo4j 知识图谱
│   ├── llm/                # LLM 服务（12+ 厂商）
│   ├── models/             # 数据模型
│   ├── prediction/         # ML 性能预测
│   ├── ui/                 # Streamlit 前端
│   └── utils/              # 工具函数
├── scripts/                # 跨平台部署脚本
│   ├── deploy.sh           # Linux/macOS 一键部署
│   └── stop.sh             # 停止服务
├── tests/                  # 测试套件
├── data/                   # 初始化数据
├── .github/
│   ├── workflows/          # CI/CD 流水线
│   │   ├── ci.yml          # 自动化测试
│   │   └── release.yml     # 自动发布
│   └── ISSUE_TEMPLATE/     # Issue 模板
├── docker-compose.yml      # Docker 编排
├── Dockerfile              # 容器构建
├── deploy.bat / deploy.sh  # 一键部署入口
├── pyproject.toml          # 项目元数据
├── requirements.txt        # 依赖清单
├── CHANGELOG.md            # 变更日志
├── CONTRIBUTING.md         # 贡献指南
└── LICENSE                 # MIT 许可证
```
