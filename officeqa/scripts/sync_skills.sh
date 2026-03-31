#!/bin/bash
# Sync evolved skills from office_qa/skills/ to officeqa/skills/ (Arena submission dir)
# Usage: bash scripts/sync_skills.sh [--dry-run]

set -euo pipefail

EVOLVED_DIR="$(dirname "$0")/../../office_qa/skills"
ARENA_DIR="$(dirname "$0")/../skills"

if [ ! -d "$EVOLVED_DIR" ]; then
    echo "Error: evolved skills dir not found at $EVOLVED_DIR"
    exit 1
fi

DRY_RUN=false
if [ "${1:-}" = "--dry-run" ]; then
    DRY_RUN=true
fi

echo "Syncing evolved skills to Arena submission..."
echo "  From: $EVOLVED_DIR"
echo "  To:   $ARENA_DIR"

# Read active skills from frontier
ACTIVE_FILE="$EVOLVED_DIR/frontier/active_skills.json"
if [ ! -f "$ACTIVE_FILE" ]; then
    echo "Error: no active_skills.json found"
    exit 1
fi

# Extract active skill names
ACTIVE_SKILLS=$(python3 -c "import json; print('\n'.join(json.load(open('$ACTIVE_FILE'))['active']))")

echo ""
echo "Active skills:"
for skill in $ACTIVE_SKILLS; do
    # Find latest version
    SKILL_DIR="$EVOLVED_DIR/$skill"
    if [ ! -d "$SKILL_DIR" ]; then
        echo "  SKIP: $skill (no directory)"
        continue
    fi

    LATEST=$(ls -d "$SKILL_DIR"/v* 2>/dev/null | sort -V | tail -1)
    if [ -z "$LATEST" ]; then
        echo "  SKIP: $skill (no versions)"
        continue
    fi

    VERSION=$(basename "$LATEST")
    SKILL_FILE="$LATEST/SKILL.md"
    if [ ! -f "$SKILL_FILE" ]; then
        echo "  SKIP: $skill/$VERSION (no SKILL.md)"
        continue
    fi

    # Convert SKILL.md to a flat .md file for arena skills_dir
    TARGET="$ARENA_DIR/${skill}.md"
    if [ "$DRY_RUN" = true ]; then
        echo "  WOULD COPY: $skill/$VERSION -> skills/${skill}.md"
    else
        cp "$SKILL_FILE" "$TARGET"
        echo "  SYNCED: $skill/$VERSION -> skills/${skill}.md"
    fi
done

echo ""
echo "Done. Run 'arena test --dry-run' to validate."
