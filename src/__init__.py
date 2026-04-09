# Input: 安装器与上层模块导入。
# Output: 声明 src 包边界。
# Pos: 仓库源码包根。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
"""Top-level source package for Resume Agent."""

from __future__ import annotations

import sys
from pathlib import Path

_SRC_ROOT = Path(__file__).resolve().parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))
