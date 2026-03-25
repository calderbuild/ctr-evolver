"""Persistent evolution memory — tracks what works and what doesn't."""
import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
MEMORY_PATH = PROJECT_ROOT / "data" / "evolution_memory.json"

MAX_ENTRIES = 10  # per list


class EvolutionMemory:
    """Structured memory for evolution decisions.

    Three lists:
    - promising_directions: what skill patterns work well
    - failed_directions: what to avoid
    - effective_patterns: reusable execution patterns from successful skills
    """

    def __init__(self):
        self.data = self._load()

    def _load(self) -> dict:
        if not MEMORY_PATH.exists():
            return {
                "promising_directions": [],
                "failed_directions": [],
                "effective_patterns": [],
            }
        return json.loads(MEMORY_PATH.read_text())

    def save(self):
        MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        MEMORY_PATH.write_text(json.dumps(self.data, indent=2, ensure_ascii=False))

    def add_promising(self, direction: str, evidence: str):
        self._append("promising_directions", {
            "direction": direction,
            "evidence": evidence,
            "updated_at": datetime.utcnow().isoformat() + "Z",
        })

    def add_failed(self, direction: str, evidence: str):
        self._append("failed_directions", {
            "direction": direction,
            "evidence": evidence,
            "updated_at": datetime.utcnow().isoformat() + "Z",
        })

    def add_pattern(self, pattern: str, source_skills: list[str]):
        self._append("effective_patterns", {
            "pattern": pattern,
            "source_skills": source_skills,
            "updated_at": datetime.utcnow().isoformat() + "Z",
        })

    def _append(self, key: str, entry: dict):
        self.data[key].append(entry)
        if len(self.data[key]) > MAX_ENTRIES:
            self.data[key] = self.data[key][-MAX_ENTRIES:]
        self.save()

    def to_prompt_text(self) -> str:
        """Format memory for inclusion in LLM prompts."""
        lines = []

        if self.data["promising_directions"]:
            lines.append("## Promising Directions (what works)")
            for d in self.data["promising_directions"]:
                lines.append(f"- {d['direction']} (evidence: {d['evidence']})")

        if self.data["failed_directions"]:
            lines.append("\n## Failed Directions (avoid these)")
            for d in self.data["failed_directions"]:
                lines.append(f"- {d['direction']} (evidence: {d['evidence']})")

        if self.data["effective_patterns"]:
            lines.append("\n## Effective Patterns (reuse these)")
            for p in self.data["effective_patterns"]:
                skills = ", ".join(p["source_skills"])
                lines.append(f"- {p['pattern']} (from: {skills})")

        return "\n".join(lines) if lines else "No evolution memory yet."
