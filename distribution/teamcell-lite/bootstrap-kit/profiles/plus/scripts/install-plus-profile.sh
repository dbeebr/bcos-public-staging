#!/bin/sh
# Additive installer: copies the Plus overlay into an already Lite-installed Cell.
# Never rewrites a Lite baseline file except one append to CONTEXT_INDEX.md.
set -eu

usage() {
  printf 'Usage: %s TARGET_CELL_DIR | --print-targets\n' "$0" >&2
  printf '  --print-targets  list the Cell-relative files this installer creates, write nothing\n' >&2
  exit 2
}

# Regenerate the Cell's Procedure Index with the Cell's own renderer (a
# baseline file). Without python3 the validator reports the stale index
# instead; nothing is silently skipped.
refresh_procedure_index() {
  if [ -f "$1/scripts/render-instructions.py" ] && command -v python3 >/dev/null 2>&1; then
    python3 "$1/scripts/render-instructions.py" --root "$1" index --write
  else
    echo "NOTE: run 'python3 scripts/render-instructions.py index --write' in $1 to refresh its Procedure Index" >&2
  fi
}

[ $# -eq 1 ] || usage

if [ "$1" = "--print-targets" ]; then
  # Single source of truth for the installer preview: exactly the files the
  # copy below creates in a fresh Cell (CONTEXT_INDEX.md is appended, not
  # created).
  printf '%s\n' docs/CONTRACTS-V1.md ONBOARDING.md history/learning-candidates/README.md \
    scripts/morning-pulse.sh scripts/post-cell-update.sh scripts/validate-cell-plus.sh
  exit 0
fi

TARGET="$1"
[ -d "$TARGET" ] || { echo "target dir does not exist: $TARGET" >&2; exit 1; }
[ -f "$TARGET/CONTEXT_INDEX.md" ] || { echo "target is not a Lite-installed Cell (no CONTEXT_INDEX.md): $TARGET" >&2; exit 1; }

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PLUS_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)

mkdir -p "$TARGET/scripts" "$TARGET/docs" "$TARGET/history/learning-candidates"
cp "$PLUS_ROOT/scripts/post-cell-update.sh" "$TARGET/scripts/post-cell-update.sh"
cp "$PLUS_ROOT/scripts/morning-pulse.sh" "$TARGET/scripts/morning-pulse.sh"
cp "$PLUS_ROOT/scripts/validate-cell-plus.sh" "$TARGET/scripts/validate-cell-plus.sh"
chmod +x "$TARGET/scripts/post-cell-update.sh" "$TARGET/scripts/morning-pulse.sh" "$TARGET/scripts/validate-cell-plus.sh"
cp "$PLUS_ROOT/docs/CONTRACTS-V1.md" "$TARGET/docs/CONTRACTS-V1.md"
[ -f "$TARGET/ONBOARDING.md" ] || cp "$PLUS_ROOT/ONBOARDING.md.template" "$TARGET/ONBOARDING.md"
if [ ! -f "$TARGET/history/learning-candidates/README.md" ]; then
  created_date=$(date +%Y-%m-%d)
  cat > "$TARGET/history/learning-candidates/README.md" <<EOF
---
bcos_type: doc
kind: learning_candidates_readme
surface: history
id: LEARNING-CANDIDATES-README
title: "Learning Candidates"
status: active
created: $created_date
created_by: install-plus-profile
created_by_type: system
created_by_id: system:install-plus-profile
created_by_display: "Teamcell Plus installer"
created_by_github: null
on_behalf_of_human_id: null
agent_model: interactive-shell
procedure_kind: workflow
use_when: "Closing surfaced a reusable pattern or correction that is not yet an accepted procedure"
not_when: "One-off facts, or a pattern already accepted as a playbook (improve that playbook instead)"
phase: close
---

# Learning candidates

Non-canonical, local buffer (Plus contract \`LearningCandidate\`,
\`docs/CONTRACTS-V1.md\`). One file per candidate:
\`history/learning-candidates/<short-slug>.md\` with \`status\`, the pattern or
correction in plain words, the Git evidence (work item, commit SHA), and its
scope limit. Status progression:
candidate -> observed_once -> repeated -> ready_for_bcos_review.

At closing, update an existing candidate when the same pattern recurs
instead of adding a duplicate. Record the candidate path in the work item's
Completion Record under \`closing_learning\`.

No BCOS repository mutation may be triggered directly from an entry here —
a human decides to open a work item first. Nothing here is activated or
promoted automatically.
EOF
fi

MARKER="profiles/plus (installed $(date +%Y-%m-%d))"
if ! grep -q "$MARKER" "$TARGET/CONTEXT_INDEX.md" 2>/dev/null; then
  printf '\n## Teamcell Plus\n\n%s — see `docs/CONTRACTS-V1.md`, `ONBOARDING.md`, `scripts/post-cell-update.sh`, `scripts/morning-pulse.sh`, `scripts/validate-cell-plus.sh`.\n' "$MARKER" >> "$TARGET/CONTEXT_INDEX.md"
fi

# Keep the generated Procedure Index in CONTEXT_INDEX.md in step with the
# procedures this package added (the learning-candidates workflow).
refresh_procedure_index "$TARGET"

echo "Plus profile installed into $TARGET"
if grep -q '{{' "$TARGET/ONBOARDING.md" 2>/dev/null; then
  echo "REMINDER: $TARGET/ONBOARDING.md still has unfilled {{...}} placeholders" >&2
  echo "          and status: draft — fill them in and set status: active" >&2
  echo "          before onboarding anyone." >&2
fi
