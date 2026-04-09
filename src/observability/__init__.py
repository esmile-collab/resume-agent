# Input: 上层模块对观测子模块的导入。
# Output: 导出当前对话压缩管理器。
# Pos: 观测包导出入口。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
"""Dialog-compression helpers used by the current runtime."""

from observability.dialog import DialogCompressionManager

__all__ = ["DialogCompressionManager"]
