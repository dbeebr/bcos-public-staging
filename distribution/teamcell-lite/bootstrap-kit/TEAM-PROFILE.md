---
bcos_type: state
kind: team_profile
surface: project
id: TEAM-PROFILE
title: "Team Profile"
status: draft
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
decision_owner: "Team Lead"
decision_owner_id: human:example-lead
decision_owner_display: "Team Lead"
cell_owner_role: lead
decision_owner_roles:
  routine_work: lead
  material_scope_change: lead
  priority_change: lead
  budget_change: unresolved
  customer_promise: lead
  legal_privacy: legal_advisor
  people_impacting: lead
  irreversible_action: lead
  security_change: unresolved
  external_visibility: lead
role_bindings:
  lead:
    human_id: human:example-lead
    display_name: "Team Lead"
    bound_at: 2026-07-14
    bound_by: human:example-lead
  legal_advisor:
    human_id: null
    display_name: null
    bound_at: null
    bound_by: null
participants:
  - human_id: human:example-lead
    display_name: Team Lead
    github: null
    role: owner
    decision_authority: true
  - human_id: human:example-contributor
    display_name: Contributor
    github: null
    role: collaborator
    decision_authority: false
---

# Team Profile

> **The named people below are the template's example team, not defaults.**
> "Team Lead" and "Contributor" are clearly fictional generic roles, not real
> people's names. When you create a cell from this template, replace every
> participant with your own team. The rules that must survive the
> replacement: stable `human:<id>` identifiers, exactly one participant with
> `decision_authority: true`, matching `decision_owner_*` fields in the
> frontmatter above, and a `role_bindings` entry for every role slug
> referenced by `cell_owner_role` or `decision_owner_roles`. Never replace
> the example with a fabricated name — an unbound role (`human_id: null`) or
> an unresolved decision class (`unresolved`) is the correct state until a
> real owner is known. See this Cell's own `schemas/teamcell-cell-ownership.schema.md`
> and `schemas/teamcell-governance-profile.schema.md` for the full field contract.

## Team

- Team name: To be confirmed.
- Example members: Team Lead (`human:example-lead`) and Contributor
  (`human:example-contributor`) — replace with your team.
- Decision owner: the participant with `decision_authority: true`, until
  changed by an accepted decision. `cell_owner_role` (above) names the
  generic role that participant holds; `role_bindings.<cell_owner_role>`
  binds that role to their `human:<id>`.
- `decision_owner_roles` lets a specific decision class (e.g. `legal_privacy`)
  defer to a different role than the Cell's general owner, or stay explicitly
  `unresolved` when no role has been chosen for it yet. This example shows
  all three states at once: a bound default role (`lead`), a decision class
  deferring to a named-but-unbound role (`legal_privacy` → `legal_advisor`),
  and decision classes with no role chosen at all (`budget_change`,
  `security_change`: `unresolved`).

## Participant Registry

| Human ID | Display | GitHub | Role | Decision Authority |
|---|---|---|---|---|
| `human:example-lead` | Team Lead | `null` | owner | yes |
| `human:example-contributor` | Contributor | `null` | collaborator | no |

Use stable human IDs in work and gate frontmatter. Do not use email addresses
as IDs. Record GitHub usernames separately when known.

## Working Agreement

- Use `inbox/INBOX.md` for raw capture.
- Use `work/` for executable tasks.
- Use `human-gates/` when a human decision is required.
- Use `history/` for durable records, reviews, reports, and decisions.
- Use `playbooks/` for reusable ways of working.

## Access And Review

- Repository visibility: private.
- Default branch: `main`.
- Sensitive changes require human review.
- Agent-generated claims require Git evidence before they can be trusted.
