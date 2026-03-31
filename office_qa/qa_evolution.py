"""QA Evolution Engine -- self-evolving agent for OfficeQA.

Reuses engine/ layer (frontier, memory) read-only.
Domain-specific prompts are overridden here, not in engine/proposer.py.
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from engine.frontier import ParetoFrontier
from engine.memory import EvolutionMemory
from office_qa import data_client, intervention, qa_evaluator, llm_evaluator
from office_qa.qa_executor import generate_answer, load_skill, list_active_skills

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
SKILLS_DIR = PROJECT_ROOT / "office_qa" / "skills"
CHECKPOINT_PATH = PROJECT_ROOT / "office_qa" / "data" / "checkpoint.json"
FEEDBACK_PATH = PROJECT_ROOT / "office_qa" / "data" / "feedback_history.txt"

DEFAULT_MODEL = "anthropic/claude-sonnet-4.6"
HAIKU_MODEL = "anthropic/claude-haiku-4.5"


def _get_client() -> OpenAI:
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        timeout=60.0,
        max_retries=2,
    )


class QAEvolutionEngine:
    """Evolution engine for OfficeQA answer strategies."""

    def __init__(self):
        self.frontier = ParetoFrontier(k=15)
        self.memory = EvolutionMemory()
        self.feedback_history = self._load_feedback_history()

    def run(self, max_steps: int = 5):
        """Run evolution loop over sample tasks."""
        checkpoint = self._load_checkpoint()
        start_step = (checkpoint["step_num"] + 1) if checkpoint else 1
        end_step = start_step + max_steps - 1

        tasks = data_client.load_sample_tasks()
        if not tasks:
            print("No sample tasks available. Run 'arena pull' first.")
            return

        print(f"Starting QA evolution from step {start_step} (running {max_steps} steps)")
        print(f"Available tasks: {len(tasks)}")

        for step_num in range(start_step, end_step + 1):
            print(f"\n{'=' * 60}")
            print(f"Step {step_num}/{max_steps}")
            print(f"{'=' * 60}")

            # 1. Generate answers for sample tasks using active skills
            active_skills = list_active_skills()
            if not active_skills:
                active_skills = ["direct_extraction"]

            generated = 0
            for i, task in enumerate(tasks[:5]):  # Top 5 tasks per step
                skill = active_skills[i % len(active_skills)]
                try:
                    result = generate_answer(
                        question=task["question"],
                        source_files=task["source_files"],
                        skill_name=skill,
                        model=HAIKU_MODEL,  # Use Haiku for cost efficiency
                    )

                    intervention.record_intervention(
                        uid=task["uid"],
                        question=task["question"],
                        generated_answer=result.get("answer", ""),
                        expected_answer=task["expected_answer"],
                        skill_name=skill,
                        difficulty=task["difficulty"],
                        reasoning=result.get("reasoning", ""),
                        confidence=result.get("confidence", "unknown"),
                    )
                    generated += 1
                    print(f"  Generated: {skill} -> {task['uid']} ({task['difficulty']})")
                except Exception as e:
                    print(f"  Error generating for {task['uid']}: {e}")

            print(f"Generated {generated} answers")

            # 2. Evaluate + evolve
            step_result = self.step()
            print(f"Evaluated: {step_result['evaluated_count']} interventions")
            if step_result.get("new_skill_name"):
                print(f"New skill: {step_result['new_skill_name']}")

            # 3. Checkpoint
            self._save_checkpoint(step_num, step_result)
            print(f"Checkpoint saved (step {step_num})")

        print(f"\nEvolution complete. Ran {max_steps} steps.")

    def step(self) -> dict:
        """Run one evolution step: evaluate -> eliminate -> propose -> generate."""
        # 1. Evaluate pending interventions
        gt_evaluations = self._evaluate_with_ground_truth()
        llm_evaluations = self._evaluate_with_llm()

        # Prefer ground truth when available
        evaluations = gt_evaluations if gt_evaluations else llm_evaluations

        if not evaluations:
            return {
                "evaluated_count": 0,
                "eliminated_skills": [],
                "new_skill_name": None,
            }

        # 2. Update frontier
        skill_metrics = self._aggregate_skill_metrics(evaluations)
        eliminated = []
        for skill_name, metrics in skill_metrics.items():
            elim = self.frontier.update(skill_name, metrics)
            eliminated.extend(elim)

        # 3. Analyze failures (QA-specific prompts)
        memory_text = self.memory.to_prompt_text()
        history_summary = intervention.get_evaluation_summary()
        failure_analysis = self._analyze_failures(
            evaluations, memory_text, history_summary
        )
        self._save_feedback(f"[{datetime.utcnow().isoformat()}] {failure_analysis}")

        # 3.5. Extract memory updates
        memory_updates = self._extract_memory_updates(evaluations)
        for p in memory_updates.get("promising", []):
            self.memory.add_promising(p.get("direction", ""), p.get("evidence", ""))
        for f in memory_updates.get("failed", []):
            self.memory.add_failed(f.get("direction", ""), f.get("evidence", ""))
        for pat in memory_updates.get("patterns", []):
            self.memory.add_pattern(
                pat.get("pattern", ""), pat.get("source_skills", [])
            )

        # 4. Propose new strategy
        active_skills = [s["skill_name"] for s in self.frontier.get_active()]
        strategy = self._propose_strategy(
            failure_analysis, active_skills, memory_text
        )

        # 5. Generate new skill
        skill_name, content = self._generate_skill(strategy, active_skills)
        self._save_skill(skill_name, content)

        # 6. Add to frontier
        self.frontier.update(
            skill_name, {"avg_ctr_lift": 0.0, "win_rate": 0.0, "coverage": 0}
        )

        return {
            "evaluated_count": len(evaluations),
            "eliminated_skills": eliminated,
            "new_skill_name": skill_name,
        }

    def _evaluate_with_ground_truth(self) -> list[dict]:
        """Evaluate pending interventions against ground truth answers."""
        pending = intervention.load_interventions(status="pending")
        evaluations = []

        for interv in pending:
            expected = interv.get("expected_answer", "")
            generated = interv.get("generated_answer", "")

            if not expected or not generated:
                continue

            eval_result = qa_evaluator.evaluate_answer(expected, generated)

            intervention.update_intervention(
                interv["intervention_id"],
                {
                    "status": "evaluated",
                    "evaluation": eval_result,
                },
            )

            status = "success" if eval_result["is_correct"] else "failure"
            evaluations.append(
                {
                    "skill_name": interv["skill_name"],
                    "uid": interv.get("uid"),
                    "question": interv.get("question", "")[:100],
                    "status": status,
                    "score": eval_result["score"],
                    "rationale": eval_result["rationale"],
                }
            )

        return evaluations

    def _evaluate_with_llm(self) -> list[dict]:
        """Evaluate using LLM-as-Judge for immediate signal."""
        pending = intervention.load_interventions(status="pending")
        if not pending:
            return []

        evaluable = [
            p for p in pending
            if p.get("generated_answer") and p["generated_answer"] != "(parse error)"
        ]
        if not evaluable:
            return []

        return llm_evaluator.evaluate_batch(evaluable)

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

            lifts = []
            for e in evals:
                if "score" in e:
                    lifts.append(e["score"])  # 0 or 1 for ground truth
                elif "llm_score" in e:
                    lifts.append((e["llm_score"] - 5) / 5)

            avg_lift = sum(lifts) / len(lifts) if lifts else 0
            win_rate = len(successes) / total if total > 0 else 0

            metrics[skill] = {
                "avg_ctr_lift": avg_lift,
                "win_rate": win_rate,
                "coverage": total,
            }

        return metrics

    # --- QA-specific LLM prompts (override engine/proposer.py prompts) ---

    def _analyze_failures(
        self, evaluations: list[dict], memory_text: str, history_summary: str
    ) -> str:
        """Analyze failed QA answers to find patterns."""
        failures = [
            e for e in evaluations
            if e.get("status") in ("failure", "inconclusive")
        ]
        if not failures:
            return "No failures to analyze."

        lines = []
        for f in failures:
            lines.append(
                f"- Skill: {f.get('skill_name')}, UID: {f.get('uid')}, "
                f"Score: {f.get('score', 0)}, Rationale: {f.get('rationale', '')[:100]}"
            )

        context_parts = []
        if memory_text:
            context_parts.append(f"## Evolution Memory\n{memory_text}")
        if history_summary:
            context_parts.append(f"## Cross-Step History\n{history_summary}")

        client = _get_client()
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": f"""Analyze these failed QA answers on U.S. Treasury Bulletin questions and identify common patterns:

{chr(10).join(lines)}

{chr(10).join(context_parts)}

What patterns do you see? What question types or reasoning strategies tend to fail? Be specific and concise.
Respond in 3-5 bullet points.""",
                }
            ],
            temperature=0.3,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()

    def _propose_strategy(
        self, failure_analysis: str, current_skills: list[str], memory_text: str
    ) -> dict:
        """Propose a new QA reasoning strategy."""
        memory_section = f"\n## Evolution Memory\n{memory_text}\n" if memory_text else ""

        client = _get_client()
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": f"""You are a financial document analysis researcher. Based on the failure analysis below, propose ONE new reasoning strategy for answering U.S. Treasury Bulletin questions.

## Failure Analysis
{failure_analysis}

## Current Active Skills
{", ".join(current_skills)}
{memory_section}
## Requirements
- Strategy must be DIFFERENT from existing skills
- Must address the failure patterns identified
- Must be specific to financial document QA (table extraction, calculation, temporal reasoning)
- AVOID directions listed in "Failed Directions"
- BUILD ON "Promising Directions" and "Effective Patterns"

Respond in JSON:
{{"name": "snake_case_name", "description": "One sentence description", "rationale": "Why this addresses the failures"}}""",
                }
            ],
            temperature=0.8,
            max_tokens=300,
        )

        text = response.choices[0].message.content.strip()
        return _parse_json(text)

    def _generate_skill(
        self, strategy: dict, existing_skills: list[str]
    ) -> tuple[str, str]:
        """Generate a new QA SKILL.md from strategy."""
        skill_name = strategy["name"]

        client = _get_client()
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": f"""Create a SKILL.md file for a financial document QA reasoning strategy.

## Strategy
- Name: {skill_name}
- Description: {strategy['description']}
- Rationale: {strategy['rationale']}

## Existing Skills (do NOT duplicate)
{', '.join(existing_skills)}

## Required Format
# {{skill_name}}
## Strategy Description
## Applicable Question Types
## Core Techniques
## Examples (Question -> Reasoning -> Answer)
## Prompt Template

Focus on Treasury Bulletin data: table extraction, multi-step calculations,
temporal reasoning across document versions. Include 2-3 worked examples.
Output ONLY the markdown content, no code fences.""",
                }
            ],
            temperature=0.7,
            max_tokens=1500,
        )

        content = response.choices[0].message.content.strip()
        return skill_name, content

    def _save_skill(self, skill_name: str, content: str) -> Path:
        """Save SKILL.md with auto-versioning."""
        skill_dir = SKILLS_DIR / skill_name
        if skill_dir.exists():
            existing = sorted(
                [d for d in skill_dir.iterdir() if d.is_dir() and d.name.startswith("v")],
                key=lambda d: int(d.name[1:]),
            )
            next_version = int(existing[-1].name[1:]) + 1 if existing else 1
        else:
            next_version = 1

        version_dir = skill_dir / f"v{next_version}"
        version_dir.mkdir(parents=True, exist_ok=True)
        path = version_dir / "SKILL.md"
        path.write_text(content)
        return path

    def _extract_memory_updates(self, evaluations: list[dict]) -> dict:
        """Extract memory updates from QA evaluations."""
        if not evaluations:
            return {"promising": [], "failed": [], "patterns": []}

        lines = []
        for e in evaluations:
            lines.append(
                f"- Skill: {e.get('skill_name')}, UID: {e.get('uid')}, "
                f"Score: {e.get('score', 0)}, Status: {e.get('status')}"
            )

        client = _get_client()
        response = client.chat.completions.create(
            model=HAIKU_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": f"""Based on these QA evaluation results for Treasury Bulletin questions, extract learnings:

{chr(10).join(lines)}

Respond in JSON:
{{
  "promising": [{{"direction": "what works", "evidence": "brief data"}}],
  "failed": [{{"direction": "what to avoid", "evidence": "brief data"}}],
  "patterns": [{{"pattern": "reusable pattern", "source_skills": ["skill1"]}}]
}}

Only include entries with clear evidence. Empty lists are fine. Be concise.""",
                }
            ],
            temperature=0.2,
            max_tokens=500,
        )

        text = response.choices[0].message.content.strip()
        result = _parse_json(text)
        for key in ("promising", "failed", "patterns"):
            if key not in result or not isinstance(result[key], list):
                result[key] = []
        return result

    # --- Checkpoint and feedback persistence ---

    def _load_feedback_history(self) -> list[str]:
        if not FEEDBACK_PATH.exists():
            return []
        text = FEEDBACK_PATH.read_text().strip()
        return text.split("\n") if text else []

    def _save_feedback(self, text: str):
        FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(FEEDBACK_PATH, "a") as f:
            f.write(text + "\n")
        self.feedback_history.append(text)

    def _save_checkpoint(self, step_num: int, result: dict):
        checkpoint = {
            "step_num": step_num,
            "timestamp": datetime.utcnow().isoformat() + "Z",
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
        if not CHECKPOINT_PATH.exists():
            return None
        return json.loads(CHECKPOINT_PATH.read_text())


def _parse_json(text: str) -> dict:
    """Parse JSON from LLM response."""
    if "```" in text:
        lines = text.split("\n")
        json_lines = []
        in_block = False
        for line in lines:
            if line.strip().startswith("```"):
                in_block = not in_block
                continue
            if in_block:
                json_lines.append(line)
        text = "\n".join(json_lines)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
        return {"name": "unknown", "description": text[:200], "rationale": "parse error"}
