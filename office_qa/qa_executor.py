"""QA answer generator using LLM + skill templates."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
SKILLS_DIR = PROJECT_ROOT / "office_qa" / "skills"
FRONTIER_PATH = SKILLS_DIR / "frontier" / "active_skills.json"

DEFAULT_MODEL = "anthropic/claude-sonnet-4.6"


def _get_client() -> OpenAI:
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        timeout=60.0,
        max_retries=2,
    )


def load_skill(skill_name: str, version: int | None = None) -> str:
    """Read SKILL.md content for a given skill.

    If version is None, loads the latest version.
    """
    skill_dir = SKILLS_DIR / skill_name
    if not skill_dir.exists():
        raise FileNotFoundError(f"Skill not found: {skill_name}")

    if version is not None:
        path = skill_dir / f"v{version}" / "SKILL.md"
    else:
        versions = sorted(
            [d for d in skill_dir.iterdir() if d.is_dir() and d.name.startswith("v")],
            key=lambda d: int(d.name[1:]),
        )
        if not versions:
            raise FileNotFoundError(f"No versions found for skill: {skill_name}")
        path = versions[-1] / "SKILL.md"

    return path.read_text()


def list_active_skills() -> list[str]:
    """Read active skill names from frontier/active_skills.json."""
    if not FRONTIER_PATH.exists():
        return []
    data = json.loads(FRONTIER_PATH.read_text())
    return data.get("active", [])


def save_active_skills(skills: list[str]):
    """Write active skill names to frontier/active_skills.json."""
    FRONTIER_PATH.parent.mkdir(parents=True, exist_ok=True)
    FRONTIER_PATH.write_text(json.dumps({"active": skills}, indent=2))


def generate_answer(
    question: str,
    source_files: list[str],
    skill_name: str,
    model: str = DEFAULT_MODEL,
) -> dict:
    """Generate an answer to an OfficeQA question using a skill template.

    Args:
        question: The question text
        source_files: List of source file names (e.g., treasury_bulletin_1941_01.txt)
        skill_name: Name of the skill to apply

    Returns dict with keys: answer, reasoning, confidence
    """
    skill_content = load_skill(skill_name)

    source_hint = ""
    if source_files:
        source_hint = f"Relevant source files: {', '.join(source_files)}"

    prompt = f"""You are an expert financial analyst answering questions about U.S. Treasury Bulletins.

## Question
{question}

## Source Information
{source_hint}
The full corpus is at /app/corpus/ with files named treasury_bulletin_YYYY_MM.txt.

## Strategy to Apply
{skill_content}

## Instructions
1. Apply the strategy above to determine the answer
2. Show your reasoning step by step
3. Be precise with numerical values -- scoring uses 1% tolerance
4. Pay attention to units (millions, billions) and rounding requirements

Respond in JSON format:
{{"answer": "your precise answer", "reasoning": "step-by-step reasoning", "confidence": "high/medium/low"}}"""

    client = _get_client()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1500,
    )

    text = response.choices[0].message.content.strip()
    return _parse_json_response(text)


def _parse_json_response(text: str) -> dict:
    """Parse JSON from LLM response, handling markdown code blocks."""
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
        return {
            "answer": "(parse error)",
            "reasoning": f"Failed to parse LLM response: {text[:200]}",
            "confidence": "low",
        }
