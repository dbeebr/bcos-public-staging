---
bcos_type: doc
id: DJBRAIN-CELL-README
title: "djbrain Cell — Example Active Cell with an App Package"
status: active
created: 2026-07-05
created_by: bcos-maintainers
surface: project
related:
  - PROJECT.md
  - AGENTS.md
  - CONTEXT_INDEX.md
  - apps/djbrain/README.md
---

# djbrain Cell — Example Active Cell

This is a **complete, fictional example** of an active BCOS Cell. Every name,
person, venue, and knowledge entry in it is invented. The *pattern* is real: it
mirrors a production Cell shape in active use.

The Cell belongs to a fictional two-person music-events team. Their maintained
domain capability is **djbrain** — a domain brain that agents query for genre
knowledge, venue profiles, and set-description guidance. Because djbrain is
active and agent-facing, it lives in `apps/djbrain/`, not in `library/`.

## What this example demonstrates

1. **The tiered Cell shape** — core surfaces, operating expansion, and one app
   package (see `docs/public-cell-target-structure.md` in the starter root).
2. **A complete work loop** — one intake entry became a task, the task hit a
   human gate, produced a decision, was completed with a proof, handed off, and
   recorded in history. Follow the chain:

```text
inbox/INBOX.md                          → raw request arrives
human-gates/HUMAN-GATE-20260630-001-*   → human approves the content posture
decisions/DECISION-20260701-001-*       → app-package placement decided
work/TASK-20260701-001-*                → executed task with Completion Record
proofs/PROOF-20260701-001-*             → evidence that closes the claim
handoffs/HANDOFF-20260702-001-*         → continuation for the next session
history/RECORD-20260701-001-*           → the durable chronological record
library/PATTERN-set-brief.md            → the reusable pattern distilled from the work
```

3. **Routing frontmatter** — every file carries the core routing profile
   (`bcos_type`, `id`, `title`, `status`, `created`, `created_by`, `surface`,
   `related`). Agent-written artifacts additionally carry actor-identity
   fields. See `schemas/` in the starter root.

## Structure

```text
README.md  PROJECT.md  AGENTS.md  CONTEXT_INDEX.md  TEAM.md
inbox/           ← raw intake, append-only
work/            ← executable tasks with Completion Records
decisions/       ← resolved choices
human-gates/     ← human judgment checkpoints
reports/         ← analysis
proofs/          ← completion evidence
handoffs/        ← continuation records
history/         ← chronological record
library/         ← proven, distilled patterns
playbooks/       ← repeatable procedures
apps/
  djbrain/       ← the active domain capability (own context, knowledge, prompts)
```

## Start here

1. Read `PROJECT.md` — what this Cell is for.
2. Read `AGENTS.md` — how agents must operate here.
3. Read `CONTEXT_INDEX.md` — what to load, what to skip.
4. Read `apps/djbrain/README.md` — the app package.
5. Follow the work-loop chain above in order.

## Rule of thumb

djbrain is an app package because it is **active**: it has its own context
index, knowledge, prompts, and proof loop, and agents query it while doing
other work. When a pattern inside djbrain proves reusable beyond it, a
distilled copy goes to `library/` — the app keeps operating.
