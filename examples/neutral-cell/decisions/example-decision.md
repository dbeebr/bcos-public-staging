---
id: DECISION-20260101-001
title: "Scope contribution guide to docs and templates only"
status: decided
created: 2026-01-01
created_by: human:morgan
decided_by: human:morgan
decision_date: 2026-01-01
scope: contribution guide for example-project v0.1
---

# DECISION-20260101-001 — Scope Contribution Guide to Docs and Templates Only

## Decision

The contribution guide for `example-project` will accept contributions for
documentation and templates only. Architecture and runtime code contributions
will require maintainer review and a separate Human Gate.

## Context

`example-project` is in early experimental status. Accepting broad code
contributions before the architecture is stable could create maintenance burden
and compatibility conflicts. Community feedback is most useful in the docs and
templates layer at this stage.

## Options Considered

- **Option A: Accept all contributions** — Open the project to all contribution
  types. Pros: maximum community engagement. Cons: high review burden; architecture
  churn risk.
- **Option B: Docs and templates only (chosen)** — Limit public contributions to
  documentation and templates. Pros: lower risk; focused feedback. Cons: some
  contributors may feel excluded.
- **Option C: No external contributions** — Keep the project read-only. Pros:
  simplest. Cons: misses community feedback entirely.

## Rationale

Option B gives the project useful early feedback on the most accessible parts
of BCOS while protecting the core architecture from premature instability.

## Scope

This decision governs the v0.1 experimental contribution guide. It does not
govern future versions or any architecture decisions.

## Reversal Conditions

Revisit this decision when the architecture has stabilized and a maintainer
is available to review code contributions consistently.

## Evidence

- Decided by: Morgan
- Source: discussion of project readiness
- Date: 2026-01-01
