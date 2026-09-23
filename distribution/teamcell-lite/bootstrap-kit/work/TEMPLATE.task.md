---
bcos_type: task
kind: work
surface: work
id: TASK-YYYYMMDD-NNN
title: "Short outcome"
status: draft
work_status: open
created: YYYY-MM-DD
created_by: human-or-agent
created_by_type: human | agent | system
created_by_id: human:<participant-id> | agent:codex | agent:copilot | agent:<id> | system:<id>
created_by_display: "Display Name"
created_by_github: <github-username> | null
on_behalf_of_human_id: human:<participant-id> | null
agent_id: agent:codex | agent:copilot | agent:<id> | null
agent_model: human-or-model
agent_capability_class: local-worker | git-only-worker | chat-reviewer | read-only-observer | automation | null
decision_owner_role: unresolved
---

# Short Outcome

<!-- Save as work/TASK-YYYYMMDD-NNN-<slug>.md. status: draft | reviewed | accepted
     (artifact trust); work_status: open | in-progress | needs-review | done.
     A planner fills Objective, Procedures, Handoff and Start Prompt so an
     agent without the planning conversation can take over. A fact, ID or
     approval the planner does not have is written as "OPEN: <what>", never
     guessed; the ID comes from the file name the task is saved under.
     Before execution the task must pass
     `python3 scripts/validate-completion.py --ready <this file>`; `--fix`
     fills only rule-derivable technical fields (constants, ID from the file
     name, created from the ID, title from the H1, this path in the start
     prompt). Open content, identity or approvals keep it a draft.
     Set work_status: done only together with a complete Completion Record —
     ./scripts/validate-cell.sh rejects placeholders, unchecked Definition-of-
     Done items, unknown commit SHAs and a remote head that does not contain
     the substantive commit. -->

## Objective

What changes when this work is done?

## Context

- `PROJECT.md`
- Add only directly relevant files.

## Procedures

<!-- Planner: check the Procedure Index in CONTEXT_INDEX.md. One line per
     selected procedure, or `none` with a reason. The executor re-checks the
     index itself; this list is a starting point, not loaded content. -->

- `<PROCEDURE-ID>` — `<path>`@`<version or short sha>` — why it applies
- none — reason

## Handoff

- Planned by: <agent id or human>, on <surface/app> (capability at planning:
  <class>) — `created_by` alone does not record the planning surface.
- Executor access needed: <local-worker | git-only-worker | chat-reviewer |
  read-only-observer>; not allowed: <actions outside scope>.
- Return evidence: Completion Record below with `procedures_applied` and
  `closing_learning`, validation results and the verified origin SHA (or
  PENDING with the reason).

## Start Prompt

```text
Repository <owner/repo>, work item work/TASK-YYYYMMDD-NNN-<slug>.md.
Classify your capability from the access you actually have.
1. Follow AGENTS.md "Start Protocol": Cell entry from .bcos/CELL-PROFILE.yaml,
   then this work item.
2. Run python3 scripts/validate-completion.py --ready
   work/TASK-YYYYMMDD-NNN-<slug>.md; apply --fix for technical fields only;
   if it still says NOT READY, stop and report the open items.
3. Re-check the Procedure Index in CONTEXT_INDEX.md; load every procedure
   under "Procedures" (and any other that fits) in full before applying it.
4. Stay inside Objective, Definition Of Done and Handoff limits; stop at a
   human gate.
5. Close with the Completion Record (procedures_applied, closing_learning,
   validation) and report the verified origin SHA or PENDING.
Reasoning: <low | medium | high>.
```

## Definition Of Done

- [ ] Observable result exists.
- [ ] `./scripts/validate-cell.sh` passes (or, in a Cell with an accepted
      validator baseline, `./scripts/validate-cell.sh --baseline <file>`
      reports no new failure — see `playbooks/VALIDATOR-BASELINE.playbook.md`).
- [ ] `git diff --check` passes.
- [ ] Result is committed.
- [ ] Remote commit is verified when an `origin` remote exists.
- [ ] Actor identity fields identify the writer, GitHub account if any, and
      accountable human ownership.
- [ ] Completion Record includes commit evidence, validation evidence, follow-up
      routing, human gate routing, and `recommendation_only_ending: false`.

## Completion Record

Add the final evidence here before setting `work_status: done`.

```yaml
- status: done
- completed_by: agent-or-human-id
- completed_date: YYYY-MM-DD
- substantive_commit_sha: full-sha-containing-deliverables
- completion_record_commit_sha: same | full-sha-if-separate
- remote_head_verified_at_completion: full-origin-main-sha-after-final-push | local-only
- changed_files:
    - path: brief annotation
- validation:
    - ./scripts/validate-cell.sh: pass | fail
    - git diff --check: pass | fail
    - git status --short --untracked-files=all: clean | expected-dirty | unexpected-dirty
- build_drift: none | expected generated artifacts included | housekeeping commit created | unexpected dirty worktree
- follow_up_routing: none | [TASK-or-gate-ids]
- human_gate_required: [] | [gate-or-decision-items]
- recommendation_only_ending: false
- handoff_anchor: commit SHA + Completion Record in task file
- accepted_risks: [] | [risk-items]
- notes: null | "non-obvious context"
- procedures_applied:
    - <PROCEDURE-ID>: loaded <path>@<version-or-short-sha>; applied: <evidence>
    - none: <reason no procedure applied>
- closing_learning: none | "<pattern or correction> — evidence: <work item/commit>; scope: <limit>; route: improve <PROCEDURE-ID> | candidate <path> | follow-up <TASK-ID>"
```

Replace every value above with real evidence; leave nothing in `<...>`,
`YYYY-MM-DD`, `full-sha-...` or `a | b` form. `local-only` is valid for the
remote head only when the Cell has no `origin` remote. If part of the
Definition Of Done is not met, keep `work_status` below `done` and route the
remainder in `follow_up_routing`.

Do not add `session_handoff_id` by default. Commit SHA plus the Completion
Record is the minimal handoff anchor.
