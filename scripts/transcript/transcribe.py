#!/usr/bin/env python3
"""
Transcribe a lecture audio file using OpenAI Whisper (local, MPS/GPU).

Course and lecture number are inferred automatically from the file path:
  courses/{course}/raw/audio/{lecture}/L{XX}_*.mp3

Usage (run from repository root with venv active):
    source .venv/bin/activate
    python scripts/transcript/transcribe.py <audio_path> [--model large-v3]

Example:
    python scripts/transcript/transcribe.py \
        "courses/example-course/raw/audio/L01/L01_guidance-audio.mp3"
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent


def parse_args():
    parser = argparse.ArgumentParser(description="Transcribe lecture audio with Whisper")
    parser.add_argument("audio_path", help="Path to the audio file (under raw/audio/)")
    parser.add_argument(
        "--model",
        default="large-v3",
        help="Whisper model name (default: large-v3)",
    )
    parser.add_argument(
        "--prompt-terms",
        default="",
        help="Comma-separated terms for initial_prompt bias (e.g. '専門用語1,専門用語2')",
    )
    return parser.parse_args()


def resolve_paths(audio_path: Path):
    """Infer course and lecture from the file path, return output paths."""
    # Expected: courses/{course}/raw/audio/{lecture}/L{XX}_*.ext
    parts = audio_path.parts
    try:
        courses_idx = parts.index("courses")
        course = parts[courses_idx + 1]
        lecture = audio_path.stem.split("_")[0]  # e.g. "L01"
    except (ValueError, IndexError):
        logging.error(
            "Cannot infer course/lecture from path.\n"
            "Expected: courses/{course}/raw/audio/{lecture}/L{XX}_*.ext"
        )
        sys.exit(1)

    course_dir = REPO_ROOT / "courses" / course
    transcript_dir = course_dir / "converted" / "transcript_raw"
    log_dir = course_dir / "converted" / "logs"
    transcript_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    stem = audio_path.stem
    return {
        "course": course,
        "lecture": lecture,
        "transcript": transcript_dir / f"{stem}_transcript_raw.md",
        "log": log_dir / f"{stem}_transcribe.log",
    }


def build_initial_prompt(prompt_terms_arg: str, course: str) -> str:
    """Build initial_prompt from --prompt-terms arg or courses/{course}/docs/prompt-terms.txt."""
    if prompt_terms_arg:
        return prompt_terms_arg.replace(",", "、")

    terms_file = REPO_ROOT / "courses" / course / "docs" / "prompt-terms.txt"
    if not terms_file.exists():
        return ""

    terms = []
    for line in terms_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            terms.append(line)

    if terms:
        logging.info(f"Loaded {len(terms)} prompt terms from {terms_file.relative_to(REPO_ROOT)}")
        return "、".join(terms)
    return ""


def select_device():
    try:
        import torch
        if torch.backends.mps.is_available():
            logging.info("Device: MPS (Apple Silicon GPU)")
            return "mps"
        logging.info("Device: CPU (MPS not available)")
        return "cpu"
    except ImportError:
        logging.info("Device: CPU (torch not found)")
        return "cpu"


def transcribe(audio_path: Path, model_name: str, device: str, initial_prompt: str = ""):
    try:
        import whisper
    except ImportError:
        logging.error("openai-whisper is not installed. Run: pip install openai-whisper")
        sys.exit(1)

    logging.info(f"Loading model: {model_name}")
    model = whisper.load_model(model_name, device=device)

    logging.info(f"Transcribing: {audio_path.name}")
    kwargs = {"language": "ja", "verbose": False}
    if initial_prompt:
        kwargs["initial_prompt"] = initial_prompt
        logging.info(f"initial_prompt: {initial_prompt}")
    result = model.transcribe(str(audio_path), **kwargs)
    return result


def write_transcript(path: Path, result: dict, audio_path: Path, paths: dict):
    segments = result.get("segments", [])
    lines = [
        f"# Transcript: {paths['lecture']} — {audio_path.stem}",
        f"",
        f"- source: `{audio_path}`",
        f"- transcribed_at: {datetime.now().isoformat()}",
        f"- language: {result.get('language', 'ja')}",
        f"",
        f"---",
        f"",
    ]
    for seg in segments:
        start = _fmt_time(seg["start"])
        end = _fmt_time(seg["end"])
        text = seg["text"].strip()
        lines.append(f"[{start} → {end}] {text}")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def _fmt_time(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def write_log(log_path: Path, audio_path: Path, transcript_path: Path, success: bool, error: str = ""):
    log_path.write_text(
        f"timestamp: {datetime.now().isoformat()}\n"
        f"source: {audio_path}\n"
        f"transcript_output: {transcript_path}\n"
        f"status: {'success' if success else 'error'}\n"
        + (f"error: {error}\n" if error else ""),
        encoding="utf-8",
    )


def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = parse_args()

    audio_path = Path(args.audio_path).resolve()
    if not audio_path.exists():
        logging.error(f"Audio file not found: {audio_path}")
        sys.exit(1)

    paths = resolve_paths(audio_path)
    logging.info(f"Course  : {paths['course']}")
    logging.info(f"Lecture : {paths['lecture']}")
    logging.info(f"Output  : {paths['transcript']}")

    device = select_device()

    initial_prompt = build_initial_prompt(args.prompt_terms, paths["course"])

    try:
        result = transcribe(audio_path, args.model, device, initial_prompt=initial_prompt)
        write_transcript(paths["transcript"], result, audio_path, paths)
        write_log(paths["log"], audio_path, paths["transcript"], success=True)
        logging.info("Done.")
    except Exception as e:
        write_log(paths["log"], audio_path, paths["transcript"], success=False, error=str(e))
        logging.error(f"Transcription failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
