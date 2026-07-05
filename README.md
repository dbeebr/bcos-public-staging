# BCOS — Base Context Operating System

BCOS is a coordination layer for distributed work between humans, AI agents, teams, tools, and time.

It helps turn work context into executable, reviewable operating memory.

## The Problem

Work now spreads across chats, repositories, documents, issues, meetings, agents, and long-running decisions. The context exists, but it is rarely in a form that another human or AI agent can safely use.

Chat history is not enough. It is too chronological, too noisy, and too hard to verify.

BCOS gives work a structure that can survive handoffs.

## What BCOS Is

BCOS is a markdown-native operating model for:

- tasks as executable contracts;
- decisions as durable truth;
- handoffs as continuation records;
- context indexes as routing layers;
- evidence as the standard for completion;
- Human Gates for sensitive or high-cost choices;
- public/private boundaries for responsible release.

BCOS is designed to be readable by people and executable by agents.

## What BCOS Is Not

BCOS is not:

- a chat archive;
- a project-management app;
- an autonomous-agent hype layer;
- a replacement for human judgment;
- a place to dump every document;
- a guarantee that all context should be public.

## How BCOS Compounds

The longer a Cell operates under BCOS, the more its Library grows. Templates get validated. Decision patterns get proven. Handoff records accumulate. Future Cells — and future agents — can start from that Library rather than blank state.

The system sequence:

```text
Work happens inside a Cell
  → Routers (Context Index, agent config) direct attention
  → Tasks, Decisions, Handoffs, Proofs record what happened
  → Human Gates protect sensitive judgment
  → The best patterns are distilled into the Library
  → The Library makes future work faster and more reliable
```

BCOS is not a template set you copy once. It is an operating layer where structured work produces compounding, reusable value. See `docs/library.md` for the full Library concept, `docs/cell-story.md` for a narrative walkthrough of how Cells grow, and `docs/why-these-surfaces.md` for the reasoning behind each surface — why Library exists, why History and Reports are separate, and why there is no top-level code surface.

## Five-Minute Mental Model

1. **Context is operational capital.** Preserve only what future work needs.
2. **Git is the durable source of truth.** Chat can suggest; committed artifacts decide.
3. **Tasks are contracts.** A task says what to read, what to do, what not to do, and how to prove completion.
4. **Decisions change future assumptions.** If it is not decided, treat it as proposed.
5. **Evidence beats claims.** Completion requires proof appropriate to the task.
6. **Human Gates protect judgment.** Public, legal, private, irreversible, or costly steps require explicit human approval.
7. **Public surface is curated.** A real operating layer may contain private history that should never be published raw.

## Quickstart

Two paths:

**Operational path** — read `docs/create-a-cell.md`. It takes you from clone
to a working Cell in your first hour: core surfaces, the three contracts
(Context Index, agent contract, team file), your first work loop with a
Completion Record, and the rule for when to add more surfaces.

**Template path** — start with six files:

```text
CONTEXT_INDEX.md              ← use templates/context-index.template.md
tasks/TASK.template.md
decisions/DECISION.template.md
handoffs/HANDOFF.template.md
proofs/PROOF.template.md
human-gates/HUMAN-GATE.template.md
```

Suggested first run:

1. Copy `templates/context-index.template.md` to create your `CONTEXT_INDEX.md`. Fill in what to read first and what not to load by default.
2. Write one task as an executable contract.
3. Record one decision that the task depends on.
4. Complete the task with evidence.
5. Add a handoff so another person or agent can continue without reading the whole history.

To see everything working together, open `examples/djbrain-cell/` — a
complete fictional Cell with a finished work loop and an active app package
under `apps/djbrain/`.

## Example Workflow

```text
1. A person creates TASK-001: "Draft a public contribution guide."
2. The task lists required context: README, license decision, community policy.
3. An agent drafts CONTRIBUTING.md but does not publish anything.
4. Validation checks pass.
5. A Human Gate approves the contribution posture.
6. The final commit and validation record become proof.
7. A handoff records what changed and what remains open.
```

## Repository Map

```text
README.md
LICENSE
CONTRIBUTING.md
CODE_OF_CONDUCT.md
SECURITY.md
SUPPORT.md
docs/
  manifesto.md
  core-model.md
  library.md
  cell-story.md
  why-these-surfaces.md
  public-private-boundary.md
  public-cell-target-structure.md   ← the two-shape model and Cell tiers
  create-a-cell.md                  ← first-hour operational path
templates/
  context-index.template.md
  task.template.md
  decision.template.md
  handoff.template.md
  proof.template.md
  human-gate.template.md
schemas/
  routing-frontmatter.schema.md     ← the tiered frontmatter contract
  completion-record.schema.md       ← what makes work actually done
examples/
  neutral-cell/                     ← the primitives, one folder per artifact type
  djbrain-cell/                     ← a complete operating Cell with apps/djbrain/
```

## Status

BCOS v0.1 is experimental. It is a working standard, not a finished product.

This extraction package is a curated surface: useful enough to try, small enough to understand, and careful enough not to expose private operating history.

Publication of this extraction package requires a separate launch Human Gate. See `docs/public-private-boundary.md`.

## License

The documentation, templates, and examples in this extraction package are released under [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). See `LICENSE` for the full text.
