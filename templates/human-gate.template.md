---
id: GATE-YYYYMMDD-NNN
title: "Decision needed: [short description]"
status: open
gate_status: pending-human-decision
requires_human_decision: true
decision_owner: human-id
created: YYYY-MM-DD
created_by: human-or-agent-id
---

# GATE-YYYYMMDD-NNN — Decision Needed

## TL;DR

State the smallest decision needed, in one or two sentences.

## Why This Gate Exists

What makes this decision costly, irreversible, public, legal, sensitive, or
architectural? Why should it not be made automatically?

## Context

What should the decision owner read or know before deciding?

- Reference: `FILE.md` or decision or prior gate
- Key constraint: description
- Risk if wrong: description

## Options

- **Option A:** Description. Consequence: ...
- **Option B:** Description. Consequence: ...

## Recommendation

State a recommendation only if the evidence supports one and it is within
the scope of the person making the recommendation.

## Open Decisions For [Decision Owner]

- [ ] Choose an option from above
- [ ] Confirm the scope of the choice
- [ ] Update `gate_status` to `approved` or `rejected`
- [ ] Commit and push

## Acceptance Instructions

To close this gate:

1. Update `gate_status` from `pending-human-decision` to `approved` or `rejected`.
2. Update `status` to `closed`.
3. Add decision notes below.
4. Commit and push with an explanatory message.

Do not have an agent close this gate. Human Git evidence is required.

## Decision Notes

*(To be filled by decision owner)*
