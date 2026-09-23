---
bcos_type: doc
kind: agent_adapter
surface: playbooks
domain: operations
id: COPILOT-INSTRUCTIONS
title: "Teamcell Lite Copilot Instructions"
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

# Teamcell Lite Copilot Instructions

Before writing, follow `AGENTS.md` "Start Protocol": run
`git status --short --untracked-files=all`, read the Cell entry listed under
`session_entry` in `.bcos/CELL-PROFILE.yaml`, then the assigned work item or
human gate. Check the Procedure Index in `CONTEXT_INDEX.md` when work starts,
at a handover, at a phase change and when a new finding appears; load a
matching procedure in full before applying it (naming it is not using it).

Before making any status, done, next-step, completion, or governance claim,
identify the repo, branch, and relevant work item or human gate; read the
specific artifact; distinguish user-reported status from Git-verified status;
load only relevant files; and route the next action into `work/`,
`human-gates/`, `history/`, `playbooks/`, a skill/tool action, or explicit
`none`.

Use only canonical BCOS Phase-1 `bcos_type` values. Put product specificity in
`kind`, `surface`, and lifecycle fields.

Every work item, human gate, playbook, and verification report must carry actor
identity fields: `created_by_type`, `created_by_id`, `created_by_display`,
`created_by_github`, and `on_behalf_of_human_id`. When Copilot or another agent
writes for the team, also include `agent_id`, `agent_model`, and
`agent_capability_class` (`local-worker | git-only-worker | chat-reviewer |
read-only-observer | automation` — the access you actually have, not the
product name). Human gates also require `decision_class`,
`decision_owner_role`, `decision_owner_id`, `decision_owner_display`, and
`reviewer_ids`; an unresolved role or unbound owner stays visibly `unresolved`
/ `null`, never a guessed name.

Write raw intake only by appending to `inbox/INBOX.md`. Put executable work in
`work/` (`work/TASK-YYYYMMDD-NNN-<slug>.md` from `work/TEMPLATE.task.md`),
human decisions in `human-gates/`, durable evidence in `history/`, and
reusable procedures in `playbooks/`. Use `playbooks/AGENT-ROUTING.playbook.md`
when placement is not obvious. Before executing a work item, run
`python3 scripts/validate-completion.py --ready <path>`: fix only what `--fix`
derives by rule, and stop on open content, identity, IDs or approvals
instead of guessing them.

Run `./scripts/validate-cell.sh` and `git diff --check` before reporting work.
A failure that existed before your change is known, not fixed: compare with
`./scripts/validate-cell.sh --baseline <file>` per
`playbooks/VALIDATOR-BASELINE.playbook.md`. Do not claim completion without
actor identity fields and Git evidence.

Before setting `work_status: done`, fill the Completion Record with status,
completed actor/date, substantive commit SHA, completion-record commit SHA or
`same`, verified remote HEAD SHA, changed files with annotations, validation
results, build drift, follow-up routing, human gates required,
`recommendation_only_ending: false`, `handoff_anchor: commit SHA + Completion
Record in task file`, accepted risks, notes, `procedures_applied` (what you
loaded and applied, with evidence, or `none: <reason>`) and `closing_learning`
(`none` or a routed pattern). Do not add
`session_handoff_id` by default. The validator rejects a done item with a
placeholder, unchecked Definition-of-Done item or unverifiable SHA, and a
Completion Record that says done while `work_status` is not `done`.

`AGENTS.md` is the authoritative contract; this file only adapts it for
Copilot and must not contradict it.
