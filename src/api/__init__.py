# Input: HTTP 服务导入与应用装配。
# Output: 声明 API 包边界。
# Pos: FastAPI 包导出入口。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
"""API package for Resume Agent."""

from .main import app

__all__ = ["app"]
