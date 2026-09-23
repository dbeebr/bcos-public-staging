#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
FIRST_RUN_PROOF_PATH='reports/verification/FIRST-RUN-INSTALL-HANDOFF.md'
# Rendering is done by the Cell's own scripts/render-instructions.py from the
# Cell's own shared core (templates/PROJECT-INSTRUCTIONS.template.md), profile
# (.bcos/CELL-PROFILE.yaml) and Procedure Index, so the Cell can re-render and
# detect drift later without this checkout. No second rendering path here.

usage() {
  printf 'Usage: %s TARGET_DIRECTORY\n' "$0" >&2
  exit 2
}

die() {
  printf 'ERROR: %s\n' "$1" >&2
  exit 1
}

trim_input() {
  printf '%s' "$1" | sed 's/^[	 ]*//; s/[	 ]*$//'
}

lower_input() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]'
}

ask_optional() {
  prompt=$1
  default=${2:-}
  if [ -n "$default" ]; then
    printf '%s [%s]: ' "$prompt" "$default" >&2
  else
    printf '%s (optional): ' "$prompt" >&2
  fi
  IFS= read -r answer || exit 1
  answer=$(trim_input "$answer")
  if [ -z "$answer" ]; then
    answer=$default
  fi
  printf '%s' "$(trim_input "$answer")"
}

ask_yes_no() {
  prompt=$1
  default=$2
  case "$(lower_input "$default")" in
    y|yes|j|ja) prompt_default='Y/n' ;;
    n|no|nein) prompt_default='y/N' ;;
    *) die "Invalid yes/no default: $default" ;;
  esac
  while :; do
    printf '%s [%s]: ' "$prompt" "$prompt_default" >&2
    IFS= read -r answer || exit 1
    answer=$(lower_input "$(trim_input "$answer")")
    [ -n "$answer" ] || answer=$default
    case "$answer" in
      y|yes|j|ja) printf 'yes'; return ;;
      n|no|nein) printf 'no'; return ;;
      *) printf 'Accepted: y/yes/j/ja or n/no/nein. Please try again.\n' >&2 ;;
    esac
  done
}

ask_choice() {
  prompt=$1
  default=$2
  shift 2
  while :; do
    printf '%s (%s) [%s]: ' "$prompt" "$*" "$default" >&2
    IFS= read -r answer || exit 1
    answer=$(lower_input "$(trim_input "$answer")")
    [ -n "$answer" ] || answer=$default
    for choice in "$@"; do
      if [ "$answer" = "$choice" ]; then
        printf '%s' "$answer"
        return
      fi
    done
    printf 'Accepted: %s. Please try again.\n' "$*" >&2
  done
}

capitalize() {
  first=$(printf '%s' "$1" | cut -c1 | tr '[:lower:]' '[:upper:]')
  rest=$(printf '%s' "$1" | cut -c2-)
  printf '%s%s' "$first" "$rest"
}


# BCOS Project Instruction Inheritance v1.1 (docs/governance/BCOS-PROJECT-
# INSTRUCTION-INHERITANCE-V1-20260717.md): resolve governance profile and
# cell-owner binding from .bcos/CELL-GOVERNANCE.yaml, the same authoritative
# source teamcell-install-preview.py wrote at install time. Never a
# hardcoded fallback -- an unresolved/unbound Cell shows that state
# explicitly.
resolve_governance_facts() {
  gov_file="$target_path/.bcos/CELL-GOVERNANCE.yaml"
  governance_profile='unresolved'
  bound_human_role='unresolved'
  bound_human_id='unresolved'
  bound_human_display='unresolved'
  [ -f "$gov_file" ] || return 0

  value=$(sed -n 's/^governance_profile:[	 ]*//p' "$gov_file" | sed -n '1p' | sed 's/^"//; s/"$//')
  [ -n "$value" ] && [ "$value" != "null" ] && governance_profile=$value

  # Own variable name: $role is the user's role/title answer (step 3).
  owner_role_value=$(sed -n 's/^cell_owner_role:[	 ]*//p' "$gov_file" | sed -n '1p' | sed 's/^"//; s/"$//')
  [ -n "$owner_role_value" ] && [ "$owner_role_value" != "null" ] && bound_human_role=$owner_role_value
  [ "$bound_human_role" = "unresolved" ] && return 0

  human_id=$(awk -v role_key="  $bound_human_role:" '
    $0 == "role_bindings:" { in_rb = 1; next }
    in_rb && index($0, role_key) == 1 { in_role = 1; next }
    in_role && index($0, "    human_id:") == 1 {
      sub("^    human_id:[	 ]*", ""); gsub(/^"|"$/, ""); print; exit
    }
    in_rb && $0 !~ /^  / && $0 != "" { in_rb = 0 }
    in_role && $0 !~ /^    / && $0 != "" { in_role = 0 }
  ' "$gov_file")
  display=$(awk -v role_key="  $bound_human_role:" '
    $0 == "role_bindings:" { in_rb = 1; next }
    in_rb && index($0, role_key) == 1 { in_role = 1; next }
    in_role && index($0, "    display_name:") == 1 {
      sub("^    display_name:[	 ]*", ""); gsub(/^"|"$/, ""); print; exit
    }
    in_rb && $0 !~ /^  / && $0 != "" { in_rb = 0 }
    in_role && $0 !~ /^    / && $0 != "" { in_role = 0 }
  ' "$gov_file")
  [ -n "$human_id" ] && [ "$human_id" != "null" ] && bound_human_id=$human_id
  [ -n "$display" ] && [ "$display" != "null" ] && bound_human_display=$display
}

[ "$#" -eq 1 ] || usage
target_path=$1

[ -d "$target_path" ] || die "Target path does not exist: $target_path"
for required in AGENTS.md CONTEXT_INDEX.md TEAM-PROFILE.md; do
  [ -f "$target_path/$required" ] ||
    die "Target does not look like a BCOS team cell (missing $required): $target_path"
done
renderer="$target_path/scripts/render-instructions.py"
for required in scripts/render-instructions.py .bcos/CELL-PROFILE.yaml templates/PROJECT-INSTRUCTIONS.template.md; do
  [ -f "$target_path/$required" ] ||
    die "This Cell predates the shared instruction renderer (missing $required). Update its Teamcell baseline first; no instructions were generated."
done

if [ -f "$target_path/$FIRST_RUN_PROOF_PATH" ]; then
  detected_state=pending-personalization
else
  detected_state=pending-first-run-agent-proof
fi

printf '%s\n' \
  'BCOS post-install Agent Init and Personalization Wizard' \
  "Detected installer state: $detected_state" \
  'This wizard never writes into external app settings and never runs an agent silently.' \
  'It only generates files inside this cell for you to review and copy yourself.' \
  'Do not enter passwords, tokens, private keys, or other secrets in any answer below.' \
  ''

if [ "$detected_state" = pending-first-run-agent-proof ]; then
  printf '%s\n' \
    "Note: the first-run agent proof and handoff do not yet exist at $target_path/$FIRST_RUN_PROOF_PATH." \
    'You may still generate personalization files now. The calibration light pass (step 8) requires the proof to exist first.' \
    ''
fi

# Step 1 — confirm workspace and repo binding
# Canonical resolution (BRIEF-20260717-004): prefer the installation receipt
# and verified Git remote over brittle prose-line matching against
# TEAM-PROFILE.md's body text. See scripts/resolve-cell-identity.py.
resolver="$REPO_ROOT/scripts/resolve-cell-identity.py"
resolved_json=$(python3 "$resolver" --target-path "$target_path" --field all)
repository=$(printf '%s' "$resolved_json" | python3 -c 'import json,sys; d=json.load(sys.stdin); v=d["repository"]["value"]; print(v if v else "")')
cell_name=$(printf '%s' "$resolved_json" | python3 -c 'import json,sys; d=json.load(sys.stdin); v=d["display_name"]["value"]; print(v if v else "")')
repository_resolved=$(printf '%s' "$resolved_json" | python3 -c 'import json,sys; d=json.load(sys.stdin); print("true" if d["repository"]["resolved"] else "false")')
cell_name_resolved=$(printf '%s' "$resolved_json" | python3 -c 'import json,sys; d=json.load(sys.stdin); print("true" if d["display_name"]["resolved"] else "false")')
if [ "$repository_resolved" != true ]; then
  repository='unresolved (no installation receipt, git remote, or structured project metadata found)'
  printf 'WARNING: repository identity could not be resolved from any canonical source.\n' >&2
fi
if [ "$cell_name_resolved" != true ]; then
  cell_name='unresolved (no PROJECT.md title, Team Profile field, or repository slug available)'
  printf 'WARNING: Cell/project display name could not be resolved from any canonical source.\n' >&2
fi
on_behalf_of_human_id=$(printf '%s' "$resolved_json" | python3 -c 'import json,sys; d=json.load(sys.stdin); v=d["on_behalf_of_human_id"]["value"]; print(v if v else "")')

printf 'Target workspace: %s\n' "$target_path"
printf 'Detected repository binding: %s\n' "$repository"
if [ "$(ask_yes_no 'Confirm this is the workspace you intend to personalize?' 'yes')" = no ]; then
  printf 'Personalization cancelled. No files were written.\n'
  exit 0
fi

# Step 2 — choose target agent/app surfaces (no surface pre-selected)
selected_surfaces=''
for surface in copilot chatgpt claude gemini other; do
  label=$(capitalize "$surface")
  if [ "$(ask_yes_no "Generate instructions for $label?" 'no')" = yes ]; then
    selected_surfaces="$selected_surfaces $surface"
  fi
done
selected_surfaces=$(trim_input "$selected_surfaces")
if [ -z "$selected_surfaces" ]; then
  printf 'No app surfaces selected. Skipping instruction-block generation.\n'
fi

# Step 2b — role of the agents that will use this project block. Role is
# separate from app/provider and from actual host capability: the rendered
# block always tells the agent to classify its capability from real access.
agent_role=both
if [ -n "$selected_surfaces" ]; then
  agent_role=$(ask_choice 'Role of the agents using this project block' 'both' planner executor both)
fi

# Step 3 — collect a small, bounded set of non-sensitive personalization facts
printf '\nPersonalization facts (all optional; leave blank to skip):\n'
tone=$(ask_optional 'Preferred communication tone' '')
language=$(ask_optional 'Primary working language' '')
timezone=$(ask_optional 'Timezone for scheduling references' '')
role=$(ask_optional 'Role/title in one short phrase' '')
tone=${tone:-Not specified}
language=${language:-Not specified}
timezone=${timezone:-Not specified}
role=${role:-Not specified}

created_date=$(date '+%Y-%m-%d')
generated_files=''
resolve_governance_facts

render_report=''
if [ -n "$selected_surfaces" ]; then
  # Steps 4-6 — one render call: the budgeted project block
  # (instructions/PROJECT-INSTRUCTIONS.md), the thin activation note per
  # selected surface and the first-run prompt. ChatGPT, when selected, sets
  # the tightest known budget (target 7200, hard limit 8000); the renderer
  # never cuts rules and refuses instead.
  budget_surface=generic
  case " $selected_surfaces " in *' chatgpt '*) budget_surface=chatgpt ;; esac
  surfaces_csv=$(printf '%s' "$selected_surfaces" | tr ' ' ',')
  if ! render_report=$(PYTHONDONTWRITEBYTECODE=1 python3 "$renderer" --root "$target_path" generate \
      --surface "$budget_surface" --role "$agent_role" --surfaces "$surfaces_csv" \
      --fact "cell_name=$cell_name" --fact "repository=$repository" --fact "target_path=$target_path" \
      --fact "tone=$tone" --fact "language=$language" --fact "timezone=$timezone" \
      --fact "role_title=$role" --fact "created_date=$created_date" \
      --fact "governance_profile=$governance_profile" --fact "bound_human_role=$bound_human_role" \
      --fact "bound_human_display=$bound_human_display" --fact "bound_human_id=$bound_human_id" 2>&1); then
    printf '%s\n' "$render_report" >&2
    die "Instruction rendering refused or failed (see above). No personalization record was written."
  fi
  printf '%s\n' "$render_report"
  for f in $(printf '%s\n' "$render_report" | sed -n 's/^Generated: //p'); do
    generated_files="$generated_files $target_path/$f"
  done
fi

# Lifecycle truth (BRIEF-20260717-005 W1): distinguish "the file exists"
# from "a human actually read it" from "a human pasted it into external app
# settings". Every generated file is `generated` by construction. The two
# remaining states are always self-reported, never BCOS-verified.
reviewed=false
activated_self_reported=false
if [ -n "$selected_surfaces" ]; then
  if [ "$(ask_yes_no 'Did you review the generated instruction blocks before pasting them anywhere?' 'no')" = yes ]; then
    reviewed=true
  fi
  if [ "$(ask_yes_no 'Did you copy/paste the generated instruction blocks into the selected app(s)? (self-reported only)' 'no')" = yes ]; then
    activated_self_reported=true
  fi
fi
# Legacy field name kept for any existing readers of this record.
user_confirmed_pasted=$activated_self_reported

# Step 7 — first agent proof: this wizard never introduces a second dispatch mechanism
printf '\nThis wizard does not dispatch an agent. Start your first agent session in the Cell\n'
printf 'with FIRST-RUN-AGENT-PROMPT.md (generated above when you selected a surface) and run ./scripts/start-cell.sh.\n'

# Step 8 — calibration light pass from TASK-007 (invoke only, never auto-run agent tests)
calibration_status=skipped-protocol-not-available
protocol_path="$REPO_ROOT/docs/operations/BCOS-AGENT-ONBOARDING-CALIBRATION-PROTOCOL-20260702.md"
if [ -f "$protocol_path" ]; then
  calibration_status=available-run-manually
  printf '\nCalibration protocol found: %s\n' "$protocol_path"
  printf 'This wizard does not auto-run agent tests. Run the light pass manually against the agent that completed the first-run proof, then record pass/fail per test in the proof handoff.\n'
else
  printf '\nNo calibration protocol is bundled with this checkout. Skipping calibration light pass.\n'
fi

# Step 9 — record what happened as a proof handoff artifact
mkdir -p "$target_path/reports/verification"
personalization_record="$target_path/reports/verification/POST-INSTALL-PERSONALIZATION.md"
{
  printf -- '---\n'
  printf 'bcos_type: report\n'
  printf 'kind: post_install_personalization_record\n'
  printf 'surface: history\n'
  printf 'id: POST-INSTALL-PERSONALIZATION\n'
  printf 'title: "Post-Install Agent Init and Personalization Record"\n'
  printf 'created_by: personalize-team-cell\n'
  printf 'created_by_type: system\n'
  printf 'created_by_id: system:personalize-team-cell\n'
  printf 'created_by_display: "BCOS Personalization Wizard"\n'
  printf 'created_by_github: null\n'
  printf 'on_behalf_of_human_id: %s\n' "${on_behalf_of_human_id:-null}"
  printf 'agent_model: interactive-shell\n'
  printf 'created: %s\n' "$created_date"
  printf 'status: draft\n'
  printf -- '---\n\n'
  printf '# Post-Install Agent Init and Personalization Record\n\n'
  printf 'This record is self-reported and generated locally. It is not proof that any\n'
  printf 'external app settings were actually configured.\n\n'
  printf '```yaml\n'
  printf 'target_workspace: %s\n' "$target_path"
  printf 'resolved_repository: "%s"\n' "$repository"
  printf 'resolved_cell_name: "%s"\n' "$cell_name"
  printf 'detected_installer_state: %s\n' "$detected_state"
  printf 'selected_surfaces: "%s"\n' "${selected_surfaces:-none}"
  printf 'generated_files:\n'
  if [ -n "$generated_files" ]; then
    for f in $generated_files; do printf '  - %s\n' "$f"; done
  else
    printf '  []\n'
  fi
  printf 'instruction_lifecycle:\n'
  printf '  generated: %s\n' "$([ -n "$selected_surfaces" ] && echo true || echo false)"
  printf '  reviewed: %s\n' "$reviewed"
  printf '  activated_self_reported: %s\n' "$activated_self_reported"
  printf 'user_confirmed_pasted: %s\n' "$user_confirmed_pasted"
  printf 'verification: self-reported\n'
  printf 'calibration_light_pass_status: %s\n' "$calibration_status"
  printf 'render:\n'
  printf '  renderer: scripts/render-instructions.py\n'
  printf '  agent_role: %s\n' "$agent_role"
  printf '  budget: "%s"\n' "$(printf '%s\n' "$render_report" | sed -n 's/^Paste block size: //p' | sed 's/"/'"'"'/g')"
  printf 'personalization_facts:\n'
  printf '  tone: "%s"\n' "$tone"
  printf '  language: "%s"\n' "$language"
  printf '  timezone: "%s"\n' "$timezone"
  printf '  role: "%s"\n' "$role"
  printf '```\n'
} > "$personalization_record"
printf '\nPersonalization record written: %s\n' "$personalization_record"

if [ -f "$target_path/$FIRST_RUN_PROOF_PATH" ]; then
  printf '\nAn existing proof handoff was found at %s/%s.\n' "$target_path" "$FIRST_RUN_PROOF_PATH"
  printf 'This wizard does not rewrite that committed handoff; the personalization record above is the durable link. Reference it from a follow-up commit if the handoff needs updating.\n'
fi

printf '\nDone.\n'
if [ -n "$selected_surfaces" ]; then
  printf 'Review the generated files before committing or pasting anything:\n'
  for f in $generated_files; do
    printf '  %s\n' "$f"
  done
fi
