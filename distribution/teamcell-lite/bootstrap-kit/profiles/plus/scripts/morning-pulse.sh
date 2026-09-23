#!/bin/sh
# Teamcell Plus Morning Pulse — bounded observer, manual-trigger-first.
# Non-authority: read-only over committed state; never mutates work/human-gates;
# never decides priority; recurring schedule stays behind a Human Gate (MD-6).
set -eu

usage() {
  cat >&2 <<'USAGE'
Usage: morning-pulse.sh --repo OWNER/NAME [--recipient HANDLE]... [--dry-run] [--force]

Reads work/, human-gates/, and recent commits from the LOCAL checkout of the
target Cell (run this from inside that repo, or pass --cell-dir). Publishes
a "Changed / Needs attention / Today / Continue here" digest as a GitHub
Issue (labels: cell-update, morning-pulse) if and only if the computed
pulse-id differs from every open morning-pulse issue's pulse-id (idempotent,
deduplicated). --force bypasses the dedup check for testing.
USAGE
  exit 2
}

REPO=""
CELL_DIR="."
DRY_RUN=0
FORCE=0
RECIPIENTS=""

while [ $# -gt 0 ]; do
  case "$1" in
    --repo) REPO="$2"; shift 2 ;;
    --cell-dir) CELL_DIR="$2"; shift 2 ;;
    --recipient) RECIPIENTS="$RECIPIENTS @$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --force) FORCE=1; shift ;;
    --help|-h) usage ;;
    *) echo "unknown arg: $1" >&2; usage ;;
  esac
done

[ -n "$REPO" ] || { echo "missing --repo" >&2; usage; }

cd "$CELL_DIR"

OPEN_WORK=$(find work -maxdepth 1 -name '*.md' -newer /dev/null 2>/dev/null | sort || true)
OPEN_GATES=$(grep -rl 'gate_status: *open' human-gates 2>/dev/null | sort || true)
RECENT_SHAS=$(git log -5 --format=%H 2>/dev/null || true)

FINGERPRINT_SRC=$(printf '%s\n%s\n%s\n' "$OPEN_WORK" "$OPEN_GATES" "$RECENT_SHAS")
PULSE_ID=$(printf '%s' "$FINGERPRINT_SRC" | shasum -a 256 2>/dev/null | cut -d' ' -f1 || printf '%s' "$FINGERPRINT_SRC" | sha256sum | cut -d' ' -f1)

if [ "$FORCE" -ne 1 ]; then
  EXISTING=$(gh issue list --repo "$REPO" --label morning-pulse --state open --json body \
    --jq ".[] | select(.body | contains(\"pulse-id: $PULSE_ID\")) | .body" 2>/dev/null || true)
  if [ -n "$EXISTING" ]; then
    echo "no change since pulse-id $PULSE_ID (deduplicated, no publish)"
    exit 0
  fi
fi

BODY=$(mktemp)
trap 'rm -f "$BODY"' EXIT
{
  echo "## Changed"
  if [ -n "$RECENT_SHAS" ]; then
    git log -5 --format='- %h %s (%an, %ad)' --date=short
  else
    echo "- (no recent commits found)"
  fi
  echo
  echo "## Needs attention"
  if [ -n "$OPEN_GATES" ]; then
    for f in $OPEN_GATES; do echo "- $f"; done
  else
    echo "- no open Human Gates"
  fi
  echo
  echo "## Today"
  if [ -n "$OPEN_WORK" ]; then
    for f in $OPEN_WORK; do echo "- $f"; done
  else
    echo "- no open work items found"
  fi
  echo
  echo "## Continue here"
  echo "- see the items above; this pulse does not set priority"
  echo
  if [ -n "$RECIPIENTS" ]; then
    echo "---"
    echo "Direct attention:$RECIPIENTS"
  fi
  echo
  echo "---"
  echo "_Non-canonical summary — source links above are the truth. pulse-id: ${PULSE_ID}_"
} > "$BODY"

gh label create morning-pulse --repo "$REPO" --color 5319E7 \
  --description "Teamcell Plus Morning Pulse" >/dev/null 2>&1 || true
gh label create cell-update --repo "$REPO" --color 0E8A16 \
  --description "Teamcell Plus Cell Update" >/dev/null 2>&1 || true

if [ "$DRY_RUN" -eq 1 ]; then
  echo "[dry-run] would create morning-pulse issue in $REPO, pulse-id $PULSE_ID"
  sed 's/^/  /' "$BODY"
  exit 0
fi

gh issue create --repo "$REPO" --title "Morning Pulse — $(date +%Y-%m-%d)" \
  --body-file "$BODY" --label cell-update --label morning-pulse
