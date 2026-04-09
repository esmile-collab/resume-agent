# Input: 分形文档脚本与仓库结构约束。
# Output: 验证目录 README 与文件头注释未失配。
# Pos: 文档守卫单元测试。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
"""Guard the fractal documentation contract."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_fractal_docs_are_synced() -> None:
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, str(root / "scripts" / "fractal_docs.py"), "--check"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
