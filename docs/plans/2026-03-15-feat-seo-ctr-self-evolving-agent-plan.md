---
title: "SEO CTR Self-Evolving Agent"
type: feat
date: 2026-03-15
deepened: 2026-03-15
reviewed: 2026-03-15
---

## Review Summary (2026-03-15 Round 2)

**12 agents reviewed. Consensus: scope too large, infrastructure over-engineered, core idea strong.**

### Critical Changes Made
1. **Scope cut ~60%**: Phase 3 (OfficeQA) removed as separate build. OfficeQA handled as research proposal experiment, not a second product
2. **Event-driven evolution**: `evolve(n_iterations)` → `step(new_measurements)`
3. **Skills versioning**: git branches → versioned files + JSON manifest
4. **Token budget corrected**: 2M → 4M/iteration; cost $20-30/iter at Sonnet, not $5
5. **Seed skills**: 10 → 4
6. **Approval states**: 6 → 5 (merge Applied/Measuring → Active; add Rejected, Reverted)
7. **Stats simplified**: one `is_significant()` function, drop Bonferroni/MDE
8. **CLI-first design**: define CLI contract before building modules
9. **Security**: sanitize SERP data before LLM; never execute LLM-generated scripts outside sandbox
10. **Crash recovery**: atomic writes, frontier state persistence, skill eval status tracking

### What Was NOT Changed
- Core value proposition: self-evolving SEO CTR agent with real GSC data
- Psychology-driven skill architecture
- Position-adjusted CTR as reward signal
- Pareto frontier for skill management
- Research proposal covering all 3 competition directions

---

# SEO CTR Self-Evolving Agent

## Overview

构建一个 **SEO CTR 自进化 Agent**：连接 Google Search Console 数据，自动识别低 CTR 页面，进化出最优的 title / meta description 生成策略，并通过 CTR 数据反馈持续自我改进。

### 一句话定位

**"一个真正能从数据中学习的 SEO Agent -- 不是一次性建议，而是持续进化"**

### 竞赛策略

官方原话："排名第四但拥有开创性研究提案的团队，可能会击败排名第一的团队获得冠军"

**核心策略：做理解问题最深的人，不是最强的工程师。**

| 评判维度 | 大多数团队 | 我们 |
|---------|-----------|------|
| OfficeQA 分数 | 全力优化这一个 benchmark | 合理分数（用现有工具 + 基础进化）|
| 研究提案 | 单领域的增量改进 | 真实产品的自进化验证 + 跨域讨论 |
| 创新性 | 用现有工具跑 benchmark | 真实业务的 GSC 数据验证自进化框架 |
| 产品潜力 | Hackathon demo | 已有 GSC 数据的可运行产品 |

**时间分配（独立参赛者）**：60% 工程 / 25% 研究提案 / 15% Demo + Presentation

---

## Problem Statement / Motivation

### SEO CTR 的真实痛点

1. **手动优化效率极低**：SEO 专家需要逐页分析 GSC 数据，识别"高曝光低点击"的页面，手动撰写更好的 title 和 description。一个中型站点有数千页面，根本做不过来
2. **现有 AI 工具是一次性的**：ClickRank、Surfer SEO 等工具生成建议后就结束了，不会根据实际 CTR 变化学习和进化
3. **没有反馈闭环**：修改 title 后 CTR 是涨了还是跌了？现有工具不会追踪结果并用它来改进下一次的建议
4. **Google AI Overviews 冲击**：AI Overviews 已将顶部有机结果的 CTR 降低 34.5%，传统 SEO 策略失效

### 市场验证

- Seer Interactive 案例：用 AI Agent 优化 SEO 标题，**28% 点击提升**
- SEO 工具市场规模预计 2026 年达 $12B+
- 每个有网站的企业都需要 SEO -- TAM 极大

### 与比赛的连接

Sentient Arena 的核心问题是：**AI Agent 能否在复杂任务上自我改进？**

我们的回答：用同一套自进化框架，在**真实业务**中验证。SEO CTR 优化是天然的自进化场景 -- CTR 就是真实用户的投票。研究提案中讨论框架的跨域泛化能力（含 OfficeQA 分析），覆盖官方全部三个研究方向。

---

## Proposed Solution

### 整体架构（SEO-Only，不做过早抽象）

```
┌──────────────────────────────────────────────────────────┐
│                  SEO Evolution Engine                      │
│                                                            │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐              │
│  │ Executor │   │ Proposer │   │  Skill   │              │
│  │(title    │   │(failure  │   │Generator │              │
│  │generator)│   │ analyzer)│   │          │              │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘              │
│       │              │              │                      │
│  ┌────▼──────────────▼──────────────▼────┐                │
│  │         Pareto Skill Frontier          │                │
│  │   (versioned files + JSON manifest)    │                │
│  └────────────────────────────────────────┘                │
│                                                            │
│  Data: GSC API          Metric: Position-adjusted CTR      │
│  Actions: rewrite       Feedback: 2-4 weeks (async)        │
│    title/desc           + historical backtesting            │
└──────────────────────────────────────────────────────────┘
```

**架构决策（来自 Architecture Strategist + Pattern Specialist Review）**：
- 不画"Universal Evolution Engine"图 -- 只构建 SEO 系统
- OfficeQA 分析放在研究提案中讨论，不构建独立系统
- 如果比赛中有余力，OfficeQA 用 EvoSkill 原生框架跑 baseline 即可

### 核心模块

#### Module 1: Evolution Engine

复用 EvoSkill/GEPA 核心理念，为 SEO 领域定制：

- **Executor**：生成优化后的 title / meta description
- **Proposer**：分析 CTR 未提升的案例，维护**累积反馈历史**防止重复提案（EvoSkill 模式）
- **Skill Generator**：根据提案生成新技能（SKILL.md + trigger.json）
- **Frontier Manager**：Pareto 前沿管理，最多 K=15 候选

**关键设计：事件驱动，非批处理循环**

```python
class SEOEvolutionEngine:
    """事件驱动的进化引擎 -- 新数据到达时触发一步进化"""

    def __init__(self, config: EvolutionConfig):
        self.config = config
        self.proposer = Proposer()
        self.generator = SkillGenerator()
        self.frontier = ParetoFrontier(max_candidates=config.max_candidates)
        self.budget = TokenBudget(limit=config.token_budget)

    def step(self, new_measurements: list[Measurement]) -> StepResult:
        """当新的 GSC 数据到达时调用，处理一批已完成测量的页面"""
        # 1. 评估已完成测量的干预效果
        evaluated = [self.evaluate(m) for m in new_measurements]

        # 2. 识别失败案例（CTR 未提升）
        failures = [e for e in evaluated if e.adjusted_ctr_delta < 0]

        if not failures:
            return StepResult(improved=len(evaluated), no_improvement=0)

        # 3. Proposer 分析失败模式（含累积历史）
        proposals = self.proposer.analyze(failures)

        # 4. 生成新技能
        new_skills = self.generator.build(proposals)

        # 5. Tournament 评估（回测）
        candidates = self.frontier.tournament_evaluate(
            new_skills,
            sample_size=config.tournament_sample_size,
            top_k=config.tournament_top_k,
        )

        # 6. 更新前沿（原子写入 frontier_state.json）
        self.frontier.update_and_persist(candidates)

        return StepResult(
            improved=len(evaluated) - len(failures),
            no_improvement=len(failures),
            new_skills=len(new_skills),
            budget_remaining=self.budget.remaining,
        )
```

#### Module 2: SEO CTR Domain

```
seo_agent/
├── gsc_client.py        — GSC API 客户端（批量查询 + parquet 缓存）
├── opportunity.py       — 机会识别（含意图过滤）
├── executor.py          — Title/Desc 生成（应用技能组合）
├── evaluator.py         — Position-adjusted CTR 评估
├── intervention.py      — 干预记录（append-only）
├── approval.py          — 审批状态机（5 states）
└── queries.py           — 数据查询层（CLI + Dashboard 共用）

engine/
├── evolution.py         — SEO Evolution Engine（事件驱动）
├── proposer.py          — 失败分析器（含累积反馈历史）
├── skill_generator.py   — 技能生成器
├── frontier.py          — Pareto 前沿管理
├── budget.py            — Token 预算管理
└── config.py            — EvolutionConfig dataclass

skills/
├── curiosity_gap/
│   ├── v1/SKILL.md
│   └── changelog.jsonl
├── number_hook/
│   └── ...
├── loss_aversion/
│   └── ...
├── position_adaptive/
│   └── ...
└── frontier/
    └── active_skills.json  — 当前前沿技能清单

cli.py                   — 统一 CLI 入口（Click/Typer）
demo/
├── app.py               — Streamlit Demo（thin rendering layer）
└── components/
```

#### Module 3: CLI Contract（先定义接口，后实现模块）

```bash
# GSC 数据管道
evo gsc sync [--days 90]
evo gsc status                          # 最后同步时间、数据范围、行数

# 机会识别
evo opportunities list [--top 20] [--format json]

# 标题生成
evo generate <page_url> [--skills curiosity_gap,number_hook]

# 进化引擎
evo evolve step                         # 处理新到的测量数据
evo evolve status                       # 当前迭代、预算余量
evo evolve backtest [--days 30]         # 用历史数据回测

# 技能管理
evo skills list [--format json]
evo skills inspect <skill_name>

# 审批门控
evo approval list [--status pending]
evo approval inspect <id>
evo approval approve <id> [--reason "..."]
evo approval reject <id> --reason "..."

# 干预记录
evo log list [--page <url>] [--format json]

# 评估
evo eval run <page_url> [--baseline-days 28]
```

所有命令支持 `--format json`，退出码：0=成功, 1=认证错误, 2=预算超限, 3=无数据。

---

### 机会识别

**筛选条件（来自 SEO Audit + Pattern Specialist Review）**：

```
position 4-15
AND impressions > 200 (desktop) / > 500 (mobile)
AND CTR < own_position_CTR_baseline * 0.8
AND intent != 'navigational'
AND NOT cannibalized (no other page ranking for same query)
```

**注意**：URL Inspection API **不返回** Google 改写的 title。Google title 改写检测需通过 SERP 抓取实现，作为 nice-to-have 而非必需。

**Opportunity Score**：

| Signal | Metric | Weight |
|--------|--------|--------|
| CTR Gap | (expected_CTR - actual_CTR) / expected_CTR | 40% |
| Traffic Potential | impressions * CTR_gap | 30% |
| Position Stability | position stddev < 2 over 28 days | 15% |
| Conversion Value | clicks * page_conversion_rate (if available) | 15% |

权重为初始默认值，计划在 50+ 干预后用回归分析校准。

---

### 初始技能库（4 个种子技能）

| Rank | Skill Name | Psychological Basis | Example |
|------|-----------|---------------------|---------|
| 1 | `curiosity_gap` | Zeigarnik Effect -- 信息缺口 | "7 Pricing Mistakes That Kill Conversions" |
| 2 | `number_hook` | Anchoring -- 具体数字锚定 | "12 Proven Methods" (+36% CTR vs no number) |
| 3 | `loss_aversion` | Prospect Theory -- 损失 > 收益 | "Don't Waste Money on X" > "Save Money on X" |
| 4 | `position_adaptive` | 按位置切换策略 | pos 1-3 用权威性，pos 4-10 用好奇心 |

**Position-Dependent Psychology**：
- **Position 1-3**: Authority + Specificity（用户期望好结果）
- **Position 4-10**: Curiosity Gap + Loss Aversion + Number Hook（需要说服）
- **Position 11-20**: 极端差异化

**硬性规则**（写入 executor 基础逻辑，不作为可进化技能）：
- Title: 50-60 字符，主关键词靠前
- Description: 150-160 字符，包含 CTA
- Brand name 放末尾（`| BrandName`）
- 包含搜索词（Google 会加粗匹配词）

---

### Title/Desc 生成安全

**SERP 数据净化（Critical Security Fix）**：

竞品标题是不可信输入。攻击者可在 SERP 标题中嵌入 prompt injection payload，经 Proposer 分析后可能"进化"入技能库，形成自增强注入链。

**缓解措施**：
1. SERP 标题在进入 LLM 前做净化：strip 指令性模式、限制长度
2. 系统 prompt 与用户数据严格分离（`system` vs `user` role）
3. 技能内容在持久化前扫描可疑模式（文件操作、网络调用、凭证引用）
4. 永远不在沙箱外执行 LLM 生成的脚本

---

### 审批状态机（5 states）

```
Draft → PendingApproval → Approved → Active → Completed
                ↓                      ↓
            Rejected              Reverted
```

**状态说明**：
- `Draft`: Proposer 创建，等待提交
- `PendingApproval`: 已提交审批，等待人工或 `--auto-approve` 确认
- `Approved`: 已批准，等待应用到页面
- `Active`: 已应用，正在收集数据。内含 `measurement_ready: bool` 标记数据是否充足
- `Completed`: 测量完成，结果已记录
- `Rejected`: 审批被拒绝
- `Reverted`: CTR 下降，已回滚到原标题

**超时策略**：PendingApproval 超过 7 天自动标记为过期。支持 `--auto-approve` 模式用于开发和全自动运行。

**实体粒度**：状态挂在 `(page_url, experiment_id)` 上，非 skill 级别。

---

### 数据管道

**GSC API**：
- 认证：Service Account（`GOOGLE_APPLICATION_CREDENTIALS` 环境变量，不用硬编码路径）
- 查询：`searchAnalytics.query`，按天单次查询，`rowLimit=25000` + 分页
- 存储：`gsc_data/{date}.parquet`，每天一个文件
- **原子写入**：先写 `.tmp` 文件，再 `os.rename`，启动时删除 `.tmp` 残留
- **数据延迟**：`data_lag_days=5`（非 3，因为数据 4-5 天才稳定）
- Python 库：`google-api-python-client` + `google-auth`
- Rate limits: 20 QPS per user; URL Inspection API 2,000/day（独立配额）

**干预记录（Intervention Log）**：

```
字段：
  id: auto-increment
  experiment_id: str
  page_url: str
  field_changed: str
  old_value: str
  new_value: str
  skill_used: str
  position_at_apply: float
  impressions_baseline_28d: int
  ctr_baseline_28d: float
  applied_at: datetime
  status: enum(active, completed, reverted)
```

**Append-only 强制**：文件用 append 模式打开，或 SQLite + trigger 禁止 UPDATE/DELETE。

**前沿状态持久化**：

```json
{
  "version": 1,
  "updated_at": "2026-03-20T10:30:00Z",
  "status": "completed",
  "members": [
    {
      "skill_id": "curiosity_gap_v2",
      "added_at_step": 3,
      "metrics": {"adjusted_ctr_delta": 0.45, "sample_size": 150}
    }
  ]
}
```

原子写入（tmp + rename）。启动时检查 `status != completed` 则回滚到上次完成状态。

---

### 统计方法（简化版）

**核心：一个函数**

```python
def is_significant(
    impressions_before: int, clicks_before: int,
    impressions_after: int, clicks_after: int,
    confidence: float = 0.90,
) -> tuple[bool, float, float]:
    """Z-test for proportions. Returns (significant, z_score, p_value)."""
```

**SEO 实验设计**：
- **Baseline 期**：修改前 4 周稳定数据
- **Washout 期**：修改后 3-5 天（Google 重新抓取过渡期）
- **Test 期**：Washout 后 4 周测量
- **Control Pages**：选 3-5 个未修改但流量模式相似的页面
- **最低 impressions**：每期 ~12,000 才能检测 20% 相对 CTR 提升
- **置信度**：90%（SEO 修改成本低、可回滚，用宽松阈值换更快迭代）

**Position-Adjusted CTR**：
- Position bucket: 1, 2, 3, 4, 5 各自独立（不合并 4-5），6-10, 11-20 可合并
- **必须按 device 分开**（mobile vs desktop）
- 排除 position stddev > 2 的页面（太不稳定，无法归因）
- 排除 test 期 impressions < 50% 或 > 200% baseline 期的页面

**研究提案中讨论但不实现**：Benjamini-Hochberg 多重比较修正、MDE 计算、季节性归一化。

---

## Technical Approach

### Phase 1: SEO CTR Agent + 基础进化（第 1 周）

**目标**：跑通 GSC → 识别机会 → 生成标题 → 回测验证 → 基础进化

- [ ] `.gitignore` 创建（**第一个 task**）：`config/gsc_credentials.json`, `config/settings.yaml`, `gsc_data/`, `*.parquet`, `.env`
- [ ] `detect-secrets` pre-commit hook 安装
- [ ] GSC 数据连接 + parquet 缓存（原子写入）
- [ ] 机会识别器（筛选 + Opportunity Score）
- [ ] Title/Desc Executor（4 个种子技能 + 硬性规则校验 + SERP 数据净化）
- [ ] 干预记录（append-only）
- [ ] CLI 基础命令：`evo gsc sync`, `evo opportunities list`, `evo generate`
- [ ] 历史回测：取 90 天数据，前 60 天训练基线曲线，后 30 天验证
- [ ] 基础进化：`evo evolve step` + `evo evolve backtest`
- [ ] Proposer（含累积反馈历史）
- [ ] Skill Generator（输出 SKILL.md + trigger.json）
- [ ] Frontier Manager（versioned files + active_skills.json + 原子持久化）

**验收标准**：
- 从 GSC 拉数据 → 识别 20+ 机会 → 生成优化建议 → 回测显示 CTR 提升
- 进化引擎能完成至少 3 步进化
- 所有 CLI 命令返回 JSON

### Phase 2: 实验 + 审批 + 真实验证（第 2 周）

**目标**：在真实页面上运行实验，收集真实数据

- [ ] 审批状态机（5 states + auto-approve mode）
- [ ] 选择 10-15 个最佳机会页面，应用优化标题
- [ ] 等待 GSC 数据回传（同时继续用回测数据进化）
- [ ] Token 预算管理（4M tokens/step ceiling）
- [ ] 进化日志（per-step, per-skill 粒度 -- 研究提案需要）
- [ ] 持续进化：每有新数据到达就运行 `evo evolve step`
- [ ] 开始撰写研究提案框架

**验收标准**：
- 10+ 页面已应用优化标题
- 进化引擎运行 5+ 步
- 研究提案框架完成（含实验设计）

### Phase 3: 研究提案 + Demo + OfficeQA baseline（第 3 周）

**目标**：撰写研究提案，打磨 demo，跑 OfficeQA baseline

- [ ] 研究提案完稿（见下方 Research Proposal Outline）
- [ ] SEO CTR Agent Demo（Streamlit）
  - Dashboard：GSC 数据概览 + 机会列表
  - 优化建议：每页 3 候选 title，标注技能
  - 进化可视化：技能进化历程 + CTR 变化
  - **认证**：`streamlit-authenticator` 或绑定 `127.0.0.1`
- [ ] OfficeQA baseline（**用 EvoSkill 原生框架**，不自建系统）
  - Fork EvoSkill → 配置 OfficeQA task → 跑 3 轮进化 → 记录分数
  - 作为研究提案的对比数据点
- [ ] 2 分钟 demo 视频（**预录制**，非现场演示）
- [ ] 5 页 slides：问题 → 方案 → 架构 → 真实数据结果 → PMF

**验收标准**：
- Demo 流畅运行
- 研究提案有真实 GSC 数据支撑
- OfficeQA 有 baseline 分数
- Demo 视频已预录制

---

## 进化驱动示例

### 初始状态（4 个种子技能）

```
输入：
  当前标题："Python Tutorial - Learn Python Programming"
  关键词："python tutorial"
  Position: 8, CTR: 1.2%（自有基线 position 8 均值 3.5%）

触发技能：number_hook + curiosity_gap + position_adaptive(pos=8 → 好奇心策略)

输出：
  候选 1: "Python Tutorial for Beginners: 7 Projects to Build in 2026"
  候选 2: "Learn Python in 30 Days: Free Tutorial with Real Projects"
  候选 3: "Why Most Python Tutorials Fail (And What Works Instead)"
```

### 进化后（经过 5 步）

```
Step 3 数据回传：number_hook 的标题 CTR 提升 +45% vs baseline (position-adjusted)
Step 4 数据回传：curiosity_gap 在 position 1-3 效果差，在 4-10 效果好
→ Proposer 提案：为 curiosity_gap 增加位置条件触发
→ Skill Generator 更新 curiosity_gap trigger.json：position >= 4
Step 5 数据回传：loss_aversion 在 transactional intent 效果好，informational 效果差
→ Proposer 提案：拆分为 loss_aversion_transactional
```

---

## Cost Model（修正后）

| 项目 | Token 估算 | Sonnet 成本 |
|------|-----------|------------|
| 一步进化（50 tasks） | ~2.67M tokens | ~$20 |
| Tournament 初筛 | ~375K tokens | ~$3 |
| Full evaluation（top 2） | ~750K tokens | ~$6 |
| Proposer + Generator | ~50K tokens | ~$0.5 |
| **总计/step** | **~4M tokens** | **~$30** |
| **5 steps** | **~20M tokens** | **~$150** |

**成本控制策略**：
- Tournament evaluation：先在 15-20 tasks 上测试（非 10），保留 top 2（非 5），再对 top 2 做 30-task 全量评估
- 用 Haiku/GPT-4o-mini 做 tournament 初筛，Sonnet 只用于 Proposer 和 final evaluation
- 回测（不用等真实数据）模拟进化，在比赛期间快速迭代
- 4M token/step 硬上限，超预算自动停止

---

## Acceptance Criteria

### Functional Requirements

- [ ] GSC 数据成功获取并解析（原子写入 + parquet 缓存 + 增量同步）
- [ ] 机会识别器筛选 Top 20 候选（含意图过滤）
- [ ] Title/Desc 生成符合 SEO 最佳实践（50-60 字符、CTA、关键词前置）
- [ ] 进化引擎 5+ 步，能自动分析失败并生成新技能
- [ ] 审批门控支持异步工作流（5-state 状态机 + auto-approve）
- [ ] Position-adjusted CTR 评估（非 raw CTR）
- [ ] 所有操作可通过 CLI 驱动（`--format json` 输出）

### Non-Functional Requirements

- [ ] 每步进化 token 预算 <= 4M tokens
- [ ] Pareto 前沿候选数 <= 15
- [ ] GSC 数据本地缓存，过去日期不重复查询（data_lag_days=5）
- [ ] 前沿状态 + 干预日志可从崩溃中恢复
- [ ] GSC credentials 通过环境变量管理（不在代码中）
- [ ] Streamlit demo 绑定 localhost 或有认证

---

## Success Metrics

| 指标 | 目标值 | 衡量方法 |
|------|--------|----------|
| SEO 机会识别覆盖率 | > 20 个机会 | GSC 数据分析 |
| Title 生成质量 | 人工评估优于原标题 > 80% | 盲评 |
| Position-Adjusted CTR 提升 | > 20%（回测） | Position-adjusted 对比 |
| 进化步数 | > 5 步 | 自动记录 |
| 每步成本 | < $30 (Sonnet) | 自动记录 |
| 研究提案质量 | 有真实 GSC 数据支撑 | 评委评价 |

---

## Risk Analysis & Mitigation

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| CTR 反馈周期太长（9 周全流程） | 比赛期间看不到真实效果 | 用历史数据回测模拟反馈；选少量页面做真实实验 |
| SERP 数据 prompt injection | 技能库被污染 | 净化外部数据；技能持久化前扫描 |
| Pareto 评估成本失控 | 预算超限 | Tournament top 2 + 30-task subset + Haiku 初筛 |
| 进化引擎崩溃 | 丢失进度 | 原子写入 + frontier_state.json + eval status tracking |
| Daytona 资源不足 | 无法运行 | 申请 2vCPU/4GB RAM/5GB disk；设 auto-stop=0 |
| 跨域迁移讨论缺乏实验数据 | 研究提案弱化 | 用 EvoSkill 跑 OfficeQA baseline 作为对比点 |

### 降级方案

1. **最低交付**：SEO CTR Agent MVP（4 种子技能 + GSC 数据 + 回测结果）+ 研究提案框架
2. **标准交付**：+ 进化引擎 5+ 步 + 真实页面实验 + Demo + 审批门控
3. **完整交付**：+ OfficeQA baseline（EvoSkill）+ 完整研究数据 + 预录制 demo

---

## Research Proposal Outline

### Title
"Self-Evolving SEO Agent: Validating Domain-Agnostic Agent Improvement with Real-World CTR Feedback"

### Abstract
现有 Agent 自进化框架（EvoSkill、Hermes Agent、GEPA）通常在合成 benchmark 上验证。本研究在真实业务场景 -- Google Search Console CTR 优化 -- 中验证自进化机制，并与 OfficeQA 文档推理 benchmark 做对比分析。

### Key Research Questions

1. 自进化框架在真实业务（2-4 周异步反馈）中的效果是否与即时反馈 benchmark 一致？
2. 心理学驱动的种子技能 vs 从零进化，哪个策略更有效？
3. Position-adjusted CTR 作为 reward signal 的信噪比如何？
4. 什么条件下技能可以跨域迁移（SEO ↔ 文档推理）？

### Experiments

| 实验 | 对照组 | 实验组 | 指标 | 可行性 |
|------|--------|--------|------|--------|
| Exp 1: 进化效果 | 无进化（种子技能固定）| 5+ 步进化后 | Position-adjusted CTR | **执行** |
| Exp 2: 种子技能价值 | 无种子，从零进化 | 4 个心理学种子 | 首步准确率差异 | **执行** |
| Exp 3: 跨域分析 | OfficeQA EvoSkill baseline | SEO 进化技能应用于 OfficeQA | 定性分析 | **提案** |
| Exp 4: 反馈延迟影响 | 即时反馈（回测） | 模拟 2-4 周延迟 | 收敛速度 | **提案** |

### Connection to Arena Research Directions

- **Direction 1 (Self-Improvement)**：进化引擎核心设计 + 真实数据验证
- **Direction 2 (Transfer Learning)**：SEO ↔ OfficeQA 技能分析（定性）
- **Direction 3 (Automatic Evaluation)**：CTR = 真实用户投票 = 自动评估；Position-adjusted CTR 是更可靠的评估信号

---

## Competitive Landscape

| 竞品 | 特点 | 我们的差异化 |
|------|------|-------------|
| ClickRank.ai | 一键优化 title/desc | 我们有进化闭环 + position-adjusted 评估 |
| Surfer SEO | 内容优化建议 | 我们聚焦 CTR，有 GSC 数据驱动的反馈 |
| SearchPilot | SEO A/B 测试 | 我们不只测试，还自动进化策略 |
| Ahrefs AI | Meta tag 生成 | 我们的技能会随数据反馈进化 |

**核心差异**：市面上没有一个 SEO 工具有**自进化能力** -- 都是静态建议引擎。

---

## References

### SEO CTR Optimization
- [Seer Interactive: 28% More Clicks](https://www.seerinteractive.com/insights/how-we-built-a-seo-ai-agent-one-tab-zero-copy-paste-28-more-clicks)
- [Claude Code as SEO Command Center](https://searchengineland.com/claude-code-seo-work-470668)

### Self-Evolving Agents
- [EvoSkill](https://github.com/sentient-agi/EvoSkill) -- Sentient + Virginia Tech
- [GEPA](https://arxiv.org/abs/2507.19457) -- DSPy, Pareto-optimal prompt evolution
- [Hermes Agent Self-Evolution](https://github.com/NousResearch/hermes-agent-self-evolution) -- ICLR 2026 Oral
- [Imbue Darwinian Evolver](https://github.com/imbue-ai/darwinian_evolver) -- 最简进化 API

### OfficeQA
- [OfficeQA Pro Paper](https://arxiv.org/abs/2603.08655) -- Databricks AI Research
- [OfficeQA GitHub](https://github.com/databricks/officeqa)

### Competition
- [Sentient Arena](https://arena.sentient.xyz)
