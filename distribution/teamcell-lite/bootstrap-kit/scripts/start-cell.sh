#!/bin/sh
set -eu

# Canonical Teamcell Lite daily-start entry point.
#
# Idempotent and non-destructive: verifies identity and Git state, offers a
# safe fast-forward-only sync, runs validate-cell.sh, and prints one NOW
# block with the active work item and next action. Never resets, discards,
# or force-pushes anything. This is a Cell/workspace start command, not an
# application dependency installer -- it never invents a tech stack.
#
# Self-contained by design: an installed Cell must be able to run this
# without the installer/distribution checkout present on the machine.

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
cd "$ROOT"

EXIT_CODE=0

warn() { printf 'WARN: %s\n' "$1" >&2; }
info() { printf '%s\n' "$1"; }
fail_exit() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

field_value() {
  file=$1
  field=$2
  [ -f "$file" ] || return 0
  sed -n "s/^$field:[	 ]*//p" "$file" | sed -n '1p' | sed 's/^"//; s/"$//'
}

yaml_nested_value() {
  # Best-effort extraction of a 2-space-indented "key: value" line under a
  # top-level "section:" block in a small, known-shape YAML file (the
  # installation receipt). Not a general YAML parser.
  file=$1
  section=$2
  key=$3
  [ -f "$file" ] || return 0
  value=$(awk -v section="$section:" -v key="  $key:" '
    $0 == section { in_section=1; next }
    in_section && index($0, key) == 1 {
      sub("^" key "[ \t]*", "");
      gsub(/^"|"$/, "");
      print;
      exit
    }
    in_section && $0 !~ /^  / && $0 != "" { in_section=0 }
  ' "$file")
  [ "$value" = "null" ] && value=""
  printf '%s' "$value"
}

normalize_remote() {
  printf '%s' "$1" | sed -E 's#^(git@|https?://|ssh://)([^/:]+)[:/]#\2/#; s#\.git/?$##' | sed -E 's#^[^/]+/##' 2>/dev/null || true
}

printf '%s\n' 'BCOS Teamcell — daily start' ''

# --- 1/2. Identity verification ---------------------------------------
receipt_repo=$(yaml_nested_value ".installation/TEAMCELL-INSTALLATION-RECEIPT.yaml" target repository)
remote_url=$(git remote get-url origin 2>/dev/null || true)
remote_repo=""
if [ -n "$remote_url" ]; then
  remote_repo=$(printf '%s' "$remote_url" | sed -E 's#^git@([^:]+):#https://\1/#' | sed -E 's#^(https?://[^/]+/)##; s#\.git$##')
fi

if [ -n "$receipt_repo" ] && [ -n "$remote_repo" ]; then
  if [ "$receipt_repo" != "$remote_repo" ]; then
    printf 'FAIL: repository identity mismatch\n' >&2
    printf '  installation receipt: %s\n' "$receipt_repo" >&2
    printf '  git remote origin:    %s\n' "$remote_repo" >&2
    printf 'Next action: confirm which is correct before continuing; do not proceed on a mismatched identity.\n' >&2
    exit 1
  fi
  info "Repository identity: $receipt_repo — OK (receipt matches git remote)"
elif [ -n "$remote_repo" ]; then
  info "Repository identity: $remote_repo (from git remote; no installation receipt found)"
elif [ -n "$receipt_repo" ]; then
  info "Repository identity: $receipt_repo (from installation receipt; no git remote configured)"
else
  warn "Repository identity could not be verified (no installation receipt, no git remote origin)."
fi

# --- 2. Branch and remote relation -------------------------------------
branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')
info "Branch: $branch"

pulled=no
if [ -n "$remote_url" ] && [ "$branch" = main ]; then
  if git fetch origin main --quiet 2>/dev/null; then
    local_head=$(git rev-parse HEAD 2>/dev/null || echo '')
    remote_head=$(git rev-parse origin/main 2>/dev/null || echo '')
    if [ "$local_head" = "$remote_head" ]; then
      info 'origin/main: up to date'
    else
      ahead_behind=$(git rev-list --left-right --count HEAD...origin/main 2>/dev/null || echo '0	0')
      ahead=$(printf '%s' "$ahead_behind" | cut -f1)
      behind=$(printf '%s' "$ahead_behind" | cut -f2)
      dirty=$(git status --porcelain 2>/dev/null || echo '')
      if [ "$ahead" = 0 ] && [ "$behind" != 0 ] && [ -z "$dirty" ]; then
        info "origin/main: behind by $behind commit(s) — clean tree, fast-forwarding..."
        if git pull --ff-only origin main --quiet 2>/dev/null; then
          info "origin/main: fast-forwarded to $(git rev-parse --short HEAD)"
          pulled=yes
        else
          warn 'git pull --ff-only failed unexpectedly; local state is unchanged. Resolve manually.'
        fi
      elif [ -n "$dirty" ]; then
        warn "Working tree has uncommitted changes; not syncing automatically. (ahead $ahead / behind $behind)"
      else
        warn "Local and origin/main have diverged (ahead $ahead / behind $behind); not auto-merging or rebasing. Resolve manually."
      fi
    fi
  else
    warn 'Could not fetch origin (offline, or this Cell has no reachable remote). Skipping sync check.'
  fi
else
  info 'origin/main: no remote configured (local-only Cell) or not on main — skipping sync.'
fi

# --- 3. Cell validation --------------------------------------------------
printf '\nRunning ./scripts/validate-cell.sh...\n'
if [ -x "$ROOT/scripts/validate-cell.sh" ]; then
  if "$ROOT/scripts/validate-cell.sh" "$ROOT"; then
    info 'validate-cell.sh: PASS'
  else
    printf 'FAIL: scripts/validate-cell.sh reported failures (see above).\n' >&2
    EXIT_CODE=1
  fi
else
  warn 'scripts/validate-cell.sh not found or not executable; skipping validation.'
fi

if [ "$EXIT_CODE" != 0 ]; then
  exit "$EXIT_CODE"
fi

# --- 4. Unresolved template placeholders ---------------------------------
# Narrow scan target, not a broad repo-wide
# grep: only the installed/runtime/configuration surfaces the installer and
# personalizer are actually supposed to resolve. Root docs (PROJECT.md,
# AGENTS.md, CONTEXT_INDEX.md, README.md, ...) intentionally carry a
# generic on_behalf_of_human_id: "human:{{CELL_OWNER_ID}}" template
# provenance field that no current tool resolves in any Cell -- scanning
# them made every healthy install look identical to a broken one.
actionable_scan_targets=''
for candidate in .bcos/CELL-GOVERNANCE.yaml TEAM-PROFILE.md FIRST-RUN-AGENT-PROMPT.md \
  reports/verification/POST-INSTALL-PERSONALIZATION.md; do
  [ -f "$candidate" ] && actionable_scan_targets="$actionable_scan_targets $candidate"
done
[ -d instructions ] && actionable_scan_targets="$actionable_scan_targets $(ls instructions/*.md 2>/dev/null | tr '\n' ' ')"

placeholder_files=''
for f in $actionable_scan_targets; do
  grep -lq '{{[A-Za-z0-9_ .-]*}}' "$f" 2>/dev/null && placeholder_files="$placeholder_files
$f"
done
placeholder_files=$(printf '%s' "$placeholder_files" | sed '/^$/d')

if [ -n "$placeholder_files" ]; then
  printf '\nUnresolved template placeholders found in installed/runtime surfaces:\n'
  printf '%s\n' "$placeholder_files" | sed 's/^/  /'
else
  printf '\nUnresolved template placeholders in installed/runtime surfaces: none\n'
fi
generic_doc_count=$(grep -rl '{{[A-Za-z0-9_ .-]*}}' --include='*.md' --include='*.yaml' . 2>/dev/null | grep -v '^\./\.git/' | wc -l | tr -d ' ')
generic_doc_count=$((generic_doc_count - $(printf '%s\n' "$placeholder_files" | sed '/^$/d' | wc -l | tr -d ' ')))
[ "${generic_doc_count:-0}" -gt 0 ] && printf '(%s generic template/example placeholder(s) elsewhere in root docs — informational, not actionable, never resolved by the installer)\n' "$generic_doc_count"

# --- 5. Instruction lifecycle / activation state --------------------------
printf '\nInstruction lifecycle:\n'
personalization_record="reports/verification/POST-INSTALL-PERSONALIZATION.md"
if [ -d instructions ] && [ -n "$(ls instructions/APP-INSTRUCTIONS-*.md 2>/dev/null)" ]; then
  reviewed=false
  activated=false
  if [ -f "$personalization_record" ]; then
    reviewed=$(sed -n 's/^ *reviewed: *//p' "$personalization_record" | head -1)
    activated=$(sed -n 's/^ *activated_self_reported: *//p' "$personalization_record" | head -1)
    reviewed=${reviewed:-false}
    activated=${activated:-false}
  fi
  for f in instructions/APP-INSTRUCTIONS-*.md; do
    surface=$(basename "$f" .md | sed 's/^APP-INSTRUCTIONS-//')
    if [ "$activated" = true ]; then
      state='activated-self-reported'
    else
      state='pending (not yet self-reported)'
    fi
    printf '  %s: generated, reviewed=%s, activation: %s\n' "$surface" "$reviewed" "$state"
  done
  [ -f instructions/PROJECT-INSTRUCTIONS.md ] &&
    printf '  ready to paste: instructions/PROJECT-INSTRUCTIONS.md (the complete fenced block)\n'
elif [ -f scripts/personalize-cell.py ]; then
  printf '  none generated yet — run: python3 scripts/personalize-cell.py   (non-interactive; then commit the result)\n'
else
  printf '  none generated yet — run scripts/personalize-team-cell.sh from the Teamcell distribution checkout you installed from if you want ChatGPT/Claude/Copilot/Gemini instruction blocks.\n'
fi

# --- 6. Active work item ---------------------------------------------------
# Work items are work/TASK-*.md (current naming, work/TEMPLATE.task.md) or
# work/WORK-*.md (earlier naming, still honored). Templates and README are
# never work items. Selection by work_status (work/README.md): the first
# in-progress item, else the first needs-review item, else the first open
# item, in file-name order. A done item is never selected as active.
active_work=""
active_title=""
open_work_count=0
if [ -d work ]; then
  for wanted in in-progress needs-review open; do
    for f in $(ls work/TASK-*.md work/WORK-*.md 2>/dev/null | sort); do
      case "$(basename "$f")" in TEMPLATE*|README.md) continue ;; esac
      if [ "$(field_value "$f" work_status)" = "$wanted" ]; then
        active_work=$f
        break
      fi
    done
    [ -n "$active_work" ] && break
  done
  for f in $(ls work/TASK-*.md work/WORK-*.md 2>/dev/null); do
    case "$(field_value "$f" work_status)" in
      done|'') : ;;
      *) open_work_count=$((open_work_count + 1)) ;;
    esac
  done
  if [ -n "$active_work" ]; then
    active_title=$(field_value "$active_work" title)
  fi
fi

# Format check of the active item (validate-completion.py --ready): a task
# that does not follow the current work/TEMPLATE.task.md, or still carries
# OPEN: items or template placeholders, is a draft and not executable.
active_ready=''
if [ -n "$active_work" ] && command -v python3 >/dev/null 2>&1 && [ -f scripts/validate-completion.py ]; then
  if ready_output=$(python3 scripts/validate-completion.py --ready "$active_work" 2>&1); then
    active_ready='yes (format check passed)'
  else
    active_ready="no — $(printf '%s\n' "$ready_output" | sed -n 's/^RESULT: NOT READY [^ ]* ([^)]*): //p' | sed -n '1p') Run: python3 scripts/validate-completion.py --ready $active_work"
  fi
fi

project_stage=$(field_value PROJECT.md status)

if [ -d instructions ] && [ -n "$(ls instructions/APP-INSTRUCTIONS-*.md 2>/dev/null)" ] && [ "${activated:-false}" != true ]; then
  next_action_text='paste the generated instruction blocks into their app project settings (see paths below), then re-run this command.'
  human_gated_text='external ChatGPT/Claude/Copilot/Gemini activation (self-reported only; BCOS cannot verify external app settings).'
elif [ -n "$active_work" ] && [ "${active_ready#no}" != "$active_ready" ]; then
  next_action_text="complete the draft $active_work (open items above) before executing it."
  human_gated_text='open facts, IDs or approvals in the active draft (planner or decision owner).'
elif [ -n "$active_work" ]; then
  next_action_text="continue $active_work."
  human_gated_text='none outstanding from this check.'
else
  next_action_text='create the next work item as work/TASK-YYYYMMDD-NNN-<slug>.md from work/TEMPLATE.task.md.'
  human_gated_text='none outstanding from this check.'
fi

printf '\n--- NOW ---\n'
printf 'Stage:        %s\n' "${project_stage:-unknown}"
if [ -n "$active_work" ]; then
  printf 'Active work:  %s%s (%s not done)\n' "$active_work" "${active_title:+ — $active_title}" "$open_work_count"
  if [ -n "$active_ready" ]; then
    printf 'Ready:        %s\n' "$active_ready"
  fi
else
  printf 'Active work:  none open (work/TASK-*.md, work/WORK-*.md)\n'
fi
printf 'Next action:  %s\n' "$next_action_text"
printf 'Human-gated:  %s\n' "$human_gated_text"
procedure_index_line=$(sed -n 's/^index_version: //p' CONTEXT_INDEX.md 2>/dev/null | sed -n '1p')
if [ -n "$procedure_index_line" ]; then
  printf 'Procedures:   %s — check CONTEXT_INDEX.md "Procedure Index" for the active work\n' "$procedure_index_line"
else
  printf 'Procedures:   no generated Procedure Index in CONTEXT_INDEX.md — run python3 scripts/render-instructions.py index --write\n'
fi
printf -- '-----------\n'

# --- 7. Generate the current primary onboarding page (START-HERE.html) ----
# Regenerated every start-cell.sh run from the same
# facts just computed above, so it never goes stale. Self-contained (no
# network dependency). This is baseline content
# and always installed, unlike SKILL-PLAYGROUND.html (capability-pack-only).
governance_file=".bcos/CELL-GOVERNANCE.yaml"
governance_profile_value=$(field_value "$governance_file" governance_profile)
cell_owner_role_value=$(field_value "$governance_file" cell_owner_role)
owner_display_value=""
if [ -n "$cell_owner_role_value" ] && [ -f "$governance_file" ]; then
  owner_display_value=$(awk -v role_key="  $cell_owner_role_value:" '
    $0 == "role_bindings:" { in_rb = 1; next }
    in_rb && index($0, role_key) == 1 { in_role = 1; next }
    in_role && index($0, "    display_name:") == 1 {
      sub("^    display_name:[	 ]*", "");
      gsub(/^"|"$/, "");
      print; exit
    }
    in_rb && $0 !~ /^  / && $0 != "" { in_rb = 0 }
    in_role && $0 !~ /^    / && $0 != "" { in_role = 0 }
  ' "$governance_file")
fi
cell_name_value=$(field_value PROJECT.md title)
[ -n "$cell_name_value" ] || cell_name_value=$(basename "$ROOT")

agent_surfaces_html=''
if [ -d instructions ] && [ -n "$(ls instructions/APP-INSTRUCTIONS-*.md 2>/dev/null)" ]; then
  for f in instructions/APP-INSTRUCTIONS-*.md; do
    surface=$(basename "$f" .md | sed 's/^APP-INSTRUCTIONS-//')
    if [ "${activated:-false}" = true ]; then
      surface_state='activated (self-reported)'
    else
      surface_state='generated, not yet activated'
    fi
    agent_surfaces_html="$agent_surfaces_html<li><a href=\"../../instructions/APP-INSTRUCTIONS-$surface.md\">$surface</a> — $surface_state</li>"
  done
else
  agent_surfaces_html='<li>none generated yet</li>'
fi

mkdir -p playbooks/onboarding
start_here_out=playbooks/onboarding/START-HERE.html
{
  printf '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
  printf '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
  printf '<title>%s — Start Here</title>\n' "$cell_name_value"
  printf '<style>body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;max-width:44rem;margin:2rem auto;padding:0 1.25rem;line-height:1.5;color:#1a1a1a;background:#fafaf8}'
  printf '@media (prefers-color-scheme: dark){body{color:#f2efe8;background:#171612}}'
  printf 'code,pre{background:rgba(127,127,127,.15);padding:.15em .4em;border-radius:.3em}'
  printf 'dt{font-weight:600;margin-top:.75em}dd{margin:0 0 .25em 0}</style>\n</head>\n<body>\n'
  printf '<h1>%s</h1>\n' "$cell_name_value"
  printf '<p>Regenerated by <code>scripts/start-cell.sh</code> on every local start — always current as of the last run. Never edit this file directly.</p>\n'
  if [ -f "$ROOT/instructions/PROJECT-INSTRUCTIONS.md" ]; then
    printf '<p style="padding:.75rem 1rem;border-left:4px solid #2a7;background:rgba(42,170,119,.12)"><strong>Ready-to-paste agent instructions:</strong> <a href="../../instructions/PROJECT-INSTRUCTIONS.md">instructions/PROJECT-INSTRUCTIONS.md</a> — copy the complete fenced block into your ChatGPT, Claude, Copilot or Gemini project. Generated for this Cell; not active in any app until you paste it.</p>\n'
  fi
  printf '<dl>\n'
  printf '<dt>Stage</dt><dd>%s</dd>\n' "${project_stage:-unknown}"
  printf '<dt>Governance</dt><dd>%s (decision owner role: %s%s)</dd>\n' "${governance_profile_value:-unresolved}" "${cell_owner_role_value:-unresolved}" "${owner_display_value:+ — $owner_display_value}"
  if [ -n "$active_work" ]; then
    printf '<dt>Active work</dt><dd>%s%s</dd>\n' "$active_work" "${active_title:+ — $active_title}"
  else
    printf '<dt>Active work</dt><dd>none open (work/TASK-*.md, work/WORK-*.md)</dd>\n'
  fi
  printf '<dt>Start command</dt><dd><code>cd %s &amp;&amp; ./scripts/start-cell.sh</code></dd>\n' "$ROOT"
  printf '<dt>Agent surfaces</dt><dd><ul>%s</ul></dd>\n' "$agent_surfaces_html"
  printf '<dt>Next action</dt><dd>%s</dd>\n' "$next_action_text"
  printf '<dt>Human-gated</dt><dd>%s</dd>\n' "$human_gated_text"
  printf '</dl>\n'
  printf '<p>See <a href="../../PROJECT.md">PROJECT.md</a> for full purpose and scope'
  if [ -f "$ROOT/playbooks/onboarding/TEAMCELL-LITE-INTRO.html" ]; then
    printf ', and <a href="TEAMCELL-LITE-INTRO.html">TEAMCELL-LITE-INTRO.html</a> for the generic Teamcell Lite workshop/reference deck (not this Cell'"'"'s current state)'
  fi
  printf '.</p>\n</body>\n</html>\n'
} > "$start_here_out"

if [ -d instructions ]; then
  for f in instructions/APP-INSTRUCTIONS-*.md; do
    [ -f "$f" ] || continue
    surface=$(basename "$f" .md | sed 's/^APP-INSTRUCTIONS-//')
    printf '%s instructions: %s\n' "$surface" "$f"
  done
fi

exit "$EXIT_CODE"
