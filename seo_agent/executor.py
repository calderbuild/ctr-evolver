"""Title/description generator using LLM + skill templates."""
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
SKILLS_DIR = PROJECT_ROOT / "skills"
FRONTIER_PATH = SKILLS_DIR / "frontier" / "active_skills.json"

# Dev model (free)
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
        # Find latest version
        versions = sorted(
            [d for d in skill_dir.iterdir() if d.is_dir() and d.name.startswith("v")],
            key=lambda d: int(d.name[1:])
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


def generate_title_desc(
    page_url: str,
    current_title: str,
    current_desc: str,
    query: str,
    position: float,
    skill_name: str,
    model: str = DEFAULT_MODEL,
) -> dict:
    """Generate new title + description using a skill template.

    Returns dict with keys: title, description, reasoning
    """
    skill_content = load_skill(skill_name)

    prompt = f"""You are an SEO expert. Your task is to write a new title and meta description for a web page to improve its click-through rate (CTR) in Google search results.

## Current Page Info
- URL: {page_url}
- Current Title: {current_title or '(unknown)'}
- Current Description: {current_desc or '(unknown)'}
- Target Query: {query}
- Current Position: {position:.1f}

## Strategy to Apply
{skill_content}

## Instructions
1. Apply the strategy described above to craft a new title and meta description
2. The title should be under 60 characters
3. The description should be under 155 characters
4. Both must be relevant to the query and page content
5. Do NOT use clickbait — the content must deliver on the promise

Respond in JSON format:
{{"title": "...", "description": "...", "reasoning": "..."}}"""

    client = _get_client()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=500,
    )

    text = response.choices[0].message.content.strip()
    return _parse_json_response(text)


def _parse_json_response(text: str) -> dict:
    """Parse JSON from LLM response, handling markdown code blocks."""
    # Strip markdown code fences if present
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
        # Fallback: try to find JSON object in text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
        return {
            "title": "(parse error)",
            "description": "(parse error)",
            "reasoning": f"Failed to parse LLM response: {text[:200]}"
        }
