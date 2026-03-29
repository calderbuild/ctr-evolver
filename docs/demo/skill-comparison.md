# Skill Comparison: Seed vs Evolved

7 seed skills evolved into 25 unique skills (35 total versions) across 10 evolution steps.

## Seed Skills (Human-Designed)

| Skill | Versions | Strategy | Pareto Metrics |
|-------|:--------:|----------|:--------------:|
| **curiosity_gap** | 1 | Create information gaps to compel clicks. Hint at valuable info without revealing it | lift=0.36, win=0.80, cov=10 |
| number_hook | 1 | Use specific numbers for credibility and scannability | -- (coverage=0) |
| loss_aversion | 1 | Emphasize what users might miss or lose. Stronger motivation than gain framing | -- (coverage=0) |
| position_adaptive | 1 | Dynamically adjust title strategy based on current search position | -- (coverage=0) |
| social_proof_authority | 3 | Combine social proof with authority signals (expert endorsements, media citations) | -- (coverage=0) |
| social_proof_signal | 3 | Embed quantified social proof ("10,000+ teams trust", "4.8 stars") | -- (coverage=0) |
| high_volume_query_targeting | 1 | Prioritize URLs with >= 500 monthly impressions for optimization experiments | -- (coverage=0) |

## Evolved Skills (System-Generated)

### Intent Confirmation (3 skills)

Skills that directly confirm the user's search intent -- the system's primary strategic pivot away from curiosity-gap.

| Skill | Versions | Strategy |
|-------|:--------:|----------|
| intent_match_confirmation | 1 | Place searched product/service name at front of title with clearest value proposition. "Information frontloading" vs curiosity gap |
| intent_match_reinforcement | 1 | Mirror user's known target intent by front-loading brand name, core value, and frictionless action directive |
| query_intent_matching | 1 | Classify query as navigational/informational/commercial-investigation, then apply intent-type-specific strategy |

### Brand Reinforcement (6 skills)

Deep specialization for branded and navigational queries -- the system's dominant evolution direction.

| Skill | Versions | Strategy |
|-------|:--------:|----------|
| brand_reinforcement | 3 | Mirror brand name prominently, reinforce core value proposition in familiar language |
| brand_trust_reinforcement | 1 | Emphasize trust signals and official identity ("Official Site", version info) |
| brand_value_reinforcement | 1 | Display brand name + core value proposition/use-case, reject emotional copy |
| branded_direct_answer_confirmation | 1 | Immediately confirm user has found their target. Brand name in most prominent position |
| branded_navigational_direct_value_confirmation | 2 | Confirm destination site identity + present single most compelling value proposition |
| branded_navigational_destination_reinforcement | 2 | Confirm destination + brand core value; no suspense, no information gaps |

### Value Proposition (4 skills)

Direct value communication -- clear functional descriptions over persuasion tactics.

| Skill | Versions | Strategy |
|-------|:--------:|----------|
| direct_value | 1 | State core function/benefit clearly with functional language matching user's confirmed intent |
| direct_value_proposition | 3 | Lead with clear benefit/function statement. Reject suspense, match known intent precisely |
| value_proposition | 1 | Front-load specific benefit or unique selling point to answer "why should I click?" |
| benefit_first_framing | 1 | Present most concrete, perceivable benefit/result at the very front of title and description |

### Social Proof Variants (2 skills)

Evolved versions combining social proof with other strategies.

| Skill | Versions | Strategy |
|-------|:--------:|----------|
| branded_social_proof_trust_signal | 1 | Inject quantifiable social proof into branded/navigational titles (user counts, ratings, milestones) |
| social_proof | 1 | Embed social proof signals (user numbers, star ratings, expert recommendations) into titles |

### Informational Query (2 skills)

Strategies for non-branded, information-seeking queries.

| Skill | Versions | Strategy |
|-------|:--------:|----------|
| high_volume_informational_targeting | 1 | Rewrite title/desc to directly answer searcher's implied question for high-volume informational queries |
| high_volume_informational_query_targeting | 1 | For broad non-brand informational queries, present clear value proposition + comparison hooks |

### Other (1 skill)

| Skill | Versions | Strategy |
|-------|:--------:|----------|
| unknown | 1 | Brand-navigation strategy for direct brand name searches; confirm destination + value |

## Key Observations

1. **Only curiosity_gap was tested** (coverage=10) due to single-opportunity bottleneck. It scored well (win_rate=0.80) under LLM-as-Judge, but the evolution system correctly identified it as counterproductive for branded queries.

2. **Evolution converged on "intent confirmation"** -- 15 of 18 evolved skills are variations of "confirm what the user already knows" rather than "create curiosity about what they don't know."

3. **Skill sophistication increased ~2.5x** -- seed skills average ~1KB; evolved skills average ~2.5KB with explicit anti-patterns, query-type taxonomies, and scenario-aware guidance.

4. **Multi-version skills** (brand_reinforcement: 3v, direct_value_proposition: 3v, social_proof_authority: 3v, social_proof_signal: 3v) show iterative refinement within a strategy direction.

## Summary

| Metric | Value |
|--------|------:|
| Seed skills | 7 |
| Evolved skills | 18 |
| Total unique skills | 25 |
| Total skill versions | 35 |
| Skills with evaluation data | 1 (curiosity_gap) |
| Dominant evolved strategy | Intent/Brand confirmation (15/18) |
