---
id: TASK-20260101-001
title: "Draft a public contribution guide"
status: done
created: 2026-01-01
created_by: human:alex
owner: human:alex
---

# TASK-20260101-001 — Draft a Public Contribution Guide

## Goal

Create a `CONTRIBUTING.md` file for the open-source project `example-project`
that describes how community members can submit improvements.

## Inputs

- `README.md` — current project overview
- `decisions/DECISION-20260101-001.md` — contribution scope decision

## Allowed Actions

- Create `CONTRIBUTING.md`
- Edit `README.md` to add a link to `CONTRIBUTING.md`
- Run `git diff --check`

## Forbidden Actions

- Do not publish or push to a public remote without a Human Gate
- Do not change the project license
- Do not merge pull requests

## Deliverables

- `CONTRIBUTING.md` — drafted contribution guide
- Completion Record in this task file

## Validation

```bash
git diff --check
git status --short --untracked-files=all
```

- [ ] `CONTRIBUTING.md` exists
- [ ] Markdown is valid (no trailing whitespace errors)
- [ ] Human Gate for publication is created and marked pending

## Definition of Done

- [x] `CONTRIBUTING.md` drafted and committed
- [x] Human Gate created for publication approval
- [x] Validation passed
- [x] Completion Record appended

## Completion Record

```yaml
status: done
completed_by: human:alex
completed_date: 2026-01-02
commit_sha: a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2
pushed_to: origin/main
validation:
  git_diff_check: passed
  deliverables_present: true
human_gate_required: true
human_gate_ref: human-gates/example-human-gate.md
follow_up: Await human gate approval before publishing
build_drift: none
accepted_risks:
  - CONTRIBUTING.md is a draft; not reviewed yet
notes: Task complete; publication awaits gate approval
```
