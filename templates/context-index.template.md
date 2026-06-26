---
bcos_type: context-index
id: CONTEXT-INDEX-{{CELL-ID}}
purpose: {{Brief description of what this Cell does}}
created_at: {{YYYY-MM-DD}}
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
