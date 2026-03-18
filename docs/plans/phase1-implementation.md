# Phase 1 Implementation Plan

## Goal

从零搭建 SEO CTR Self-Evolving Agent，跑通完整链路：GSC 数据 → 机会识别 → 标题生成 → 回测验证 → 基础进化。

## Scope

**In:**
- 项目脚手架（conda env, .gitignore, .env, git init）
- GSC OAuth 登录 + token 持久化
- GSC 数据拉取 + parquet 缓存
- 机会识别器
- Title/Desc Executor（4 种子技能）
- 干预记录（append-only）
- 历史回测
- 进化引擎（Proposer + Skill Generator + Frontier）
- CLI 基础命令

**Out:**
- 审批状态机（Phase 2）
- Streamlit Demo（Phase 3）
- OfficeQA（Phase 3）
- Dedalus / Daytona 集成（延后）
- budget.py（开发期用免费模型，不需要预算追踪）

## Risk

| 风险 | 缓解 |
|------|------|
| GSC OAuth 流程复杂 | 用 OAuth Desktop flow，token 存本地 JSON |
| Python 3.14 兼容性 | conda env 用 3.12，避免 bleeding edge |
| 开发期烧 OpenRouter credits | Week 1 用 Llama 3.3 70B 免费模型 |
| 回测数据不足 | 最少需要 90 天 GSC 数据 |

## Compatibility

- 与主计划 `2026-03-15-feat-seo-ctr-self-evolving-agent-plan.md` 完全对齐
- 成本模型已修正：~$6/step（非 $30），$100 够 ~16 步

---

## Task List

### Step 0: 项目脚手架（30 min）

**文件**: `.gitignore`, `.env`, `environment.yml`, `CLAUDE.md`（更新）

- [ ] 创建 conda env `cohort0`（Python 3.12）
- [ ] 创建 `.env`（只放 `OPENROUTER_API_KEY`）
- [ ] 删除 `API.md`（明文 key 安全隐患）
- [ ] 创建 `.gitignore`
- [ ] `git init` + 首次 commit
- [ ] 更新 `CLAUDE.md`（EvoTransfer → SEO CTR Agent，更新目录结构）
- [ ] 安装基础依赖：`openai`, `google-auth-oauthlib`, `google-api-python-client`, `pandas`, `pyarrow`, `python-dotenv`, `click`

**验收**: conda env 可用，git repo 初始化，API.md 已删除

### Step 1: GSC OAuth + 数据拉取（2 hr）

**文件**: `seo_agent/gsc_client.py`, `config/`

- [ ] OAuth Desktop flow：用户浏览器登录 → 保存 token 到 `config/gsc_token.json`
- [ ] `gsc_client.py`：按天查询 `searchAnalytics.query`，`rowLimit=25000`
- [ ] Parquet 缓存：`gsc_data/{date}.parquet`，原子写入（tmp + rename）
- [ ] 增量同步：跳过已有日期，`data_lag_days=5`
- [ ] CLI: `evo gsc sync [--days 90]`, `evo gsc status`

**验收**: `evo gsc sync --days 90` 拉取真实数据，`evo gsc status` 显示数据范围

### Step 2: 机会识别（1 hr）

**文件**: `seo_agent/opportunity.py`

- [ ] 筛选逻辑：position 4-15, impressions > 200, CTR < baseline * 0.8
- [ ] Opportunity Score：CTR Gap 40% + Traffic Potential 30% + Position Stability 15% + 15% placeholder
- [ ] CLI: `evo opportunities list [--top 20] [--format json]`

**验收**: 从真实 GSC 数据中识别 20+ 机会页面

### Step 3: Title/Desc Executor + 种子技能（2 hr）

**文件**: `seo_agent/executor.py`, `skills/*/v1/SKILL.md`

- [ ] 4 个种子技能 SKILL.md：curiosity_gap, number_hook, loss_aversion, position_adaptive
- [ ] Executor：读取 SKILL.md → 构建 prompt → 调用 LLM → 生成 3 候选标题
- [ ] 硬性规则校验：title 50-60 字符，desc 150-160 字符，关键词前置
- [ ] SERP 数据净化（strip 指令性模式）
- [ ] CLI: `evo generate <page_url> [--skills curiosity_gap,number_hook]`
- [ ] 开发期用免费模型（`meta-llama/llama-3.3-70b-instruct:free`）

**LLM 调用方式（无 wrapper，直接用 OpenAI SDK）**:
```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    timeout=60.0,
    max_retries=2,
)

# 调用处直接传 model 字符串
response = client.chat.completions.create(
    model="meta-llama/llama-3.3-70b-instruct:free",  # 开发期免费
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ],
)
```

**验收**: `evo generate <url>` 输出 3 个候选标题，符合硬性规则

### Step 4: 干预记录 + 回测（1.5 hr）

**文件**: `seo_agent/intervention.py`, `seo_agent/evaluator.py`

- [ ] 干预记录：append-only JSONL 文件（`data/interventions.jsonl`）
- [ ] Position-adjusted CTR 评估：按 position bucket + device 分开
- [ ] `is_significant()` 函数：Z-test for proportions，confidence=0.90
- [ ] 历史回测：前 60 天基线，后 30 天验证
- [ ] CLI: `evo eval run <page_url>`, `evo evolve backtest [--days 30]`

**验收**: 回测显示种子技能在历史数据上的 CTR 变化

### Step 5: 进化引擎（2 hr）

**文件**: `engine/evolution.py`, `engine/proposer.py`, `engine/skill_generator.py`, `engine/frontier.py`

- [ ] `SEOEvolutionEngine.step(new_measurements)` — 事件驱动
- [ ] Proposer：分析失败案例，维护累积反馈历史
- [ ] Skill Generator：根据提案生成新 SKILL.md + trigger.json
- [ ] Frontier Manager：Pareto 前沿，K=15，tournament 评估
- [ ] 前沿状态持久化：`skills/frontier/active_skills.json`，原子写入
- [ ] CLI: `evo evolve step`, `evo evolve status`

**验收**: `evo evolve step` 完成一步进化，生成新技能，更新前沿

### Step 6: CLI 入口 + 集成测试（1 hr）

**文件**: `cli.py`

- [ ] Click/Typer 统一入口，所有子命令挂载
- [ ] `--format json` 全局支持
- [ ] 退出码：0=成功, 1=认证错误, 2=预算超限, 3=无数据
- [ ] 端到端测试：sync → opportunities → generate → backtest → evolve step

**验收**: 完整链路跑通，CLI 输出 JSON

---

## 目录结构

```
cohort 0/
├── .env                    # OPENROUTER_API_KEY only
├── .gitignore
├── cli.py                  # Click/Typer 入口
├── CLAUDE.md               # 更新后
├── environment.yml         # conda env spec
├── seo_agent/
│   ├── __init__.py
│   ├── gsc_client.py       # GSC OAuth + 数据拉取
│   ├── opportunity.py      # 机会识别
│   ├── executor.py         # Title/Desc 生成
│   ├── evaluator.py        # Position-adjusted CTR
│   └── intervention.py     # 干预记录
├── engine/
│   ├── __init__.py
│   ├── evolution.py        # SEOEvolutionEngine
│   ├── proposer.py         # 失败分析
│   ├── skill_generator.py  # 技能生成
│   └── frontier.py         # Pareto 前沿
├── skills/
│   ├── curiosity_gap/v1/SKILL.md
│   ├── number_hook/v1/SKILL.md
│   ├── loss_aversion/v1/SKILL.md
│   ├── position_adaptive/v1/SKILL.md
│   └── frontier/active_skills.json
├── config/
│   └── gsc_token.json      # OAuth token（gitignored）
├── data/
│   ├── gsc/                # parquet 缓存（gitignored）
│   └── interventions.jsonl # 干预记录
└── docs/                   # 现有文档
```

## 关键设计决策

1. **无 LLM wrapper**：直接用 OpenAI SDK，model 字符串传参
2. **无 budget.py**：开发期用免费模型，正式跑时再加
3. **无 async**：顺序执行，3 周项目不值得
4. **无 ModelTier enum**：2 个模型用字符串常量
5. **GSC 用 OAuth Desktop flow**：用户浏览器登录，token 存本地
6. **干预记录用 JSONL**：比 SQLite 简单，append-only 天然保证
7. **Python 3.12**：避免 3.14 兼容性问题

## 时间估算

| Step | 预估 | 累计 |
|------|------|------|
| 0: 脚手架 | 30 min | 30 min |
| 1: GSC | 2 hr | 2.5 hr |
| 2: 机会识别 | 1 hr | 3.5 hr |
| 3: Executor | 2 hr | 5.5 hr |
| 4: 回测 | 1.5 hr | 7 hr |
| 5: 进化引擎 | 2 hr | 9 hr |
| 6: CLI 集成 | 1 hr | 10 hr |
