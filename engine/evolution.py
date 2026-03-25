"""SEO Evolution Engine — event-driven evolution loop."""

import json
import os
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from seo_agent import evaluator, executor, gsc_client, intervention, opportunity
from . import frontier, proposer, skill_generator
from .memory import EvolutionMemory

PROJECT_ROOT = Path(__file__).parent.parent
FEEDBACK_PATH = PROJECT_ROOT / "data" / "feedback_history.txt"
CHECKPOINT_PATH = PROJECT_ROOT / "data" / "checkpoint.json"


class SEOEvolutionEngine:
    """Event-driven evolution engine for SEO CTR optimization."""

    def __init__(self, site_url: str):
        self.site_url = site_url
        self.frontier = frontier.ParetoFrontier(k=15)
        self.feedback_history = self._load_feedback_history()
        self.memory = EvolutionMemory()

    def _load_feedback_history(self) -> list[str]:
        """Load past feedback/analysis from disk."""
        if not FEEDBACK_PATH.exists():
            return []
        text = FEEDBACK_PATH.read_text().strip()
        return text.split("\n") if text else []

    def _save_feedback(self, text: str):
        """Append feedback to history."""
        FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(FEEDBACK_PATH, "a") as f:
            f.write(text + "\n")
        self.feedback_history.append(text)

    def _save_checkpoint(self, step_num: int, result: dict):
        """Save checkpoint after each step (atomic write)."""
        checkpoint = {
            "step_num": step_num,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "site_url": self.site_url,
            "last_result": {
                "evaluated_count": result.get("evaluated_count", 0),
                "eliminated_skills": result.get("eliminated_skills", []),
                "new_skill_name": result.get("new_skill_name"),
            },
            "active_skills": [s["skill_name"] for s in self.frontier.get_active()],
        }
        CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp_fd, tmp_path = tempfile.mkstemp(dir=CHECKPOINT_PATH.parent, suffix=".tmp")
        os.close(tmp_fd)
        try:
            with open(tmp_path, "w") as f:
                json.dump(checkpoint, f, indent=2)
            os.rename(tmp_path, CHECKPOINT_PATH)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    def _load_checkpoint(self) -> dict | None:
        """Load last checkpoint."""
        if not CHECKPOINT_PATH.exists():
            return None
        return json.loads(CHECKPOINT_PATH.read_text())

    def run(self, max_steps: int = 15, min_impressions: int = 5, mode: str = "burst"):
        """Run evolution loop.

        Args:
            max_steps: Maximum evolution steps
            min_impressions: Minimum impressions for opportunity filtering
            mode: "burst" = run steps back-to-back (default)
                  "continuous" = smart loop, sync when stale, wait between steps
        """
        if mode == "continuous":
            return self._run_continuous(max_steps, min_impressions)
        return self._run_burst(max_steps, min_impressions)

    def _run_burst(self, max_steps: int, min_impressions: int):
        """Run steps back-to-back (original behavior)."""
        checkpoint = self._load_checkpoint()
        start_step = (checkpoint["step_num"] + 1) if checkpoint else 1

        print(f"Starting evolution from step {start_step} (max {max_steps})")

        for step_num in range(start_step, max_steps + 1):
            print(f"\n{'=' * 60}")
            print(f"Step {step_num}/{max_steps}")
            print(f"{'=' * 60}")

            # 1. Sync latest data
            print("Syncing GSC data...")
            gsc_client.sync(self.site_url)
            df = gsc_client.load_data()

            if df.empty:
                print("No data available. Stopping.")
                break

            # 2. Identify opportunities
            opps = opportunity.identify_opportunities(
                df, min_impressions=min_impressions, top_n=10, position_range=(1, 50)
            )
            print(f"Found {len(opps)} opportunities")

            if not opps:
                print("No opportunities found. Stopping.")
                break

            # 3. Generate interventions for top opportunities
            active_skills = executor.list_active_skills()
            if not active_skills:
                active_skills = ["curiosity_gap"]

            generated = 0
            for opp in opps[:5]:  # Top 5 opportunities
                # Round-robin skills
                skill = active_skills[generated % len(active_skills)]

                try:
                    result = executor.generate_title_desc(
                        page_url=opp["page"],
                        current_title="",
                        current_desc="",
                        query=opp["query"],
                        position=opp["position"],
                        skill_name=skill,
                        model="anthropic/claude-haiku-4.5",
                    )

                    intervention.record_intervention(
                        page_url=opp["page"],
                        query=opp["query"],
                        old_title="",
                        new_title=result["title"],
                        old_desc="",
                        new_desc=result["description"],
                        skill_name=skill,
                        position_at_intervention=opp["position"],
                    )
                    generated += 1
                    print(f"  Generated: {skill} -> {opp['query'][:40]}")
                except Exception as e:
                    print(f"  Error generating for {opp['query'][:40]}: {e}")

            print(f"Generated {generated} interventions")

            # 4. Evaluate + evolve
            step_result = self.step(df)
            print(f"Evaluated: {step_result['evaluated_count']} interventions")
            if step_result.get("new_skill_name"):
                print(f"New skill: {step_result['new_skill_name']}")

            # 5. Checkpoint
            self._save_checkpoint(step_num, step_result)
            print(f"Checkpoint saved (step {step_num})")

        print(f"\nEvolution complete. Ran steps {start_step}-{step_num}.")

    def _run_continuous(self, max_steps: int, min_impressions: int):
        """Smart continuous loop — sync when stale, wait between steps."""
        SYNC_INTERVAL = 6 * 3600  # 6 hours between syncs
        STEP_INTERVAL = 3600  # 1 hour between steps minimum

        checkpoint = self._load_checkpoint()
        start_step = (checkpoint["step_num"] + 1) if checkpoint else 1
        last_sync = 0

        print(f"Continuous mode: starting from step {start_step}, max {max_steps}")
        print(
            f"Sync interval: {SYNC_INTERVAL // 3600}h, Step interval: {STEP_INTERVAL // 60}min"
        )

        step_num = start_step
        while step_num <= max_steps:
            now = time.time()

            # Sync if stale
            if now - last_sync > SYNC_INTERVAL:
                print(
                    f"\n[{datetime.utcnow().strftime('%H:%M:%S')}] Syncing GSC data..."
                )
                try:
                    gsc_client.sync(self.site_url)
                    last_sync = now
                except Exception as e:
                    print(f"  Sync error: {e}")

            df = gsc_client.load_data()
            if df.empty:
                print("No data. Waiting...")
                time.sleep(STEP_INTERVAL)
                continue

            # Check for evaluable interventions
            pending = intervention.load_interventions(status="pending")
            evaluable = 0
            for p in pending:
                t = datetime.fromisoformat(p["timestamp"].replace("Z", ""))
                if datetime.utcnow() - t > timedelta(days=7):
                    evaluable += 1

            # Identify opportunities
            opps = opportunity.identify_opportunities(
                df, min_impressions=min_impressions, top_n=10, position_range=(1, 50)
            )

            has_work = evaluable > 0 or len(opps) > 0

            if not has_work:
                print(
                    f"[{datetime.utcnow().strftime('%H:%M:%S')}] No work. "
                    f"Pending: {len(pending)}, Evaluable: {evaluable}, Opps: {len(opps)}. "
                    f"Waiting {STEP_INTERVAL // 60}min..."
                )
                time.sleep(STEP_INTERVAL)
                continue

            print(f"\n{'=' * 60}")
            print(f"Step {step_num}/{max_steps} (continuous)")
            print(f"Evaluable: {evaluable}, Opportunities: {len(opps)}")
            print(f"{'=' * 60}")

            # Generate new interventions if we have opportunities
            if opps:
                active_skills = executor.list_active_skills()
                if not active_skills:
                    active_skills = ["curiosity_gap"]

                generated = 0
                for opp in opps[:5]:
                    skill = active_skills[generated % len(active_skills)]
                    try:
                        result = executor.generate_title_desc(
                            page_url=opp["page"],
                            current_title="",
                            current_desc="",
                            query=opp["query"],
                            position=opp["position"],
                            skill_name=skill,
                            model="anthropic/claude-haiku-4.5",
                        )
                        intervention.record_intervention(
                            page_url=opp["page"],
                            query=opp["query"],
                            old_title="",
                            new_title=result["title"],
                            old_desc="",
                            new_desc=result["description"],
                            skill_name=skill,
                            position_at_intervention=opp["position"],
                        )
                        generated += 1
                        print(f"  Generated: {skill} -> {opp['query'][:40]}")
                    except Exception as e:
                        print(f"  Error: {e}")
                print(f"Generated {generated} interventions")

            # Evaluate + evolve
            step_result = self.step(df)
            print(f"Evaluated: {step_result['evaluated_count']} interventions")
            if step_result.get("new_skill_name"):
                print(f"New skill: {step_result['new_skill_name']}")

            self._save_checkpoint(step_num, step_result)
            step_num += 1

            # Wait before next iteration
            print(f"Waiting {STEP_INTERVAL // 60}min before next check...")
            time.sleep(STEP_INTERVAL)

        print(f"\nContinuous evolution complete after {step_num - start_step} steps.")

    def step(self, new_measurements: pd.DataFrame) -> dict:
        """Run one evolution step: evaluate -> eliminate -> propose -> generate.

        Args:
            new_measurements: Latest GSC data (DataFrame)

        Returns:
            dict with step results
        """
        # 1. Evaluate pending interventions
        evaluations = self._evaluate_interventions(new_measurements)

        if not evaluations:
            return {
                "evaluated_count": 0,
                "eliminated_skills": [],
                "new_skill_name": None,
                "message": "No interventions to evaluate",
            }

        # 2. Update frontier with new metrics
        skill_metrics = self._aggregate_skill_metrics(evaluations)
        eliminated = []
        for skill_name, metrics in skill_metrics.items():
            elim = self.frontier.update(skill_name, metrics)
            eliminated.extend(elim)

        # 3. Analyze failures (with memory + history context)
        memory_text = self.memory.to_prompt_text()
        history_summary = intervention.get_evaluation_summary()
        failure_analysis = proposer.analyze_failures(
            evaluations, memory_text=memory_text, history_summary=history_summary
        )
        self._save_feedback(f"[{datetime.utcnow().isoformat()}] {failure_analysis}")

        # 3.5. Update evolution memory from evaluations
        memory_updates = proposer.extract_memory_updates(evaluations)
        for p in memory_updates.get("promising", []):
            self.memory.add_promising(p.get("direction", ""), p.get("evidence", ""))
        for f in memory_updates.get("failed", []):
            self.memory.add_failed(f.get("direction", ""), f.get("evidence", ""))
        for pat in memory_updates.get("patterns", []):
            self.memory.add_pattern(
                pat.get("pattern", ""), pat.get("source_skills", [])
            )

        # 4. Propose new strategy (with memory)
        active_skills = [s["skill_name"] for s in self.frontier.get_active()]
        strategy = proposer.propose_strategy(
            failure_analysis,
            active_skills,
            self.feedback_history,
            memory_text=memory_text,
        )

        # 5. Generate new skill
        skill_name, content = skill_generator.generate_skill(strategy, active_skills)
        skill_generator.save_skill(skill_name, content)

        # 6. Add to frontier with initial metrics
        self.frontier.update(
            skill_name, {"avg_ctr_lift": 0.0, "win_rate": 0.0, "coverage": 0}
        )

        return {
            "evaluated_count": len(evaluations),
            "eliminated_skills": eliminated,
            "new_skill_name": skill_name,
            "failure_analysis": failure_analysis,
        }

    def _evaluate_interventions(
        self, new_data: pd.DataFrame, min_age_days: int = 7
    ) -> list[dict]:
        """Evaluate pending interventions that are old enough to have after-data."""
        pending = intervention.load_interventions(status="pending")
        evaluations = []

        for interv in pending:
            interv_time = datetime.fromisoformat(interv["timestamp"].replace("Z", ""))

            # Skip interventions that are too recent to evaluate
            if datetime.utcnow() - interv_time < timedelta(days=min_age_days):
                continue

            before_data = new_data[
                pd.to_datetime(new_data["date"]) < pd.to_datetime(interv_time.date())
            ]
            after_cutoff = interv_time + timedelta(days=7)
            after_data = new_data[
                (pd.to_datetime(new_data["date"]) >= pd.to_datetime(interv_time.date()))
                & (
                    pd.to_datetime(new_data["date"])
                    < pd.to_datetime(after_cutoff.date())
                )
            ]

            eval_result = evaluator.evaluate_intervention(
                interv, before_data, after_data
            )

            intervention.update_intervention(
                interv["intervention_id"],
                {"status": "evaluated", "evaluation": eval_result},
            )

            evaluations.append(
                {
                    **eval_result,
                    "skill_name": interv["skill_name"],
                    "query": interv["query"],
                    "page_url": interv["page_url"],
                }
            )

        return evaluations

    def _aggregate_skill_metrics(self, evaluations: list[dict]) -> dict:
        """Aggregate metrics by skill."""
        skill_evals = {}
        for e in evaluations:
            skill = e["skill_name"]
            if skill not in skill_evals:
                skill_evals[skill] = []
            skill_evals[skill].append(e)

        metrics = {}
        for skill, evals in skill_evals.items():
            successes = [e for e in evals if e.get("status") == "success"]
            total = len(evals)

            avg_lift = (
                sum(e.get("ctr_lift", 0) for e in evals) / total if total > 0 else 0
            )
            win_rate = len(successes) / total if total > 0 else 0

            metrics[skill] = {
                "avg_ctr_lift": avg_lift,
                "win_rate": win_rate,
                "coverage": total,
            }

        return metrics


def backtest(site_url: str, days: int = 30) -> dict:
    """Run backtest on historical data."""
    df = gsc_client.load_data()

    if df.empty:
        return {"error": "No data available"}

    df["date"] = pd.to_datetime(df["date"])
    cutoff = df["date"].max() - timedelta(days=days)
    train_data = df[df["date"] < cutoff]
    test_data = df[df["date"] >= cutoff]

    if train_data.empty or test_data.empty:
        return {"error": f"Not enough data to split at {days} days"}

    # Identify opportunities from training data
    opps = opportunity.identify_opportunities(
        train_data, min_impressions=3, top_n=20, position_range=(1, 50)
    )

    if not opps:
        return {"error": "No opportunities found in training data"}

    # For each skill, simulate interventions
    active_skills = executor.list_active_skills()
    if not active_skills:
        active_skills = [
            "curiosity_gap",
            "number_hook",
            "loss_aversion",
            "position_adaptive",
        ]

    results = {skill: [] for skill in active_skills}

    for opp in opps:
        for skill in active_skills:
            page_train = train_data[
                (train_data["page"] == opp["page"])
                & (train_data["query"] == opp["query"])
            ]
            page_test = test_data[
                (test_data["page"] == opp["page"])
                & (test_data["query"] == opp["query"])
            ]

            if not page_train.empty and not page_test.empty:
                train_ctr = page_train["clicks"].sum() / page_train["impressions"].sum()
                test_ctr = page_test["clicks"].sum() / page_test["impressions"].sum()
                lift = test_ctr - train_ctr

                results[skill].append(
                    {"page": opp["page"], "query": opp["query"], "lift": lift}
                )

    # Aggregate results
    summary = {}
    for skill, evals in results.items():
        if not evals:
            continue
        avg_lift = sum(e["lift"] for e in evals) / len(evals)
        wins = sum(1 for e in evals if e["lift"] > 0)
        win_rate = wins / len(evals)

        summary[skill] = {
            "avg_ctr_lift": avg_lift,
            "win_rate": win_rate,
            "coverage": len(evals),
        }

    return summary
