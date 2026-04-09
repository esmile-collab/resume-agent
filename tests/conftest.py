# Input: pytest 会话级共享配置。
# Output: 输出测试通用 fixture 与环境准备逻辑。
# Pos: 测试全局配置文件。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
"""Shared pytest setup for path resolution across Python/pytest versions."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
