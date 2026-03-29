# Evolution Timeline

## 10-Step Evolution History

The system ran two distinct phases: an initial phase without LLM-as-Judge (pre-v2) where no evaluations were possible, followed by a productive phase after introducing the proxy evaluator.

### Phase 1: Pre-LLM-Judge (Steps 1-19, v1 codebase)

All 19 steps returned `insufficient_data` for every intervention. The evolution loop was structurally complete but functionally frozen:

- 0 meaningful evaluations produced
- Proposer received empty failure lists ("No failures to analyze")
- All skills stuck at metrics (0, 0, 0) -- Pareto frontier could not differentiate
- ~$90 in API credits consumed with zero learning signal

**Diagnosis**: meetspot receives ~2.4 impressions/day. A z-test needs ~400 impressions per group = 167 days per evaluation. The competition runs 21 days.

### Phase 2: Post-LLM-Judge (Steps 1-10, v2 codebase)

| Step | Evaluated | New Skill Generated | Active Skills | Key Event |
|------|-----------|--------------------:|:-------------:|-----------|
| 1 | 6 | intent_match_confirmation | 8 | First LLM evaluations. curiosity_gap scores well |
| 2 | 8 | brand_value_reinforcement | 9 | System detects "meetspot" is branded query |
| 3 | 10 | direct_value_proposition | 10 | Proposer identifies curiosity gap as counterproductive for branded |
| 4 | 10 | intent_match_reinforcement | 11 | Strategy pivot: from "create curiosity" to "confirm intent" |
| 5 | 10 | high_volume_informational_targeting | 12 | Explores non-branded query strategies |
| 6 | 10 | branded_navigational_direct_value_confirmation | 13 | Deep specialization for navigational intent |
| 7 | 10 | branded_direct_answer_confirmation | 14 | Further brand reinforcement variants |
| 8 | 10 | branded_social_proof_trust_signal | 15 | Combines social proof + brand trust |
| 9 | 10 | unknown | 16 | Exploration of novel strategy space |
| 10 | 10 | branded_navigational_destination_reinforcement | 17 | Final step: 9 active skills in frontier |

### Key Metrics

| Metric | Pre-LLM-Judge (19 steps) | Post-LLM-Judge (10 steps) |
|--------|:------------------------:|:-------------------------:|
| Total evaluations | 0 | ~94 |
| Skills with non-zero metrics | 0 | 1 (curiosity_gap) |
| New skills generated | 0 useful | 18 |
| Skill versions created | 7 (seed only) | 35 (7 seed + 28 evolved) |
| Top skill win_rate | N/A | 0.80 (curiosity_gap) |
| Evolution memory entries | 0 | 9 failed + patterns |
| API cost | ~$90 (wasted) | ~$47.50 (productive) |

### Evolution Insight

```
Step 1-3: "curiosity_gap works well" (LLM judge scores high)
Step 4-6: "but wait — for branded queries, curiosity gap is wrong"
Step 7-10: "generate alternatives: intent confirmation, brand reinforcement"
```

The system independently discovered that curiosity-gap strategies are counterproductive for branded queries like "meetspot" -- a genuine SEO insight that emerged from the evolution process, not from human instruction.
