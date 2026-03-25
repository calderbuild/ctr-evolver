---
title: Evolution Loop Launch - Switch Sites and Run First Cycle
type: feat
date: 2026-03-22
---

# Evolution Loop Launch

## Overview

项目代码已完成但从未运行过。距离比赛结束（2026-04-04）还有 13 天。需要：切换到有流量的站点、修复数据问题、本地跑通进化循环、部署到 Daytona 持续运行。

## Problem Statement

1. **站点数据不可用**：jasonrobert.me 已废弃，换为 `calderbuild.github.io`（主）和 `meetspot-irq2.onrender.com`（流量更多）
2. **CTR int64 疑似问题**：旧数据中 CTR 列为 int64 全零。可能是站点真的没点击（jasonrobert.me 太小），也可能是 parquet 类型推断。换站点后需验证
3. **评估阈值过高**：evaluator 要 100+ impressions，小站达不到。需根据新站点实际流量调整
4. **代码未提交**：大量文件 untracked，需整理提交

## Proposed Solution

### Phase 1: Fix & Validate (Day 1-2)

#### 1.1 切换站点 + 清理旧数据

- `cli.py`：把 `--site-url` 默认值从 `sc-domain:jasonrobert.me` 改为 `sc-domain:calderbuild.github.io`（或 URL-prefix 格式，取决于 GSC 中的注册方式）
- `scripts/run_evolution.sh`：同步更新默认 `SITE_URL`
- 删除 `data/gsc/` 下旧 parquet 文件（jasonrobert.me 的数据）
- **验证**：`python cli.py gsc sync --site-url "sc-domain:calderbuild.github.io" --days 90`，检查返回数据的 CTR dtype 和值

**文件**：`cli.py`（6 处默认值）、`scripts/run_evolution.sh`（2 处）

#### 1.2 验证 CTR 数据类型

同步新站点数据后：
```python
import pandas as pd
df = pd.read_parquet("data/gsc/<latest>.parquet")
print(df.dtypes)  # ctr 应为 float64
print(df[df['ctr'] > 0].head())  # 应有非零 CTR
```

如果 CTR 仍为 int64（pandas 对全零列的类型推断），在 `gsc_client.py` 的 `query_day()` 末尾强制转换：
```python
df["ctr"] = df["ctr"].astype(float)
df["position"] = df["position"].astype(float)
```

**文件**：`seo_agent/gsc_client.py:123`

#### 1.3 评估 meetspot-irq2.onrender.com 流量

- 同步数据：`python cli.py gsc sync --site-url "https://meetspot-irq2.onrender.com/" --days 90`
- 对比两个站点的页面数、展示量、点击量
- 选流量更大的作为主站点

#### 1.4 调整评估阈值

根据新站点实际流量调整 `seo_agent/evaluator.py` 中的阈值：
- 如果日均展示 < 50：`min_impressions` 降到 10-20
- 如果日均展示 > 100：保持 100 或适当降低到 50
- `CLAUDE.md` 中记录实际选择的阈值及原因

**文件**：`seo_agent/evaluator.py`

#### 1.5 端到端本地验证

按顺序跑通完整流程：
```bash
python cli.py gsc sync --days 90
python cli.py gsc status
python cli.py opportunities list --top 20 --min-impressions 5
python cli.py generate <top_page_url> --skill curiosity_gap
python cli.py evolve step
```

**完成标准**：`evolve step` 成功完成，生成至少 1 个新技能，checkpoint 文件存在。

### Phase 2: Commit & Run (Day 2-3)

#### 2.1 Git 整理提交

分 2-3 个有意义的 commit：
1. `feat: core agent and evolution engine` — seo_agent/, engine/, skills/
2. `feat: CLI and deployment config` — cli.py, scripts/, .devcontainer/, requirements.txt
3. `fix: site config and data pipeline` — Phase 1 的修复

#### 2.2 本地 Burst 模式跑 3-5 步

```bash
python cli.py evolve run --max-steps 5 --mode burst --min-impressions 5
```

目标：验证进化循环能连续运行，frontier 在更新，技能在迭代。预估成本 ~$30（5 步 x $6/步）。

用免费模型先跑 1 步确认流程无误，再切付费模型：
```bash
# 先用 llama 测试流程
# 确认无误后切 sonnet/haiku 正式跑
```

### Phase 3: Daytona Deployment (Day 3-5)

#### 3.1 部署到 Daytona

按 `docs/deployment-checklist.md` 执行：
- 推代码到 GitHub
- 创建 Daytona workspace（2 vCPU / 4GB RAM / 5GB disk）
- 验证网络：curl openrouter.ai / googleapis.com
- 复制 GSC token 和 .env 到 sandbox
- 启动 continuous 模式

#### 3.2 Continuous 模式运行

```bash
SITE_URL="..." MODE=continuous MAX_STEPS=15 bash scripts/run_evolution.sh
```

每 6h 同步 GSC → 评估 pending interventions → 进化 → 生成新技能。

### Phase 4: Research Proposal (Day 6-9)

#### 4.1 收集进化数据

从运行结果中提取：
- Frontier 演变过程（哪些技能被淘汰、哪些存活）
- Memory 积累过程（promising/failed directions）
- CTR lift 数据（如果有显著结果）
- 技能 diff（v1 → vN 的变化）

#### 4.2 撰写研究提案

覆盖三个研究方向：
- **Self-Improvement（主线）**：进化循环如何通过真实 CTR 反馈自我改进
- **Transfer Learning（定性讨论）**：框架如何迁移到其他垂直领域
- **Auto-Eval（CTR = 用户投票）**：搜索结果点击率作为自动评估信号的优劣

### Phase 5: Demo (Day 10-12)

#### 5.1 Streamlit Dashboard

端口 8501，展示：
- 进化时间线（步数 vs frontier 变化）
- 技能对比（before/after title 示例）
- CTR lift 可视化
- 实时进化状态

### Buffer: Day 13 (2026-04-04)

提交、检查、polish。

## Acceptance Criteria

- [ ] 新站点 GSC 数据同步成功，CTR 为 float 类型
- [ ] `evolve step` 本地跑通，生成新技能
- [ ] Burst 模式跑 3-5 步，frontier 有变化
- [ ] 代码 commit 到 GitHub
- [ ] Daytona 部署成功，continuous 模式运行
- [ ] 研究提案完成
- [ ] Streamlit demo 可用

## Risk Analysis

| 风险 | 影响 | 缓解 |
|------|------|------|
| 新站点流量也不够 | 评估永远 insufficient_data | 降低阈值 + 模拟评估 fallback |
| OpenRouter $100 credits 不够 | 进化步数受限 | 免费模型测试 + 控制步数 |
| Daytona 网络限制 | 无法访问 API | 提前测试 + 备选本地运行 |
| 7 天评估等待 | 比赛结束前拿不到评估结果 | burst 模式先跑 + 用 backtest 验证 |
| GSC OAuth 在 Daytona 不可用 | 需本地先完成授权 | 复制 token.json 到 sandbox |

## Dependencies

- GSC 已注册 calderbuild.github.io 和 meetspot-irq2.onrender.com
- OpenRouter API key 有效且有余额
- Daytona workspace 可创建

## References

- 进化引擎计划：`docs/plans/2026-03-19-refactor-evolution-engine-optimization-plan.md`
- 部署清单：`docs/deployment-checklist.md`
- Daytona 部署计划：`docs/plans/2026-03-19-feat-daytona-deployment-evolution-loop-plan.md`
