---
title: Commit, Push to GitHub, Deploy to Daytona
type: feat
date: 2026-03-25
---

# Commit, Push to GitHub, Deploy to Daytona

## Overview

All code is written, validated end-to-end, and bug-fixed. Zero commits beyond the initial scaffold. This plan covers organizing commits, pushing to GitHub (via SSH proxy), and deploying to Daytona for continuous 24/7 evolution.

## Acceptance Criteria

- [ ] 2-3 clean commits covering all code changes
- [ ] GitHub private repo with code pushed (no secrets)
- [ ] Daytona workspace created from repo
- [ ] GSC credentials injected into sandbox
- [ ] `python cli.py evolve run --max-steps 5 --mode continuous` running in Daytona
- [ ] Checkpoint verified after first sandbox step

---

## Phase 1: Organize and Commit

### 1.1 Verify .gitignore coverage

Confirm these are excluded (already configured):
- `.env` (API keys)
- `config/gsc_token.json`, `config/gsc_credentials.json` (OAuth secrets)
- `data/` (parquet cache, interventions, checkpoint, memory)
- `__pycache__/`

**Check**: `git status` should NOT show `.env`, `config/gsc_*.json`, or `data/` files.

### 1.2 Stage and commit in logical groups

**Commit 1: Core agent and evolution engine**
```bash
git add seo_agent/ engine/ skills/
git commit -m "feat: SEO CTR evolution engine with 7 skills and Pareto frontier"
```
Files: `seo_agent/*.py` (5 modules), `engine/*.py` (5 modules), `skills/` (7 skill directories + frontier config)

**Commit 2: CLI, scripts, and deployment config**
```bash
git add cli.py scripts/ .devcontainer/ requirements.txt
git commit -m "feat: CLI interface, run script, and Daytona devcontainer"
```

**Commit 3: Plans and documentation**
```bash
git add docs/ CLAUDE.md environment.yml
git commit -m "docs: project plans, CLAUDE.md, and environment config"
```

### 1.3 Verify no secrets leaked

```bash
git log --oneline --stat  # review file list
git show HEAD -- .env 2>/dev/null  # should show nothing
git show HEAD -- config/ 2>/dev/null  # should show nothing
```

---

## Phase 2: Push to GitHub

### 2.1 Create private repo

```bash
gh repo create cohort-0-seo-agent --private --source=. --remote=origin
```

Or if repo already exists:
```bash
git remote add origin git@github.com:<user>/cohort-0-seo-agent.git
```

### 2.2 Push via SSH proxy

Per mistakes-log: GitHub HTTPS push hangs due to osxkeychain. Use SSH remote with `~/.ssh/config` ProxyCommand.

```bash
git push -u origin main
```

Verify `~/.ssh/config` has:
```
Host github.com
    ProxyCommand nc -X connect -x 127.0.0.1:7897 %h %p
```

### 2.3 Verify on GitHub

```bash
gh repo view --web  # opens browser to verify
```

---

## Phase 3: Daytona Workspace Setup

### 3.1 Create workspace

```bash
daytona create <github-repo-url>
```

This uses `.devcontainer/devcontainer.json` which requests:
- 2 vCPU / 4GB RAM / 5GB disk
- Python 3.12 image
- `pip install -r requirements.txt` on creation
- Port 8501 forwarded (Streamlit, future use)

### 3.2 Inject credentials

GSC OAuth requires a browser -- cannot run in headless sandbox. Copy the locally-generated token:

```bash
# Option A: daytona cp (if supported)
daytona cp config/gsc_token.json <workspace>:config/gsc_token.json
daytona cp config/gsc_credentials.json <workspace>:config/gsc_credentials.json

# Option B: SSH + cat
daytona ssh <workspace>
mkdir -p config
cat > config/gsc_token.json << 'EOF'
<paste token content>
EOF
cat > config/gsc_credentials.json << 'EOF'
<paste credentials content>
EOF
```

Set environment variables:
```bash
# In sandbox
cat > .env << 'EOF'
OPENROUTER_API_KEY=<key>
EOF
```

### 3.3 Verify sandbox environment

```bash
# In Daytona sandbox
python cli.py gsc sync --days 30  # quick sync test
python cli.py gsc status
python cli.py opportunities list --top 5 --min-impressions 1
```

### 3.4 Network verification

Confirm API access:
```bash
curl -s https://openrouter.ai/api/v1/models | head -c 200  # OpenRouter
curl -s https://www.googleapis.com/discovery/v1/apis | head -c 200  # Google
```

If blocked, request Tier 3 network or submit whitelist for `openrouter.ai` and `googleapis.com`.

---

## Phase 4: Start Continuous Evolution

### 4.1 Initial burst (validate in sandbox)

```bash
python cli.py evolve run --max-steps 2 --mode burst
```

Verify:
- `data/checkpoint.json` created
- New skills generated
- No API errors

### 4.2 Switch to continuous mode

```bash
nohup bash scripts/run_evolution.sh > evolution.log 2>&1 &
```

Or use `tmux`/`screen` for persistence:
```bash
tmux new -s evolution
bash scripts/run_evolution.sh
# Ctrl+B, D to detach
```

The continuous mode:
- Syncs GSC data every 6 hours
- Waits 1 hour between steps
- Evaluates interventions only after 7 days (age check)
- Checkpoints after every step
- Auto-resumes from checkpoint on restart

### 4.3 Monitor

```bash
# Check progress
cat data/checkpoint.json | python -m json.tool
ls skills/*/v*/SKILL.md | wc -l  # total skills
cat data/evolution_memory.json | python -m json.tool
tail -50 evolution.log
```

### 4.4 Resume after sandbox stop

Daytona auto-stops after 15 minutes of inactivity. To resume:
```bash
daytona start <workspace>
daytona ssh <workspace>
tmux attach -t evolution || bash scripts/run_evolution.sh
```

Checkpoint ensures no work is lost -- evolution resumes from step N+1.

---

## Risk Analysis

| Risk | Mitigation |
|------|-----------|
| SSH proxy not working for push | Verify `~/.ssh/config` first; fall back to `gh repo create --source=.` which uses gh's own auth |
| Daytona rejects 2vCPU request | Default 1vCPU works for evolution (not compute-heavy); only Streamlit needs more |
| Network blocked in sandbox | Test curl to APIs before starting evolution; request whitelist |
| Sandbox stops mid-step | Checkpoint saves after each step; 2-5 min/step well under 15-min timeout |
| GSC token expires in sandbox | Token has refresh_token; auto-refreshes. If fails, re-copy from local |

## Dependencies

- `gh` CLI authenticated (for repo creation)
- `~/.ssh/config` with GitHub proxy (for push)
- `daytona` CLI installed and authenticated
- Local `config/gsc_token.json` valid and unexpired
- `.env` with `OPENROUTER_API_KEY` (>$75 remaining budget)

## Cost

- Burst validation (2 steps): ~$12
- Continuous mode: ~$6/step, budget for ~10 more steps
- Total remaining: ~$72 after this plan

## Timeline

| Step | Time |
|------|------|
| Phase 1: Commit | 10 min |
| Phase 2: Push | 5 min |
| Phase 3: Daytona setup | 30 min |
| Phase 4: Start evolution | 15 min |
| **Total** | **~1 hour** |
