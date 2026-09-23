---
bcos_type: index
id: CONTEXT-INDEX-{{CELL-ID}}
title: "Context Index — {{Cell Name}}"
status: active
created: {{YYYY-MM-DD}}
created_by: {{human-or-agent-id}}
surface: project
purpose: {{Brief description of what this Cell does}}
updated_at: {{YYYY-MM-DD}}
---

# Context Index — {{Cell Name}}

## Purpose

{{One or two sentences describing this Cell's purpose and scope.}}

## Entry Points

Read these first when entering this Cell:

| File | Why to read it |
|---|---|
| `README.md` | {{Overview and orientation}} |
| `{{path/to/active-task.md}}` | {{Current active task}} |
| `{{path/to/key-decision.md}}` | {{Key decision affecting current work}} |

## Load When

| Situation | Read |
|---|---|
| Starting a new task | Entry points above, plus `templates/task.template.md` |
| Continuing from a handoff | The handoff record, then entry points |
| Making a decision | `templates/decision.template.md`, plus relevant prior decisions |
| Reviewing completion | The task file, then `templates/proof.template.md` |

## Procedure Index

Reusable procedures available in this Cell. Check this list when a task
starts, at a handover, at a phase change and when a new finding appears;
load the full file before applying an entry. (A Teamcell Lite Cell generates
this section from each procedure's frontmatter with
`scripts/render-instructions.py index --write`.)

| ID | Kind | Use when | Not when | Phase | Path |
|---|---|---|---|---|---|
| {{PROCEDURE-ID}} | {{skill / playbook / workflow}} | {{concrete situation}} | {{nearest situation where it does not apply}} | {{plan / execute / close}} | `{{playbooks/name.playbook.md}}` |

## Do Not Load by Default

These files exist but should not be loaded unless specifically needed:

- `{{path/to/archive/}}` — historical records; load only when investigating past decisions
- `{{path/to/completed-tasks/}}` — completed tasks; load only for reference or audit

## Related Files

| File | Role |
|---|---|
| `templates/` | Artifact templates for tasks, decisions, handoffs, proofs, human gates |
| `decisions/` | Recorded decisions that affect current work |
| `handoffs/` | Handoff records for session or contributor transitions |
| `proofs/` | Evidence records for completed work |

## Routing Notes

{{Optional: any Cell-specific routing guidance. For example:}}

{{- "All tasks that change public-facing content require a Human Gate."}}
{{- "Agent sessions should load the most recent handoff before starting work."}}
{{- "Decisions in `decisions/` override any conflicting guidance in chat or session history."}}
