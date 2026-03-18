---
title: "Arena API Integration (OpenRouter / Dedalus / Daytona)"
type: feat
date: 2026-03-18
deepened: 2026-03-18
---

## Enhancement Summary

**Deepened on:** 2026-03-18
**Agents used:** cost-optimization, model-comparison, security-sentinel, performance-oracle, architecture-strategist, code-simplicity-reviewer

### Key Findings
1. **成本估算修正**：原计划 $30/step 严重高估 ~5 倍。实际 Haiku+Sonnet 混合路由下 ~$6/step，$100 可跑 ~16 步进化
2. **架构简化**：砍掉 LLMClient 封装、ModelTier enum、独立 test script。直接用 OpenAI SDK，6 行代码即可
3. **安全优先**：API.md 含明文 key，必须在 git init 前删除
4. **廉价替代模型**：Gemini Flash Lite ($0.075/$0.30) 和 DeepSeek V3 ($0.26/$0.38) 可作为 ultra-budget 选项

---

# Arena API Integration

## Overview

Sentient Arena 提供三项 $100 credits 福利。评估结论：**只接入 OpenRouter，其余延后。**

## 三项服务评估

### 1. OpenRouter ($100) -- 唯一立即接入的服务

**是什么**：LLM API 聚合平台，兼容 OpenAI SDK（改 `base_url` 即可）。零加价（OpenRouter 不加 markup，按原始模型定价收费）。$100 credits 自动获得 paid tier（无 rate limit 限制）。

**可用模型定价**：

| 模型 | Input $/M | Output $/M | 适用场景 |
|------|-----------|------------|----------|
| Gemini 2.5 Flash Lite | $0.075 | $0.30 | Ultra-budget executor |
| DeepSeek V3.2 | $0.26 | $0.38 | 高性价比全能 |
| Claude 3 Haiku | $0.25 | $1.25 | 最廉价 Claude |
| Claude 3.5 Haiku | $0.80 | $4 | 平衡选项 |
| **Claude Haiku 4.5** | **$1** | **$5** | **Tournament + Executor** |
| **Claude Sonnet 4.6** | **$3** | **$15** | **生成 + 分析** |
| Llama 3.3 70B | FREE | FREE | 开发/原型 |

### 成本模型（修正后，重要）

原计划估算 $30/step，**实际 ~$6/step**。差异来源：原估算假设全部使用 Sonnet，但 Haiku 路由后成本大幅降低。

| 组件 | 模型 | Input tokens | Output tokens | 成本 |
|------|------|-------------|---------------|------|
| Tournament 初筛（20 tasks） | Haiku 4.5 | 300K | 75K | $0.68 |
| Full eval（top 2, 60 runs） | Sonnet 4.6 | 600K | 150K | $4.05 |
| Proposer（失败分析） | Sonnet 4.6 | 30K | 10K | $0.24 |
| Skill Generator | Sonnet 4.6 | 20K | 15K | $0.29 |
| Executor（50 tasks） | Haiku 4.5 | 400K | 100K | $0.90 |
| **Step 总计** | | **~1.35M** | **~350K** | **~$6.16** |

**$100 预算容量**：

| 方案 | $/step | 可跑步数 | 备注 |
|------|--------|----------|------|
| Haiku+Sonnet 混合（推荐） | ~$6 | **~16 步** | 足够完成比赛 |
| 全 Sonnet（原估算） | ~$30 | ~3 步 | 不够用 |
| Ultra-budget（Gemini Flash） | ~$1.5 | ~66 步 | 质量存疑 |

**结论：$100 OpenRouter credits 比预期宽裕很多。无需额外资金即可完成 5 步计划。**

### 模型选择策略（效果分析）

| 任务 | 推荐模型 | 理由 |
|------|----------|------|
| Title/desc 生成 | **Sonnet 4.6** | 创意写作需要较强语言能力，心理触发器（好奇心缺口、锚定效应）需要 nuanced 理解 |
| Tournament 评估 | **Haiku 4.5** | "检测问题比生成更简单"，小模型做 judge 效果接近大模型（GPT-4o Mini 研究：78x 成本降低，精度提升） |
| 失败分析（Proposer） | **Sonnet 4.6** | 需要深入推理 why CTR 没有提升 |
| 技能生成（Generator） | **Sonnet 4.6** | 需要生成结构化 SKILL.md，质量直接影响进化方向 |
| Executor（批量执行） | **Haiku 4.5** | 按已有 skill 模板执行，不需要创造性推理 |

**进阶策略**：Week 1 开发期用 Llama 3.3 70B（免费），Week 2 真实实验切 Haiku/Sonnet。这样开发调试零成本。

### 接入方式（极简，6 行）

```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

# 用到的地方直接调用，不需要 wrapper
response = client.chat.completions.create(
    model="anthropic/claude-haiku-4.5",  # 或 anthropic/claude-sonnet-4.6
    messages=[{"role": "user", "content": prompt}],
)
text = response.choices[0].message.content
tokens_used = response.usage  # .prompt_tokens, .completion_tokens
```

**不需要 LLMClient 封装类**。理由：
- OpenAI SDK 本身就是标准化接口，所有调用方都理解
- ModelTier enum 对 2 个模型是过度设计，直接传 model 字符串
- budget 追踪在需要时加到调用处，不需要提前抽象
- 一个人三周项目，grep `client.chat.completions.create` 就能找到所有调用点

### 2. Dedalus ($100) -- 不用

AI Agent 编排平台。我们的 evolution engine 是自定义流程，加一层 Dedalus SDK 抽象增加复杂度。credits 可能是 MCP hosting 费用而非 LLM token。Demo 阶段如需 agent 展示再考虑。

### 3. Daytona ($100) -- 不用

云开发环境。Phase 2 远程实验时再接入。已在 `docs/deployment-checklist.md` 中规划。

## 决策总结

| 服务 | 决策 | 理由 |
|------|------|------|
| **OpenRouter** | 立即接入 | $100 够跑 ~16 步进化，远超需求 |
| **Dedalus** | 跳过 | 不匹配当前架构 |
| **Daytona** | 延后至 Phase 2 | 本地开发够用 |

## 实施任务（精简后只剩 2 步）

### Task 1：安全处理 API Keys（在 git init 之前）

- [ ] 创建 `.gitignore`（必须在 `git init` 之前）
- [ ] 创建 `.env` 只放 `OPENROUTER_API_KEY`（其他 key 用到时再加）
- [ ] **删除 `API.md`**（不是加到 .gitignore，而是删除。明文 key 不应存在于项目目录）
- [ ] 检查项目目录是否被 iCloud/Dropbox 同步（如果是，key 可能已泄露到云端）

```bash
# .gitignore
.env
*.key
*.pem
__pycache__/
.venv/
data/           # GSC 数据
checkpoints/    # 进化状态
```

```bash
# .env（只放当前需要的）
OPENROUTER_API_KEY=sk-or-v1-a862358d...
```

### Task 2：验证连通性（嵌入开发流程，不单独写 test script）

在写第一个需要 LLM 的模块（executor 或 proposer）时，直接验证 OpenRouter 调用。不需要独立的 `scripts/test_openrouter.py`。

如果想快速验证一下：

```python
# 一次性验证，跑完删掉
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.environ["OPENROUTER_API_KEY"])

# 免费模型测试连通性
r = client.chat.completions.create(model="meta-llama/llama-3.3-70b-instruct:free", messages=[{"role":"user","content":"ping"}])
print(r.choices[0].message.content)

# 付费模型测试
r = client.chat.completions.create(model="anthropic/claude-haiku-4.5", messages=[{"role":"user","content":"ping"}])
print(r.choices[0].message.content, r.usage)
```

## 砍掉的东西（及理由）

| 原计划内容 | 决策 | 理由 |
|-----------|------|------|
| LLMClient 封装类 | 砍掉 | OpenAI SDK 已是标准接口，无需二次封装 |
| ModelTier enum | 砍掉 | 2 个模型用字符串足够 |
| budget.py 集成 | 延后 | Week 1 开发期用免费模型，不需要预算追踪 |
| 独立 test script | 砍掉 | 开发中自然验证 |
| Dedalus/Daytona .env keys | 砍掉 | 用到时 30 秒加上 |
| 方案 B（裸 requests） | 砍掉 | OpenAI SDK 更好，没理由用 requests |

## 对主计划的影响

**需要更新 `2026-03-15-feat-seo-ctr-self-evolving-agent-plan.md` 中的成本模型**：

- `~$30/step` → `~$6/step`（Haiku+Sonnet 混合路由）
- `5 steps = ~$150` → `5 steps = ~$30`（OpenRouter $100 credits 绰绰有余）
- `4M token/step` → `~1.7M token/step`（token 估算也偏高）
- 可以考虑增加进化步数（从 5 步增加到 10-15 步），因为预算充裕

## Acceptance Criteria

- [ ] `API.md` 已删除（不是隐藏，是删除）
- [ ] `.gitignore` 在 `git init` 之前就位
- [ ] `.env` 只含 `OPENROUTER_API_KEY`
- [ ] 能成功调用 OpenRouter（Haiku 4.5 + Sonnet 4.6）
