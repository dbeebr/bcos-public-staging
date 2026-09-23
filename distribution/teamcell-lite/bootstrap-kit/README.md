---
bcos_type: doc
kind: getting_started
surface: project
id: README
title: "BCOS Teamcell Lite v0.4"
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
version: "BCOS Teamcell Lite v0.4 - release candidate"
---

# BCOS Teamcell Lite v0.4

Version marker: **BCOS Teamcell Lite v0.4 — release candidate**

This repository is a small private Git workspace for a small team (two
people are enough) with a clear inbox, executable work files, human gates,
history, and playbooks. Humans and AI agents work in it under the same
contract: Git is the source of truth, and completion needs evidence.

v0.4 makes the contract, templates, validator and start command agree:
canonical types and `agent_capability_class` values, `work/TASK-*.md` work
items, an honest-completion check (`scripts/validate-completion.py`, whose
`--ready` mode is the format check a task passes before execution), and an
exact-identity validator baseline (`playbooks/VALIDATOR-BASELINE.playbook.md`).
v0.3 introduced role-based ownership (`cell_owner_role` /
`decision_owner_roles` / `role_bindings`) and the three-tier governance
profile in `.bcos/CELL-GOVERNANCE.yaml.template`.

## Packages

| Package | Installed | Adds |
|---|---|---|
| `teamcell-lite-baseline` | always | everything in this README's surfaces, scripts and templates |
| `teamcell-plus-profile` | only when selected | `ONBOARDING.md`, `docs/CONTRACTS-V1.md`, `scripts/post-cell-update.sh`, `scripts/morning-pulse.sh`, `scripts/validate-cell-plus.sh`, `history/learning-candidates/` |
| `team-capability-pack` | only when selected (selects Plus too) | `apps/team-capability-pack/` with three bounded skills and `playbooks/onboarding/SKILL-PLAYGROUND.html` |

`packages/PACKAGES.yaml` is the machine-readable package contract. The
installation receipt (`.installation/TEAMCELL-INSTALLATION-RECEIPT.yaml`)
records which packages this Cell actually received.

## Start here

1. Run `./scripts/start-cell.sh` — it verifies identity and Git state,
   validates the Cell and prints the current active work item and next
   action (and refreshes `playbooks/onboarding/START-HERE.html`).
2. Read `PROJECT.md`, then `AGENTS.md` (agents follow its Start Protocol: the
   Cell entry in `.bcos/CELL-PROFILE.yaml`, the work item, then the matching
   procedures from the Procedure Index in `CONTEXT_INDEX.md`).
3. Replace the fictional example team in `TEAM-PROFILE.md` with your own.
4. Add raw input to `inbox/INBOX.md`.
5. Create a work item as `work/TASK-YYYYMMDD-NNN-<slug>.md` from
   `work/TEMPLATE.task.md`. It is executable once
   `python3 scripts/validate-completion.py --ready <path>` reports READY;
   facts, IDs or approvals nobody has yet stay `OPEN: ...`.
6. Select a governance profile in `.bcos/CELL-GOVERNANCE.yaml`
   (`quick_build | operating_team | compliance_safety`) when ready — the
   installer writes that file; without the installer, copy it from
   `.bcos/CELL-GOVERNANCE.yaml.template`. `legacy_unresolved: true` is a
   valid default state.
7. Run `./scripts/validate-cell.sh` before every completion claim.

## For Agents: Route Before Writing

Before creating a new file, decide which Teamcell Lite surface owns the work.
Use `CONTEXT_INDEX.md`, `AGENTS.md`, and `playbooks/AGENT-ROUTING.playbook.md`
as the routing layer.

- Raw unprocessed input goes to `inbox/INBOX.md`.
- Executable work goes to `work/`.
- Human decisions go to `human-gates/`.
- Durable evidence, reviews, reports, and accepted decisions go to `history/`.
- Reusable procedures go to `playbooks/`.

Domain knowledge concepts start as work items. For example, a brand brain must
first be captured in `work/`; its later surface requires the decision owner's
human gate before implementation. An actively queried domain capability is
promoted to `apps/<app-id>/`; passive proven patterns are distilled to
`library/`. See `docs/EXPANSION-PROFILE.md` for the optional expansion
surfaces.

Readiness is proof-based. A local install is not team-ready. Team-ready
requires first-use proof, hosted repository proof, and a multi-committer
two-person proof.

Named roles in this template's worked example (Team Lead, Contributor) are
clearly fictional, not real people's names, and not defaults — replace them
via `TEAM-PROFILE.md` when creating your own cell. An unbound role or an
unresolved decision class is the correct state until a real owner is known;
never invent a name.

## License

This package (scripts, schemas, configuration, adapters, skills, playbooks
and their operative templates) is released under the MIT License — see
`LICENSE` in this directory. It ships with the baseline package (source root
`.`) into every installed Cell, so `LICENSE` is present at the root of each
Cell created from this template. The optional `teamcell-plus-profile` and
`team-capability-pack` packages are additive overlays on a Cell that already
carries this baseline `LICENSE` and are covered by it (see
`profiles/plus/README.md`).
