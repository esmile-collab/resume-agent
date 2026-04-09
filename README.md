<!--
Input: 当前仓库结构、现行运行链路与核心工程约束。
Output: 输出仓库级全局地图、主文档入口和维护规则。
Pos: 根目录总地图，是整个分形文档体系的第一层。
Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
-->
# Resume Agent

这是一个面向真实投递场景的会话式简历工作台。当前仓库的目标不是做“聊天玩具”，而是提供一个能本地跑通、能部署、能演示完整主流程的 demo：上传基础简历与 JD，沉淀求职方向资产，完成评分、生成、润色、导出，并把每轮行为留痕到会话和产物版本里。

## 3 分钟上手

### 运行环境

- Python 3.11+
- Node.js 20+
- `npm`

### 一键启动

```bash
cp .env.example .env
./start.sh
```

启动后：

- 前端工作台：`http://127.0.0.1:5173`
- 后端 API：`http://127.0.0.1:8000`

### 常用检查

```bash
python -m pytest tests/acceptance tests/unit/test_fractal_docs.py
cd frontend && npm run build
python scripts/fractal_docs.py --check
```

## 当前能做什么

- 创建会话并恢复历史会话
- 上传基础简历、JD、PDF、DOCX
- 沉淀 `profile / experiences / tracks`
- 管理 `JD Matches / Career Dashboard`
- 执行简历评分、生成、润色
- 查看 artifact 版本并导出 `PDF / DOCX`
- 查看 snapshot、trace 和会话留痕

## 仓库速览

- `frontend/`: React 工作台
- `src/api/`: FastAPI HTTP 入口
- `src/agent/`: planner / memory / runtime / tools 主链
- `src/services/`: JD 分析、简历解析、patch、导出
- `src/scoring/`: 评分引擎
- `src/db/`: SQLite schema 与 CRUD
- `scripts/`: 启动、评测、文档守卫
- `tests/`: acceptance / unit / e2e / integration

## 先看这些文档

- [docs/README.md](docs/README.md)
- [docs/项目运行说明.md](docs/%E9%A1%B9%E7%9B%AE%E8%BF%90%E8%A1%8C%E8%AF%B4%E6%98%8E.md)
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- [docs/product/MVP_PRD_Resume_Fit_Agent.md](docs/product/MVP_PRD_Resume_Fit_Agent.md)
- [docs/product/UI交互设计.md](docs/product/UI%E4%BA%A4%E4%BA%92%E8%AE%BE%E8%AE%A1.md)
- [docs/technical/ARCHITECTURE.md](docs/technical/ARCHITECTURE.md)

## 当前系统地图

| 层级 | 目录 | 作用 |
| --- | --- | --- |
| 入口层 | `frontend/` | React 工作台，负责会话 UI、方向切换、产物编辑与运行轨迹展示。 |
| 入口层 | `src/api/` | FastAPI session/message API 和管理端点。 |
| 运行时 | `src/agent/` | planner、memory、tool registry、runtime 主链。 |
| 领域层 | `src/services/` | JD 分析、简历解析、patch 生成、导出。 |
| 评分层 | `src/scoring/` | 混合评分引擎与评分报告模型。 |
| 持久化层 | `src/db/` | SQLite schema 与 CRUD 仓储。 |
| 观测层 | `src/observability/` | 长对话压缩与摘要落盘。 |
| 工程层 | `scripts/`、`tests/`、`config/` | 启动、回归、文档守卫、默认配置。 |

## 当前产品主流程

1. 用户创建 session，并可附带基础简历。
2. 用户补充背景信息，系统写入 profile、experience、track 等结构化 memory。
3. 用户上传 JD，系统把 JD 入库并归档到对应 track。
4. 用户触发评分，系统生成 score report artifact。
5. 用户触发生成或润色，系统产出新的简历版本并支持导出。
6. 前端随时查看 snapshot、trace、artifact diff 与历史会话。

## 当前主文档

- [docs/README.md](docs/README.md)
- [docs/项目运行说明.md](docs/%E9%A1%B9%E7%9B%AE%E8%BF%90%E8%A1%8C%E8%AF%B4%E6%98%8E.md)
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- [docs/product/MVP_PRD_Resume_Fit_Agent.md](docs/product/MVP_PRD_Resume_Fit_Agent.md)
- [docs/product/UI交互设计.md](docs/product/UI%E4%BA%A4%E4%BA%92%E8%AE%BE%E8%AE%A1.md)
- [docs/product/评分系统设计_v2_混合评分_校招版_v2.1.md](docs/product/%E8%AF%84%E5%88%86%E7%B3%BB%E7%BB%9F%E8%AE%BE%E8%AE%A1_v2_%E6%B7%B7%E5%90%88%E8%AF%84%E5%88%86_%E6%A0%A1%E6%8B%9B%E7%89%88_v2.1.md)
- [docs/technical/ARCHITECTURE.md](docs/technical/ARCHITECTURE.md)

## 分形文档规则

任何功能、架构、写法更新，都必须在工作结束后同步更新相关目录的子文档和文件头注释。

当前文档体系分三层：

1. 根目录 `README.md`：全局地图，只描述当前系统边界、主文档和总规则。
2. 每个受管目录的 `README.md`：3 行内说明本目录定位、边界、维护要求，并列出文件清单。
3. 每个可注释文件的头部声明：`Input / Output / Pos / Rule`，说明依赖、对外输出、局部地位和同步义务。

说明：

- `JSON`、图片、数据集、依赖目录等无法安全内联注释的文件，不强行写文件头，由所属目录 `README.md` 承担说明。
- `docs/archive/` 与 `docs/reference/` 保存历史/参考材料，不再作为当前开发入口。
- `resume-score-skills/`、评测数据集、缓存目录和构建产物不纳入本轮分形文档强约束。
