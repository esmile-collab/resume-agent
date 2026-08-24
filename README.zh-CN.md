<p align="center">
  <strong>Resume Agent（简历 Agent）</strong>
</p>

<p align="center">
  <em>一个对话式的简历优化工作台：评分、生成、局部润色与导出，全程留痕可追溯。</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/React-18-61dafb.svg" alt="React 18" />
  <img src="https://img.shields.io/badge/FastAPI-0.110+-009688.svg" alt="FastAPI" />
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT" />
</p>

<p align="center">
  <a href="README.md">English</a> · <strong>简体中文</strong>
</p>

---

## 解决什么问题

**Resume Agent** 是一个围绕会话式工作流搭建的端到端简历优化平台。和一次性问答的聊天工具不同，它被设计成一个可部署的系统：求职过程中的每个决定、每版产物和每次评分记录都会被保留下来。

上传基础简历和目标 JD（职位描述）后，系统会分析差距、评估匹配度、生成定向版本、局部润色表达并导出——所有操作都在同一个工作台内完成，背后是结构化记忆和完整的审计记录。

## 谁可以使用

- 同时投递多个岗位、希望把简历优化变成可重复、可检查流程的求职者。
- 想参考如何把一个带评分、结构化记忆和全链路追踪的 Agent（智能代理）工作流落地成可部署系统的开发者。

## 提供了什么

- **会话管理**：创建、恢复和切换求职会话，状态完整持久化。
- **简历评分**：硬性指标（关键词、结构、经历密度）与 LLM（大语言模型）软性评估结合的混合评分引擎，支持 JD 隐含要求推断。
- **智能生成**：在保持事实准确的前提下，生成对齐目标 JD 的简历版本。
- **分块润色**：针对局部表达做定向改进，带修改记录和差异对比。
- **多格式导出**：导出 PDF 或 DOCX，产物带版本管理。
- **结构化记忆**：职业档案、经历条目和求职方向以可查询的结构化数据存储，而不是原始聊天记录。
- **全程可追溯**：每个 Agent 动作都会记录为可观察的追踪日志，带快照差异和产物版本。

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│   ChatPanel · ScorePanel · MemoryPanel · ArtifactPanel  │
└─────────────────────────┬───────────────────────────────┘
                          │ REST API
┌─────────────────────────▼───────────────────────────────┐
│                  API Layer (FastAPI)                      │
│              Sessions · Messages · Artifacts              │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                   Agent Runtime                           │
│   Planner → Memory → Tool Registry → Runtime Pipeline    │
└──┬──────────┬──────────┬──────────┬──────────┬──────────┘
   │          │          │          │          │
┌──▼──┐  ┌───▼───┐ ┌────▼───┐ ┌───▼───┐ ┌───▼────┐
│Scoring│  │ JD    │ │Resume  │ │Polish │ │Export  │
│Engine │  │Analyzer│ │Parser  │ │Patcher│ │Service │
└──┬───┘  └───┬───┘ └────┬───┘ └───┬───┘ └───┬────┘
   │          │          │          │          │
┌──▼──────────▼──────────▼──────────▼──────────▼────────┐
│               Persistence (SQLite)                      │
│         Sessions · Artifacts · Snapshots                │
└────────────────────────────────────────────────────────┘
```

## 如何开始使用

### 环境要求

- Python 3.11+
- Node.js 20+
- npm

### 安装与运行

```bash
# 克隆仓库
git clone git@github.com:esmile-collab/resume-agent.git
cd resume-agent

# 配置环境
cp .env.example .env
# 编辑 .env —— 填入你的 LLM API Key（Anthropic 或 OpenAI）

# 一键启动（安装依赖、初始化数据库、同时启动前后端）
./start.sh
```

启动后可以访问：

| 服务 | 地址 |
| --- | --- |
| 前端 | http://127.0.0.1:5173 |
| 后端 | http://127.0.0.1:8000 |
| API 文档 | http://127.0.0.1:8000/docs |

### 只启动单个服务

```bash
./start.sh backend    # 只启动 API 服务
./start.sh frontend   # 只启动前端开发服务器
```

### Docker

```bash
docker build -t resume-agent .
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -v resume-data:/app/.data \
  resume-agent
```

## 项目结构

```
resume-agent/
├── frontend/                 # React 前端（Vite + TypeScript）
│   └── src/
│       ├── components/       # 界面面板：对话、评分、记忆、产物等
│       ├── api/              # 前端 API 客户端
│       └── types.ts          # 共享 TypeScript 类型
├── src/                      # 后端 Python 包
│   ├── api/                  # FastAPI HTTP 层与接口
│   ├── agent/                # 核心运行时：规划器、记忆、工具
│   ├── services/             # 领域逻辑：JD 分析、解析、润色、导出
│   ├── scoring/              # 混合评分引擎
│   ├── db/                   # SQLite 表结构与数据访问
│   ├── observability/        # 长上下文压缩与追踪日志
│   ├── cli/                  # 基于 Click 的命令行
│   └── tools/                # 工具实现
├── tests/                    # 验收、单元、集成与端到端测试
├── docs/                     # 产品与技术文档
├── scripts/                  # 初始化、评测、回归与文档检查脚本
├── config/                   # 默认配置（YAML）
├── Dockerfile                # 生产容器镜像
├── render.yaml               # Render.com 部署配置
└── pyproject.toml            # Python 包清单
```

## 使用流程

1. **创建会话**：新建工作台，可选附上基础简历。
2. **建立档案**：系统提取并存储结构化档案、经历和求职方向。
3. **录入 JD**：上传职位描述，系统按求职方向分析并归档。
4. **评分**：运行匹配分析，得到带差距识别的详细评分卡。
5. **生成 / 润色**：产出针对 JD 的简历版本，所有修改可追踪。
6. **导出**：下载 PDF 或 DOCX，保留完整版本历史。
7. **回顾**：随时可以查看快照、执行追踪和产物差异。

## 开发

### 环境准备

```bash
# 后端
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 前端
cd frontend && npm install
```

### 运行测试

```bash
# 全部测试
python -m pytest tests/

# 验收 + 单元测试
python -m pytest tests/acceptance tests/unit/

# 带覆盖率
python -m pytest --cov=src --cov-report=html tests/
```

### Lint 与格式化

```bash
python -m black src/ tests/
python -m mypy src/
```

### 构建前端

```bash
cd frontend && npm run build
```

## 文档

| 文档 | 说明 |
| --- | --- |
| [产品 PRD](docs/product/MVP_PRD_Resume_Fit_Agent.md) | 产品需求与范围 |
| [系统架构](docs/technical/ARCHITECTURE.md) | 系统设计与模块职责 |
| [评分系统](docs/product/评分系统设计_v2_混合评分_校招版_v2.1.md) | 评分引擎设计与方法 |
| [部署指南](docs/DEPLOYMENT.md) | 生产环境部署说明 |
| [交互设计](docs/product/UI交互设计.md) | 界面交互流程 |

## 技术栈

| 层 | 技术 |
| --- | --- |
| 前端 | React 18 · TypeScript · Vite |
| 后端 | Python 3.11 · FastAPI · Uvicorn |
| 数据库 | SQLite |
| LLM | Anthropic Claude / OpenAI GPT |
| 文档处理 | pypdf · python-docx · reportlab |
| 命令行 | Click |
| 测试 | pytest · pytest-cov · pytest-asyncio |
| 部署 | Docker · Render.com |

## 许可证

本项目采用 MIT License，详见 [LICENSE](LICENSE)。
