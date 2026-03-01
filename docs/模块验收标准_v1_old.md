# 模块验收标准

本文档定义每个模块的详细验收标准，包括：
- 功能要求
- 接口定义
- 测试用例
- 验收命令

---

## Stage 0: 环境准备

### 验收标准

| 检查项 | 命令 | 预期结果 |
|---|---|---|
| 项目结构存在 | `ls -la src/` | 包含 db/, routes/, tools/, cli/, models/ 目录 |
| 依赖安装成功 | `python -c "import pydantic, click, sqlite3"` | 无报错 |
| 测试可运行 | `pytest --collect-only` | 收集到 0 个测试（无报错） |

### 验收脚本

```bash
#!/bin/bash
# test_stage0.sh

echo "=== Stage 0 验收 ==="

echo "1. 检查项目结构..."
ls src/db src/routes src/tools src/cli 2>/dev/null || exit 1

echo "2. 检查依赖安装..."
python -c "import pydantic, click, sqlite3" || exit 1

echo "3. 检查测试框架..."
pytest --collect-only >/dev/null 2>&1 || exit 1

echo "✓ Stage 0 验收通过"
```

---

## Stage 1: 数据层 + 最小 CLI

### M0: 工程脚手架

#### 功能要求
1. 项目目录结构完整
2. 配置文件正确
3. 日志系统可用
4. 错误处理机制

#### 验收标准

| 检查项 | 命令 | 预期结果 |
|---|---|---|
| 配置文件 | `cat config/default.yaml` | 包含 database, logging 配置 |
| 日志输出 | `python -m src.cli.main --help 2>&1 \| grep "resume-agent"` | 显示帮助信息 |
| 错误处理 | `python -m src.cli.main --invalid-arg` | 返回错误码 1 |

#### 验收测试

```python
# tests/acceptance/test_m0.py
def test_project_structure():
    """测试项目结构完整"""
    from pathlib import Path
    dirs = ["src/db", "src/routes", "src/tools", "src/cli"]
    for d in dirs:
        assert Path(d).exists(), f"目录 {d} 不存在"

def test_config_exists():
    """测试配置文件存在"""
    from pathlib import Path
    assert Path("config/default.yaml").exists()

def test_logging():
    """测试日志系统"""
    import logging
    logger = logging.getLogger("resume_agent")
    logger.info("test message")
    # 不应该抛出异常
```

---

### M1: SQLite + 本地文件持久化

#### 功能要求
1. 数据库表创建
2. Project CRUD 操作
3. ProjectJDEntry CRUD 操作
4. 版本可恢复（基础）

#### 接口定义

```python
# src/db/models.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Project:
    id: str
    name: str
    cycle: str
    created_at: datetime
    base_resume_path: Optional[str] = None

@dataclass
class ProjectJDEntry:
    id: str
    project_id: str
    raw_content: str
    source_file: str
    created_at: datetime

# src/db/crud.py
class ProjectCRUD:
    def create(self, name: str, cycle: str = "") -> Project
    def get(self, id: str) -> Optional[Project]
    def list_all(self) -> list[Project]
    def update(self, id: str, **kwargs) -> Project
    def delete(self, id: str) -> bool

class ProjectJDEntryCRUD:
    def create(self, project_id: str, content: str, source_file: str) -> ProjectJDEntry
    def get(self, id: str) -> Optional[ProjectJDEntry]
    def list_by_project(self, project_id: str) -> list[ProjectJDEntry]
    def delete(self, id: str) -> bool
```

#### 验收标准

> **设计决策**: 采用"名称即 ID"的简化方案，项目 ID 等于项目名称。

| 检查项 | 命令 | 预期结果 |
|---|---|---|
| 创建项目 | `resume-agent project init --name test` | 输出"项目已创建: test"，数据落盘 |
| 创建带cycle | `resume-agent project init --name test --cycle "2024春招"` | 输出"项目已创建: test (2024春招)" |
| 查询项目 | `resume-agent project get --name test` | 显示项目信息 |
| 列出项目 | `resume-agent project list` | 显示所有项目 |
| 数据库文件 | `ls data/db/` | 存在 resume_agent.db |
| 删除项目 | `resume-agent project delete --name test` | 返回成功 |

#### 验收测试

```python
# tests/acceptance/test_m1.py
import pytest
from src.db.crud import ProjectCRUD, ProjectJDEntryCRUD
from src.db.models import Project

def test_create_project():
    """测试创建项目"""
    crud = ProjectCRUD()
    project = crud.create(name="test-project")
    assert project.id is not None
    assert project.name == "test-project"

def test_get_project():
    """测试查询项目"""
    crud = ProjectCRUD()
    project = crud.create(name="test-project")
    retrieved = crud.get(project.id)
    assert retrieved is not None
    assert retrieved.id == project.id

def test_list_projects():
    """测试列出项目"""
    crud = ProjectCRUD()
    crud.create(name="project-1")
    crud.create(name="project-2")
    projects = crud.list_all()
    assert len(projects) >= 2

def test_create_jd_entry():
    """测试创建 JD 条目"""
    crud = ProjectCRUD()
    project = crud.create(name="test-project", cycle="")

    jd_crud = ProjectJDEntryCRUD()
    jd_entry = jd_crud.create(
        project_id=project.id,
        content="JD content here",
        source_file="test.txt"
    )
    assert jd_entry.id is not None
    assert jd_entry.project_id == project.id

def test_persistence():
    """测试数据持久化"""
    crud = ProjectCRUD()
    project = crud.create(name="persist-test")

    # 新建 CRUD 实例，模拟重启
    crud2 = ProjectCRUD()
    retrieved = crud2.get(project.id)
    assert retrieved is not None
    assert retrieved.name == "persist-test"
```

---

### M1.5: 最小 CLI

#### 功能要求
1. `project init` 命令
2. `project list` 命令
3. `project get` 命令
4. `project delete` 命令

#### 接口定义

```bash
# 命令行接口
resume-agent project init --name <name> [--cycle <cycle>]
resume-agent project list [--format json|table]
resume-agent project get --name <name> [--format json|table]
resume-agent project delete --name <name>
```

#### 验收标准

| 场景 | 命令 | 预期输出 |
|---|---|---|
| 创建项目 | `resume-agent project init --name myproject` | `✓ Project created: myproject` |
| 创建带cycle | `resume-agent project init --name myproject --cycle "2024春招"` | `✓ Project created: myproject (2024春招)` |
| 列出项目 | `resume-agent project list` | 表格显示所有项目 |
| 列出JSON | `resume-agent project list --format json` | JSON 数组 |
| 查询项目 | `resume-agent project get --name myproject` | 显示项目详情 |
| 删除项目 | `resume-agent project delete --name myproject` | `✓ 项目已删除: myproject` |
| 重复创建 | `resume-agent project init --name dupetest` (第二次) | `✗ 项目已存在: dupetest` |
| 查询不存在 | `resume-agent project get --name nonexistent` | `✗ 项目不存在: nonexistent` |

#### 验收脚本

```bash
#!/bin/bash
# test_m1_5.sh

set -e

echo "=== M1.5 CLI 验收 ==="

# 清理环境
rm -rf data/db/

echo "1. 测试创建项目..."
output=$(resume-agent project init --name testproject)
echo "$output" | grep -q "项目已创建" || exit 1

echo "2. 测试列出项目..."
output=$(resume-agent project list)
echo "$output" | grep -q "testproject" || exit 1

echo "3. 测试查询项目..."
output=$(resume-agent project get --name testproject)
echo "$output" | grep -q "testproject" || exit 1

echo "4. 测试 JSON 格式..."
output=$(resume-agent project list --format json)
echo "$output" | python -m json.tool >/dev/null || exit 1

echo "5. 测试删除项目..."
output=$(resume-agent project delete --name testproject)
echo "$output" | grep -q "项目已删除" || exit 1

echo "6. 测试重复创建..."
resume-agent project init --name dupetest 2>/dev/null
resume-agent project init --name dupetest 2>&1 | grep -q "已存在" || exit 1

echo "7. 测试查询不存在..."
resume-agent project get --name nonexistent 2>&1 | grep -q "不存在" || exit 1

echo "✓ M1.5 CLI 验收通过"
```

---

## Stage 2: 工具 Stub + 路由骨架

### M3-stub: Domain Tools Stub

#### 功能要求
1. ScorerStub：返回固定评分
2. AllocatorStub：总是创建新卡片
3. ParserStub：返回假数据

#### 接口定义

```python
# src/tools/stub/scorer_stub.py
class ScorerStub:
    def score(self, jd: str, resume: str) -> ScoreCard:
        return ScoreCard(
            score=50,
            match_level="medium",
            dimensions=[],
            suggestion="建议补充后生成"
        )

# src/tools/stub/allocator_stub.py
class AllocatorStub:
    def allocate(self, jd_entries, existing_cards) -> AllocationPlan:
        # 总是创建新卡片
        return AllocationPlan(
            decisions=[
                AllocationDecision(
                    jd_entry_id=jd.id,
                    action="create_new_card",
                    reason="Stub: 总是创建新卡片"
                )
                for jd in jd_entries
            ]
        )
```

#### 验收标准

| 检查项 | 测试 | 预期结果 |
|---|---|---|
| ScorerStub 可调用 | `scorer = ScorerStub(); scorer.score("jd", "resume")` | 返回 ScoreCard, score=50 |
| AllocatorStub 可调用 | `allocator = AllocatorStub(); allocator.allocate([jd], [])` | 返回创建新卡片的决策 |

#### 验收测试

```python
# tests/acceptance/test_m3_stub.py
def test_scorer_stub():
    from src.tools.stub.scorer_stub import ScorerStub

    scorer = ScorerStub()
    card = scorer.score("jd content", "resume content")

    assert card.score == 50
    assert card.match_level == "medium"
    assert card.suggestion == "建议补充后生成"

def test_allocator_stub():
    from src.tools.stub.allocator_stub import AllocatorStub
    from src.db.models import ProjectJDEntry

    allocator = AllocatorStub()
    jd_entries = [
        ProjectJDEntry(id="jd1", project_id="p1", raw_content="jd", source_file="test.txt")
    ]

    plan = allocator.allocate(jd_entries, [])

    assert len(plan.decisions) == 1
    assert plan.decisions[0].action == "create_new_card"
```

---

### M2: 路由与状态机

#### 功能要求
1. 6 意图分类
2. 5 状态状态机
3. 路由决策逻辑
4. 风险确认机制

#### 接口定义

```python
# src/routes/intent.py
class Intent(Enum):
    INGEST_JD = "ingest_jd"
    UPDATE_RESUME = "update_resume"
    ADD_INFO = "add_info"
    GENERATE = "generate"
    COMPARE = "compare"
    ABANDON = "abandon"

class TaskState(Enum):
    PENDING = "pending"
    SCORED = "scored"
    GENERATING = "generating"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

@dataclass
class RouteDecision:
    state: TaskState
    message: str
    actions: list[str]
    await_risk_ack: bool = False
    mode: Optional[str] = None

# src/routes/router.py
class TaskRouter:
    def route(self, intent: Intent, task_state: TaskState,
              score_card: Optional[ScoreCard] = None) -> RouteDecision
```

#### 验收测试

```python
# tests/acceptance/test_m2.py
def test_ingest_jd_routing():
    """测试 ingest_jd 路由"""
    from src.routes.router import TaskRouter
    from src.routes.intent import Intent, TaskState

    router = TaskRouter()
    decision = router.route(Intent.INGEST_JD, TaskState.PENDING)

    assert decision.state == TaskState.SCORED
    assert "JD" in decision.message

def test_generate_high_match():
    """测试高匹配生成路由"""
    from src.routes.router import TaskRouter
    from src.routes.intent import Intent, TaskState
    from src.models import ScoreCard, MatchLevel

    router = TaskRouter()
    score_card = ScoreCard(score=80, match_level=MatchLevel.HIGH)
    decision = router.route(Intent.GENERATE, TaskState.SCORED, score_card)

    assert decision.state == TaskState.GENERATING
    assert decision.mode == "normal"

def test_generate_low_match():
    """测试低匹配生成路由"""
    from src.routes.router import TaskRouter
    from src.routes.intent import Intent, TaskState
    from src.models import ScoreCard, MatchLevel

    router = TaskRouter()
    score_card = ScoreCard(score=30, match_level=MatchLevel.LOW)
    decision = router.route(Intent.GENERATE, TaskState.SCORED, score_card)

    assert decision.state == TaskState.SCORED
    assert decision.await_risk_ack == True
```

---

## Stage 3-5: 验收标准（占位）

### M3-real: 真实工具实现

待 Stage 2 完成后定义详细验收标准。

### M4: 端到端编排

待 Stage 3 完成后定义详细验收标准。

### M5: 完整 CLI

待 Stage 4 完成后定义详细验收标准。

---

## 通用验收流程

### 1. 开发 Agent 自测

```bash
# 运行单元测试
pytest tests/unit/ -v

# 运行类型检查
mypy src/

# 运行代码格式检查
black --check src/
```

### 2. 测试 Agent 验收

```bash
# 创建隔离环境
python -m venv .venv_test
source .venv_test/bin/activate
pip install -e .

# 运行验收测试
pytest tests/acceptance/test_m<module_number>.py -v

# 生成测试报告
pytest tests/acceptance/test_m<module_number>.py --html=report.html
```

### 3. 问题定位

```bash
# 测试失败时
pytest tests/acceptance/test_m<module_number>.py -vv --tb=short

# 查看详细日志
pytest tests/acceptance/test_m<module_number>.py --log-level=DEBUG --log-cli
```

### 4. 通过标准

- 所有验收测试通过
- 代码覆盖率 > 80%
- 无 mypy 错误
- 无 black 格式问题

---

## 附录：测试数据模板

### 示例 JD

```yaml
# tests/fixtures/jd/sample_jd.yaml
id: jd_sample_001
company_name: 示例科技公司
position: 产品经理
requirements:
  - 3年以上产品经验
  - 有数据分析能力
  - 熟悉敏捷开发
```

### 示例简历

```yaml
# tests/fixtures/resume/sample_resume.yaml
id: resume_sample_001
name: 张三
experiences:
  - company: ABC公司
    position: 产品实习生
    duration: 2023-06 至今
skills:
  - Python
  - SQL
  - 产品设计
```
