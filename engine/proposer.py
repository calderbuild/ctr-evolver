"""Failure analysis and new strategy proposal."""
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def _get_client() -> OpenAI:
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        timeout=60.0,
        max_retries=2,
    )


DEFAULT_MODEL = "anthropic/claude-sonnet-4.6"


def analyze_failures(
    evaluations: list[dict],
    memory_text: str = "",
    history_summary: str = "",
) -> str:
    """Analyze failed interventions to find common patterns.

    Args:
        evaluations: List of evaluation dicts (from evaluator.evaluate_intervention)
                     each must also contain 'skill_name', 'query', 'page_url'
        memory_text: Formatted evolution memory (from EvolutionMemory.to_prompt_text())
        history_summary: Cross-step evaluation summary table

    Returns:
        Analysis text describing failure patterns
    """
    failures = [e for e in evaluations if e.get("status") in ("failure", "inconclusive")]

    if not failures:
        return "No failures to analyze."

    # Build summary for LLM
    failure_lines = []
    for f in failures:
        failure_lines.append(
            f"- Skill: {f.get('skill_name', '?')}, Query: {f.get('query', '?')}, "
            f"CTR lift: {f.get('ctr_lift', 0):.4f}, Status: {f.get('status')}"
        )

    failure_summary = "\n".join(failure_lines)

    # Build context sections
    context_parts = []
    if memory_text:
        context_parts.append(f"## Evolution Memory\n{memory_text}")
    if history_summary:
        context_parts.append(f"## Cross-Step History\n{history_summary}")
    extra_context = "\n\n".join(context_parts)

    client = _get_client()
    response = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[{
            "role": "user",
            "content": f"""Analyze these failed SEO title/description interventions and identify common patterns:

{failure_summary}

{extra_context}

What patterns do you see? What types of queries or strategies tend to fail? Be specific and concise.
Respond in 3-5 bullet points."""
        }],
        temperature=0.3,
        max_tokens=500,
    )

    return response.choices[0].message.content.strip()


def propose_strategy(
    failure_analysis: str,
    current_skills: list[str],
    feedback_history: list[str],
    memory_text: str = "",
    model: str = DEFAULT_MODEL,
) -> dict:
    """Propose a new skill strategy based on failure analysis.

    Args:
        failure_analysis: Output from analyze_failures()
        current_skills: Names of currently active skills
        feedback_history: List of past feedback/analysis strings
        memory_text: Formatted evolution memory

    Returns:
        dict with keys: name, description, rationale
    """
    history_text = "\n".join(f"- {fb}" for fb in feedback_history[-5:]) if feedback_history else "None yet."

    memory_section = f"\n## Evolution Memory\n{memory_text}\n" if memory_text else ""

    client = _get_client()
    response = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": f"""You are an SEO strategy researcher. Based on the failure analysis below, propose ONE new title/description optimization strategy.

## Failure Analysis
{failure_analysis}

## Current Active Skills
{', '.join(current_skills)}

## Past Feedback
{history_text}
{memory_section}
## Requirements
- The strategy must be DIFFERENT from existing skills
- It should address the failure patterns identified
- It should be specific and actionable
- AVOID directions listed in "Failed Directions" above
- BUILD ON patterns listed in "Promising Directions" and "Effective Patterns"

Respond in JSON:
{{"name": "snake_case_name", "description": "One sentence description", "rationale": "Why this addresses the failures"}}"""
        }],
        temperature=0.8,
        max_tokens=300,
    )

    text = response.choices[0].message.content.strip()
    return _parse_json(text)


def _parse_json(text: str) -> dict:
    """Parse JSON from LLM response."""
    import json

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


def extract_memory_updates(evaluations: list[dict]) -> dict:
    """Extract structured memory updates from evaluation results.

    Returns dict with keys: promising, failed, patterns
    Each is a list of dicts with direction/pattern + evidence.
    """
    if not evaluations:
        return {"promising": [], "failed": [], "patterns": []}

    # Build evaluation summary
    lines = []
    for e in evaluations:
        lines.append(
            f"- Skill: {e.get('skill_name', '?')}, Query: {e.get('query', '?')}, "
            f"CTR lift: {e.get('ctr_lift', 0):.4f}, Status: {e.get('status')}"
        )
    summary = "\n".join(lines)

    client = _get_client()
    response = client.chat.completions.create(
        model="anthropic/claude-haiku-4.5",
        messages=[{
            "role": "user",
            "content": f"""Based on these SEO intervention evaluation results, extract learnings:

{summary}

Respond in JSON:
{{
  "promising": [{{"direction": "what works", "evidence": "brief data"}}],
  "failed": [{{"direction": "what to avoid", "evidence": "brief data"}}],
  "patterns": [{{"pattern": "reusable pattern", "source_skills": ["skill1"]}}]
}}

Only include entries with clear evidence. Empty lists are fine. Be concise."""
        }],
        temperature=0.2,
        max_tokens=500,
    )

    text = response.choices[0].message.content.strip()
    result = _parse_json(text)

    # Validate structure
    for key in ("promising", "failed", "patterns"):
        if key not in result or not isinstance(result[key], list):
            result[key] = []

    return result
