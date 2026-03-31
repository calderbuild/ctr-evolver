---
title: "feat: Competition Sprint -- Transfer Evolution Framework to OfficeQA"
type: feat
status: active
date: 2026-03-31
deepened: 2026-03-31
---

# Competition Sprint -- Transfer Evolution Framework to OfficeQA

## Overview

用 4-11 天时间将现有 SEO 自进化框架迁移到 OfficeQA 基准测试，同时通过 Arena CLI 提交排行榜，并用实际迁移结果强化研究提案的 transferability 论证。三个目标同时推进：排行榜得分、框架迁移验证、研究提案完善。

## Problem Frame

竞赛终评 = 排行榜分数 + 研究提案质量。当前状态：

- 研究提案已完成，质量较高（LLM-as-Judge 创新、10 步进化实证、独立发现 branded query 反直觉洞察）
- 排行榜零提交、OfficeQA 代码零起步
- Arena CLI 已下载但未安装
- 当前排行榜最高分仅 1.6%（4/246）-- 赛道极早期，有机会

研究提案 Section 7.2 声称框架 ~60% 可复用 -- **实际证明这个声明**比任何单一分数提升都更有说服力。

## Requirements Trace

- R1. 在排行榜上有分数（非零提交）
- R2. 框架迁移验证研究提案的 transferability 声明
- R3. 每日 3 次提交配额的高效利用
- R4. $200 OpenRouter 额度的预算管理
- R5. 研究提案更新，加入 OfficeQA 迁移实证
- R6. LiteLLM 供应链安全检查

## Scope Boundaries

- **In**: Arena CLI 安装、OfficeQA baseline 提交、进化框架迁移、研究提案更新、安全检查
- **Out**: 从零自建 document parser（用 OfficeQA 提供的 parsed 数据）、构建完整 RAG pipeline（harness agent 自带工具）、Streamlit demo（时间不够）
- **Non-goal**: 拿第一名 -- 目标是 meaningful score + compelling research narrative

## Context & Research

### OfficeQA 基准测试

- **数据**: 美国财政部公报（非 SEC 文件），696 份 PDF，~89,000 页，2600 万+ 数值
- **题目**: 246 题（OfficeQA Full）或 133 题（OfficeQA Pro，难题子集）
- **题型**: 数据分析 62%、多文档检索 11%、外部知识 22%、视觉推理 3%
- **评分**: 二值（正确 1.0 / 错误 0.0），数值答案允许容差（0.1%-5%）
- **SOTA**: Claude Opus 4.6 + oracle parsed docs = 66.9%；agent 模式 54.1%

### Arena CLI 提交机制

- 提交的是 **agent 代码**，不是预计算答案 -- 平台服务端运行你的 agent
- Agent 类型：`harness`（封装 opencode/codex/goose/openhands-sdk）
- 配置：`arena.yaml` 指定 harness、model、prompt_template、skills_dir
- 平台提供 API key -- 服务端运行时不消耗你的 OpenRouter 额度
- 本地测试（`arena test`）消耗你的额度

### 框架迁移分析

| 模块 | 迁移级别 | 改动内容 |
|------|---------|---------|
| `engine/frontier.py` | 直接复用 | 无 |
| `engine/memory.py` | 直接复用 | 无 |
| `engine/proposer.py` | 轻度改动 | 3 个 LLM prompt 改写 |
| `engine/skill_generator.py` | 轻度改动 | 1 个 prompt + SKILL.md 模板 |
| `engine/evolution.py` | 中度重写 | 抽取 base class，重写数据管道 |
| `seo_agent/llm_evaluator.py` | 中度改动 | 评分维度 + prompt |
| `seo_agent/intervention.py` | 轻度改动 | 字段重命名 |
| `seo_agent/executor.py` | 部分复用 | skill 加载复用，生成 prompt 重写 |
| `seo_agent/evaluator.py` | 全部重写 | CTR → QA accuracy |
| `seo_agent/opportunity.py` | 全部重写 | CTR gap → 弱题识别 |
| `seo_agent/gsc_client.py` | 全部重写 | GSC → OfficeQA 数据加载 |

**预估复用率约 70%**（engine 层几乎全复用，agent 层需重写）。研究提案声称 ~60%，迁移分析预估 ~70%，实际复用率待实现后验证。

### 关键战略发现

1. **排行榜极早期** -- 最高分 1.6%（4/246），说明大多数队伍还在搭建基础设施
2. **Parsing 是最大杠杆** -- parser 选择可带来 22 分差距。OfficeQA 提供三种格式（raw PDF / structured JSON / transformed text），用 transformed text 即可避免 parser 开发
3. **Harness agent 自带能力** -- opencode/codex 等已有文件浏览、代码执行等工具，不需要从零构建 agent
4. **服务端运行不消耗额度** -- `arena submit` 的服务端评估由平台付费，只有 `arena test` 本地测试消耗 OpenRouter 额度
5. **Skills 注入机制** -- `arena.yaml` 支持 `skills_dir`，进化产生的 SKILL.md 可以直接注入 harness agent

## Key Technical Decisions

- **双轨策略**: 先用 harness agent + 优化 prompt 快速上分（Day 1-2），再迁移进化框架持续改进（Day 3-7）
  - 理由：先有分数再优化，避免迁移完成前排行榜为零的风险
- **选择 `opencode` harness**: 模型兼容性最广，支持 OpenRouter 全部模型
  - 理由：不锁定特定模型供应商，且 CLI 文档推荐
- **用 OfficeQA transformed text 格式**: 避免 PDF parser 开发
  - 理由：Parsing 错误占失败 40-50%，用官方预处理数据消除这个变量
- **进化框架本地运行、Skills 通过 `skills_dir` 注入提交**: 进化循环不在服务端运行
  - 理由：服务端只支持 harness agent，不支持自定义 Python agent；进化是离线优化
- **LLM-as-Judge 评估维度**: `factual_accuracy`, `completeness`, `numerical_precision`, `reasoning_quality`, `source_grounding`
  - 理由：匹配 OfficeQA 的评分标准（精确数值答案 + 多文档推理）

## Open Questions

### Resolved During Planning

- **评估模型 MiniMax vs DeepSeek?**: Discord 说"还在确认"。不影响我们的实现 -- harness agent 通过 `arena.yaml` 配置模型，可随时切换
- **提交截止 April 4 还是 April 11?**: 按 April 4 规划，延期视为 bonus time。核心交付物必须 April 3 EOD 前就绪
- **LiteLLM 供应链是否影响我们?**: 需要检查。我们的代码不直接依赖 LiteLLM，但 arena-cli 间接依赖。安装 CLI 前先验证

### Deferred to Implementation

- **最优 harness model 选择**: 需要 `arena test` 本地跑几个模型对比后决定。候选：`anthropic/claude-sonnet-4.6`、`qwen/qwen3-coder`（免费）、`deepseek/deepseek-v3.2`
- **Seed skills 的具体策略内容**: 需要看几道 OfficeQA 样题后才能设计
- **进化步数预算**: 取决于本地测试成本，需实测后计算

## High-Level Technical Design

> *This illustrates the intended approach and is directional guidance for review, not implementation specification.*

```
Phase 1: Quick Score (Day 1-2)          Phase 2: Evolution Transfer (Day 3-4)
┌─────────────────────────────┐         ┌──────────────────────────────────┐
│ Install Arena CLI            │         │ office_qa/ (new domain layer)    │
│ arena init grounded-reasoning│         │  ├─ data_client.py (load corpus)│
│ arena test --smoke           │         │  ├─ qa_executor.py (run skills) │
│                              │         │  ├─ qa_evaluator.py (score)     │
│ Optimize arena.yaml:         │         │  └─ qa_opportunity.py (weakness)│
│  ├─ prompt_template (CoT)    │         │                                  │
│  ├─ model selection           │         │ engine/ (read-only reuse)        │
│  └─ skills_dir (manual seeds)│         │  ├─ prompts overridden in qa_evo│
│                              │         │  ├─ frontier.py + memory.py as-is│
│ Submit → get baseline score  │         │  └─ qa_evolution.py (new glue)  │
└─────────────────────────────┘         │                                  │
                                         │ Run evolution locally:           │
Phase 3: Research + Polish (Day 5+)     │  evolve → new skills → inject   │
┌─────────────────────────────┐         │  into arena.yaml skills_dir     │
│ Update research proposal:    │         │  → arena submit → score         │
│  ├─ Section 7.2 + real data │         │  → feed scores back to evolution│
│  ├─ OfficeQA results table  │         └──────────────────────────────────┘
│  └─ Transfer cost analysis  │
│                              │
│ Final demo materials         │
└─────────────────────────────┘
```

## Implementation Units

### Phase 1: Quick Score (Day 1-2)

- [ ] **Unit 1: Security Check + CLI Installation**

**Goal:** 验证 LiteLLM 供应链安全，安装 Arena CLI，完成认证

**Requirements:** R1, R6

**Dependencies:** None

**Files:**
- Inspect: `/Users/calder/cohort 0/arena-cli-latest.tar.gz`
- Create: `~/.arena/` (CLI installation directory)

**Approach:**
- 运行 Quancore 提供的 compromise checker gist 扫描本地环境
- 检查 arena-cli wheels 内是否包含 litellm（`unzip -l arena_cli-0.3.1-py3-none-any.whl | grep litellm`）
- 如果 arena-cli 依赖受影响版本，考虑在隔离 venv 中安装
- 安装 CLI：`bash install.sh && export PATH="$HOME/.arena/bin:$PATH"`
- 认证：`arena auth login`
- 验证：`arena doctor`

**Test expectation:** none -- infrastructure setup, verified by `arena doctor` passing

**Verification:**
- `arena doctor` 返回全部绿色
- `arena quota` 显示剩余提交次数

- [ ] **Unit 2: Initialize Project + Explore Sample Tasks**

**Goal:** 初始化 Arena 项目，理解 OfficeQA 任务格式和评估方式

**Requirements:** R1, R3

**Dependencies:** Unit 1

**Files:**
- Create: `/Users/calder/cohort 0/officeqa/arena.yaml`
- Create: `/Users/calder/cohort 0/officeqa/pyproject.toml`
- Downloaded: `/Users/calder/cohort 0/officeqa/.arena/samples/`

**Approach:**
- `arena init grounded-reasoning`（或实际 competition slug）在 `officeqa/` 子目录
- 仔细阅读 sample tasks 的 `instruction.md`、`task.toml`、`tests/` 目录
- 理解输入格式（文档如何传入 agent）、输出格式（agent 需要产出什么）、评分逻辑（`tests/` 中的 verifier）
- 这一步的核心产出是**理解**，不是代码

**Test expectation:** none -- exploration and understanding

**Verification:**
- 能清楚描述：任务怎么传入、agent 怎么回答、答案怎么评分
- Sample tasks 目录存在且有内容

- [ ] **Unit 3: Baseline Submission -- Default Harness**

**Goal:** 用默认配置提交第一次，获得 baseline 分数

**Requirements:** R1, R3

**Dependencies:** Unit 2

**Files:**
- Modify: `/Users/calder/cohort 0/officeqa/arena.yaml`

**Approach:**
- 配置最简 `arena.yaml`：`opencode` harness + `qwen/qwen3-coder`（免费模型，省额度）
- `arena test --smoke` 本地验证一道题（确认流程通畅）
- `arena submit` 提交第一版
- 记录 baseline 分数作为后续改进基准

**Patterns to follow:**
- CLI scaffold 提供的默认 `arena.yaml` 结构

**Test scenarios:**
- Happy path: `arena test --smoke` 通过，agent 产出答案，verifier 返回分数
- Error path: 如果 smoke test 失败，检查 Docker 配置、模型连接、任务格式

**Verification:**
- `arena submit` 成功返回 submission ID
- `arena results <id>` 显示分数（即使很低）
- 排行榜上能看到自己

- [ ] **Unit 4: Prompt Engineering -- Manual Skill Injection**

**Goal:** 通过 prompt template + 手动编写的 skills 快速提分

**Requirements:** R1, R3, R4

**Dependencies:** Unit 3（需要 baseline 分数和对任务格式的理解）

**Files:**
- Create: `/Users/calder/cohort 0/officeqa/prompt_template.md.j2`
- Create: `/Users/calder/cohort 0/officeqa/skills/` (3-5 seed skill files)
- Modify: `/Users/calder/cohort 0/officeqa/arena.yaml`

**Approach:**
- 基于 sample tasks 的分析，手写 3-5 个 seed skills（QA 推理策略）：
  - `direct_extraction`: 从表格中精确定位数值
  - `multi_step_calculation`: 多步计算链（先提取再计算）
  - `temporal_reasoning`: 跨时间段对比（找最新修订值）
  - `multi_document_synthesis`: 跨文档信息整合
  - `external_knowledge`: 需要补充外部知识的题目识别
- 写 prompt template（Jinja2），注入 chain-of-thought 推理指令
- 在 `arena.yaml` 中配置 `prompt_template_path` 和 `skills_dir`
- 本地测试 2-3 题验证效果，然后提交

**Test scenarios:**
- Happy path: prompt + skills 提升分数超过 baseline
- Edge case: 某些题型（视觉推理）skills 不适用 -- 接受这个限制
- Error path: prompt 过长导致 token 超限 -- 精简 skill 内容

**Verification:**
- `arena test --n 5` 的分数高于 Unit 3 baseline
- `arena submit` 成功且分数有提升

### Phase 2: Evolution Framework Transfer (Day 3-5)

- [ ] **Unit 5: OfficeQA Domain Layer -- Data + Executor**

**Goal:** 创建 `office_qa/` 模块，实现数据加载和 skill-based 答题

**Requirements:** R2

**Dependencies:** Unit 2（理解任务格式），Unit 4（seed skills 已存在）

**Files:**
- Create: `office_qa/__init__.py`
- Create: `office_qa/data_client.py`
- Create: `office_qa/qa_executor.py`
- Reuse: `seo_agent/executor.py` 的 `load_skill()` 和 `list_active_skills()` 逻辑
- Test: `tests/test_qa_executor.py`

**Approach:**
- `data_client.py`: 加载 OfficeQA 题目（CSV）和 parsed documents（transformed text 格式）
- `qa_executor.py`: 复用 skill 加载逻辑，新写 `generate_answer()` -- 用 skill template + 文档上下文 + 题目生成答案
- 保持与 SEO 版本相同的模式：每个模块自有 `_get_client()`，不共享

**Patterns to follow:**
- `seo_agent/executor.py` 的 `load_skill()` / `_parse_json_response()` 模式
- `seo_agent/gsc_client.py` 的数据缓存模式

**Test scenarios:**
- Happy path: `data_client.load_questions()` 返回题目列表；`qa_executor.generate_answer(question, context, skill)` 返回结构化答案
- Edge case: 题目引用的文档不存在 -- 返回明确错误而非静默失败
- Error path: LLM 返回非 JSON 格式 -- `_parse_json_response()` 容错处理

**Verification:**
- `python -m py_compile office_qa/data_client.py` 通过
- `python -m py_compile office_qa/qa_executor.py` 通过
- 能对一道 sample question 生成答案

- [ ] **Unit 6: OfficeQA Evaluator + Opportunity Finder**

**Goal:** 实现答案评估（ground truth + LLM-as-Judge 双路径）和弱题识别

**Requirements:** R2

**Dependencies:** Unit 5

**Files:**
- Create: `office_qa/qa_evaluator.py`
- Create: `office_qa/llm_evaluator.py`
- Create: `office_qa/qa_opportunity.py`
- Create: `office_qa/intervention.py`
- Test: `tests/test_qa_evaluator.py`

**Approach:**
- `qa_evaluator.py`: 用 OfficeQA 的 `reward.py` 评分逻辑（精确匹配 + 数值容差）
- `llm_evaluator.py`: 改编自 `seo_agent/llm_evaluator.py`，五维评分改为 `factual_accuracy`, `completeness`, `numerical_precision`, `reasoning_quality`, `source_grounding`
- `qa_opportunity.py`: 按题型/难度/当前 skill 表现识别弱区
- `intervention.py`: 复用 JSONL append-only 模式，字段改为 QA 相关

**Patterns to follow:**
- `seo_agent/evaluator.py` 的双路径评估模式
- `seo_agent/llm_evaluator.py` 的评分维度 + status 映射
- `seo_agent/intervention.py` 的 JSONL 存储模式

**Test scenarios:**
- Happy path: ground truth "123.45" vs predicted "123.45" → score 1.0；ground truth "123.45" vs predicted "124.00" → score 0.0（超出容差）
- Edge case: 答案是文本非数值 -- exact match 回退
- Integration: evaluator + intervention 联动 -- 评估结果正确写入 JSONL

**Verification:**
- 所有 `.py` 文件 `py_compile` 通过
- 能评估一道 sample question 的答案并记录到 intervention log

- [ ] **Unit 7: Evolution Engine Adaptation**

**Goal:** 适配 engine 层 prompts，创建 QA 进化引擎

**Requirements:** R2

**Dependencies:** Unit 5, Unit 6

**Files:**
- Create: `office_qa/qa_evolution.py`（基于 `engine/evolution.py` 改写外层）
- Reuse (read-only): `engine/proposer.py`、`engine/skill_generator.py`、`engine/frontier.py`、`engine/memory.py`
- Test: `tests/test_qa_evolution.py`

**Approach:**
- 不修改 `engine/proposer.py` 和 `engine/skill_generator.py` 本体 -- 保持 SEO 版本不变
- `qa_evolution.py` 继承或组合 engine 模块，覆盖 prompts 和数据管道
- 复用 `engine/frontier.py` 和 `engine/memory.py`（零改动）
- QA 进化循环：evaluate answers → update frontier → analyze failures → propose strategy → generate skill

**Patterns to follow:**
- `engine/evolution.py` 的 `step()` 流程骨架
- checkpoint 原子写入模式

**Test scenarios:**
- Happy path: `qa_evolution.step()` 完成一个完整循环 -- 评估、frontier 更新、failure 分析、新 skill 生成
- Edge case: 所有答案都正确（无 failure）-- proposer 仍应能提出改进方向
- Integration: 生成的 SKILL.md 文件格式正确，可被 `qa_executor.load_skill()` 加载

**Verification:**
- `python -m py_compile office_qa/qa_evolution.py` 通过
- 能完成至少 1 步进化循环并产出新 skill 文件

- [ ] **Unit 8: Evolution → Submission Pipeline**

**Goal:** 将进化产生的 skills 注入 Arena 提交，形成闭环

**Requirements:** R2, R3

**Dependencies:** Unit 4, Unit 7

**Files:**
- Create: `/Users/calder/cohort 0/officeqa/scripts/sync_skills.sh`
- Modify: `/Users/calder/cohort 0/officeqa/arena.yaml`

**Approach:**
- 进化循环在本地 `office_qa/` 运行，产出 skills 到 `skills/` 目录
- `sync_skills.sh`: 从进化目录复制最新 active skills 到 `officeqa/skills/`（Arena 项目的 `skills_dir`）
- 每次进化循环后：sync skills → `arena submit` → 记录分数 → 反馈给下一步进化
- 手动闭环（不自动化 submit，因为每天只有 3 次）

**Test scenarios:**
- Happy path: 进化产出新 skill → sync → submit → 分数提升
- Edge case: 进化 skill 比手动 skill 差 -- 保留手动 skill 作为 baseline，只注入有提升的
- Error path: skill 文件格式不兼容 -- sync 脚本做格式验证

**Verification:**
- sync 后 `officeqa/skills/` 包含最新 evolved skills
- `arena test --smoke` 用 evolved skills 不报错
- 至少一次提交用 evolved skills 且有分数

### Phase 3: Research + Polish (Day 5-7+)

- [ ] **Unit 9: Research Proposal Update**

**Goal:** 用 OfficeQA 迁移实证更新研究提案

**Requirements:** R5

**Dependencies:** Unit 7, Unit 8（需要实际迁移数据和分数）

**Files:**
- Modify: `/Users/calder/cohort 0/docs/research-proposal.md`

**Approach:**
- Section 7.2 (Transfer Learning): 从理论预测变为实证验证
  - 实际代码行数对比（预期 vs 实际）
  - 实际复用率（预期 ~60% vs 实际）
  - 迁移耗时
- 新增 Section 6.6 或 7.4: OfficeQA 实验结果
  - Baseline score vs evolved score
  - 进化步数 vs 分数曲线
  - 跨域 skill 质量对比
- 更新 Abstract 和 Conclusion -- 加入"成功迁移到第二个域"的主张

**Test expectation:** none -- documentation update

**Verification:**
- 研究提案包含 OfficeQA 数据表格和迁移分析
- 所有数据与实际实验结果一致

- [ ] **Unit 10: Final Optimization Sprint**

**Goal:** 用剩余提交配额最大化排行榜分数

**Requirements:** R1, R3, R4

**Dependencies:** Unit 8, Unit 9

**Files:**
- Modify: `/Users/calder/cohort 0/officeqa/arena.yaml`（model / prompt 调优）
- Modify: `/Users/calder/cohort 0/officeqa/skills/`（最优 skill 组合）

**Approach:**
- 对比不同模型的性价比（免费 qwen vs 付费 sonnet -- 记住服务端不消耗你的额度）
- 尝试 `anthropic/claude-sonnet-4.6` 或更强模型提交
- 调优 prompt template（CoT 深度、示例数量）
- 如果 deadline 延期到 April 11，额外跑更多进化步数

**Test scenarios:**
- Happy path: 模型升级 + evolved skills = 显著分数提升
- Edge case: 强模型在某些题型反而更差 -- 记录并分析

**Verification:**
- 最终提交分数 > Phase 1 baseline
- 所有提交配额被合理使用（不浪费在无意义的重复提交上）

## System-Wide Impact

- **Interaction graph:** Arena CLI → 平台 API → Docker 容器（服务端）；本地进化循环 → skills 目录 → Arena 提交
- **Error propagation:** 服务端执行失败 → `arena results` 返回错误 → 分析日志 → 调整配置重试
- **State lifecycle:** 进化 checkpoint + intervention log 持久化本地状态；Arena 提交历史在平台侧
- **API surface parity:** 进化框架的 skill 格式必须兼容 harness agent 的 `skills_dir` 读取方式
- **Unchanged invariants:** SEO 版本的 `engine/` 和 `seo_agent/` 代码不修改 -- QA 版本是新增代码

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| Arena CLI 安装失败或有 LiteLLM 漏洞 | 先运行 compromise checker；在隔离 venv 安装 |
| OfficeQA 任务格式与预期不同 | Unit 2 专门用于理解格式，不写代码 |
| 服务端模型选择有限或行为不同 | 本地 `arena test` 验证后再 `submit` |
| 进化框架迁移耗时超预期 | Phase 1 先保底拿分，Phase 2 是增量改进 |
| $200 额度不够本地测试 | 服务端 submit 不消耗额度；本地测试用免费模型 |
| Deadline 不延期（April 4） | Phase 1 + Phase 2 前半段 4 天可完成；Phase 3 是 nice-to-have |
| 进化产出的 skills 不如手动 skills | 保留手动 baseline，只注入有验证提升的 evolved skills |

## Daily Cadence

| Day | Date | Phase | Focus | Submissions |
|-----|------|-------|-------|-------------|
| 1 | Mar 31 | P1 | Unit 1-2: CLI 安装 + 任务探索 | 0 |
| 2 | Apr 1 | P1 | Unit 3-4: Baseline + prompt 优化 | 2-3 |
| 3 | Apr 2 | P2 | Unit 5-6: QA domain layer | 1-2（验证性提交） |
| 4 | Apr 3 | P2 | Unit 7-8: Evolution engine + pipeline | 2-3 |
| 5+ | Apr 4+ | P3 | Unit 9-10: Research update + optimization | 2-3/day |

注意：`officeqa/` 是 Arena CLI 项目目录（提交用），`office_qa/` 是进化框架的 Python 模块（本地进化用），两者分开。

## Sources & References

- OfficeQA benchmark: [github.com/databricks/officeqa](https://github.com/databricks/officeqa)
- OfficeQA paper: [arxiv.org/abs/2603.08655](https://arxiv.org/abs/2603.08655)
- Arena CLI: `/Users/calder/cohort 0/arena-cli-latest.tar.gz`
- EvoSkill framework: [github.com/sentient-agi/EvoSkill](https://github.com/sentient-agi/EvoSkill)
- LiteLLM compromise checker: [gist.github.com/barannama/507f297b1348affe1d62a4b0c4916177](https://gist.github.com/barannama/507f297b1348affe1d62a4b0c4916177)
- AgentBeats leaderboard: [agentbeats.dev/agentbeater/officeqa](https://agentbeats.dev/agentbeater/officeqa)
- Research proposal: `/Users/calder/cohort 0/docs/research-proposal.md`
