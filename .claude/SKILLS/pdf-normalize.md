---
name: pdf-normalize
description: PDF変換済みMarkdownの構造崩れを修正し、講義ノート形式に整形する（PDFのみ・transcript なしの場合に使う）。スライドPDFの場合は図の判別・テキスト化も行う。
---

## 使い方

```
/pdf-normalize
```

対象授業と講義番号を指定してください（例: `example-course L01`）。

## 処理手順

### 変換直後の構造整形 + Phase 0-1: PDF種別判定 → 画像処理

→ **`_pdf-common-phases.md`** に従う（「変換直後: converted/pdf_md の構造整形」→ Phase 0 → Phase 1 の順）

### Phase 2: 構造の整形

1. `courses/{course}/converted/pdf_json/L{NUM}_*.json` も読み込む
2. **表を修正する**: MD 内の表に画像参照（`![image N](...) ラベル`）や列ずれがある場合、
   JSON の body text をコンテキストに使いながら正しい Markdown 表に再構築する
   - 画像参照はラベルテキストだけに置き換える
   - 結合セルの階層構造を正しく復元する
   - 空欄（穴埋め）は `（ **** ）` 表記のまま残す
3. 見出し階層・ページ跨ぎの語分断を確認・修正する（→ `_pdf-common-phases.md`「変換直後の構造整形」の整形ルール。H1→H2→H3 の構造を保つ）
4. 箇条書きの崩れを修正する
5. `templates/lecture-note.md` のセクション構造に合わせて再構成する
6. `## 重要用語` セクションに専門用語を抽出する
7. `courses/{course}/claude/lectures/L{NUM}_*.md` に保存する
8. `courses/{course}/claude/lectures/STATUS.md` の該当行を更新する
   - `claude` 列を ✅ にする
   - タイトルが空欄なら pdf_md の内容から補完する

> **バッチ処理（Claude Code を使わずスクリプト単体で実行する場合）:**
> `ANTHROPIC_API_KEY` を設定したうえで
> `python scripts/pdf/table-normalize.py {course} {lecture}` を実行する

## 完了報告

スキル完了後、以下を簡潔に報告する:
- PDF種別（テキスト/スライド）
- 画像総数・分類内訳（残したconcept/theory/data数、削除したphoto/decorative数）
- 主なテキスト化した図のタイトル

## 注意事項

- `converted/` の元ファイルは上書きしない
- transcript もある場合は `/process-lecture` を使う
- `pdftoppm` が未インストールの場合は `brew install poppler` を案内する
