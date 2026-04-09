#!/bin/bash
# Input: pytest 与本地回归命令。
# Output: 执行仓库回归检查。
# Pos: 回归脚本。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
# M7 最小回归脚本：覆盖主链路与新增稳定性模块

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

PYTEST_BIN="${PYTEST_BIN:-.venv/bin/pytest}"

echo "=== M7 回归测试 ==="
"$PYTEST_BIN" tests/acceptance/test_m4.py -v
"$PYTEST_BIN" tests/acceptance/test_m5.py -v
"$PYTEST_BIN" tests/acceptance/test_m6.py -v
"$PYTEST_BIN" tests/acceptance/test_m7.py -v
echo "✓ M7 回归测试通过"
