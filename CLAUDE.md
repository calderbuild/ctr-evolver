# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Sentient Arena Cohort 0 参赛项目，实现 **EvoSkill 自进化 Agent 框架**，应用于两个领域：

1. **SEO CTR 优化**（`seo_agent/`）— 连接 Google Search Console，自动进化 title/description 生成策略
2. **OfficeQA 文档推理**（`office_qa/` + `officeqa/`）— 当前竞赛重点，U.S. Treasury Bulletin 金融文档问答

竞赛截止 2026-04-04，$45K+ 奖金池。评判：排行榜分数（performance + latency + cost，MiniMax M2.5 评估）+ 研究报告。每天 3 次提交（PST 午夜重置）。

## 技术栈

- Python 3.12（conda env: cohort0）
- OpenAI SDK → OpenRouter API（兼容接口，$100 Arena credits）
- Google Search Console API（OAuth Desktop flow，仅 SEO 领域）
- pandas + pyarrow, scipy, Click, Streamlit

## 环境搭建

```bash
conda env create -f environment.yml
conda activate cohort0
# 或者
pip install -r requirements.txt
```

需要 `.env`：`OPENROUTER_API_KEY`。GSC 首次使用需 OAuth（`config/gsc_credentials.json` → `config/gsc_token.json`）。

## 开发命令

```bash
# 语法检查（无 pytest，逐文件编译验证）
python -m py_compile cli.py
python -m py_compile office_qa/qa_evolution.py

# === SEO 领域 ===
python cli.py gsc sync --days 90
python cli.py gsc status
python cli.py opportunities list --top 20 --min-impressions 5
python cli.py generate <page_url> --skill curiosity_gap
python cli.py evolve step                                      # 单步
python cli.py evolve run --max-steps 15 --mode burst           # 连续
python cli.py evolve backtest --days 30
bash scripts/run_evolution.sh                                   # 一键运行

# === OfficeQA 领域（竞赛重点） ===
# 本地进化测试（Python API）
python -c "from office_qa.qa_evolution import QAEvolutionEngine; QAEvolutionEngine().run(max_steps=5)"

# Arena CLI 提交（需 pip install sentient-arena-cli，或用 npx）
arena auth                                                      # 认证
arena test --dry-run                                            # 验证配置
arena test --n 5                                                # 跑 5 道样题
arena submit                                                    # 提交排行榜（3/天）
bash officeqa/scripts/sync_skills.sh                            # 进化技能 → 提交目录

# Formula library CLI（agent 运行时也可调用）
python3 officeqa/skills/formulas.py percent_change 100 150 2
python3 officeqa/skills/formulas.py cagr 100 200 10 2
python3 officeqa/skills/formulas.py geometric_mean 1.5 2.0 --decimals 3

# === 沙箱 ===
python3 scripts/daemon_evolve.py [max_steps]                    # Daytona 后台守护
python3 scripts/export_skills.py                                # 导出 base64 tarball
```

`max_steps` 表示"本次要跑多少步"而非绝对上限。Checkpoint 恢复从上次步数 +1 继续。

## 架构

三层设计：领域层（数据采集 + 单次操作）→ 进化层（决策循环）→ 提交层（Arena harness）。

### 共享进化引擎 engine/

SEO 领域的进化基础设施，frontier/memory/proposer/skill_generator 被 OfficeQA 复用：

- `evolution.py`：`SEOEvolutionEngine` 主循环（硬依赖 `seo_agent` 模块）。`step()` = evaluate → frontier → analyze failures → memory → propose → generate。支持 burst/continuous 模式，checkpoint 原子写入
- `proposer.py`：三个 LLM 调用 — `analyze_failures()`/`propose_strategy()`（Sonnet）、`extract_memory_updates()`（Haiku）。注入 evolution memory + history
- `frontier.py`：Pareto 前沿（K=15），三维 avg_ctr_lift / win_rate / coverage，composite 加权 50/30/20
- `skill_generator.py`：strategy → `skills/{name}/v{N}/SKILL.md`，自动版本递增
- `memory.py`：三类记忆 promising/failed/patterns，各上限 10 条 FIFO → `data/evolution_memory.json`

### seo_agent/ — SEO 领域层

- `gsc_client.py`：GSC OAuth + 按天 parquet 缓存。`load_data()` / `status()` 不接受 `site_url`
- `opportunity.py`：position baseline CTR 曲线（15 位）算 opportunity_score
- `executor.py`：加载 SKILL.md 模板调 LLM 生成 title/desc
- `evaluator.py`：position-adjusted CTR + z-test（n<30 直接 not significant）
- `llm_evaluator.py`：LLM-as-Judge 代理评估（Haiku 五维度打分）
- `intervention.py`：append-only JSONL，更新 = 追加同 ID 新记录

### office_qa/ — OfficeQA 进化层

镜像 seo_agent 架构，适配文档问答领域：

- `data_client.py`：从 `.arena/samples/` 加载样题（246 道 Treasury Bulletin 问题）
- `qa_executor.py`：加载 SKILL.md 模板，LLM 生成带推理的答案
- `qa_evaluator.py`：ground-truth 模糊匹配（数值 1% 容差）
- `llm_evaluator.py`：LLM-as-Judge 五维度（factual_accuracy, completeness, numerical_precision, reasoning_quality, source_grounding）
- `qa_evolution.py`：QA 领域进化循环，复用 engine/frontier + engine/memory
- `intervention.py`：QA intervention JSONL（uid, question, answer, expected）

### officeqa/ — Arena 提交目录

竞赛提交入口，**不含进化逻辑**，只有运行时配置：

- `arena.yaml`：harness 配置（openhands-sdk harness, qwen3-coder 模型, 8GB/600s）
- `prompts/officeqa_prompt.j2`：Jinja2 agent prompt 模板（基础指令，skills 是主要内容载体）
- `skills/`：**必须是 `子目录/SKILL.md` 格式**（openhands-sdk 只加载此结构，扁平文件会被忽略）。当前 6 个 skill：system_instructions, corpus_guide, table_parsing, formula_library, domain_knowledge, answer_format
- `scripts/sync_skills.sh`：从 office_qa 进化结果同步到提交目录
- `.arena/samples/`：Arena CLI 下载的样题 + 评估脚本

### 跨模块模式

- **LLM JSON 解析**：`executor._parse_json_response()` 和 `proposer._parse_json()` 各有 code-fence 剥离 + 宽松 JSON 提取。新增 LLM 调用复用此模式
- **OpenRouter client**：每个模块各有 `_get_client()`，参数相同。不要抽象成共享 helper — 有意为之
- **原子写入**：parquet 和 checkpoint 都用 tmpfile + rename
- **技能版本**：`skills/{name}/v{N}/SKILL.md`，`executor.load_skill()` 自动取最新版本

## LLM 模型选择

```python
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    timeout=60.0,
    max_retries=2,
)
```

- 开发期：`meta-llama/llama-3.3-70b-instruct:free`
- 生成/分析：`anthropic/claude-sonnet-4.6`（$3/$15 per M tokens）
- 评估/记忆提取：`anthropic/claude-haiku-4.5`（$1/$5 per M tokens）
- Arena 提交评估：MiniMax M2.5（服务端指定，不可更改）
- Arena 开发期 agent：`openrouter/qwen/qwen3-coder`（arena.yaml 配置）

## 注意事项

### SEO 领域

- `min_impressions` 默认 5（小站点数据稀疏）；`position_range` 放宽到 `(1, 50)`
- `evaluator.evaluate_intervention()` 需 before/after 各 100+ impressions，否则 `insufficient_data`
- `opportunity.get_baseline_ctr()` 只覆盖 position 1-15，超出 clamp 到 15
- Continuous 模式 pending intervention 等 1 天评估（原 7 天已降低）
- Pareto frontier 中 coverage=0 新技能有免淘汰保护
- 进化循环用 `frontier.get_active()` 而非 `executor.list_active_skills()`（后者读静态 JSON）

### OfficeQA 领域

- 246 道题，easy/hard 两级难度，fuzzy numeric matching 1% 容差
- 禁止预计算答案/查找表 — agent 必须实时推理（违反将被取消资格）
- 提交前必须 `arena test --dry-run` 验证 arena.yaml + prompt 模板存在
- 评估用服务端模型，开发期模型选择仅影响本地测试
- **评分逻辑**（reward.py）：数字比较用 base number（`"543 million"` base=543 匹配 `"543"`，但不匹配 `"543000000"`）；1900-2100 整数会被当年份过滤；多数字答案要求 ALL 匹配；支持 `<FINAL_ANSWER>` 标签提取
- **openhands-sdk skills 加载**：只扫描 skills_dir 下的子目录，每个子目录取 `SKILL.md`。扁平文件（.md/.py）不会被加载。formulas.py 必须内嵌在 SKILL.md 中由 agent 在运行时写入 `/tmp/`

### Arena 评分公式

`Score = total_correct × (1 + log2_cost_adjustment + log2_time_adjustment)`

正确率主导，cost/time 通过 log2 给予有限加分/扣分。优化优先级：**正确数 >> 延迟/成本**。

### Arena 运行时环境（Docker 容器内）

agent 在 Docker 中运行，看到的文件系统：
- `/app/corpus/`：697 个 Treasury Bulletin 文本文件（`treasury_bulletin_YYYY_MM.txt`）
- `/app/corpus/index.txt`：文件索引
- `/app/answer.txt`：agent 必须写入此文件，否则得 0 分
- 表格用 `|` 分隔列；`(123)` = 负数；`-` = 零
- 数据年份 X 的数据常出现在 X+1 年 1-3 月的 bulletin 中

### 默认站点

`https://meetspot-irq2.onrender.com/`（cli.py 硬编码）。环境变量 `SITE_URL`、`MAX_STEPS`、`MIN_IMPRESSIONS`、`MODE` 可覆盖默认值。

## Daytona 沙箱部署

- Sandbox：`ctr-evolver`（`daytona exec ctr-evolver -- <cmd>`）
- Repo：https://github.com/calderbuild/ctr-evolver
- **googleapis.com 被阻断**，GSC sync 不可用。本地同步后上传 `data/`
- **`daytona exec` strip 所有引号** — 复杂操作用 repo 内脚本
- **nohup/setsid 不生效** — 后台任务用 `python3 scripts/daemon_evolve.py [max_steps]`
- macOS tar 包含 `._` 文件致 Linux parquet 读取失败 → `COPYFILE_DISABLE=1 tar`
- 恢复：`daytona start ctr-evolver` → `daemon_evolve.py 15`

## 数据流

### SEO

```
GSC API -> parquet (data/gsc/) -> DataFrame
  -> identify_opportunities() -> generate_title_desc() -> record_intervention()
  -> [等待] -> evaluate_intervention() -> update_intervention()
  -> frontier.update() -> analyze_failures() + propose_strategy() -> generate_skill()
```

### OfficeQA

```
.arena/samples/ -> data_client.load_tasks() -> qa_executor.generate_answer()
  -> qa_evaluator (ground-truth match) / llm_evaluator (proxy scoring)
  -> record_intervention() -> frontier.update() -> propose + generate new skill
  -> sync_skills.sh -> officeqa/skills/ -> arena submit
```
