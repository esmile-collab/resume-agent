#!/usr/bin/env python3
# Input: 仓库结构、目录元信息和文件元信息覆盖表。
# Output: 生成或校验目录 README 与文件头部声明。
# Pos: 分形文档体系的同步器与守门脚本。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MANAGED_ROOTS = [
    "config",
    "docs",
    "frontend",
    "scripts",
    "src",
    "tests",
]

ROOT_MANAGED_FILES = [
    "README.md",
    "Dockerfile",
    "pyproject.toml",
    "render.yaml",
    "start.sh",
]

EXCLUDED_DIR_NAMES = {
    ".git",
    ".data",
    ".backup",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "dist",
    "node_modules",
    "resume_agent.egg-info",
    "evaluation_dataset",
    "evaluation_dataset_v2",
    "evaluation_results",
    "resume-score-skills",
    "stitch picture",
    "expected",
    "fixtures",
}

EXCLUDED_FILE_NAMES = {
    ".DS_Store",
    "package-lock.json",
    "vite.config.js",
    "vite.config.d.ts",
    "tsconfig.tsbuildinfo",
    "tsconfig.node.tsbuildinfo",
}

NON_COMMENTABLE_SUFFIXES = {
    ".json",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".pdf",
    ".csv",
}

DIR_META: dict[str, tuple[str, str, str]] = {
    "config": (
        "仓库默认配置基线，只存环境无关参数。",
        "服务启动前读取这里的默认值，不承载业务编排。",
        "本目录文件变更后，先更新本页，再检查根目录 README 的系统地图。",
    ),
    "docs": (
        "现行文档总入口，只保留当前 demo 的主线资料与归档索引。",
        "把活文档、参考资料、历史沉淀分层放置，避免方案混写。",
        "本目录结构或文档角色变更后，务必回写根目录 README 与对应子目录 README。",
    ),
    "docs/archive": (
        "历史分析与阶段性文档归档区。",
        "保留曾经的讨论与阶段计划，但不再作为当前开发入口。",
        "这里新增或迁移文件时，要同步说明它为什么退出主文档集。",
    ),
    "docs/archive/analysis": (
        "专题分析归档区。",
        "存放意图识别、LLM 策略、润色方案等横向研究材料。",
        "这里只做回溯，不承载当前实现约束。",
    ),
    "docs/archive/history": (
        "阶段任务与流程规范归档区。",
        "保留里程碑计划、验收模板与旧运行说明，供复盘使用。",
        "若恢复某份文档为现行入口，需把它迁回活跃目录并更新索引。",
    ),
    "docs/reference": (
        "参考资料区，保存仍有价值但不进入主导航的材料。",
        "这里的内容可辅助评测或专项验证，但不定义当前产品主流程。",
        "引用这里的文档时，要在活文档里明确“参考”而不是“现行约束”。",
    ),
    "docs/reference/evaluation": (
        "评测体系参考区。",
        "存放数据集策略、评测总结和快速使用说明，服务效果验证。",
        "评测入口变化时，要同步更新 docs/README 与根目录 README。",
    ),
    "docs/product": (
        "产品需求与交互设计目录。",
        "只保留当前 demo 真正在用的 PRD、UI 设计和评分子系统说明。",
        "任何功能范围或交互规则变化，都要先回写这里，再提交代码。",
    ),
    "docs/product/archive": (
        "产品设计历史归档区。",
        "保存旧版 PRD、评分方案演化稿和草案文档，供追溯对比。",
        "这些文档不再约束当前实现，只作为历史证据。",
    ),
    "docs/technical": (
        "技术设计目录，描述当前可运行 demo 的真实架构。",
        "重点解释运行链路、模块边界、持久化、部署与运维方式。",
        "技术边界变更时，这里是代码后的第一更新点。",
    ),
    "docs/technical/archive": (
        "技术方案历史归档区。",
        "保留旧路由、多轮设计、工具替换计划和 memory 规划草稿。",
        "若某份方案重新启用，需迁回现行目录并重写定位说明。",
    ),
    "frontend": (
        "React 工作台前端目录。",
        "承载会话 UI、记忆面板、方向管理与产物编辑，不保存服务端业务规则。",
        "前端入口或构建部署调整后，更新本页与根目录运行地图。",
    ),
    "frontend/src": (
        "前端源码主目录。",
        "由 App 状态编排、API 客户端和各业务面板组成。",
        "本目录文件增删改后，要同步说明数据流和组件职责变化。",
    ),
    "frontend/src/api": (
        "前端 API 适配层。",
        "把 React 侧请求统一收口到 session/message 与管理端点。",
        "接口字段或调用路径变化时，这里和后端文档必须一起更新。",
    ),
    "frontend/src/components": (
        "前端业务面板目录。",
        "每个组件承担一个工作台子视图，围绕同一份会话状态工作。",
        "组件职责变化后，更新本页，避免 UI 与系统地图脱节。",
    ),
    "scripts": (
        "工程脚本目录。",
        "放置启动、评测、回归和文档检查脚本，不承载核心业务模块。",
        "新增脚本前先判断是否属于长期能力，避免临时脚本堆积。",
    ),
    "src": (
        "后端源码主目录。",
        "按运行时、API、数据库、评分、服务与观测分层组织。",
        "任何模块边界调整都必须先更新这里，再更新对应子目录 README。",
    ),
    "src/agent": (
        "会话式 Agent 核心编排层。",
        "负责 plan、tool、memory、runtime 四块主链，驱动 think-call-observe。",
        "这是系统主心骨，接口或链路调整必须先在此目录落字。",
    ),
    "src/api": (
        "FastAPI HTTP 入口层。",
        "把前端与外部调用转成运行时、记忆管理和产物管理操作。",
        "新增端点前先确认它属于现有 session/message 模型。",
    ),
    "src/cli": (
        "命令行入口层。",
        "提供数据库初始化、服务启动和会话调试命令。",
        "CLI 能力要和 HTTP 入口保持同一套运行时语义。",
    ),
    "src/db": (
        "SQLite 持久化层。",
        "定义表结构、数据库连接和 CRUD 仓储，为 runtime 提供状态落盘。",
        "表结构变化时，必须同步更新技术文档里的对象模型。",
    ),
    "src/observability": (
        "轻量观测与对话压缩目录。",
        "负责长对话压缩和摘要落盘，辅助 memory 管理。",
        "观测策略变化时，要同步更新 ARCHITECTURE 与这里的目录说明。",
    ),
    "src/scoring": (
        "评分引擎目录。",
        "封装混合评分模型与评分报告数据结构，为 resume_score 工具服务。",
        "评分维度或模型策略变化时，需同步产品评分文档。",
    ),
    "src/services": (
        "领域服务目录。",
        "提供 JD 分析、简历解析、patch 生成、导出等纯服务能力。",
        "服务职责应保持单一，避免和 runtime/CRUD 交叉。",
    ),
    "src/tools": (
        "工具命名空间占位目录。",
        "当前真实工具注册集中在 src/agent/tools.py，这里只保留包边界。",
        "若把工具拆回此目录，先更新架构文档再迁代码。",
    ),
    "tests": (
        "测试总目录。",
        "围绕当前 session/message 架构组织验收与文档守卫测试。",
        "新测试要先写明覆盖哪一层，避免回到按阶段堆脚本的旧习惯。",
    ),
    "tests/acceptance": (
        "现行验收测试目录。",
        "覆盖 runtime、HTTP API 和稳定回归场景，是 demo 可信度基线。",
        "行为变化后必须先补这里，再谈文档更新完成。",
    ),
    "tests/e2e": (
        "端到端测试预留目录。",
        "当前仓库未放入现行 E2E 用例，但保留作为后续扩展位。",
        "新增 E2E 时，需说明它与 acceptance 的边界。",
    ),
    "tests/integration": (
        "集成测试预留目录。",
        "当前为空，用于未来补充跨模块组合验证。",
        "目录被激活时，先补 README 里的边界定义再放测试。",
    ),
    "tests/unit": (
        "单元测试目录。",
        "用于放置工程守卫和小粒度模块验证。",
        "单测职责变化后，要同步 tests/README 的测试分层说明。",
    ),
}

DIR_EXTRA_SECTIONS: dict[str, str] = {
    "docs": """## 当前主文档

- `README.md`：文档体系总索引与活文档入口。
- `项目运行说明.md`：本地运行、API 样例和产物路径。
- `DEPLOYMENT.md`：部署路径与线上落地约束。

## 非主线资料

- `reference/`：仍有参考价值的评测资料。
- `archive/`：历史分析、旧阶段计划和已退役方案。
""",
    "docs/product": """## 当前主文档

- `MVP_PRD_Resume_Fit_Agent.md`：当前 demo 的产品范围、对象模型与主流程。
- `UI交互设计.md`：当前 React 工作台的交互原则与面板协作方式。
- `评分系统设计_v2_混合评分_校招版_v2.1.md`：评分子系统规则与实现约束。
- `jd-隐含要求推断-prompt.md`：JD 隐含要求提取的专项提示词参考。
""",
    "docs/technical": """## 当前主文档

- `ARCHITECTURE.md`：当前可运行 demo 的真实架构与部署边界。
""",
    "tests": """## 测试分层

- `acceptance/`：当前必须稳定通过的主链回归。
- `unit/`：工程守卫与小粒度验证。
- `e2e/`、`integration/`：预留目录，当前未承载主线用例。
""",
}

FILE_META_OVERRIDES: dict[str, tuple[str, str, str, str, str]] = {
    "Dockerfile": (
        "Python 基础镜像、仓库源码和启动命令。",
        "提供可构建的后端容器镜像。",
        "根目录部署文件。",
        "容器部署",
        "定义容器化部署所需的镜像构建流程。",
    ),
    "README.md": (
        "当前仓库结构、现行运行链路与核心工程约束。",
        "输出仓库级全局地图、主文档入口和维护规则。",
        "根目录总地图，是整个分形文档体系的第一层。",
        "全局地图",
        "解释整个仓库当前到底是什么、怎么跑、怎么维护。",
    ),
    "pyproject.toml": (
        "Python 包元数据、依赖和测试工具配置。",
        "提供后端安装、脚本入口和开发工具配置。",
        "根目录 Python 构建清单。",
        "构建清单",
        "约束 Python 包安装、测试和格式化入口。",
    ),
    "render.yaml": (
        "Render 平台环境变量、持久化磁盘与仓库源码。",
        "提供当前后端服务在 Render 的部署配置。",
        "根目录部署文件。",
        "云部署配置",
        "定义 Render 上的后端部署方式。",
    ),
    "start.sh": (
        "本地 shell 环境、前后端端口与虚拟环境状态。",
        "一键启动前后端并初始化数据库。",
        "根目录本地启动入口。",
        "启动脚本",
        "让 demo 在本地以最少步骤跑起来。",
    ),
    "config/default.yaml": (
        "启动脚本、后端服务和本地开发环境读取默认参数。",
        "提供数据库、日志和 CLI 的默认配置值。",
        "系统配置基线文件。",
        "默认配置",
        "定义本地开发的基础参数，不处理业务逻辑。",
    ),
    "frontend/.env.production": (
        "Vite 构建流程和部署平台读取前端环境变量。",
        "提供生产环境 API 基地址。",
        "前端生产环境变量样例。",
        "环境配置",
        "约束前端构建时连接哪个后端地址。",
    ),
    "frontend/index.html": (
        "Vite 构建链路和浏览器入口读取页面骨架。",
        "提供 React 挂载点与基础 HTML 模板。",
        "前端 HTML 外壳。",
        "入口模板",
        "承载前端首屏 HTML 容器。",
    ),
    "frontend/package.json": (
        "npm、Vite 和部署平台读取脚本与依赖声明。",
        "提供前端依赖与构建命令。",
        "前端构建清单。",
        "构建清单",
        "定义前端依赖与构建脚本。",
    ),
    "frontend/src/App.tsx": (
        "浏览器事件、API 客户端和各子面板组件。",
        "输出统一的工作台状态编排与页面布局。",
        "React 前端总控组件。",
        "前端总控",
        "负责会话恢复、请求流转和面板组合。",
    ),
    "frontend/src/api/client.ts": (
        "前端组件调用的请求参数与浏览器 fetch。",
        "输出统一的后端 API 调用函数。",
        "前端 API 适配层。",
        "接口适配",
        "把前端请求收口到可复用的 HTTP 调用函数。",
    ),
    "frontend/src/main.tsx": (
        "Vite 入口与 App 组件。",
        "把 React 应用挂载到浏览器 DOM。",
        "前端启动入口。",
        "启动入口",
        "完成 React 应用初始化。",
    ),
    "frontend/src/styles.css": (
        "App 和各业务面板共享的样式类。",
        "输出工作台的全局样式规则。",
        "前端全局样式文件。",
        "样式基线",
        "定义工作台公共布局与视觉样式。",
    ),
    "frontend/src/types.ts": (
        "后端响应结构和前端状态模型。",
        "输出 React 侧复用的 TypeScript 类型。",
        "前端共享类型文件。",
        "类型中心",
        "约束前端状态和接口数据结构。",
    ),
    "frontend/src/vite-env.d.ts": (
        "Vite 环境变量与 TypeScript 编译器。",
        "补充前端构建时的类型声明。",
        "前端构建类型补丁。",
        "构建类型",
        "让 Vite 环境变量在 TS 中可见。",
    ),
    "scripts/bootstrap.sh": (
        "开发者手动执行和本地环境初始化流程。",
        "搭建基础开发环境。",
        "环境初始化脚本。",
        "初始化脚本",
        "帮助本地快速准备开发依赖。",
    ),
    "scripts/dev.sh": (
        "本地开发者与 shell 环境。",
        "启动开发态工作流。",
        "开发辅助脚本。",
        "开发脚本",
        "收口常用本地开发命令。",
    ),
    "scripts/fault_drill.sh": (
        "开发者手动演练与故障验证场景。",
        "触发预设故障演练流程。",
        "故障演练脚本。",
        "演练脚本",
        "验证异常场景与恢复路径。",
    ),
    "scripts/fractal_docs.py": (
        "仓库结构、目录元信息和文件元信息覆盖表。",
        "生成或校验目录 README 与文件头部声明。",
        "分形文档体系的同步器与守门脚本。",
        "文档守门脚本",
        "批量维护目录地图和文件头部契约。",
    ),
    "scripts/generate_evaluation_dataset.py": (
        "评测样本模板与生成参数。",
        "生成评测数据集文件。",
        "评测数据生成脚本。",
        "评测脚本",
        "构造评分/润色评测所需的数据集。",
    ),
    "scripts/generate_realistic_dataset.py": (
        "真实化样本模板与生成参数。",
        "输出更贴近真实投递场景的数据集。",
        "评测数据增强脚本。",
        "评测脚本",
        "扩展更真实的评测输入样本。",
    ),
    "scripts/run_evaluation.py": (
        "评测数据集、评分器与报告模板。",
        "运行评测并生成结果报告。",
        "评测执行入口。",
        "评测入口",
        "收口评测运行和结果汇总。",
    ),
    "scripts/run_regression.sh": (
        "pytest 与本地回归命令。",
        "执行仓库回归检查。",
        "回归脚本。",
        "回归脚本",
        "统一触发关键回归场景。",
    ),
    "scripts/test.sh": (
        "开发者本地测试命令。",
        "执行默认测试集合。",
        "测试快捷脚本。",
        "测试脚本",
        "降低日常测试执行成本。",
    ),
    "scripts/test_direct_score.py": (
        "评分引擎与样例 JD/简历文本。",
        "直接验证评分器输出。",
        "评分专项测试脚本。",
        "专项验证",
        "验证评分引擎在脚本场景下的输出。",
    ),
    "scripts/test_polish_all.py": (
        "润色服务与多份测试样本。",
        "批量验证润色流程。",
        "润色专项测试脚本。",
        "专项验证",
        "覆盖多样本的润色结果检查。",
    ),
    "scripts/test_skills_integration.py": (
        "技能脚本与评测样本。",
        "验证技能内容与主仓库评测的一致性。",
        "技能集成测试脚本。",
        "专项验证",
        "检查技能实现与主仓库逻辑是否对齐。",
    ),
    "scripts/test_stage0.sh": (
        "旧阶段脚本兼容需求与 shell 环境。",
        "保留最基础的历史启动验证。",
        "历史基线脚本。",
        "兼容脚本",
        "保留早期阶段的最小环境检查。",
    ),
    "src/__init__.py": (
        "安装器与上层模块导入。",
        "声明 src 包边界。",
        "仓库源码包根。",
        "包声明",
        "提供源码包的最外层命名空间。",
    ),
    "src/agent/__init__.py": (
        "上层 API/CLI 对 agent 包的导入。",
        "导出当前主运行时对象。",
        "Agent 包导出入口。",
        "包导出",
        "把核心运行时暴露给 API 和 CLI。",
    ),
    "src/agent/memory.py": (
        "SQLite CRUD、对话压缩器、项目目录结构和文件系统。",
        "输出项目快照、结构化记忆读写和产物管理能力。",
        "Agent 的长期记忆与资产中枢。",
        "记忆中枢",
        "维护 profile、experiences、tracks、JD 和 artifacts。",
    ),
    "src/agent/models.py": (
        "planner、runtime、tool registry 共享的数据结构。",
        "输出会话级决策、附件、计划步骤和工具执行模型。",
        "Agent 内部协议类型中心。",
        "类型中心",
        "统一 runtime、planner 和 tools 之间的数据协议。",
    ),
    "src/agent/planner.py": (
        "用户消息、附件和 memory snapshot。",
        "输出当前轮的 intent decision 与 plan steps。",
        "会话式 Agent 的轻量规划器。",
        "规划器",
        "决定本轮是补信息、入库、评分、生成还是润色。",
    ),
    "src/agent/runtime.py": (
        "planner、memory、tool registry 和持久化 CRUD。",
        "输出会话创建、消息处理、快照与 trace 结果。",
        "服务端 think-call-observe 主运行时。",
        "运行时核心",
        "驱动消息主链并把结果回给前端或 CLI。",
    ),
    "src/agent/tools.py": (
        "memory、评分器、分析器、解析器、导出器和 patcher。",
        "输出可被 runtime 调用的内置工具目录与执行结果。",
        "当前系统的工具注册表。",
        "工具注册表",
        "把领域能力封装成 runtime 可调用的稳定工具。",
    ),
    "src/api/__init__.py": (
        "HTTP 服务导入与应用装配。",
        "声明 API 包边界。",
        "FastAPI 包导出入口。",
        "包声明",
        "保持 API 包可被应用服务器导入。",
    ),
    "src/api/main.py": (
        "FastAPI、runtime、上传解析器与 pydantic 请求模型。",
        "输出 session/message API、管理端点和上传端点。",
        "后端 HTTP 入口主文件。",
        "HTTP 入口",
        "承接前端请求并转发到 runtime 与 memory。",
    ),
    "src/cli/__init__.py": (
        "命令行入口导入。",
        "声明 CLI 包边界。",
        "CLI 包导出入口。",
        "包声明",
        "保持 CLI 模块可被 setuptools 命令发现。",
    ),
    "src/cli/main.py": (
        "click、runtime 和数据库初始化能力。",
        "输出命令行子命令与本地调试入口。",
        "仓库 CLI 主入口。",
        "CLI 入口",
        "为本地启动和会话调试提供命令接口。",
    ),
    "src/db/__init__.py": (
        "数据库子模块导入。",
        "声明持久化包边界。",
        "数据库包导出入口。",
        "包声明",
        "保持 db 包命名空间稳定。",
    ),
    "src/db/agent_crud.py": (
        "数据库连接、表模型和 JSON 序列化辅助函数。",
        "输出 agent 运行时相关表的 CRUD 仓储。",
        "Agent 持久化仓储层。",
        "持久化仓储",
        "服务 sessions、messages、tracks、artifacts 等核心对象。",
    ),
    "src/db/crud.py": (
        "数据库连接、项目表和 JD 表。",
        "输出项目与 JD 的基础 CRUD 能力。",
        "项目级基础仓储层。",
        "持久化仓储",
        "管理 project 与 project_jd_entries 等基础实体。",
    ),
    "src/db/database.py": (
        "SQLite 路径配置与 schema 初始化 SQL。",
        "输出数据库连接和初始化函数。",
        "SQLite 连接与建表入口。",
        "数据库入口",
        "保证持久化目录和表结构随服务启动可用。",
    ),
    "src/db/models.py": (
        "SQLite 表结构对应的 dataclass 模型。",
        "输出项目、会话、JD、轨迹和产物实体类型。",
        "数据库实体定义文件。",
        "实体模型",
        "承接 CRUD 返回值和类型约束。",
    ),
    "src/observability/__init__.py": (
        "上层模块对观测子模块的导入。",
        "导出当前对话压缩管理器。",
        "观测包导出入口。",
        "包导出",
        "把 observability 能力暴露给 memory。",
    ),
    "src/observability/dialog.py": (
        "项目目录、消息历史和 JSON 文件存储。",
        "输出长对话压缩、摘要恢复和消息落盘能力。",
        "对话观测与压缩模块。",
        "观测核心",
        "在长会话场景下控制上下文体积并保留摘要。",
    ),
    "src/scoring/__init__.py": (
        "上层工具对评分器的导入。",
        "导出当前校园招聘评分器与相关模型。",
        "评分包导出入口。",
        "包导出",
        "为 runtime 工具暴露评分子系统主类。",
    ),
    "src/scoring/campus_scorer.py": (
        "JD、简历文本和可选 LLM 客户端。",
        "输出硬软结合的评分报告对象。",
        "当前 resume_score 工具背后的评分引擎。",
        "评分引擎",
        "把规则分与软性能力分合成为匹配度报告。",
    ),
    "src/scoring/models.py": (
        "评分器内部的维度定义和报告结构。",
        "输出评分报告、硬指标、软指标等数据模型。",
        "评分子系统类型文件。",
        "类型中心",
        "约束评分结果的结构化输出。",
    ),
    "src/services/__init__.py": (
        "上层运行时对领域服务的导入。",
        "声明 services 包边界。",
        "领域服务包导出入口。",
        "包声明",
        "保持领域服务的包命名空间稳定。",
    ),
    "src/services/analyzer.py": (
        "JD 文本、简历文本和关键词提取规则。",
        "输出优势、缺口与行动建议分析结果。",
        "非评分型 JD/简历分析服务。",
        "分析服务",
        "为评分补充可解释的优势与缺口描述。",
    ),
    "src/services/exporter.py": (
        "结构化简历 block JSON。",
        "输出 markdown 形式的简历文本。",
        "简历导出服务。",
        "导出服务",
        "把结构化编辑结果转成可落盘文本。",
    ),
    "src/services/patcher.py": (
        "简历 block、JD 文本和缺口提示。",
        "输出可应用的 block 级 patch 候选。",
        "简历润色 patch 生成服务。",
        "润色服务",
        "在不重写整份简历的前提下生成局部改写建议。",
    ),
    "src/services/resume_parser.py": (
        "原始简历文本和 block patch 请求。",
        "输出可编辑 block JSON 并支持回写 patch。",
        "简历结构化解析服务。",
        "解析服务",
        "把原始文本拆成可定位、可修改的 block。",
    ),
    "src/tools/__init__.py": (
        "历史工具命名空间导入。",
        "声明 tools 包边界。",
        "历史工具包占位入口。",
        "包占位",
        "保留工具命名空间，当前真实注册在 src/agent/tools.py。",
    ),
    "tests/__init__.py": (
        "pytest 测试发现机制。",
        "声明 tests 包边界。",
        "测试包导出入口。",
        "包声明",
        "保持测试目录可被 Python 识别。",
    ),
    "tests/acceptance/test_agent_api.py": (
        "FastAPI 应用、测试客户端和 SQLite 重置环境。",
        "验证 HTTP API 端到端行为。",
        "现行 API 验收测试。",
        "验收测试",
        "覆盖会话、上传、管理端点和产物链路。",
    ),
    "tests/acceptance/test_agent_runtime.py": (
        "runtime、SQLite 环境和文件产物目录。",
        "验证 think-call-observe 主链能完整跑通。",
        "现行运行时验收测试。",
        "验收测试",
        "确保 ingest/score/generate/polish 主流程可用。",
    ),
    "tests/acceptance/test_regression_suite.py": (
        "runtime、SQLite 环境和稳定场景样本。",
        "验证背景捕获、JD 入库、评分生成和轨道管理回归。",
        "主链回归验收测试。",
        "回归测试",
        "把容易回退的关键行为钉在当前架构上。",
    ),
    "tests/conftest.py": (
        "pytest 会话级共享配置。",
        "输出测试通用 fixture 与环境准备逻辑。",
        "测试全局配置文件。",
        "测试配置",
        "集中放置 pytest 共享配置。",
    ),
    "tests/unit/test_fractal_docs.py": (
        "分形文档脚本与仓库结构约束。",
        "验证目录 README 与文件头注释未失配。",
        "文档守卫单元测试。",
        "工程守卫",
        "把分形文档规则纳入自动检查。",
    ),
}

ROOT_README_RULE = "任何功能、架构、写法更新，都必须在工作结束后同步更新相关目录的子文档和文件头注释。"


def is_excluded_dir(path: Path) -> bool:
    return any(part in EXCLUDED_DIR_NAMES for part in path.parts)


def is_excluded_file(path: Path) -> bool:
    return path.name in EXCLUDED_FILE_NAMES


def managed_directories() -> list[Path]:
    result: list[Path] = []
    for root_name in MANAGED_ROOTS:
        root_path = ROOT / root_name
        if not root_path.exists():
            continue
        for path in [root_path, *sorted(root_path.rglob("*"))]:
            if not path.is_dir():
                continue
            if is_excluded_dir(path.relative_to(ROOT)):
                continue
            result.append(path)
    dedup = sorted({path for path in result}, key=lambda item: item.relative_to(ROOT).as_posix())
    return dedup


def managed_files() -> list[Path]:
    files: list[Path] = []
    for root_file in ROOT_MANAGED_FILES:
        path = ROOT / root_file
        if path.exists():
            files.append(path)
    for root_name in MANAGED_ROOTS:
        root_path = ROOT / root_name
        if not root_path.exists():
            continue
        for path in sorted(root_path.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(ROOT)
            if is_excluded_dir(rel.parent):
                continue
            if is_excluded_file(rel):
                continue
            files.append(path)
    return files


def comment_style(rel_path: str) -> str | None:
    path = Path(rel_path)
    if path.name == "Dockerfile":
        return "hash"
    if path.name in {"package.json", "vercel.json"}:
        return None
    if path.suffix in NON_COMMENTABLE_SUFFIXES:
        return None
    if path.suffix in {".py", ".sh", ".yaml", ".yml", ".toml"} or path.name.startswith(".env"):
        return "hash"
    if path.suffix in {".ts", ".tsx", ".js", ".jsx"} or path.name.endswith(".d.ts"):
        return "slash"
    if path.suffix == ".css":
        return "css"
    if path.suffix in {".md", ".html"}:
        return "html"
    if path.suffix == ".txt":
        return None
    return None


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def first_markdown_heading(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return ""


def generic_file_meta(rel_path: str) -> tuple[str, str, str, str, str]:
    path = Path(rel_path)
    title = first_markdown_heading(read_text(ROOT / rel_path)) if path.suffix == ".md" else path.stem

    if path.name == "README.md":
        dir_name = path.parent.as_posix() or "."
        return (
            f"{dir_name} 目录结构、子目录边界和文件职责清单。",
            "输出当前目录的极简架构说明与成员地图。",
            f"{dir_name} 的目录说明文件。",
            "目录地图",
            "解释当前目录下有哪些成员以及它们各自做什么。",
        )

    if rel_path.startswith("docs/product/"):
        return (
            "当前产品范围、交互约束与实现边界。",
            f"输出产品文档《{title or path.name}》的说明内容。",
            "产品设计文档。",
            "产品文档",
            "沉淀当前产品范围、规则或设计说明。",
        )

    if rel_path.startswith("docs/technical/"):
        return (
            "当前技术架构、模块边界与工程约束。",
            f"输出技术文档《{title or path.name}》的说明内容。",
            "技术设计文档。",
            "技术文档",
            "解释当前实现、约束或工程机制。",
        )

    if rel_path.startswith("docs/archive/") or rel_path.startswith("docs/reference/") or rel_path.startswith(
        "docs/product/archive/"
    ) or rel_path.startswith("docs/technical/archive/"):
        return (
            "历史设计、专项分析或参考资料。",
            f"保留《{title or path.name}》作为参考或归档材料。",
            "历史或参考文档。",
            "参考文档",
            "保留曾经的讨论、分析或评测沉淀。",
        )

    if rel_path.startswith("docs/"):
        return (
            "当前系统边界、运行方式与文档索引。",
            f"输出文档《{title or path.name}》的说明内容。",
            "仓库级说明文档。",
            "说明文档",
            "为当前 demo 提供运行、部署或索引说明。",
        )

    if rel_path.startswith("frontend/src/components/"):
        nice = path.stem.replace("Panel", " 面板").replace("Board", " 看板")
        return (
            "App 传入的状态、回调函数和后端返回数据。",
            f"输出 {nice} 的 React 展示与交互片段。",
            "前端业务面板组件。",
            "业务组件",
            "承担工作台中的一个具体面板或看板。",
        )

    if rel_path.startswith("frontend/src/"):
        return (
            "前端状态、类型或构建上下文。",
            f"输出 {path.name} 对应的前端模块能力。",
            "前端源码文件。",
            "前端模块",
            "服务 React 工作台的数据流或展示逻辑。",
        )

    if rel_path.startswith("scripts/"):
        return (
            "本地 shell/python 环境与工程命令参数。",
            f"输出脚本 {path.name} 对应的工程辅助能力。",
            "工程脚本文件。",
            "工程脚本",
            "服务启动、评测、回归或检查流程。",
        )

    if rel_path.startswith("tests/acceptance/"):
        return (
            "运行时、HTTP API 和 SQLite 测试环境。",
            f"输出 {path.name} 对当前主链的验收断言。",
            "验收测试文件。",
            "验收测试",
            "验证当前会话式 demo 的关键行为。",
        )

    if rel_path.startswith("tests/unit/"):
        return (
            "工程约束或小粒度模块接口。",
            f"输出 {path.name} 对局部规则的单元断言。",
            "单元测试文件。",
            "单元测试",
            "守住局部模块或工程规则。",
        )

    if rel_path.startswith("tests/"):
        return (
            "测试上下文与共享 fixture。",
            f"输出 {path.name} 对测试体系的支持能力。",
            "测试支持文件。",
            "测试支持",
            "服务测试发现、配置或局部验证。",
        )

    if rel_path.startswith("src/"):
        return (
            "当前后端子模块与同层共享协议。",
            f"输出 {path.name} 对应的模块能力。",
            "后端源码文件。",
            "后端模块",
            "服务 session/message demo 的一块实现。",
        )

    return (
        "上游调用方与同目录文件。",
        f"输出 {path.name} 对应的文本化或代码能力。",
        "仓库受管文件。",
        "受管文件",
        "纳入分形文档系统的可维护文件。",
    )


def file_meta(rel_path: str) -> tuple[str, str, str, str, str]:
    return FILE_META_OVERRIDES.get(rel_path, generic_file_meta(rel_path))


def render_header(rel_path: str) -> str | None:
    style = comment_style(rel_path)
    if style is None:
        return None
    input_text, output_text, pos_text, _, _ = file_meta(rel_path)
    lines = [
        f"Input: {input_text}",
        f"Output: {output_text}",
        f"Pos: {pos_text}",
        "Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。",
    ]
    if style == "hash":
        return "".join(f"# {line}\n" for line in lines)
    if style == "slash":
        return "".join(f"// {line}\n" for line in lines)
    if style == "css":
        return "/*\n" + "\n".join(lines) + "\n*/\n"
    if style == "html":
        return "<!--\n" + "\n".join(lines) + "\n-->\n"
    return None


def strip_existing_header(text: str, rel_path: str) -> str:
    style = comment_style(rel_path)
    if style in {"hash", "slash"}:
        shebang = ""
        body = text
        if body.startswith("#!"):
            first_newline = body.find("\n")
            shebang = body[: first_newline + 1]
            body = body[first_newline + 1 :]
        prefix = "#" if style == "hash" else "//"
        lines = body.splitlines(keepends=True)
        if len(lines) >= 4 and all(lines[index].startswith(f"{prefix} ") for index in range(4)):
            normalized = "".join(lines[:4])
            if "Input:" in normalized and "Rule:" in normalized:
                body = "".join(lines[4:])
        return shebang + body

    if style == "css":
        return re.sub(r"^/\*\nInput:.*?Rule:.*?\n\*/\n?", "", text, count=1, flags=re.S)

    if style == "html":
        return re.sub(r"^<!--\nInput:.*?Rule:.*?\n-->\n?", "", text, count=1, flags=re.S)

    return text


def expected_file_content(path: Path) -> str:
    rel_path = path.relative_to(ROOT).as_posix()
    header = render_header(rel_path)
    original = read_text(path)
    body = strip_existing_header(original, rel_path)
    shebang = ""
    if body.startswith("#!"):
        first_newline = body.find("\n")
        shebang = body[: first_newline + 1]
        body = body[first_newline + 1 :]
    if not header:
        return original
    return shebang + header + body.lstrip("\ufeff")


def should_manage_file_header(path: Path) -> bool:
    rel_path = path.relative_to(ROOT).as_posix()
    if path.name == "README.md" and path.parent != ROOT:
        return False
    return render_header(rel_path) is not None


def immediate_children(dir_path: Path) -> tuple[list[Path], list[Path]]:
    files: list[Path] = []
    dirs: list[Path] = []
    for child in sorted(dir_path.iterdir(), key=lambda item: item.name):
        rel = child.relative_to(ROOT)
        if child.is_dir():
            if is_excluded_dir(rel):
                continue
            dirs.append(child)
        elif child.is_file():
            if is_excluded_file(rel):
                continue
            files.append(child)
    return files, dirs


def dir_meta(rel_dir: str) -> tuple[str, str, str]:
    return DIR_META.get(
        rel_dir,
        (
            "当前目录承载一组同边界的文件。",
            "这里的文件应该围绕一个明确职责聚合，避免跨层混放。",
            "目录成员变化后，先更新此页，再更新上一级目录说明。",
        ),
    )


def inventory_row_for_file(path: Path) -> tuple[str, str, str]:
    rel_path = path.relative_to(ROOT).as_posix()
    _, _, _, role, function = file_meta(rel_path)
    return path.name, role, function


def inventory_row_for_dir(path: Path) -> tuple[str, str, str]:
    rel_dir = path.relative_to(ROOT).as_posix()
    summary = dir_meta(rel_dir)
    return path.name, "子模块目录", summary[0]


def render_directory_readme(dir_path: Path) -> str:
    rel_dir = dir_path.relative_to(ROOT).as_posix()
    summary = dir_meta(rel_dir)
    files, dirs = immediate_children(dir_path)
    if not any(file_path.name == "README.md" for file_path in files):
        files = [dir_path / "README.md", *files]
    else:
        files = sorted(files, key=lambda item: (item.name != "README.md", item.name))

    lines = [
        f"# {rel_dir}",
        "",
        f"- 定位：{summary[0]}",
        f"- 边界：{summary[1]}",
        f"- 维护：{summary[2]}",
        "",
    ]

    extra = DIR_EXTRA_SECTIONS.get(rel_dir)
    if extra:
        lines.extend([extra.rstrip(), ""])

    lines.extend(
        [
            "## 文件清单",
            "",
            "| 文件 | 地位 | 功能 |",
            "| --- | --- | --- |",
        ]
    )
    for file_path in files:
        name, role, function = inventory_row_for_file(file_path)
        lines.append(f"| `{name}` | {role} | {function} |")
    if not files:
        lines.append("| `（空）` | 预留位 | 当前目录还没有直接文件。 |")
    lines.append("")

    lines.extend(
        [
            "## 子目录",
            "",
            "| 子目录 | 地位 | 功能 |",
            "| --- | --- | --- |",
        ]
    )
    for child_dir in dirs:
        name, role, function = inventory_row_for_dir(child_dir)
        lines.append(f"| `{name}` | {role} | {function} |")
    if not dirs:
        lines.append("| `（空）` | 叶子目录 | 当前目录没有下一级目录。 |")
    lines.append("")
    readme_rel = (dir_path / "README.md").relative_to(ROOT).as_posix()
    header = render_header(readme_rel) or ""
    return header + "\n".join(lines)


def expected_readme_path(dir_path: Path) -> Path:
    return dir_path / "README.md"


def ensure_root_readme_rule() -> list[str]:
    root_readme = ROOT / "README.md"
    if not root_readme.exists():
        return ["Missing root README.md"]
    text = read_text(root_readme)
    if ROOT_README_RULE not in text:
        return ["Root README.md is missing the global maintenance rule"]
    return []


def write_mode() -> int:
    for directory in managed_directories():
        readme_path = expected_readme_path(directory)
        readme_path.write_text(render_directory_readme(directory), encoding="utf-8")

    for file_path in managed_files():
        if not should_manage_file_header(file_path):
            continue
        file_path.write_text(expected_file_content(file_path), encoding="utf-8")
    return 0


def check_mode() -> int:
    failures: list[str] = []
    failures.extend(ensure_root_readme_rule())

    for directory in managed_directories():
        readme_path = expected_readme_path(directory)
        expected = render_directory_readme(directory)
        if not readme_path.exists():
            failures.append(f"Missing README: {readme_path.relative_to(ROOT).as_posix()}")
            continue
        actual = read_text(readme_path)
        if actual != expected:
            failures.append(f"Outdated README: {readme_path.relative_to(ROOT).as_posix()}")

    for file_path in managed_files():
        if not should_manage_file_header(file_path):
            continue
        expected = expected_file_content(file_path)
        actual = read_text(file_path)
        if actual != expected:
            failures.append(f"Outdated header: {file_path.relative_to(ROOT).as_posix()}")

    if failures:
        for item in failures:
            print(item)
        return 1
    print("fractal docs check passed")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync or check fractal documentation files.")
    parser.add_argument("--check", action="store_true", help="Only check whether docs are up to date.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return check_mode() if args.check else write_mode()


if __name__ == "__main__":
    sys.exit(main())
