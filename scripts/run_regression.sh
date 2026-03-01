#!/bin/bash
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
