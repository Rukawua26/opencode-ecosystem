#!/bin/bash
# create-skill.sh - Scaffold a new OpenCode skill
# Usage: bash tools/scripts/create-skill.sh <skill-name>

set -euo pipefail

SKILL_NAME="${1:-}"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SKILLS_DIR="$REPO_ROOT/skills"

if [ -z "$SKILL_NAME" ]; then
  echo "Usage: bash tools/scripts/create-skill.sh <skill-name>"
  echo "Example: bash tools/scripts/create-skill.sh my-new-skill"
  exit 1
fi

SKILL_DIR="$SKILLS_DIR/$SKILL_NAME"

if [ -d "$SKILL_DIR" ]; then
  echo "Error: Skill '$SKILL_NAME' already exists at $SKILL_DIR"
  exit 1
fi

echo "Creating skill: $SKILL_NAME"
mkdir -p "$SKILL_DIR"

cat > "$SKILL_DIR/SKILL.md" << EOF
---
name: $SKILL_NAME
description: TODO - Describe what this skill does and when to use it.
---

# $SKILL_NAME

TODO - Explain the purpose of this skill.

## When to Use

TODO - Describe the trigger conditions for this skill.

## Instructions

TODO - Step-by-step instructions for the agent.

## Examples

TODO - Show example usage.

## Constraints

TODO - List any limitations or rules.
EOF

echo "Created: $SKILL_DIR/SKILL.md"
echo ""
echo "Next steps:"
echo "  1. Edit $SKILL_DIR/SKILL.md"
echo "  2. Fill in the description, instructions, and examples"
echo "  3. Run 'npm test' to verify the skill structure"
echo ""
