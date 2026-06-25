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

## Five-Minute Mental Model

1. **Context is operational capital.** Preserve only what future work needs.
2. **Git is the durable source of truth.** Chat can suggest; committed artifacts decide.
3. **Tasks are contracts.** A task says what to read, what to do, what not to do, and how to prove completion.
4. **Decisions change future assumptions.** If it is not decided, treat it as proposed.
5. **Evidence beats claims.** Completion requires proof appropriate to the task.
6. **Human Gates protect judgment.** Public, legal, private, irreversible, or costly steps require explicit human approval.
7. **Public surface is curated.** A real operating layer may contain private history that should never be published raw.

## Quickstart With Templates

Start with five files:

```text
CONTEXT_INDEX.md
tasks/TASK.template.md
decisions/DECISION.template.md
handoffs/HANDOFF.template.md
proofs/PROOF.template.md
```

Suggested first run:

1. Create a small `CONTEXT_INDEX.md` that says what to read first and what not to load by default.
2. Write one task as an executable contract.
3. Record one decision that the task depends on.
4. Complete the task with evidence.
5. Add a handoff so another person or agent can continue without reading the whole history.

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

Recommended public v0.1 structure:

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
  public-private-boundary.md
templates/
  task.template.md
  decision.template.md
  handoff.template.md
  proof.template.md
  human-gate.template.md
examples/
  neutral-cell/
```

## Status

BCOS v0.1 is experimental. It is a working standard, not a finished product.

This extraction package is a curated surface: useful enough to try, small enough to understand, and careful enough not to expose private operating history.

Publication of this extraction package requires a separate launch Human Gate. See `docs/public-private-boundary.md`.

## License

The documentation, templates, and examples in this extraction package are released under [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). See `LICENSE` for the full text.
