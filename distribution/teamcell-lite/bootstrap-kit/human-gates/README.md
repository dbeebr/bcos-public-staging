---
bcos_type: doc
kind: human_gate_guide
surface: human-gates
domain: operations
id: HUMAN-GATES-README
title: "Human Gates Guide"
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

# Human Gates Guide

Human gates are proposals, reviews, or decisions that require human judgment.
They are not a separate `bcos_type`.

Use `human-gates/TEMPLATE.human-gate.md` when a change is costly, sensitive,
hard to reverse, or changes trusted team state.

Each human gate must name the decision owner by role (`decision_owner_role`)
— a stable human ID (`decision_owner_id`) is filled in once a specific
person is bound to that role in `.bcos/CELL-GOVERNANCE.yaml` — and list the
expected human reviewers. An unassigned decision class (`unresolved`) or a
named-but-unbound role (`decision_owner_id: null`) must stay visibly
unresolved; never default to any name.

`gate_status` lifecycle: `draft` while the question is still being written,
`open` while the decision is pending, then exactly one of `accepted`,
`changes-requested`, `rejected` (set by the decision owner) or `withdrawn`
(the question no longer applies). Only a human decision
owner moves a gate out of `open`; agents may draft and propose, never decide.
