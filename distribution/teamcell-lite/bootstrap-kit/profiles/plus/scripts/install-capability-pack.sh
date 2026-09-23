#!/bin/sh
# Additive, explicitly opt-in installer for the Team Capability Pack app.
# Never bundled into install-plus-profile.sh's default copy set -- a Cell
# operator must run this script by name to add this capability.
# Never rewrites a baseline file except one append to CONTEXT_INDEX.md.
set -eu

usage() {
  printf 'Usage: %s TARGET_CELL_DIR | --print-targets\n' "$0" >&2
  printf '  --print-targets  list the Cell-relative files this installer writes, write nothing\n' >&2
  exit 2
}

[ $# -eq 1 ] || usage

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PLUS_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
PACK_SRC="$PLUS_ROOT/apps/team-capability-pack"

if [ "$1" = "--print-targets" ]; then
  # Single source of truth for the installer preview: exactly the files the
  # copy below creates (CONTEXT_INDEX.md is appended, not created).
  (cd "$PACK_SRC" && find . -type f ! -path './onboarding/*' | sed 's#^\./#apps/team-capability-pack/#') | LC_ALL=C sort
  printf '%s\n' playbooks/onboarding/SKILL-PLAYGROUND.html
  exit 0
fi

TARGET="$1"
[ -d "$TARGET" ] || { echo "target dir does not exist: $TARGET" >&2; exit 1; }
[ -f "$TARGET/CONTEXT_INDEX.md" ] || { echo "target is not a Lite-installed Cell (no CONTEXT_INDEX.md): $TARGET" >&2; exit 1; }

[ -d "$PACK_SRC" ] || { echo "capability pack source not found: $PACK_SRC" >&2; exit 1; }

if [ -d "$TARGET/apps/team-capability-pack" ]; then
  echo "already installed: $TARGET/apps/team-capability-pack (no-op; remove it first to reinstall)" >&2
  exit 0
fi

mkdir -p "$TARGET/apps"
cp -R "$PACK_SRC" "$TARGET/apps/team-capability-pack"
rm -rf "$TARGET/apps/team-capability-pack/onboarding"

mkdir -p "$TARGET/playbooks/onboarding"
cp "$PACK_SRC/onboarding/SKILL-PLAYGROUND.html" "$TARGET/playbooks/onboarding/SKILL-PLAYGROUND.html"

# Resolve on_behalf_of_human_id from the target Cell's own governance file
# (self-contained -- no dependency on the installer/distribution checkout).
# Never leaves the raw human:{{CELL_OWNER_ID}} template token in an
# installed Cell; an unresolved
# owner becomes an explicit "human:unresolved", never a fallback name and
# never a bare {{...}} token (validate-cell.sh's apps/ placeholder check
# treats any {{...}} there as a hard failure).
gov_file="$TARGET/.bcos/CELL-GOVERNANCE.yaml"
owner_id='unresolved'
if [ -f "$gov_file" ]; then
  owner_role=$(sed -n 's/^cell_owner_role:[	 ]*//p' "$gov_file" | sed -n '1p' | sed 's/^"//; s/"$//')
  if [ -n "$owner_role" ] && [ "$owner_role" != "null" ]; then
    resolved=$(awk -v role_key="  $owner_role:" '
      $0 == "role_bindings:" { in_rb = 1; next }
      in_rb && index($0, role_key) == 1 { in_role = 1; next }
      in_role && index($0, "    human_id:") == 1 {
        sub("^    human_id:[	 ]*", ""); gsub(/^"|"$/, ""); print; exit
      }
      in_rb && $0 !~ /^  / && $0 != "" { in_rb = 0 }
      in_role && $0 !~ /^    / && $0 != "" { in_role = 0 }
    ' "$gov_file")
    resolved=${resolved#human:}
    [ -n "$resolved" ] && [ "$resolved" != "null" ] && owner_id=$resolved
  fi
fi
for f in "$TARGET/apps/team-capability-pack/README.md" \
  "$TARGET/apps/team-capability-pack/CONTEXT_INDEX.md" \
  "$TARGET/apps/team-capability-pack/skills"/*.skill.md; do
  [ -f "$f" ] || continue
  sed -i.bak "s#{{CELL_OWNER_ID}}#$owner_id#g" "$f" && rm -f "$f.bak"
done

MARKER="Team Capability Pack (installed $(date +%Y-%m-%d))"
if ! grep -q "$MARKER" "$TARGET/CONTEXT_INDEX.md" 2>/dev/null; then
  cat >> "$TARGET/CONTEXT_INDEX.md" <<EOF

## Team Capability Pack

$MARKER — optional. Its three skills are listed in the Procedure Index
above; \`apps/team-capability-pack/CONTEXT_INDEX.md\` is their bounded
sub-index (routing detail, one skill at a time). Not part of default
context load.
EOF
fi

# The three skills carry their own index metadata; regenerate the Cell's
# Procedure Index so they are listed as available only now that they exist.
if [ -f "$TARGET/scripts/render-instructions.py" ] && command -v python3 >/dev/null 2>&1; then
  python3 "$TARGET/scripts/render-instructions.py" --root "$TARGET" index --write
else
  echo "NOTE: run 'python3 scripts/render-instructions.py index --write' in $TARGET to refresh its Procedure Index" >&2
fi

echo "Team Capability Pack installed into $TARGET/apps/team-capability-pack"
echo "Checks: ./scripts/validate-cell.sh and python3 scripts/validate-skill-playground.py in the Cell."
