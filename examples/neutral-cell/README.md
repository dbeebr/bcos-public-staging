# Neutral Example Cell

This is a neutral, generic example of a BCOS cell. It demonstrates how BCOS
artifacts work together without referencing any real person, organization, or
project.

## What This Cell Contains

```text
examples/neutral-cell/
  README.md                          ← this file
  tasks/example-task.md              ← a completed example task
  human-gates/example-human-gate.md  ← an example Human Gate (open)
  decisions/example-decision.md      ← a recorded decision
  proofs/example-proof.md            ← a proof record
  handoffs/example-handoff.md        ← a handoff record
  library/README.md                  ← a nascent Library with one proven pattern
```

## Scenario

A small documentation team is preparing a contribution guide for an open-source
project. The scenario is intentionally simple and uses only fictional names and
projects. No real people, organizations, clients, or operating systems are
referenced.

## How To Use This Example

Read the files in this order:

1. `tasks/example-task.md` — See how a task is structured as an executable contract
2. `decisions/example-decision.md` — See how a decision is recorded
3. `human-gates/example-human-gate.md` — See how a Human Gate pauses execution for judgment
4. `proofs/example-proof.md` — See how proof is recorded for a completed claim
5. `handoffs/example-handoff.md` — See how a handoff enables continuation

## What This Example Teaches

This is a **primitive-artifact teaching example**. It uses an artifact-type folder
model — one folder per BCOS primitive type — to show how tasks, decisions, handoffs,
proofs, Human Gates, and Library entries work together inside a Cell.

BCOS operating templates may use different operational surfaces. For example, a
team bootstrap template might separate raw intake from executable work, add
routing layers (Context Index, agent configuration), include playbooks for
reusable procedures, and organize durable evidence into a history surface. Both
artifact-type and operating-surface folder models are valid BCOS implementations
at different layers of the system.

This example teaches the building blocks. Operating templates teach how to run a
Cell day-to-day.

## Key Concepts Illustrated

- A task defines allowed and forbidden actions before work begins
- Decisions record choices that change what future work assumes
- Human Gates require explicit human approval before sensitive steps
- Proof records durable evidence, not just confidence
- Handoffs let another person or agent continue without re-reading everything
- A Library grows from proven patterns — the Cell's distilled, reusable operating capital

## Decision Ownership and Agent Authority

Human Gates require an accountable human decision owner. The `decision_owner`
field in every Human Gate identifies the person responsible for the judgment.

Agents — whether AI or automated — may propose, draft, validate, and report.
Agents may not approve Human Gates, accept truth on behalf of the Cell, or make
sensitive changes without explicit human authorization.

This boundary exists because not every step should be automated or delegated.
Human Gates protect the decisions where judgment, accountability, and
irreversibility matter most.
