---
bcos_type: proposal
kind: human_gate
surface: human-gates
id: GATE-YYYYMMDD-NNN
title: "Decision Needed"
status: draft
gate_status: open
requires_human_decision: true
decision_class: <one of the ten canonical decision classes listed in .bcos/CELL-GOVERNANCE.yaml.template (see this Cell's own docs/teamcell-gate-matrix.md for which classes need a gate under the selected profile); example: budget_change>
decision_owner_role: <role-slug bound in .bcos/CELL-GOVERNANCE.yaml's decision_owner_roles for decision_class above> | unresolved
decision_owner_id: <human:id resolved via .bcos/CELL-GOVERNANCE.yaml role_bindings — null when the role is unbound or decision_owner_role is unresolved>
decision_owner_display: "<display name, mirrors decision_owner_id>" | null
reviewer_ids:
  - <human:id>
created: YYYY-MM-DD
created_by: human-or-agent
created_by_type: human | agent | system
created_by_id: human:<participant-id> | agent:codex | agent:copilot | agent:<id> | system:<id>
created_by_display: "<Participant Display Name>"
created_by_github: <github-username> | null
on_behalf_of_human_id: human:<participant-id> | null
agent_id: agent:codex | agent:copilot | agent:<id> | null
agent_model: human-or-model
agent_capability_class: local-worker | git-only-worker | chat-reviewer | read-only-observer | automation | null
---

# Decision Needed

## TL;DR For Human Review

State the smallest decision needed.

## Context

What evidence should the decision owner inspect?

## Options

- Option A:
- Option B:

## Recommendation

State a recommendation only if the evidence supports it.

## Unresolved Owner

If `decision_owner_role: unresolved` above, this decision is blocked pending
role assignment in `.bcos/CELL-GOVERNANCE.yaml` — do not proceed as though
any default owner applies, including a prior Cell's or the template's
example owner. If a role is named but `decision_owner_id` is `null`, this
decision is blocked pending appointment of a human to that role. Both are
first-class, visible states — never silently default to a name.

## Open Decisions For The Decision Owner

- [ ] Choose the path.
