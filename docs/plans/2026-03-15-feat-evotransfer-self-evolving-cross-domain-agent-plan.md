---
title: "EvoTransfer: Self-Evolving Agent with Cross-Domain Skill Transfer"
type: feat
date: 2026-03-15
---

# EvoTransfer: Self-Evolving Agent with Cross-Domain Skill Transfer

## Overview

构建一个自进化的文档推理 Agent，在 Sentient 的 EvoSkill 框架基础上实现两个核心创新：**多层级技能进化**（Parsing / Retrieval / Reasoning 三层分别进化）和**跨领域技能迁移**（自动识别通用技能并迁移到新文档领域）。同时覆盖官方三大研究方向中的两个（Self-Improvement + Transfer Learning），以研究提案的深度弥补排名差距。

### 产品愿景

**SkillForge** — "Enterprise Document AI that learns and transfers"
- 目标用户：拥有大量复杂文档的企业（金融、法律、合规、医疗）
- 核心痛点：现有 RAG/AI 方案不会随使用而改进，且无法跨文档类型迁移
- PMF 信号：Databricks OfficeQA Pro 论文表明，即使最强模型在企业文档推理上也仅达 ~48%，市场缺口巨大

---

## Problem Statement / Motivation

### 当前痛点

1. **Parsing 是最大瓶颈**：OfficeQA Pro 论文显示，使用 Databricks ai_parse_document 预解析可带来 16.1% 的平均性能提升。大多数团队会聚焦 reasoning，但 parsing 才是低垂的果实
2. **EvoSkill 仅在 reasoning 层进化**：当前 EvoSkill 在 OfficeQA 上从 60.6% 提升到 67.9%（+7.3%），但它把 parsing 当作固定前处理，没有将其作为可进化技能
3. **技能迁移未被系统研究**：EvoSkill 论文展示了 SealQA → BrowseComp 的零样本迁移（+5.3%），但缺乏系统性的迁移机制设计
4. **静态 benchmark 无法覆盖企业多样性**：每个企业的文档都不同，需要 Agent 能在新领域快速自适应

### 为什么这个方向有差异化

| 维度 | 大多数团队 | 我们 |
|------|-----------|------|
| 技术路径 | 直接用 EvoSkill 或纯 Prompt 优化 | 多层级进化 + 跨域迁移 |
| 研究方向 | 单一方向 | Self-Improvement + Transfer Learning |
| 产品潜力 | Hackathon demo | 可持续的企业 SaaS |
| 创新性 | 增量改进 | 架构级创新 |

---

## Proposed Solution

### 核心架构：三层进化 + 跨域迁移

```
                    ┌─────────────────────────────────────────┐
                    │           EvoTransfer Agent              │
                    │                                         │
                    │  ┌─────────┐ ┌──────────┐ ┌──────────┐  │
                    │  │ Parsing │ │Retrieval │ │Reasoning │  │
                    │  │ Skills  │ │ Skills   │ │ Skills   │  │
                    │  └────┬────┘ └────┬─────┘ └────┬─────┘  │
                    │       │           │            │         │
                    │  ┌────▼───────────▼────────────▼────┐   │
                    │  │        Skill Evolution Engine      │   │
                    │  │  (EvoSkill-inspired, multi-level)  │   │
                    │  └────────────────┬──────────────────┘   │
                    │                   │                       │
                    │  ┌────────────────▼──────────────────┐   │
                    │  │      Skill Transfer Protocol       │   │
                    │  │  (classify → adapt → validate)     │   │
                    │  └───────────────────────────────────┘   │
                    └─────────────────────────────────────────┘
```

### 三层技能进化

#### Layer 1: Parsing Skills（文档解析技能）
- 表格结构识别策略（嵌套表头、合并单元格、多列布局）
- 数值提取与归一化（百分比、货币、日期格式）
- 视觉元素处理（图表描述、页码定位）
- **进化方式**：对比不同 parsing 策略在子集上的准确率，选择最优策略组合

#### Layer 2: Retrieval Skills（检索技能）
- 基于问题类型的文档定位策略（时间范围查询 vs 跨文档聚合）
- 多版本文档去重与权威性排序
- 相关表格/段落的精准定位
- **进化方式**：评估检索召回率和精确率，进化检索策略

#### Layer 3: Reasoning Skills（推理技能）
- 数值计算与验证（交叉验证、单位换算）
- 多步推理链构建
- 答案置信度评估与自我修正
- **进化方式**：经典 EvoSkill 方式，基于错误分析进化推理 prompt

### 跨域迁移协议

```
Step 1: Skill Classification（技能分类）
  ├── Domain-General Skills（通用技能）
  │   - 表格解析、数值提取、多步推理
  │   - 这些技能在不同文档领域都有效
  └── Domain-Specific Skills（领域特定技能）
      - Treasury Bulletin 特有的表格格式、术语
      - 特定数据源的版本管理逻辑

Step 2: Transfer Adaptation（迁移适配）
  ├── 通用技能直接迁移，零修改
  ├── 领域技能通过 few-shot 适配到新领域
  └── 自动生成新领域的测试用例验证迁移效果

Step 3: Validation（验证）
  ├── 在新领域自动生成小规模 benchmark
  ├── 评估迁移后的性能基线
  └── 启动新领域的进化循环
```

---

## Technical Approach

### Phase 1: Foundation（第 1 周前半）

**目标**：搭建基础架构，跑通 OfficeQA baseline

- [ ] Fork EvoSkill 仓库，搭建本地开发环境
- [ ] 实现 OfficeQA 数据加载与评估 pipeline（使用 officeqa_pro.csv + reward.py）
- [ ] 用 Claude Code + OpenHands SDK 构建基础 Agent
- [ ] 跑通 baseline，记录初始准确率
- [ ] 使用 Databricks 提供的预解析数据（treasury_bulletins_parsed/）作为起点

**文件清单**：
- `agent/base_agent.py` — 基础 Agent 框架
- `agent/evaluator.py` — OfficeQA 评估脚本（封装 reward.py）
- `config/settings.yaml` — 模型、API key、参数配置
- `scripts/run_baseline.py` — baseline 运行脚本

**验收标准**：baseline 在 officeqa_pro.csv 上的准确率有可复现记录

### Phase 2: Multi-Level Skill Evolution（第 1 周后半 - 第 2 周前半）

**目标**：实现三层技能进化机制

- [ ] 定义 Skill 数据结构（SKILL.md + trigger metadata + helper scripts，复用 EvoSkill 格式）
- [ ] 实现 Parsing Skill 进化模块
  - 文档解析策略的 A/B 测试框架
  - 基于错误分析的解析策略生成器
- [ ] 实现 Retrieval Skill 进化模块
  - 问题分类器（时间查询/聚合查询/比较查询等）
  - 检索策略的自动优化
- [ ] 实现 Reasoning Skill 进化模块（复用/扩展 EvoSkill 核心逻辑）
- [ ] 实现 Pareto Frontier 管理器（跨三层维护最优技能组合）
- [ ] 在 officeqa_full.csv easy split 上进化，在 officeqa_pro.csv 上验证

**文件清单**：
- `skills/parsing/` — Parsing Skills 目录
- `skills/retrieval/` — Retrieval Skills 目录
- `skills/reasoning/` — Reasoning Skills 目录
- `evolution/proposer.py` — 失败分析与技能提案
- `evolution/skill_builder.py` — 技能构建器
- `evolution/frontier.py` — Pareto 前沿管理
- `evolution/orchestrator.py` — 多层级进化编排

**验收标准**：在 officeqa_pro.csv 上准确率 > baseline + 5%

### Phase 3: Cross-Domain Transfer（第 2 周后半）

**目标**：实现技能迁移机制并在第二个领域验证

- [ ] 实现 Skill Classifier（基于 LLM 的技能分类器）
  - 输入：一个 skill folder
  - 输出：domain-general / domain-specific 分类 + 理由
- [ ] 选择第二个文档领域用于迁移验证（候选：SEC 10-K filings、法律合同、医疗记录）
- [ ] 实现 Transfer Protocol
  - 通用技能零样本迁移
  - 领域技能 few-shot 适配
- [ ] 实现 Auto-Eval Generator（在新领域自动生成评估问题）
  - 从文档中抽取事实 → 生成问答对 → 自动验证
- [ ] 在新领域运行迁移实验，记录结果

**文件清单**：
- `transfer/classifier.py` — 技能分类器
- `transfer/adapter.py` — 技能适配器
- `transfer/auto_eval.py` — 自动评估生成器
- `experiments/transfer_results/` — 迁移实验结果

**验收标准**：迁移后在新领域的准确率显著高于 cold-start baseline

### Phase 4: Research Proposal & Demo（第 3 周）

**目标**：撰写研究提案，打磨 demo

- [ ] 撰写研究提案（markdown 格式），覆盖：
  - 多层级 vs 单层级技能进化的对比实验
  - 跨域迁移的成功率与失败模式分析
  - 技能可迁移性的定量指标
  - 与 EvoSkill baseline 的对比
- [ ] 构建 Demo 界面（Streamlit/Gradio）
  - 实时展示进化过程
  - 可视化技能库与迁移图谱
  - 交互式问答演示
- [ ] 最终在 officeqa_pro.csv 上的完整评估
- [ ] 准备 presentation slides

**文件清单**：
- `research/proposal.md` — 研究提案
- `demo/app.py` — Demo 应用
- `demo/visualizations.py` — 可视化组件
- `results/final_evaluation.json` — 最终评估结果

**验收标准**：Demo 可流畅运行；研究提案有数据支撑

---

## Alternative Approaches Considered

### 1. 纯 Prompt 优化 + Chain-of-Thought
- **否决原因**：天花板低，无创新性，大多数团队都会这么做

### 2. 纯 RAG 管线优化
- **否决原因**：只解决检索问题，不解决进化和迁移

### 3. 直接用 EvoSkill 不做修改
- **否决原因**：无差异化，且 EvoSkill 是 Sentient 自己做的，评委对它最熟悉

### 4. 综合三个方向（Self-Improvement + Transfer + Auto-Eval）
- **否决原因**：独立参赛工作量过大，不如深耕两个方向

---

## Acceptance Criteria

### Functional Requirements

- [ ] Agent 能在 OfficeQA Pro 上跑完全部 133 道题并生成评分
- [ ] 多层级进化机制能自动发现并构建新技能
- [ ] 技能分类器能正确区分通用/领域特定技能（准确率 > 80%）
- [ ] 迁移到新领域后准确率 > cold-start baseline

### Non-Functional Requirements

- [ ] 单次运行成本控制在合理范围（优先用 officeqa_full easy split 进化）
- [ ] 进化过程可复现（通过 git branch 管理技能版本）
- [ ] Demo 流畅可演示

### Quality Gates

- [ ] OfficeQA Pro 准确率 > EvoSkill baseline（67.9%）或有合理解释
- [ ] 研究提案有至少 3 组对比实验数据
- [ ] 代码可在 Daytona 沙箱中运行

---

## Success Metrics

| 指标 | 目标值 | 衡量方法 |
|------|--------|----------|
| OfficeQA Pro 准确率 | > 65%（理想 > 70%） | reward.py 评分 |
| 多层级 vs 单层级提升幅度 | > 3% | 对照实验 |
| 跨域迁移后准确率提升 | > cold-start +10% | 新领域 auto-eval |
| 研究提案质量 | 有数据支撑的创新性发现 | 评委评价 |
| Demo 完整度 | 端到端可演示 | 现场演示 |

---

## Dependencies & Prerequisites

### 外部依赖

- Sentient 提供的 API credits（Discord 中获取）
- OpenHands SDK
- Databricks OfficeQA 数据集（已开源）
- Claude API（用于进化中的 LLM 调用）
- 第二领域文档数据集（SEC 10-K filings 可从 EDGAR 免费获取）

### 技术栈

- Python 3.11+
- OpenHands SDK + Claude Code
- EvoSkill 框架（fork 并扩展）
- Streamlit/Gradio（Demo）
- Git worktrees（技能版本管理）

---

## Risk Analysis & Mitigation

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| API 成本过高 | 无法充分迭代 | 中 | 先用小子集迭代；用开源模型（Qwen 2.5）做初步筛选 |
| 多层级进化收益不明显 | 研究结论弱化 | 中 | 即使负面结果也有研究价值；聚焦最有收益的层级 |
| 跨域迁移效果差 | 迁移故事不完整 | 中 | 选择与 Treasury Bulletins 相似的金融文档领域 |
| 独立作战工作量过大 | 无法按时完成 | 高 | 严格分阶段，Phase 1-2 是核心，Phase 3-4 可降级 |
| EvoSkill 代码不稳定 | 构建耗时 | 低 | 核心逻辑自己实现，只参考 EvoSkill 的 Skill 格式 |

### 降级方案

如果时间不够：
1. **最低交付**：Phase 1 + Phase 2 部分 + 研究提案 → 有 baseline 提升 + 有创新方向
2. **标准交付**：Phase 1 + Phase 2 + Phase 3 部分 → 有完整进化 + 初步迁移验证
3. **完整交付**：全部 4 个 Phase → 最佳冲奖状态

---

## Research Proposal Outline

### Title
"Multi-Level Skill Evolution and Cross-Domain Transfer for Grounded Document Reasoning"

### Key Research Questions

1. **层级解耦**：在文档推理任务中，parsing / retrieval / reasoning 三层分别进化，与端到端单层进化相比，哪种策略更有效？
2. **技能可迁移性**：什么特征决定了一个进化出的技能是否可以跨领域迁移？
3. **进化效率**：多层级进化是否能以更少的迭代次数达到更高的准确率？
4. **最优粒度**：技能的最优粒度是什么？太粗失去针对性，太细难以复用

### Experiments Design

| 实验 | 对照组 | 实验组 | 指标 |
|------|--------|--------|------|
| Exp 1: 单层 vs 多层 | EvoSkill（仅 reasoning 层进化） | EvoTransfer（三层进化） | OfficeQA Pro 准确率 |
| Exp 2: 层级贡献度 | 无进化 baseline | 分别只进化 P / R / R 层 | 各层独立贡献 |
| Exp 3: 跨域迁移 | Cold-start Agent 在新领域 | 迁移 OfficeQA 通用技能后 | 新领域准确率 |
| Exp 4: 进化效率 | EvoSkill N 轮迭代 | EvoTransfer N 轮迭代 | 收敛速度 |

---

## References & Research

### Internal References
- EvoSkill 框架：https://github.com/sentient-agi/EvoSkill
- OfficeQA 数据集：https://github.com/databricks/officeqa
- OpenHands SDK：https://github.com/All-Hands-AI/OpenHands

### External References
- [OfficeQA Pro 论文](https://arxiv.org/abs/2603.08655) — Databricks AI Research
- [EvoSkill 论文](https://arxiv.org/abs/2603.02766) — Sentient + Virginia Tech
- [Hermes Agent Self-Evolution](https://github.com/NousResearch/hermes-agent-self-evolution) — NousResearch, ICLR 2026 Oral
- [EvoAgentX](https://github.com/EvoAgentX/EvoAgentX) — Self-Evolving Agent Ecosystem
- [Darwinian Evolver](https://github.com/NousResearch/hermes-agent/issues/336) — Imbue, 95.1% on ARC-AGI-2
- [Anthropic Demystifying Evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) — Agent 评估最佳实践
- [Self-Evolving Agents Survey](https://github.com/EvoAgentX/Awesome-Self-Evolving-Agents)

### Competition Context
- Sentient Arena Cohort 0：126 人入选，$45K 奖金池
- 评判标准：综合评价（Holistic），排行榜分数 + 研究提案质量
- 官方推荐：使用 OpenHands / CodeX / Aider 作为 Skills 整合进自定义 Agent
