---
bcos_type: doc
kind: expansion_profile
surface: project
id: TEAMCELL-LITE-EXPANSION-PROFILE
title: "Teamcell Lite Optional Expansion Profile"
status: active
created: 2026-07-05
created_by: claude-fable-5
created_by_type: agent
created_by_id: agent:claude-fable-5
created_by_display: "Claude Fable 5"
created_by_github: null
on_behalf_of_human_id: "human:{{CELL_OWNER_ID}}"
agent_id: agent:claude-fable-5
agent_model: claude-fable-5
agent_capability_class: local-worker
---

# Optional Expansion Profile

Teamcell Lite ships with the core surfaces (`inbox/`, `work/`,
`human-gates/`, `history/`, `playbooks/`, `scripts/`, plus
`reports/verification/` for validator evidence). Real two-person cells run on
these alone. This profile lists the surfaces a cell may **add when they earn
their place** — never upfront.

## When to add each surface

| Surface | Add when | What it holds |
|---|---|---|
| `decisions/` | resolved choices need to be findable apart from gates and history | recorded decisions with rationale |
| `reports/` (top-level) | analysis accumulates beyond verification reports | evaluations and explorations that inform decisions |
| `proofs/` | completion claims need standalone auditable evidence | records strong enough to close a claim |
| `handoffs/` | work crosses sessions, people, or agents | continuation records anchored to commit SHA + Completion Record |
| `library/` | a pattern has proven itself in completed work and will be reused | curated, distilled patterns (never raw records) |
| `apps/<app-id>/` | a domain knowledge area becomes an actively queried capability | the capability package: own README, CONTEXT_INDEX, knowledge, prompts, proof loop |

Adding a surface is a routed change: create a work item, pass a human gate for
the new surface, then update `CONTEXT_INDEX.md` and `AGENTS.md` routing tables
in the same task.

## The `apps/` vs `library/` rule

A **domain brain** — a brand brain, product brain, or any knowledge package
agents query while doing other work — follows this lifecycle:

1. **Capture:** it enters as domain knowledge work items in `work/`.
2. **Gate:** its target surface is a human-gate decision — never an agent
   default.
3. **Promote:** when the gate confirms it is an *actively queried, maintained
   capability*, it lives in `apps/<app-id>/` with its own local context index
   and proof loop. Placing an active capability in `library/` hides it and
   misdescribes it.
4. **Distill:** patterns proven inside the app are *copied* to `library/`;
   the operating original stays in the app.
5. **Demote:** an unmaintained app package is archived to `history/` or
   reduced to its `library/` remains — recorded as a decision.

Precedent: this rule generalizes a real production cell's promotion of its
brand brain from `library/` to `apps/`, decided by the cell's human decision
owner after operating both placements.

## What stays out

Even in fully expanded cells: no top-level code surface (route code via
`work/` → `scripts/` → `library/tools/`) and no new surface without a gate.

Artifact templates live in-surface (`work/TEMPLATE.task.md`,
`human-gates/TEMPLATE.human-gate.md`, `playbooks/TEMPLATE.playbook.md`). The
baseline's `templates/` folder is different: it holds only the
personalization sources (`PROJECT-INSTRUCTIONS`, the one shared
instruction core; the thin `APP-INSTRUCTIONS-*` activation notes;
`FIRST-RUN-AGENT-PROMPT`) that `scripts/render-instructions.py` renders —
called by `scripts/personalize-cell.py` (the installer's mandatory,
non-interactive personalization step) and by the interactive
`personalize-team-cell.sh` — into `instructions/` and
`FIRST-RUN-AGENT-PROMPT.md`. Do not put other templates there. `packages/PACKAGES.yaml` and `.installation/` are package and
installation metadata, not work surfaces.

## Distribution boundary

The Teamcell distribution ships this template tree plus installer tools and
contract documents. An installed Cell receives only the files of the
packages selected at install time (see `packages/PACKAGES.yaml`);
`profiles/` is distribution source material and never appears in a Cell.
