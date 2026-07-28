---
name: process-lecture
description: 大学授業の配布資料（PDF変換済み）と音声文字起こしから完成版講義ノートを生成する。スライドPDFの場合は図の判別・テキスト化も行う。
---

## 使い方

```
/process-lecture
```

対象授業と講義番号を指定してください（例: `example-course L01`）。

## 処理手順

### 変換直後の構造整形 + Phase 0-1: PDF種別判定 → 画像処理

→ **`_pdf-common-phases.md`** に従う（「変換直後: converted/pdf_md の構造整形」→ Phase 0 → Phase 1 の順）

Phase 1 でテキスト化した図は、Phase 2 で構築する `## レジュメ要点` の関連する見出し直下に挿入する。

### Phase 2: PDF構造の整形

1. `courses/{course}/converted/pdf_json/L{NUM}_*.json` も読み込む（表構造のコンテキスト）
2. 見出し階層・ページ跨ぎの語分断・箇条書き・表の崩れを修正する（→ `_pdf-common-phases.md`「変換直後の構造整形」の整形ルール）。穴埋めは `（ **** ）` 表記のまま残す
3. `templates/lecture-note.md` のセクション構造に合わせて再構成する
4. `## 重要用語` セクションに専門用語を抽出する

### Phase 3: transcript の統合（transcript がある場合のみ）

5. `courses/{course}/converted/transcript_corrected/` に `L{NUM}_*_transcript_corrected.md` があればそれを読み込む。なければ `courses/{course}/converted/transcript_raw/L{NUM}_*.md` を読み込む
6. 口語表現・フィラーを除去し、レジュメに追加価値のある補足を抽出する
7. `## 授業での補足` セクションに統合する
8. `## 未理解点` を更新する
9. `courses/{course}/exam-info.md` が存在する場合、試験・テスト・単位・レポート課題に関する言及がないか transcript を確認する。あれば「講義中に出た試験ヒント（回別）」に追記、なければ「L{NUM}: 試験関連の言及なし（確認済み・日付）」を追記する

### Phase 4: 出力

10. `courses/{course}/claude/lectures/L{NUM}_*.md` に保存する
11. `courses/{course}/claude/lectures/STATUS.md` の該当行を更新する
    - `claude` 列を ✅ にする
    - タイトルが空欄なら pdf_md の内容から補完する
    - 備考欄に特記事項（推論補完あり・穴埋め残存あり等）があれば記入する

## 完了報告

スキル完了後、以下を簡潔に報告する:
- PDF種別（テキスト/スライド）
- 画像総数・分類内訳（残した concept/theory/data 数、削除した photo/decorative 数）
- 主なテキスト化した図のタイトル
- transcript から抽出した補足項目数

## 注意事項

- `converted/` の元ファイルは上書きしない
- 出力先に既存ファイルがある場合は上書き前に確認する
- transcript がない場合は Phase 3 をスキップする
- `pdftoppm` が未インストールの場合は `brew install poppler` を案内する
