---
bcos_type: doc
id: SETBRAIN-CELL-TEAM
title: "setbrain Cell Team"
status: active
created: 2026-07-05
created_by: bcos-maintainers
surface: project
related:
  - PROJECT.md
---

# Team — setbrain Cell

*(Fictional example team. Replace every entry when you copy this Cell.)*

## Participants

| ID | Display name | Role | Decision owner |
|---|---|---|---|
| `human:alex-rivera` | Alex Rivera | owner | yes |
| `human:sam-okafor` | Sam Okafor | collaborator | no |
| `agent:example-agent` | Example Agent | contractor | never |

## Rules

- Exactly one human is the decision owner at any time. Changing the owner is
  itself a recorded decision.
- Human gates name their decision owner and reviewers explicitly; an agent can
  prepare a gate but never resolve one.
- Agents act `on_behalf_of_human_id` — accountability always traces to a human.

> Note for Teamcell Lite users: this file plays the same role as
> `TEAM-PROFILE.md` in the Teamcell Lite template. The two names are aliases
> for the same surface.
