#!/usr/bin/env python3
# Input: 评测数据集、评分器与报告模板。
# Output: 运行评测并生成结果报告。
# Pos: 评测执行入口。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
"""
评测执行脚本 - 自动运行评测并生成报告

使用方法:
    python run_evaluation.py --dataset evaluation_dataset
    python run_evaluation.py --dataset evaluation_dataset --category education
    python run_evaluation.py --dataset evaluation_dataset --test-id edu_001
"""

import argparse
import json
import csv
from pathlib import Path
from typing import Literal
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from scoring.campus_scorer import CampusScorerV21
except ImportError:
    print("❌ 无法导入评分模块，请确保 src/scoring/campus_scorer.py 存在")
    sys.exit(1)


class EvaluationRunner:
    """评测运行器"""

    def __init__(self, dataset_dir: Path):
        self.dataset_dir = Path(dataset_dir)
        self.metadata_dir = self.dataset_dir / "metadata"
        self.jds_dir = self.dataset_dir / "jds"
        self.resumes_dir = self.dataset_dir / "resumes"
        self.output_dir = self.dataset_dir / "results"
        self.output_dir.mkdir(exist_ok=True)

        # 加载元数据
        self.mapping_data = self._load_mapping()
        self.ground_truth = self._load_ground_truth()

        # 初始化评分器
        self.scorer = CampusScorerV21()

    def _load_mapping(self) -> dict:
        """加载数据集映射"""
        mapping_file = self.metadata_dir / "dataset_mapping.csv"
        if not mapping_file.exists():
            return {}

        mapping = {}
        with open(mapping_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                mapping[row["pair_id"]] = row
        return mapping

    def _load_ground_truth(self) -> dict:
        """加载真实标签"""
        gt_file = self.metadata_dir / "ground_truth_labels.json"
        if not gt_file.exists():
            return {}

        with open(gt_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        return {item["pair_id"]: item for item in data}

    def run_single_test(self, pair_id: str) -> dict:
        """运行单个测试"""
        if pair_id not in self.mapping_data:
            print(f"❌ 未找到测试对: {pair_id}")
            return {}

        # 读取文件
        mapping = self.mapping_data[pair_id]
        jd_file = self.dataset_dir / mapping["jd_file"]
        resume_file = self.dataset_dir / mapping["resume_file"]

        if not jd_file.exists() or not resume_file.exists():
            print(f"❌ 文件不存在: {pair_id}")
            return {}

        jd_text = jd_file.read_text(encoding="utf-8")
        resume_text = resume_file.read_text(encoding="utf-8")

        # 运行评分
        print(f"📊 评测中: {pair_id} ({mapping['category']})")
        result = self.scorer.score(jd_text, resume_text)

        # 整理结果
        return {
            "pair_id": pair_id,
            "category": mapping["category"],
            "predicted": {
                "final_score": result.final_score,
                "match_level": result.match_level,
                "hard_scores": {
                    "internship": result.hard_metrics.internship_score,
                    "project": result.hard_metrics.project_score,
                    "technical_practice": result.hard_metrics.technical_practice_score,
                    "education": result.hard_metrics.education_score,
                    "major": result.hard_metrics.major_score,
                    "gpa": result.hard_metrics.gpa_score,
                    "english": result.hard_metrics.english_score,
                    "stability": result.hard_metrics.stability_score,
                },
                "soft_scores": {
                    "learning_ability": result.soft_metrics.learning_ability,
                    "execution": result.soft_metrics.execution,
                    "communication": result.soft_metrics.communication,
                    "data_awareness": result.soft_metrics.data_awareness,
                    "stability": result.soft_metrics.stability,
                    "adaptability": result.soft_metrics.adaptability,
                    "resume_logic": result.soft_metrics.resume_logic,
                },
                "total_hard": result.hard_metrics.total_score,
                "total_soft": result.soft_metrics.total_score,
            },
            "ground_truth": self.ground_truth.get(pair_id, {}).get("ground_truth_labels", {}),
            "expected_match_level": mapping.get("expected_match_level", ""),
            "jd_position": mapping.get("jd_position", ""),
            "jd_company": mapping.get("jd_company", ""),
        }

    def run_category_tests(self, category: str) -> list:
        """运行某个类别的所有测试"""
        results = []
        for pair_id, mapping in self.mapping_data.items():
            if mapping["category"].startswith(category):
                result = self.run_single_test(pair_id)
                if result:
                    results.append(result)
        return results

    def run_all_tests(self) -> list:
        """运行所有测试"""
        results = []
        for pair_id in self.mapping_data.keys():
            result = self.run_single_test(pair_id)
            if result:
                results.append(result)
        return results

    def calculate_metrics(self, results: list) -> dict:
        """计算评测指标"""
        if not results:
            return {}

        metrics = {
            "total_tests": len(results),
            "score_errors": [],
            "match_level_accuracy": 0,
            "category_metrics": {},
            "dimension_mae": {}
        }

        correct_match_level = 0
        dimension_errors = {
            "internship": [],
            "project": [],
            "education": [],
            "learning_ability": [],
            "execution": [],
            "data_awareness": []
        }

        for result in results:
            predicted = result["predicted"]
            ground_truth = result["ground_truth"]

            # 匹配级别准确率
            if predicted["match_level"] == ground_truth.get("overall"):
                correct_match_level += 1

            # 各维度误差
            for dim in dimension_errors.keys():
                if dim in ground_truth and dim in predicted["hard_scores"]:
                    error = abs(predicted["hard_scores"][dim] - ground_truth[dim])
                    dimension_errors[dim].append(error)
                elif dim in ground_truth and dim in predicted["soft_scores"]:
                    error = abs(predicted["soft_scores"][dim] - ground_truth[dim])
                    dimension_errors[dim].append(error)

        # 计算MAE
        for dim, errors in dimension_errors.items():
            if errors:
                metrics["dimension_mae"][dim] = sum(errors) / len(errors)

        metrics["match_level_accuracy"] = correct_match_level / len(results) if results else 0

        return metrics

    def generate_report(self, results: list, metrics: dict) -> str:
        """生成评测报告"""
        report = f"""# 简历评分系统评测报告

## 概览

- **测试数量**: {metrics.get('total_tests', 0)}
- **匹配级别准确率**: {metrics.get('match_level_accuracy', 0):.1%}

## 维度误差 (MAE)

| 维度 | MAE | 评级 |
|------|-----|------|
"""

        for dim, mae in metrics.get("dimension_mae", {}).items():
            level = "✅ 优秀" if mae < 10 else "⚠️ 需改进" if mae < 15 else "❌ 较差"
            report += f"| {dim} | {mae:.1f} | {level} |\n"

        report += "\n## 详细结果\n\n"

        # 按类别分组
        by_category = {}
        for result in results:
            cat = result["category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(result)

        for category, cat_results in sorted(by_category.items()):
            report += f"### {category}\n\n"
            for result in cat_results:
                report += f"""
#### {result['pair_id']} - {result['jd_position']} @ {result['jd_company']}

| 指标 | 预测值 | 真实值 | 误差 |
|------|--------|--------|------|
| 总分 | {result['predicted']['final_score']:.1f} | {result['ground_truth'].get('final_score', '-')} | - |
| 匹配级别 | {result['predicted']['match_level']} | {result['ground_truth'].get('overall', '-')} | {'✅' if result['predicted']['match_level'] == result['ground_truth'].get('overall', '') else '❌'} |

"""

        return report

    def save_results(self, results: list, metrics: dict):
        """保存评测结果"""
        # 保存JSON结果
        results_file = self.output_dir / "evaluation_results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump({
                "results": results,
                "metrics": metrics
            }, f, ensure_ascii=False, indent=2)

        # 保存报告
        report = self.generate_report(results, metrics)
        report_file = self.output_dir / "evaluation_report.md"
        report_file.write_text(report, encoding="utf-8")

        print(f"\n✅ 评测完成！")
        print(f"   - 结果文件: {results_file}")
        print(f"   - 评测报告: {report_file}")


def main():
    parser = argparse.ArgumentParser(description="运行评测")
    parser.add_argument(
        "--dataset", "-d",
        type=Path,
        default=Path("evaluation_dataset"),
        help="数据集目录"
    )
    parser.add_argument(
        "--category", "-c",
        type=str,
        help="测试类别（education, internship, project, soft_skills, polish）"
    )
    parser.add_argument(
        "--test-id", "-t",
        type=str,
        help="指定测试ID"
    )

    args = parser.parse_args()

    runner = EvaluationRunner(args.dataset)

    # 运行测试
    if args.test_id:
        results = [runner.run_single_test(args.test_id)]
    elif args.category:
        results = runner.run_category_tests(args.category)
    else:
        results = runner.run_all_tests()

    if not results:
        print("❌ 没有运行任何测试")
        return

    # 计算指标并生成报告
    metrics = runner.calculate_metrics(results)
    runner.save_results(results, metrics)


if __name__ == "__main__":
    main()
