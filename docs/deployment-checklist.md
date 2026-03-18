# Deployment Checklist: Sentient Arena Cohort 0 -- Daytona Sandbox

## Risk Assessment

### 1. Sandbox Compatibility

| Component | Will it work? | Notes |
|-----------|---------------|-------|
| GSC API (`google-auth` + `google-api-python-client`) | Yes, with caveats | Requires Tier 3+ for unrestricted egress, or `googleapis.com` must be on the network allow list |
| Parquet files (`pyarrow` / `pandas`) | Yes | Pure Python install, no external service dependency |
| Git branches / worktrees | Yes | Daytona provides a full filesystem and Git toolbox |
| BM25 index (`rank_bm25` or similar) | Yes | CPU-only, in-memory. 200MB corpus fits in 1GB RAM but is tight -- request 2GB+ |
| Embedding index | Conditional | If using a local model (e.g. `sentence-transformers`), needs 2GB+ RAM. If calling an external embedding API, needs egress to that API host |
| Streamlit | Yes | Use `forwardPorts: [8501]` in devcontainer.json or `daytona forward 8501` |
| LLM API calls (Claude, OpenRouter, Fireworks) | Yes, with caveats | Same egress restriction as GSC. Tier 3+ or explicit allow list required |

**Critical finding**: Default sandbox is 1 vCPU / 1GB RAM / 3GB disk. This is **insufficient** for BM25 + embedding index over 200MB of text. Request at minimum 2 vCPU / 4GB RAM / 5GB disk. Org maximum is 4 vCPU / 8GB RAM / 10GB disk.

### 2. Credential Management

GSC credentials (`config/gsc_credentials.json`) and API keys must never be committed to git.

**Threat model**:
- Daytona sandbox filesystem persists across stop/start. Credentials written to disk survive restarts.
- Sandbox archival moves filesystem to object storage -- credentials would be included.
- If the repo is public, `.gitignore` is the only barrier.

### 3. Data Persistence

Daytona sandbox filesystem **persists** across stop/start cycles. Memory state (running processes) is **lost** on stop.

Key implications:
- Parquet cache files survive restarts. No data loss on normal stop/start.
- Auto-stop after 15 minutes of inactivity. A long evolution run (>15 min without user interaction) could be killed.
- Auto-archive after 7 days of being stopped. Archived sandboxes take longer to restart but preserve all files.
- **Process state is lost**: if the evolution loop is running when the sandbox stops, the process dies. Only filesystem state survives.

### 4. Network Access

- Default (Tier 1-2): restricted egress. Only whitelisted package registries and GitHub are accessible. `googleapis.com`, `api.anthropic.com`, `openrouter.ai` are **not** whitelisted by default.
- Tier 3+: full internet access.
- If stuck on Tier 1-2: submit a whitelist request via Daytona's sandbox-network-whitelist repository or contact `support@daytona.io`.

### 5. Streamlit Port Exposure

Two options:
1. Add `"forwardPorts": [8501]` to `.devcontainer/devcontainer.json` -- port is forwarded automatically on workspace start.
2. Run `daytona forward 8501` inside the workspace -- port becomes publicly accessible.

Avoid port 3000 (triggers Streamlit dev mode detection bug).

### 6. Resource Limits

| Resource | Default | Org Maximum | Recommended for this project |
|----------|---------|-------------|------------------------------|
| vCPU | 1 | 4 | 2 |
| RAM | 1 GB | 8 GB | 4 GB |
| Disk | 3 GiB | 10 GB | 5 GB |

Disk budget estimate:
- GSC parquet cache (90 days): ~50-100 MB
- OfficeQA corpus + parsed docs: ~200-500 MB
- BM25 / embedding indexes: ~200-500 MB
- Git history (skill branches): ~100 MB
- Python packages: ~500 MB - 1 GB
- **Total**: ~1-2.5 GB. 3GB default is too tight. Request 5GB+.

### 7. Evolution Loop Recovery

The evolution loop is a long-running process. If it crashes or the sandbox stops:
- **Filesystem survives**: parquet caches, skill folders, git branches all persist.
- **Process state is lost**: loop counter, in-memory variables, partial LLM responses are gone.
- **Must design for resumability**: checkpoint after each iteration to disk.

---

## Pre-Deploy Checklist

### Environment Setup

- [ ] Create Daytona sandbox with elevated resources:
  ```
  CPU: 2 vCPU, Memory: 4 GB, Disk: 5 GB
  Auto-stop: 0 (disabled) OR set to 60+ minutes
  ```
- [ ] Verify Python 3.11+ is available: `python3 --version`
- [ ] Verify git is available: `git --version`
- [ ] Verify network egress to required APIs:
  ```bash
  curl -s -o /dev/null -w "%{http_code}" https://www.googleapis.com/discovery/v1/apis
  curl -s -o /dev/null -w "%{http_code}" https://api.anthropic.com/v1/messages
  curl -s -o /dev/null -w "%{http_code}" https://openrouter.ai/api/v1/models
  ```
  If any return non-200: check Daytona tier or submit whitelist request.
- [ ] Install Python dependencies:
  ```bash
  pip install google-auth google-api-python-client pandas pyarrow rank-bm25 streamlit pyyaml
  ```
- [ ] Verify disk space after install: `df -h /`
- [ ] Create `.devcontainer/devcontainer.json` with port forwarding:
  ```json
  {
    "forwardPorts": [8501],
    "postCreateCommand": "pip install -r requirements.txt"
  }
  ```

### Credential Setup

- [ ] Create `config/` directory
- [ ] Verify `.gitignore` contains:
  ```
  config/gsc_credentials.json
  config/*.json
  .env
  *.key
  ```
- [ ] Upload GSC service account JSON to `config/gsc_credentials.json` via Daytona filesystem API or direct file write
- [ ] Set environment variables (add to `~/.bashrc` for persistence across restarts):
  ```bash
  echo 'export GOOGLE_APPLICATION_CREDENTIALS="/workspace/config/gsc_credentials.json"' >> ~/.bashrc
  echo 'export ANTHROPIC_API_KEY="sk-ant-..."' >> ~/.bashrc
  echo 'export OPENROUTER_API_KEY="..."' >> ~/.bashrc
  source ~/.bashrc
  ```
- [ ] Verify GSC connection:
  ```bash
  python3 -c "
  from google.oauth2 import service_account
  from googleapiclient.discovery import build
  creds = service_account.Credentials.from_service_account_file(
      'config/gsc_credentials.json',
      scopes=['https://www.googleapis.com/auth/webmasters.readonly']
  )
  service = build('searchconsole', 'v1', credentials=creds)
  sites = service.sites().list().execute()
  print('Connected. Sites:', [s['siteUrl'] for s in sites.get('siteEntry', [])])
  "
  ```
- [ ] Verify LLM API connection:
  ```bash
  python3 -c "
  import os, urllib.request, json
  req = urllib.request.Request('https://api.anthropic.com/v1/messages',
      data=json.dumps({'model':'claude-sonnet-4-20250514','max_tokens':10,'messages':[{'role':'user','content':'ping'}]}).encode(),
      headers={'x-api-key': os.environ['ANTHROPIC_API_KEY'], 'content-type':'application/json', 'anthropic-version':'2023-06-01'})
  resp = urllib.request.urlopen(req)
  print('LLM API OK:', resp.status)
  "
  ```

### Data Backup Strategy

Since Daytona filesystem persists but process state does not:

- [ ] **Parquet cache**: append-only by design. Each day's GSC data is a separate file (`gsc_data/{date}.parquet`). No backup needed -- files are immutable once written.
- [ ] **Skill library**: version-controlled via git branches. Push to remote after each successful evolution iteration:
  ```bash
  git push origin --all  # push all skill branches
  ```
- [ ] **Evolution state checkpoint**: after each iteration, write state to disk:
  ```python
  # engine/checkpoint.py
  import json
  from pathlib import Path

  def save_checkpoint(iteration: int, frontier_state: dict, metrics: list):
      checkpoint = {
          "iteration": iteration,
          "frontier": frontier_state,
          "metrics": metrics,
          "timestamp": datetime.now().isoformat()
      }
      path = Path("checkpoints") / f"iter_{iteration:04d}.json"
      path.parent.mkdir(exist_ok=True)
      path.write_text(json.dumps(checkpoint, indent=2))

  def load_latest_checkpoint() -> dict | None:
      checkpoints = sorted(Path("checkpoints").glob("iter_*.json"))
      if not checkpoints:
          return None
      return json.loads(checkpoints[-1].read_text())
  ```
- [ ] **Periodic backup to remote**: add a post-iteration hook:
  ```bash
  git add checkpoints/ gsc_data/ skills/ results/
  git commit -m "checkpoint: iteration N"
  git push origin main
  ```
- [ ] **OfficeQA indexes**: BM25 and embedding indexes should be serialized to disk after construction. Rebuilding from scratch takes time but is not data loss.

### Pre-Run Validation

Run these checks before starting the evolution loop:

```bash
# 1. Disk space (need at least 1 GB free)
FREE_KB=$(df / | tail -1 | awk '{print $4}')
if [ "$FREE_KB" -lt 1000000 ]; then echo "STOP: Less than 1GB free disk"; fi

# 2. Memory check (need at least 2 GB available)
free -m | head -2

# 3. GSC API quota check (25,000/day limit)
# If you've already run queries today, check remaining

# 4. Git clean state
git status --porcelain | wc -l
# Expected: 0 (no uncommitted changes)

# 5. Checkpoint existence (for resumption)
ls -la checkpoints/ 2>/dev/null || echo "No prior checkpoints -- starting fresh"

# 6. Auto-stop setting
# Verify sandbox auto-stop is disabled or set to > expected run time
```

---

## Monitoring Plan

### What to Watch During Evolution Runs

| Signal | How to check | Alert condition |
|--------|-------------|-----------------|
| Process alive | `ps aux \| grep evolution` | Process not found |
| Disk usage | `df -h /` every iteration | > 80% used |
| Memory usage | `free -m` every iteration | < 200 MB available |
| Token budget | `cat checkpoints/iter_NNNN.json \| jq .metrics.total_tokens` | > 80% of 2M ceiling |
| LLM API errors | Evolution loop error logs | > 3 consecutive failures |
| GSC API quota | Count of daily API calls | > 20,000 (approaching 25K limit) |
| Iteration time | Timestamp delta between checkpoints | > 2x expected duration |
| Accuracy trend | Plot from checkpoint metrics | Decreasing for 3+ iterations |

### Log Files to Monitor

```
logs/evolution.log       -- main loop output
logs/gsc_api.log         -- GSC API call counts and errors
logs/llm_calls.log       -- LLM token usage per call
checkpoints/             -- iteration state files
```

### Recommended Monitoring Script

```bash
#!/bin/bash
# monitor.sh -- run in a separate terminal
while true; do
    echo "=== $(date) ==="
    echo "Disk: $(df -h / | tail -1 | awk '{print $5}')"
    echo "Mem:  $(free -m | grep Mem | awk '{print $4}') MB free"
    echo "Proc: $(ps aux | grep -c '[e]volution')"
    LATEST=$(ls -t checkpoints/iter_*.json 2>/dev/null | head -1)
    if [ -n "$LATEST" ]; then
        echo "Last checkpoint: $LATEST"
    fi
    echo "---"
    sleep 300
done
```

---

## Rollback Procedures

### Scenario 1: Evolution loop crashes mid-iteration

**Can roll back?** Yes.

**Steps:**
1. Check the last valid checkpoint: `ls -t checkpoints/iter_*.json | head -1`
2. Verify the checkpoint file is valid JSON: `python3 -m json.tool < checkpoints/iter_NNNN.json`
3. Restart the evolution loop with `--resume` flag (reads latest checkpoint)
4. Verify the frontier state matches the checkpoint

### Scenario 2: Sandbox stops unexpectedly (auto-stop or crash)

**Can roll back?** Yes -- filesystem persists.

**Steps:**
1. Start the sandbox again (Daytona auto-restarts on reconnect)
2. Re-source environment variables: `source ~/.bashrc`
3. Verify credentials still exist: `ls config/gsc_credentials.json`
4. Resume from checkpoint (same as Scenario 1)
5. Check if any parquet files were being written at crash time:
   ```bash
   find gsc_data/ -name "*.parquet" -size 0
   # Delete any zero-byte files (incomplete writes)
   ```

### Scenario 3: Bad skill evolution (accuracy drops)

**Can roll back?** Yes -- git branches.

**Steps:**
1. Identify the last good iteration from checkpoint metrics
2. Check out the corresponding skill branch:
   ```bash
   git log --oneline --all | head -20
   git checkout skills/iter_NNNN  # last good iteration
   ```
3. Reset the frontier to the last good state
4. Restart evolution from that point

### Scenario 4: GSC credential leak (committed to git)

**Steps:**
1. Immediately revoke the service account key in Google Cloud Console
2. Remove from git history:
   ```bash
   git filter-branch --force --index-filter \
     'git rm --cached --ignore-unmatch config/gsc_credentials.json' HEAD
   git push origin --force --all
   ```
3. Generate a new service account key
4. Upload to sandbox and verify `.gitignore`

### Scenario 5: Disk full

**Steps:**
1. Check largest directories: `du -sh */ | sort -rh | head -10`
2. Remove old checkpoints (keep last 5): `ls -t checkpoints/iter_*.json | tail -n +6 | xargs rm`
3. Clear pip cache: `pip cache purge`
4. If still full: archive old parquet data to git remote and delete local copies
5. Consider requesting larger disk from Daytona

---

## Streamlit Demo Deployment

- [ ] Verify Streamlit runs:
  ```bash
  streamlit run demo/app.py --server.port 8501 --server.address 0.0.0.0
  ```
- [ ] Forward port: `daytona forward 8501` or rely on `devcontainer.json` config
- [ ] Test from external browser using the forwarded URL
- [ ] For demo day: ensure sandbox auto-stop is disabled so the app stays up
- [ ] Fallback: record a video of the demo in case live sandbox access fails

---

## Timeline-Sensitive Notes

| Window | Action |
|--------|--------|
| Before first run | Complete all items in Pre-Deploy Checklist |
| Start of each evolution run | Run Pre-Run Validation checks |
| Every iteration | Checkpoint writes automatically |
| After each evolution session | `git push` all branches and checkpoints |
| Before demo day | Disable sandbox auto-stop; verify Streamlit port forwarding |
| After competition | Revoke GSC credentials; archive or delete sandbox |

---

## Sources

- [Daytona Sandbox Docs](https://www.daytona.io/docs/en/sandboxes/)
- [Daytona Limits](https://www.daytona.io/docs/limits/)
- [Daytona Network Limits](https://www.daytona.io/docs/en/network-limits/)
- [Daytona Sandbox Management](https://www.daytona.io/docs/en/sandbox-management/)
- [Daytona Port Forwarding Changelog](https://www.daytona.io/changelog/workspace-restart-and-enhanced-port-forwarding)
- [Streamlit Remote Deployment](https://docs.streamlit.io/knowledge-base/deploy/remote-start)
