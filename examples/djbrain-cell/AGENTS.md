---
bcos_type: doc
id: DJBRAIN-CELL-AGENTS
title: "djbrain Cell Agent Contract"
status: active
created: 2026-07-05
created_by: bcos-maintainers
surface: playbooks
related:
  - CONTEXT_INDEX.md
  - PROJECT.md
---

# Agent Contract — djbrain Cell

Preserve context coherence. Keep work inspectable. Leave Git evidence.

## Start Protocol

Before writing anything:

1. Confirm the repository and branch.
2. Run `git status --short --untracked-files=all`.
3. Read `PROJECT.md`, then `CONTEXT_INDEX.md`.
4. Read the assigned work item or human gate.
5. Read only the additional files the task actually needs.

## Read Gate

Before any status, completion, or next-step claim about Cell work: read the
specific artifact the claim is about. Do not rely on chat memory. Distinguish
"user reports X" from "Git confirms X at commit `<sha>`".

## Routing

| Intent | Target |
|---|---|
| Raw unprocessed input | append to `inbox/INBOX.md` |
| Executable work | create a task in `work/` from `work/TEMPLATE.task.md` |
| Human decision needed before acting | create a gate in `human-gates/` |
| Resolved choice worth finding later | record in `decisions/` |
| Analysis | `reports/` |
| Completion evidence | `proofs/` |
| Continuation across sessions | `handoffs/` |
| Durable chronological record | `history/` |
| Proven reusable pattern | `library/` |
| Repeatable procedure | `playbooks/` |
| djbrain domain content | `apps/djbrain/` (read its `CONTEXT_INDEX.md` first) |

New domain knowledge starts as a `work/` task. Creating a new top-level
surface requires a human gate first.

## Identity

Artifacts written by an agent must say so in frontmatter:

```yaml
created_by_type: agent
created_by_id: agent:<id>
created_by_display: "<display name>"
on_behalf_of_human_id: human:alex-rivera | human:sam-okafor
```

## Completion

Work is not done until:

- the task's Definition of Done is satisfied;
- a Completion Record is appended to the task file with `status: done`,
  changed files, validation results, and a commit SHA;
- evidence strong enough to close the claim exists (in `proofs/` when the
  claim needs standalone evidence);
- changes are committed, and pushed when an `origin` remote exists.

Never end governed work with recommendations only. If the next action is real
work, create the durable artifact (task, gate, or handoff) before stopping.
