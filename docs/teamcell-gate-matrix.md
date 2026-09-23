# Teamcell Gate Decision Matrix

Maps the ten canonical decision classes × the three governance profiles to
whether a Human Gate is required and, when it is not, the minimum evidence the
profile still demands.

## Decision classes

These are exactly the `decision_owner_roles` keys in
`schemas/teamcell-cell-ownership.schema.md`. The two lists must stay identical.

| Decision class | Meaning |
|---|---|
| `routine_work` | Normal day-to-day work with no material scope, cost or risk change. |
| `material_scope_change` | The work's scope changes materially from what was agreed. |
| `priority_change` | The relative priority of work changes materially. |
| `budget_change` | Cost or budget changes materially. |
| `customer_promise` | A commitment is made to a customer (delivery, feature, SLA, pricing). |
| `legal_privacy` | Legal exposure or personal-data handling changes. |
| `people_impacting` | The decision materially affects a person's role, workload, standing or livelihood. |
| `irreversible_action` | The action cannot be cheaply undone (data deletion, irreversible external commitment). |
| `security_change` | Security posture, access control or credential handling changes. |
| `external_visibility` | Output becomes visible outside the Cell. |

## Matrix

"Evidence" is the minimum required when the class is not gated. "Standard
Completion Record" refers to `schemas/completion-record.schema.md`.

| Decision class | `quick_build` gate | `quick_build` evidence | `operating_team` gate | `operating_team` evidence | `compliance_safety` gate |
|---|---|---|---|---|---|
| `routine_work` | No | Lightweight work item entry; Git provenance mandatory. | No | Standard Completion Record. | **Yes** |
| `material_scope_change` | No | Lightweight work item entry with an explicit scope note; Git provenance mandatory. | **Yes** | — | **Yes** |
| `priority_change` | No | Lightweight work item entry with an explicit priority note; Git provenance mandatory. | **Yes** | — | **Yes** |
| `budget_change` | **Yes** | — | **Yes** | — | **Yes** |
| `customer_promise` | No | Lightweight work item entry with an explicit customer note; Git provenance mandatory. | **Yes** | — | **Yes** |
| `legal_privacy` | **Yes** | — | **Yes** | — | **Yes** |
| `people_impacting` | **Yes** | — | **Yes** | — | **Yes** |
| `irreversible_action` | **Yes** | — | **Yes** | — | **Yes** |
| `security_change` | **Yes** | — | No | Standard Completion Record plus an explicit reviewer note naming the engineering-review or release process that substituted for a Human Gate. | **Yes** |
| `external_visibility` | **Yes** | — | No | Standard Completion Record plus an explicit reviewer note naming the release process that substituted for a Human Gate. | **Yes** |

`compliance_safety` gates every class, so it has no evidence column.

## The `security_change` / `external_visibility` asymmetry

`quick_build` gates these two classes; `operating_team` does not. This is
intentional:

- A `quick_build` Cell has not yet established routine engineering
  discipline, so catastrophic-risk classes get a hard safety net even though
  most work is ungated.
- An `operating_team` Cell is expected to have normal engineering process
  (code review, a real release process) that catches security and
  external-visibility risk. Its gates are reserved for business-impact
  classes that engineering process does not naturally catch: scope,
  priority, budget, customer, legal/privacy, people and irreversible actions.

A team that wants these two classes hard-gated on top of normal operation
selects `compliance_safety`. Tools must not reinterpret `operating_team`.

## `compliance_safety`

`compliance_safety` hard-gates all governed mutations with no implicit
authority, including `routine_work`. It has no ungated class. Any narrowing
of this set is a governance decision that must amend this document
explicitly; it may not be inferred by tooling.

## Consuming the matrix

To decide whether a decision needs a Human Gate:

1. Read `governance_profile` from `.bcos/CELL-GOVERNANCE.yaml`
   (`schemas/teamcell-governance-profile.schema.md`).
2. Classify the decision into exactly one of the ten classes.
3. Look up the cell in the matrix.

If `governance_profile` is `null` (`legacy_unresolved: true`), no column
applies. That absence is surfaced as a blocking, visible state — never
defaulted to any profile's column.

When a gate is required, it is routed to the role named in
`decision_owner_roles.<class>`, or reported as blocked per the ownership
schema's two unresolved states (class unresolved, or role unbound). A gate is
never routed to a hardcoded person.

## Out of scope

- A machine-readable twin of this table or a routing script that reads it.
  This document is the canonical source either way.
- Adding, removing or redefining a decision class without the matching change
  to the ownership schema.
