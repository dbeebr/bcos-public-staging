---
bcos_type: task
id: TASK-20260701-001
title: "Seed the set-brief guide and first genre notes in setbrain"
status: done
work_status: done
created: 2026-07-01
created_by: alex-rivera
created_by_type: human
created_by_id: human:alex-rivera
created_by_display: "Alex Rivera"
owner: agent:example-agent
surface: work
related:
  - ../human-gates/HUMAN-GATE-20260630-001-set-brief-content-posture.md
  - ../decisions/DECISION-20260701-001-setbrain-app-package.md
  - ../proofs/PROOF-20260701-001-set-brief-guide-validation.md
---

# TASK-20260701-001 — Seed the Set-Brief Guide and First Genre Notes

*(Fictional example.)*

## Goal

setbrain answers its first real question: "write a set brief for a booking" —
backed by a canonical brief format and genre notes for house and techno.

## Inputs

- `../human-gates/HUMAN-GATE-20260630-001-set-brief-content-posture.md` — Option A: text-only briefs
- `../decisions/DECISION-20260701-001-setbrain-app-package.md` — app-package placement
- `../apps/setbrain/CONTEXT_INDEX.md` — where content routes inside the package

## Allowed Actions

- Create files under `apps/setbrain/knowledge/` and `apps/setbrain/prompts/`.
- Append a Completion Record to this file.

## Forbidden Actions

- Do not embed or copy photos (gate Option A).
- Do not create new top-level surfaces.
- Do not resolve or edit human gates.

## Deliverables

- `apps/setbrain/knowledge/genre-notes.md`
- `apps/setbrain/knowledge/venue-profiles.md`
- `apps/setbrain/prompts/set-brief.prompt.md`

## Validation

```bash
git diff --check
git status --short --untracked-files=all
```

- [x] All three deliverables exist and carry routing frontmatter
- [x] No photo embeds anywhere (gate Option A respected)

## Definition of Done

- [x] Deliverables committed
- [x] Validation passes
- [x] Completion Record appended
- [x] Evidence recorded in `proofs/`

## Completion Record

```yaml
status: done
completed_by: agent:example-agent
on_behalf_of_human_id: human:alex-rivera
completed_date: 2026-07-01
commit_sha: "<example — in a real Cell this is the verified commit hash>"
changed_files:
  - apps/setbrain/knowledge/genre-notes.md: house + techno seeded
  - apps/setbrain/knowledge/venue-profiles.md: three fictional venues profiled
  - apps/setbrain/prompts/set-brief.prompt.md: canonical brief prompt, text-only per gate
validation:
  git_diff_check: pass
  photo_embed_scan: pass (none found)
proof: ../proofs/PROOF-20260701-001-set-brief-guide-validation.md
follow_up: ../handoffs/HANDOFF-20260702-001-continue-genre-notes.md
human_gate_required: []
recommendation_only_ending: false
```
