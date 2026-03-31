"""OfficeQA data client -- load questions and corpus files."""

import csv
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SAMPLES_DIR = PROJECT_ROOT / "officeqa" / ".arena" / "samples"


def load_sample_tasks() -> list[dict]:
    """Load all sample tasks from Arena CLI samples directory.

    Returns list of dicts with keys: uid, question, expected_answer, difficulty,
    tolerance, source_files, source_docs, task_dir
    """
    tasks = []
    if not SAMPLES_DIR.exists():
        return tasks

    for task_dir in sorted(SAMPLES_DIR.iterdir()):
        if not task_dir.is_dir() or task_dir.name == ".":
            continue

        config_path = task_dir / "tests" / "config.json"
        instruction_path = task_dir / "instruction.md"

        if not config_path.exists():
            continue

        config = json.loads(config_path.read_text())
        question = instruction_path.read_text().strip() if instruction_path.exists() else config.get("question", "")

        # Extract just the question (before "## Available Resources")
        if "## Available Resources" in question:
            question = question[:question.index("## Available Resources")].strip()

        tasks.append({
            "uid": config.get("uid", task_dir.name),
            "question": question,
            "expected_answer": str(config.get("expected_answer", "")),
            "difficulty": config.get("difficulty", "unknown"),
            "tolerance": float(config.get("tolerance", 0.01)),
            "source_files": config.get("source_files", []),
            "source_docs": config.get("source_docs", []),
            "task_dir": str(task_dir),
        })

    return tasks


def load_questions_by_difficulty(difficulty: str = None) -> list[dict]:
    """Load sample tasks filtered by difficulty (easy/hard)."""
    tasks = load_sample_tasks()
    if difficulty:
        tasks = [t for t in tasks if t["difficulty"] == difficulty]
    return tasks


def get_task_stats() -> dict:
    """Get summary stats of available sample tasks."""
    tasks = load_sample_tasks()
    difficulties = {}
    for t in tasks:
        d = t["difficulty"]
        difficulties[d] = difficulties.get(d, 0) + 1
    return {
        "total": len(tasks),
        "by_difficulty": difficulties,
    }
