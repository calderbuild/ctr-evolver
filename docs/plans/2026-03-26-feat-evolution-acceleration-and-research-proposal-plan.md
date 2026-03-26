---
title: Evolution Acceleration + Research Proposal
type: feat
date: 2026-03-26
---

# Evolution Acceleration + Research Proposal

## Overview

进化循环已在 Daytona 跑了 19 步，但 **0 次有效评估** -- meetspot 流量太低（61 天 144 行，~10 impressions/query），所有 intervention 都返回 `insufficient_data`。Pareto frontier 冻结在 (0,0,0)，技能进化完全停滞。

竞赛还剩 9 天（截止 2026-04-04）。官方明确说："排名第四但拥有开创性研究提案的团队，可能会击败排名第一的团队获得冠军"。本计划两线并行：让进化循环真正运转 + 写出高质量研究提案。

## Problem Analysis

### 为什么进化循环在空转

代码分析（详细数据来源：codebase-analyzer agent 报告）：

| 问题 | 位置 | 影响 |
|------|------|------|
| Gate 3: `after_impressions >= 10` | evaluator.py:116 | meetspot 单 query 总 impressions 才 ~10，无法通过 |
| Gate 4: `before/after >= 30` 才做 z-test | evaluator.py:56 | 永远不会达到统计显著性 |
| `insufficient_data` 不进入失败分析 | proposer.py:37 只看 `failure`/`inconclusive` | proposer 看不到真实问题 |
| 按 page+query 聚合评估 | evaluator.py:95-100 | 粒度太细，数据更碎片化 |
| 7 天等待期 | evolution.py:373 | 9 天内最多只能评估 1 轮 |
| 技能生成基于空信号 | proposer.py 每步调 Sonnet 但无数据 | 纯烧 API credits |
| 3 个目标 query 质量差 | `https //meet-com...`、`site:onrender.com` | 不是真实用户意图 |

### 竞赛评判框架

来源：`cohort0.md` 启动仪式笔记

**核心考题**：Databricks Office QA Benchmark（SEC filings QA）
**评判方式**：综合评价 = 排行榜分数 + 研究提案质量
**官方高优研究方向**：
1. **AI Self-improvement 评估** -- 比较 GAPA、Evolver、EVO Skills 等框架的设计模式
2. **Transfer Learning** -- 定制化 agent 能否跨域迁移
3. **Automatic Evaluation** -- 如何在运行中自动生成评估标准

我们的 SEO 自进化 agent 直接命中方向 1 和 3，间接涉及方向 2。

---

## Proposed Solution

### 两线并行

**Line A: Evolution Acceleration（工程，2 天）**
让进化循环在 9 天内产生真实的 evaluate → evolve 循环，哪怕结果不显著。

**Line B: Research Proposal（写作，3 天）**
将 SEO agent 作为案例，产出高质量研究提案覆盖全部三个官方方向。

### Line A: Evolution Acceleration

#### A1. LLM-as-Judge 代理评估器（核心创新）

**动机**：真实 CTR 数据 7 天才有、且量不够。但 LLM 可以即时评估 title/description 质量作为代理信号。

**实现**：新增 `seo_agent/llm_evaluator.py`：
- 输入：原始 title/desc + 生成的 title/desc + query + position
- LLM（Haiku，成本低）基于 SEO 最佳实践打分 0-10，评估维度：
  - 关键词相关性
  - 点击吸引力（好奇心缺口、数字、情感词）
  - 长度适当性（50-60 chars）
  - 搜索意图匹配
- 输出：score + reasoning

**与真实 CTR 的关系**：
- LLM score 作为即时代理信号驱动进化
- 真实 CTR 作为长期验证信号（如果有足够数据）
- 研究提案中分析两者的相关性/差异

**研究价值**：直接对标官方方向 3（Automatic Evaluation）-- 展示如何在稀疏数据环境下用 LLM 自动生成评估标准。

**文件变更**：
- 新增 `seo_agent/llm_evaluator.py`
- 修改 `engine/evolution.py`：step() 中加入 LLM 评估路径
- 修改 `engine/frontier.py`：接受 LLM score 作为新的优化维度

#### A2. 降低真实数据评估门槛

**变更**：
- `evaluator.py:116`：impressions 要求 10 → 3
- `evaluator.py:56`：z-test 要求 30 → 5（标注为"方向性结果"）
- `evolution.py`：等待期 7 天 → 1 天
- `evaluator.py`：新增 page-level 聚合模式（不按 query 拆分）

#### A3. 清理数据质量

- `opportunity.py`：排除 `site:` 操作符 query 和 URL-as-query 模式
- 重置 sandbox 的 checkpoint 和 interventions（从 step 1 重新开始干净数据）

#### A4. 进化效率优化

- `proposer.py`：当 `evaluated_count == 0` 且无 LLM 评估时跳过 Sonnet 调用（省钱）
- `evolution.py`：让 `insufficient_data` 状态也进入失败分析流程

### Line B: Research Proposal

#### B1. 论文结构

标题（暂定）：**"Self-Evolving SEO Agents: Lessons from Sparse-Signal Skill Evolution with LLM-as-Judge"**

结构：
1. **Introduction**: 自进化 AI 的愿景 vs 现实挑战
2. **Framework**: EvoSkill 在 SEO 领域的应用 -- 架构、技能表示、进化机制
3. **Challenge: Sparse Signals**: 真实业务中反馈信号的稀缺性（7 天延迟、低流量、噪声）
4. **Innovation: LLM-as-Judge**: 用 LLM 作为代理评估器加速进化循环
5. **Experiments**:
   - LLM score vs 真实 CTR 的相关性分析
   - 进化曲线（技能 fitness 随迭代变化）
   - Pareto frontier 的动态变化
6. **Transfer Discussion**: 框架从 SEO → Office QA 的迁移可行性分析
7. **Automatic Evaluation**: 如何让 agent 自己决定评估标准
8. **Conclusion + Future Work**

#### B2. 对标三个官方方向

| 方向 | 我们的贡献 |
|------|-----------|
| AI Self-improvement 评估 | 实证数据：19 步真实进化 + LLM 评估加速后的对比 |
| Transfer Learning | 分析 EvoSkill 的 SEO 实现 vs 原始 coding 实现的架构差异，讨论迁移成本 |
| Automatic Evaluation | LLM-as-Judge 作为自动评估方案，解决稀疏数据场景 |

#### B3. Demo 准备

- 进化过程的可视化（技能 fitness 曲线、Pareto frontier 变化）
- 前后对比：原始 title vs 进化后 title
- 成本分析：每步进化的 API 费用

---

## Acceptance Criteria

### Line A（工程）
- [ ] `llm_evaluator.py` 实现并通过语法检查
- [ ] 进化循环能在无真实 CTR 数据时通过 LLM score 完成 evaluate → evolve
- [ ] Pareto frontier 出现非零 metrics
- [ ] 至少产生 1 个通过进化生成的新技能
- [ ] Sandbox 中重新运行 5+ 步并验证 checkpoint

### Line B（研究）
- [ ] 研究提案 markdown 完成，覆盖全部三个官方方向
- [ ] 包含实验数据和可视化
- [ ] Demo 脚本或 Streamlit 准备

---

## Implementation Phases

### Phase 1: LLM-as-Judge + 门槛调整（Day 1-2）

优先级最高，解锁进化循环。

1. 实现 `seo_agent/llm_evaluator.py`
2. 修改 evaluator.py 降低门槛
3. 修改 opportunity.py 清理 query 质量
4. 修改 evolution.py 集成双评估路径
5. 本地验证 → push → sandbox pull → 重新启动进化

### Phase 2: 数据收集（Day 2-5）

进化循环持续运行，收集数据：
- LLM 评估分数分布
- 技能 fitness 变化
- 新技能生成记录
- 本地每天同步最新 GSC 数据到 sandbox

### Phase 3: Research Proposal（Day 3-7）

基于收集到的数据写研究提案：
- 框架分析
- 实验结果
- 跨域讨论

### Phase 4: Demo + Polish（Day 7-9）

- 可视化
- Presentation 准备
- 最终提交

---

## Risk Analysis

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| LLM-as-Judge 评分不稳定 | 中 | 进化方向随机 | 多次评分取均值；用结构化 rubric |
| API credits 不够 | 中 | 无法完成进化 | Haiku 评估（$1/M）；跳过无数据步 |
| 真实 CTR 数据始终为零 | 高 | 无法做 LLM vs CTR 相关性 | 用历史 CTR 数据做回测代替 |
| 研究提案深度不够 | 低 | 评分受限 | 聚焦 Automatic Evaluation 方向，这是我们最有说服力的贡献 |

## Cost Estimate

| 项目 | 估算 |
|------|------|
| LLM 评估（Haiku, ~100 evaluations） | ~$1 |
| 进化步（Sonnet 分析 + Haiku 评估） | ~$4/step |
| 预计运行 10-15 步 | ~$40-60 |
| 剩余预算 | ~$72 |
| 够用 | Yes |

## Dependencies

- Daytona sandbox 持续可用
- OpenRouter API credits 剩余 > $50
- GSC token 未过期
- 本地 GSC 数据定期同步到 sandbox

## References

- EvoSkill 框架: https://github.com/sentient-agi/EvoSkill
- 竞赛详情: cohort0.md（启动仪式笔记）
- Self-Evolving Agent 论文: https://arxiv.org/abs/... (AgentEvolver, EvolveR)
- LLM-as-Judge: proxy evaluation for sparse-signal environments
- SEO CTR 因素: title length 50-60 chars, numbers, emotional words, curiosity gaps
