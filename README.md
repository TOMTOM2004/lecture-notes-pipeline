# lecture-notes-pipeline

大学授業の録音・配布 PDF から整形ノートを生成するパイプラインの基盤一式。

授業データを raw（原本・不可侵）/ converted（機械変換＋穴埋め清書）/ claude（余談込み完成ノート）の3層で管理し、PDF 変換 → 文字起こし → Claude Code による整形をスクリプトとスキルで回す。

実際の授業データ（PDF・録音・ノート本文）は含まない。`courses/example-course/` はディレクトリ構造のサンプル。

## 目的

- 授業理解の蓄積
- 試験対策
- 知識の横断的整理
- 将来的な再利用

## 解説記事

この基盤の設計判断は Zenn に書いている:

- [授業ノートを raw / converted / claude の3層に分けた理由](https://zenn.dev/) <!-- 公開後に URL 差し替え -->
- [家の Windows PC を定時起動の AI ワーカーにして、授業ノートの生成を完全自動化した](https://zenn.dev/) <!-- 公開後に URL 差し替え -->
- [並列化したら文字起こしが3倍遅くなった話 — Whisper × Apple Silicon (MPS) の実測](https://zenn.dev/)

---

## セットアップ

### 1. Java の確認

```bash
java -version
```

未インストールの場合:

```bash
brew install openjdk
echo 'export PATH="/opt/homebrew/opt/openjdk/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### 2. Python 仮想環境の作成とパッケージのインストール

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Claude Code スキルのインストール

```bash
bash scripts/install-skills.sh
```

インストール後、Claude Code を再起動してスキルを有効化する。

---

## 使い方

### 1回分の講義を処理する（通常フロー）

**① raw にファイルを置く**

PDF は `L{回番号}_` プレフィックスを付けてリネームして配置する。

```
courses/{授業}/raw/handouts/pdf/L07_slides.pdf
courses/{授業}/raw/handouts/pdf/L07_handout.pdf
```

音声は回別サブフォルダに配置する。

```
courses/{授業}/raw/audio/L07/L07_lecture.m4a
```

**② PDF を変換する**

```bash
source .venv/bin/activate
python scripts/pdf/convert-pdf.py <course> <lecture> <pdf_path>
```

例:

```bash
python scripts/pdf/convert-pdf.py \
  example-course \
  L07 \
  "courses/example-course/raw/handouts/pdf/L07_slides.pdf"
```

→ `converted/pdf_md/` と `converted/pdf_json/` に出力される。

**③ Claude Code でノートを整形する**

```
/process-lecture example-course L07
```

PDF のみの場合（`/pdf-normalize` は表構造の自動修正も含む）:

```
/pdf-normalize example-course L07
```

→ `claude/lectures/L07_*.md` に完成版が生成される。

**④ 音声を文字起こしする（授業後）**

```bash
source .venv/bin/activate
python scripts/transcript/transcribe.py \
  "courses/example-course/raw/audio/L07/L07_lecture.m4a"
```

→ `converted/transcript_raw/L07_lecture_transcript_raw.md` に出力される。

授業用語リストが `courses/{授業}/docs/prompt-terms.txt` にあれば自動で読み込まれる（`--prompt-terms` の手打ち不要）。

**⑤ 文字起こしを校正する**

```
/correct-transcript example-course L07
```

→ `converted/transcript_corrected/L07_lecture_transcript_corrected.md` に出力される。
`scripts/transcript/corrections.json` の既知誤認識パターンを適用後、PDF資料を参照して同音異義語を修正する。

**⑥ ノートの空欄・補足を更新する**

`/process-lecture` または手動で `claude/lectures/L07_*.md` の空欄を補完する。
文字起こしは `transcript_corrected/` を参照する（`transcript_raw/` は直接使わない）。

**⑦ STATUS.md は自動更新される**

各スキル（`/correct-transcript`・`/pdf-normalize`・`/process-lecture`）の実行後に
`courses/{授業}/claude/lectures/STATUS.md` が自動的に更新される。

---

### 用語集を作る

```
/glossary-builder example-course L01-L07
```

→ `claude/glossary/` または `shared/glossary/` にエントリが生成される。

---

### 試験前の復習ノートを作る

```
/make-review example-course L01-L07 中間
```

→ `claude/reviews/L01-L07_中間.md` に復習ノートが生成される。

---

### 新授業を追加する

```bash
bash scripts/new-course.sh <course-directory-name> "<授業名>"
```

例:

```bash
bash scripts/new-course.sh another-course "Another Course"
```

---

## ディレクトリ構造

```
lecture-notes-pipeline/
├─ courses/               # 授業ごとのデータ
│  └─ {course}/
│     ├─ raw/             # 原本（編集禁止）
│     ├─ converted/       # 機械変換結果（原則編集禁止）
│     └─ claude/          # Claude整形後の作業層（編集可）
│        └─ lectures/STATUS.md  # 処理進捗管理
├─ shared/                # 複数授業横断リソース
├─ .claude/SKILLS/        # Claude Code スキル
├─ scripts/               # 共通スクリプト
├─ prompts/               # 共通プロンプト
├─ templates/             # ノートテンプレート
└─ docs/                  # リポジトリ設計書
```

## 基本ルール

- `raw/` は編集しない
- `converted/` は原則編集しない
- `claude/` は人間編集可
- 音声ファイルはGit管理外（ローカル保持のみ）

詳細は `docs/conventions.md` を参照。
