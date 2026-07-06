---
bcos_type: doc
kind: playbook
id: SETBRAIN-CELL-PLAYBOOK-UPDATE-KNOWLEDGE
title: "Playbook — update setbrain knowledge"
status: active
created: 2026-07-02
created_by: example-agent
created_by_type: agent
created_by_id: agent:example-agent
created_by_display: "Example Agent"
on_behalf_of_human_id: human:alex-rivera
surface: playbooks
related:
  - ../apps/setbrain/CONTEXT_INDEX.md
---

# Playbook — Update setbrain Knowledge

*(Fictional example.)*

## Trigger

Any change to files under `apps/setbrain/knowledge/`.

## Steps

1. Create a task in `work/` from the template; name the exact knowledge files.
2. Read `apps/setbrain/CONTEXT_INDEX.md`, then only the target files.
3. Append or edit within existing headings; prompts reference headings, so
   never restructure without checking `apps/setbrain/prompts/`.
4. Run `git diff --check`; scan for image embeds (text-only posture).
5. Append the Completion Record with changed files and validation results.
6. If the change closes a claim, add a proof; if work remains, add a handoff.

## Output

A committed knowledge change whose task file explains what changed and why —
findable by the next agent without reading chat history.
