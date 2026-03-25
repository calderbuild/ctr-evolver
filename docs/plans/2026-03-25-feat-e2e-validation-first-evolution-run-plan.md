---
title: End-to-End Validation and First Evolution Run
type: feat
date: 2026-03-25
---

# End-to-End Validation and First Evolution Run

## Overview

All 1,942 lines of the SEO CTR Self-Evolving Agent are written but **never executed**. This plan covers switching the target site to `meetspot-irq2.onrender.com`, validating every pipeline stage, and completing the first real evolution steps. After this plan, the agent should be generating real skills from real GSC data.

## Problem Statement

- Code has never been run end-to-end on real data
- Hardcoded site URL points to abandoned `jasonrobert.me`
- 54 stale parquet files in `data/gsc/` from wrong site
- Evaluator threshold (100 impressions) may be too high for the target site
- Only 11 days remain until April 3 deadline
- $100 OpenRouter budget (~16 evolution steps at $6/step)

## Proposed Solution

Five-phase sequential validation: config -> data -> pipeline -> generation -> evolution. Each phase gates the next. Fail fast at each stage rather than discovering issues deep in the evolution loop.

## Acceptance Criteria

- [x] `python cli.py gsc sync --days 90` succeeds with meetspot data
- [x] `python cli.py opportunities list --top 20` returns >= 5 opportunities
- [x] `python cli.py generate <page_url> --skill curiosity_gap` produces valid title/description
- [x] `python cli.py evolve step` completes without error, generates new skill
- [x] `data/checkpoint.json` created with valid state
- [x] `skills/frontier/metrics.json` updated
- [x] At least one new skill directory exists (`skills/{name}/v1/SKILL.md`)

---

## Phase 1: Site Configuration Switch

### 1.1 Determine GSC URL format

GSC supports two property types:
- **Domain property**: `sc-domain:example.com` (covers all subdomains + protocols)
- **URL-prefix property**: `https://meetspot-irq2.onrender.com/` (exact prefix match)

Since `meetspot-irq2.onrender.com` is a subdomain of `onrender.com`, it **must** be registered as a URL-prefix property (you can't own `sc-domain:onrender.com`).

**Action**: Verify the site is registered in GSC. Run:
```bash
python -c "from seo_agent.gsc_client import get_service; svc = get_service(); print([s['siteUrl'] for s in svc.sites().list().execute().get('siteEntry', [])])"
```

This lists all sites the authenticated account has access to. Use the exact string GSC returns.

**Files**: None yet (discovery step)

### 1.2 Update hardcoded defaults

Replace `sc-domain:jasonrobert.me` with the correct GSC URL in:

| File | Line | Change |
|------|------|--------|
| `cli.py` | 23 | `--site-url` default in `sync` |
| `cli.py` | 33 | `--site-url` default in `status` |
| `cli.py` | 50 | `--site-url` default in `list_opportunities` |
| `cli.py` | 110 | `--site-url` default in `step` |
| `cli.py` | 126 | `--site-url` default in `run` |
| `cli.py` | 141 | `--site-url` default in `backtest` |
| `scripts/run_evolution.sh` | 10, 24 | `SITE_URL` default |

**Constraint**: Use the exact string from GSC API (step 1.1). Do not guess the format.

### 1.3 Clean stale data

```bash
rm -rf data/gsc/*.parquet
rm -f data/interventions.jsonl
rm -f data/checkpoint.json
rm -f data/evolution_memory.json
rm -f skills/frontier/metrics.json
```

Keep seed skills (`skills/*/v1/SKILL.md`) and `skills/frontier/active_skills.json` intact.

### 1.4 GSC OAuth (if not done)

If `config/gsc_token.json` doesn't exist or is for a different account:
```bash
python -c "from seo_agent.gsc_client import get_service; get_service()"
```

This triggers OAuth desktop flow (opens browser). Must be done locally -- Daytona sandbox can't do headless OAuth.

**Constraint**: Requires `config/gsc_credentials.json` (OAuth client ID from Google Cloud Console).

---

## Phase 2: Data Sync and Validation

### 2.1 Sync GSC data

```bash
python cli.py gsc sync --days 90
```

**Expected**: Creates parquet files in `data/gsc/`. Should take 1-3 minutes for 90 days.

**Failure modes**:
- `HttpError 403`: Site not verified in GSC -> verify ownership first
- `HttpError 403: User does not have sufficient permission`: Wrong GSC account
- Empty dataframes: Site has no search traffic -> need a different site
- Network timeout: Add `--days 30` to reduce scope

### 2.2 Validate data quality

```bash
python cli.py gsc status
```

Check:
- **rows** > 0 (otherwise site has no data)
- **files** matches expected day count (minus GSC's 3-5 day lag)

Then validate dtypes:

```python
python -c "
from seo_agent.gsc_client import load_data
df = load_data()
print(df.dtypes)
print(f'CTR range: {df[\"ctr\"].min():.6f} to {df[\"ctr\"].max():.6f}')
print(f'Rows: {len(df):,}')
print(f'Unique pages: {df[\"page\"].nunique()}')
print(f'Unique queries: {df[\"query\"].nunique()}')
"
```

**Critical check**: If `ctr` dtype is `int64` (all zeros), fix in `gsc_client.py:query_day()` by adding explicit `.astype(float)` cast on the ctr column.

### 2.3 Assess site traffic volume

If total rows < 500 or unique pages < 10:
- Lower `min_impressions` in CLI default from 5 to 1
- Lower evaluator threshold from 100 to 20 (`seo_agent/evaluator.py:109`)
- Consider switching `--days 90` to `--days 180` for more data

Record the actual traffic level in CLAUDE.md for future reference.

---

## Phase 3: Pipeline Validation

### 3.1 Opportunity identification

```bash
python cli.py opportunities list --top 20 --min-impressions 5
```

**Expected**: At least 5 opportunities with non-zero opportunity_score.

**If < 5 results**: Lower `--min-impressions` to 1, widen `--position-max` to 100.

**Verify output sanity**:
- Position values are 1-50 range
- CTR values are 0-1 range (not percentages)
- Baseline CTR > actual CTR for shown opportunities (that's why they're opportunities)

### 3.2 Single generation test

Pick the top opportunity URL from 3.1:

```bash
python cli.py generate "<page_url>" --skill curiosity_gap
```

**Expected**: Returns title + description. Validates:
- OpenRouter API key works
- Skill template loading (`skills/curiosity_gap/v1/SKILL.md`)
- LLM JSON parsing (`executor._parse_json_response()`)

**Failure modes**:
- `AuthenticationError`: Bad API key -> check `.env`
- `RateLimitError`: Budget exhausted -> check OpenRouter dashboard
- JSON parse error: LLM returned bad format -> check `executor.py` fallback parsing

### 3.3 Test with each seed skill

Run generation with all 4 seed skills to verify they all load:

```bash
for skill in curiosity_gap number_hook loss_aversion position_adaptive; do
    echo "=== $skill ==="
    python cli.py generate "<page_url>" --skill $skill
    echo ""
done
```

---

## Phase 4: First Evolution Step

### 4.1 Dry run: evolve step

```bash
python cli.py evolve step
```

On first run with no pending interventions, `step()` should:
1. **Evaluate pending**: 0 interventions (skip)
2. **Update frontier**: No new data (skip)
3. **Analyze failures**: No failures yet -> generic analysis
4. **Propose strategy**: Should produce a new direction
5. **Generate skill**: Should create `skills/{name}/v1/SKILL.md`

**Verify**:
- `data/checkpoint.json` exists and is valid JSON
- New skill directory created under `skills/`
- `data/evolution_memory.json` created (may be empty initially)
- No Python tracebacks in output

### 4.2 Review generated skill

Read the new SKILL.md. Check:
- Has proper structure (strategy, applicability, techniques, prompt template)
- Prompt template includes `{page_url}`, `{query}`, `{position}` placeholders
- Not a copy of an existing seed skill

### 4.3 Record an intervention manually (optional)

To test the evaluation pipeline without waiting 7 days, manually insert a test intervention:

```python
python -c "
from seo_agent.intervention import record_intervention
record_intervention(
    page_url='<top_opportunity_url>',
    query='<top_query>',
    skill_name='curiosity_gap',
    old_title='Old Title',
    old_desc='Old description',
    new_title='New Optimized Title',
    new_desc='New optimized description',
    position=5.0,
    impressions=100
)
print('Intervention recorded')
"
```

Then run `evolve step` again to verify it picks up the pending intervention (though it won't evaluate until 7 days pass or you mock the timestamp).

---

## Phase 5: Burst Mode Validation

### 5.1 Run 3 steps in burst mode

```bash
python cli.py evolve run --max-steps 3 --mode burst
```

**Cost estimate**: ~$18 (3 steps x $6/step with Sonnet+Haiku)

**Expected**:
- 3 sequential evolution steps complete
- 3 new skills generated (or skill versions incremented)
- Checkpoint updated after each step
- Frontier metrics populated

### 5.2 Verify evolution state

```python
python -c "
import json
from pathlib import Path

# Checkpoint
cp = json.loads(Path('data/checkpoint.json').read_text())
print(f'Steps completed: {cp[\"step_count\"]}')
print(f'Last step: {cp[\"last_step_time\"]}')

# Frontier
metrics = json.loads(Path('skills/frontier/metrics.json').read_text())
print(f'Active skills: {len(metrics)}')
for name, m in metrics.items():
    print(f'  {name}: score={m.get(\"composite_score\", \"N/A\")}')

# Memory
mem = json.loads(Path('data/evolution_memory.json').read_text())
print(f'Memory entries: promising={len(mem.get(\"promising\", []))}, failed={len(mem.get(\"failed\", []))}, patterns={len(mem.get(\"patterns\", []))}')
"
```

### 5.3 Validate active_skills.json updated

```bash
cat skills/frontier/active_skills.json
```

Should include both seed skills and newly generated ones.

---

## Risk Analysis

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| GSC has no data for meetspot site | Medium | Blocks everything | Verify via API in Phase 1.1 before any code changes |
| CTR dtype is int64 | Low | Bad opportunity scores | Fix with `.astype(float)` in gsc_client.py |
| OpenRouter budget runs out mid-burst | Low | Evolution stops | Use free Llama model for first 2 steps, then switch to Sonnet |
| First evolution step errors on empty state | Medium | Debug cycle | Expected -- step() should handle empty interventions gracefully |
| Site traffic too low for 100-impression threshold | High | Evaluations never complete | Lower threshold to 20 in Phase 2.3 |

## Dependencies

- GSC OAuth credentials (`config/gsc_credentials.json`) must exist
- `.env` must have valid `OPENROUTER_API_KEY`
- meetspot site must be verified in Google Search Console
- conda env `cohort0` must be activated with all deps installed

## Cost Budget

| Phase | Model | Estimated Cost |
|-------|-------|---------------|
| Phase 3 (4 generations) | Sonnet | ~$0.50 |
| Phase 4 (1 step) | Sonnet + Haiku | ~$6 |
| Phase 5 (3 steps) | Sonnet + Haiku | ~$18 |
| **Total** | | **~$24.50** |

Leaves ~$75 for subsequent continuous evolution (~12 more steps).

## Post-Validation Next Steps

1. **Git commit**: Stage all changes, 2-3 organized commits
2. **Daytona deployment**: Follow `docs/plans/2026-03-19-feat-daytona-deployment-evolution-loop-plan.md`
3. **Continuous mode**: Switch to `--mode continuous` for 6h sync + 1h step intervals
4. **Leaderboard prep**: When submission CLI is ready, prepare submission format
5. **Research proposal**: Collect evolution metrics for self-improvement evidence
