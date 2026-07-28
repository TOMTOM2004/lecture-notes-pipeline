#!/usr/bin/env python3
"""
Fix table structure in PDF-converted Markdown files using Claude API.

PDF conversion often produces broken tables:
  - Image references with embedded text labels (e.g. "![image 1](...) a")
  - Merged-cell hierarchies flattened into wrong columns
  - Missing row/column labels

This script reads converted/pdf_md/{lecture}_*.md and the corresponding
converted/pdf_json/{lecture}_*.json, then calls Claude API to reconstruct
correct Markdown tables. The fixed MD is written back in place.

Usage (run from repository root with venv active):
    source .venv/bin/activate
    python scripts/pdf/table-normalize.py <course> <lecture>

Example:
    python scripts/pdf/table-normalize.py example-course L02
"""

import argparse
import logging
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent

SYSTEM_PROMPT = """\
You are a Markdown document repair assistant specializing in tables converted from PDFs.

Your task: fix ONLY the tables in the given Markdown document. Leave all other content unchanged.

Common problems to fix:
1. Image references that contain text labels — e.g. "![image 2](path) a" means the cell value is "a".
   Extract the label text and discard the image reference entirely.
2. Hierarchical (merged-cell) tables that were flattened incorrectly — reconstruct the correct
   row/column grouping using the surrounding body text as context.
3. Columns shifted or extra empty columns introduced by the converter.

Rules:
- Output the complete corrected Markdown document and nothing else (no explanation, no code fences).
- If a table looks correct already, leave it unchanged.
- Use the JSON body text provided as context to infer missing label values.
- Blank fill-in-the-blank cells (e.g. "(　)" or empty cells that are intentional gaps in the
  original) must remain blank — do not fill them in.
"""


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fix table structure in converted Markdown using Claude API"
    )
    parser.add_argument("course", help="Course directory name")
    parser.add_argument("lecture", help="Lecture prefix (e.g. L02)")
    return parser.parse_args()


def find_pairs(course: str, lecture: str):
    """Return list of (md_path, json_path) pairs for the lecture."""
    course_dir = REPO_ROOT / "courses" / course
    md_dir = course_dir / "converted" / "pdf_md"
    json_dir = course_dir / "converted" / "pdf_json"

    pairs = []
    for md_path in sorted(md_dir.glob(f"{lecture}_*.md")):
        json_path = json_dir / (md_path.stem + ".json")
        pairs.append((md_path, json_path if json_path.exists() else None))

    return pairs


def build_user_message(md_path: Path, json_path: Path | None) -> str:
    md_content = md_path.read_text(encoding="utf-8")

    context = ""
    if json_path:
        import json
        data = json.loads(json_path.read_text(encoding="utf-8"))
        body_parts = [p.get("body", "") for p in data.get("pages", [])]
        body_text = "\n".join(b for b in body_parts if b.strip())
        if body_text:
            context = f"\n\n---\nJSON body text (for context / label inference):\n{body_text}"

    return f"Markdown document to fix:\n\n{md_content}{context}"


def call_claude(user_message: str) -> str:
    try:
        import anthropic
    except ImportError:
        logging.error("anthropic is not installed. Run: pip install anthropic")
        sys.exit(1)

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = parse_args()

    pairs = find_pairs(args.course, args.lecture)
    if not pairs:
        logging.error(f"No MD files found for {args.lecture} in course {args.course}")
        sys.exit(1)

    for md_path, json_path in pairs:
        logging.info(f"Processing: {md_path.name}")
        user_message = build_user_message(md_path, json_path)

        logging.info("  Calling Claude API...")
        fixed_md = call_claude(user_message)

        md_path.write_text(fixed_md, encoding="utf-8")
        logging.info(f"  Fixed MD written: {md_path}")

    logging.info("Done.")


if __name__ == "__main__":
    main()
