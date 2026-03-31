"""LLM-as-Judge evaluator for QA answer quality.

Uses LLM to score generated answers against reference answers
or evaluate answer quality when ground truth is unavailable.
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


def evaluate_answer(
    question: str,
    generated_answer: str,
    expected_answer: str = "",
    difficulty: str = "unknown",
) -> dict:
    """Score a generated answer for an OfficeQA question.

    Returns:
        dict with keys: score (0-10), dimensions (dict of sub-scores), reasoning
    """
    reference_section = ""
    if expected_answer:
        reference_section = f"\nREFERENCE ANSWER: {expected_answer}"

    client = _get_client()
    response = client.chat.completions.create(
        model=EVAL_MODEL,
        messages=[
            {
                "role": "user",
                "content": f"""Rate this answer to a U.S. Treasury Bulletin question (difficulty: {difficulty}).

QUESTION: {question}

GENERATED ANSWER: {generated_answer}
{reference_section}

Score each dimension 0-10:
1. factual_accuracy: Is the answer numerically correct or very close to the reference?
2. completeness: Does it answer all parts of the question?
3. numerical_precision: Correct decimal places, units, rounding as specified?
4. reasoning_quality: Does the reasoning path make sense for this type of question?
5. source_grounding: Does the answer appear grounded in actual document data (not hallucinated)?

Respond in JSON only:
{{"score": <overall 0-10>, "dimensions": {{"factual_accuracy": N, "completeness": N, "numerical_precision": N, "reasoning_quality": N, "source_grounding": N}}, "reasoning": "<one sentence>"}}""",
            }
        ],
        temperature=0.2,
        max_tokens=300,
    )

    text = response.choices[0].message.content.strip()
    return _parse_json(text)


def evaluate_batch(interventions: list[dict]) -> list[dict]:
    """Evaluate a batch of QA interventions using LLM-as-Judge.

    Each intervention must have: question, generated_answer, skill_name.
    Optionally: expected_answer, difficulty.

    Returns list of evaluation results with llm_score added.
    """
    results = []
    for interv in interventions:
        eval_result = evaluate_answer(
            question=interv.get("question", ""),
            generated_answer=interv.get("generated_answer", ""),
            expected_answer=interv.get("expected_answer", ""),
            difficulty=interv.get("difficulty", "unknown"),
        )
        results.append(
            {
                "intervention_id": interv.get("intervention_id"),
                "skill_name": interv.get("skill_name"),
                "question": interv.get("question", "")[:100],
                "uid": interv.get("uid"),
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
        return {"score": 5, "dimensions": {}, "reasoning": "parse error"}
