# Input: 历史工具命名空间导入。
# Output: 声明 tools 包边界。
# Pos: 历史工具包占位入口。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
"""Compatibility exports for the active runtime tool registry."""

from agent.tools import AgentToolRegistry

__all__ = ["AgentToolRegistry"]
