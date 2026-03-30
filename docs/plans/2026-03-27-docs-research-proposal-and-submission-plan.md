---
title: Research Proposal and Competition Submission
type: docs
date: 2026-03-27
---

# Research Proposal and Competition Submission

## Overview

工程全部完成。进化循环在 Daytona 正常运行（20+ 技能进化生成，LLM-as-Judge 评估器工作正常）。剩余 8 天聚焦竞赛交付物：研究提案 + Demo。

## Deliverables

### 1. 研究提案（docs/research-proposal.md）

**Title**: Self-Evolving SEO Agents: LLM-as-Judge for Sparse-Signal Skill Evolution

覆盖官方三个研究方向：
- AI Self-improvement 评估
- Transfer Learning
- Automatic Evaluation

**数据来源**（从 sandbox 拉取）：
- `data/checkpoint.json` -- 进化历史
- `skills/frontier/metrics.json` -- 各技能 Pareto metrics
- `skills/*/v*/SKILL.md` -- 全部进化技能内容
- `data/evolution_memory.json` -- 进化记忆
- `data/interventions.jsonl` -- 干预记录（含 LLM 评估分数）
- `evolution.log` -- 完整运行日志

### 2. Demo 材料

- 进化过程日志截图 / 录屏
- 技能 fitness 变化图（简单 matplotlib）
- 前后对比表（原始 title vs 各技能生成的 title）
- 架构图（已有 ASCII 版，可升级为 mermaid）

### 3. Solution Presentation

- 5 分钟 slides 或 markdown 演示
- 重点讲"为什么 LLM-as-Judge 是解决稀疏信号的正确方案"

---

## Tasks

### Phase 1: 数据导出（0.5 天）

- [ ] 从 sandbox 拉取所有进化数据到本地 `data/sandbox_export/`
- [ ] 整理 LLM 评分数据（从 interventions.jsonl 提取）
- [ ] 导出新进化技能到本地 `skills/`
- [ ] 统计：总步数、总技能数、各技能 metrics、API 消耗

### Phase 2: 研究提案写作（2 天）

- [ ] Abstract（200 词）
- [ ] Introduction：自进化 AI 的愿景 vs 现实
- [ ] Framework：EvoSkill for SEO 架构
- [ ] Challenge：稀疏信号问题分析（附真实数据）
- [ ] Innovation：LLM-as-Judge 方案
- [ ] Experiments：进化曲线、技能 metrics、评分分布
- [ ] Discussion：Transfer Learning + Automatic Evaluation
- [ ] Conclusion

### Phase 3: 可视化 + Demo（1 天）

- [ ] matplotlib 脚本：技能 fitness 随步数变化
- [ ] 前后对比表：每个技能的 title 示例
- [ ] 架构 mermaid 图
- [ ] 成本分析表

### Phase 4: 提交准备（0.5 天）

- [ ] 最终审读研究提案
- [ ] 打包所有材料
- [ ] 提交到竞赛平台

---

## Acceptance Criteria

- [ ] 研究提案 >= 2000 词，覆盖全部三个官方方向
- [ ] 包含 3+ 个数据驱动的图表/表格
- [ ] Demo 可在 5 分钟内展示完整进化流程
- [ ] 所有材料 push 到 GitHub repo

## Timeline

| Phase | 日期 |
|-------|------|
| 数据导出 | 03-27 |
| 研究提案 | 03-28 ~ 03-29 |
| 可视化 + Demo | 03-30 |
| 提交准备 | 03-31 |
| Buffer | 04-01 ~ 04-04 |
