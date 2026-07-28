# プロンプト: 用語抽出

## 用途

講義ノートから重要用語を抽出し、`templates/glossary-entry.md` 形式で出力する。

## プロンプト本文

```
以下の講義ノートから重要な専門用語を抽出し、glossaryエントリを生成してください。

【授業名】: {course}
【講義番号】: L{NUM}

【講義ノート】:
---
{lecture_note}
---

出力形式:
- `templates/glossary-entry.md` に従う
- ファイル名: 英語表記のケバブケース（例: adverse-selection.md）
- 日本語・英語両表記を必ず含める
- 既存glossaryと重複しそうな用語は末尾に「[要確認: 既存エントリあり可能性]」と付記する
```
