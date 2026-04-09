<!--
Input: 历史设计、专项分析或参考资料。
Output: 保留《评测集快速开始指南》作为参考或归档材料。
Pos: 历史或参考文档。
Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
-->
# 评测集快速开始指南

## 概述

本指南帮助你快速创建和使用简历评分与润色系统的评测集。

---

## 一、生成评测数据集

### 1. 生成完整数据集（50个测试对）

```bash
cd /Users/cyx/program_coding/简历\ agent
python scripts/generate_evaluation_dataset.py --category all
```

### 2. 生成特定类别数据集

```bash
# 只生成学历维度测试
python scripts/generate_evaluation_dataset.py --category education

# 只生成实习维度测试
python scripts/generate_evaluation_dataset.py --category internship

# 只生成项目维度测试
python scripts/generate_evaluation_dataset.py --category project

# 只生成软性指标测试
python scripts/generate_evaluation_dataset.py --category soft_skills

# 只生成润色功能测试
python scripts/generate_evaluation_dataset.py --category polish
```

### 3. 输出结构

```
evaluation_dataset/
├── jds/
│   ├── edu_001_jd.md          # JD文件
│   ├── edu_002_jd.md
│   └── ...
├── resumes/
│   ├── edu_001_resume.md      # 简历文件
│   ├── edu_002_resume.md
│   └── ...
└── metadata/
    ├── dataset_mapping.csv    # 测试配对关系
    └── ground_truth_labels.json # 真实标签
```

---

## 二、运行评测

### 1. 运行完整评测

```bash
python scripts/run_evaluation.py --dataset evaluation_dataset
```

### 2. 运行特定类别评测

```bash
# 只评测学历维度
python scripts/run_evaluation.py --dataset evaluation_dataset --category education

# 只评测实习维度
python scripts/run_evaluation.py --dataset evaluation_dataset --category internship
```

### 3. 运行单个测试

```bash
# 测试单个配对
python scripts/run_evaluation.py --dataset evaluation_dataset --test-id edu_001
```

### 4. 输出结果

```
evaluation_dataset/
└── results/
    ├── evaluation_results.json     # 详细结果JSON
    └── evaluation_report.md        # 可读报告
```

---

## 三、评测报告解读

### 报告结构

```markdown
# 简历评分系统评测报告

## 概览
- 测试数量: 50
- 匹配级别准确率: 85%

## 维度误差 (MAE)
| 维度 | MAE | 评级 |
|------|-----|------|
| internship | 8.5 | ✅ 优秀 |
| project | 12.3 | ⚠️ 需改进 |
| education | 2.1 | ✅ 优秀 |

## 详细结果
### 学历_985_AI
#### edu_001 - AI算法工程师 @ 字节跳动
...
```

### 指标说明

| 指标 | 说明 | 目标值 |
|------|------|--------|
| **MAE** | 平均绝对误差，越小越好 | < 10 分 |
| **匹配级别准确率** | 预测级别正确的比例 | > 85% |
| **✅ 优秀** | MAE < 10 | - |
| **⚠️ 需改进** | 10 ≤ MAE < 15 | - |
| **❌ 较差** | MAE ≥ 15 | - |

---

## 四、润色功能评测（需要 resume-polish skill）

### 1. 生成润色测试数据

```bash
python scripts/generate_evaluation_dataset.py --category polish
```

### 2. 评测流程

```bash
# 使用 resume-polish skill 处理润色测试
# 润色简历：简历：evaluation_dataset/resumes/pln_001_resume.md JD：evaluation_dataset/jds/pln_001_jd.md
```

### 3. 润色评测要点

| 检查项 | 说明 |
|--------|------|
| **是否编造事实** | 改写后是否添加了原简历中没有的信息（必须为0） |
| **关键词覆盖** | JD关键词是否被正确嵌入 |
| **表达优化** | 技术术语是否转为业务语言 |
| **STAR完整性** | 改写后是否包含完整的STAR结构 |
| **评分提升** | 改写后评分是否提升 |

---

## 五、自定义测试数据

### 添加新的测试配对

1. 在 `generate_evaluation_dataset.py` 中添加新模板：

```python
JD_TEMPLATES = {
    "my_custom_jd": {
        "name": "我的自定义岗位",
        "company": "公司名",
        "卷度系数": 0.7,
        "required_skills": ["技能1", "技能2"],
        ...
    }
}

RESUME_TEMPLATES = {
    "my_custom_resume": {
        "category": "custom",
        "education": "清华大学 | 计算机科学与技术 | 本科",
        ...
    }
}

TEST_PAIRS = [
    {"id": "custom_001", "jd": "my_custom_jd", "resume": "my_custom_resume", "category": "自定义"}
]
```

2. 重新生成数据集：

```bash
python scripts/generate_evaluation_dataset.py --category all
```

---

## 六、常见问题

### Q1: 生成的简历不够真实怎么办？

**A**: 可以基于生成的模板进行修改，或使用真实脱敏简历替换生成文件。

### Q2: 如何添加真实标签？

**A**: 编辑 `ground_truth_labels.json`，添加人工标注的真实分数：

```json
{
  "pair_id": "edu_001",
  "ground_truth_labels": {
    "final_score": 85.0,
    "internship": 100.0,
    "project": 90.0,
    ...
  }
}
```

### Q3: 评测结果显示"较差"怎么办？

**A**:
1. 检查该维度的失败案例
2. 查看具体误差来源
3. 调整 `campus_scorer.py` 中的评分逻辑或 prompts
4. 重新运行评测验证

### Q4: 如何测试润色功能？

**A**: 润色功能评测需要人工检查，重点关注：
- 是否编造事实（打开原简历和润色后简历对比）
- 关键词是否正确嵌入
- 表达是否优化

---

## 七、下一步

1. **生成数据集**: 运行 `generate_evaluation_dataset.py`
2. **运行评测**: 运行 `run_evaluation.py`
3. **分析结果**: 查看 `evaluation_report.md`
4. **优化系统**: 根据失败案例调整评分逻辑
5. **迭代验证**: 重新运行评测确认改进效果

---

## 八、评测维度参考

完整评测维度请参考: [docs/EVALUATION_DATASET_STRATEGY.md](docs/EVALUATION_DATASET_STRATEGY.md)

### 核心测试维度

| 维度 | 测试数量 | 覆盖场景 |
|------|----------|----------|
| 学历层次 | 10 | 985/211/双非/海外 |
| 实习经历 | 15 | 大厂/独角兽/中型/无实习 |
| 项目经历 | 10 | 完整/课程/想法/无项目 |
| 专业对口 | 6 | 完全对口/相关/跨专业 |
| 技术栈匹配 | 4 | 完全匹配/部分/不匹配 |
| 软性指标 | 15 | 学习能力/执行能力/数据意识 |
| 润色功能 | 10 | 关键词/表达/逻辑/STAR |
| 边界场景 | 5 | 极端高分/极端低分/信息缺失 |
