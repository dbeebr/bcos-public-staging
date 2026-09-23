---
bcos_type: doc
kind: playbook
surface: playbooks
domain: operations
id: AGENT-ROUTING
title: "Agent Routing Playbook"
status: active
procedure_kind: "playbook"
use_when: "Before creating an artifact, folder, config or agent-instruction surface, or before a status, done or next-step claim"
not_when: "Editing inside an artifact whose place is already settled"
phase: "plan, execute, close"
created: 2026-06-24
created_by: copilot
created_by_type: agent
created_by_id: agent:copilot
created_by_display: "GitHub Copilot"
created_by_github: null
on_behalf_of_human_id: "human:{{CELL_OWNER_ID}}"
agent_id: agent:copilot
agent_model: github-copilot
agent_capability_class: local-worker
---

# Agent Routing Playbook

## Trigger

Use this playbook before creating a new artifact, folder, configuration file, or
agent instruction surface.

Also use it before a status, done, next-step, completion, or governance claim
about teamcell-governed work.

## Inputs

- `PROJECT.md`
- `CONTEXT_INDEX.md`
- `AGENTS.md`
- The assigned work item, human gate, or human request

## Routing Rules

Before making a claim, identify the repo, branch, and relevant artifact; read
the artifact; and distinguish user-reported status from Git-verified status.
Then route the next action below.

| Input or intent | Target |
|---|---|
| Raw unprocessed input | Append to `inbox/INBOX.md` |
| Executable work with outcome, gates, and validation | Create a task in `work/` |
| Human decision required before safe implementation | Create a gate in `human-gates/` |
| Durable evidence, review, report, or accepted decision | Record in `history/` |
| Reusable procedure or repeatable agent workflow | Create a playbook in `playbooks/` |
| No actionable follow-up | Record explicit `none` in the response or Completion Record |
| Domain knowledge concept | First create a work item in `work/`; do not create a new knowledge or context surface until a human gate accepts the target placement |
| Active maintained domain capability (after gate) | `apps/<app-id>/` — see `docs/EXPANSION-PROFILE.md` |
| Passive, proven cross-work pattern | Distill to `library/` (an optional expansion surface, added by gate) |
| Validator failure that existed before this change | Keep it visible as known; compare by identity per `playbooks/VALIDATOR-BASELINE.playbook.md`; route its repair to `work/` |
| Repo-level agent behavior | Update `AGENTS.md` and, when allowed by the task, `.github/copilot-instructions.md` |
| Tool-specific or domain-specific agent guidance | Create a playbook first; promote later only after review |
| MCP configuration | Create a human gate first; include no secrets and assume no runtime until accepted |

Do not end governed work with recommendation-only prose. If the next action is
real work, create or update the durable artifact.

## Domain Knowledge Rule

Domain knowledge concepts are not new surfaces by default. Create executable
work first, define the intended outcome and validation, and use a human gate
before creating a new knowledge or context path.

A domain brain (for example, a brand brain) is first domain knowledge work
inside the team cell. It must be captured as a work item first. Its later
target surface requires the decision owner's human gate before implementation.
When the gate accepts an actively queried capability, route it to
`apps/<app-id>/`; distill passive proven patterns to `library/`
(see `docs/EXPANSION-PROFILE.md`).

## MCP Rule

MCP configuration requires a human gate before implementation. Do not add
secrets, tokens, private endpoints, runtime assumptions, or local machine
specific values to the repository.

## Output

The new artifact is placed in the correct existing surface, or a human gate
captures the placement decision before implementation.

## Validation

Run:

```sh
./scripts/validate-cell.sh
git diff --check
git status --short --untracked-files=all
```
