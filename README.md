# 通用 ERP 自动化交付平台

基于 AI 多 Agent 协同的 SaaS ERP 自动化交付平台。5 个专业化 AI 子 Agent 通过 Supervisor 模式协同工作，从需求解析到运维答疑，全流程自动化 ERP 项目实施交付。支持 **JEECG、Odoo、ERPNext、SAP S/4HANA、Dynamics 365、金蝶云、用友 YonSuite** 及自定义 REST API 共 8 种 ERP 系统。

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    React + TypeScript 前端                  │
│                  (Cal.com 设计系统, Vite)                    │
├─────────────────────────────────────────────────────────────┤
│                  FastAPI 编排层 (Supervisor)                │
│          状态机 → Agent 调度 → 工具注册 → SSE 流式输出        │
├──────────┬──────────┬──────────┬──────────┬─────────────────┤
│需求解析   │方案生成   │系统配置  │数据迁移   │   运维答疑      │
│Agent     │Agent      │Agent    │Agent     │   Agent        │
│          │           │         │          │                │
│解析需求   │生成方案   │配置 ERP  │导入数据   │  7×24 运维     │
│文档       │PPT/Excel │自动创建  │批量迁移   │  故障诊断       │
│          │          │组织/审批  │          │                │
├──────────┴──────────┴──────────┴──────────┴─────────────────┤
│                 MySQL + Redis + Milvus + MinIO              │
└─────────────────────────────────────────────────────────────┘
```

## 快速开始

### 环境要求

- **Python** 3.12+
- **Node.js** 18+
- **pnpm** (前端包管理器)
- **Docker Desktop** (基础设施)

### 一键启动

```bash
# 1. 启动 Docker Desktop

# 2. 双击运行
python start.py

# 或者手动启动
cd frontend && pnpm install && pnpm dev
cd backend && pip install -r requirements.txt && uvicorn app.main:app --port 8000
```

访问 `http://localhost:5173`

### Docker 服务

```bash
cd D:\project3
docker compose up -d    # MySQL, Redis, Milvus, MinIO

cd D:\jeecg-boot
docker compose up -d    # JEECG ERP (可选)
```

## 支持的 ERP 系统

| Provider | API 风格 | 认证方式 | 配置文件 |
|---|---|---|---|
| JEECG Boot | REST | JWT | `config/erp_providers/jeecg.yaml` |
| Odoo | JSON-RPC/REST | API Key | `config/erp_providers/odoo.yaml` |
| ERPNext | REST | Token | `config/erp_providers/erpnext.yaml` |
| SAP S/4HANA | OData | OAuth2 | `config/erp_providers/sap_s4hana.yaml` |
| Dynamics 365 BC | OData | OAuth2 | `config/erp_providers/dynamics365.yaml` |
| 金蝶云·苍穹 | REST | OAuth2 | `config/erp_providers/kingdee.yaml` |
| 用友 YonSuite | REST | OAuth2 | `config/erp_providers/yonsuite.yaml` |
| 自定义 REST API | REST | 任意 | `config/erp_providers/custom.yaml` |

添加新 ERP：复制 `custom.yaml`，填写 API 路径和认证方式即可。

## 五大 Agent

| Agent | 功能 | 输出 |
|---|---|---|
| **需求解析** | 解析客户需求文档（PDF/DOCX），提取组织架构、模块清单 | 结构化需求 JSON |
| **方案生成** | 基于历史案例生成实施方案、报价单、培训计划 | PPT + Excel |
| **系统配置** | 调用 ERP API 自动创建组织、用户、审批流、角色 | ERP 实际配置 |
| **数据迁移** | 读取 Excel、映射字段、清洗去重、批量导入 | 迁移报告 + 错误日志 |
| **运维问答** | 知识库检索、故障诊断、告警推送 | 诊断报告 |

## 项目结构

```
├── frontend/          # React + TypeScript + Vite 前端
│   └── src/
│       ├── components/    # UI 组件 + 页面组件
│       ├── pages/         # 路由页面
│       ├── services/      # API 客户端
│       ├── tokens/        # 设计 Token (Cal.com)
│       └── types/         # TypeScript 类型
├── backend/           # FastAPI 后端
│   └── app/
│       ├── agents/        # 5 个 AI Agent
│       ├── api/           # REST 路由
│       ├── orchestrator/  # 状态机 + Supervisor
│       ├── tools/         # 15 个工具实现
│       ├── models/        # SQLAlchemy 模型
│       └── schemas/       # Pydantic Schema
├── config/
│   ├── agents/            # Agent YAML 配置
│   └── erp_providers/     # ERP Provider YAML 配置
├── docker-compose.yml
└── start.py           # 一键启动脚本
```

## License

MIT © 2026 wuwufei88
