---
bcos_type: doc
kind: app_readme
surface: apps
domain: operations
id: TEAM-CAPABILITY-PACK-APP-README
title: "Team Capability Pack — installed app"
status: active
created: 2026-07-12
created_by: claude-sonnet-5-bcos-orchestrator
created_by_type: agent
created_by_id: agent:claude-sonnet-5-bcos-orchestrator
created_by_display: "Claude Sonnet 5 (BCOS orchestrator session)"
created_by_github: null
on_behalf_of_human_id: "human:{{CELL_OWNER_ID}}"
agent_id: agent:claude-sonnet-5-bcos-orchestrator
agent_model: claude-sonnet-5
agent_capability_class: local-worker
related:
  - CONTEXT_INDEX.md
  - skills/BUSINESS-ANALYST.skill.md
  - skills/REQUIREMENTS-ENGINEERING.skill.md
  - skills/TEAM-EVENT-PLANNER.skill.md
---

# Team Capability Pack

An **optional**, explicitly opt-in Teamcell Plus app. It ships three
bounded skills that turn a Cell's business ambiguity into work the Cell's
existing objects (`WorkItem`, `HumanGate`, `CompletionRecord`,
`CellUpdate`, `LearningCandidate`) already know how to carry:

```text
business ambiguity
  -> Business Analyst
  -> accepted outcome
  -> Requirements Engineering
  -> team collaboration need
  -> Team Event Planner
  -> WorkItem / HumanGate / CompletionRecord / CellUpdate
```

## What this is not

- Not a default Teamcell Plus surface. `scripts/install-plus-profile.sh`
  never copies this app; a Cell operator installs it explicitly via
  `scripts/install-capability-pack.sh <target-cell-dir>` (see
  `../../scripts/install-capability-pack.sh`).
- Not a decision-maker. Every skill below produces analysis,
  specification, or design for a human owner to accept, edit, or reject —
  never a standing delegation of business, architecture, scheduling, or
  people authority.
- Not a Brand Brain duplicate. Skills may cite an installed
  `apps/brand-brain/` (or equivalent domain brain) when relevant, with a
  direct source reference; they never copy its content inline.
- Not an upstream BCOS skill registry entry. These are Cell-local
  capability files with this app's own, simpler frontmatter; nothing
  outside this Cell registers or activates them.

## Contents

In the template source this app also carries its onboarding page, which
installs to the Cell's `playbooks/onboarding/SKILL-PLAYGROUND.html` — not
into `apps/team-capability-pack/` — per `packages/PACKAGES.yaml`'s
`onboarding_source`. The installed `apps/team-capability-pack/` tree is:

```text
apps/team-capability-pack/
  README.md              -- this file
  CONTEXT_INDEX.md        -- bounded routing: which skill to load, when
  skills/
    BUSINESS-ANALYST.skill.md
    REQUIREMENTS-ENGINEERING.skill.md
    TEAM-EVENT-PLANNER.skill.md
```

No separate `templates/`, `examples/`, or `tests/` subfolder — each skill
file is self-contained (its own Positive Example / Negative Example
sections), matching `docs/EXPANSION-PROFILE.md`'s "no `templates/` folder
by default; templates live in-surface" rule. Deterministic checks for this
pack are the Cell-root validators: `scripts/validate-cell.sh` (fails on any
unresolved double-brace template placeholder under `apps/` and on a package/receipt
mismatch) and `scripts/validate-skill-playground.py` (checks the installed
`playbooks/onboarding/SKILL-PLAYGROUND.html`).

## Routing into Cell objects

| Skill output | Routes into |
|---|---|
| Business Analyst analysis | `work/` `WorkItem` (default); `human-gates/` `HumanGate` when the analysis surfaces a genuine strategic fork |
| Requirements Engineering spec | `work/` `WorkItem`, tracing back to the accepted decision/`WorkItem` it specifies |
| Team Event Planner design | `work/` `WorkItem` before the event; a `CellUpdate` or `CompletionRecord` after, if warranted |
| Any skill noticing a repeatable pattern | `history/learning-candidates/` `LearningCandidate` (non-canonical, human-gated) — never a direct BCOS write |

## Try it

A practical, static onboarding page —
`playbooks/onboarding/SKILL-PLAYGROUND.html` — gives a half AI-affine team
three complete copy/paste prompts (one per skill above) to try in VS Code
with real repo context, plus three copy/paste prompts for reviewing and
safely proposing an improvement to a skill without editing procedure truth
directly.

## Removal

Delete `apps/team-capability-pack/`, remove the one `CONTEXT_INDEX.md`
routing line this app added (see the target Cell's `CONTEXT_INDEX.md`
"Team Capability Pack" section), and remove
`playbooks/onboarding/SKILL-PLAYGROUND.html`. No Teamcell Plus baseline file
or domain-brain content is touched by installing or removing this app.
Record the removal in the Cell's installation history; the installation
receipt keeps describing the original install.

## License

Installing this pack requires teamcell-plus-profile, which requires an
already-Lite-installed Cell; the baseline package's `LICENSE` (MIT) at the
Cell root already covers these files. No separate license file is added by
this package.
