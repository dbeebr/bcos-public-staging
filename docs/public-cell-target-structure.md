# Public Cell Target Structure

BCOS public starter has two jobs:

1. explain the operating model;
2. give a complete starter Cell that a person or agent can copy and run.

The public repository root is not the user's Cell. It is the distribution package.

## Public starter repo

```text
README.md
LICENSE
CONTRIBUTING.md
CODE_OF_CONDUCT.md
SECURITY.md
SUPPORT.md
docs/
templates/
schemas/
examples/
  neutral-cell/
  djbrain-cell/
```

## Active Cell repo

```text
README.md
PROJECT.md
AGENTS.md
CONTEXT_INDEX.md
TEAM.md
.github/
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
apps/
  <app-id>/
    README.md
    CONTEXT_INDEX.md
    knowledge/
    prompts/
    reports/
    proofs/
templates/
schemas/
scripts/
```

## Routing rules

| Intent | Target |
|---|---|
| Raw unprocessed input | `inbox/` |
| Executable work | `work/` |
| Human decision before action | `human-gates/` |
| Recorded decision | `decisions/` |
| Analysis | `reports/` |
| Completion evidence | `proofs/` |
| Continuation record | `handoffs/` |
| Chronological record | `history/` |
| Proven reusable pattern | `library/` |
| Repeatable procedure | `playbooks/` |
| Active domain capability | `apps/<app-id>/` |

## Why `apps/` exists

Some BCOS Cells maintain active domain brains or productized capabilities. These are not just documents. They need local context, prompts, decisions, reports, and proofs.

Use `apps/<app-id>/` when the capability is active and maintained.

Use `library/` only after a pattern has been proven and distilled for reuse.

## Minimal Markdown routing fields

```yaml
bcos_type: task | decision | report | record | proof | handoff | template | index | state | doc | skill | schema
surface: root | inbox | work | decisions | reports | history | proofs | handoffs | human-gates | playbooks | library | apps | templates | schemas | scripts
cell_id: <stable-cell-id>
app_id: <optional-app-id>
owner_id: <human-or-team-id>
agent_scope: none | read | draft | execute | commit
privacy: public | internal | private | sensitive
status: draft | active | ready | done | archived
related:
  - <path-or-id>
```

## First example

See `examples/djbrain-cell/` for an example of an active Cell that contains an app package under `apps/djbrain/`.
