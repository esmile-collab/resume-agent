# Input: 上层 API/CLI 对 agent 包的导入。
# Output: 导出当前主运行时对象。
# Pos: Agent 包导出入口。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
"""Server-side agent runtime package."""

from agent.runtime import ResumeAgentRuntime

__all__ = ["ResumeAgentRuntime"]
