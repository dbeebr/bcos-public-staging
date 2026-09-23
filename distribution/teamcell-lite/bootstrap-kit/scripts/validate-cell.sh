#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

usage() {
  printf 'Usage: %s [CELL_ROOT] [--baseline FILE | --write-baseline FILE]\n' "$0" >&2
  printf '  --baseline FILE        compare failures by exact identity against a recorded\n' >&2
  printf '                         baseline; any failure not listed in FILE is blocking,\n' >&2
  printf '                         even when the total failure count is unchanged.\n' >&2
  printf '  --write-baseline FILE  record the current failure identities (see\n' >&2
  printf '                         playbooks/VALIDATOR-BASELINE.playbook.md); not a pass.\n' >&2
  exit 2
}

ROOT=
BASELINE_FILE=
WRITE_BASELINE_FILE=
while [ "$#" -gt 0 ]; do
  case "$1" in
    --baseline)
      [ "$#" -ge 2 ] || usage
      BASELINE_FILE=$2
      shift 2
      ;;
    --write-baseline)
      [ "$#" -ge 2 ] || usage
      WRITE_BASELINE_FILE=$2
      shift 2
      ;;
    --help|-h)
      usage
      ;;
    --*)
      usage
      ;;
    *)
      [ -z "$ROOT" ] || usage
      ROOT=$1
      shift
      ;;
  esac
done
[ -n "$ROOT" ] || ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
if [ -n "$BASELINE_FILE" ] && [ -n "$WRITE_BASELINE_FILE" ]; then
  usage
fi
if [ -n "$BASELINE_FILE" ] && [ ! -f "$BASELINE_FILE" ]; then
  printf 'Baseline file not found: %s\n' "$BASELINE_FILE" >&2
  exit 2
fi

FAILURES=0
WARNINGS=0
FAIL_LOG=${TMPDIR:-/tmp}/teamcell-lite-failures.$$
: > "$FAIL_LOG"
trap 'rm -f "$FAIL_LOG"' EXIT

# Every FAIL message is a stable failure identity: rule text plus the
# affected path/field. --baseline compares these identities exactly
# (playbooks/VALIDATOR-BASELINE.playbook.md), never just the count.
fail() {
  printf 'FAIL: %s\n' "$1" >&2
  printf '%s\n' "$1" >> "$FAIL_LOG"
  FAILURES=$((FAILURES + 1))
}

pass() {
  printf 'PASS: %s\n' "$1"
}

count_lines() {
  if [ -z "$1" ]; then
    printf '0'
  else
    printf '%s\n' "$1" | wc -l | tr -d '[:space:]'
  fi
}

warn() {
  printf 'WARN: %s\n' "$1" >&2
  WARNINGS=$((WARNINGS + 1))
}

has_field() {
  file=$1
  field=$2
  grep -q "^$field:" "$file"
}

field_value() {
  file=$1
  field=$2
  sed -n "s/^$field:[	 ]*//p" "$file" | sed -n '1p' | sed 's/^"//; s/"$//'
}

field_is_empty_or_null() {
  file=$1
  field=$2
  value=$(field_value "$file" "$field" | sed 's/^[	 ]*//; s/[	 ]*$//')
  [ "$value" = "" ] || [ "$value" = "null" ]
}

require_field() {
  file=$1
  relative_path=$2
  field=$3
  if ! has_field "$file" "$field"; then
    fail "missing frontmatter field $field in $relative_path"
    return 1
  fi
  return 0
}

require_nonempty_field() {
  file=$1
  relative_path=$2
  field=$3
  if ! require_field "$file" "$relative_path" "$field"; then
    return 1
  fi
  if field_is_empty_or_null "$file" "$field"; then
    fail "empty frontmatter field $field in $relative_path"
    return 1
  fi
  return 0
}

is_canonical_type() {
  case "$1" in
    task|proposal|decision|council|review|brief|doc|synthesis|report|record|skill|schema|template|index|state|genesis_record|app_instruction_block|prompt)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

# agent_capability_class (AGENTS.md "Actor Identity Rules"): the access
# class the writing agent actually had, not its product or model name.
capability_class_state() {
  case "$1" in
    local-worker|git-only-worker|chat-reviewer|read-only-observer|automation)
      printf 'canonical'
      ;;
    coding-agent|design-agent)
      printf 'legacy'
      ;;
    *)
      printf 'invalid'
      ;;
  esac
}

required_files='
README.md
PROJECT.md
TEAM-PROFILE.md
AGENTS.md
CONTEXT_INDEX.md
inbox/INBOX.md
work/README.md
work/TEMPLATE.task.md
human-gates/README.md
human-gates/TEMPLATE.human-gate.md
history/decisions/.gitkeep
history/records/.gitkeep
history/reviews/.gitkeep
playbooks/README.md
playbooks/TEMPLATE.playbook.md
reports/verification/.gitkeep
.github/copilot-instructions.md
scripts/validate-cell.sh
scripts/validate-completion.py
scripts/render-instructions.py
.bcos/CELL-PROFILE.yaml
.bcos/CELL-GOVERNANCE.yaml.template
docs/teamcell-gate-matrix.md
schemas/teamcell-cell-ownership.schema.md
schemas/teamcell-governance-profile.schema.md
schemas/completion-record.schema.md
'

for relative_path in $required_files; do
  if [ -e "$ROOT/$relative_path" ]; then
    pass "required path $relative_path"
  else
    fail "missing required path $relative_path"
  fi
done

tmp_files=${TMPDIR:-/tmp}/teamcell-lite-md-files.$$
find "$ROOT" -type d -name '.source-cache' -prune -o -type f -name '*.md' -print > "$tmp_files"

while IFS= read -r markdown_file; do
  relative_path=${markdown_file#"$ROOT"/}

  first_line=$(sed -n '1p' "$markdown_file")
  if [ "$first_line" != '---' ]; then
    fail "missing opening frontmatter marker in $relative_path"
    continue
  fi

  if [ "$(sed -n '2,$p' "$markdown_file" | grep -n '^---$' | sed -n '1p')" = "" ]; then
    fail "missing closing frontmatter marker in $relative_path"
    continue
  fi

  for field in bcos_type id title status created created_by agent_model; do
    if ! has_field "$markdown_file" "$field"; then
      fail "missing frontmatter field $field in $relative_path"
    fi
  done

  if has_field "$markdown_file" bcos_type; then
    bcos_type=$(field_value "$markdown_file" bcos_type)
    if is_canonical_type "$bcos_type"; then
      pass "canonical bcos_type $bcos_type in $relative_path"
    else
      fail "non-canonical bcos_type '$bcos_type' in $relative_path"
    fi
  fi

  if has_field "$markdown_file" agent_capability_class; then
    capability_value=$(field_value "$markdown_file" agent_capability_class | sed 's/^[	 ]*//; s/[	 ]*$//')
    case "$capability_value" in
      ''|null|*'|'*|'<'*|'OPEN:'*)
        # empty/null is checked per surface below; enum lists and <...>
        # are template prose, not a claim; "OPEN: ..." is a draft's visibly
        # open value (validate-completion.py --ready blocks execution on it)
        :
        ;;
      *)
        case "$(capability_class_state "$capability_value")" in
          canonical) : ;;
          legacy) warn "legacy agent_capability_class '$capability_value' in $relative_path (canonical: local-worker | git-only-worker | chat-reviewer | read-only-observer | automation)" ;;
          *) fail "non-canonical agent_capability_class '$capability_value' in $relative_path" ;;
        esac
        ;;
    esac
  fi

  case "$relative_path" in
    work/*.md|human-gates/*.md|playbooks/*.md|reports/verification/*.md)
      for identity_field in created_by_type created_by_id created_by_display created_by_github on_behalf_of_human_id; do
        require_field "$markdown_file" "$relative_path" "$identity_field" || true
      done
      require_nonempty_field "$markdown_file" "$relative_path" created_by_type || true
      require_nonempty_field "$markdown_file" "$relative_path" created_by_id || true
      require_nonempty_field "$markdown_file" "$relative_path" created_by_display || true

      created_by_type=$(field_value "$markdown_file" created_by_type)
      if [ "$created_by_type" = "agent" ]; then
        require_nonempty_field "$markdown_file" "$relative_path" agent_id || true
        require_nonempty_field "$markdown_file" "$relative_path" agent_model || true
        require_nonempty_field "$markdown_file" "$relative_path" agent_capability_class || true
        require_nonempty_field "$markdown_file" "$relative_path" on_behalf_of_human_id || true
      fi
      ;;
  esac

  case "$relative_path" in
    work/*.md)
      if ! grep -q '^surface:[	 ]*work$' "$markdown_file"; then
        fail "work file lacks surface: work in $relative_path"
      fi
      if grep -q '^bcos_type:[	 ]*task$' "$markdown_file" &&
        ! grep -q '^work_status:' "$markdown_file"; then
        fail "task under work lacks work_status in $relative_path"
      fi
      ;;
    human-gates/*.md)
      if ! grep -q '^surface:[	 ]*human-gates$' "$markdown_file"; then
        fail "human-gates file lacks surface: human-gates in $relative_path"
      fi
      if grep -q '^kind:[	 ]*human_gate$' "$markdown_file"; then
        for gate_field in gate_status requires_human_decision decision_owner_role decision_owner_id decision_owner_display reviewer_ids; do
          if ! has_field "$markdown_file" "$gate_field"; then
            fail "human gate lacks $gate_field in $relative_path"
          fi
        done

        # decision_owner_id / decision_owner_display may legitimately be the
        # literal `null` (role unresolved, or role named but unbound) per
        # schemas/teamcell-cell-ownership.schema.md's two unresolved states —
        # only a truly blank field (not even `null`) is a failure here.
        for owner_detail_field in decision_owner_id decision_owner_display; do
          if has_field "$markdown_file" "$owner_detail_field"; then
            detail_value=$(field_value "$markdown_file" "$owner_detail_field" | sed 's/^[	 ]*//; s/[	 ]*$//')
            if [ "$detail_value" = "" ]; then
              fail "blank $owner_detail_field in $relative_path (use the literal null when unresolved/unbound, never leave blank)"
            fi
          fi
        done

        # decision_owner_role tripwire: `unresolved` is always valid and
        # visible. A named role-slug must have a corresponding entry in
        # .bcos/CELL-GOVERNANCE.yaml's decision_owner_roles map (bound or
        # explicitly unresolved there too) — a role claimed by a gate but
        # absent from the Cell's governance config is a dangling reference.
        # Bracket-wrapped placeholder text (`<...>`, as shipped in
        # human-gates/TEMPLATE.human-gate.md) is template prose, not a real
        # claim, and is skipped.
        if has_field "$markdown_file" decision_owner_role; then
          role_value=$(field_value "$markdown_file" decision_owner_role | sed 's/^[	 ]*//; s/[	 ]*$//')
          case "$role_value" in
            ''|'<'*)
              :
              ;;
            unresolved)
              pass "human gate $relative_path has an explicit, visible unresolved decision_owner_role"
              ;;
            *)
              governance_file="$ROOT/.bcos/CELL-GOVERNANCE.yaml"
              if [ ! -f "$governance_file" ]; then
                fail "human gate $relative_path names decision_owner_role '$role_value' but .bcos/CELL-GOVERNANCE.yaml does not exist to verify it against"
              else
                decision_owner_roles_block=$(awk '/^decision_owner_roles:/{f=1;next} /^[^ ]/{f=0} f' "$governance_file")
                # -Eq (POSIX ERE, unescaped `|`): the prior `grep -q` form used
                # `\|` for alternation, a GNU BRE extension not honored by
                # BSD/POSIX grep (macOS's default /usr/bin/grep silently
                # treats `\|` as non-alternating, so the intended OR never
                # fires there). `-E` makes the alternation portable across
                # grep implementations.
                if printf '%s\n' "$decision_owner_roles_block" | grep -Eq "[:[:space:]]$role_value\$|[:[:space:]]$role_value[[:space:]]"; then
                  pass "human gate $relative_path's decision_owner_role '$role_value' has a corresponding .bcos/CELL-GOVERNANCE.yaml decision_owner_roles entry"
                else
                  fail "human gate $relative_path names decision_owner_role '$role_value' with no corresponding entry (bound or explicitly unresolved) in .bcos/CELL-GOVERNANCE.yaml's decision_owner_roles map"
                fi
              fi
              ;;
          esac
        fi
      fi
      ;;
  esac
done < "$tmp_files"

rm -f "$tmp_files"

if [ -f "$ROOT/PROJECT.md" ]; then
  for heading in '## Purpose' '## Scope' '## Data Policy'; do
    if grep -q "^$heading$" "$ROOT/PROJECT.md"; then
      pass "PROJECT.md contains $heading"
    else
      fail "PROJECT.md missing $heading"
    fi
  done
fi

if [ -f "$ROOT/TEAM-PROFILE.md" ]; then
  # Structural checks: any team passes; no specific names are required.
  participant_count=$(grep -c '^[	 ]*-[	 ]*human_id:[	 ]*human:' "$ROOT/TEAM-PROFILE.md" || true)
  if [ "${participant_count:-0}" -ge 1 ]; then
    pass "TEAM-PROFILE.md registers $participant_count participant(s) with human: IDs"
  else
    fail "TEAM-PROFILE.md registers no participant with a human: ID"
  fi

  display_count=$(grep -c '^[	 ]*display_name:[	 ]*..*' "$ROOT/TEAM-PROFILE.md" || true)
  if [ "${display_count:-0}" -ge "${participant_count:-0}" ] && [ "${display_count:-0}" -ge 1 ]; then
    pass "TEAM-PROFILE.md participants carry display_name values"
  else
    fail "TEAM-PROFILE.md has participants without display_name"
  fi

  owner_count=$(grep -c '^[	 ]*decision_authority:[	 ]*true' "$ROOT/TEAM-PROFILE.md" || true)
  if [ "${owner_count:-0}" -eq 1 ]; then
    pass "TEAM-PROFILE.md names exactly one participant with decision_authority: true"
  else
    fail "TEAM-PROFILE.md must name exactly one participant with decision_authority: true (found ${owner_count:-0})"
  fi

  for owner_field in decision_owner decision_owner_id decision_owner_display; do
    if grep -q "^$owner_field:[	 ]*..*" "$ROOT/TEAM-PROFILE.md"; then
      pass "TEAM-PROFILE.md carries $owner_field"
    else
      fail "TEAM-PROFILE.md missing or empty $owner_field"
    fi
  done

  if grep -q 'github:[	 ]*null' "$ROOT/TEAM-PROFILE.md"; then
    warn "TEAM-PROFILE.md keeps placeholder GitHub value(s) for at least one participant"
  fi
fi

# --- Governance-profile config: .bcos/CELL-GOVERNANCE.yaml ---
# The canonical template ships only .bcos/CELL-GOVERNANCE.yaml.template
# (governance_profile deliberately unresolved/uncreated — never pre-selected,
# per schemas/teamcell-governance-profile.schema.md). A Cell that has not yet
# hydrated the template file into a real .bcos/CELL-GOVERNANCE.yaml is a
# valid, expected pre-configuration state, not an error. Once the real file
# exists, its governance_profile must be one of the three enum values or
# null, and null must pair with legacy_unresolved: true.
governance_template="$ROOT/.bcos/CELL-GOVERNANCE.yaml.template"
governance_file="$ROOT/.bcos/CELL-GOVERNANCE.yaml"
if [ -f "$governance_file" ]; then
  profile_value=$(sed -n 's/^governance_profile:[	 ]*//p' "$governance_file" | sed -n '1p' | sed 's/^[	 ]*//; s/[	 ]*$//')
  legacy_value=$(sed -n 's/^legacy_unresolved:[	 ]*//p' "$governance_file" | sed -n '1p' | sed 's/^[	 ]*//; s/[	 ]*$//')
  case "$profile_value" in
    quick_build|operating_team|compliance_safety)
      pass ".bcos/CELL-GOVERNANCE.yaml governance_profile '$profile_value' is a valid enum value"
      if [ "$legacy_value" = "true" ]; then
        fail ".bcos/CELL-GOVERNANCE.yaml has governance_profile '$profile_value' but legacy_unresolved: true (must be false once a profile is selected)"
      fi
      ;;
    null)
      pass ".bcos/CELL-GOVERNANCE.yaml governance_profile is null (unresolved)"
      if [ "$legacy_value" != "true" ]; then
        fail ".bcos/CELL-GOVERNANCE.yaml has governance_profile: null but legacy_unresolved is not true"
      fi
      ;;
    *)
      fail ".bcos/CELL-GOVERNANCE.yaml governance_profile '$profile_value' is outside the three-value enum (quick_build | operating_team | compliance_safety) and is not null"
      ;;
  esac
elif [ -f "$governance_template" ]; then
  pass ".bcos/CELL-GOVERNANCE.yaml not yet hydrated from .bcos/CELL-GOVERNANCE.yaml.template (valid pre-configuration state)"
else
  fail ".bcos/CELL-GOVERNANCE.yaml is missing and no .bcos/CELL-GOVERNANCE.yaml.template is present to hydrate it from"
fi

# --- Owner-drift tripwire: literal owner-default leakage ---
# A template's historical owner default must never survive into a Cell as a
# live default. The identities to watch for are listed, one per line, in the
# optional .bcos/owner-denylist.txt (a maintainer-side file; # comments and
# blank lines ignored). Without that file the tripwire has nothing to watch
# and passes. A file may still mention a listed identity inside a
# documentation-example fence, used to show a *rejected* pattern:
#   <!-- validator:documentation-example:start --> ... <!-- validator:documentation-example:end -->
#
# Allowlist: a real Cell may deliberately bind a listed human: identity as a
# real owner via .bcos/CELL-GOVERNANCE.yaml's role_bindings map. That
# recorded binding distinguishes "legitimately retained real owner" from
# "unexamined template residue"; only such a binding suppresses the ban.
owner_denylist_file="$ROOT/.bcos/owner-denylist.txt"
owner_denylist_pattern=""
owner_denylist_ids=""
if [ -f "$owner_denylist_file" ]; then
  owner_denylist_entries=$(sed 's/#.*$//; s/^[	 ]*//; s/[	 ]*$//' "$owner_denylist_file" | sed '/^$/d')
  owner_denylist_pattern=$(printf '%s\n' "$owner_denylist_entries" | sed 's/[][\.*^$(){}?+|/]/\\&/g' | paste -sd '|' -)
  owner_denylist_ids=$(printf '%s\n' "$owner_denylist_entries" | grep '^human:' || true)
fi

owner_role_bound=false
governance_file="$ROOT/.bcos/CELL-GOVERNANCE.yaml"
if [ -n "$owner_denylist_ids" ] && [ -f "$governance_file" ]; then
  role_bindings_block=$(awk '/^role_bindings:/{f=1;next} /^[^ ]/{f=0} f' "$governance_file")
  bound_human_ids=$(printf '%s\n' "$role_bindings_block" | sed -n 's/^[	 ]*human_id:[	 ]*//p' | sed 's/^"//; s/"[	 ]*$//; s/[	 ]*$//')
  for denied_id in $owner_denylist_ids; do
    if printf '%s\n' "$bound_human_ids" | grep -Fxq "$denied_id"; then
      owner_role_bound=true
    fi
  done
fi

if [ -z "$owner_denylist_pattern" ]; then
  pass "owner-drift tripwire: no .bcos/owner-denylist.txt entries to watch for"
else
  find "$ROOT" -type d -name '.git' -prune -o -type d -name '.source-cache' -prune -o -type f \
    \( -name '*.md' -o -name '*.sh' -o -name '*.html' -o -name '*.py' -o -name '*.template' \) -print |
  while IFS= read -r scan_file; do
    if awk '
        /<!-- validator:documentation-example:start -->/ { infence = 1; next }
        /<!-- validator:documentation-example:end -->/ { infence = 0; next }
        !infence { print }
      ' "$scan_file" | grep -q -E "$owner_denylist_pattern"; then
      printf '%s\n' "${scan_file#"$ROOT"/}"
    fi
  done > "${TMPDIR:-/tmp}/teamcell-lite-owner-leak.$$"
  owner_leak_files=$(cat "${TMPDIR:-/tmp}/teamcell-lite-owner-leak.$$" 2>/dev/null || true)
  rm -f "${TMPDIR:-/tmp}/teamcell-lite-owner-leak.$$"
  if [ -n "$owner_leak_files" ]; then
    if [ "$owner_role_bound" = "true" ]; then
      pass "owner-denylist identity found in $(printf '%s\n' "$owner_leak_files" | wc -l | tr -d '[:space:]') file(s), but allowlisted: .bcos/CELL-GOVERNANCE.yaml's role_bindings records an explicit binding for it (a legitimately retained real Cell owner, not template residue)"
    else
      fail "owner-denylist identity (.bcos/owner-denylist.txt) found outside a documentation-example fence in: $(printf '%s' "$owner_leak_files" | tr '\n' ' ')"
    fi
  else
    pass "no owner-denylist identities outside documentation-example fences"
  fi
fi

if grep -R -n -E '-----BEGIN (RSA |DSA |EC |OPENSSH |)PRIVATE KEY-----' "$ROOT" --exclude-dir=.source-cache >/dev/null 2>&1; then
  fail "private key material found"
else
  pass "no private key material found"
fi

if grep -R -n -E '(api[_-]?key|access[_-]?token|secret|password)[	 ]*[:=][	 ]*["'\'']?[A-Za-z0-9_./+=:-]{12,}' "$ROOT" \
  --include='*.md' --include='*.sh' --include='*.json' --exclude-dir=.source-cache >/dev/null 2>&1; then
  fail "credential-shaped assignment found"
else
  pass "no credential-shaped assignments found"
fi

if [ -d "$ROOT/apps" ]; then
  if grep -R -n -E '\{\{[A-Za-z0-9_ .-]+\}\}' "$ROOT/apps" --exclude-dir=.source-cache >/dev/null 2>&1; then
    fail "unresolved {{placeholder}} token found under apps/"
  else
    pass "no unresolved placeholder tokens under apps/"
  fi

  if command -v python3 >/dev/null 2>&1; then
    if python3 "$SCRIPT_DIR/verify-app-manifests.py" "$ROOT"; then
      pass "apps/ provenance manifest(s) verified"
    else
      fail "apps/ provenance manifest verification failed (see output above)"
    fi
  else
    warn "python3 not available — skipped apps/ provenance manifest verification"
  fi
fi

if git -C "$ROOT" rev-parse --show-toplevel >/dev/null 2>&1; then
  pass "Git repository present"
  if git -C "$ROOT" diff --check; then
    pass "git diff --check passed"
  else
    fail "git diff --check failed"
  fi

  if git -C "$ROOT" remote get-url origin >/dev/null 2>&1; then
    pass "origin remote configured"
  else
    warn "no origin remote configured"
  fi

  committer_count=$(git -C "$ROOT" log --format='%ae' 2>/dev/null | sort -u | sed '/^$/d' | wc -l | tr -d ' ')
  if [ "${committer_count:-0}" -ge 2 ]; then
    pass "multiple committers observed"
  else
    warn "repo has only one committer or no commits"
  fi
else
  fail "target is not a Git repository"
fi

# --- Evidence-aware first-use / two-person readiness ---
# Unconditional warnings here made a healthy solo Cell and a genuinely
# incomplete first-use look identical. Both are now read from committed
# evidence instead of asserted blind.
if [ -f "$ROOT/reports/verification/FIRST-RUN-INSTALL-HANDOFF.md" ]; then
  pass "first-use proof recorded (reports/verification/FIRST-RUN-INSTALL-HANDOFF.md)"
else
  warn "first-use proof is pending — reports/verification/FIRST-RUN-INSTALL-HANDOFF.md not yet recorded"
fi

if [ "${participant_count:-0}" -le 1 ]; then
  pass "two-person proof: not applicable (TEAM-PROFILE.md declares a solo Cell — ${participant_count:-0} participant)"
elif [ "${committer_count:-0}" -ge 2 ]; then
  pass "two-person proof: satisfied (${committer_count:-0} distinct committers observed)"
else
  warn "two-person proof is pending — TEAM-PROFILE.md declares ${participant_count:-0} participants but only ${committer_count:-0} distinct committer(s) observed"
fi

# --- Package-tree reconciliation ---
# Re-derives packages/PACKAGES.yaml's "Reconciliation rule" structurally
# (well-known paths) instead of parsing that manifest at runtime: the
# installed copy of packages/PACKAGES.yaml is reference metadata only and
# a POSIX-sh validator carries no YAML parser.
receipt_file="$ROOT/.installation/TEAMCELL-INSTALLATION-RECEIPT.yaml"
if [ -f "$receipt_file" ]; then
  installed_ids=$(awk '/^installed_packages:/{f=1;next} /^[^ -]/{f=0} f' "$receipt_file" |
    sed -n 's/^-[	 ]*package_id:[	 ]*//p' | sed 's/^"//; s/"[	 ]*$//; s/[	 ]*$//')

  if [ -d "$ROOT/profiles" ]; then
    fail "profiles/ is present but must never appear in an installed Cell (it is distribution source material only)"
  else
    pass "profiles/ absent (required for every installed Cell, baseline or optional)"
  fi

  plus_declared=false
  printf '%s\n' "$installed_ids" | grep -Fxq "teamcell-plus-profile" && plus_declared=true
  plus_present=false
  [ -f "$ROOT/ONBOARDING.md" ] && [ -f "$ROOT/docs/CONTRACTS-V1.md" ] && plus_present=true
  if [ "$plus_declared" = "$plus_present" ]; then
    pass "teamcell-plus-profile presence matches installed_packages (installed: $plus_declared)"
  else
    fail "teamcell-plus-profile mismatch: installed_packages declares installed=$plus_declared but ONBOARDING.md/docs/CONTRACTS-V1.md presence=$plus_present"
  fi

  pack_declared=false
  printf '%s\n' "$installed_ids" | grep -Fxq "team-capability-pack" && pack_declared=true
  pack_present=false
  [ -d "$ROOT/apps/team-capability-pack" ] && [ -f "$ROOT/playbooks/onboarding/SKILL-PLAYGROUND.html" ] && pack_present=true
  if [ "$pack_declared" = "$pack_present" ]; then
    pass "team-capability-pack presence matches installed_packages (installed: $pack_declared)"
  else
    fail "team-capability-pack mismatch: installed_packages declares installed=$pack_declared but apps/team-capability-pack + onboarding presence=$pack_present"
  fi
else
  warn "no installation receipt found — skipped package-tree reconciliation"
fi

# --- Honest completion / status synchronicity ---
# scripts/validate-completion.py checks every work item: a done status needs
# a complete, placeholder-free Completion Record with real commit evidence,
# and a Completion Record that says done needs a done work_status.
if [ -d "$ROOT/work" ]; then
  if command -v python3 >/dev/null 2>&1; then
    completion_output=$(python3 "$SCRIPT_DIR/validate-completion.py" "$ROOT" 2>&1) || true
    completion_failures=0
    while IFS= read -r completion_line; do
      case "$completion_line" in
        'FAIL: '*)
          fail "${completion_line#FAIL: }"
          completion_failures=$((completion_failures + 1))
          ;;
        'WARN: '*)
          warn "${completion_line#WARN: }"
          ;;
      esac
    done <<EOF_COMPLETION
$completion_output
EOF_COMPLETION
    if [ "$completion_failures" -eq 0 ]; then
      pass "work item status and Completion Records are consistent ($(printf '%s\n' "$completion_output" | sed -n 's/^SUMMARY: //p'))"
    fi
  else
    warn "python3 not available — skipped work item completion checks (scripts/validate-completion.py)"
  fi
fi

# --- Procedure Index, Cell profile and rendered instructions ---
# scripts/render-instructions.py check: every path in .bcos/CELL-PROFILE.yaml
# exists; the Procedure Index in CONTEXT_INDEX.md equals what the active
# procedure files declare (a stale index fails); listed procedures belong to
# installed packages; instructions/ files still match their render hash
# (hand edits fail) and their budget; stale renders warn.
if command -v python3 >/dev/null 2>&1; then
  if [ -f "$ROOT/scripts/render-instructions.py" ] && [ -f "$ROOT/.bcos/CELL-PROFILE.yaml" ]; then
    render_output=$(PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/scripts/render-instructions.py" --root "$ROOT" check 2>&1) || true
    render_failures=0
    while IFS= read -r render_line; do
      case "$render_line" in
        'FAIL: '*)
          fail "${render_line#FAIL: }"
          render_failures=$((render_failures + 1))
          ;;
        'WARN: '*)
          warn "${render_line#WARN: }"
          ;;
        'ERROR: '*)
          fail "instruction renderer: ${render_line#ERROR: }"
          render_failures=$((render_failures + 1))
          ;;
      esac
    done <<EOF_RENDER
$render_output
EOF_RENDER
    if [ "$render_failures" -eq 0 ]; then
      pass "procedure index, Cell profile and rendered instructions are consistent ($(printf '%s\n' "$render_output" | sed -n 's/^SUMMARY: //p'))"
    fi
  fi
else
  warn "python3 not available — skipped procedure index and rendered instruction checks (scripts/render-instructions.py)"
fi

sort -u "$FAIL_LOG" > "$FAIL_LOG.sorted"
mv "$FAIL_LOG.sorted" "$FAIL_LOG"

if [ -n "$WRITE_BASELINE_FILE" ]; then
  {
    printf '# Teamcell Lite validator baseline — one exact failure identity per line.\n'
    printf '# Recorded: %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    if git -C "$ROOT" rev-parse HEAD >/dev/null 2>&1; then
      printf '# Recorded at commit: %s\n' "$(git -C "$ROOT" rev-parse HEAD)"
    fi
    printf '# A listed failure is known, not fixed. See playbooks/VALIDATOR-BASELINE.playbook.md.\n'
    cat "$FAIL_LOG"
  } > "$WRITE_BASELINE_FILE"
  printf 'Baseline recorded: %s known failure identit(y/ies) in %s. This is not a pass.\n' "$(count_lines "$(cat "$FAIL_LOG")")" "$WRITE_BASELINE_FILE"
  exit 0
fi

if [ -n "$BASELINE_FILE" ]; then
  known_file=${TMPDIR:-/tmp}/teamcell-lite-baseline-known.$$
  sed 's/^[	 ]*//; s/[	 ]*$//' "$BASELINE_FILE" | sed '/^#/d; /^$/d' | sort -u > "$known_file"
  new_failures=$(comm -23 "$FAIL_LOG" "$known_file")
  resolved_failures=$(comm -13 "$FAIL_LOG" "$known_file")
  still_known=$(comm -12 "$FAIL_LOG" "$known_file")
  rm -f "$known_file"
  printf '\nBaseline comparison against %s (exact failure identity, not count):\n' "$BASELINE_FILE"
  if [ -n "$still_known" ]; then
    printf '%s\n' "$still_known" | sed 's/^/  KNOWN (still present, not fixed): /'
  fi
  if [ -n "$resolved_failures" ]; then
    printf '%s\n' "$resolved_failures" | sed 's/^/  RESOLVED (remove from baseline): /'
  fi
  if [ -n "$new_failures" ]; then
    printf '%s\n' "$new_failures" | sed 's/^/  NEW (blocking): /' >&2
    printf 'Teamcell Lite validation failed against baseline: %s new failure(s), %s total issue(s), %s warning(s).\n' \
      "$(count_lines "$new_failures")" "$FAILURES" "$WARNINGS" >&2
    exit 1
  fi
  printf 'Teamcell Lite validation passed against baseline: no new failures; %s known failure(s) remain, %s resolved; %s warning(s).\n' \
    "$(count_lines "$still_known")" "$(count_lines "$resolved_failures")" "$WARNINGS"
  exit 0
fi

if [ "$FAILURES" -ne 0 ]; then
  printf 'Teamcell Lite validation failed with %s issue(s), %s warning(s).\n' "$FAILURES" "$WARNINGS" >&2
  exit 1
fi

printf 'Teamcell Lite validation passed with %s warning(s).\n' "$WARNINGS"
