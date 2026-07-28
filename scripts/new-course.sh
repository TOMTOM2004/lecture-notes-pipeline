#!/bin/bash
# Add a new course to the repository
# Usage: bash scripts/new-course.sh <course-directory-name> "<授業名>"
# Example: bash scripts/new-course.sh another-course "Another Course"

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [ -z "$1" ]; then
  echo "Usage: bash scripts/new-course.sh <course-directory-name> \"<授業名>\""
  echo "Example: bash scripts/new-course.sh another-course \"another-course\""
  exit 1
fi

COURSE="$1"
COURSE_NAME="${2:-$1}"
COURSE_DIR="$REPO_ROOT/courses/$COURSE"

if [ -d "$COURSE_DIR" ]; then
  echo "Error: $COURSE_DIR already exists"
  exit 1
fi

echo "Creating course: $COURSE ($COURSE_NAME)"

mkdir -p \
  "$COURSE_DIR/docs" \
  "$COURSE_DIR/raw/handouts/pdf" \
  "$COURSE_DIR/raw/audio" \
  "$COURSE_DIR/raw/syllabus" \
  "$COURSE_DIR/converted/pdf_md" \
  "$COURSE_DIR/converted/pdf_json" \
  "$COURSE_DIR/raw/assignments/pdf" \
  "$COURSE_DIR/converted/transcript_raw" \
  "$COURSE_DIR/converted/transcript_corrected" \
  "$COURSE_DIR/converted/logs" \
  "$COURSE_DIR/claude/lectures" \
  "$COURSE_DIR/claude/glossary" \
  "$COURSE_DIR/claude/reviews" \
  "$COURSE_DIR/claude/references" \
  "$COURSE_DIR/claude/scratch"

# .gitkeep for empty directories
find "$COURSE_DIR" -type d | while read d; do touch "$d/.gitkeep"; done

# STATUS.md
cat > "$COURSE_DIR/claude/lectures/STATUS.md" <<EOF
# 講義処理状態 — $COURSE_NAME

凡例: ✅ 完了 / 🔄 処理中 / - 未着手

| 回 | タイトル | raw | converted | claude | 備考 |
|---|---|:---:|:---:|:---:|---|
| L01 | | - | - | - | |
| L02 | | - | - | - | |
| L03 | | - | - | - | |
| L04 | | - | - | - | |
| L05 | | - | - | - | |
| L06 | | - | - | - | |
| L07 | | - | - | - | |
| L08 | | - | - | - | |
| L09 | | - | - | - | |
| L10 | | - | - | - | |
| L11 | | - | - | - | |
| L12 | | - | - | - | |
| L13 | | - | - | - | |
| L14 | | - | - | - | |
| L15 | | - | - | - | |
EOF

# course-info.md
cat > "$COURSE_DIR/docs/course-info.md" <<EOF
# $COURSE_NAME

## 基本情報

- **授業名**: $COURSE_NAME
- **担当教員**:
- **開講学期**:
- **単位数**:
- **教室**:

## 概要

## 評価方法

## 参考文献

## メモ
EOF

echo ""
echo "Created: courses/$COURSE/"
echo "Next steps:"
echo "  1. courses/$COURSE/docs/course-info.md を編集する"
echo "  2. raw/syllabus/ にシラバスを置く"
echo "  3. git add courses/$COURSE/ && git commit -m \"add: $COURSE_NAME\""
