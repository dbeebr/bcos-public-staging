# Public Cell Target Structure

BCOS public starter has two jobs:

1. explain the operating model;
2. give a complete example Cell that a person or agent can copy and run.

The public repository root is not the user's Cell. It is the distribution
package.

## Public starter repo

```text
README.md
LICENSE
CONTRIBUTING.md
CODE_OF_CONDUCT.md
SECURITY.md
SUPPORT.md
docs/
  manifesto.md  core-model.md  cell-story.md  library.md
  why-these-surfaces.md  public-private-boundary.md
  public-cell-target-structure.md  create-a-cell.md
templates/
schemas/
examples/
  neutral-cell/      ← the primitives, one folder per artifact type
  setbrain-cell/      ← a complete operating Cell with an app package
```

## Active Cell repo — three tiers, not one flat wall

A Cell does not start with every folder. It starts with the core tier and adds
surfaces when they earn their place. This tiering comes from operating
evidence: real two-person Cells run on Tier 1 alone; agent-operated Cells grow
into Tier 2; Cells that maintain a domain brain add Tier 3.

**Tier 1 — Core (every Cell):**

```text
README.md  PROJECT.md  AGENTS.md  CONTEXT_INDEX.md  TEAM.md
inbox/     work/     human-gates/     history/     playbooks/     scripts/
```

Artifact templates live *in-surface* (`work/TEMPLATE.task.md`,
`human-gates/TEMPLATE.human-gate.md`) — where agents already look. A separate
`templates/` folder is a distribution-package surface, not a Cell default.

**Tier 2 — Operating expansion (when unfamiliar contributors or agents
operate the Cell):**

```text
decisions/   reports/   proofs/   handoffs/   library/
```

**Tier 3 — Capability expansion (per active domain capability):**

```text
apps/
  <app-id>/
    README.md
    CONTEXT_INDEX.md
    knowledge/   prompts/   reports/   proofs/
```

## Routing rules

| Intent | Target | Tier |
|---|---|---|
| Raw unprocessed input | `inbox/` (append to `INBOX.md`) | 1 |
| Executable work | `work/` | 1 |
| Human decision before action | `human-gates/` | 1 |
| Chronological record | `history/` | 1 |
| Repeatable procedure | `playbooks/` | 1 |
| Cell infrastructure (validators, helpers) | `scripts/` | 1 |
| Recorded, findable decision | `decisions/` | 2 |
| Analysis | `reports/` | 2 |
| Completion evidence | `proofs/` | 2 |
| Continuation record | `handoffs/` | 2 |
| Proven reusable pattern | `library/` | 2 |
| Active domain capability | `apps/<app-id>/` | 3 |

## The `apps/` rule

Some Cells maintain active domain brains: knowledge an agent queries while
doing other work — a brand brain, a product brain, a domain expert package.
These are not passive documents.

- Use **`apps/<app-id>/`** when the capability is active and maintained: it
  gets its own README, context index, knowledge, prompts, and proof loop.
- Use **`library/`** only for passive, proven, distilled patterns.
- **Promotion:** domain knowledge starts as `work/` items; when agents start
  treating it as a queryable capability, a human gate approves promotion to
  `apps/<app-id>/`.
- **Distillation:** patterns proven inside an app get *copied* to `library/`;
  the operating original stays in the app.
- **Demotion:** an unmaintained app package is archived to `history/` or
  reduced to its `library/` remains — recorded as a decision.

`examples/setbrain-cell/` shows the full shape, including the promotion
decision record (`decisions/DECISION-20260701-001-setbrain-app-package.md`).

## Markdown routing fields

The full tiered contract lives in `schemas/routing-frontmatter.schema.md`.
The short version — every artifact carries the core profile:

```yaml
bcos_type: task | decision | report | record | proof | handoff | doc | template | index | state | schema | skill
id: <STABLE-ID>
title: "<title>"
status: draft | active | ready | done | archived
created: YYYY-MM-DD
created_by: <human-or-agent-id>
surface: <folder-surface>
related:
  - <path-or-id>
```

Team- and agent-operated Cells add the actor-identity operating profile.
Four further fields (`cell_id`, `app_id`, `privacy`, `agent_scope`) are an
experimental federation profile: documented in the schema, required nowhere.
A new user should be able to write a valid artifact after reading only the
core profile.

## Two examples, two layers

- `examples/neutral-cell/` teaches the **primitives**: one folder per artifact
  type, minimal moving parts.
- `examples/setbrain-cell/` teaches the **operating shape**: tiered surfaces,
  a complete work loop with proof and handoff, and an app package.

Read neutral-cell to understand the pieces. Copy setbrain-cell to start
operating.
