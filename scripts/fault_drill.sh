#!/bin/bash
# M7 故障演练：模拟对话状态文件损坏并验证系统可恢复

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python3.14}"

echo "=== M7 故障演练 ==="
"$PYTHON_BIN" - <<'PY'
from pathlib import Path

from orchestration import ResumeOrchestratorUseCase

use_case = ResumeOrchestratorUseCase()
project = use_case.init_project(name="fault-drill", cycle="2026秋招", base_resume_text="")
project_id = project["project_id"]

dialog_file = Path(".data") / "artifacts" / project_id / "state" / "dialog_messages.json"
dialog_file.parent.mkdir(parents=True, exist_ok=True)
dialog_file.write_text("{broken json", encoding="utf-8")

result = use_case.append_dialog_turn(
    project_id=project_id,
    role="user",
    content="故障恢复后的消息",
    facts=["恢复验证事实"],
)
assert result["recovered_from_corruption"] is True

messages = use_case.read_dialog_messages(project_id)
assert len(messages) == 1
assert messages[0]["content"] == "故障恢复后的消息"

print("✓ fault drill passed:", project_id)
PY
