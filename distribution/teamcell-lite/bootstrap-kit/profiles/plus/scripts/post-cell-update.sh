#!/bin/sh
# Publish a Teamcell Plus Cell Update as a GitHub Issue.
# Layer-1 canonical interaction per TEAMCELL-PLUS-OPERATING-MODEL-AND-ENGAGEMENT-20260712.md.
set -eu

usage() {
  cat >&2 <<'USAGE'
Usage: post-cell-update.sh --repo OWNER/NAME --title TEXT --body-file FILE [--mention HANDLE]... [--dry-run]

Publishes a GitHub Issue labeled "cell-update" (created if missing) via `gh`.
Each --mention adds an explicit @HANDLE line to the body so the mentioned
account receives a real GitHub notification (proof requirement — configured
watching alone is not sufficient proof of delivery).
USAGE
  exit 2
}

REPO=""
TITLE=""
BODY_FILE=""
DRY_RUN=0
MENTIONS=""

while [ $# -gt 0 ]; do
  case "$1" in
    --repo) REPO="$2"; shift 2 ;;
    --title) TITLE="$2"; shift 2 ;;
    --body-file) BODY_FILE="$2"; shift 2 ;;
    --mention) MENTIONS="$MENTIONS @$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --help|-h) usage ;;
    *) echo "unknown arg: $1" >&2; usage ;;
  esac
done

[ -n "$REPO" ] || { echo "missing --repo" >&2; usage; }
[ -n "$TITLE" ] || { echo "missing --title" >&2; usage; }
[ -n "$BODY_FILE" ] && [ -f "$BODY_FILE" ] || { echo "missing/unreadable --body-file" >&2; usage; }

TMP_BODY=$(mktemp)
trap 'rm -f "$TMP_BODY"' EXIT
cat "$BODY_FILE" > "$TMP_BODY"
if [ -n "$MENTIONS" ]; then
  printf '\n\n---\nDirect attention:%s\n' "$MENTIONS" >> "$TMP_BODY"
fi

# Ensure the label exists (idempotent — gh label create fails harmlessly if present).
gh label create cell-update --repo "$REPO" --color 0E8A16 \
  --description "Teamcell Plus Cell Update" >/dev/null 2>&1 || true

if [ "$DRY_RUN" -eq 1 ]; then
  echo "[dry-run] would create issue in $REPO"
  echo "  title: $TITLE"
  echo "  labels: cell-update"
  echo "  body:"
  sed 's/^/    /' "$TMP_BODY"
  exit 0
fi

gh issue create --repo "$REPO" --title "$TITLE" --body-file "$TMP_BODY" --label cell-update
