#!/bin/sh
set -eu

# scripts/teamcell-install-preflight.sh
#
# Executable preflight checks for a Teamcell installation, per
# docs/architecture/BCOS-TEAMCELL-INSTALL-SEMANTICS-V1-20260714.md's
# "Preflight" section: git availability, GitHub CLI presence and
# authentication, VS Code presence, target directory/repository state, and
# access to the declared source repositories. Every failed check prints
# actionable repair text — never a stack trace — and the script exits
# non-zero if any check fails.
#
# Usage:
#   scripts/teamcell-install-preflight.sh TARGET_DIR \
#     [--mode new_from_template|hydrate_existing_repo|clone_existing_cell] \
#     [--source-repo OWNER/REPO] [--package-repo OWNER/REPO ...] \
#     [--manual]
#
# --manual prints the equivalent manual checklist for a human who cannot run
# this script live, instead of executing any check.

SCRIPT_NAME=$(basename "$0")
MODE=
PREFLIGHT_REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
# Default source: this checkout when it is a Teamcell distribution (it
# carries distribution/teamcell-lite/SOURCE-MANIFEST.json), else the
# operator's canonical template repository.
if [ -f "$PREFLIGHT_REPO_ROOT/distribution/teamcell-lite/SOURCE-MANIFEST.json" ]; then
  SOURCE_REPO=$PREFLIGHT_REPO_ROOT
else
  SOURCE_REPO=dbeebr/bcos-teamcell-lite-template
fi
PACKAGE_REPOS=
MANUAL=no
TARGET=

usage() {
  printf 'Usage: %s TARGET_DIR [--mode MODE] [--source-repo OWNER/REPO] [--package-repo OWNER/REPO ...] [--manual]\n' "$SCRIPT_NAME" >&2
  exit 2
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --mode)
      [ "$#" -ge 2 ] || usage
      MODE=$2
      shift 2
      ;;
    --source-repo)
      [ "$#" -ge 2 ] || usage
      SOURCE_REPO=$2
      shift 2
      ;;
    --package-repo)
      [ "$#" -ge 2 ] || usage
      PACKAGE_REPOS="$PACKAGE_REPOS $2"
      shift 2
      ;;
    --manual)
      MANUAL=yes
      shift
      ;;
    --help|-h)
      usage
      ;;
    --*)
      usage
      ;;
    *)
      if [ -z "$TARGET" ]; then
        TARGET=$1
        shift
      else
        usage
      fi
      ;;
  esac
done

[ -n "$TARGET" ] || usage

FAILED=0
PASSED=0

pass() {
  PASSED=$((PASSED + 1))
  printf 'PASS: %s\n' "$1"
}

fail() {
  FAILED=$((FAILED + 1))
  printf 'FAIL: %s\n' "$1" >&2
  printf '  repair: %s\n' "$2" >&2
}

print_manual_checklist() {
  cat <<EOF
TEAMCELL INSTALL PREFLIGHT — MANUAL CHECKLIST
(for a human who cannot run this script live; walk through each item by hand)

Target: $TARGET
Declared mode: ${MODE:-not yet chosen}
Declared source repo: $SOURCE_REPO
Declared package repos:${PACKAGE_REPOS:- none}

1. Git availability
   - Run: git --version
   - Confirm a version prints (any modern git works; 2.x or later recommended).
   - If missing: install Git (https://git-scm.com/downloads) then re-check.

2. GitHub CLI presence and authentication (only needed when a declared
   source or package is a remote owner/repo; skip for local paths such as
   a clone of the public Teamcell distribution)
   - Run: gh --version
   - Run: gh auth status
   - Confirm gh is installed and shows "Logged in to github.com".
   - If missing: install GitHub CLI (https://cli.github.com), then run:
       gh auth login

3. VS Code presence (optional — any editor works)
   - Run: code --version   (or open VS Code and check Command Palette ->
     "Shell Command: Install 'code' command in PATH")
   - If missing: install VS Code (https://code.visualstudio.com/) and enable
     the 'code' shell command.

3b. Python 3 with PyYAML
   - Run: python3 -c 'import yaml; print(yaml.__version__)'
   - If missing: python3 -m pip install --user pyyaml

4. Target directory/repository state
   - Inspect $TARGET by hand:
     - Does it exist? Is it empty (or only a bare .git directory)?
     - Does it already contain TEAM-PROFILE.md, .bcos/CELL-GOVERNANCE.yaml,
       or .installation/TEAMCELL-INSTALLATION-RECEIPT.yaml (already a Cell)?
   - Confirm the target state matches the declared mode's precondition:
     - new_from_template requires an empty target (or bare .git only).
     - hydrate_existing_repo requires an existing, populated target.
     - clone_existing_cell accepts either.

5. Access to declared source repositories
   - For each of: $SOURCE_REPO$PACKAGE_REPOS
     Run: gh repo view <owner/repo>
   - Confirm it resolves without a permission error.
   - If it fails: request access from the repository owner, or run
       gh auth refresh -h github.com -s repo
     to widen your token's scope, then retry.

Do not proceed to a confirmed install until every item above is confirmed by
hand. This checklist does not itself run any check — it is the manual
fallback for a human without shell access to this script.
EOF
}

if [ "$MANUAL" = yes ]; then
  print_manual_checklist
  exit 0
fi

printf 'TEAMCELL INSTALL PREFLIGHT\n'
printf 'Target: %s\n' "$TARGET"
printf 'Declared mode: %s\n' "${MODE:-not yet chosen}"
printf 'Declared source repo: %s\n\n' "$SOURCE_REPO"

# 1. Git availability
if command -v git >/dev/null 2>&1; then
  GIT_VERSION=$(git --version 2>/dev/null || printf 'unknown')
  pass "git is available ($GIT_VERSION)"
else
  fail "git is not installed or not on PATH" \
    "install Git (https://git-scm.com/downloads), then re-run this preflight"
fi

# 2. GitHub CLI presence and authentication (only for remote sources)
# The GitHub CLI is only required when a declared source or package is a
# remote owner/repo. Installing from local paths (for example a clone of the
# public Teamcell distribution) needs no GitHub login.
NEEDS_GH=no
for repo in "$SOURCE_REPO" $PACKAGE_REPOS; do
  [ -n "$repo" ] || continue
  [ -e "$repo" ] || NEEDS_GH=yes
done
if [ "$NEEDS_GH" = yes ]; then
  if command -v gh >/dev/null 2>&1; then
    pass "gh (GitHub CLI) is installed"
    if gh auth status >/dev/null 2>&1; then
      pass "gh is authenticated"
    else
      fail "gh is installed but not authenticated" \
        "run: gh auth login"
    fi
  else
    fail "gh (GitHub CLI) is not installed or not on PATH" \
      "install GitHub CLI (https://cli.github.com), then run: gh auth login"
  fi
else
  pass "gh (GitHub CLI) not required: every declared source is a local path"
fi

if command -v python3 >/dev/null 2>&1; then
  if python3 -c 'import yaml' >/dev/null 2>&1; then
    pass "python3 with PyYAML is available"
  else
    fail "python3 is available but the PyYAML package is not installed" \
      "run: python3 -m pip install --user pyyaml   (or install your platform's python3-yaml package)"
  fi
else
  fail "python3 is not installed or not on PATH" \
    "install Python 3.9 or later (https://www.python.org/downloads/), then: python3 -m pip install --user pyyaml"
fi

# 3. VS Code presence (optional — any editor works)
VSCODE_FOUND=no
if command -v code >/dev/null 2>&1; then
  VSCODE_FOUND=yes
else
  for candidate in \
    '/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code' \
    '/Applications/Visual Studio Code - Insiders.app/Contents/Resources/app/bin/code'
  do
    if [ -x "$candidate" ]; then
      VSCODE_FOUND=yes
      break
    fi
  done
fi
# Advisory only: any editor works for a Cell; VS Code is simply the editor the
# generated first-run prompt refers to.
if [ "$VSCODE_FOUND" = yes ]; then
  pass "VS Code is available"
else
  printf 'NOTE: VS Code was not found (no '"'"'code'"'"' on PATH and no /Applications install detected) — optional; any editor works.\n'
fi

# 4. Target directory/repository state
if [ -e "$TARGET" ] && [ ! -d "$TARGET" ]; then
  fail "target exists and is not a directory: $TARGET" \
    "remove or rename the conflicting file, or choose a different target path"
else
  if [ -d "$TARGET" ]; then
    NON_GIT_ENTRIES=$(find "$TARGET" -mindepth 1 -maxdepth 1 ! -name .git -print -quit 2>/dev/null || true)
    if [ -n "$NON_GIT_ENTRIES" ]; then
      TARGET_STATE=populated
    else
      TARGET_STATE=empty-or-bare-git
    fi
  else
    TARGET_STATE=does-not-exist
  fi

  case "$MODE" in
    new_from_template)
      if [ "$TARGET_STATE" = populated ]; then
        fail "target is populated but new_from_template requires an empty target (or bare .git only): $TARGET" \
          "choose an empty target, or re-run with --mode hydrate_existing_repo or --mode clone_existing_cell if that is what you intend"
      else
        pass "target state ($TARGET_STATE) satisfies new_from_template's empty-target precondition"
      fi
      ;;
    hydrate_existing_repo)
      if [ "$TARGET_STATE" != populated ]; then
        fail "target is not populated but hydrate_existing_repo requires an existing, populated target: $TARGET" \
          "point --target at the existing, populated repository you intend to hydrate, or use --mode new_from_template for an empty target"
      else
        pass "target state ($TARGET_STATE) satisfies hydrate_existing_repo's populated-target precondition"
      fi
      ;;
    clone_existing_cell)
      pass "target state ($TARGET_STATE) is acceptable for clone_existing_cell (source dictates, not target emptiness)"
      ;;
    *)
      pass "target state: $TARGET_STATE (no --mode given to this preflight invocation; re-run with --mode once resolved to check the mode-specific precondition)"
      ;;
  esac
fi

# 5. Access to declared source repositories
GH_READY=no
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  GH_READY=yes
fi
for repo in "$SOURCE_REPO" $PACKAGE_REPOS; do
  [ -n "$repo" ] || continue
  if [ -e "$repo" ]; then
    # A local filesystem path (e.g. clone_existing_cell's --clone-source
    # pointing at an already-hydrated local Cell) — check readability
    # directly rather than through gh, which only resolves owner/repo slugs.
    if [ -r "$repo" ]; then
      pass "access confirmed to local source path: $repo"
    else
      fail "local source path is not readable: $repo" \
        "check the path exists and this user has read permission: ls -la \"$repo\""
    fi
    continue
  fi
  if [ "$GH_READY" = yes ]; then
    if gh repo view "$repo" >/dev/null 2>&1; then
      pass "access confirmed to source repository: $repo"
    else
      fail "no access to declared source repository: $repo" \
        "request access from the repository owner, or run: gh auth refresh -h github.com -s repo"
    fi
  else
    fail "cannot check access to $repo without an authenticated gh" \
      "resolve the gh authentication failure above first, then re-run this preflight"
  fi
done

printf '\nSUMMARY: %s passed, %s failed\n' "$PASSED" "$FAILED"
if [ "$FAILED" -gt 0 ]; then
  printf 'Preflight FAILED. Repair the items above before confirming an install.\n' >&2
  exit 1
fi
printf 'Preflight PASSED.\n'
exit 0
