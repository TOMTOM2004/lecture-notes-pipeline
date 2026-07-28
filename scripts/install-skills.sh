#!/bin/bash
# Install skills to Claude Code's skills directory
# Run from repository root: bash scripts/install-skills.sh

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_SRC="$REPO_ROOT/.claude/SKILLS"
SKILLS_DEST="$HOME/.claude/skills"

if [ ! -d "$SKILLS_SRC" ]; then
  echo "Error: $SKILLS_SRC not found"
  exit 1
fi

mkdir -p "$SKILLS_DEST"

echo "Installing skills from $SKILLS_SRC to $SKILLS_DEST"

for skill_file in "$SKILLS_SRC"/*.md; do
  filename="$(basename "$skill_file")"
  dest="$SKILLS_DEST/$filename"

  if [ -f "$dest" ]; then
    echo "  Updating: $filename"
  else
    echo "  Installing: $filename"
  fi

  cp "$skill_file" "$dest"
done

echo ""
echo "Done. Installed skills:"
ls "$SKILLS_DEST"/*.md 2>/dev/null | xargs -I{} basename {}
echo ""
echo "Reload Claude Code to apply changes."
