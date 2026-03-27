---
title: Fix Skill Adoption + Research Proposal + Demo
type: feat
date: 2026-03-27
---

# Fix Skill Adoption + Research Proposal + Demo

## Overview

进化循环已经能跑了（LLM-as-Judge 工作正常，9 步完成），但有两个问题需要修：
1. 新技能被生成但不被使用（active_skills 始终只有 curiosity_gap）
2. 只有 1 个 query（meetspot）被循环处理

修完后重点转向竞赛交付物：研究提案 + Demo。

---

## Phase 1: Fix Skill Adoption Bug（0.5 天）

### 问题

`frontier.update()` 在 `step()` 中被调用时，传入的 LLM 评估 metrics 正确更新到 `self.metrics`，但 Pareto dominance 在所有技能 metrics 接近零时无法区分。同时 `active_skills.json` 在 sandbox 中被 `_save_active()` 覆盖，但 `_run_burst()` 的 intervention 生成代码读的是 `executor.list_active_skills()` 而非 frontier 的 active list。

### 修复

- [ ] `engine/evolution.py` 的 `_run_burst()` 中：intervention 生成时使用 `self.frontier.get_active()` 的技能名，而非 `executor.list_active_skills()`
- [ ] 确认 `frontier.update()` 被调用后 `active_skills.json` 包含新技能
- [ ] 如果所有技能 metrics 相近（Pareto 无法区分），改用 composite score 排序保留所有技能

### 验证

`active_skills.json` 在进化后包含 >1 个技能，且不同步骤使用不同技能。

---

## Phase 2: 扩展 Position Range 和 Query 池（0.5 天）

### 问题

当前 meetspot 站点只有 1 个非垃圾 query（`meetspot`），进化循环每步都在对同一个 query 生成 intervention。没有多样性。

### 修复

- [ ] `opportunity.py`：放宽 `position_range` 默认值到 `(1, 50)`（CLI 已传但函数签名默认 `(4, 15)`）
- [ ] `evolution.py`：放宽 `ctr_threshold` 到 1.0（不过滤 CTR 高于 baseline 的页面）
- [ ] 验证修改后能找到 3+ 个 opportunity

---

## Phase 3: Research Proposal（2 天）

### 结构

文件：`docs/research-proposal.md`

**Title**: Self-Evolving SEO Agents: LLM-as-Judge for Sparse-Signal Skill Evolution

**Sections**:

1. **Abstract**（200 词）
   - 问题：真实业务中反馈信号稀疏，传统统计评估不可行
   - 方案：LLM-as-Judge 代理评估 + EvoSkill 自进化框架
   - 结果：从 0 次有效评估到每步 6-9 次评估，成功生成新技能

2. **Introduction**
   - AI Self-improvement 的愿景 vs 现实挑战
   - SEO CTR 优化作为自进化的天然场景
   - 竞赛对标：覆盖全部三个官方研究方向

3. **Framework: EvoSkill for SEO**
   - 架构图（现有 CLAUDE.md 中的 ASCII 图）
   - 技能表示（SKILL.md 版本化文件）
   - 进化机制（Proposer -> Generator -> Evaluator -> Frontier）
   - 与原始 EvoSkill（coding benchmarks）的差异

4. **Challenge: Sparse Feedback Signals**
   - meetspot 数据分析：144 行/61 天、~10 impressions/query
   - 统计评估的数学不可能性（需要 30+ impressions per window）
   - 对比大型站点（成千上万 impressions）
   - 通用 insight：很多真实业务面临同样的稀疏信号问题

5. **Innovation: LLM-as-Judge**
   - 动机：即时评估代替 7 天等待
   - 实现：结构化 rubric（5 维度 0-10 分）
   - 效果：evaluated_count 从 0 跃升到 6-9
   - 讨论：代理信号 vs 真实信号的偏差风险
   - 防 reward hacking：多维度评估、随机化

6. **Experiments**
   - 进化前/后对比（evaluated_count, 新技能数量）
   - LLM 评分分布
   - Pareto frontier 变化
   - 成本分析：每步 API 费用

7. **Discussion: Transfer & Automatic Evaluation**
   - **Transfer Learning**：SEO -> Office QA 迁移可行性分析
     - 共享架构（Proposer/Generator/Evaluator 独立于领域）
     - 领域特定部分（scorer 函数、skill 模板）
   - **Automatic Evaluation**：LLM-as-Judge 作为通用方案
     - 适用场景：任何反馈延迟或稀疏的领域
     - 局限性：LLM 偏好 vs 真实用户偏好

8. **Conclusion + Future Work**

### 数据需求

- [ ] 从 sandbox 拉取：checkpoint history, evolution_memory.json, interventions.jsonl, skills/
- [ ] 整理 LLM 评分数据（需要从 log 或 interventions 提取）

---

## Phase 4: Demo 准备（1 天）

- [ ] 进化过程的 terminal 录屏或日志截图
- [ ] 技能 fitness 变化的简单可视化（matplotlib 脚本）
- [ ] 前后对比表：原始 title vs 进化后 title（从 interventions.jsonl 提取）
- [ ] 成本统计：总 API 消耗

---

## Acceptance Criteria

- [ ] 进化循环使用 2+ 个不同技能
- [ ] 研究提案完成，覆盖 3 个官方方向
- [ ] 有实验数据支撑论点
- [ ] Demo 材料就绪

## Timeline

| Phase | 时间 | 截止 |
|-------|------|------|
| Phase 1: Fix skill adoption | 0.5 天 | 03-27 |
| Phase 2: Expand query pool | 0.5 天 | 03-27 |
| Phase 3: Research proposal | 2 天 | 03-29 |
| Phase 4: Demo | 1 天 | 03-30 |
| Buffer + polish | 5 天 | 04-04 |
