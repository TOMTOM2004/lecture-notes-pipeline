#!/usr/bin/env python3
"""
Convert a lecture PDF to Markdown and JSON using OpenDataLoader PDF.

Usage (run from repository root with venv active):
    source .venv/bin/activate
    python scripts/pdf/convert-pdf.py <course> <lecture_num> <pdf_path> [--type assignment]

Examples:
    python scripts/pdf/convert-pdf.py example-course L07 \
        "courses/example-course/raw/handouts/pdf/L07_slides.pdf"

    python scripts/pdf/convert-pdf.py example-course A01 \
        "courses/example-course/raw/assignments/pdf/A01_exercise.pdf" --type assignment
"""

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Ensure Homebrew-installed Java is found regardless of shell PATH
_java_homebrew = Path("/opt/homebrew/opt/openjdk/bin")
if _java_homebrew.exists() and str(_java_homebrew) not in os.environ.get("PATH", ""):
    os.environ["PATH"] = str(_java_homebrew) + os.pathsep + os.environ.get("PATH", "")

try:
    import opendataloader_pdf
except ImportError:
    print("Error: opendataloader-pdf is not installed.")
    print("Run: pip install -U opendataloader-pdf")
    sys.exit(1)

REPO_ROOT = Path(__file__).parent.parent.parent

# Fill-in blanks in distributed handouts appear as full-width parens whose only
# content is whitespace (optionally a trailing %). The whitespace class excludes
# newlines so a match can never span lines.
_BLANK_PCT_RE = re.compile(r"（[ \t　]*%[ \t　]*）")
_BLANK_RE = re.compile(r"（[ \t　]+）")

# Japanese script chars (hiragana・katakana・kanji・々〆). PDF text extraction
# scatters stray spaces *between* such chars (justified layout / per-glyph
# positioning), e.g. "収 益", "得 ら れ る". Japanese prose almost never spaces
# these, so collapsing a space flanked by two of them is correct the vast
# majority of the time. Spaces next to ASCII/digits ("S 社", "次の 2 つ") or `*`
# (blank marker `（ **** ）`) keep a non-JP side and are left untouched.
#
# NOT zero-false-positive (unlike blank normalization): a half-width space can be
# meaningful between two JP chars in opendataloader-shredded formulas
# (numerator / denominator) or item-boundary fragments — those get merged. This
# is an accepted trade-off: the original spacing survives in pdf_json (built from
# the un-postprocessed tree), which the structure-cleanup LLM pass reads to
# reconstruct formulas. Full-width spaces (U+3000) in deliberate formula layout
# are outside the `[ \t]` class and preserved.
_JP = r"぀-ヿ㐀-䶿一-鿿々〆゠"
_JP_GAP_RE = re.compile(rf"(?<=[{_JP}])[ \t]+(?=[{_JP}])")

# Same artifact next to Japanese punctuation / brackets, e.g. "の 「営業", "分類 （単位",
# "から ，（". A space is removed only when one side is JP punctuation and the other is
# JP-script-or-punctuation — so the blank marker `（ **** ）` (the adjacent char is the
# ASCII `*`) and ASCII-adjacent spacing are left untouched.
_JP_PUNCT = r"「」『』（）〔〕【】、。，．！？"
_ALLOWED = _JP + _JP_PUNCT
_PUNCT_GAP_RE1 = re.compile(rf"(?<=[{_ALLOWED}])[ \t]+(?=[{_JP_PUNCT}])")
_PUNCT_GAP_RE2 = re.compile(rf"(?<=[{_JP_PUNCT}])[ \t]+(?=[{_ALLOWED}])")


def postprocess_markdown(md_text: str) -> str:
    """Mechanical cleanup applied to every converted Markdown.

    1. Normalize empty fill-in blanks to the repo blank notation `（ **** ）` so
       downstream notes share one marker (`**** ` flanked by half-width spaces).
       Filled parens (digits/text inside, e.g. `（100.0 %）`) are left untouched.
    2. Collapse stray spaces sitting between two Japanese-script characters, or
       next to Japanese punctuation / brackets (PDF extraction artifact).
       Conservative: a neighbour must always be JP-script-or-punctuation, so
       intentional spacing around alphanumerics / the `（ **** ）` marker survives.

    Heading / page-break-split repair and soft-wrap (mid-sentence newline) joins
    are intentionally NOT done here — they need judgment and live in the
    structure-cleanup pass (see _pdf-common-phases.md).
    """
    md_text = _BLANK_PCT_RE.sub("（ **** %）", md_text)
    md_text = _BLANK_RE.sub("（ **** ）", md_text)
    md_text = _JP_GAP_RE.sub("", md_text)
    # Two rounds so chained gaps ("， 営業" -> "，営業") fully collapse.
    for _ in range(2):
        md_text = _PUNCT_GAP_RE1.sub("", md_text)
        md_text = _PUNCT_GAP_RE2.sub("", md_text)
    return md_text


def parse_args():
    parser = argparse.ArgumentParser(description="Convert lecture PDF to Markdown and JSON")
    parser.add_argument("course", help="Course directory name (e.g. example-course)")
    parser.add_argument("lecture", help="Lecture number (e.g. L07)")
    parser.add_argument("pdf_path", help="Path to the source PDF file")
    parser.add_argument("--type", choices=["lecture", "assignment", "data"], default="lecture",
                        help="PDF type: lecture (default), assignment, or data (reference data)")
    return parser.parse_args()


def build_output_paths(course: str, lecture: str, pdf_path: Path, pdf_type: str = "lecture"):
    stem = pdf_path.stem  # e.g. L07_slides
    course_dir = REPO_ROOT / "courses" / course

    if pdf_type == "assignment":
        md_dir = course_dir / "converted" / "assignment_md"
        json_dir = course_dir / "converted" / "assignment_json"
    elif pdf_type == "data":
        md_dir = course_dir / "converted" / "data_md"
        json_dir = course_dir / "converted" / "data_json"
    else:
        md_dir = course_dir / "converted" / "pdf_md"
        json_dir = course_dir / "converted" / "pdf_json"
    log_dir = course_dir / "converted" / "logs"

    for d in [md_dir, json_dir, log_dir]:
        d.mkdir(parents=True, exist_ok=True)

    return {
        "md": md_dir / f"{stem}.md",
        "json": json_dir / f"{stem}.json",
        "log": log_dir / f"{stem}_convert.log",
        "tmp": REPO_ROOT / ".tmp_convert",
    }


def run_conversion(pdf_path: Path, tmp_dir: Path):
    """Run OpenDataLoader PDF conversion."""
    tmp_dir.mkdir(parents=True, exist_ok=True)
    opendataloader_pdf.convert(
        input_path=[str(pdf_path)],
        output_dir=str(tmp_dir),
        format="json,markdown",
    )


def find_tmp_outputs(tmp_dir: Path, stem: str):
    """Find the generated files in tmp directory."""
    md_files = list(tmp_dir.glob(f"{stem}*.md"))
    json_files = list(tmp_dir.glob(f"{stem}*.json"))
    return (md_files[0] if md_files else None,
            json_files[0] if json_files else None)


def collect_elements(node: dict | list, result: list) -> None:
    """
    Recursively walk OpenDataLoader's nested JSON tree and collect
    all leaf-level content nodes into a flat list.

    Actual structure:
      top-level: { "file name": ..., "kids": [ {element}, ... ] }
      elements may contain nested "kids" and "list items"
    """
    if isinstance(node, list):
        for item in node:
            collect_elements(item, result)
    elif isinstance(node, dict):
        el_type = node.get("type", "")
        if el_type in ("paragraph", "heading", "table") and node.get("content"):
            result.append(node)
        elif el_type in ("list item",) and node.get("content"):
            result.append(node)
        # Recurse into kids and list items
        for child in node.get("kids", []):
            collect_elements(child, result)
        for item in node.get("list items", []):
            collect_elements(item, result)


def build_structured_json(raw_json_path: Path, course: str, lecture: str, pdf_path: Path):
    """
    Convert OpenDataLoader's nested JSON tree into a flat page-grouped structure
    for Claude API input.
    """
    with open(raw_json_path, encoding="utf-8") as f:
        raw = json.load(f)

    flat_elements: list = []
    collect_elements(raw, flat_elements)

    pages: dict[int, dict] = {}

    for el in flat_elements:
        page_num = el.get("page number", 1)
        el_type = el.get("type", "")
        content = el.get("content", "")

        if page_num not in pages:
            pages[page_num] = {"page": page_num, "headings": [], "body": "", "tables": []}

        if el_type == "heading":
            pages[page_num]["headings"].append(content)
        elif el_type == "table":
            pages[page_num]["tables"].append(content)
        else:
            pages[page_num]["body"] += content + "\n"

    # Extract title from first heading
    title = ""
    if pages and 1 in pages and pages[1]["headings"]:
        title = pages[1]["headings"][0]

    return {
        "course": course,
        "lecture": lecture,
        "title": title,
        "source_pdf": pdf_path.name,
        "converted_at": datetime.now().isoformat(),
        "pages": [pages[p] for p in sorted(pages.keys())],
    }


def write_log(log_path: Path, pdf_path: Path, outputs: dict, success: bool, error: str = ""):
    log_path.write_text(
        f"timestamp: {datetime.now().isoformat()}\n"
        f"source: {pdf_path}\n"
        f"md_output: {outputs['md']}\n"
        f"json_output: {outputs['json']}\n"
        f"status: {'success' if success else 'error'}\n"
        + (f"error: {error}\n" if error else ""),
        encoding="utf-8",
    )


def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = parse_args()

    pdf_path = Path(args.pdf_path).resolve()
    if not pdf_path.exists():
        logging.error(f"PDF not found: {pdf_path}")
        sys.exit(1)

    outputs = build_output_paths(args.course, args.lecture, pdf_path, args.type)

    logging.info(f"Converting: {pdf_path.name}")
    logging.info(f"  → Markdown : {outputs['md']}")
    logging.info(f"  → JSON     : {outputs['json']}")

    try:
        run_conversion(pdf_path, outputs["tmp"])

        tmp_md, tmp_json = find_tmp_outputs(outputs["tmp"], pdf_path.stem)

        # Save Markdown
        if tmp_md:
            md_text = postprocess_markdown(tmp_md.read_text(encoding="utf-8"))
            outputs["md"].write_text(md_text, encoding="utf-8")
            logging.info("  Markdown saved.")
        else:
            logging.warning("  Markdown output not found.")

        # Build and save structured JSON
        if tmp_json:
            structured = build_structured_json(tmp_json, args.course, args.lecture, pdf_path)
            outputs["json"].write_text(
                json.dumps(structured, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            logging.info("  JSON saved.")
        else:
            logging.warning("  JSON output not found.")

        write_log(outputs["log"], pdf_path, outputs, success=True)
        logging.info("Done.")

    except Exception as e:
        write_log(outputs["log"], pdf_path, outputs, success=False, error=str(e))
        logging.error(f"Conversion failed: {e}")
        sys.exit(1)

    finally:
        # Clean up tmp directory
        import shutil
        if outputs["tmp"].exists():
            shutil.rmtree(outputs["tmp"])


if __name__ == "__main__":
    main()
