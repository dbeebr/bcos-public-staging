---
bcos_type: index
id: SETBRAIN-CELL-CONTEXT-INDEX
title: "Context Index — setbrain Cell"
status: active
created: 2026-07-05
created_by: bcos-maintainers
surface: project
related:
  - README.md
  - AGENTS.md
---

# Context Index — setbrain Cell

## Entry Points

| File | Why |
|---|---|
| `README.md` | orientation and the worked example chain |
| `PROJECT.md` | purpose, scope, trust model |
| `AGENTS.md` | agent operating contract |
| `TEAM.md` | who decides, who reviews |
| `apps/setbrain/README.md` | the app package |

## Load When

| Situation | Read |
|---|---|
| Starting new work | entry points + `work/TEMPLATE.task.md` |
| Continuing a session | latest file in `handoffs/`, then the referenced task |
| Touching setbrain content | `apps/setbrain/CONTEXT_INDEX.md` |
| Making a decision | relevant prior files in `decisions/` |
| Verifying a completion claim | the task file, then the proof it references |

## Do Not Load by Default

- `history/` — chronological record; load only when investigating what happened
- `inbox/INBOX.md` older entries — processed intake is history, not context

## Routes

| Surface | Holds |
|---|---|
| `inbox/` | raw intake (append-only) |
| `work/` | executable tasks |
| `decisions/` | resolved choices |
| `human-gates/` | human judgment checkpoints |
| `reports/` | analysis |
| `proofs/` | completion evidence |
| `handoffs/` | continuation records |
| `history/` | what happened |
| `library/` | what to reuse |
| `playbooks/` | how to repeat procedures |
| `apps/setbrain/` | the active domain capability |
