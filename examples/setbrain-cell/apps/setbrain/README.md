---
bcos_type: doc
id: SETBRAIN-APP-README
title: "setbrain App Package"
status: active
created: 2026-07-05
created_by: bcos-maintainers
surface: apps
app_id: setbrain
related:
  - CONTEXT_INDEX.md
  - ../../decisions/DECISION-20260701-001-setbrain-app-package.md
---

# setbrain App Package

*(Fictional example.)*

setbrain is this Cell's **active domain capability**: the knowledge brain a
fictional music-events team maintains so that agents can produce set briefs,
answer genre questions, and check venue fit without hallucinating.

It is an app package — not a `library/` entry — because it is *operated*:
it has its own context index, knowledge that gets maintained, prompt payloads
that get versioned, and its own proof loop
(DECISION-20260701-001 records the placement rationale).

## Local structure

```text
README.md          ← this file
CONTEXT_INDEX.md   ← local routing; read before touching anything here
knowledge/         ← maintained domain knowledge (genres, venues)
prompts/           ← reusable prompt payloads agents execute
reports/           ← app-specific analysis
proofs/            ← app-specific evidence
```

## Rules for agents

1. **Never invent domain facts.** If it is not in `knowledge/`, say so.
2. Content changes go through a Cell-root `work/` task
   (see `playbooks/PLAYBOOK-update-setbrain-knowledge.md`).
3. Output posture is text-only (HUMAN-GATE-20260630-001).
4. When a pattern proves reusable beyond setbrain, distill a copy to the
   Cell-level `library/` — the operating original stays here.
