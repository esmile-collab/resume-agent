#!/usr/bin/env python3
# Input: 评测样本模板与生成参数。
# Output: 生成评测数据集文件。
# Pos: 评测数据生成脚本。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
"""
评测集生成工具 - 自动生成 JD 和简历测试数据

使用方法:
    python generate_evaluation_dataset.py --category all
    python generate_evaluation_dataset.py --category education
    python generate_evaluation_dataset.py --category internship
"""

import argparse
import json
from pathlib import Path
from typing import Literal


# ============ JD 模板库 ============

JD_TEMPLATES = {
    "ai_engineer": {
        "name": "AI算法工程师",
        "company": "字节跳动",
        "卷度系数": 0.95,
        "required_skills": ["Python", "PyTorch", "深度学习", "NLP", "Transformer", "大模型"],
        "preferred_skills": ["CUDA", "C++", "分布式训练"],
        "internship_required": True,
        "project_required": True,
        "education_requirement": "985/211硕士",
        "major_requirement": ["计算机", "数学", "统计", "自动化"],
        "template": """
## 岗位职责
1. 负责大语言模型（LLM）的训练优化与部署
2. 设计并实现高效的模型微调（SFT、RLHF）方案
3. 参与对话系统的研发，提升模型在具体场景下的表现
4. 跟业界前沿技术，推动技术落地

## 任职要求
**基本要求：**
- 985/211院校硕士及以上学历，计算机、数学、统计等相关专业
- 熟练掌握 Python、PyTorch 等深度学习框架
- 熟悉 Transformer、BERT、GPT 等主流模型架构
- 有扎实的深度学习、NLP 理论基础

**优先考虑：**
- 有大模型训练、微调经验者优先
- 有知名互联网公司AI相关实习经验者优先
- 有顶会论文（NeurIPS、ICML、ACL等）发表者优先
- 熟悉 CUDA、分布式训练者优先

## 团队介绍
我们负责字节跳动大模型相关技术的研发，包括模型训练、微调、部署全流程。
"""
    },

    "frontend_engineer": {
        "name": "前端开发工程师",
        "company": "美团",
        "卷度系数": 0.65,
        "required_skills": ["JavaScript", "React", "TypeScript", "CSS", "HTML"],
        "preferred_skills": ["Vue", "Node.js", "Webpack"],
        "internship_required": True,
        "project_required": False,
        "education_requirement": "本科及以上",
        "major_requirement": ["计算机", "软件工程"],
        "template": """
## 岗位职责
1. 负责美团外卖前端核心功能开发
2. 参与前端架构设计和性能优化
3. 与产品、设计团队紧密配合，高质量完成需求

## 任职要求
- 本科及以上学历，计算机、软件工程相关专业
- 熟练掌握 JavaScript、TypeScript
- 熟悉 React 或 Vue 框架
- 有良好的编程习惯和代码风格

## 优先条件
- 有互联网公司前端实习经验者优先
- 有大型前端项目开发经验者优先
- 有开源项目贡献者优先
"""
    },

    "product_manager": {
        "name": "产品经理",
        "company": "腾讯",
        "卷度系数": 0.75,
        "required_skills": ["产品设计", "需求分析", "数据分析", "PRD撰写"],
        "preferred_skills": ["SQL", "Axure", "Figma"],
        "internship_required": True,
        "project_required": True,
        "education_requirement": "本科及以上",
        "major_requirement": ["不限"],
        "template": """
## 岗位职责
1. 负责腾讯视频产品的功能规划和设计
2. 深入理解用户需求，进行需求分析和优先级排序
3. 撰写PRD文档，与研发、设计团队协作推动产品落地
4. 通过数据分析持续优化产品体验

## 任职要求
- 本科及以上学历，专业不限
- 具备良好的逻辑思维和沟通能力
- 有互联网产品实习或项目经验者优先
- 熟练使用 Axure、Figma 等工具

## 加分项
- 有视频/内容社区产品经验者优先
- 有大厂产品实习经验者优先
- 数据分析能力强者优先
"""
    },

    "operations": {
        "name": "用户运营",
        "company": "小红书",
        "卷度系数": 0.45,
        "required_skills": ["用户运营", "活动策划", "数据分析", "内容运营"],
        "preferred_skills": ["Excel", "SQL", "PPT"],
        "internship_required": False,
        "project_required": False,
        "education_requirement": "本科及以上",
        "major_requirement": ["不限"],
        "template": """
## 岗位职责
1. 负责小红书社区用户增长和活跃
2. 策划并执行用户活动，提升用户参与度
3. 分析用户行为数据，优化运营策略
4. 维护核心用户关系，收集用户反馈

## 任职要求
- 本科及以上学历，专业不限
- 对互联网运营有浓厚兴趣
- 具备良好的沟通能力和执行力
- 有相关实习或校园活动经验者优先

## 优先条件
- 有社区/内容运营经验者优先
- 数据敏感度高者优先
"""
    }
}

# ============ 简历模板库 ============

RESUME_TEMPLATES = {
    # ========== 学历场景 ==========
    "education_985": {
        "category": "education",
        "education": "清华大学 | 计算机科学与技术 | 本科 | 985",
        "gpa": "3.8/4.0 | 专业排名前10%",
        "expected_scores": {"education": 100, "overall": "high"}
    },
    "education_211": {
        "category": "education",
        "education": "北京交通大学 | 计算机科学与技术 | 本科 | 211",
        "gpa": "3.5/4.0 | 专业排名前30%",
        "expected_scores": {"education": 85, "overall": "medium"}
    },
    "education_dual": {
        "category": "education",
        "education": "北京工业大学 | 软件工程 | 本科 | 双非一本",
        "gpa": "3.2/4.0 | 专业排名前50%",
        "expected_scores": {"education": 70, "overall": "medium-low"}
    },
    "education_overseas_top": {
        "category": "education",
        "education": "Stanford University | Computer Science | Master | 海外Top",
        "gpa": "3.9/4.0 | GPA: 3.9",
        "expected_scores": {"education": 105, "overall": "high"}  # 精英校加分
    },

    # ========== 实习场景 ==========
    "internship_big": {
        "category": "internship",
        "internships": [
            {
                "company": "字节跳动",
                "position": "算法工程师实习生",
                "duration": "2023.07 - 2023.12",
                "description": "负责推荐算法优化，使用深度学习模型提升CTR 15%"
            }
        ],
        "expected_scores": {"internship": 100, "overall": "high"}
    },
    "internship_unicorn": {
        "category": "internship",
        "internships": [
            {
                "company": "小红书",
                "position": "后端开发实习生",
                "duration": "2023.06 - 2023.09",
                "description": "参与用户系统开发，使用Go语言实现微服务架构"
            }
        ],
        "expected_scores": {"internship": 85, "overall": "medium-high"}
    },
    "internship_none": {
        "category": "internship",
        "internships": [],
        "expected_scores": {"internship": 20, "overall": "low"}
    },

    # ========== 项目场景 ==========
    "project_full": {
        "category": "project",
        "projects": [
            {
                "name": "基于LLM的智能问答系统",
                "role": "核心开发者",
                "description": "使用LangChain + OpenAI API构建企业知识库问答系统，支持文档上传、向量检索、多轮对话。已完成上线，用户数500+，日均查询1000+次。",
                "tech_stack": ["Python", "LangChain", "OpenAI API", "Pinecone", "FastAPI"]
            }
        ],
        "expected_scores": {"project": 100, "overall": "high"}
    },
    "project_course": {
        "category": "project",
        "projects": [
            {
                "name": "图书管理系统（课程设计）",
                "role": "开发者",
                "description": "使用Java + MySQL实现图书的增删改查功能，支持用户管理和借阅记录查询。",
                "tech_stack": ["Java", "MySQL", "Swing"]
            }
        ],
        "expected_scores": {"project": 60, "overall": "medium-low"}
    },
    "project_idea": {
        "category": "project",
        "projects": [
            {
                "name": "校园社交APP（构思阶段）",
                "role": "发起者",
                "description": "计划做一个校园社交应用，帮助同学们找到志同道合的朋友。正在做产品设计。",
                "tech_stack": []
            }
        ],
        "expected_scores": {"project": 30, "overall": "low"}
    },

    # ========== 软性指标场景 ==========
    "soft_learning_high": {
        "category": "soft_skills",
        "learning_evidence": "2周自学PyTorch并完成图像分类项目，准确率达92%",
        "execution_evidence": "独立从0到1完成个人博客系统开发，上线后持续维护至今",
        "data_evidence": "优化推荐算法后，CTR从2.3%提升至3.1%，提升35%",
        "expected_scores": {"learning_ability": 100, "execution": 100, "data_awareness": 100}
    },
    "soft_learning_low": {
        "category": "soft_skills",
        "learning_evidence": "",
        "execution_evidence": "参与团队项目，按导师要求完成分配任务",
        "data_evidence": "负责的功能上线后效果良好",
        "expected_scores": {"learning_ability": 50, "execution": 60, "data_awareness": 50}
    },
    "soft_no_data": {
        "category": "soft_skills",
        "learning_evidence": "学习过机器学习相关知识",
        "execution_evidence": "完成了一个个人项目",
        "data_evidence": "项目效果很好，获得了导师的好评",  # 无量化数据
        "expected_scores": {"data_awareness": 40}
    },

    # ========== 润色测试场景 ==========
    "polish_missing_keywords": {
        "category": "polish",
        "polish_type": "关键词缺失",
        "jd_keywords": ["大模型", "对话系统", "NLP"],
        "resume_content": """
## 实习经历
**字节跳动 | 算法实习生**
负责深度学习模型训练和优化工作。

## 项目经历
**智能问答系统**
使用API开发了一个问答应用。
""",
        "expected_changes": ["添加'大模型'", "添加'对话系统'", "添加'NLP'"]
    },
    "polish_technical_jargon": {
        "category": "polish",
        "polish_type": "技术术语堆砌",
        "jd_keywords": ["用户体验", "产品优化"],
        "resume_content": """
## 项目经历
**用户增长项目**
使用A/B测试、漏斗分析、留存分析、用户分群、RFM模型等技术手段进行用户数据分析，通过SQL提取数据，用Python做数据清洗，用Tableau做可视化。
""",
        "expected_changes": ["将技术术语转为业务价值说明", "突出对用户体验的提升"]
    },
    "polish_passive_voice": {
        "category": "polish",
        "polish_type": "被动表达",
        "jd_keywords": [],
        "resume_content": """
## 项目经历
**电商推荐系统**
- 负责推荐算法开发
- 协助数据清洗工作
- 参与系统测试
""",
        "expected_changes": ["'负责'改为'主导'", "'协助'改为'独立完成'", "'参与'改为'推动'"]
    }
}

# ============ 测试配对矩阵 ============

TEST_PAIRS = [
    # 学历维度 (10个)
    {"id": "edu_001", "jd": "ai_engineer", "resume": "education_985", "category": "学历_985_AI"},
    {"id": "edu_002", "jd": "ai_engineer", "resume": "education_211", "category": "学历_211_AI"},
    {"id": "edu_003", "jd": "ai_engineer", "resume": "education_dual", "category": "学历_双非_AI"},
    {"id": "edu_004", "jd": "ai_engineer", "resume": "education_overseas_top", "category": "学历_海外Top_AI"},
    {"id": "edu_005", "jd": "frontend_engineer", "resume": "education_985", "category": "学历_985_前端"},
    {"id": "edu_006", "jd": "frontend_engineer", "resume": "education_211", "category": "学历_211_前端"},
    {"id": "edu_007", "jd": "frontend_engineer", "resume": "education_dual", "category": "学历_双非_前端"},
    {"id": "edu_008", "jd": "product_manager", "resume": "education_985", "category": "学历_985_产品"},
    {"id": "edu_009", "jd": "product_manager", "resume": "education_dual", "category": "学历_双非_产品"},
    {"id": "edu_010", "jd": "operations", "resume": "education_211", "category": "学历_211_运营"},

    # 实习维度 (15个)
    {"id": "int_001", "jd": "ai_engineer", "resume": "internship_big", "category": "实习_大厂_AI"},
    {"id": "int_002", "jd": "ai_engineer", "resume": "internship_unicorn", "category": "实习_独角兽_AI"},
    {"id": "int_003", "jd": "ai_engineer", "resume": "internship_none", "category": "实习_无_AI"},
    {"id": "int_004", "jd": "frontend_engineer", "resume": "internship_big", "category": "实习_大厂_前端"},
    {"id": "int_005", "jd": "frontend_engineer", "resume": "internship_none", "category": "实习_无_前端"},
    {"id": "int_006", "jd": "product_manager", "resume": "internship_big", "category": "实习_大厂_产品"},
    {"id": "int_007", "jd": "product_manager", "resume": "internship_none", "category": "实习_无_产品"},
    {"id": "int_008", "jd": "operations", "resume": "internship_none", "category": "实习_无_运营"},

    # 项目维度
    {"id": "prj_001", "jd": "ai_engineer", "resume": "project_full", "category": "项目_完整_AI"},
    {"id": "prj_002", "jd": "ai_engineer", "resume": "project_course", "category": "项目_课程_AI"},
    {"id": "prj_003", "jd": "ai_engineer", "resume": "project_idea", "category": "项目_想法_AI"},
    {"id": "prj_004", "jd": "frontend_engineer", "resume": "project_full", "category": "项目_完整_前端"},

    # 软性指标维度
    {"id": "soft_001", "jd": "ai_engineer", "resume": "soft_learning_high", "category": "软技能_高能力"},
    {"id": "soft_002", "jd": "ai_engineer", "resume": "soft_learning_low", "category": "软技能_低能力"},
    {"id": "soft_003", "jd": "product_manager", "resume": "soft_no_data", "category": "软技能_无数据"},

    # 润色测试维度
    {"id": "pln_001", "jd": "ai_engineer", "resume": "polish_missing_keywords", "category": "润色_关键词缺失"},
    {"id": "pln_002", "jd": "product_manager", "resume": "polish_technical_jargon", "category": "润色_技术术语"},
    {"id": "pln_003", "jd": "operations", "resume": "polish_passive_voice", "category": "润色_被动表达"},
]


def generate_resume(resume_template: dict) -> str:
    """生成简历文本"""
    if resume_template.get("polish_type"):
        # 润色测试专用简历
        return resume_template["resume_content"]

    # 常规简历生成
    sections = []

    # 教育背景
    if "education" in resume_template:
        sections.append(f"## 教育背景\n{resume_template['education']}\n{resume_template.get('gpa', '')}")

    # 实习经历
    if "internships" in resume_template:
        sections.append("## 实习经历")
        for intern in resume_template["internships"]:
            sections.append(f"""
**{intern['company']} | {intern['position']}**
{intern['duration']}
{intern['description']}
""")

    # 项目经历
    if "projects" in resume_template:
        sections.append("## 项目经历")
        for proj in resume_template["projects"]:
            tech_str = ", ".join(proj.get("tech_stack", []))
            sections.append(f"""
**{proj['name']}** | {proj['role']}
技术栈：{tech_str}
{proj['description']}
""")

    # 软性指标证据
    if "learning_evidence" in resume_template:
        sections.append(f"""
## 自我评价
- 学习能力：{resume_template.get('learning_evidence', '暂无')}
- 执行能力：{resume_template.get('execution_evidence', '暂无')}
- 数据意识：{resume_template.get('data_evidence', '暂无')}
""")

    return "\n".join(sections)


def generate_jd(jd_template: dict) -> str:
    """生成JD文本"""
    return f"""# {jd_template['company']} | {jd_template['name']}

{jd_template['template'].strip()}
"""


def create_dataset(
    output_dir: Path,
    category: Literal["all", "education", "internship", "project", "soft_skills", "polish"]
):
    """创建评测数据集"""

    # 过滤测试配对
    if category != "all":
        test_pairs = [p for p in TEST_PAIRS if p["category"].startswith({
            "education": "学历",
            "internship": "实习",
            "project": "项目",
            "soft_skills": "软技能",
            "polish": "润色"
        }[category])]
    else:
        test_pairs = TEST_PAIRS

    # 创建目录结构
    (output_dir / "jds").mkdir(parents=True, exist_ok=True)
    (output_dir / "resumes").mkdir(parents=True, exist_ok=True)
    (output_dir / "metadata").mkdir(parents=True, exist_ok=True)

    # 生成数据
    mapping_data = []
    ground_truth_data = []

    for pair in test_pairs:
        jd_template = JD_TEMPLATES[pair["jd"]]
        resume_template = RESUME_TEMPLATES[pair["resume"]]

        # 生成JD文件
        jd_content = generate_jd(jd_template)
        jd_file = output_dir / "jds" / f"{pair['id']}_jd.md"
        jd_file.write_text(jd_content, encoding="utf-8")

        # 生成简历文件
        resume_content = generate_resume(resume_template)
        resume_file = output_dir / "resumes" / f"{pair['id']}_resume.md"
        resume_file.write_text(resume_content, encoding="utf-8")

        # 记录元数据
        mapping_data.append({
            "pair_id": pair["id"],
            "jd_file": f"jds/{pair['id']}_jd.md",
            "resume_file": f"resumes/{pair['id']}_resume.md",
            "category": pair["category"],
            "jd_position": jd_template["name"],
            "jd_company": jd_template["company"],
            "jd_competition": jd_template["卷度系数"],
            "expected_match_level": resume_template.get("expected_scores", {}).get("overall", "unknown")
        })

        ground_truth_data.append({
            "pair_id": pair["id"],
            "category": pair["category"],
            "ground_truth_labels": resume_template.get("expected_scores", {}),
            "test_focus": get_test_focus(pair["category"])
        })

    # 保存元数据
    import csv
    with open(output_dir / "metadata" / "dataset_mapping.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=mapping_data[0].keys())
        writer.writeheader()
        writer.writerows(mapping_data)

    with open(output_dir / "metadata" / "ground_truth_labels.json", "w", encoding="utf-8") as f:
        json.dump(ground_truth_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 已生成 {len(test_pairs)} 个测试对到 {output_dir}")
    print(f"   - JD文件: {output_dir / 'jds'}")
    print(f"   - 简历文件: {output_dir / 'resumes'}")
    print(f"   - 元数据: {output_dir / 'metadata'}")


def get_test_focus(category: str) -> str:
    """获取测试重点描述"""
    focus_map = {
        "学历": "测试学历评分是否正确（985=100, 211=85, 双非=70）",
        "实习": "测试实习评分是否按公司层级正确计算",
        "项目": "测试项目评分（完整=100, 课程=60, 想法=30）",
        "软技能": "测试软性指标评分的准确性",
        "润色": "测试润色功能是否正确识别问题并进行改写"
    }
    for key, desc in focus_map.items():
        if category.startswith(key):
            return desc
    return "通用测试"


def main():
    parser = argparse.ArgumentParser(description="生成评测数据集")
    parser.add_argument(
        "--category", "-c",
        choices=["all", "education", "internship", "project", "soft_skills", "polish"],
        default="all",
        help="生成的测试类别"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("evaluation_dataset"),
        help="输出目录"
    )

    args = parser.parse_args()
    create_dataset(args.output, args.category)


if __name__ == "__main__":
    main()
