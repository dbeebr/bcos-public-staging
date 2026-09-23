---
bcos_type: doc
kind: playbook_guide
surface: playbooks
domain: operations
id: PLAYBOOKS-README
title: "Playbooks Guide"
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

# Playbooks Guide

Playbooks are reusable ways of working. They should explain a repeatable path,
its trigger, its inputs, its output, and its proof requirements.

Start from `playbooks/TEMPLATE.playbook.md`. Its frontmatter fields
`procedure_kind`, `use_when`, `not_when` and `phase` are the playbook's entry
in the Procedure Index of `CONTEXT_INDEX.md`, which lists every available
procedure (playbooks, installed skills, workflows) with trigger, non-trigger,
phase, path and package. The index is generated — never add rows by hand:
after a playbook becomes `status: active`, changes or is removed, run
`python3 scripts/render-instructions.py index --write`. The validator fails
on a stale index.

A playbook is an accepted, situational procedure. Unreviewed ideas belong in
`inbox/INBOX.md` or a work item first; a concrete run of a procedure belongs
in `work/` with its own evidence.
