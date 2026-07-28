---
name: course-status
description: 全授業の講義処理状態を横断集計してダッシュボード形式で表示する。各授業のSTATUS.mdを読み込み、進捗・ボトルネック・次のアクションを一画面で把握できる。「進捗どう？」「ダッシュボード見せて」「全授業の状態を教えて」「どこまで進んでる？」などと言われたら使う。
---

## 使い方

```
/course-status
```

引数不要。`courses/*/claude/lectures/STATUS.md` をすべて読んで集計する。

オプション: `--save` を付けると `shared/status-dashboard.md` にも保存する（デフォルトは表示のみ）。

## 処理手順

### 1. 全授業のSTATUS.mdを収集

`courses/*/claude/lectures/STATUS.md` をGlobで列挙し、それぞれ読み込む。

### 2. 各授業のテーブルをパース

各STATUS.mdから以下を抽出:
- 授業名（ファイルパスのディレクトリ名）
- 全講義行の `raw` / `converted` / `claude` 列の状態（✅ / 🔄 / -）
- タイトル・備考

### 3. 集計値の計算

各授業について:
- **総講義数**（通常15、L00含む場合は16）
- **raw 完了数**（✅の数）
- **converted 完了数**（✅の数）
- **claude 完了数**（✅の数）
- **進捗率**（claude✅数 ÷ 総講義数 × 100）
- **ボトルネック**: raw > converted > claude の差から、どのフェーズで詰まっているかを特定
- **次のアクション候補**: 各フェーズで最も進んでいない次の講義（例: `L03 PDF変換待ち`）

### 4. ダッシュボード出力

以下の構成で整形出力する:

```markdown
# 📊 全授業 進捗ダッシュボード

最終集計日時: {YYYY-MM-DD HH:MM}

## サマリー

| 授業 | 進捗 | raw | converted | claude | ボトルネック | 次のアクション |
|---|---|---|---|---|---|---|
| {course1} | {progress_bar} {percentage}% | {n}/{total} | {n}/{total} | {n}/{total} | {stage} | {next_action} |
| {course2} | ... | | | | | |

## 授業別詳細

### {course1}

**進捗**: {claude_done}/{total} 回完了（{percentage}%）

| 状態 | 講義 |
|---|---|
| ✅ 完了（claude ✅） | {list of lectures} |
| 🔄 進行中（raw/converted のみ） | {list} |
| - 未着手 | {list} |

**備考ハイライト**: {notes with 推論 / 穴埋め / 再録 etc. があれば列挙}

### {course2}
...
```

### 5. 次のアクション推奨

各授業について以下のルールで「次のアクション」を決定する:

| 状況 | 推奨アクション |
|---|---|
| 最新回でraw✅ あり、converted `-` | `L{NUM} PDF変換待ち` （`scripts/pdf/convert-pdf.py` 実行を促す） |
| converted✅ あり、claude `-` | `L{NUM} ノート生成待ち` （`/process-lecture` or `/pdf-normalize`） |
| 全講義 `-` | `L01から開始可能` |
| 全講義 claude✅ | `✨ 全回完了` |

### 6. 進捗バー表示

`{progress_bar}` は UTF-8 のブロック文字で表示する:
- `████████░░` のような形式（10セグメント）
- 10% = ▒、20% = ██ のように塗る

例: 20% → `██░░░░░░░░`、60% → `██████░░░░`、100% → `██████████`

### 7. `--save` オプション対応

引数に `--save` が含まれていれば、生成したダッシュボードを `shared/status-dashboard.md` にも書き出す。
ファイル先頭に以下のメタ情報を付ける:

```markdown
<!-- generated_at: {ISO日時} -->
<!-- source: /course-status skill -->
```

## 注意事項

- STATUS.mdが存在しない授業ディレクトリはスキップする（警告を表示）
- L00を含む授業と含まない授業があるので、パース時は行頭に `| L` で始まる行を柔軟に拾う
- 進捗率の計算は claude 列の ✅ 数を基準とする（最終成果物の完成度）
- ボトルネックの判定: 例えば raw=5, converted=3, claude=1 なら「claude フェーズがボトルネック」
- 絵文字（📊 ✨ 🔄 ⚠️ 等）は積極的に使って視認性を上げる
- 単一授業のみ見たい場合（引数で授業名を受け取る）は将来拡張とし、現時点では全授業固定
