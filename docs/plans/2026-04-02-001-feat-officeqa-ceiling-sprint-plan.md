---
title: "feat: OfficeQA Ceiling Sprint -- From 175 to 200+"
type: feat
status: active
date: 2026-04-02
---

# OfficeQA Ceiling Sprint -- From 175 to 200+

## Overview

v8 = 175.3 分（#3），距 #1（182.1）差 6.8 分（约 7-8 题）。目标不只是 #1，而是逼近天花板（200+）。基于 v5→v7→v8 的提升数据，聚焦最高 ROI 的改进。

## 版本演进数据

| Version | Score | Correct (est) | Key Change | Lift |
|---------|-------|---------------|------------|------|
| v5 | 152.2 | ~167 (68%) | prompt 重写 + skills 体系 | baseline |
| v7 | 171.3 | ~185 (75%) | openhands-sdk + SKILL.md 格式 | +19.1 |
| v8 | 175.3 | ~190 (77%) | 答案格式 + 搜索 cascade + 表格解析 | +4.0 |

## 剩余错题原因分析（~56 题，推测）

| 失败类型 | 估计数量 | 可修复性 |
|---------|---------|---------|
| Agent 超时/迭代耗尽未写 answer.txt | 8-12 | 高 |
| 搜索失败后放弃（空 answer.txt） | 5-8 | 高 |
| 复杂推理超出 qwen3-coder 能力 | 10-15 | 中（换模型） |
| 表格解析仍有错误 | 5-8 | 中 |
| 外部知识缺失 | 3-5 | 高 |
| 答案格式不匹配 | 3-5 | 中 |
| 视觉/图表题（不可解） | 5-8 | 低 |

## Implementation Units

### Unit 1: 兜底写入 + 错误恢复（预估 +8-13 题）

**Goal:** 确保 agent 在任何情况下都写 answer.txt，即使找不到确切答案

**Files:**
- Modify: `officeqa/skills/00_system_instructions/SKILL.md`

**Approach:**
- 在 Step 0（Setup）阶段立即写一个占位 answer.txt："0"
- 在工作流末尾添加强制检查："如果还没写 answer.txt，用你目前最好的猜测写入"
- 添加指令："如果搜索 3 次都找不到数据，基于你对 Treasury Bulletin 的知识给出最合理的估计值"
- 添加指令："宁可给一个合理的近似值，也不要留空文件"
- 添加时间管理指令："如果已经用了 30+ 迭代还没找到答案，立即用当前最佳推测写入"

### Unit 2: 减少无效迭代，更快切换策略（预估 +2-3 题）

**Goal:** Agent 不要在 grep 上浪费太多迭代

**Files:**
- Modify: `officeqa/skills/00_system_instructions/SKILL.md`

**Approach:**
- 修改搜索策略：grep 最多尝试 3 次（精确→关键词→同义词），之后必须切换到 Python 批量扫描
- 添加"快速失败"指令：如果 grep 返回 0 结果，不要换更多关键词，直接写 Python 扫描脚本
- 多文件策略从"3+ 年才用"改为"2+ 年就用"

### Unit 3: 扩展 domain_knowledge（预估 +2-3 题）

**Goal:** 覆盖更多可能被问到的外部知识

**Files:**
- Modify: `officeqa/skills/04_domain_knowledge/SKILL.md`

**Approach:**
- 补充更多 Treasury Secretaries（1965-2025）
- 补充更多历史事件：9/11、2008 金融危机、COVID-19
- 补充更多金融术语：TIPS、STRIPS、savings bonds、agency securities
- 补充重要的制度变化日期：Bretton Woods 结束（1971）、社会保障改革（1983）等

### Unit 4: 模型 A/B 测试准备（预估 +5-10 题）

**Goal:** 准备用更强模型做一次提交，验证正确率提升

**Files:**
- Modify: `officeqa/arena.yaml`（model 字段）

**Approach:**
- 候选模型列表（按 ROI 排序）：
  1. `anthropic/claude-sonnet-4.6` — 最强推理，$3/$15，成本高但正确率可能 +10%
  2. `google/gemini-2.5-flash-preview` — 快速廉价，可能和 qwen3-coder 差不多
  3. `deepseek/deepseek-r1` — 强推理，成本中等
- 策略：用 1 次提交测试 claude-sonnet-4.6（最大可能提升），如果正确率明显上升但成本太高再考虑折中模型
- 注意：模型切换只改 arena.yaml 的 model 字段，不影响 skills

### Unit 5: 研究报告最终版

**Goal:** 准备最终研究报告以提交

**Files:**
- Modify: `docs/research-proposal.md`
- Reference: `docs/technical-overview.md`

**Approach:**
- 整合所有版本的分数演进数据
- 突出跨领域迁移（SEO→QA）的研究价值
- 包含失败分析和改进策略的具体数据
- 最终提交到 Discord #proposals channel

## 提交策略（明天 3 次配额）

| 提交 | 内容 | 目标 |
|------|------|------|
| #1 早 | v9: Unit 1+2+3（兜底+恢复+知识） | 验证改进效果，预期 180+ |
| #2 中 | v10: 如果 v9 有效，微调；如果无效，回退 v8 配置 | 巩固或修复 |
| #3 晚 | v11: Unit 4 模型 A/B（如果前两次已到 180+）或安全网 | 冲击最高 |
