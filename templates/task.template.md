---
bcos_type: task
id: TASK-YYYYMMDD-NNN
title: "Short description of what this task accomplishes"
status: draft
work_status: open            # open | in-progress | needs-review | done
created: YYYY-MM-DD
created_by: human-or-agent-id
owner: human-or-agent-id
surface: work
---

# TASK-YYYYMMDD-NNN — Title

## Goal

State the specific outcome this task must achieve. One or two sentences.

## Inputs

List what must be read or available before execution begins:

- `FILE.md` — why it is needed
- Source decision ID or data

## Allowed Actions

List what is permitted:

- Edit `output-file.md`
- Run `./scripts/validate.sh`

## Forbidden Actions

List what is explicitly off-limits:

- Do not publish or push to a public remote
- Do not change files outside the listed scope
- Do not accept or close Human Gates

## Deliverables

List the expected outputs:

- `output-file.md` — description of what it contains
- Completion Record in this task file

## Validation

Commands to run before declaring completion:

```bash
git diff --check
git status --short --untracked-files=all
```

Additional validation specific to this task:

- [ ] Deliverable exists and passes structural check
- [ ] No forbidden actions were taken

## Procedures

Selected procedures from the Cell's Procedure Index (`CONTEXT_INDEX.md`),
one line each with path and version, or `none` with a reason. The executor
re-checks the index itself; a listed procedure is not yet loaded content.

- `<PROCEDURE-ID>` — `<path>`@`<version>` — why it applies

## Handoff

- Planned by: <agent or human>, on <surface/app>
- Executor access needed: <capability class>; not allowed: <...>
- Start prompt: repository, this task's path, "follow the Cell entry and
  this task; load the procedures above in full; close with the Completion
  Record" — enough for an agent that never saw the planning conversation.

## Definition of Done

- [ ] All deliverables exist and are committed
- [ ] Validation passes
- [ ] Completion Record is appended to this file
- [ ] Changes pushed to origin

## Completion Record

Fill this only when the Definition of Done is met, then set
`work_status: done` in the frontmatter in the same commit. Replace every
placeholder with real evidence (`schemas/completion-record.schema.md`).

```yaml
status: pending               # done once complete
completed_by: <human-or-agent-id>
completed_date: YYYY-MM-DD
commit_sha: <full 40-character SHA of the substantive commit>
changed_files:
  - <path>: <what changed and why>
validation:
  git diff --check: pass
recommendation_only_ending: false
follow_up: none
human_gate_required: []
accepted_risks: []
notes: null
procedures_applied:
  - <PROCEDURE-ID>: loaded <path>@<version>; applied: <evidence>
closing_learning: none
```
