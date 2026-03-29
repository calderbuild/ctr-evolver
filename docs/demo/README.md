# Self-Evolving SEO Agent: Demo Materials

## Overview

A self-evolving AI agent that autonomously discovers and optimizes SEO title/description strategies through an evolutionary loop. Built on the EvoSkill framework, adapted for real-world SEO with LLM-as-Judge proxy evaluation.

**Repository**: [github.com/calderbuild/ctr-evolver](https://github.com/calderbuild/ctr-evolver)

---

## Research Proposal

**[Self-Evolving SEO Agents: LLM-as-Judge for Sparse-Signal Skill Evolution](../research-proposal.md)**

Full paper covering system design, the sparse signal challenge, LLM-as-Judge solution, experiments, and analysis across all three Arena research directions.

---

## Demo Materials

| Document | Description |
|----------|-------------|
| [Architecture Diagram](architecture.md) | Mermaid flowcharts: system architecture, dual evaluation path, evolution loop |
| [Skill Comparison](skill-comparison.md) | 25 skills (7 seed + 18 evolved) with strategies and Pareto metrics |
| [Title Examples](title-examples.md) | Before/after title comparison for 3 representative skills |
| [Evolution Timeline](evolution-timeline.md) | 10-step evolution history with key events and metrics |
| [Cost Analysis](cost-analysis.md) | Per-step cost breakdown, commercial tool comparison, scaling projections |

---

## Key Numbers

| Metric | Value |
|--------|------:|
| Evolution steps | 10 |
| Seed skills | 7 |
| Evolved skills | 18 |
| Total skill versions | 35 |
| LLM evaluations | ~94 |
| Top skill win rate | 0.80 |
| Total API cost | $47.50 |
| Cost per step | $4.75 |

---

## The Core Insight

Real-world self-evolution faces a fundamental challenge: **feedback signals are often too sparse for statistical evaluation**. Our target site receives ~2.4 impressions/day -- a z-test would need 167 days per evaluation, but the competition runs 21 days.

**Solution**: LLM-as-Judge as a proxy evaluator. This transformed 0 evaluations/step into 6-10 evaluations/step, enabling the evolution loop to generate meaningful skill differentiation and produce genuinely sophisticated strategies.

The system independently discovered that curiosity-gap strategies are counterproductive for branded queries -- a real SEO insight that emerged from evolution, not human instruction.
