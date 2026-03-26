"""LLM-as-Judge evaluator for title/description quality.

Uses LLM to score generated titles as a proxy for CTR
when real click data is too sparse for statistical evaluation.
"""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

EVAL_MODEL = "anthropic/claude-haiku-4.5"


def _get_client() -> OpenAI:
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        timeout=60.0,
        max_retries=2,
    )


def evaluate_title(
    original_title: str,
    generated_title: str,
    generated_description: str,
    query: str,
    position: float,
) -> dict:
    """Score a generated title/description against the original.

    Returns:
        dict with keys: score (0-10), dimensions (dict of sub-scores), reasoning
    """
    client = _get_client()
    response = client.chat.completions.create(
        model=EVAL_MODEL,
        messages=[
            {
                "role": "user",
                "content": f"""Rate this SEO title/description rewrite for the search query "{query}" (position {position:.0f}).

ORIGINAL TITLE: {original_title or "(none)"}

GENERATED TITLE: {generated_title}
GENERATED DESCRIPTION: {generated_description}

Score each dimension 0-10:
1. keyword_relevance: Does the title contain the query or close variants?
2. click_appeal: Would a searcher want to click? (curiosity, value proposition, specificity)
3. length_quality: Title 50-60 chars? Description 120-160 chars? No truncation risk?
4. intent_match: Does it match what someone searching "{query}" actually wants?
5. improvement: Is this better than the original? (5 = same, >5 = better, <5 = worse)

Respond in JSON only:
{{"score": <overall 0-10>, "dimensions": {{"keyword_relevance": N, "click_appeal": N, "length_quality": N, "intent_match": N, "improvement": N}}, "reasoning": "<one sentence>"}}""",
            }
        ],
        temperature=0.2,
        max_tokens=300,
    )

    text = response.choices[0].message.content.strip()
    return _parse_json(text)


def evaluate_batch(interventions: list[dict]) -> list[dict]:
    """Evaluate a batch of interventions using LLM-as-Judge.

    Each intervention must have: generated_title, generated_description, query,
    position_at_intervention, and optionally original_title.

    Returns list of evaluation results with llm_score added.
    """
    results = []
    for interv in interventions:
        eval_result = evaluate_title(
            original_title=interv.get("original_title", ""),
            generated_title=interv.get("generated_title", ""),
            generated_description=interv.get("generated_description", ""),
            query=interv.get("query", ""),
            position=interv.get("position_at_intervention", 10),
        )
        results.append(
            {
                "intervention_id": interv.get("intervention_id"),
                "skill_name": interv.get("skill_name"),
                "query": interv.get("query"),
                "page_url": interv.get("page_url"),
                "llm_score": eval_result.get("score", 5),
                "llm_dimensions": eval_result.get("dimensions", {}),
                "llm_reasoning": eval_result.get("reasoning", ""),
                "status": _score_to_status(eval_result.get("score", 5)),
            }
        )
    return results


def _score_to_status(score: float) -> str:
    """Convert LLM score to status for frontier compatibility."""
    if score >= 7:
        return "success"
    elif score <= 3:
        return "failure"
    return "inconclusive"


def _parse_json(text: str) -> dict:
    """Parse JSON from LLM response (same pattern as executor/proposer)."""
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
        return {"score": 5, "dimensions": {}, "reasoning": "parse error"}
