# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Sentient Arena Cohort 0 参赛项目。核心方向：**SEO CTR Self-Evolving Agent** — 连接 Google Search Console 数据，自动识别低 CTR 页面，进化出最优的 title/meta description 生成策略，通过 CTR 数据反馈持续自我改进。

竞赛为期 3 周（2026-03-13 至 2026-04-04），$45K 奖金池，126 人入选。评判标准为综合评价（排行榜分数 + 研究提案质量）。

## 技术栈

- Python 3.12（conda env: cohort0）
- OpenAI SDK → OpenRouter API（兼容接口，$100 Arena credits）
- Google Search Console API（OAuth Desktop flow）
- pandas + pyarrow（数据处理）
- Click（CLI）
- Streamlit（Demo，Phase 3）

## 环境搭建

```bash
conda env create -f environment.yml
conda activate cohort0
# 或者
pip install -r requirements.txt
```

需要 `.env` 文件（参考 `.env` 格式）：`OPENROUTER_API_KEY`。GSC 首次使用需 OAuth 授权（`config/gsc_credentials.json` → 自动生成 `config/gsc_token.json`）。

## 开发命令

```bash
# 激活环境
conda activate cohort0

# 语法检查
python -m py_compile cli.py
python -m py_compile seo_agent/gsc_client.py  # 等，逐文件

# GSC 数据
python cli.py gsc sync --days 90
python cli.py gsc status

# 机会识别
python cli.py opportunities list --top 20 --min-impressions 5

# 单页生成
python cli.py generate <page_url> --skill curiosity_gap

# 进化循环
python cli.py evolve step                                      # 单步
python cli.py evolve run --max-steps 15 --mode burst           # 连续执行
python cli.py evolve run --max-steps 15 --mode continuous      # 智能等待（6h 同步，1h 步间隔）
python cli.py evolve backtest --days 30                        # 回测

# 一键运行（加载 .env，默认 continuous 模式）
bash scripts/run_evolution.sh

# 沙箱后台守护进程（Daytona 专用，fork 后退出）
python3 scripts/daemon_evolve.py [max_steps]

# 导出技能+数据为 base64 tarball（sandbox 数据取回）
python3 scripts/export_skills.py  # → export.b64
```

默认站点：`https://meetspot-irq2.onrender.com/`（cli.py 中硬编码）。环境变量 `SITE_URL`、`MAX_STEPS`、`MIN_IMPRESSIONS`、`MODE` 可覆盖 `run_evolution.sh` 默认值。

`max_steps` 表示"本次要跑多少步"而非"绝对步数上限"。从 checkpoint 恢复时会从上次步数 +1 开始，再跑 max_steps 步。

## 架构

两层设计：`seo_agent/` 负责数据采集和单次操作，`engine/` 负责进化决策循环。

### seo_agent/ — 数据层

- `gsc_client.py`：GSC OAuth + 按天 parquet 缓存（`data/gsc/{date}.parquet`）。`load_data()` 和 `status()` 不接受 `site_url`，数据目录是全局的。`status()` 返回键名 `files` / `rows`。
- `opportunity.py`：按 (page, query) 聚合，用 position baseline CTR 曲线（硬编码 15 位）算 opportunity_score = impressions * ctr_gap。
- `executor.py`：加载 `skills/{name}/v{N}/SKILL.md` 作为 prompt 模板，调 LLM 生成 title/desc。`list_active_skills()` 读 `skills/frontier/active_skills.json`。
- `evaluator.py`：position-adjusted CTR 评估 + two-proportion z-test 显著性检验（n<30 直接判 not significant）。
- `llm_evaluator.py`：LLM-as-Judge 代理评估。GSC 数据稀疏时用 Haiku 打分（0-10，五维度）代替真实 CTR 数据。`_score_to_status()` 将分数映射为 success/failure/inconclusive 供 frontier 消费。
- `intervention.py`：append-only JSONL（`data/interventions.jsonl`）。更新 = 追加同 ID 新记录，读取取最后一条。`get_evaluation_summary()` 按技能聚合输出 markdown 表格。

### engine/ — 进化层

- `evolution.py`：`SEOEvolutionEngine` 主循环。`step()` 流程：evaluate pending -> update frontier -> analyze failures (with memory + history) -> extract memory updates -> propose strategy -> generate skill。`run()` 支持 burst / continuous 两种模式。Checkpoint 原子写入（tmpfile + rename）。
- `proposer.py`：三个 LLM 调用 — `analyze_failures()`（Sonnet）、`propose_strategy()`（Sonnet）、`extract_memory_updates()`（Haiku）。都注入 evolution memory + evaluation history 作为上下文。
- `frontier.py`：Pareto 前沿（K=15），三维：avg_ctr_lift / win_rate / coverage。composite score 加权 50/30/20。
- `skill_generator.py`：从 strategy dict 生成 SKILL.md，自动版本递增（`skills/{name}/v{N}/`）。
- `memory.py`：三类记忆 promising/failed/patterns，各上限 10 条 FIFO，持久化到 `data/evolution_memory.json`。

### 跨模块模式

- **LLM JSON 解析**：`executor._parse_json_response()` 和 `proposer._parse_json()` 各自实现了相同的 code-fence 剥离 + 宽松 JSON 提取逻辑。新增 LLM 调用时复用此模式。
- **OpenRouter client**：每个模块各有 `_get_client()`，参数相同（`base_url`, `api_key`, `timeout=60`, `max_retries=2`）。不要抽象成共享 helper — 有意为之。
- **原子写入**：parquet（`gsc_client`）和 checkpoint（`evolution`）都用 tmpfile + rename 模式。
- **技能版本**：`skills/{name}/v{N}/SKILL.md`，`executor.load_skill()` 自动取最新版本。

## LLM 模型选择

直接用 OpenAI SDK，不封装 wrapper：

```python
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    timeout=60.0,
    max_retries=2,
)
```

- 开发期：`meta-llama/llama-3.3-70b-instruct:free`（免费）
- 生成/分析：`anthropic/claude-sonnet-4.6`（$3/$15 per M tokens）
- 评估/记忆提取：`anthropic/claude-haiku-4.5`（$1/$5 per M tokens）

成本：~$6/step（Haiku+Sonnet 混合），$100 够 ~16 步进化。

## 关键外部资源

- EvoSkill 框架：https://github.com/sentient-agi/EvoSkill
- OpenRouter API：https://openrouter.ai/docs/quickstart

## 注意事项

- 小站点 GSC 数据稀疏时 `min_impressions=200` 过高，CLI 默认用 5；`position_range` 放宽到 `(1, 50)`
- `evaluator.evaluate_intervention()` 需 before/after 各 100+ impressions 才出结果，否则返回 `insufficient_data`
- `opportunity.get_baseline_ctr()` 只覆盖 position 1-15，超出范围 clamp 到 15
- Continuous 模式下 pending intervention 要等 1 天才会被评估（原 7 天，已降低）
- Pareto frontier 中 coverage=0 的新技能有免淘汰保护，直到被实际试用
- 进化循环的技能列表必须从 `frontier.get_active()` 读取，不要用 `executor.list_active_skills()`（后者读静态 JSON，不反映 frontier 变化）

## Daytona 沙箱部署

- Sandbox 名称：`ctr-evolver`（`daytona exec ctr-evolver -- <cmd>`）
- Repo：https://github.com/calderbuild/ctr-evolver （public）
- **googleapis.com 被 Daytona 网络阻断**，GSC sync 不可用。需本地同步数据后上传 `data/` 到 sandbox
- OpenRouter API 正常可用
- 代码更新流程：本地 commit + push → sandbox 内 `git pull`
- **`daytona exec` 会 strip 所有引号**（单引号、双引号），无法直接传含引号的 shell/python 命令。复杂操作用 repo 内 Python 脚本或 gist 中转
- **`daytona exec` 的 nohup/setsid 不生效** -- exec 退出时子进程被杀。后台任务用 `python3 scripts/daemon_evolve.py [max_steps]`
- macOS `tar` 打包会包含 `._` resource fork 文件，导致 Linux 端 parquet 读取失败。上传前 `COPYFILE_DISABLE=1 tar` 或 Linux 端 `find -name '._*' -delete`
- 沙箱自动停止后文件系统保留 — 进化循环有 checkpoint 机制
- 恢复：`daytona start ctr-evolver` → `daytona exec ctr-evolver --cwd /home/daytona/ctr-evolver -- python3 scripts/daemon_evolve.py 15`

## 数据流

```
GSC API -> parquet (data/gsc/) -> DataFrame
  -> identify_opportunities() -> [{page, query, position, impressions, ctr, baseline_ctr, opportunity_score}]
  -> generate_title_desc() -> {title, description, reasoning}
  -> record_intervention() -> interventions.jsonl (status=pending)

7 天后（continuous 模式实际 1 天）:
  -> evaluate_intervention() -> {ctr_lift, position_adjusted_lift, is_significant}
  -> update_intervention() -> interventions.jsonl (status=evaluated)
  -> frontier.update() -> 淘汰弱技能 + 更新 active_skills.json
  -> analyze_failures() + propose_strategy() -> generate_skill() -> skills/{name}/v{N}/SKILL.md
```
