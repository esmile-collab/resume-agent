#!/usr/bin/env python3
# Input: 评分引擎与样例 JD/简历文本。
# Output: 直接验证评分器输出。
# Pos: 评分专项测试脚本。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
"""
直接测试 resume-score 功能（通过底层模块）
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scoring.campus_scorer import CampusScorerV21


def test_resume_score():
    """测试简历评分"""

    # 读取测试文件
    jd_file = Path("evaluation_dataset_v2/jds/ai_engineer_bytedance.md")
    resume_file = Path("evaluation_dataset_v2/resumes/resume_with_hidden_keywords.md")

    jd_text = jd_file.read_text(encoding='utf-8')
    resume_text = resume_file.read_text(encoding='utf-8')

    print("=" * 60)
    print("直接测试 resume-score (CampusScorerV21)")
    print("=" * 60)

    # 创建评分器
    scorer = CampusScorerV21()

    # 执行评分
    print("\n📊 执行评分...")
    report = scorer.score(jd_text, resume_text)

    print(f"\n✅ 评分完成！")
    print(f"\n总分: {report.final_score:.1f}/100")
    print(f"评级: {report.match_level}")
    print(f"\n硬性指标: {report.hard_metrics.total_score:.1f}/60")
    print(f"  - 实习经历: {report.hard_metrics.internship_score:.1f}")
    print(f"  - 项目经历: {report.hard_metrics.project_score:.1f}")
    print(f"  - 技术实践: {report.hard_metrics.technical_practice_score:.1f}")
    print(f"  - 教育背景: {report.hard_metrics.education_score:.1f}")
    print(f"\n软性指标: {report.soft_metrics.total_score:.1f}/40")
    print(f"  - 学习能力: {report.soft_metrics.learning_ability:.1f}")
    print(f"  - 执行能力: {report.soft_metrics.execution:.1f}")
    print(f"  - 数据意识: {report.soft_metrics.data_awareness:.1f}")
    print(f"  - 简历逻辑: {report.soft_metrics.resume_logic:.1f}")

    print(f"\n建议: {report.suggestion}")

    return report


if __name__ == "__main__":
    test_resume_score()
