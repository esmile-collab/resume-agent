# Input: 上层运行时对领域服务的导入。
# Output: 声明 services 包边界。
# Pos: 领域服务包导出入口。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
"""Service layer for Resume Polisher MVP."""

from services.analyzer import AnalysisResult, JDAnalyzer
from services.exporter import ResumeExporter
from services.patcher import PatchCandidate, PolishPatcher
from services.resume_parser import ResumeBlock, ResumeParser

__all__ = [
    "AnalysisResult",
    "JDAnalyzer",
    "PatchCandidate",
    "PolishPatcher",
    "ResumeBlock",
    "ResumeExporter",
    "ResumeParser",
]

