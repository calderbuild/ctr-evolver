---
title: "feat: OfficeQA Rank #1 Sprint -- From 73.7 to 183+"
type: feat
status: active
date: 2026-04-01
---

# OfficeQA Rank #1 Sprint

## Overview

从排行榜第 7（73.711 分，82/246 正确）冲到第 1（目标 >183 分，需 ~200/246 正确）。所有团队共用 MiniMax M2.5 模型，差距在 prompt engineering、skills 架构、和检索策略。

## Problem Frame

**评分公式**（从 arena_core 源码确认）:
```
Score = total_correct * (1.0 + cost_adj + time_adj)
```
- cost_adj 和 time_adj 是 log2 对数调整，有上下限 cap
- 我们 v2: 82 correct * 0.899 = 73.711（效率惩罚约 10%）
- 第 1 名: ~200 correct * ~0.92 = 183.245（估算）
- **结论：正确率是决定性因素，需要从 82 提升到 200+**

**核心瓶颈分析**（基于 OfficeQA 论文 + 样题分析）:
1. **表格解析错误**占失败的 40-50% -- agent 用 grep 找到正确区域但误读列对齐
2. **文件定位不准** -- 55% 题目需多文件，agent 不知道去哪找
3. **复杂公式缺失** -- 25% 题目需 CAGR、几何均值、Theil 指数等非基础计算
4. **外部知识缺失** -- 10% 题目需知道二战日期、金本位集团成员等
5. **MiniMax M2.5 过度啰嗦** -- 3x token 生成量，浪费时间和成本

## Requirements Trace

- R1. 总分 >183（超过当前第 1 名）
- R2. 正确率 >200/246（82%+）
- R3. 效率乘数 >0.90（控制成本和延迟）
- R4. 每日 3 次提交的高效利用（A/B 测试 + 迭代）
- R5. 可复现的改进（每次提交知道改了什么、效果如何）

## Scope Boundaries

- **In**: prompt 重写、skills 架构、MCP server 工具、检索策略、公式库、答案格式优化
- **Out**: 自建 document parser（用已有 parsed text）、修改 harness 源码、训练/微调模型
- **Non-goal**: 完美解答视觉题（~3% 题目，文本无法解答）

## Context & Research

### 评分公式细节

```python
cost_adj = clamp(log2(cost_baseline / avg_cost) * weight, -cap, +cap)
time_adj = clamp(log2(time_baseline / avg_time) * weight, -cap, +cap)
# 具体 baseline/weight/cap 值服务端配置，不公开
```

每多答对 1 题 ≈ 得 0.85-1.0 分（取决于效率乘数）。从 82 到 200 = +118 题 = +100-118 分。

### MiniMax M2.5 特性

| 特性 | 值 | 影响 |
|------|---|------|
| 参数量 | 230B MoE, 10B active | 推理能力中等偏上 |
| 上下文窗口 | 205K tokens | 可装入大文件，但要控制 |
| 输入成本 | $0.30/M tokens | 低 |
| 输出成本 | $1.20/M tokens | 中 |
| 输出速度 | ~51 tokens/s | 中 |
| 特点 | 过度详细、输出量 3x | 需要明确指令压缩输出 |
| SWE-Bench | 80.2% | 工具调用能力强 |

### 样题失败模式分布

| 失败类型 | 影响比例 | 优先级 |
|---------|---------|--------|
| 表格列解析错误 | ~80% 题目受影响 | P0 |
| 文件定位不准 | ~55% | P0 |
| 复杂公式缺失 | ~35% | P1 |
| 外部知识缺失 | ~10% | P2 |
| 答案格式错误 | ~15% | P1 |
| 视觉题（不可解） | ~5% | 跳过 |

### 题目类型分布（20 样题推算 246 题）

| 类型 | 比例 | 策略 |
|------|------|------|
| 直接提取 | ~15% | 稳拿：grep + 精准列解析 |
| 简单计算（%变化、均值、差值） | ~40% | 稳拿：Python 计算模板 |
| 中等计算（CAGR、几何均值、多文件） | ~25% | 争取：公式库 + 多文件检索 |
| 高级计算（HP滤波、波动率） | ~10% | 争取部分：提供公式实现 |
| 外部知识 | ~10% | 争取：知识注入 skill |

## Key Technical Decisions

- **保持 opencode harness**: 不换 harness -- opencode 工具调用能力最全，且我们已有 2 次成功提交的数据
  - 理由：换 harness 引入未知变量，不如优化已有的

- **Prompt 策略：极简指令 + 丰富 skills**: prompt template 只放核心工作流（<500 tokens），详细策略放 skills 目录
  - 理由：MiniMax M2.5 上下文 205K 够用，但 skills 是按需加载的参考材料，不占主 prompt

- **MCP server 加持检索**: 添加 filesystem MCP server 增强文件浏览能力
  - 理由：opencode 自带文件工具，但 MCP filesystem 提供更结构化的目录浏览

- **Python 计算优先**: 所有数学用 `python3 -c` 或写临时 .py 文件
  - 理由：MiniMax M2.5 心算不可靠，Python 是确定性的

- **每日提交策略**: Day N-早提交"激进改动版"，Day N-晚提交"保守微调版"，保留 1 次做 A/B 对照
  - 理由：3 次/天，需要既大胆尝试又保底

## Open Questions

### Resolved During Planning

- **MiniMax M2.5 是否支持 thinking mode?** 是，但会大幅增加延迟（325x worst case）。通过 prompt 明确禁用：不要求 "think step by step"
- **Skills 文件是注入 system prompt 还是工具?** opencode harness 将 skills_dir 下的文件复制到 agent 环境，agent 可按需读取
- **能否用 MCP server?** 能。arena.yaml 支持 stdio MCP servers，container 内自动安装

### Deferred to Implementation

- **最优 MAX_ITERATIONS 值**: 需要 A/B 测试 -- 太低（20）会漏答，太高（100）浪费成本
- **哪些题型从 MCP filesystem 获益最多**: 需要看 v3 结果的 per-question 数据
- **公式库是否应该预写成 .py 文件而非 skill 文本**: 取决于 agent 是更倾向 import 还是内联代码

## High-Level Technical Design

> *This illustrates the intended approach and is directional guidance for review, not implementation specification.*

```
┌─────────────────────────────────────────────────────────────┐
│                    PROMPT TEMPLATE (精简)                      │
│  1. Parse question → identify type + date + format          │
│  2. Search corpus → find files → extract data              │
│  3. Calculate → python3 only                               │
│  4. Format + write /app/answer.txt                         │
└─────────────────────────┬───────────────────────────────────┘
                          │ {{ instruction }}
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    SKILLS DIRECTORY                           │
│                                                              │
│  01_corpus_guide.md     ← 文件命名规则 + 时间逻辑           │
│  02_table_parsing.md    ← 列解析技巧 + 单位处理            │
│  03_formula_library.md  ← CAGR/几何均值/Theil/HP 公式      │
│  04_domain_knowledge.md ← 二战日期/财政年/金本位成员        │
│  05_answer_format.md    ← 格式规范 + 常见错误               │
│                                                              │
│  formulas.py            ← 可执行的 Python 公式库            │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    MCP SERVERS (可选)                         │
│  filesystem → /app/corpus/ 结构化浏览                       │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Units

### Phase 1: Prompt + Skills 重构（明天第 1-2 次提交）

- [ ] **Unit 1: 重写 Prompt Template -- MiniMax M2.5 优化**

**Goal:** 针对 M2.5 特性重写 prompt，压缩输出、强化精度指令

**Requirements:** R2, R3

**Dependencies:** None

**Files:**
- Modify: `/Users/calder/cohort 0/officeqa/prompts/officeqa_prompt.j2`

**Approach:**
- 开头强调 `/app/answer.txt` 写入（当前已有，保留）
- 添加 M2.5 特定指令："Be concise. Do NOT explain your reasoning in detail. Focus on finding the answer efficiently."
- 添加 "Do NOT use thinking mode" 或等效指令减少延迟
- 结构化为：Parse → Search → Extract → Calculate → Write 五步流程
- 每步限制输出量："Output only the file path and relevant table section, not the entire file"
- 添加负面示例："Do NOT round intermediate results. Do NOT add units unless the question specifies."
- 保持 <500 tokens 总长

**Patterns to follow:**
- 当前 v3 prompt（已验证可用）

**Test scenarios:**
- Happy path: 简单查找题（UID0217 类型）agent 在 3 步内找到答案并写入
- Edge case: 多文件题（UID0057 类型）agent 能构造正确文件名模式
- Error path: 表格解析错误时 agent 能自我校验

**Verification:**
- prompt 长度 <500 tokens
- dry-run 通过

- [ ] **Unit 2: 构建高质量 Skills 体系**

**Goal:** 创建 5 个专精 skill 文件 + 1 个可执行公式库

**Requirements:** R2

**Dependencies:** None（可与 Unit 1 并行）

**Files:**
- Create: `/Users/calder/cohort 0/officeqa/skills/01_corpus_guide.md`
- Create: `/Users/calder/cohort 0/officeqa/skills/02_table_parsing.md`
- Create: `/Users/calder/cohort 0/officeqa/skills/03_formula_library.md`
- Create: `/Users/calder/cohort 0/officeqa/skills/04_domain_knowledge.md`
- Create: `/Users/calder/cohort 0/officeqa/skills/05_answer_format.md`
- Create: `/Users/calder/cohort 0/officeqa/skills/formulas.py`
- Delete: `/Users/calder/cohort 0/officeqa/skills/treasury_qa_guide.md`（合并进新 skills）

**Approach:**
- `01_corpus_guide.md`: 文件命名规则、时间→文件映射逻辑、搜索最佳实践
- `02_table_parsing.md`: Markdown 表格列解析（split by `|`）、多行表头处理、单位识别、(123)=负数、dash=零
- `03_formula_library.md`: 所有中高级公式的 Python 实现 + 使用场景说明
  - percent_change, absolute_percent_change, CAGR, geometric_mean, theil_index, euclidean_norm, hp_filter, annualized_volatility
- `04_domain_knowledge.md`: 外部知识参考表
  - 战争日期：WW1(1914-1918, US 1917), WW2(1939-1945, US Dec 1941), Korean(1950-1953), Vietnam(1955-1975)
  - 财政年变化：1977 前 Jul-Jun，1977 后 Oct-Sep
  - 金本位集团(1935): 法国、荷兰、瑞士、意大利、波兰、比利时、卢森堡
  - 财政部长列表（如果有题目问）
- `05_answer_format.md`: 格式规范、容差规则、常见格式错误
- `formulas.py`: 可直接 `python3 formulas.py <function> <args>` 调用的公式库

**Test scenarios:**
- Happy path: `python3 formulas.py cagr 100 200 10` 输出正确 CAGR
- Happy path: `python3 formulas.py geometric_mean 1.5 2.0 1.8` 输出正确几何均值
- Edge case: `python3 formulas.py hp_filter "100,200,150,300"` 能处理 HP 滤波
- Error path: 参数错误时给出清晰错误信息

**Verification:**
- 所有 skill 文件存在
- `formulas.py` 能通过 `python3 -m py_compile` 且函数可调用
- arena test --dry-run 通过

- [ ] **Unit 3: 配置优化 + 第一次提交**

**Goal:** 调整 arena.yaml 配置，提交 v4 并收集数据

**Requirements:** R3, R4

**Dependencies:** Unit 1, Unit 2

**Files:**
- Modify: `/Users/calder/cohort 0/officeqa/arena.yaml`

**Approach:**
- MAX_ITERATIONS: 测试 25（比 v3 的 30 更紧凑，减成本）
- LLM_TEMPERATURE: 保持 0.1（低温度 = 高一致性）
- timeout_per_task: 保持 600（足够复杂题）
- 可选：添加 MCP filesystem server 配置
- 提交后立刻记录：submission ID、提交时间、改动摘要

**Test scenarios:**
- Happy path: dry-run 通过，submit 成功
- Error path: 配置无效时 dry-run 报错

**Verification:**
- arena submit 成功
- 收到 submission ID

### Phase 2: 数据驱动迭代（后续每日）

- [ ] **Unit 4: v3/v4 结果分析 + 失败模式诊断**

**Goal:** 分析 per-question 结果，识别最高 ROI 的改进方向

**Requirements:** R4, R5

**Dependencies:** Unit 3 提交结果出来后

**Files:**
- Create: `/Users/calder/cohort 0/officeqa/scripts/analyze_results.py`（分析提交结果的工具）

**Approach:**
- 从 `arena results <id>` 获取 per-question 数据（如果 API 支持）
- 如果不支持 per-question，通过本地 smoke test 对 20 个样题逐个测试
- 分类失败原因：文件未找到 / 表格解析错 / 公式错 / 格式错 / 超时
- 计算每类改进的预期收益（失败数 * 可修复比例）
- 输出改进优先级排序

**Test scenarios:**
- Happy path: 分析脚本成功解析结果，输出分类统计
- Edge case: 部分题目无详细数据 -- 使用样题推断

**Verification:**
- 有明确的 "Top 3 改进方向" 输出
- 每个方向有估算的分数提升

- [ ] **Unit 5: 持续迭代循环**

**Goal:** 建立每日改进 → 提交 → 分析 → 改进的闭环

**Requirements:** R1, R4, R5

**Dependencies:** Unit 4

**Files:**
- Modify: `/Users/calder/cohort 0/officeqa/prompts/officeqa_prompt.j2`（根据分析迭代）
- Modify: `/Users/calder/cohort 0/officeqa/skills/*`（根据分析迭代）
- Modify: `/Users/calder/cohort 0/officeqa/arena.yaml`（根据分析调参）

**Approach:**
每天 3 次提交的策略：
1. **早：激进改动** -- 基于前一天分析，做最大改动（新 skill、prompt 重写、配置变化）
2. **中：微调** -- 根据早提交结果微调（修复明显 bug、调参数）
3. **晚：保守** -- 只做有把握的小改进，确保不退步

每次提交记录：
- 改动摘要
- 预期效果
- 实际分数
- 分析：哪些改进有效、哪些无效

**Verification:**
- 每日分数有正向趋势
- 改动日志完整可追溯

### Phase 3: 高级优化（Day 3+）

- [ ] **Unit 6: MCP Server 集成**

**Goal:** 添加 filesystem MCP server 增强文件检索能力

**Requirements:** R2

**Dependencies:** Unit 3（基础提交能力已验证）

**Files:**
- Modify: `/Users/calder/cohort 0/officeqa/arena.yaml`（添加 mcp_servers 配置）

**Approach:**
- 添加 `@modelcontextprotocol/server-filesystem` MCP server，挂载 `/app/corpus/`
- 测试 agent 能否通过 MCP 工具列出文件、读取特定行范围
- 如果 MCP 检索比 grep 更精准（尤其对表格），保留；否则去掉
- MCP 会增加初始化开销 -- 需要 A/B 对比确认净收益

**Test scenarios:**
- Happy path: agent 通过 MCP 读取 /app/corpus/treasury_bulletin_1941_01.txt 成功
- Error path: MCP server 初始化失败 -- agent 回退到 shell grep

**Verification:**
- 提交含 MCP 的版本分数 >= 不含 MCP 的版本

- [ ] **Unit 7: 进化框架本地运行 + Skill 注入**

**Goal:** 用 office_qa/ 进化框架对 20 个样题运行进化，产出更好的 skills

**Requirements:** R2

**Dependencies:** Unit 2（seed skills 就绪）

**Files:**
- Modify: `/Users/calder/cohort 0/office_qa/qa_evolution.py`（如需调整）
- Create: 进化产出的新 skill 文件
- Run: `/Users/calder/cohort 0/officeqa/scripts/sync_skills.sh`

**Approach:**
- 运行 3-5 步进化循环
- 评估进化产出的 skills 是否比手动 skills 好
- 只注入有验证提升的 evolved skills
- 在研究提案中记录进化结果

**Verification:**
- 至少 1 步进化循环完成
- 产出的 skill 文件可被 load_skill() 加载

## Alternative Approaches Considered

| 方案 | 优势 | 劣势 | 决定 |
|------|------|------|------|
| 换 codex harness | 可能更好的推理 | 未知兼容性，浪费提交试错 | 否，保持 opencode |
| 大量 MCP tools | 更强工具能力 | 初始化成本高，M2.5 可能不擅长 MCP | 仅加 filesystem |
| 预计算答案嵌入 | 保证正确 | **明确违规**（Competition Rules 1.1） | 绝对不做 |
| 多 rollout 投票 | +5-15% | harness 不原生支持多 rollout | 暂不做 |
| 换更大的 timeout | 更多时间思考 | 延迟惩罚增大 | 保持 600s |

## Success Metrics

| 里程碑 | 分数目标 | 正确题目 | 时间线 |
|--------|---------|---------|--------|
| M1: 进入 Top 5 | >148 | >160 | Day 2 (Apr 2) |
| M2: 进入 Top 3 | >175 | >190 | Day 3 (Apr 3) |
| M3: 冲击 #1 | >183 | >200 | Day 4+ (Apr 4+) |

## Risk Analysis & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Prompt 改动导致退步 | Medium | High | 保持 v2/v3 备份，每次只改一个维度 |
| 其他队伍也在快速提升 | High | Medium | 关注排行榜变化，知道需要多少分 |
| Skills 过长占满上下文 | Medium | High | 测量 skill 总 token 数，控制在 <50K |
| MiniMax M2.5 不稳定 | Low | Medium | 低温度 + 明确指令减少随机性 |
| 提交配额浪费在无效改动 | Medium | High | 每次提交前 dry-run + 记录假设 |
| Deadline 不延期 (Apr 4) | Medium | High | Phase 1-2 在 Apr 2-3 完成，Phase 3 是 bonus |

## Daily Cadence

| Day | Date | Submissions | Focus |
|-----|------|-------------|-------|
| 1 | Apr 1 | v3 等结果 + v4 如有配额 | 已提交 v3，分析结果 |
| 2 | Apr 2 | 3x | Phase 1: prompt 重写 + skills 体系 + 第一次验证 |
| 3 | Apr 3 | 3x | Phase 2: 数据驱动迭代，目标 Top 3 |
| 4 | Apr 4 | 3x | Phase 2-3: 精细优化 + MCP 实验 |
| 5+ | Apr 5-11 | 3x/day | Phase 3: 进化框架 + 高级优化（如延期） |

## Sources & References

- 评分公式: `arena_core/leaderboard/score_calculator.py`（从 CLI wheel 提取）
- OfficeQA 论文: arxiv.org/abs/2603.08655
- MiniMax M2.5: minimax.io/models/text
- 样题分析: `/Users/calder/cohort 0/officeqa/.arena/samples/`
- 当前 prompt: `/Users/calder/cohort 0/officeqa/prompts/officeqa_prompt.j2`
- Competition Guide: `/Users/calder/cohort 0/CLi.md`
