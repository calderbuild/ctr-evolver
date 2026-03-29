---
title: Demo Materials for Competition Submission
type: docs
date: 2026-03-29
---

# Demo Materials for Competition Submission

## Goal

为 Sentient Arena 竞赛提交创建 Demo 材料，补充研究提案，让评委快速理解系统能力。

## Scope

**In**: 架构图、技能对比表、title before/after 示例、成本分析可视化
**Out**: Streamlit 交互 demo（时间不够）、视频录制（无法重跑 sandbox 进化）

## 现有素材

研究提案 (`docs/research-proposal.md`) 已包含：
- 6.2 节技能进化表（种子 7 → 进化 18）
- 6.5 节成本分析表
- 3.1 节 ASCII 架构图
- 5.3 节 LLM-as-Judge 前后对比表

本地数据：
- 35 个 SKILL.md 文件（7 种子 + 18 进化，含多版本）
- `skills/frontier/metrics.json`（Pareto 指标）
- `data/checkpoint.json`（10 步进化历史）

## Tasks

### 1. 架构 Mermaid 图

文件：`docs/demo/architecture.md`

将 ASCII 架构图升级为 mermaid flowchart：
- 5 个核心模块：Executor / Evaluator / Proposer / Generator / Frontier
- 双评估路径（CTR + LLM-as-Judge）高亮
- 数据流箭头标注（GSC data → opportunities → interventions → evaluation → frontier → new skill）
- 进化循环用虚线框标注

验收：mermaid 语法正确，GitHub 可直接渲染。

### 2. 技能对比表

文件：`docs/demo/skill-comparison.md`

Markdown 表格展示 26 个技能（7 种子 + 19 unique 进化）：
- 列：技能名 | 类型（seed/evolved）| 版本数 | 策略摘要（一句话）| Pareto 指标
- 按类别分组：Intent Confirmation / Brand Reinforcement / Value Proposition / Social Proof / Other
- 用 metrics.json 数据填充 Pareto 指标列
- 标注 curiosity_gap 是唯一有 coverage 的技能

数据来源：遍历 `skills/*/v1/SKILL.md` 提取策略摘要 + `metrics.json`。

验收：涵盖所有 26 个技能，数据与 metrics.json 一致。

### 3. Before/After Title 示例

文件：`docs/demo/title-examples.md`

抽样 3 个进化技能，展示对同一查询（"meetspot"）生成的 title 差异：

选择标准：
- 1 个 seed（curiosity_gap）— 唯一有评估数据的
- 1 个进化技能（intent_match_confirmation）— 研究提案重点讨论的
- 1 个进化技能（brand_value_reinforcement 或 direct_value_proposition）— 代表另一类策略

每个技能展示：
- 原始 title（meetspot 当前的）
- 技能生成的 title
- 技能核心策略（一句话）
- 字数/格式对比

方法：读取 SKILL.md 的 example 部分，或用现有 executor 代码在本地跑一次生成。如果 SKILL.md 自带 before/after 示例则直接用。

验收：3 组清晰的对比，能直观看出不同策略的差异。

### 4. 进化时间线图

文件：`docs/demo/evolution-timeline.md`

用 Mermaid gantt 或简单 Markdown 表格展示 10 步进化过程：
- 每步：步号 | 日期 | 评估数 | 生成的新技能 | 关键事件
- 标注关键转折点（Step 1-3 无 LLM Judge → Step 4+ 有 LLM Judge）
- 从 checkpoint.json 和 research-proposal 数据填充

验收：10 步完整记录，与 checkpoint 数据一致。

### 5. 成本分析可视化

已在研究提案 6.5 节有完整表格。Demo 版本补充：
- 与商业 SEO 工具月费对比（Ahrefs $99/mo, SEMrush $119/mo）
- 单次优化成本 breakdown 饼图（用 mermaid pie）
- 强调 $47.50 / 10 步 / 25 技能的性价比

文件：添加到 `docs/demo/cost-analysis.md`

### 6. 汇总 Demo 入口

文件：`docs/demo/README.md`

一页索引，链接到所有 demo 材料 + 研究提案 + GitHub repo。供评委快速导航。

## 不做的事

- 不做 Streamlit 交互 demo（时间有限，Markdown + Mermaid 足够）
- 不重跑进化循环（sandbox 数据已足够）
- 不做视频录制（文字 + 图表更容易评审）
- 不做 matplotlib 脚本（Mermaid 在 GitHub 直接渲染，零依赖）

## Acceptance Criteria

- [x] 架构 mermaid 图可在 GitHub 正确渲染
- [x] 技能对比表覆盖全部 26 个技能
- [x] 3 组 before/after title 对比清晰直观
- [x] 所有数据与 research-proposal.md 一致
- [x] Demo 入口页链接完整可访问
