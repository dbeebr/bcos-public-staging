---
bcos_type: state
kind: project
surface: project
id: PROJECT
title: "Teamcell Lite Project Context"
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
---

# Teamcell Lite Project Context

## Purpose

Use this repository as the shared operating memory for a small private team.
The repository should make current work, human decisions, and durable evidence
visible to both humans and agents.

## Scope

This cell contains raw intake, executable work, human decision gates, history,
and reusable playbooks for one bounded team workspace.

## Non-Goals

- No dashboard or command-center runtime.
- No MCP runtime.
- No graph, vector, or compiled context layer.
- No broad BCOS migration.
- No sensitive data until the data policy is explicitly accepted.

## Data Policy

Do not commit credentials, private keys, passwords, tokens, unredacted personal
secrets, or confidential material that the team has not approved for this
repository. Treat inbox entries as raw and untrusted until reviewed.

## Decision Authority

The decision owner named in `TEAM-PROFILE.md`'s `cell_owner_role` binding (in
this template's worked example: the `lead` role, bound to
`human:example-lead`, a clearly fictional example — never a real person's
name) holds decision authority for `routine_work` and any decision class
whose `decision_owner_roles` entry defers to that role, until this file is
reviewed and accepted by the team. Agents may draft work and propose
decisions on behalf of an accountable human. Agents may not accept truth,
close human gates, or approve sensitive changes.

## Governance Profile

This Cell's machine-readable governance-profile and ownership configuration
lives in `.bcos/CELL-GOVERNANCE.yaml` (written by the confirmed installer, or
copied by hand from `.bcos/CELL-GOVERNANCE.yaml.template`; both start with
`governance_profile: null` and `legacy_unresolved: true` unless a human
selected a profile — never pre-selected). One of three profiles
(`quick_build`, `operating_team`, `compliance_safety`) determines which
decision classes require a Human Gate; the full matrix is
`docs/teamcell-gate-matrix.md`, shipped at that same path in every installed
Cell (baseline package). A Cell with no
selected profile is a valid, expected state — not an error — until a human
explicitly chooses one.

## Repository Scope

- Default branch: `main`
- Intended visibility: private
- Intended use: small-team workspace

## Trust Model

Git is the source of truth. Chat-only claims are not proof. A claim is durable
only when it is recorded in this repository, committed, and pushed when an
`origin` remote exists.
