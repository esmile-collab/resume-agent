<!--
Input: 历史设计、专项分析或参考资料。
Output: 保留《简历评分与润色系统评测集 - 总结》作为参考或归档材料。
Pos: 历史或参考文档。
Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
-->
# 简历评分与润色系统评测集 - 总结

## 📋 评测策略已完成

### 1. 核心文档

| 文档 | 说明 | 路径 |
|------|------|------|
| **评测策略** | 完整的评测维度设计和测试场景定义 | [docs/EVALUATION_DATASET_STRATEGY.md](docs/EVALUATION_DATASET_STRATEGY.md) |
| **快速开始** | 评测系统使用教程 | [docs/EVALUATION_QUICKSTART.md](docs/EVALUATION_QUICKSTART.md) |
| **数据生成工具** | 自动生成评测数据集 | [scripts/generate_evaluation_dataset.py](scripts/generate_evaluation_dataset.py) |
| **评测执行工具** | 自动运行评测并生成报告 | [scripts/run_evaluation.py](scripts/run_evaluation.py) |

---

## 🎯 评测覆盖维度（50 个测试对）

### 硬性指标测试（35 个）

#### 学历层次（10 个）
- 985/211/双非/二本/海外Top/海外普通
- 测试精英校加分（清北+HYPSM+Oxbridge）
- 不同学历在各类 JD 中的评分准确性

#### 实习经历（15 个）
- 一线大厂/独角兽/中型公司/初创/无实习
- 按卷度区分：高卷度（AI算法）vs 中卷度（产品）vs 低卷度（运营）
- 测试卷度系数对实习 vs 项目权重的影响

#### 项目经历（10 个）
- 完整上线项目/课程设计/个人Demo/想法阶段/无项目
- 测试项目评分的准确性（完整=100, 课程=60, 想法=30）

### 软性指标测试（15 个）

| 维度 | 测试场景 | 数量 |
|------|----------|------|
| 学习能力 | 快速掌握/正常学习/学习较慢/无证据 | 5 |
| 执行能力 | 主导上线/参与核心/辅助支持/只有想法 | 5 |
| 数据意识 | 量化决策/有数据/定性描述/完全无数据 | 5 |

### 润色功能测试（10 个）

| 改写类型 | 测试场景 | 数量 |
|----------|----------|------|
| 关键词强化 | JD核心词完全缺失/密度不足 | 3 |
| 表达优化 | 技术术语堆砌/被动表达 | 2 |
| 逻辑重组 | STAR结构不完整/描述混乱 | 3 |
| 排序优化 | 相关经历未前置 | 2 |

---

## 🚀 使用方法

### 1️⃣ 生成评测数据集

```bash
# 生成完整数据集（50个测试对）
python scripts/generate_evaluation_dataset.py --category all

# 生成特定类别
python scripts/generate_evaluation_dataset.py --category education    # 学历维度
python scripts/generate_evaluation_dataset.py --category internship   # 实习维度
python scripts/generate_evaluation_dataset.py --category project      # 项目维度
python scripts/generate_evaluation_dataset.py --category soft_skills  # 软性指标
python scripts/generate_evaluation_dataset.py --category polish       # 润色功能
```

### 2️⃣ 运行评测

```bash
# 运行完整评测
python scripts/run_evaluation.py --dataset evaluation_dataset

# 运行特定类别评测
python scripts/run_evaluation.py --dataset evaluation_dataset --category education

# 运行单个测试
python scripts/run_evaluation.py --dataset evaluation_dataset --test-id edu_001
```

### 3️⃣ 查看评测报告

```bash
cat evaluation_dataset/results/evaluation_report.md
```

---

## 📊 评测指标

| 指标 | 计算方式 | 目标值 |
|------|----------|--------|
| **总分 MAE** | \|predicted_score - ground_truth\| / n | < 5 分 |
| **总分 RMSE** | sqrt(Σ(predicted - ground_truth)² / n) | < 7 分 |
| **级别准确率** | match_level 预测正确的比例 | > 85% |
| **硬性指标 MAE** | 硬性各维度预测误差均值 | < 10 分 |
| **软性指标 MAE** | 软性各维度预测误差均值 | < 15 分 |
| **事实编造检测** | 编造事实的改写数量 / 总改写数 | = 0 |

---

## 📁 数据集结构

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
├── metadata/
│   ├── dataset_mapping.csv            # JD-Resume配对关系
│   └── ground_truth_labels.json       # 人工标注的真实标签
└── results/
    ├── evaluation_results.json        # 详细结果JSON
    └── evaluation_report.md           # 可读报告
```

---

## ✅ 已完成工作

1. ✅ 设计完整的评测维度覆盖策略
2. ✅ 创建评测数据生成工具（支持 8 大类测试场景）
3. ✅ 创建评测执行工具（支持自动运行和报告生成）
4. ✅ 编写快速开始指南
5. ✅ 更新 README.md 添加评测系统说明
6. ✅ 测试验证工具正常运行

---

## 🎯 下一步建议

### 立即可做

1. **生成完整数据集**
   ```bash
   python scripts/generate_evaluation_dataset.py --category all
   ```

2. **运行评测**
   ```bash
   python scripts/run_evaluation.py --dataset evaluation_dataset
   ```

3. **分析结果**
   - 查看 `evaluation_report.md`
   - 找出误差较大的维度
   - 分析失败案例

### 持续改进

1. **添加真实数据**：用真实脱敏简历替换生成的模板简历
2. **人工标注**：为更多测试对添加人工评分作为 ground truth
3. **迭代优化**：根据评测结果调整评分逻辑和 prompts
4. **扩展覆盖**：添加更多特殊场景（如跨专业转型、Gap Year 等）

---

## 💡 关键设计亮点

### 1. 卷度感知评分
- 高卷度岗位（AI算法）：项目 > 实习品牌
- 低卷度岗位（运营）：实习品牌 > 项目
- 系统根据 JD 的卷度系数动态调整权重

### 2. 精英校识别
- 自动识别清北+HYPSM+Oxbridge
- 给予 +5 分 bonus（满分 105 分）

### 3. 双视角分析
- 显性 JD 要求：硬性技能匹配
- 隐含用人要求：推断 3 个隐含要求（过往经历、深度能力、潜在风险）

### 4. 润色边界控制
- **严禁编造事实**：只优化表达，不添加新信息
- **STAR 结构补全**：确保背景、任务、行动、结果完整
- **关键词嵌入**：自然融入 JD 核心词

---

## 📞 需要帮助？

- 查看完整策略：[docs/EVALUATION_DATASET_STRATEGY.md](docs/EVALUATION_DATASET_STRATEGY.md)
- 快速开始：[docs/EVALUATION_QUICKSTART.md](docs/EVALUATION_QUICKSTART.md)
- 项目 README：[README.md](README.md)
