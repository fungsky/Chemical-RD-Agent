# Chemical R&D Agent（ChemAgent）

**面向日化、精细化工、医药研发人员的 AI 研发助理**：把客户需求变成配方草稿，把实验数据变成洞察，把技术资料变成可检索知识。不替代 PLM/LIMS/ERP，只做研发 AI 与数据内核。

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-green)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-blue)](https://react.dev)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

> 外部集成边界说明见 [docs/外部系统集成边界与接口清单.md](docs/外部系统集成边界与接口清单.md)

## 功能

- AI 研发助理：需求 → 配方草稿 / 调整 / 分析，支持显示思考过程
- 配方中心：检索、新建、编辑、版本历史、批量导入导出
- 原材料库：材料档案、参数查看、供应商、批量导入导出
- 实验与预测：DOE 设计 → 一键转实验计划 → 目标规格自动判定 → 模型训练与可信度提示
- 知识 Wiki：文档上传、AI 编译、知识页人工查阅与修正、语义检索
- 系统管理：AI 服务接入（12+ 厂商）、主题/字号、用户/角色/审计
- 研发工作台：客户需求、样品反馈、待办、时间线、AI 下一步建议、项目报告

## 快速启动

### Docker Compose（推荐）

```bash
docker compose up -d --build
docker compose --profile init up -d   # 首次初始化样例数据
```

### 本地开发

后端：

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -e .
python run.py api
```

前端（React + Ant Design）：

```bash
cd web
npm install
npm run dev
```

默认账户：`admin / admin123`（请及时修改）。

## 技术架构

```text
React + AntD (web/)
      │ REST / OpenAPI
FastAPI (chem_agent/api/)
      ├─ Neo4j 知识图谱（可降级本地模式）
      ├─ SQLite/PostgreSQL/MySQL 认证与配置
      ├─ ChromaDB 知识库 / LLM Wiki
      └─ LLM：OpenAI 兼容（智谱、DeepSeek、通义等 12+ 厂商）
```

## 目录

```text
chem_agent/   FastAPI 后端
web/          React + Ant Design 前端
data/         样例数据与标准索引
tests/        自动化测试
docs/         产品与集成文档
```

## 开源与边界

- 本项目定位为 **AI + 研发数据内核**，不实现 PLM/LIMS/ERP 流程；
- 外部系统（PLM/LIMS/ERP）通过接口/导入导出集成；
- 涉及安全、法规、健康数据时，AI 结论仅作为研发参考，需人工核验。

## 联系

欢迎 Issues / Discussions 反馈问题与使用场景。
