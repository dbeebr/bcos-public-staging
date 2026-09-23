---
bcos_type: doc
kind: playbook
surface: playbooks
domain: operations
id: PLAYBOOK-YYYYMMDD-NNN
title: "Reusable Way Of Working"
status: draft
procedure_kind: playbook
use_when: "One line: the concrete situation that makes this playbook apply"
not_when: "One line: the nearest situation where it does NOT apply"
phase: "plan | execute | close (one or more)"
created: YYYY-MM-DD
created_by: human-or-agent
created_by_type: human | agent | system
created_by_id: human:<participant-id> | agent:codex | agent:copilot | agent:<id> | system:<id>
created_by_display: "Display Name"
created_by_github: <github-username> | null
on_behalf_of_human_id: human:<participant-id> | null
agent_id: agent:codex | agent:copilot | agent:<id> | null
agent_model: human-or-model
agent_capability_class: local-worker | git-only-worker | chat-reviewer | read-only-observer | automation | null
---

# Reusable Way Of Working

<!-- The four fields procedure_kind, use_when, not_when and phase feed the
     generated Procedure Index in CONTEXT_INDEX.md. Keep them short and
     concrete. Once status is active, run
     `python3 scripts/render-instructions.py index --write`. -->

## Trigger

When should this playbook be used?

## Not A Trigger

The nearest situations where it does not apply.

## Inputs

- Required file or decision.

## Steps

1. Do the smallest safe first step.
2. Validate the result.
3. Record Git evidence.

## Output

What artifact or state should exist afterward?
