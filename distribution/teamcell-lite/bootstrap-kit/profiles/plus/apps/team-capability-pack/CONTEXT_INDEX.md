---
bcos_type: index
kind: context
surface: apps
domain: operations
id: TEAM-CAPABILITY-PACK-APP-CONTEXT-INDEX
title: "Team Capability Pack — bounded context index"
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
---

# Team Capability Pack — Context Index

Load only the one skill file the request classifies into. Do not load all
three skills, this whole app, or Brand Brain by default.

## Routing table

| The request looks like... | Load |
|---|---|
| A business question, goal, process, or stakeholder situation is unclear or under-specified, and someone needs a structured read before deciding anything | `skills/BUSINESS-ANALYST.skill.md` |
| An outcome/decision is already accepted and needs to become specific, testable work | `skills/REQUIREMENTS-ENGINEERING.skill.md` |
| A team needs to meet, workshop, or align, and the interaction itself needs designing | `skills/TEAM-EVENT-PLANNER.skill.md` |
| The request is brand-, tone-, or journey-sensitive | additionally load the installed domain brain's own bounded index (e.g. `apps/brand-brain/CONTEXT_INDEX.md`) — only the specific file(s) it points to, never its full content by default |
| None of the above — routine Cell work, a status question, a code change, an unrelated skill | load nothing from this app |

## Classify-then-load rule

1. Read the request.
2. Match it to exactly one row above (or none).
3. Load only that one skill file (plus, if flagged, the domain brain's own
   bounded pointer — not its full content).
4. If the request spans more than one skill (e.g. a business question that
   will also need requirements), load the first skill only; that skill's
   own output routes to the next skill as a separate step, not a combined
   context load.

## Try it

`playbooks/onboarding/SKILL-PLAYGROUND.html` is a static, no-build onboarding
page with a complete copy/paste prompt per skill above, plus the
skill-improvement review loop. It is a discovery aid, not a context source —
it does not replace this routing table.

## Non-default guarantee

Neither this index, any file in `skills/`, nor the installed domain brain
is part of the Cell's default session bootstrap (`AGENTS.md` ->
`BCOS_STATE.md`-equivalent -> root `CONTEXT_INDEX.md`). The root
`CONTEXT_INDEX.md` carries exactly one routing pointer to this file; this
file is the only place skill-specific detail loads from.
