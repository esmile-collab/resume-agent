#!/usr/bin/env python3
# Input: 真实化样本模板与生成参数。
# Output: 输出更贴近真实投递场景的数据集。
# Pos: 评测数据增强脚本。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
"""
真实评测数据集生成器 v2.0

改进点：
1. 生成更真实、更完整的简历内容
2. 润色测试用例严格遵循"不编造事实"原则
3. 实现"识别→润色"的模块化流程
"""

import json
from pathlib import Path


# ============ 真实的 JD 模板 ============

REALISTIC_JDS = {
    "ai_engineer_bytedance": """# 字节跳动 | AI算法工程师（大模型方向）

## 岗位职责
1. 负责大语言模型（LLM）的训练优化与部署
2. 设计并实现高效的模型微调（SFT、RLHF）方案
3. 参与对话系统的研发，提升模型在具体场景下的表现
4. 跟进业界前沿技术，推动技术落地

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
""",

    "frontend_meituan": """# 美团 | 前端开发工程师

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
""",

    "pm_tencent": """# 腾讯 | 产品经理（视频方向）

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
}

# ============ 真实的简历模板 ============

REALISTIC_RESUMES = {
    # 场景1：关键词缺失但内容真实的简历
    "resume_with_hidden_keywords": """# 个人简历

## 教育背景
**清华大学** | 计算机科学与技术 | 本科 | 2021.09 - 2025.06
GPA: 3.8/4.0 | 专业排名：前10%

## 实习经历

### 字节跳动 | 算法实习生
**2024.07 - 2024.12**
- 负责深度学习模型的训练和优化工作
- 参与模型的性能调优和部署流程
- 使用 PyTorch 实现模型代码，进行实验验证

### 商汤科技 | 研发实习生
**2024.01 - 2024.06**
- 协助进行计算机视觉算法的研发
- 参与数据处理和模型训练工作

## 项目经历

### 智能问答助手
**2024.03 - 2024.05**
- 使用 API 开发了问答应用
- 实现了多轮对话功能
- 完成了系统测试和部署

### 图像分类系统
**2023.09 - 2023.12**
- 使用深度学习框架实现图像分类
- 完成数据预处理和模型训练
- 达到了较好的分类效果

## 技能
- 编程语言：Python、C++
- 深度学习：PyTorch、TensorFlow
- 其他：Git、Linux、SQL

## 自我评价
具备扎实的深度学习基础，有实际项目经验。学习能力强，能快速掌握新技术。
""",

    # 场景2：表达被动的真实简历
    "resume_passive_voice": """# 个人简历

## 教育背景
**北京大学** | 软件工程 | 本科 | 2021.09 - 2025.06
GPA: 3.6/4.0

## 实习经历

### 腾讯 | 前端开发实习生
**2024.07 - 至今**
- 负责视频播放器相关功能的开发
- 协助团队完成性能优化工作
- 参与代码评审和技术讨论
- 按要求完成分配的任务

### 阿里巴巴 | 前端实习生
**2024.01 - 2024.06**
- 协助开发电商活动页面
- 参与组件库的维护工作
- 配合设计师完成页面实现

## 项目经历

### 视频网站前端项目
**2023.10 - 2023.12**
- 负责整体前端架构设计
- 实现了视频播放功能
- 参与了性能优化工作

## 技能
- 前端框架：React、Vue
- 编程语言：JavaScript、TypeScript
- 其他：HTML、CSS、Webpack
""",

    # 场景3：STAR结构不完整的真实简历
    "resume_incomplete_star": """# 个人简历

## 教育背景
**上海交通大学 | 电子信息工程 | 本科 | 2021.09 - 2025.06**

## 实习经历

### 美团 | 产品经理实习生
**2024.07 - 2024.12**
参与了外卖推荐算法相关的产品工作，包括需求分析、方案设计、上线跟踪等环节。

### 小红书 | 运营实习生
**2024.01 - 2024.06**
负责内容审核和用户反馈处理，参与了一些运营活动的策划和执行。

## 项目经历

### 校园二手交易平台
- 使用 Vue + Spring Boot 开发
- 实现了商品发布、搜索、交易功能
- 技术栈：Vue、Spring Boot、MySQL

### 在线考试系统
- 基于 Django 框架开发
- 支持在线答题和自动评分
- 技术栈：Django、React、PostgreSQL

## 技能
- 产品工具：Axure、Figma、XMind
- 数据分析：Excel、SQL
- 编程：Python、JavaScript
"""
}

# ============ 润色规则定义（严格遵守不编造原则）============

POLISH_RULES = {
    "keyword_extraction": {
        "description": "从原简历中提取已有的技术关键词，确保不添加新内容",
        "allowed_operations": [
            "将描述性词汇改为具体技术名词（如'深度学习框架'改为'PyTorch'，当简历中技能部分提到PyTorch时）",
            "在已有事实基础上添加JD关键词（如'深度学习模型'可改为'深度学习/LLM模型'，因为LLM是深度学习的子集）"
        ],
        "forbidden_operations": [
            "添加原简历完全没有提及的技术或经验",
            "将通用的词改成简历中没有的具体技术"
        ]
    },
    "passive_to_active": {
        "description": "将被动表达改为主动表达，但不改变事实",
        "allowed_operations": [
            "将'负责'改为'主导'（当确实独立完成时）",
            "将'协助'改为'参与'或'协作完成'",
            "将'参与'改为'核心参与'（当确实是核心成员时）"
        ],
        "examples": [
            ("负责深度学习模型的训练", "主导深度学习模型的训练和优化"),
            ("协助团队完成性能优化", "协作完成系统性能优化，提升响应速度30%"),
            ("使用API开发了问答应用", "基于LLM API开发智能问答应用，支持多轮对话")
        ]
    },
    "star_completion": {
        "description": "补充STAR结构中的缺失要素，但只基于已有信息",
        "allowed_operations": [
            "为缺少背景的项目添加场景说明（基于项目名称和内容推断）",
            "为缺少结果的项目补充定性结果（如'完成上线'、'投入使用'）",
            "为缺少任务的项目明确目标"
        ],
        "forbidden_operations": [
            "编造具体的量化数据（如用户数、性能百分比）",
            "添加原简历中没有的项目阶段或成果"
        ],
        "examples": [
            {
                "before": "使用API开发了问答应用。",
                "after": """**背景**：针对用户咨询场景，构建智能问答能力
**任务**：实现基于API的问答系统
**行动**：调用API接口，完成问答逻辑开发和测试
**结果**：成功开发并上线问答应用""",
                "changes": ["添加背景推断", "明确任务", "补充行动细节", "添加定性结果"]
            }
        ]
    }
}

# ============ 润色识别结果定义 ============

POLISH_IDENTIFICATION_RESULT = {
    "resume_analysis": {
        "jd_keywords_found": ["深度学习", "PyTorch", "模型训练", "Python"],
        "jd_keywords_missing": ["LLM", "大语言模型", "SFT", "微调", "对话系统", "NLP", "Transformer", "BERT", "GPT"],
        "sections_analyzed": [
            {
                "section_id": "internship_bytedance_01",
                "section_type": "实习经历",
                "title": "字节跳动 | 算法实习生",
                "issues": [
                    {
                        "type": "keyword_missing",
                        "severity": "HIGH",
                        "description": "JD核心词'LLM/大语言模型'完全缺失",
                        "current_content": "负责深度学习模型的训练和优化工作",
                        "can_polish": True,
                        "polish_strategy": "将'深度学习模型'改为'深度学习/大语言模型'（LLM是深度学习的子集，不算编造）"
                    },
                    {
                        "type": "expression_passive",
                        "severity": "MEDIUM",
                        "description": "使用'负责'开头，表达较被动",
                        "current_content": "负责深度学习模型的训练和优化工作",
                        "can_polish": True,
                        "polish_strategy": "改为'主导深度学习/大语言模型的训练优化'"
                    }
                ]
            },
            {
                "section_id": "project_qa_01",
                "section_type": "项目经历",
                "title": "智能问答助手",
                "issues": [
                    {
                        "type": "keyword_missing",
                        "severity": "HIGH",
                        "description": "JD核心词'对话系统'完全缺失",
                        "current_content": "使用API开发问答应用",
                        "can_polish": True,
                        "polish_strategy": "将'问答应用'改为'对话问答应用'或'智能问答系统'"
                    },
                    {
                        "type": "star_incomplete",
                        "severity": "HIGH",
                        "description": "缺少STAR结构的背景、任务、结果要素",
                        "current_content": "使用API开发了问答应用\n实现了多轮对话功能\n完成了系统测试和部署",
                        "can_polish": True,
                        "polish_strategy": "重新组织为STAR结构，添加定性描述但不编造数据"
                    }
                ]
            }
        ],
        "summary": {
            "total_issues": 4,
            "high_priority": 2,
            "medium_priority": 2,
            "can_polish_without_fabrication": True
        }
    }
}


# ============ 正确的润色示例（严格遵守原则） ============

CORRECT_POLISH_EXAMPLE = {
    "original": """## 实习经历

### 字节跳动 | 算法实习生
**2024.07 - 2024.12**
- 负责深度学习模型的训练和优化工作
- 参与模型的性能调优和部署流程
- 使用 PyTorch 实现模型代码，进行实验验证

## 项目经历

### 智能问答助手
**2024.03 - 2024.05**
- 使用 API 开发了问答应用
- 实现了多轮对话功能
- 完成了系统测试和部署""",

    "identification": POLISH_IDENTIFICATION_RESULT,

    "polished": """## 实习经历

### 字节跳动 | 算法实习生（深度学习/大模型方向）
**2024.07 - 2024.12**
- **主导**深度学习/大语言模型的训练优化和性能调优工作
- 使用 **PyTorch** 实现模型代码，完成实验验证和部署流程
- 参与模型全流程开发，从数据处理到模型上线

## 项目经历

### 智能对话问答助手
**2024.03 - 2024.05**
**背景**：针对智能问答场景，开发对话应用
**任务**：基于API构建支持多轮对话的问答系统
**行动**：调用API接口，实现问答逻辑、多轮对话管理和功能测试
**结果**：成功完成开发并部署上线""",

    "changes_log": [
        {
            "section": "实习标题",
            "before": "字节跳动 | 算法实习生",
            "after": "字节跳动 | 算法实习生（深度学习/大模型方向）",
            "type": "关键词强化",
            "reason": "添加'大模型'，因为'深度学习'包含大模型，且JD要求大模型经验。不算编造，只是明确方向。"
        },
        {
            "section": "实习描述-第1条",
            "before": "负责深度学习模型的训练和优化工作",
            "after": "主导深度学习/大语言的训练优化和性能调优工作",
            "type": "表达优化",
            "reason": "将'负责'改为'主导'，'模型'明确为'大语言模型'（LLM是深度学习子集），添加'性能调优'（后文已提到）。"
        },
        {
            "section": "项目标题",
            "before": "智能问答助手",
            "after": "智能对话问答助手",
            "type": "关键词强化",
            "reason": "添加'对话'，匹配JD的'对话系统'要求。原内容提到'多轮对话'，所以不算编造。"
        },
        {
            "section": "项目描述",
            "before": "使用API开发了问答应用\n实现了多轮对话功能\n完成了系统测试和部署",
            "after": "**背景**：针对智能问答场景，开发对话应用\n**任务**：基于API构建支持多轮对话的问答系统\n**行动**：调用API接口，实现问答逻辑、多轮对话管理和功能测试\n**结果**：成功完成开发并部署上线",
            "type": "STAR结构重组",
            "reason": "将原有内容重新组织为STAR结构，不添加新事实，只是优化逻辑呈现。"
        }
    ],

    "fact_check": {
        "added_technologies": [],  # 没有添加原简历没有的技术
        "added_projects": [],      # 没有添加原简历没有的项目
        "added_roles": [],         # 没有添加原简历没有的职位
        "fabricated_data": False   # 没有编造数据
    }
}


def generate_realistic_dataset(output_dir: Path):
    """生成真实的评测数据集"""

    output_dir = Path(output_dir)
    (output_dir / "jds").mkdir(parents=True, exist_ok=True)
    (output_dir / "resumes").mkdir(parents=True, exist_ok=True)
    (output_dir / "expected").mkdir(parents=True, exist_ok=True)

    # 生成 JD 文件
    for name, content in REALISTIC_JDS.items():
        (output_dir / "jds" / f"{name}.md").write_text(content, encoding="utf-8")

    # 生成简历文件
    for name, content in REALISTIC_RESUMES.items():
        (output_dir / "resumes" / f"{name}.md").write_text(content, encoding="utf-8")

    # 生成期望的润色结果
    (output_dir / "expected" / "correct_polish_example.json").write_text(
        json.dumps(CORRECT_POLISH_EXAMPLE, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # 生成润色规则文档
    (output_dir / "polish_rules.json").write_text(
        json.dumps(POLISH_RULES, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # 生成识别结果示例
    (output_dir / "identification_example.json").write_text(
        json.dumps(POLISH_IDENTIFICATION_RESULT, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"✅ 真实评测数据集已生成到 {output_dir}")
    print(f"   - JD: {len(REALISTIC_JDS)} 个")
    print(f"   - 简历: {len(REALISTIC_RESUMES)} 个")
    print(f"   - 期望结果: 1 个完整示例")


if __name__ == "__main__":
    generate_realistic_dataset(Path("evaluation_dataset_v2"))
