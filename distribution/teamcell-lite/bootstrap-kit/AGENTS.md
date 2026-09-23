---
bcos_type: doc
kind: agent_contract
surface: playbooks
domain: operations
id: TEAMCELL-LITE-AGENTS
title: "Teamcell Lite Agent Contract"
status: active
created: 2026-06-24
created_by: codex
created_by_type: agent
created_by_id: agent:codex
created_by_display: "Codex"
created_by_github: null
on_behalf_of_human_id: "human:{{CELL_OWNER_ID}}"
agent_id: agent:codex
agent_model: gpt-5
agent_capability_class: local-worker
---

# Teamcell Lite Agent Contract

Preserve context coherence. Keep work inspectable. Leave Git evidence.

## Start Protocol

Before writing:

1. Confirm the repository and branch.
2. Run `git status --short --untracked-files=all`.
3. Read the Cell entry: the files listed under `session_entry` in
   `.bcos/CELL-PROFILE.yaml`, in that order (this file is one of them).
4. Read the assigned work item or human gate. Before executing a work item,
   run `python3 scripts/validate-completion.py --ready <path>`: fix only what
   `--fix` derives by rule; if it still reports open items, the item is a
   draft — stop and report them instead of guessing.
5. Check the Procedure Index in `CONTEXT_INDEX.md` against the work and load
   every matching procedure in full (see "Procedures").
6. Confirm the artifact's actor identity fields before creating or completing it.
7. Read only directly relevant files.

A work item's start prompt points to this entry instead of repeating a file
list; an agent that never saw the planning conversation must be able to
start from the repository, the work item path and this protocol alone.

## Planning, Handoff and Roles

Planning and execution are work steps, not products or models. Planning
may create and persist work items and hand authorized execution over;
implementation happens in the execution step. Role, capability class and
authority stay separate: persist only with the write access you actually
have (otherwise deliver a copy/paste artifact, `persisted: false`), and
authority comes only from the decision owner and the gates recorded in the
work item — never from role, capability, task wording or a model's
suggestion. A handoff never widens scope or permissions, and no model
suggestion dispatches work on its own. Correcting rule-derivable technical
fields inside the authorized write scope needs no extra human approval.

A planner writes the work item in the format of the current
`work/TEMPLATE.task.md` (`.bcos/CELL-PROFILE.yaml` `task_template`): read it
from the repository, or — without access — from a planning context pack
(`python3 scripts/render-instructions.py context-pack --role planner`), and
name its version. Facts, IDs or approvals the planner does not have are
written as `OPEN: <what>`, never invented. An executor pack for a task that
fails the format check is refused (`context-pack --role executor --task ...`
exits 5).

## Fetch/Read Gate

Before any status, done, next-step, completion, or governance claim about
teamcell-governed work:

1. Identify the repository, current branch, and relevant work item, human gate,
   or brief by ID.
2. Read the specific artifact the claim is about. Do not rely on chat memory or
   a prior session's output.
3. Distinguish user-reported status from Git-verified status. Use wording such
   as "User reports X; Git verification pending" or "Git confirms X at commit
   SHA `<sha>`."
4. Load only directly relevant files.
5. Route the resulting next action into `work/`, `human-gates/`, `history/`,
   `playbooks/`, a skill/tool action, or explicit `none`.

Do not leave BCOS-governed follow-up as recommendation-only prose.

## Procedures

Procedures are the Cell's skills, playbooks and workflows. The available
ones are listed in the generated Procedure Index in `CONTEXT_INDEX.md`; each
entry says when to use it, when not, the phase, its path and its package.

- **Select** when a work item or sub-task starts, at every handover
  (planner to executor, agent to agent), at a phase change, and when a new
  finding appears during the work (for example a validator failure that
  makes `VALIDATOR-BASELINE` relevant). An explicit `none` with a reason is
  valid. Do not re-check on every chat message. When nothing fits, say "no
  matching installed procedure found" and label any general draft as such;
  a missing index entry alone does not prove that a specific package is
  absent, and with an unreadable, routed or stale index say you cannot tell.
- **Load** the full procedure file before applying it. An index entry, a
  path or a planner's selection is not loaded content. Without file or Git
  access, ask for the file (or a context pack from
  `scripts/render-instructions.py context-pack`) instead of guessing.
- **Apply and record.** A planner lists the selected procedures (ID +
  path/version, or `none` + reason) in the work item's `Procedures` section.
  The executor re-checks the index itself and records in the Completion
  Record's `procedures_applied` what it actually loaded and applied, with
  evidence. Naming a procedure is not using it.
- **Close.** The Completion Record's `closing_learning` names a reusable
  pattern or correction with evidence and scope limit and routes it: improve
  an existing procedure, propose a candidate (a follow-up work item, or the
  Plus learning-candidates workflow when installed), or `none`. There is no
  duty to find something every time, and nothing is promoted or activated
  automatically.
- **Maintain the index.** A procedure file carries its own index metadata
  (`procedure_kind`, `use_when`, `not_when`, `phase`, `package`, `status`).
  After a procedure is accepted, changed or removed, or a package is
  installed, run `python3 scripts/render-instructions.py index --write`;
  `./scripts/validate-cell.sh` fails on a stale index. Only `status: active`
  procedures that exist in this Cell are listed.
- **Rendered instructions.** Files in `instructions/` are rendered from the
  shared core `templates/PROJECT-INSTRUCTIONS.template.md`, the Cell profile
  and the index. Never edit them by hand; re-render with
  `python3 scripts/render-instructions.py refresh` and re-paste. Whether a
  block is active in an external app stays self-reported.

## Actor Identity Rules

Every work, human-gate, playbook, and verification-report artifact must identify
the actor that wrote it and the accountable human when an agent acts for the
team.

Required fields:

```yaml
created_by_type: human | agent | system
created_by_id: human:<participant-id> | agent:codex | agent:copilot | agent:<id> | system:<id>
created_by_display: "<Participant Display Name>" | "Codex" | "GitHub Copilot"
created_by_github: <github-username> | null
on_behalf_of_human_id: human:<participant-id> | null
```

`<participant-id>` is a stable `human:<id>` value already registered in
`TEAM-PROFILE.md`'s `participants[]` array. Never hardcode a real person's
name here as a template default — see `TEAM-PROFILE.md`'s own worked example
(role-based, fictional) for the pattern.

Agent-written artifacts must also include:

```yaml
agent_id: agent:codex | agent:copilot | agent:<id>
agent_model: <model-or-tool>
agent_capability_class: local-worker | git-only-worker | chat-reviewer | read-only-observer | automation
```

`agent_capability_class` records the access the writer actually had, not its
product or model name:

- `local-worker`: local repository, shell and Git access.
- `git-only-worker`: Git connector/API access without a local shell.
- `chat-reviewer`: no verifiable repository write access; produces
  copy/paste artifacts marked pending-verification.
- `read-only-observer`: inspects and reports only.
- `automation`: a script or scheduled job acting without an interactive agent.

The earlier values `coding-agent` and `design-agent` are legacy: existing
artifacts keep them (the validator warns), new artifacts use the list above.

Human-written artifacts use `agent_id: null`, `agent_model: human`, and
`agent_capability_class: null`.

Human gates must additionally name the accountable decision owner by role and
reviewers:

```yaml
decision_class: <one of the ten canonical decision classes listed in
  .bcos/CELL-GOVERNANCE.yaml.template's decision_owner_roles — see this
  Cell's own docs/teamcell-gate-matrix.md for which need a gate>
decision_owner_role: <role-slug from .bcos/CELL-GOVERNANCE.yaml's
  decision_owner_roles map> | unresolved
decision_owner_id: human:<participant-id> | null
decision_owner_display: "<Participant Display Name>" | null
reviewer_ids:
  - human:<participant-id>
```

`decision_owner_role: unresolved` means no role has been chosen for this
decision class yet — the gate is blocked pending role assignment. A named
role with `decision_owner_id: null` means the role exists but no human is
currently bound to it — the gate is blocked pending appointment. Both are
first-class, visible states. Neither may ever silently default to a name —
not any prior Cell's owner, not the template's own historical example, and
not any other real person not explicitly bound to that role in
`.bcos/CELL-GOVERNANCE.yaml`. See `human-gates/TEMPLATE.human-gate.md` and
`.bcos/CELL-GOVERNANCE.yaml.template`.

## Write Rules

- Append raw input to `inbox/INBOX.md`; do not rewrite old entries.
- Create executable work in `work/` from `work/TEMPLATE.task.md`, named
  `work/TASK-YYYYMMDD-NNN-<slug>.md` (earlier `work/WORK-*.md` items stay
  valid).
- Create human decisions in `human-gates/` from
  `human-gates/TEMPLATE.human-gate.md`.
- Move durable evidence to `history/` after it is decided, reviewed, or recorded.
- Put reusable procedures in `playbooks/`.

## Artifact Placement Decision

Before creating files, classify the artifact by intent:

- Raw unprocessed input: append to `inbox/INBOX.md`.
- Executable work with outcome, gates, and validation: create a task in `work/`.
- Human decision required before safe implementation: create a gate in
  `human-gates/`.
- Durable evidence, review, report, or accepted decision: record it in
  `history/`.
- Reusable procedure or repeatable agent workflow: create a playbook in
  `playbooks/`.
- Domain knowledge concept: first create a work item in `work/`; do not create
  a new knowledge or context surface until a human gate accepts the target
  placement.
- Active maintained domain capability (after an accepted gate): promote to
  `apps/<app-id>/`; passive proven patterns are distilled to `library/`. See
  `docs/EXPANSION-PROFILE.md`.
- Repo-level agent behavior: update `AGENTS.md` and, when allowed by the task,
  `.github/copilot-instructions.md`.
- Tool-specific or domain-specific agent guidance: create a playbook first;
  promote later only after review.
- MCP configuration: create a human gate first; include no secrets and assume
  no runtime until accepted.

A domain brain (for example, a brand brain) is first domain knowledge work
inside the team cell. It must be captured as a work item first. Its later
target surface requires the decision owner's human gate before implementation;
an actively queried capability routes to `apps/<app-id>/`.

Use `playbooks/AGENT-ROUTING.playbook.md` when the placement is not obvious.

## Type Rules

New Markdown files must use one of the canonical BCOS Phase-1 `bcos_type`
values:

`task`, `proposal`, `decision`, `council`, `review`, `brief`, `doc`,
`synthesis`, `report`, `record`, `skill`, `schema`, `template`, `index`,
`state`, or `genesis_record`.

Do not create convenience types such as `project`, `inbox`, `human_gate`, or
`playbook`. Put specificity in `kind`, `surface`, `domain`, `work_status`, or
`gate_status`.

Two further types exist only for personalization sources under `templates/`
and the files generated from them: `app_instruction_block`
(`instructions/*.md`) and `prompt` (`FIRST-RUN-AGENT-PROMPT.md`). Do not use
them for other artifacts.

Lifecycle fields are separate from the type:

- `status` (artifact trust): `draft | reviewed | accepted`; guides, contracts
  and indexes that are in force use `active`.
- `work_status` (work items only): `open | in-progress | needs-review | done`.
- `gate_status` (human gates only): see `human-gates/README.md`.

## Completion

A work item is not done until its Definition of Done is satisfied, validation is
recorded, actor identity fields are present, changes are committed, and the
remote commit is verified when an `origin` remote exists. Do not claim
team-ready status before a multi-committer proof exists.

Before setting `work_status: done`, the work item's Completion Record must
include:

- `status: done`
- `completed_by` or `agent`
- `completed_date`
- `substantive_commit_sha` or `commit_sha`
- `completion_record_commit_sha`, or `same` when the Completion Record is in
  the substantive commit
- `remote_head_verified_at_completion` or `remote_head_verification_sha`: the
  full origin SHA verified after the push, which must contain the substantive
  commit; `local-only` only when the Cell has no `origin` remote
- `changed_files` with annotations
- `validation` results, including `./scripts/validate-cell.sh` and
  `git diff --check`
- `build_drift`
- `follow_up_routing` or `follow_up_tasks`
- `human_gate_required`
- `recommendation_only_ending: false`
- `handoff_anchor: commit SHA + Completion Record in task file`
- `accepted_risks`
- `notes`
- `procedures_applied`: per procedure `<ID>: loaded <path>@<version or short
  sha>; applied: <evidence>`, or `none: <reason>`
- `closing_learning`: `none`, or the pattern/correction with evidence, scope
  limit and route

Do not introduce `session_handoff_id` by default. Commit SHA plus the
Completion Record is the minimal handoff anchor.

`./scripts/validate-cell.sh` enforces this through
`scripts/validate-completion.py`: a done work item with a missing,
placeholder or unverifiable Completion Record fails, and so does a
Completion Record that says done while `work_status` is not `done`. Keep
unfinished Definition-of-Done items open, or route them to a follow-up item,
instead of marking the work done. A `procedures_applied` entry that claims
`applied` without `loaded`, or names a procedure that does not exist in this
Cell, fails; Completion Records written before these two fields existed only
warn.

## Validation Baseline

A validator failure that already existed before your change is known, not
fixed. When a Cell carries accepted pre-existing failures, compare by exact
failure identity with `./scripts/validate-cell.sh --baseline <file>` and
follow `playbooks/VALIDATOR-BASELINE.playbook.md`. A new failure blocks even
when the total count is unchanged. Never use a baseline to legitimize a
defect in a fresh Cell.
