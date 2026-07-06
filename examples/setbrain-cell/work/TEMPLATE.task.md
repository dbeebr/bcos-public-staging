---
bcos_type: template
id: SETBRAIN-CELL-TASK-TEMPLATE
title: "Task template — setbrain Cell"
status: active
created: 2026-07-05
created_by: bcos-maintainers
surface: work
---

# TASK-YYYYMMDD-NNN — Title

## Goal

One or two sentences: the outcome this task must achieve.

## Inputs

- `path/or/id` — why it is needed

## Allowed Actions

- …

## Forbidden Actions

- …

## Deliverables

- `path` — what it contains

## Validation

```bash
git diff --check
git status --short --untracked-files=all
```

## Definition of Done

- [ ] Deliverables committed
- [ ] Validation passes
- [ ] Completion Record appended
- [ ] Evidence routed to `proofs/` when the claim needs standalone evidence

## Completion Record

```yaml
status: pending
```
