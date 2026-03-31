"""QA intervention log -- append-only JSONL storage.

Same pattern as seo_agent/intervention.py but with QA-specific fields.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
INTERVENTIONS_PATH = PROJECT_ROOT / "office_qa" / "data" / "interventions.jsonl"


def record_intervention(
    uid: str,
    question: str,
    generated_answer: str,
    expected_answer: str,
    skill_name: str,
    difficulty: str = "unknown",
    reasoning: str = "",
    confidence: str = "unknown",
) -> str:
    """Record a new QA intervention. Returns intervention_id."""
    intervention_id = str(uuid.uuid4())[:8]
    record = {
        "intervention_id": intervention_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "uid": uid,
        "question": question[:200],  # truncate for storage
        "generated_answer": generated_answer,
        "expected_answer": expected_answer,
        "skill_name": skill_name,
        "difficulty": difficulty,
        "reasoning": reasoning[:500],
        "confidence": confidence,
        "status": "pending",
    }
    INTERVENTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(INTERVENTIONS_PATH, "a") as f:
        f.write(json.dumps(record) + "\n")
    return intervention_id


def update_intervention(intervention_id: str, updates: dict):
    """Update an intervention by appending a new record with the same ID."""
    records = _load_all()
    latest = None
    for r in records:
        if r["intervention_id"] == intervention_id:
            latest = r

    if latest is None:
        return

    latest.update(updates)
    latest["updated_at"] = datetime.utcnow().isoformat() + "Z"
    with open(INTERVENTIONS_PATH, "a") as f:
        f.write(json.dumps(latest) + "\n")


def load_interventions(status: str = None) -> list[dict]:
    """Load interventions, optionally filtered by status.

    Returns latest version of each intervention (last-write-wins).
    """
    records = _load_all()

    # Deduplicate: keep last record per intervention_id
    by_id = {}
    for r in records:
        by_id[r["intervention_id"]] = r

    interventions = list(by_id.values())

    if status:
        interventions = [i for i in interventions if i.get("status") == status]

    return interventions


def get_evaluation_summary() -> str:
    """Get markdown summary of evaluations by skill."""
    evaluated = load_interventions(status="evaluated")
    if not evaluated:
        return "No evaluations yet."

    # Aggregate by skill
    skill_stats = {}
    for e in evaluated:
        skill = e.get("skill_name", "unknown")
        if skill not in skill_stats:
            skill_stats[skill] = {"total": 0, "correct": 0, "scores": []}
        skill_stats[skill]["total"] += 1
        eval_data = e.get("evaluation", {})
        if eval_data.get("is_correct"):
            skill_stats[skill]["correct"] += 1
        if "llm_score" in e:
            skill_stats[skill]["scores"].append(e["llm_score"])

    lines = ["| Skill | Total | Correct | Accuracy | Avg LLM Score |"]
    lines.append("|-------|-------|---------|----------|---------------|")
    for skill, stats in sorted(skill_stats.items()):
        acc = stats["correct"] / stats["total"] if stats["total"] else 0
        avg_llm = sum(stats["scores"]) / len(stats["scores"]) if stats["scores"] else 0
        lines.append(
            f"| {skill} | {stats['total']} | {stats['correct']} | {acc:.1%} | {avg_llm:.1f} |"
        )

    return "\n".join(lines)


def _load_all() -> list[dict]:
    """Load all records from JSONL file."""
    if not INTERVENTIONS_PATH.exists():
        return []
    records = []
    for line in INTERVENTIONS_PATH.read_text().strip().split("\n"):
        if line.strip():
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records
