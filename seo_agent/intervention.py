"""Append-only intervention log (JSONL format)."""

import json
import uuid
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
INTERVENTIONS_PATH = DATA_DIR / "interventions.jsonl"


def record_intervention(
    page_url: str,
    query: str,
    old_title: str,
    new_title: str,
    old_desc: str,
    new_desc: str,
    skill_name: str,
    position_at_intervention: float,
) -> str:
    """Record a new intervention. Returns intervention_id."""
    intervention_id = str(uuid.uuid4())
    record = {
        "intervention_id": intervention_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "page_url": page_url,
        "query": query,
        "old_title": old_title,
        "new_title": new_title,
        "old_desc": old_desc,
        "new_desc": new_desc,
        "skill_name": skill_name,
        "position_at_intervention": position_at_intervention,
        "status": "pending",  # pending, evaluated, failed
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(INTERVENTIONS_PATH, "a") as f:
        f.write(json.dumps(record) + "\n")

    return intervention_id


def load_interventions(status: str | None = None) -> list[dict]:
    """Load all interventions, deduplicated by intervention_id (last write wins).

    The JSONL is append-only: updates append a new record with the same ID.
    We keep only the last record per intervention_id, then filter by status.
    """
    if not INTERVENTIONS_PATH.exists():
        return []

    # Last-write-wins: later lines override earlier ones for the same ID
    by_id: dict[str, dict] = {}
    with open(INTERVENTIONS_PATH) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            by_id[record["intervention_id"]] = record

    if status is None:
        return list(by_id.values())
    return [r for r in by_id.values() if r.get("status") == status]


def update_intervention(intervention_id: str, updates: dict):
    """Update an intervention by appending a new record with the same ID.

    The latest record for a given intervention_id is the current state.
    """
    # Load existing intervention
    interventions = load_interventions()
    existing = None
    for record in interventions:
        if record["intervention_id"] == intervention_id:
            existing = record
            break

    if existing is None:
        raise ValueError(f"Intervention not found: {intervention_id}")

    # Merge updates
    updated = {**existing, **updates}
    updated["updated_at"] = datetime.utcnow().isoformat() + "Z"

    # Append new record
    with open(INTERVENTIONS_PATH, "a") as f:
        f.write(json.dumps(updated) + "\n")


def get_latest_state(intervention_id: str) -> dict | None:
    """Get the latest state of an intervention."""
    interventions = load_interventions()
    latest = None
    for record in interventions:
        if record["intervention_id"] == intervention_id:
            latest = record

    return latest


def get_evaluation_summary(max_rows: int = 20) -> str:
    """Build a cross-step evaluation summary table for Proposer context.

    Aggregates evaluated interventions by skill, returns markdown table.
    """
    evaluated = load_interventions(status="evaluated")
    if not evaluated:
        return ""

    # Aggregate by skill
    skill_stats: dict[str, dict] = {}
    for record in evaluated:
        skill = record.get("skill_name", "unknown")
        if skill not in skill_stats:
            skill_stats[skill] = {"total": 0, "wins": 0, "lifts": [], "queries": []}

        stats = skill_stats[skill]
        stats["total"] += 1

        eval_data = record.get("evaluation", {})
        lift = eval_data.get("ctr_lift", 0)
        stats["lifts"].append(lift)
        if eval_data.get("status") == "success":
            stats["wins"] += 1
        stats["queries"].append(record.get("query", "?")[:30])

    # Build markdown table
    lines = ["| Skill | Total | Wins | Win Rate | Avg Lift | Sample Queries |"]
    lines.append("|-------|-------|------|----------|----------|----------------|")

    for skill, stats in sorted(skill_stats.items(), key=lambda x: -x[1]["total"]):
        total = stats["total"]
        wins = stats["wins"]
        win_rate = f"{wins / total:.0%}" if total > 0 else "N/A"
        avg_lift = sum(stats["lifts"]) / len(stats["lifts"]) if stats["lifts"] else 0
        queries = ", ".join(stats["queries"][:3])
        lines.append(
            f"| {skill} | {total} | {wins} | {win_rate} | {avg_lift:+.4f} | {queries} |"
        )

        if len(lines) > max_rows + 2:
            break

    return "\n".join(lines)
