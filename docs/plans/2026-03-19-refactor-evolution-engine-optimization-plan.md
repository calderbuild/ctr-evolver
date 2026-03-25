---
title: "Evolution Engine Optimization — Incorporating EvoScientist + autoresearch Patterns"
type: refactor
date: 2026-03-19
---

# 进化引擎优化 — 融合 EvoScientist + autoresearch 模式

## 背景

Phase 1 已完成基础进化循环（Proposer -> Generator -> Evaluator -> Frontier）。Phase 2 部署计划已就绪。

调研了两个高质量参考项目：
- **EvoScientist**（Sentient 官方，3 agent + 2 persistent memory + 3 evolution types + Elo tournament）
- **autoresearch**（Karpathy，program.md as skill + results.tsv append-only + NEVER STOP loop + git branch per run）

当前引擎存在几个可优化点，这两个项目提供了经过验证的解决方案。

## 目标

在不重写核心架构的前提下，引入 3 个高价值改进，提升进化质量和自主运行能力。

## 非目标

- 不引入 3-agent 架构（EvoScientist 的 Researcher/Engineer/Evolution Manager 分离对我们的规模过度设计）
- 不做 git branch per experiment（我们用 JSONL + checkpoint 已够用）
- 不做 Elo tournament（数据量不够，Pareto frontier 已足够）

## 风险

| 风险 | 影响 | 缓解 |
|------|------|------|
| 改动过多导致 Phase 2 部署延迟 | 错过数据收集窗口 | 严格限制改动范围，每个改进独立可合并 |
| persistent memory 增加 token 消耗 | 成本上升 | memory 内容限制在 2000 tokens 以内 |

## 兼容性

所有改动向后兼容。现有 interventions.jsonl、checkpoint.json、active_skills.json 格式不变。

---

## 调研发现

### autoresearch 关键模式

1. **program.md 即技能**：整个实验逻辑写在一个 markdown 文件中，LLM 每次读取并执行。我们的 SKILL.md 已经是这个模式，验证了方向正确。

2. **results.tsv append-only 日志**：每次实验结果追加到 TSV 文件，LLM 下次运行时读取全部历史来决策。关键洞察：**让 LLM 看到完整历史，而不是只看最近一步的评估结果**。

3. **NEVER STOP 自主循环**：program.md 中明确写 "NEVER stop running experiments"，循环结构是 `while True: propose -> run -> evaluate -> keep/discard`。keep/discard 决策由 LLM 自主做出。

4. **极简状态管理**：没有复杂的状态机，只有 results.tsv 一个文件。所有决策上下文都从这个文件重建。

### EvoScientist 关键模式

1. **两种持久化记忆**：
   - **Ideation Memory**：记录"哪些方向有前途"（从 top-ranked ideas 中总结）和"哪些方向已失败"（从低分 ideas 中总结）
   - **Experimentation Memory**：记录"可复用的实验策略"（从成功实验的代码轨迹中蒸馏）

2. **三种进化类型**（Evolution Manager 的核心）：
   - **Idea Direction Evolution**：总结 top-ranked ideas 的共性方向 → 更新 ideation memory
   - **Idea Validation Evolution**：记录失败方向 → 更新 ideation memory 的"避免"列表
   - **Experiment Strategy Evolution**：从成功实验中提取可复用的执行模式 → 更新 experimentation memory

3. **Elo-based Tournament Selection**：用 Elo 评分系统对 ideas 排名，而非简单的 win/loss 统计。

4. **Tree Search for Idea Generation**：ideas 形成树结构，新 idea 可以是已有 idea 的变体（mutation）或组合（crossover）。

---

## 改进方案（3 个独立改进）

### 改进 1: Persistent Evolution Memory (~1.5h)

**来源**: EvoScientist 的 ideation memory + experimentation memory

**问题**: 当前 Proposer 只看 `feedback_history.txt`（纯文本追加），没有结构化的"什么有效/什么无效"记忆。每次提案都从头分析失败，容易重复提出已失败的方向。

**方案**: 新增 `data/evolution_memory.json`，包含两个结构化记忆：

```json
{
  "promising_directions": [
    {
      "direction": "数字锚定在 position 4-10 效果最好",
      "evidence": "number_hook win_rate 0.65 at pos 4-10, 0.30 at pos 1-3",
      "updated_at": "2026-03-20T10:00:00Z"
    }
  ],
  "failed_directions": [
    {
      "direction": "loss_aversion 在 informational intent 查询上无效",
      "evidence": "3 次实验 CTR lift < 0",
      "updated_at": "2026-03-20T10:00:00Z"
    }
  ],
  "effective_patterns": [
    {
      "pattern": "在 description 中包含具体数字时 CTR 提升更大",
      "source_skills": ["number_hook", "curiosity_gap_v2"],
      "updated_at": "2026-03-20T10:00:00Z"
    }
  ]
}
```

**文件改动**:
- `engine/memory.py`（新增）— `EvolutionMemory` 类，load/save/update
- `engine/proposer.py` — `analyze_failures()` 和 `propose_strategy()` 接收 memory 参数
- `engine/evolution.py` — step() 中在评估后更新 memory，在提案时传入 memory

**约束**:
- 每个列表最多 10 条（FIFO 淘汰旧条目）
- memory 更新由 LLM 完成（在 analyze_failures 的 prompt 中要求输出结构化 memory update）
- 总 token 消耗 < 2000 tokens

**验收**: proposer 的 prompt 中包含 memory 内容，生成的提案不重复已知失败方向

---

### 改进 2: 完整历史可见的评估 (~1h)

**来源**: autoresearch 的 results.tsv 模式

**问题**: 当前 `step()` 只评估 pending interventions，Proposer 只看当前步的失败。LLM 无法看到跨步骤的趋势（比如"number_hook 连续 3 步都在 position 4-10 表现好"）。

**方案**: 在 Proposer 的 prompt 中注入最近 N 步的完整评估摘要。

```python
def _build_history_summary(max_steps: int = 5) -> str:
    """从 interventions.jsonl 构建最近 N 步的评估摘要表。"""
    all_interventions = intervention.load_interventions(status="evaluated")
    # 按 skill 聚合: skill_name | total | wins | avg_lift | best_query
    # 返回 markdown 表格
```

**文件改动**:
- `engine/proposer.py` — `analyze_failures()` prompt 中增加历史摘要表
- `seo_agent/intervention.py` — 新增 `get_evaluation_summary()` 辅助函数

**约束**: 摘要限制在 20 行以内，避免 token 爆炸

**验收**: Proposer 的分析输出引用了跨步骤的趋势

---

### 改进 3: NEVER STOP 自主循环 (~1h)

**来源**: autoresearch 的 NEVER STOP 模式

**问题**: 当前 `run()` 是固定 max_steps 循环，每步都生成新干预。但在真实场景中：
- GSC 数据每天更新一次，不需要每分钟跑
- 应该在"有新数据"时才触发评估
- sandbox 15 分钟自动停止，需要更智能的循环策略

**方案**: 改造 `run()` 为两种模式：

```python
def run(self, max_steps=15, mode="burst"):
    """
    mode="burst": 连续跑 max_steps 步（当前行为，用于回测/初始化）
    mode="continuous": 持续运行，每次检查是否有新数据，有则 step()
    """
```

continuous 模式逻辑：
1. 检查上次 sync 时间，如果 > 6h 则 sync
2. 检查是否有 pending interventions 可评估（需要 7 天数据）
3. 如果有可评估的 → evaluate + evolve
4. 如果机会列表有变化 → 生成新干预
5. 写 checkpoint，sleep 到下次检查

**文件改动**:
- `engine/evolution.py` — `run()` 增加 continuous 模式
- `cli.py` — `evolve run` 增加 `--mode continuous` 选项
- `scripts/run_evolution.sh` — 改为 continuous 模式

**约束**:
- continuous 模式下每次循环间隔 >= 1h（避免无意义的 API 调用）
- 仍然受 max_steps 限制（安全阀）
- checkpoint 记录 last_sync_time，resume 时跳过不必要的 sync

**验收**: `python cli.py evolve run --mode continuous --max-steps 15` 能智能等待新数据

---

## 优先级排序

| 改进 | 价值 | 工作量 | 优先级 |
|------|------|--------|--------|
| 1. Persistent Memory | 高（直接提升进化质量） | 1.5h | P0 |
| 2. 完整历史可见 | 中（改善 Proposer 决策） | 1h | P0 |
| 3. NEVER STOP 循环 | 中（提升自主运行能力） | 1h | P1 |

建议顺序：先做 1 和 2（它们互相增强），再做 3。

## 时间线

| 日期 | 任务 |
|------|------|
| 03-19 | 改进 1 + 2 实现 |
| 03-20 | 改进 3 实现 + Git push + Daytona 部署 |
| 03-20 ~ 03-28 | continuous 模式运行，收集进化数据 |

## 验证方式

```bash
# 验证 memory
cat data/evolution_memory.json

# 验证历史可见
python cli.py evolve step  # 观察 proposer 输出是否引用历史

# 验证 continuous 模式
python cli.py evolve run --mode continuous --max-steps 3
```
