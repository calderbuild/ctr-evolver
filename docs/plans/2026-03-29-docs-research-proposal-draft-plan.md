---
title: Research Proposal Draft and Demo Preparation
type: docs
date: 2026-03-29
---

# Research Proposal Draft and Demo Preparation

## Current State

竞赛还剩 6 天（04-04 截止）。工程完成度已足够支撑研究提案：
- 10 步进化循环完成
- 25 个技能（7 原始 + 18 进化），35 个 SKILL.md 版本
- LLM-as-Judge 评估器工作正常
- `curiosity_gap` 是唯一被试用的技能（lift=0.36, win=0.80）
- 其他技能因 meetspot 只有 1 个 opportunity 无法 round-robin 到

## Key Insight for Proposal

**不要掩盖失败，把它变成研究贡献。**

"进化循环跑通了，但 meetspot 数据太稀疏导致只有一个技能被试用" -- 这本身就是一个有价值的发现。论文可以讨论：
1. LLM-as-Judge 成功解决了"无评估信号"问题（evaluated_count 从 0 到 10）
2. 但暴露了新问题：单 opportunity 站点无法产生多技能竞争
3. 这说明自进化框架的有效性依赖于**任务多样性**，不只是信号密度

---

## Phase 1: 研究提案（2 天）

文件：`docs/research-proposal.md`

### 结构

- [x] **Abstract**（200 词）：问题 → 方案 → 发现
- [x] **1. Introduction**：自进化 AI 的应用，SEO 作为天然实验场
- [x] **2. Related Work**：EvoSkill、PromptBreeder、DSPy、LLM-as-Judge 文献
- [x] **3. System Design**
  - 架构图（5 模块：Executor / Evaluator / Proposer / Generator / Frontier）
  - 技能表示（SKILL.md 版本化文件）
  - 双评估路径（CTR + LLM-as-Judge）
- [x] **4. The Sparse Signal Challenge**
  - meetspot 数据分析表：144 行 / 61 天 / ~2 impressions/天
  - 统计评估不可能性的数学推导
  - 对比大型站点需求
- [x] **5. LLM-as-Judge as Proxy Evaluator**
  - 设计：5 维度结构化 rubric（关键词相关性、点击吸引力、长度质量、意图匹配、改进度）
  - 结果：evaluated_count 0 → 10，curiosity_gap 获得 win_rate=0.80
  - 讨论：代理信号 vs 真实信号的差异，reward hacking 风险
- [x] **6. Experiments & Results**
  - 数据表：进化步数、技能数量、Pareto metrics
  - curiosity_gap 的评估数据（唯一有 coverage 的技能）
  - 进化生成技能的质量分析（抽样 3 个比较）
  - 失败分析：为什么其他技能没被试用（单 opportunity 瓶颈）
- [x] **7. Discussion: Three Official Directions**
  - 7.1 AI Self-improvement：框架设计模式分析（vs 原始 EvoSkill coding benchmark）
  - 7.2 Transfer Learning：SEO → Office QA 迁移可行性（共享哪些模块，领域特定部分）
  - 7.3 Automatic Evaluation：LLM-as-Judge 作为通用方案，适用场景和局限
- [x] **8. Conclusion & Future Work**

### 数据需求

已有本地数据（之前 export 过）：
- `skills/frontier/metrics.json`
- `data/checkpoint.json`
- `data/interventions.jsonl`
- `data/evolution_memory.json`
- `skills/*/v*/SKILL.md`

不需要再从 sandbox 拉。

---

## Phase 2: Demo 材料（1 天）

- [ ] CLI 进化过程的 terminal 录屏或日志截图
- [ ] 技能列表对比表（原始 7 个 vs 进化后 25 个）
- [ ] 抽样 3 个进化技能的 before/after title 对比
- [ ] 架构 mermaid 图
- [ ] 成本分析：10 步 x ~$4/步 = ~$40 total

---

## Phase 3: 提交准备（0.5 天）

- [ ] 最终审读
- [ ] 所有材料 commit + push 到 GitHub
- [ ] 提交到竞赛平台

---

## Acceptance Criteria

- [ ] 研究提案 >= 2000 词
- [ ] 覆盖全部三个官方研究方向
- [ ] 包含数据驱动的实验结果
- [ ] 有清晰的架构图

## Timeline

| 日期 | 任务 |
|------|------|
| 03-29 ~ 03-30 | 研究提案初稿 |
| 03-31 | Demo 材料 + 润色 |
| 04-01 | 提交准备 |
| 04-02 ~ 04-04 | Buffer |
