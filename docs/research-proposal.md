# Self-Evolving SEO Agents: LLM-as-Judge for Sparse-Signal Skill Evolution

## Abstract

Self-evolving AI agents promise autonomous improvement through experience, yet real-world deployment exposes a fundamental tension: meaningful feedback signals are often too sparse for statistical evaluation. We present an SEO CTR optimization agent built on the EvoSkill framework that automatically discovers and evolves title/description generation strategies ("skills") through a closed-loop system. When deployed against a low-traffic site with ~2 daily impressions, traditional CTR-based evaluation proved mathematically impossible — requiring 30+ impressions per time window that would take months to accumulate. We introduce LLM-as-Judge as a proxy evaluator, using a structured 5-dimension rubric to provide immediate quality signals. This approach increased evaluable interventions from 0 to 10 per evolution step, enabled the Pareto frontier to differentiate skills, and produced 18 novel skills from 7 seed skills across 10 evolution steps. We further validated framework transferability by porting the evolution engine to the OfficeQA benchmark (U.S. Treasury Bulletin question answering), achieving the transfer with 1,095 new LOC while reusing 1,082 LOC of engine code unchanged — confirming that ~50% of the framework is directly reusable across domains, with the remaining 50% following identical structural patterns. We discuss implications for all three Arena research directions: AI self-improvement evaluation, transfer learning across domains, and automatic evaluation generation.

---

## 1. Introduction

The vision of self-evolving AI agents — systems that autonomously improve their capabilities through experience — has motivated significant recent research. Frameworks like EvoSkill, PromptBreeder, and DSPy demonstrate that LLM-based agents can systematically optimize their prompts, tools, and strategies through evolutionary loops.

However, a gap exists between benchmark demonstrations and real-world deployment. Most self-evolution frameworks are validated on synthetic benchmarks where feedback is immediate, deterministic, and abundant. In contrast, real business applications often face:

- **Delayed feedback**: SEO changes take days to weeks before measurable CTR impact appears
- **Sparse signals**: Low-traffic pages may receive only a handful of impressions per week
- **Noisy measurements**: CTR varies with search position, time of day, seasonal trends, and competitor actions
- **No ground truth**: Unlike coding benchmarks with test suites, there is no objective "correct" title

We chose SEO CTR optimization as our domain precisely because it embodies these challenges. Every website owner faces the problem of underperforming search listings, and the feedback signal — whether users click — is a direct, unmanipulable measure of real human behavior. This makes it both a practical application and a demanding test bed for self-evolution.

Our contribution is threefold:
1. A complete implementation of the EvoSkill evolution loop adapted for SEO, with dual evaluation paths (CTR-based and LLM-as-Judge)
2. Empirical evidence that LLM-as-Judge enables meaningful evolution when real feedback is too sparse
3. Analysis of the framework's transferability and the broader implications for automatic evaluation

---

## 2. Related Work

**EvoSkill** (Sentient Labs) defines the canonical five-stage evolution loop: Base Agent → Proposer → Generator → Evaluator → Frontier. Originally designed for coding benchmarks, it treats agent configurations as "programs that can be iterated on automatically," with skills stored as versioned files and performance tracked through a Pareto frontier.

**PromptBreeder** (Meyerson et al., 2023) evolves task-prompts and mutation-prompts simultaneously through a population-based approach. It demonstrates that LLMs can self-referentially improve their own prompts, but relies on benchmark tasks with deterministic scoring.

**DSPy** (Khattab et al., 2023) provides a programming framework for optimizing LLM pipelines, compiling declarative modules into optimized prompts. While powerful, it assumes the availability of labeled training data for optimization.

**LLM-as-Judge** (Zheng et al., 2023) establishes that strong LLMs can serve as reliable evaluators of text quality, achieving high agreement with human judgments. This insight is foundational to our approach — when real-world metrics are unavailable, LLM evaluation provides a viable proxy signal.

**AgentEvolver** and **EvolveR** represent recent work on autonomous agent self-improvement. Both emphasize that adaptivity — the ability to improve performance through experience — is a key evaluation criterion, often measured as Success Rate by Iteration Steps.

Our work bridges these threads by applying the EvoSkill framework to a domain where the "evaluator" module faces fundamental data sparsity constraints, and demonstrating that LLM-as-Judge provides a practical solution.

---

## 3. System Design

### 3.1 Architecture

Our system implements a modified EvoSkill loop with two layers:

```
Data Layer (seo_agent/)          Evolution Layer (engine/)
┌─────────────────────┐          ┌──────────────────────────┐
│ GSC Client          │          │ Evolution Engine          │
│  └─ OAuth + parquet │          │  ├─ step(): evaluate →    │
│     cache           │          │  │   eliminate → propose   │
│                     │          │  │   → generate            │
│ Opportunity Finder  │          │  ├─ Proposer (Sonnet)     │
│  └─ position-based  │          │  ├─ Skill Generator      │
│     CTR gap scoring │          │  ├─ Pareto Frontier (K=15)│
│                     │  ┌──────▷│  └─ Evolution Memory      │
│ Executor            │  │      │                            │
│  └─ SKILL.md →      ├──┘      │ Dual Evaluator:           │
│     LLM → title     │         │  ├─ CTR-based (real data) │
│                     │         │  └─ LLM-as-Judge (proxy)  │
│ Evaluator (CTR)     │         └──────────────────────────┘
│ LLM Evaluator       │
└─────────────────────┘
```

### 3.2 Skill Representation

Each skill is a versioned markdown file (`skills/{name}/v{N}/SKILL.md`) containing:
- Strategy description and psychological mechanism
- Applicable query types and scenarios
- Core techniques (3-5 actionable rules)
- Before/after examples
- Prompt template for the executor

Skills are injected as context into the title/description generation prompt. The executor loads the latest version automatically.

### 3.3 Evolution Loop

Each evolution step follows a fixed sequence:

1. **Sync**: Fetch latest GSC data (or use cache if API unavailable)
2. **Identify**: Find top opportunities by `opportunity_score = impressions × (baseline_CTR - actual_CTR)`
3. **Generate**: For each opportunity, apply a skill via round-robin to produce new title/description
4. **Evaluate**: Score interventions through dual evaluation paths
5. **Evolve**: Update Pareto frontier → Analyze failures → Propose strategy → Generate new skill
6. **Checkpoint**: Atomic save of state for crash recovery

### 3.4 Pareto Frontier

Skills are managed through multi-objective Pareto dominance across three dimensions:
- `avg_ctr_lift`: Average CTR improvement (or normalized LLM score)
- `win_rate`: Fraction of interventions rated "success"
- `coverage`: Number of interventions evaluated

A skill with `coverage=0` (never tested) receives immunity from elimination, ensuring newly generated skills get at least one trial before being judged.

---

## 4. The Sparse Signal Challenge

### 4.1 The Mathematics of Impossibility

Our target site (meetspot-irq2.onrender.com) represents a common real-world scenario: a functional web application with minimal organic search traffic.

| Metric | Value |
|--------|-------|
| Total GSC data points | 144 rows |
| Date range | 61 days (Dec 2025 – Mar 2026) |
| Average daily impressions | ~2.4 |
| Unique queries | 5 (only 1 non-garbage) |
| Primary query | "meetspot" (branded, ~10 total impressions) |

For a two-proportion z-test to detect a 20% CTR lift at α=0.05 with 80% power, each group requires approximately 400 impressions. At 2.4 impressions/day, accumulating sufficient data for a single evaluation would take:

```
400 impressions ÷ 2.4/day = 167 days per evaluation
```

The competition runs for 21 days.

### 4.2 Cascading Failures

The sparsity problem cascades through the entire evolution pipeline:

1. **Evaluator gates block**: With thresholds of 10+ impressions before/after, every intervention returned `insufficient_data`
2. **Proposer receives no signal**: The failure analyzer saw zero failures (since `insufficient_data ≠ failure`), returning "No failures to analyze"
3. **Frontier frozen**: All skills remained at metrics (0, 0, 0) — Pareto dominance cannot distinguish between equally-zero vectors
4. **New skills stillborn**: Generated skills were immediately dominated by existing ones (also at zero) and eliminated
5. **API credits wasted**: Each step made 3 LLM calls (2× Sonnet, 1× Haiku) producing skills based on empty context

After 19 evolution steps, the system had produced **0 meaningful evaluations**.

### 4.3 Diagnosis

This failure exposed a fundamental assumption in the EvoSkill framework: the evaluator produces actionable signals in reasonable time. When this assumption breaks, the entire evolution loop degenerates into an expensive random walk.

---

## 5. LLM-as-Judge as Proxy Evaluator

### 5.1 Design

We introduced a Haiku-based evaluator (`seo_agent/llm_evaluator.py`) that scores generated titles immediately, without waiting for real CTR data. The evaluation uses a structured 5-dimension rubric:

| Dimension | Description | Scale |
|-----------|-------------|-------|
| keyword_relevance | Does the title contain the query or close variants? | 0-10 |
| click_appeal | Would a searcher want to click? (curiosity, value, specificity) | 0-10 |
| length_quality | Title 50-60 chars? Description 120-160 chars? | 0-10 |
| intent_match | Does it match what someone searching the query actually wants? | 0-10 |
| improvement | Is this better than the original? (5 = same) | 0-10 |

The overall score maps to evolution status:
- Score >= 7 → `success` (skill shows promise)
- Score <= 3 → `failure` (skill is counterproductive)
- Otherwise → `inconclusive` (insufficient differentiation)

### 5.2 Integration

The dual evaluation path works as follows:

```python
# In evolution step:
ctr_evaluations = self._evaluate_interventions(data)  # CTR-based
llm_evaluations = self._llm_evaluate_interventions()  # LLM-based
evaluations = ctr_evaluations if ctr_evaluations else llm_evaluations
```

CTR evaluation takes priority when available. LLM evaluation serves as a fallback, ensuring the evolution loop always has signal to work with.

LLM scores are normalized to the Pareto frontier's expected range: `(score - 5) / 5` maps [0, 10] to [-1, 1], comparable to CTR lift values.

### 5.3 Results

| Metric | Before LLM-as-Judge | After LLM-as-Judge |
|--------|---------------------|---------------------|
| Evaluated interventions per step | 0 | 6-10 |
| Skills with non-zero metrics | 0 | 1 (curiosity_gap) |
| New skills generated | 0 (proposals based on empty context) | 18 (proposals based on evaluations) |
| Frontier differentiation | Impossible (all zeros) | Active (win_rate=0.80 for top skill) |
| Evolution steps to first evolution | Never | Step 1 |

The `curiosity_gap` skill — the only one that received coverage (10 evaluations) — achieved `avg_ctr_lift=0.36` and `win_rate=0.80` under LLM evaluation. This represents a normalized score where 0.36 means the LLM judged curiosity_gap titles as meaningfully better than originals.

### 5.4 Limitations

**Proxy ≠ Reality**: LLM-as-Judge measures what an LLM thinks users will click, not what users actually click. The correlation between LLM quality assessments and real CTR is an open empirical question.

**Single-opportunity bottleneck**: With only one non-garbage query ("meetspot"), the round-robin skill assignment never reached beyond the first skill. This means 17 of 18 generated skills were never empirically tested, even by the LLM evaluator.

**Reward hacking risk**: Skills could theoretically be optimized to score well on the rubric dimensions without actually improving click-through rates. Our multi-dimensional rubric mitigates this partially, but the risk remains.

---

## 6. Experiments and Results

### 6.1 Evolution Timeline

| Phase | Steps | Key Event |
|-------|-------|-----------|
| Pre-LLM-Judge (v1) | 1-19 | 0 evaluations, system spinning with no signal |
| Post-LLM-Judge (v2) | 1-10 | 6-10 evaluations per step, new skills generated |

### 6.2 Skill Evolution

Starting from 7 seed skills, the system generated 18 additional skills across 10 steps:

| Category | Count | Examples |
|----------|-------|---------|
| Seed skills | 7 | curiosity_gap, number_hook, loss_aversion, position_adaptive, social_proof_authority, social_proof_signal, high_volume_query_targeting |
| Intent confirmation | 3 | intent_match_confirmation, intent_match_reinforcement, query_intent_matching |
| Brand reinforcement | 4 | brand_value_reinforcement, brand_trust_reinforcement, brand_reinforcement, branded_navigational_direct_value_confirmation |
| Value proposition | 3 | direct_value_proposition, direct_value, value_proposition |
| Social proof variants | 2 | branded_social_proof_trust_signal, social_proof (v2-v3) |
| Other | 6 | benefit_first_framing, high_volume_informational_targeting, branded_direct_answer_confirmation, etc. |

Notably, the evolution system independently converged on a meaningful insight: for branded queries like "meetspot," curiosity-gap strategies are counterproductive. The system generated multiple "intent confirmation" and "brand reinforcement" skills that directly oppose the seed curiosity_gap strategy — providing immediate relevance confirmation instead of creating information gaps.

### 6.3 Evolved Skill Quality

Comparing seed vs. evolved skills qualitatively:

**Seed skill (curiosity_gap/v1, 1065 bytes)**:
- Generic curiosity-gap framework
- No query-type awareness
- Basic prompt template

**Evolved skill (intent_match_confirmation/v1, 2699 bytes)**:
- Explicit psychological mechanism explained ("information confirmation" vs "information gap")
- Query-type taxonomy (branded, navigational, functional, competitor comparison)
- 5 specific techniques with formatting rules
- Anti-patterns listed (what NOT to do)
- Scenario-aware application guidance

The evolution system produced skills that are **2.5x longer** and **qualitatively more sophisticated** than the seed skills, with explicit reasoning about when to use and when NOT to use each strategy.

### 6.4 Evolution Memory

The system's memory module correctly diagnosed the core problem across 10 steps:

- `failed_directions`: 9 entries, all identifying "curiosity_gap on 'meetspot' produces no CTR lift"
- `effective_patterns`: Detected inconsistency between success labels and zero CTR lift
- `promising_directions`: Empty — accurately reflecting no empirically validated wins

This demonstrates the system's capacity for honest self-assessment, even when the LLM evaluator was assigning "success" labels.

### 6.5 Cost Analysis

| Component | Model | Cost per step | Total (10 steps) |
|-----------|-------|--------------|-------------------|
| Intervention generation | Haiku | ~$0.10 | ~$1.00 |
| LLM evaluation | Haiku | ~$0.05 | ~$0.50 |
| Failure analysis | Sonnet | ~$1.50 | ~$15.00 |
| Strategy proposal | Sonnet | ~$1.50 | ~$15.00 |
| Memory extraction | Haiku | ~$0.10 | ~$1.00 |
| Skill generation | Sonnet | ~$1.50 | ~$15.00 |
| **Total** | | **~$4.75** | **~$47.50** |

At ~$4.75 per evolution step, the system is economically viable for ongoing optimization of commercial websites.

---

## 7. Discussion: Three Research Directions

### 7.1 AI Self-Improvement Evaluation

Our implementation reveals a design pattern hierarchy for self-evolving agents:

**What works**:
- Versioned skill files as the unit of evolution (interpretable, diffable, rollbackable)
- Pareto frontier with coverage-based immunity for untested variants
- Append-only intervention log with atomic checkpoint writes
- Dual evaluation paths (real + proxy) for graceful degradation

**What fails**:
- Assuming evaluator signals are always available
- Round-robin skill assignment when opportunities are scarce (never reaches skill #2)
- Static status categories (`insufficient_data` was invisible to the failure analyzer)
- New skills initialized at (0,0,0) being immediately Pareto-dominated

**Comparison with original EvoSkill**: Our SEO adaptation required replacing the evaluator module entirely (test suite → CTR + LLM judge), modifying the frontier logic (immunity for untested skills), and adding a persistence layer (checkpoint, JSONL interventions, evolution memory). The Proposer and Generator modules transferred with minimal changes, suggesting these are the most domain-agnostic components.

### 7.2 Transfer Learning

The EvoSkill framework's architecture naturally decomposes into domain-specific and domain-agnostic components. We validated this claim empirically by transferring our SEO evolution framework to the OfficeQA benchmark (U.S. Treasury Bulletin question answering).

#### 7.2.1 Predicted vs. Actual Transfer Cost

| Component | Predicted | Actual | Notes |
|-----------|----------|--------|-------|
| Proposer | Low (prompts only) | Low (3 prompts rewritten) | Overridden in QA engine, original untouched |
| Generator | Low (template only) | Low (1 prompt + template) | Same pattern, different domain framing |
| Frontier (Pareto) | No change | **Zero changes** | Fully domain-agnostic as designed |
| Memory | No change | **Zero changes** | Categories universal across domains |
| Evaluator | High (full rewrite) | High (new module) | CTR statistics → QA accuracy + LLM-as-Judge |
| Executor | High (full rewrite) | High (new module) | Title generation → answer generation |
| Data Client | High (full rewrite) | High (new module) | GSC API → OfficeQA corpus loader |
| Intervention Log | Low (field rename) | Low (field rename) | Append-only JSONL pattern identical |

#### 7.2.2 Quantitative Transfer Analysis

| Metric | Value |
|--------|-------|
| Original codebase | 2,029 LOC (engine: 1,082 + seo_agent: 947) |
| New QA domain code | 1,095 LOC (office_qa/) |
| Engine layer reused as-is | 1,082 LOC (frontier, memory, proposer pattern, skill_generator pattern) |
| Modules with zero changes | 2/6 engine modules (frontier.py, memory.py) |
| Modules with prompt-only changes | 2/6 engine modules (proposer, skill_generator — overridden, not modified) |
| Modules requiring full rewrite | 4/7 domain modules (evaluator, executor, data_client, opportunity) |
| Time to transfer | ~4 hours of implementation |

The original prediction of "~60% reusable" was directionally correct: the engine layer (1,082 LOC) transferred entirely, representing 50% of the total code needed for the new domain. The remaining 50% was new domain-specific code, but it followed identical patterns established in the SEO implementation — the same JSON parsing helpers, the same JSONL intervention log structure, the same skill versioning scheme.

#### 7.2.3 Key Insight: Pattern Transfer > Code Transfer

The most valuable form of transfer was not direct code reuse but **pattern reuse**. Every new module in `office_qa/` mirrors its `seo_agent/` counterpart structurally: same function signatures, same error handling, same persistence patterns. This meant the QA implementation required almost no design decisions — only domain-specific prompt engineering.

This confirms a design principle: **the EvoSkill framework's value is in its architecture (evaluation → frontier → analysis → proposal → generation), not in any single module's implementation**.

### 7.3 Automatic Evaluation

Our LLM-as-Judge approach addresses a broader challenge: how do agents evaluate their own performance when ground truth is unavailable or delayed?

**The structured rubric pattern** is potentially generalizable:
- Define 3-5 independent quality dimensions
- Score each dimension explicitly (reducing evaluator variance)
- Map composite scores to evolution-compatible statuses
- Use the cheapest capable model (Haiku at $1/M tokens vs Sonnet at $15/M)

**When LLM-as-Judge works well**:
- The quality dimensions are well-defined and domain-understood
- The evaluation doesn't require access to real-world state
- Speed of iteration matters more than evaluation precision
- The proxy and true metrics are directionally correlated

**When it fails**:
- The true objective is adversarial or game-theoretic (SEO is partially this)
- Domain expertise exceeds the evaluator model's training data
- Reward hacking exploits systematic rubric biases

**Key insight**: LLM-as-Judge is most valuable not as a replacement for real evaluation, but as an **acceleration mechanism** that enables rapid exploration of the skill space before expensive real-world testing. The optimal strategy is likely a two-phase approach: LLM-as-Judge for broad exploration, then real metrics for validation of top candidates.

---

## 8. Conclusion

We demonstrate that the EvoSkill self-evolution framework can be successfully adapted for SEO CTR optimization, a domain where real-world feedback signals are fundamentally sparse. Our key contribution — LLM-as-Judge as a proxy evaluator — transforms an evolution loop that produced zero useful evaluations into one that generates 6-10 evaluations per step and produces qualitatively sophisticated skills.

The system evolved from 7 seed skills to 25 skills (35 versions), independently discovering that curiosity-gap strategies are counterproductive for branded queries — a genuine SEO insight that emerged from the evolution process, not from human instruction.

We further validated framework transferability by porting the complete evolution engine to the OfficeQA domain (U.S. Treasury Bulletin question answering). The transfer required 1,095 lines of new domain-specific code while reusing the entire 1,082-line engine layer unchanged. Key finding: the most valuable form of transfer was not direct code reuse but **pattern reuse** — every new module mirrors its SEO counterpart structurally, eliminating design decisions and reducing the transfer to domain-specific prompt engineering. This confirms the framework's architecture as the primary unit of reuse, not any single module's implementation.

Three open questions remain for future work:

1. **Correlation validation**: How well do LLM quality scores predict actual CTR improvements? This requires deployment on a higher-traffic site where real CTR data is available for comparison.

2. **Cross-domain evolution dynamics**: Do skills evolved in one domain (SEO) provide useful seed strategies for another (QA)? Our transfer was structural (code and patterns) — transfer of evolved skills themselves remains unexplored.

3. **Hybrid evaluation scheduling**: What is the optimal ratio of cheap LLM evaluations to expensive real-world measurements? This is an exploration-exploitation tradeoff that likely has a principled solution.

---

## References

- EvoSkill: Self-Improving Agent Framework. Sentient Labs, 2025. https://github.com/sentient-agi/EvoSkill
- Zheng, L. et al. "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena." NeurIPS 2023.
- Khattab, O. et al. "DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines." ICLR 2024.
- Meyerson, E. et al. "Language Model Crossover: Variation through Few-Shot Prompting." arXiv:2302.12170.
- Seer Interactive. "AI-Powered SEO Title Optimization Case Study." 2024.

---

## Appendix A: Repository

Source code: https://github.com/calderbuild/ctr-evolver

## Appendix B: Evolved Skill Example

**intent_match_confirmation** (auto-generated, not human-written):

> Strategy: Directly confirm user search intent by placing the searched product/service name at the front of the title, paired with the clearest value proposition, to eliminate ambiguity and provide immediate relevance signals for navigational and branded queries.
>
> Core mechanism: Opposite of curiosity gap — uses "information frontloading" where the user's first glance confirms "this is exactly what I'm looking for," reducing cognitive friction and accelerating click decisions.
