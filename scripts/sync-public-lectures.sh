#!/bin/bash
# example-course の整形ノート（claude/lectures/）を public リポへ同期する。
#
# 方式: 毎回 public リポを clone し直し、lectures/*.md を rsync --delete で
#       ミラーリング → README の講義一覧を自動再生成 → 差分があれば commit & push。
#       ローカルに永続クローンを持たないので状態ズレが起きにくい。
#
# Usage: bash scripts/sync-public-lectures.sh [--dry-run]
#   --dry-run  push せず差分だけ表示

set -euo pipefail

# === 設定 ===
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$REPO_ROOT/courses/example-course/claude/lectures"
PUBLIC_REPO="https://github.com/<your-account>/<your-public-notes-repo>.git"
COURSE_TITLE="example-course"
COURSE_SUBTITLE="○○大学「example-course」（担当: ○○、20XX年度前期）"

DRY_RUN=0
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1

# === 前提チェック ===
[ -d "$SRC" ] || { echo "ERROR: ノート元ディレクトリが無い: $SRC"; exit 1; }
command -v gh >/dev/null || { echo "ERROR: gh CLI が必要"; exit 1; }
command -v rsync >/dev/null || { echo "ERROR: rsync が必要"; exit 1; }

# 機密スキャン（安全弁）: 該当があれば中断
if grep -rInE "token|password|secret|gho_|ghp_|@gmail\.com" "$SRC" >/dev/null 2>&1; then
  echo "ERROR: ノートに機密らしき文字列を検出。公開を中断。下記を確認:"
  grep -rInE "token|password|secret|gho_|ghp_|@gmail\.com" "$SRC"
  exit 1
fi

# === 作業用に public リポを clone ===
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
echo "→ clone $PUBLIC_REPO"
git clone -q "$PUBLIC_REPO" "$WORK/repo"
cd "$WORK/repo"

# === lectures をミラー（削除も反映） ===
mkdir -p lectures
rsync -a --delete --include='*.md' --include='.gitkeep' --exclude='*' "$SRC/" lectures/

# === README の講義一覧を自動生成 ===
# 各ノート先頭の "# L0X タイトル" 見出しから回番号とタイトルを抽出（STATUS.md 除外）
build_table() {
  for f in $(ls lectures/L*.md 2>/dev/null | sort); do
    head=$(grep -m1 '^# ' "$f" | sed 's/^# *//')
    num=$(echo "$head" | grep -oE '^L[0-9]+' || true)
    title=$(echo "$head" | sed -E 's/^L[0-9]+ *//')
    [ -n "$num" ] && printf '| %s | %s |\n' "$num" "$title"
  done
}

cat > README.md <<EOF
# ${COURSE_TITLE} — 講義ノート

${COURSE_SUBTITLE}の整形講義ノート。

配布資料と文字起こしをもとに作成した個人の学習ノート。

## ノート一覧

| 回 | タイトル |
|---|---|
$(build_table)

> 進捗は [lectures/STATUS.md](./lectures/STATUS.md) を参照。

## 注意

- 個人の学習用ノートであり、内容の正確性は保証しない。
- 一部に \`[[...]]\` 形式の内部リンクが残るが、ノート間の参照メモであり外部では解決されない。
EOF

# === 差分確認 ===
git add -A
if git diff --cached --quiet; then
  echo "✓ 差分なし。同期済み。"
  exit 0
fi

echo "=== 同期される差分 ==="
git diff --cached --stat

if [ "$DRY_RUN" = "1" ]; then
  echo "(--dry-run のため push しません)"
  exit 0
fi

git commit -q -m "sync: example-course 講義ノート更新 ($(git diff --cached --name-only | wc -l | tr -d ' ') files)"
git push -q origin HEAD
echo "✓ push 完了: $PUBLIC_REPO"
