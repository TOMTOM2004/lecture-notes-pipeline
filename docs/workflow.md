# 処理ワークフロー

## 概要

```
raw/ ──→ converted/ ──→ claude/ ──→ 人間編集
原本       機械変換          Claude整形
（不変）   （再生成可能）    （作業層）
```

## ステップ別手順

### Step 1: 原本保存 → `raw/`

```
courses/{授業}/raw/handouts/pdf/L07_*.pdf
courses/{授業}/raw/audio/L07_*.m4a       ← Git管理外
courses/{授業}/raw/syllabus/syllabus.pdf ← 必要時のみ作成
```

- 配布レジュメPDFをそのままコピー
- 音声ファイルはローカル保持のみ（.gitignore）

### Step 2: PDF変換 → `converted/`

`scripts/pdf/convert-pdf.py` を使って変換する（OpenDataLoader PDF）。

```bash
python scripts/pdf/convert-pdf.py <course> <lecture> <pdf_path>
```

例:
```bash
python scripts/pdf/convert-pdf.py \
  example-course \
  L07 \
  "courses/example-course/raw/handouts/pdf/L07_slides.pdf"
```

1回のコマンドで以下が生成される:

**Markdown（`converted/pdf_md/`）:**
```
courses/{授業}/converted/pdf_md/L07_*.md
```

**JSON（`converted/pdf_json/`）— Claude API入力用:**
```
courses/{授業}/converted/pdf_json/L07_*.json
```
構造: `{ course, lecture, title, source_pdf, pages: [{ page, headings, body, tables }] }`

**変換ログ（`converted/logs/`）:**
```
courses/{授業}/converted/logs/L07_*_convert.log
```

初回セットアップ（Python・Java・pip install）は `docs/setup.md` を参照。

**文字起こし（対面授業 / Whisper）:**
```bash
python scripts/transcript/transcribe.py \
  courses/{授業}/raw/audio/L07/L07_lecture.m4a
```
→ `converted/transcript_raw/L07_*_transcript_raw.md` に出力される。
`courses/{授業}/docs/prompt-terms.txt` があれば自動で Whisper の initial_prompt に使用される。

**Whisper 文字起こし校正:**
```
/correct-transcript {授業} L07
```
→ `converted/transcript_corrected/L07_*_transcript_corrected.md` に出力される。
`scripts/transcript/corrections.json` の既知誤認識パターンを適用後、PDF資料を参照して校正する。

新たな誤認識を発見したら `corrections.json` に手動追記する（または Claude Code に口頭で依頼する）。

**文字起こし（オンライン授業 / NotebookLM）:**

1. NotebookLM でYouTube動画を文字起こしし、出力をコピーする
2. `converted/transcript_raw/L07_lecture_transcript_raw.md` として保存する
3. 以下で整形・補正する:
```
/normalize-notebooklm {授業} L07
```
→ `converted/transcript_corrected/L07_*_transcript_corrected.md` に出力される。
NotebookLMの前置き文を除去し、PDF資料を参照して専門用語を補正する。

### Step 3: Claude整形 → `claude/lectures/`

`/pdf-normalize`（PDF のみ）または `/process-lecture`（PDF + transcript）スキルを使って整形。

```
courses/{授業}/claude/lectures/L07_*.md
```

`templates/lecture-note.md` の構造に合わせた最終版を生成する。
transcript は `transcript_corrected/` を優先して参照する（なければ `transcript_raw/` にフォールバック）。
スキル実行後、STATUS.md が自動更新される。

### Step 4: 人間編集

`claude/` 配下のファイルを直接編集・追記。

- 授業中に取ったメモを追加
- 未理解点の解消を更新
- 用語集 `claude/glossary/` への反映

---

## スキルの使い方

`scripts/install-skills.sh` を実行すると、`.claude/SKILLS/` の内容が `~/.claude/skills/` にインストールされる。

```bash
bash scripts/install-skills.sh
```

利用可能になるスキル:

| スキル | 用途 |
|---|---|
| `/pdf-normalize` | PDF→MD整形（PDFのみ・transcript なし、スライドPDFの場合は図をテキスト化） |
| `/correct-transcript` | Whisper transcript_raw の同音異義語誤認識を校正 |
| `/normalize-notebooklm` | NotebookLM transcript_raw の前置き除去・専門用語補正・見出し統一 |
| `/process-lecture` | PDF + transcript から完成版ノートを生成 |
| `/glossary-builder` | 用語抽出・glossary エントリ生成 |
| `/make-review` | 複数回分のノートから復習ノートを生成 |

---

## 授業の追加

新授業を追加する際は scaffold スクリプトを実行する（STATUS.md・course-info.md も自動生成される）:

```bash
bash scripts/new-course.sh <course-directory-name> "<授業名>"
```
