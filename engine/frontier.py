"""Pareto frontier management for skill selection."""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
FRONTIER_PATH = PROJECT_ROOT / "skills" / "frontier" / "active_skills.json"
METRICS_PATH = PROJECT_ROOT / "skills" / "frontier" / "metrics.json"


class ParetoFrontier:
    """Manage Pareto frontier of skills (K=15 max)."""

    def __init__(self, k: int = 15):
        self.k = k
        self.metrics = self._load_metrics()

    def _load_metrics(self) -> dict:
        """Load skill metrics from disk."""
        if not METRICS_PATH.exists():
            return {}
        return json.loads(METRICS_PATH.read_text())

    def _save_metrics(self):
        """Save skill metrics to disk."""
        METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
        METRICS_PATH.write_text(json.dumps(self.metrics, indent=2))

    def update(self, skill_name: str, metrics: dict) -> list[str]:
        """Update frontier with new skill metrics.

        Args:
            skill_name: Name of skill
            metrics: dict with keys: avg_ctr_lift, win_rate, coverage

        Returns:
            List of eliminated skill names
        """
        # Update metrics
        self.metrics[skill_name] = metrics

        # Compute Pareto frontier
        skills = list(self.metrics.keys())
        dominated = set()

        for s1 in skills:
            for s2 in skills:
                if s1 == s2:
                    continue
                if self._dominates(self.metrics[s2], self.metrics[s1]):
                    dominated.add(s1)
                    break

        # Keep non-dominated skills
        frontier = [s for s in skills if s not in dominated]

        # If frontier > K, keep top K by composite score
        eliminated = []
        if len(frontier) > self.k:
            scored = [(s, self._composite_score(self.metrics[s])) for s in frontier]
            scored.sort(key=lambda x: x[1], reverse=True)
            frontier = [s for s, _ in scored[:self.k]]
            eliminated = [s for s, _ in scored[self.k:]]

        # Save active skills
        self._save_active(frontier)
        self._save_metrics()

        return eliminated

    def _dominates(self, a: dict, b: dict) -> bool:
        """Check if metrics a dominates b (Pareto dominance).

        a dominates b if:
        - a is >= b on all dimensions
        - a is > b on at least one dimension
        """
        dimensions = ["avg_ctr_lift", "win_rate", "coverage"]
        all_gte = all(a.get(d, 0) >= b.get(d, 0) for d in dimensions)
        any_gt = any(a.get(d, 0) > b.get(d, 0) for d in dimensions)
        return all_gte and any_gt

    def _composite_score(self, metrics: dict) -> float:
        """Compute composite score for tie-breaking.

        Weighted sum: 50% avg_ctr_lift + 30% win_rate + 20% coverage (normalized)
        """
        lift = metrics.get("avg_ctr_lift", 0)
        win_rate = metrics.get("win_rate", 0)
        coverage = metrics.get("coverage", 0)

        # Normalize coverage (assume max 100 pages)
        coverage_norm = min(coverage / 100, 1.0)

        return 0.5 * lift + 0.3 * win_rate + 0.2 * coverage_norm

    def _save_active(self, skills: list[str]):
        """Save active skill names to frontier/active_skills.json."""
        FRONTIER_PATH.parent.mkdir(parents=True, exist_ok=True)
        FRONTIER_PATH.write_text(json.dumps({"active": skills}, indent=2))

    def get_active(self) -> list[dict]:
        """Get current active skills with their metrics."""
        if not FRONTIER_PATH.exists():
            return []

        active_names = json.loads(FRONTIER_PATH.read_text()).get("active", [])
        return [
            {"skill_name": name, "metrics": self.metrics.get(name, {})}
            for name in active_names
        ]

    def remove(self, skill_name: str):
        """Remove a skill from frontier."""
        if skill_name in self.metrics:
            del self.metrics[skill_name]
            self._save_metrics()

        # Update active list
        if FRONTIER_PATH.exists():
            active = json.loads(FRONTIER_PATH.read_text()).get("active", [])
            if skill_name in active:
                active.remove(skill_name)
                self._save_active(active)
