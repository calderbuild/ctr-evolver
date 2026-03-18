# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Sentient Arena Cohort 0 参赛项目。核心方向：**SEO CTR Self-Evolving Agent** — 连接 Google Search Console 数据，自动识别低 CTR 页面，进化出最优的 title/meta description 生成策略，通过 CTR 数据反馈持续自我改进。

竞赛为期 3 周（2026-03-13 至 2026-04-04），$45K 奖金池，126 人入选。评判标准为综合评价（排行榜分数 + 研究提案质量）。

## 目录结构

```
cli.py                  — Click CLI 入口（evo 命令）
seo_agent/
  gsc_client.py         — GSC OAuth + 数据拉取（parquet 缓存）
  opportunity.py        — 机会识别（筛选 + Opportunity Score）
  executor.py           — Title/Desc 生成（应用技能组合）
  evaluator.py          — Position-adjusted CTR 评估
  intervention.py       — 干预记录（append-only JSONL）
engine/
  evolution.py          — SEOEvolutionEngine（事件驱动 step()）
  proposer.py           — 失败分析（含累积反馈历史）
  skill_generator.py    — 技能生成（输出 SKILL.md）
  frontier.py           — Pareto 前沿管理（K=15）
skills/
  {name}/v{N}/SKILL.md  — 技能定义（EvoSkill 格式）
  frontier/active_skills.json — 当前前沿技能清单
config/                 — 凭证（gitignored）
data/                   — GSC 数据 + 干预记录（gitignored）
docs/
  plans/                — 规划文档
  deployment-checklist.md — Daytona 部署清单
```

## 技术栈

- Python 3.12（conda env: cohort0）
- OpenAI SDK → OpenRouter API（兼容接口，$100 Arena credits）
- Google Search Console API（OAuth Desktop flow）
- pandas + pyarrow（数据处理）
- Click（CLI）
- Streamlit（Demo，Phase 3）

## 开发命令

```bash
# 激活环境
conda activate cohort0

# CLI
python cli.py gsc sync --days 90
python cli.py opportunities list --top 20
python cli.py generate <page_url>
python cli.py evolve step
python cli.py evolve backtest --days 30
```

## LLM 调用

直接用 OpenAI SDK，不封装 wrapper：

```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    timeout=60.0,
    max_retries=2,
)
```

模型选择：
- 开发期：`meta-llama/llama-3.3-70b-instruct:free`（免费）
- 生成/分析：`anthropic/claude-sonnet-4.6`（$3/$15 per M tokens）
- 评估/执行：`anthropic/claude-haiku-4.5`（$1/$5 per M tokens）

成本：~$6/step（Haiku+Sonnet 混合），$100 够 ~16 步进化。

## 关键外部资源

- EvoSkill 框架：https://github.com/sentient-agi/EvoSkill
- OfficeQA 数据集：https://github.com/databricks/officeqa
- OfficeQA Pro 论文：https://arxiv.org/abs/2603.08655
- OpenRouter API：https://openrouter.ai/docs/quickstart

## 凭证管理

- API keys 在 `.env`（gitignored），用 `python-dotenv` 加载
- GSC OAuth token 在 `config/gsc_token.json`（gitignored）
- 绝对不在代码中硬编码凭证

## Daytona 沙箱约束（Phase 2 部署时）

- 需申请 2 vCPU / 4GB RAM / 5GB disk
- 沙箱自动停止后文件系统保留 — 进化循环有 checkpoint 机制
- 避免 port 3000（Streamlit bug）
