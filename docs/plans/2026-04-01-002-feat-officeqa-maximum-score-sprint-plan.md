---
title: "feat: OfficeQA Maximum Score Sprint -- 3-Day Push to Theoretical Ceiling"
type: feat
status: active
date: 2026-04-01
---

# OfficeQA Maximum Score Sprint

## Overview

从 #7（152.2 分，v5 opencode）冲击理论最高分。不只是超过当前 #1（182.1），而是逼近 246 题全对的天花板。3 天剩余（Apr 2-4），每天 3 次提交，共 9 次迭代机会。

## Problem Frame

**评分公式**:
```
Score = total_correct × (1 + cost_adj + time_adj)
```
- cost_adj, time_adj 是 log2 对数调整，有上下限 cap
- 理论天花板：246 × ~1.1 ≈ 270（全对 + 极低成本/延迟）
- 当前 #1（182.1）≈ 200 correct × 0.91 multiplier
- 我们 v5（152.2）= 167 correct × 0.91 multiplier（68% 正确率）

**核心差距分析**（从 167 到 230+ 正确）:

| 失败类型 | 估计影响题数 | 可修复性 | 改进策略 |
|---------|------------|---------|---------|
| 表格列对齐/单位错误 | ~25 题 | 高 | 强化 parse_val + 列计数逻辑 |
| 文件定位失败 | ~15 题 | 高 | 更完善的日期→文件映射 + 全月扫描 |
| 复杂计算错误 | ~10 题 | 中 | 公式库 + 更多 edge case 处理 |
| 答案格式不匹配 | ~10 题 | 高 | 基于 reward.py 精确匹配规则优化 |
| Agent 超时/迭代耗尽 | ~8 题 | 中 | 更高效的搜索策略 |
| 视觉/图表题 | ~5 题 | 低 | 文本近似 + 跳过不可解题 |
| 外部知识缺失 | ~6 题 | 中 | 扩充 domain_knowledge |

## Requirements Trace

- R1. 总分 >200（超越当前所有队伍）
- R2. 正确率 >85%（210+/246）
- R3. 效率乘数 >0.92（低成本 + 快速度）
- R4. 最大化每次提交的信息收益（9 次提交 = 9 次学习机会）
- R5. 可复现、可回滚的迭代流程

## Scope Boundaries

- **In**: prompt 优化、skills 重写、模型选择实验、MCP server 工具、答案格式精调、搜索策略优化
- **Out**: 修改 harness 源码、预计算答案（违规）、训练/微调模型
- **Non-goal**: 解决纯视觉题（~2-3% 题目，文本无法解答）

## Key Technical Decisions

### D1: 保持 openhands-sdk harness
**理由**: Top 4 全用它，天花板已验证到 182+。v7 刚提交，等结果确认 harness 切换有效。

### D2: 模型保持 qwen3-coder（可能切换）
**理由**: 免费模型，成本 $0/task → 效率乘数最大化。但如果正确率瓶颈在模型能力，考虑切换到 claude-sonnet-4.6 或 deepseek-r1（需 A/B 测试确认 ROI）。
**决策点**: v7 结果出来后，如果正确率 <75%，测试更强模型。

### D3: Prompt 极简 + Skills 丰富策略
**理由**: MiniMax M2.5（评估模型）上下文 205K tokens，skills 作为参考材料不占主 prompt。系统指令 <500 tokens 控制输出量。

### D4: 基于 reward.py 反向优化答案格式
**理由**: 评分逻辑有明确规则（base number 比较、年份过滤、文本 overlap），可以精确匹配。Agent 输出必须遵循这些规则。

### D5: 每次提交前本地 smoke test 5 道样题
**理由**: 不浪费提交配额在明显有 bug 的版本上。用 `arena test --n 5` 验证。

## Open Questions

### Resolved During Planning

- **openhands-sdk 是否正确加载 SKILL.md?** 已验证（commit c386659 修复了格式问题）
- **MAX_ITERATIONS 50 够用吗?** v5 用 30 就到了 68% 正确率，50 应该够绝大多数题

### Deferred to Implementation

- **qwen3-coder vs claude-sonnet-4.6 哪个正确率更高?** 需要 v7 结果 + A/B 测试
- **MCP filesystem server 是否有净收益?** 需要实验（初始化开销 vs 检索精度）
- **哪些具体题目失败了?** 需要 per-question 结果分析（如果 arena 提供）

## High-Level Technical Design

> *This illustrates the intended approach and is directional guidance for review, not implementation specification.*

```
┌─ Phase 1: 诊断（Apr 1 晚 - Apr 2 早）──────────────────────┐
│  v7 结果分析 → 失败模式分类 → 优化优先级                      │
│  本地 smoke test → 逐题诊断                                   │
└──────────────────────┬────────────────────────────────────────┘
                       │
┌─ Phase 2: 高 ROI 修复（Apr 2 全天）─────────────────────────┐
│  3 次提交 = 3 次迭代                                          │
│  ① 修复答案格式 + 搜索策略                                    │
│  ② 修复表格解析 + 单位处理                                    │
│  ③ 模型 A/B 测试（如有必要）                                  │
└──────────────────────┬────────────────────────────────────────┘
                       │
┌─ Phase 3: 精细优化（Apr 3）─────────────────────────────────┐
│  3 次提交                                                     │
│  ① 基于 Phase 2 数据的针对性修复                              │
│  ② MCP server 实验                                            │
│  ③ 最高分版本确认                                             │
└──────────────────────┬────────────────────────────────────────┘
                       │
┌─ Phase 4: 收尾（Apr 4）────────────────────────────────────┐
│  3 次提交                                                     │
│  ① 最终优化                                                   │
│  ② 安全网提交（最佳已知配置）                                 │
│  ③ 研究报告提交                                               │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Units

### Phase 1: 诊断与基线建立（今晚）

- [ ] **Unit 1: v7 结果分析 + 失败模式诊断**

**Goal:** 理解 v7（openhands-sdk）的实际表现，建立优化基线

**Requirements:** R4, R5

**Dependencies:** v7 评估完成

**Files:**
- Create: `officeqa/scripts/analyze_submission.py`（可选，如果 arena API 提供 per-question 数据）

**Approach:**
- 获取 v7 per-question 结果（如果 arena 提供 `arena results <id>` 命令）
- 如果无 per-question 数据，对 20 个样题逐个跑 `arena test --n 1` 观察 agent 行为
- 分类失败原因：文件未找到 / 表格解析错 / 公式错 / 格式错 / 超时
- 对比 v5（opencode 152.2）vs v7（openhands-sdk）的差异
- 生成优先级排序的改进列表

**Test scenarios:**
- Happy path: v7 分数 > v5（152.2），确认 harness 切换有效
- Edge case: v7 分数 < v5 — 需要诊断 openhands-sdk 的 skill 加载是否正常
- Integration: 对 20 样题的逐题 pass/fail 记录完整

**Verification:**
- 有明确的 "Top 5 改进方向" + 每个方向的预估分数提升
- 知道 v7 vs v5 的具体差异

### Phase 2: 高 ROI 修复（Apr 2）

- [ ] **Unit 2: 答案格式精确匹配优化**

**Goal:** 基于 reward.py 评分规则，确保 agent 输出格式 100% 匹配

**Requirements:** R1, R2

**Dependencies:** Unit 1 的失败分析

**Files:**
- Modify: `officeqa/skills/05_answer_format/SKILL.md`
- Modify: `officeqa/skills/00_system_instructions/SKILL.md`

**Approach:**
- reward.py 关键规则写入 skill：
  - 数字用 base number（写 "543" 而非 "543,000,000"，即使题目说 "in millions"）
  - 不要在答案中输出多余数字（会被 year filter 或 multi-match 干扰）
  - 百分比：写 "12.34%"（包含 % 符号）
  - 列表：[val1, val2] 格式，逗号+空格分隔
  - 日期："March 3, 1977" 格式
  - 不要输出单位词（"million"、"billion"），只写数字
- `<FINAL_ANSWER>` 标签作为备选提取机制
- 在系统指令中添加明确的 "output cleanliness" 规则

**Test scenarios:**
- Happy path: 百分比题 → agent 输出 "12.34%" 而非 "12.34" 或 "12.34 percent"
- Happy path: 列表题 → "[8.124, 12.852]" 格式正确
- Edge case: 数字含千位逗号 → "[374,443, 381,327]" 正确保留
- Edge case: 年份不被误过滤 → 如果答案是 "2003"，不会被当年份过滤

**Verification:**
- 对 5 道格式多样的样题 smoke test 全通过

- [ ] **Unit 3: 搜索策略强化**

**Goal:** 减少文件定位失败率

**Requirements:** R2

**Dependencies:** Unit 1 的失败分析

**Files:**
- Modify: `officeqa/skills/01_corpus_guide/SKILL.md`
- Modify: `officeqa/skills/00_system_instructions/SKILL.md`

**Approach:**
- 扩展同义词表：covering 更多 Treasury Bulletin 术语变体
- 添加 "fallback cascade" 搜索策略：
  1. 精确短语 grep
  2. 关键词组合 grep
  3. 同义词替换 grep
  4. 宽泛扫描相关年份的所有月份
- 添加常见数据位置提示：
  - 年度汇总：通常在次年 1-3 月 bulletin
  - ESF 数据：季度末（03, 06, 09, 12）
  - 公共债务：每月 bulletin 都有
- 文件名模板：确保 agent 知道所有可能的月份编号（01-12，不是只有常见的几个）

**Test scenarios:**
- Happy path: 常见术语（"expenditures"）→ 直接找到
- Edge case: 非标准术语（"intergovernmental transfers"）→ 同义词回退找到
- Error path: 所有搜索都失败 → agent 宽泛扫描后仍给出最佳猜测

**Verification:**
- 针对 5 道"文件定位困难"的样题 smoke test

- [ ] **Unit 4: 表格解析鲁棒性提升**

**Goal:** 减少列对齐错误和单位处理错误

**Requirements:** R2

**Dependencies:** None

**Files:**
- Modify: `officeqa/skills/02_table_parsing/SKILL.md`
- Modify: `officeqa/skills/00_system_instructions/SKILL.md`

**Approach:**
- 强化表格解析指导：
  - 始终打印完整表头（前 3-5 行），确认列含义
  - 打印目标行的所有列值，标注列索引
  - 交叉验证：用多行数据确认列索引正确（不只看一行）
- 单位处理强化：
  - 在提取数据时同时提取表头单位（millions/billions/thousands）
  - 如果题目要求不同单位，必须转换
  - 添加常见 magnitude 参考（联邦支出 pre-2000 = billions，post-2010 = trillions）
- parse_val() 增强：处理更多特殊格式（"n.a."、"(1)"、带脚注的数字）

**Test scenarios:**
- Happy path: 标准表格 → 正确提取列值
- Edge case: 多行表头 → 正确识别数据起始行
- Edge case: 混合单位表（部分列 millions，部分 billions）→ 正确转换
- Error path: 表格格式异常（缺少分隔符）→ 回退到行文本解析

**Verification:**
- 对 5 道表格密集型样题 smoke test

- [ ] **Unit 5: 配置实验 + 第一轮提交**

**Goal:** 提交优化后的 v8，验证改进效果

**Requirements:** R3, R4

**Dependencies:** Unit 2, 3, 4

**Files:**
- Modify: `officeqa/arena.yaml`（版本号、可能的配置调整）

**Approach:**
- 基于 Unit 1 诊断结果决定是否调整 MAX_ITERATIONS 或模型
- dry-run + 5 题 smoke test 验证
- 提交并记录 submission ID + 改动摘要
- 如果 v7 结果显示 openhands-sdk 有退步，考虑回退到 opencode + 最新 prompt

**Test scenarios:**
- Happy path: dry-run 通过，submit 成功，分数 > v7
- Error path: 分数退步 → 回退到已知最佳配置

**Verification:**
- 提交成功，记录 submission ID

### Phase 3: 精细优化（Apr 3）

- [ ] **Unit 6: 数据驱动迭代**

**Goal:** 基于 v8 结果做针对性修复

**Requirements:** R1, R2, R4

**Dependencies:** Unit 5 结果

**Files:**
- Modify: `officeqa/skills/*/SKILL.md`（根据失败分析）

**Approach:**
- 分析 v8 结果 vs v7 vs v5，确认哪些改进有效
- 识别仍然失败的题型，做针对性修复
- 每次提交只改一个维度（单变量测试）
- 保留最佳版本的完整 snapshot

**Test scenarios:**
- Happy path: 每次提交分数递增
- Edge case: 某次改动导致退步 → 回退 + 分析原因

**Verification:**
- 每次提交有明确的改动日志和分数记录

- [ ] **Unit 7: MCP Server 实验（如有收益空间）**

**Goal:** 测试 filesystem MCP server 是否提升文件检索准确率

**Requirements:** R2

**Dependencies:** Unit 5（基础提交能力验证）

**Files:**
- Modify: `officeqa/arena.yaml`（添加 mcp_servers 配置）

**Approach:**
- 添加 `@modelcontextprotocol/server-filesystem` MCP server
- 挂载 `/app/corpus/` 提供结构化文件浏览
- 用 1 次提交做 A/B 测试：含 MCP vs 不含 MCP
- 如果 MCP 初始化开销 > 检索收益，果断去掉

**Test scenarios:**
- Happy path: MCP 加持下文件检索更准确，分数提升
- Error path: MCP 初始化失败或超时 → agent 回退到 grep
- Edge case: MCP 增加成本/延迟但不增加正确率 → 净亏损

**Verification:**
- 含 MCP 版本分数 vs 不含 MCP 版本分数对比

- [ ] **Unit 8: 模型 A/B 测试（条件触发）**

**Goal:** 如果 qwen3-coder 正确率触及天花板，测试更强模型

**Requirements:** R2

**Dependencies:** Unit 6 结果分析

**Files:**
- Modify: `officeqa/arena.yaml`（model 字段）

**Approach:**
- 触发条件：v8/v9 正确率停滞在 <80%，且分析显示是模型推理能力不足（而非 prompt/skill 问题）
- 候选模型：
  - `anthropic/claude-sonnet-4.6`（$3/$15，推理强但贵）
  - `deepseek/deepseek-r1`（推理强，成本中等）
  - `google/gemini-2.5-flash-preview`（快速，成本低）
- 用同一 prompt + skill 只换模型，1 次提交验证
- 注意：更贵模型会降低效率乘数，需要正确率提升覆盖成本

**Test scenarios:**
- Happy path: 更强模型 +15% 正确率，即使效率乘数降低也净收益
- Edge case: 正确率提升但被成本惩罚抵消 → 评估 tradeoff
- Error path: 模型不兼容 openhands-sdk 工具调用 → 回退 qwen3-coder

**Verification:**
- 新模型分数 vs qwen3-coder 分数对比

### Phase 4: 收尾（Apr 4 截止日）

- [ ] **Unit 9: 最终优化 + 安全网提交**

**Goal:** 确保最高分版本被提交

**Requirements:** R1, R5

**Dependencies:** Phase 2-3 所有结果

**Files:**
- 可能修改: `officeqa/skills/*/SKILL.md`、`officeqa/arena.yaml`

**Approach:**
- 如果有新改进：先提交改进版（1 次）
- 如果改进版分数更高：太好了
- 如果改进版退步：提交已知最高分版本作为安全网（arena 取最高分）
- 保留 1 次提交给研究报告相关调整（如有需要）

**Test scenarios:**
- Happy path: 最终版本是历史最高分
- Error path: 最后一次提交退步 → 无影响，取历史最高

**Verification:**
- Dashboard 显示的最高分即为最终竞赛分数

- [ ] **Unit 10: 研究报告**

**Goal:** 提交竞赛研究报告

**Requirements:** 竞赛要求

**Dependencies:** 所有提交完成

**Files:**
- Create/Modify: `docs/research-proposal.md`（更新为最终版本）

**Approach:**
- 涵盖：方法论（EvoSkill 框架）、设计决策、实验结果、关键发现
- 格式：Markdown 或 PDF
- 提交方式：Discord Channel
- 截止：Apr 4 11:59 PM PST

**Test expectation:** none -- 文档任务

**Verification:**
- 报告已通过 Discord 提交

## Alternative Approaches Considered

| 方案 | 优势 | 劣势 | 决定 |
|------|------|------|------|
| 多 rollout 投票 | +5-15% 正确率 | harness 不原生支持，实现复杂 | 暂不做 |
| 自定义 Docker 镜像 | 预装工具/索引 | 不确定是否允许 | 不做 |
| 预建文件索引 | O(1) 检索 | 可能被视为预计算 | 不做 |
| 换 Codex harness | 可能更强推理 | 排行榜无 Codex 成功案例 | 不做 |

## Success Metrics

| 里程碑 | 分数目标 | 正确题目 | 时间线 |
|--------|---------|---------|--------|
| M0: v7 基线 | >152 | >167 | Apr 1（今晚） |
| M1: 进入 Top 4 | >165 | >180 | Apr 2 |
| M2: 冲击 #1 | >183 | >200 | Apr 3 |
| M3: 拉开差距 | >200 | >220 | Apr 4 |

## Risk Analysis & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| v7 openhands-sdk 退步 | Medium | High | 保留 v5 opencode 配置可回退 |
| Prompt 改动导致退步 | Medium | High | 单变量测试，每次只改一个维度 |
| 其他队伍也在冲刺 | High | Medium | 关注排行榜，保持快速迭代 |
| 提交配额浪费 | Medium | High | 每次提交前 dry-run + 5 题 smoke test |
| 模型切换无效 | Medium | Low | 只在正确率明显触顶时尝试 |
| deadline 前未达目标 | Medium | High | Phase 4 安全网提交确保最高分保留 |

## Daily Cadence

| Day | Date | Submissions | Focus |
|-----|------|-------------|-------|
| 0 | Apr 1 | v7 等结果 | 诊断 + 计划 |
| 1 | Apr 2 | 3x | 格式修复 + 搜索强化 + 表格解析 |
| 2 | Apr 3 | 3x | 数据驱动迭代 + MCP 实验 + 模型测试 |
| 3 | Apr 4 | 3x | 最终优化 + 安全网 + 研究报告 |

## Sources & References

- 评分公式: reward.py（`officeqa/.arena/samples/officeqa-uid0004/tests/reward.py`）
- 竞赛规则: arena.sentient.xyz/challenges/grounded-reasoning
- 当前 prompt: `officeqa/skills/00_system_instructions/SKILL.md`
- 当前配置: `officeqa/arena.yaml`
- 现有计划: `docs/plans/2026-04-01-001-feat-officeqa-rank-one-sprint-plan.md`
- openhands-sdk 源码: `~/.arena/venv/lib/python3.13/site-packages/arena_sdk/harness/openhands_sdk.py`
