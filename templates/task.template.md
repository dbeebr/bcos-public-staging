---
id: TASK-YYYYMMDD-NNN
title: "Short description of what this task accomplishes"
status: draft
created: YYYY-MM-DD
created_by: human-or-agent-id
owner: human-or-agent-id
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

## Definition of Done

- [ ] All deliverables exist and are committed
- [ ] Validation passes
- [ ] Completion Record is appended to this file
- [ ] Changes pushed to origin

## Completion Record

```yaml
status: pending
```
