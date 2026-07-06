---
bcos_type: decision
id: DECISION-20260701-001
title: "setbrain lives in apps/setbrain/, not library/"
status: done
created: 2026-07-01
created_by: alex-rivera
created_by_type: human
created_by_id: human:alex-rivera
created_by_display: "Alex Rivera"
surface: decisions
related:
  - ../human-gates/HUMAN-GATE-20260630-001-set-brief-content-posture.md
  - ../apps/setbrain/README.md
---

# DECISION-20260701-001 — setbrain Is an App Package

*(Fictional example.)*

## Decision

The team's domain brain is promoted to a first-class app package:

```text
apps/setbrain/
```

`library/` is reserved for passive, proven, distilled patterns. setbrain is not
passive: agents query it for genre knowledge, venue profiles, and prompt
payloads while producing set briefs.

## Rationale

Placing an actively queried capability under `library/` hides it and
misdescribes it. `apps/<app-id>/` gives it its own context index, knowledge,
prompts, and proof loop without polluting the Cell root.

## Consequences

- setbrain content changes go through `work/` tasks like all other work.
- Patterns proven inside setbrain are *copied* to `library/` when they become
  reusable beyond it; the app keeps the operating original.
- If setbrain ever becomes unmaintained, it is archived to `history/` or reduced
  to its distilled `library/` remains — recorded as a new decision.
