---
bcos_type: doc
kind: routing_delta
surface: project
id: TEAMCELL-LITE-GENERIC-PUBLIC-ROUTING-DELTA-20260705
title: "Teamcell Lite Generic Public Routing Delta"
status: done
created: 2026-07-05
created_by: claude-chat
created_by_type: agent
created_by_id: agent:claude-chat
created_by_display: "Claude Chat"
created_by_github: null
on_behalf_of_human_id: "human:{{CELL_OWNER_ID}}"
agent_id: agent:claude-chat
agent_model: gpt-5.5-thinking
agent_capability_class: chat-reviewer
---

# Teamcell Lite Generic Public Routing Delta

Date: 2026-07-05
Status: **applied** — historical record, no open follow-up

## Purpose

This note records the generic routing delta that made Teamcell Lite reusable outside the single team it was first built for.

## Applied 2026-07-05

This delta was applied directly to the template:

- Named people are now explicitly the template's **example team** (`TEAM-PROFILE.md`, `README.md`, `PROJECT.md`); the human-gate template uses placeholders.
- `scripts/validate-cell.sh` now checks TEAM-PROFILE **structure** (≥1 registered participant, display names, exactly one `decision_authority: true`, non-empty `decision_owner_*`) instead of requiring specific names — any team passes.
- Brand Brain became *an example* of a domain brain in `README.md`, `AGENTS.md`, `CONTEXT_INDEX.md`, and the routing playbook.
- `docs/EXPANSION-PROFILE.md` records the optional expansion surfaces (`decisions/`, `reports/`, `proofs/`, `handoffs/`, `library/`, `apps/<app-id>/`) and the apps-vs-library lifecycle (capture → gate → promote → distill → demote).
- Routing tables in `AGENTS.md`, `CONTEXT_INDEX.md`, and the playbook gained the `apps/<app-id>/` row.

Not applied (deliberate): physical creation of the expansion folders in the template — they are opt-in per cell, by gate.

## Keep

- `PROJECT.md` as the project scope and trust model.
- `AGENTS.md` as the agent operating contract.
- `CONTEXT_INDEX.md` as the selective context loader.
- `inbox/`, `work/`, `human-gates/`, `history/`, and `playbooks/` as minimal private-team surfaces.
- Proof-based completion.

## Change for generic starters

- Treat named people as examples, not defaults.
- Treat Brand Brain as an example of an app package, not as the only domain-knowledge case.
- Allow active domain capabilities under `apps/<app-id>/` when they have local context, prompts, reports, and proofs.
- Keep `library/` for proven reusable patterns only.
- Add `decisions/`, `proofs/`, and `handoffs/` when the Cell is meant to be operated by unfamiliar contributors or agents.

## Recommended active Cell expansion

```text
README.md
PROJECT.md
AGENTS.md
CONTEXT_INDEX.md
TEAM.md
inbox/
work/
decisions/
human-gates/
reports/
proofs/
handoffs/
history/
library/
playbooks/
apps/<app-id>/
templates/
schemas/
scripts/
```

## Routing rule

If a domain capability is active and maintained, route it to `apps/<app-id>/`.

If a pattern is proven and reusable across Cells, distill it to `library/`.

If work is only raw intake, keep it in `inbox/` until processed.

## Follow-up

None open. The delta became a direct template patch (above) plus the
optional expansion profile in `docs/EXPANSION-PROFILE.md`. The "Recommended
active Cell expansion" tree above is illustrative: every folder beyond the
core surfaces is added by gate, one at a time.
