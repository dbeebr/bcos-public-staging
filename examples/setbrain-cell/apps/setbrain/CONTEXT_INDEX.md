---
bcos_type: index
id: SETBRAIN-APP-CONTEXT-INDEX
title: "Context Index — setbrain App"
status: active
created: 2026-07-05
created_by: bcos-maintainers
surface: apps
app_id: setbrain
related:
  - README.md
---

# Context Index — setbrain App

Read this file whenever a task touches `apps/setbrain/`.

## Read first

1. `README.md` — rules and boundary
2. the active Cell-root `work/` task
3. only the local files the task needs

## Local routes

| Need | Read or write |
|---|---|
| Genre knowledge | `knowledge/genre-notes.md` |
| Venue knowledge | `knowledge/venue-profiles.md` |
| Generate a set brief | `prompts/set-brief.prompt.md` |
| App-specific analysis | `reports/` |
| App-specific evidence | `proofs/` |

## Boundary

Cell governance (tasks, gates, decisions, handoffs) stays at the Cell root.
Only setbrain's own domain content lives here. Prompts reference knowledge-file
headings — restructuring knowledge files requires checking `prompts/` in the
same task.
