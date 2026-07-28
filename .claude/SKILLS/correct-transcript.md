---
name: correct-transcript
description: 音声文字起こし（transcript_raw）の同音異義語誤認識をPDF資料を参照して校正し、transcript_corrected に保存する
---

## 使い方

```
/correct-transcript
```

対象授業と講義番号を指定してください（例: `example-course L02`）。

## 処理手順

1. `scripts/transcript/corrections.json` を読み込む
   - `_comment` キーは無視する
   - key=誤認識テキスト、value=正しいテキストのペアを把握する

2. `courses/{course}/converted/transcript_raw/` から `L{NUM}` で始まるファイルをすべて読み込む

3. `courses/{course}/converted/pdf_md/` から `L{NUM}_*.md` をすべて読み込む（校正の参照資料）

4. 以下の優先順位で校正する:
   - **優先1**: `corrections.json` に登録済みのパターンを機械的に置換する
   - **優先2**: PDF資料に記載されている正しい語句を参照し、同音異義語・誤認識を修正する
   - 判断できない箇所は修正せずそのまま残す

5. **変更してはいけないもの**:
   - タイムスタンプ行（`[00:00 → 00:09]` の形式）
   - Markdownのメタ情報行（`#`, `-`, `---` で始まる行）
   - 意味・構造（誤認識の修正のみ行う）

6. 校正済みテキストを `courses/{course}/converted/transcript_corrected/` に保存する
   - ファイル名: 元ファイルの `_transcript_raw` を `_transcript_corrected` に置換
   - 例: `L02_lecture-audio_transcript_raw.md` → `L02_lecture-audio_transcript_corrected.md`
   - ファイル先頭に以下のメタ情報を追加する:
     ```
     <!-- corrected_at: {ISO日時} -->
     <!-- source: {元ファイルパス} -->
     ```

7. `courses/{course}/claude/lectures/STATUS.md` の該当行を更新する
   - `converted` 列を ✅ にする（transcript_corrected が生成されたため）
   - タイトルが空欄なら pdf_md の内容から補完する

## 注意事項

- `converted/` の元ファイル（`transcript_raw/`）は上書きしない
- 出力先にすでにファイルがある場合は上書き前に確認する
- 校正後、主な変更点（何箇所修正したか・主な置換内容）を簡潔に報告する
