"""Skill generation — create new SKILL.md from strategy proposal."""
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
SKILLS_DIR = PROJECT_ROOT / "skills"

DEFAULT_MODEL = "anthropic/claude-sonnet-4.6"


def _get_client() -> OpenAI:
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        timeout=60.0,
        max_retries=2,
    )


def generate_skill(
    strategy: dict,
    existing_skills: list[str],
    model: str = DEFAULT_MODEL,
) -> tuple[str, str]:
    """Generate a new SKILL.md from a strategy proposal.

    Args:
        strategy: dict with keys: name, description, rationale
        existing_skills: Names of existing skills (to avoid duplication)

    Returns:
        (skill_name, content) tuple
    """
    skill_name = strategy["name"]

    client = _get_client()
    response = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": f"""Create a SKILL.md file for an SEO title/description optimization strategy.

## Strategy
- Name: {skill_name}
- Description: {strategy['description']}
- Rationale: {strategy['rationale']}

## Existing Skills (do NOT duplicate)
{', '.join(existing_skills)}

## Required Format
Write the SKILL.md with these sections:
# {{skill_name}}
## 策略描述
## 适用场景
## 核心技巧
## 示例
## Prompt 模板

Make it specific and actionable. Include 2-3 before/after examples.
Output ONLY the markdown content, no code fences."""
        }],
        temperature=0.7,
        max_tokens=1000,
    )

    content = response.choices[0].message.content.strip()
    return skill_name, content


def save_skill(skill_name: str, content: str) -> Path:
    """Save SKILL.md to skills/{name}/v{N}/SKILL.md.

    Auto-increments version number.
    """
    skill_dir = SKILLS_DIR / skill_name

    # Find next version
    if skill_dir.exists():
        existing = sorted(
            [d for d in skill_dir.iterdir() if d.is_dir() and d.name.startswith("v")],
            key=lambda d: int(d.name[1:])
        )
        next_version = int(existing[-1].name[1:]) + 1 if existing else 1
    else:
        next_version = 1

    version_dir = skill_dir / f"v{next_version}"
    version_dir.mkdir(parents=True, exist_ok=True)

    path = version_dir / "SKILL.md"
    path.write_text(content)

    return path
