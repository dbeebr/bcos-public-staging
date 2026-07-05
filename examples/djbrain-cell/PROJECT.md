---
bcos_type: doc
id: DJBRAIN-CELL-PROJECT
title: "djbrain Cell Project Context"
status: active
created: 2026-07-05
created_by: bcos-maintainers
surface: project
related:
  - TEAM.md
  - AGENTS.md
---

# djbrain Cell Project Context

*(Fictional example content.)*

## Purpose

Run the shared work of a two-person music-events team and maintain one active
domain capability: **djbrain**, the team's knowledge brain for genres, venues,
and set descriptions.

## Scope

Intake, executable work, decisions, human gates, reports, proofs, handoffs,
history, distilled library patterns, playbooks, and the `apps/djbrain/`
package.

Out of scope: event ticketing, finances, and any software product source code —
those live in their own repositories.

## Trust Model

- Git is the durable source of truth. Chat can suggest; committed artifacts decide.
- Chat memory is not proof. Completion requires a Completion Record plus evidence.
- Alex Rivera (`human:alex-rivera`) is the decision owner (see `TEAM.md`).
- Agents operate as contractors under `AGENTS.md`.

## Data Policy

- No personal data beyond the two team members' working names.
- No credentials, tokens, or private endpoints in any artifact.
- Raw domain knowledge stays inside `apps/djbrain/`; the Cell root stays
  governance-only.

## Rules

- Raw input is appended to `inbox/INBOX.md`, never edited retroactively.
- Domain knowledge changes go through a `work/` task; new top-level surfaces
  require a human gate first.
- Reusable patterns are distilled into `library/` only after they are proven
  in completed work.
