#!/bin/sh
set -eu

usage() {
  printf 'Usage: %s [--variant stable|teamcell-lite] TARGET_DIRECTORY\n' "$0" >&2
  exit 2
}

VARIANT=stable

while [ "$#" -gt 0 ]; do
  case "$1" in
    --variant)
      [ "$#" -ge 2 ] || usage
      VARIANT=$2
      shift 2
      ;;
    --variant=*)
      VARIANT=${1#--variant=}
      shift
      ;;
    --teamcell-lite)
      VARIANT=teamcell-lite
      shift
      ;;
    --help|-h)
      usage
      ;;
    --*)
      usage
      ;;
    *)
      break
      ;;
  esac
done

[ "$#" -eq 1 ] || usage

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
TARGET=$1

case "$VARIANT" in
  stable)
    KIT_ROOT="$REPO_ROOT/distribution/bootstrap-kit"
    ;;
  teamcell-lite)
    KIT_ROOT="$REPO_ROOT/distribution/teamcell-lite/bootstrap-kit"
    ;;
  *)
    printf 'Unsupported bootstrap variant: %s\n' "$VARIANT" >&2
    usage
    ;;
esac

[ -d "$KIT_ROOT" ] || {
  printf 'Bootstrap kit not found: %s\n' "$KIT_ROOT" >&2
  exit 1
}

if [ -e "$TARGET" ] && [ ! -d "$TARGET" ]; then
  printf 'Target exists and is not a directory: %s\n' "$TARGET" >&2
  exit 1
fi

mkdir -p "$TARGET"

if find "$TARGET" -mindepth 1 -maxdepth 1 ! -name .git -print -quit | grep -q .; then
  printf 'Target must be empty except for an optional .git directory: %s\n' "$TARGET" >&2
  exit 1
fi

if [ ! -d "$TARGET/.git" ]; then
  git -C "$TARGET" init -b main >/dev/null
fi

cp -R "$KIT_ROOT/." "$TARGET/"

# teamcell-lite's teamcell-lite-baseline package excludes profiles/ (packages/
# PACKAGES.yaml source_root of the two optional packages, teamcell-plus-
# profile and team-capability-pack) -- baseline installs must not receive
# optional-package source material by default (FAIL-PATTERN-20260717-015).
# Optional packages are copied separately, on top of this baseline tree, by
# scripts/teamcell-install-preview.py's mutate_new_from_template when
# explicitly selected via --optional-package.
if [ "$VARIANT" = teamcell-lite ] && [ -d "$TARGET/profiles" ]; then
  rm -rf "$TARGET/profiles"
fi

chmod +x "$TARGET/scripts/validate-cell.sh"

"$TARGET/scripts/validate-cell.sh" "$TARGET"

printf '\nTeam cell installed at %s\n' "$TARGET"
printf 'Variant: %s\n' "$VARIANT"
if [ "$VARIANT" = teamcell-lite ]; then
  printf 'Read PROJECT.md, add raw intake to inbox/INBOX.md, and create work from work/TEMPLATE.task.md.\n'
else
  printf 'Next: edit TEAM-PROFILE.md, add one inbox entry, and create one task from tasks/README.md.\n'
fi
