# Input: 上层工具对评分器的导入。
# Output: 导出当前校园招聘评分器与相关模型。
# Pos: 评分包导出入口。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
"""Scoring module for campus recruitment resume evaluation."""

from .campus_scorer import CampusScorerV21
from .models import (
    HardMetricsScore,
    ScoreReport,
    SoftMetricsScore,
)

__all__ = [
    "CampusScorerV21",
    "ScoreReport",
    "HardMetricsScore",
    "SoftMetricsScore",
]
