---
title: "Phase 2: Daytona Deployment + Real Evolution Loop"
type: feat
date: 2026-03-19
---

# Phase 2: Daytona 部署 + 真实进化循环

## 背景

Phase 1 代码已完成（GSC client、机会识别、executor、evaluator、intervention、evolution engine、4 个种子技能）。但尚未：
- 同步过真实 GSC 数据
- 跑过完整 evolve step
- 初始化 git repo
- 部署到 Daytona

距截止日 2026-04-04 还有 ~2.5 周。需要尽快在真实数据上跑通循环，收集足够的进化迭代数据。

## 目标

在 Daytona sandbox 上持续运行进化循环，收集 10+ 步进化数据用于 demo 和研究提案。

## 非目标

- Streamlit demo（Phase 3）
- 研究提案撰写（Phase 3）
- 多站点支持

## 风险

| 风险 | 影响 | 缓解 |
|------|------|------|
| Daytona 15 分钟自动停止 | 进化循环被中断 | checkpoint 机制 + 幂等 resume |
| GSC 数据量不足（小站点） | 机会识别筛不出结果 | 降低 min_impressions 阈值 |
| 网络限制（Tier 1-2） | 无法调用 OpenRouter/GSC API | 申请 Tier 3 或提交 whitelist |
| 免费模型 rate limit | 开发期无法测试 | 本地验证用付费模型小量测试 |

## 兼容性

无破坏性变更。新增 checkpoint 机制和 devcontainer 配置，不改变现有接口。

---

## 实施步骤

### Step 1: 本地验证 — 真实 GSC 数据 (~30min)

**描述**: 在本地同步真实 GSC 数据，验证完整 pipeline。

**文件**: 无新增，使用现有 CLI

**任务**:
- [ ] `python cli.py gsc sync --site-url "sc-domain:jasonrobert.me" --days 90`
- [ ] `python cli.py gsc status` — 确认数据量
- [ ] `python cli.py opportunities list --top 10` — 确认能筛出机会
- [ ] 如果 min_impressions=200 筛不出结果，降低到 50 或 100
- [ ] `python cli.py generate <page_url> --skill curiosity_gap` — 用付费模型测试一次生成

**验收**: opportunities list 输出 >= 5 条机会，generate 输出合理的 title/desc

---

### Step 2: Checkpoint + Resume 机制 (~1h)

**描述**: evolution engine 需要在每步之后持久化状态，sandbox 重启后能从上次中断处继续。

**文件**:
- `engine/evolution.py` — 添加 checkpoint 逻辑
- `data/checkpoint.json` — 进化状态快照

**任务**:
- [ ] 在 `SEOEvolutionEngine` 中添加 `_save_checkpoint(step_num, result)` — 每步完成后写 `data/checkpoint.json`
- [ ] 添加 `_load_checkpoint() -> dict | None` — 启动时读取上次状态
- [ ] 添加 `run(max_steps, start_from_checkpoint=True)` — 多步循环，支持断点续跑
- [ ] checkpoint 内容：`step_num`, `timestamp`, `last_result`, `frontier_state`
- [ ] 原子写入（tmpfile + rename）

**约束**: checkpoint 只记录"跑到第几步"，不缓存 LLM 响应。重跑一步的成本 ~$6，可接受。

**验收**: 手动 kill 进程后重启，能从上次完成的步骤继续

---

### Step 3: Git 初始化 + 远程仓库 (~20min)

**描述**: 初始化 git repo，推送到 GitHub，为 Daytona 部署做准备。

**文件**:
- 现有 `.gitignore`（已配置好）

**任务**:
- [ ] `git init && git add -A && git commit -m "Phase 1: SEO CTR evolution engine MVP"`
- [ ] 创建 GitHub private repo
- [ ] `git remote add origin git@github.com:<user>/<repo>.git`
- [ ] `git push -u origin main`（走 SSH 代理）
- [ ] 确认 `.env`, `config/gsc_*.json`, `data/` 未被提交

**验收**: GitHub 上能看到完整代码，无敏感文件

---

### Step 4: Daytona 配置 (~1h)

**描述**: 创建 devcontainer 配置，申请资源，处理网络和凭证。

**文件**:
- `.devcontainer/devcontainer.json` — Daytona workspace 配置
- `scripts/setup.sh` — sandbox 初始化脚本

**任务**:
- [ ] 创建 `.devcontainer/devcontainer.json`:
  ```json
  {
    "image": "mcr.microsoft.com/devcontainers/python:3.12",
    "postCreateCommand": "pip install -r requirements.txt",
    "forwardPorts": [8501],
    "customizations": {
      "daytona": {
        "resources": {
          "cpu": 2,
          "memory": "4Gi",
          "disk": "5Gi"
        }
      }
    }
  }
  ```
- [ ] 创建 `requirements.txt`（从 environment.yml 提取 pip 依赖）
- [ ] 创建 `scripts/setup.sh` — 设置环境变量、注入凭证
- [ ] 申请 Daytona Tier 3 网络权限（或提交 whitelist: `openrouter.ai`, `googleapis.com`）
- [ ] 规划 GSC 凭证注入方式：sandbox 启动后手动写入 `config/gsc_token.json`，或通过环境变量

**约束**: GSC OAuth Desktop flow 在 headless sandbox 中无法运行浏览器。需要在本地完成 OAuth，然后把 token 文件复制到 sandbox。

**验收**: `daytona create <repo-url>` 成功创建 workspace，`python cli.py gsc status` 能运行

---

### Step 5: 远程进化循环 (~2h setup, 持续运行)

**描述**: 在 Daytona sandbox 上启动进化循环，收集真实数据。

**文件**:
- `scripts/run_evolution.sh` — 进化循环启动脚本
- `cli.py` — 添加 `evolve run` 命令（多步循环）

**任务**:
- [ ] 在 CLI 添加 `evolve run --max-steps 15 --site-url <url>` 命令
  - 调用 `SEOEvolutionEngine.run(max_steps=15)`
  - 每步之间 sleep 等待新数据（或立即继续，取决于是否有新的 pending interventions）
- [ ] 创建 `scripts/run_evolution.sh`:
  ```bash
  #!/bin/bash
  source .env
  python cli.py gsc sync --days 90
  python cli.py evolve run --max-steps 15
  ```
- [ ] 复制 GSC token 到 sandbox: `daytona cp config/gsc_token.json <workspace>:config/gsc_token.json`
- [ ] 设置 sandbox 环境变量: `OPENROUTER_API_KEY`
- [ ] 启动进化循环
- [ ] 验证 checkpoint 写入正常
- [ ] 每天检查进度，手动 resume 如果 sandbox 被停止

**约束**:
- 15 分钟自动停止 — 每步 evolve 需要在 15 分钟内完成（预计 2-5 分钟/步，OK）
- 如果 sandbox 停止，SSH 进去运行 `scripts/run_evolution.sh` 即可 resume

**验收**: 成功在 Daytona 上跑完 >= 3 步进化，checkpoint 文件存在

---

### Step 6: 模型切换 — 免费 → 付费 (~15min)

**描述**: 开发验证完成后，切换到付费模型获得更好的生成质量。

**文件**:
- `seo_agent/executor.py` — 改 DEFAULT_MODEL
- `engine/proposer.py` — 改 DEFAULT_MODEL
- `engine/skill_generator.py` — 改 DEFAULT_MODEL

**任务**:
- [ ] executor.py: 生成用 `anthropic/claude-sonnet-4.6`
- [ ] proposer.py: 分析用 `anthropic/claude-sonnet-4.6`
- [ ] skill_generator.py: 生成用 `anthropic/claude-sonnet-4.6`
- [ ] 批量执行（backtest）保持 `anthropic/claude-haiku-4.5`
- [ ] 验证一次完整 step 的实际成本

**验收**: 一步 evolve step 成本 < $8

---

## 时间线

| 日期 | 里程碑 |
|------|--------|
| 03-19 | Step 1-2: 本地验证 + checkpoint |
| 03-20 | Step 3-4: Git + Daytona 配置 |
| 03-21 | Step 5-6: 远程循环启动 + 模型切换 |
| 03-21 ~ 03-28 | 持续运行进化循环，收集 10+ 步数据 |
| 03-28 | Phase 3 开始：Streamlit demo + 研究提案 |

## 验证方式

```bash
# 在 Daytona sandbox 上
python cli.py gsc status          # 确认数据
python cli.py opportunities list  # 确认机会
python cli.py evolve run --max-steps 3  # 跑 3 步验证
cat data/checkpoint.json          # 确认 checkpoint
ls skills/                        # 确认新技能生成
cat skills/frontier/active_skills.json  # 确认前沿更新
```
