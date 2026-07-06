---
bcos_type: record
kind: human_gate
id: HUMAN-GATE-20260630-001
title: "Set-brief content posture: what may leave the Cell"
status: done
gate_status: resolved
created: 2026-06-30
created_by: sam-okafor
created_by_type: human
created_by_id: human:sam-okafor
created_by_display: "Sam Okafor"
surface: human-gates
decision_owner: Alex Rivera
decision_owner_id: human:alex-rivera
decision_owner_display: "Alex Rivera"
reviewer_ids:
  - human:alex-rivera
  - human:sam-okafor
related:
  - ../inbox/INBOX.md
  - ../decisions/DECISION-20260701-001-setbrain-app-package.md
---

# HUMAN-GATE-20260630-001 — Set-Brief Content Posture

*(Fictional example.)*

## Why this is a gate

Set briefs are sent outside the team. What leaves the Cell — venue photos,
artist references, licensing posture — is a judgment call an agent must not
make alone.

## Question for the decision owner

May set briefs generated from setbrain include venue photos, and under what
posture?

## Options

- **A** — text-only briefs; photos are linked, never embedded.
- **B** — embed photos only when the venue has given written permission.
- **C** — embed freely.

## Decision

```yaml
gate_resolved: true
resolved_at: 2026-06-30
resolved_by: human:alex-rivera
option_selected: A
rationale: text-only keeps every brief safe to forward; permissions can be revisited when volume justifies it
```

Follow-up routed to `work/TASK-20260701-001-seed-set-brief-guide.md`.
