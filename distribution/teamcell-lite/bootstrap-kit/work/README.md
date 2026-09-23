---
bcos_type: doc
kind: work_guide
surface: work
domain: operations
id: WORK-README
title: "Work Guide"
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

# Work Guide

Use one Markdown file per executable unit of work. Start from
`work/TEMPLATE.task.md` and name the file `work/TASK-YYYYMMDD-NNN-<slug>.md`.
Items named `work/WORK-*.md` by earlier versions stay valid; both families
are recognized by `scripts/start-cell.sh` and the validator.

Each work file must identify the actor that wrote it, the GitHub account if
known, and the accountable human when an agent writes for the team.

Work state is separate from artifact trust:

- `status: draft | reviewed | accepted`
- `work_status: open | in-progress | needs-review | done`

`scripts/start-cell.sh` shows as active work the first `in-progress` item,
else the first `needs-review`, else the first `open` item (file-name order).
A `done` item is never shown as active.

A task is executable only when it passes the format check against the
current `work/TEMPLATE.task.md`:

```sh
python3 scripts/validate-completion.py --ready work/TASK-YYYYMMDD-NNN-<slug>.md
```

`--fix` fills only fields a fixed rule derives (constants, the ID from the
file name, `created` from the ID, `title` from the H1, the task's own path in
the start prompt) and marks other missing fields `OPEN: ...`. Missing
content, actor identity, IDs or approvals are never invented: the task stays
a draft until the planner or decision owner supplies them. Correcting
technical fields inside the authorized write scope needs no extra human
approval.

Do not set `work_status: done` until validation and Git evidence are recorded.
`./scripts/validate-cell.sh` (via `scripts/validate-completion.py`) fails a
done item whose Completion Record is missing, still holds template
placeholders, leaves Definition-of-Done boxes unchecked, or names commits
that do not exist or are not contained in the verified remote head. It also
fails the reverse drift: a Completion Record that says done on an item that
is not `work_status: done`.
