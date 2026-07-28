# 環境セットアップ

## 必要な環境

| 要件 | バージョン | 備考 |
|---|---|---|
| Python | 3.10+ | |
| Java | 11+ | OpenDataLoader の動作要件 |
| pip | 最新推奨 | |

---

## 1. Java のインストール確認

```bash
java -version
```

Java 11 未満または未インストールの場合は Homebrew でインストールする:

```bash
brew install java
```

インストール後、`~/.zshrc` に以下を追記してシェルに反映させる:

```bash
export PATH="/opt/homebrew/opt/openjdk/bin:$PATH"
```

> `convert-pdf.py` はHomebrew版Javaのパスを自動解決するため、シェルの設定がなくても動作する。

---

## 2. Python 仮想環境の作成とパッケージのインストール

リポジトリルートで実行:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

インストール確認:

```bash
python -c "import opendataloader_pdf; print('OK')"
```

以降のコマンドは仮想環境を有効化した状態（`source .venv/bin/activate`）で実行する。

---

## 3. Claude Code スキルのインストール

```bash
bash scripts/install-skills.sh
```

インストール後、Claude Code を再起動してスキルを有効化する。

---

## PDF変換の実行

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

変換結果:
- `courses/{course}/converted/pdf_md/L07_*.md` — Markdown
- `courses/{course}/converted/pdf_json/L07_*.json` — JSON（Claude API入力用）
- `courses/{course}/converted/logs/L07_*_convert.log` — 変換ログ

---

## 表構造の修正（table-normalize）

PDF変換で崩れた表を Claude API で修正する。`/pdf-normalize` スキルの実行前に自動的に呼ばれる。

```bash
python scripts/pdf/table-normalize.py <course> <lecture>
```

例:

```bash
python scripts/pdf/table-normalize.py example-course L02
```

- `converted/pdf_md/{lecture}_*.md` を読み込み、Claude API で表を修正して上書き保存する
- 対応する `converted/pdf_json/` のファイルもコンテキストとして使用する

### 初回のみ: anthropic のインストールと API キー設定

```bash
pip install anthropic
```

API キーを環境変数に設定（`.zshrc` 等に追記推奨）:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

---

## 音声文字起こしの実行

```bash
python scripts/transcript/transcribe.py <audio_path>
```

例:

```bash
python scripts/transcript/transcribe.py \
  "courses/example-course/raw/audio/L01/L01_guidance-audio.mp3"
```

- course・lecture はファイルパスから自動解決される
- デフォルトモデル: `large-v3`（変更する場合は `--model medium` 等を指定）
- Apple Silicon GPU（MPS）を自動検出して使用、なければ CPU にフォールバック

出力:
- `courses/{course}/converted/transcript_raw/{stem}_transcript_raw.md` — タイムスタンプ付き文字起こし
- `courses/{course}/converted/logs/{stem}_transcribe.log` — 実行ログ

### 初回のみ: torch と openai-whisper のインストール

```bash
pip install torch openai-whisper
```

MPS の動作確認:

```bash
python -c "import torch; print('MPS:', torch.backends.mps.is_available())"
```

---

## 変換後の流れ

```
PDF変換完了
  ↓
/process-lecture {course} L07   # Claude Code でノート整形
  ↓
claude/lectures/L07_*.md 完成
  ↓
STATUS.md を更新
```
