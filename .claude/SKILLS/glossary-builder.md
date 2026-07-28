---
name: glossary-builder
description: 講義ノートから専門用語を抽出してglossaryエントリを生成する
---

## 使い方

```
/glossary-builder
```

対象授業と講義番号（または範囲）を指定してください（例: `example-course L01-L07`）。

## 処理手順

1. 対象講義ノートの `## 重要用語` セクションを収集する
2. 既存の glossary エントリと重複確認する
3. 新規用語について `templates/glossary-entry.md` 形式でエントリを生成する
4. 授業固有の用語 → `courses/{course}/claude/glossary/{term}.md`
5. 複数授業で登場する用語 → `shared/glossary/{term}.md`

## 注意事項

- 既存エントリを上書きしない（追記のみ）
- 英語・日本語両表記を必ず含める
- ファイル名は小文字ケバブケース（例: `adverse-selection.md`）
