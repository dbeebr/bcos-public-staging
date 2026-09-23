#!/bin/sh
# Plus-only validator addition: a work item that declares `implements_gate:`
# must reference a human-gates/ file whose gate_status is `accepted`.
# Answers a failure mode observed repeatedly in an operating Cell
# (implementation landed before its gate was accepted) as a hard check, not prose.
set -eu

CELL_DIR="${1:-.}"
cd "$CELL_DIR"

FAIL=0

for f in work/*.md; do
  [ -f "$f" ] || continue
  GATE_ID=$(grep -m1 '^implements_gate:' "$f" 2>/dev/null | sed 's/^implements_gate: *//' | tr -d '"' || true)
  [ -n "$GATE_ID" ] || continue
  GATE_FILE=$(grep -rl "^id: $GATE_ID\$" human-gates 2>/dev/null | head -1 || true)
  if [ -z "$GATE_FILE" ]; then
    echo "BLOCK $f declares implements_gate: $GATE_ID but no human-gates/ file has that id"
    FAIL=1
    continue
  fi
  STATUS=$(grep -m1 '^gate_status:' "$GATE_FILE" | sed 's/^gate_status: *//' || true)
  if [ "$STATUS" != "accepted" ]; then
    echo "BLOCK $f implements gate $GATE_ID which is gate_status: ${STATUS:-<missing>} (must be accepted)"
    FAIL=1
  fi
done

if [ "$FAIL" -eq 0 ]; then
  echo "validate-cell-plus: passed (0 gate-before-acceptance violations)"
fi
exit "$FAIL"
