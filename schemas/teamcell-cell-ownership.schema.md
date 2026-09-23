# Schema — Teamcell Cell Ownership

A role-first ownership model for a Teamcell Lite Cell. Decision authority is
expressed as generic role slugs bound to participants, never as a flat
person-named owner string. Every name or role in this document is an example,
not a default.

## Where this model lives

The same ownership block appears in two places and must be kept identical:

1. **`TEAM-PROFILE.md` frontmatter** — the human-authored, Git-visible copy,
   alongside the existing `participants[]` array and legacy flat fields.
2. **`.bcos/CELL-GOVERNANCE.yaml`** — the machine-parsed copy
   (`schemas/teamcell-governance-profile.schema.md`).

Once a Cell adopts this model it must not define these fields in only one of
the two locations.

## Object shape

```yaml
cell_owner_role: <role-slug>

decision_owner_roles:
  routine_work: <role-slug> | unresolved
  material_scope_change: <role-slug> | unresolved
  priority_change: <role-slug> | unresolved
  budget_change: <role-slug> | unresolved
  customer_promise: <role-slug> | unresolved
  legal_privacy: <role-slug> | unresolved
  people_impacting: <role-slug> | unresolved
  irreversible_action: <role-slug> | unresolved
  security_change: <role-slug> | unresolved
  external_visibility: <role-slug> | unresolved

role_bindings:
  <role-slug>:
    human_id: human:<id> | null
    display_name: <name> | null
    bound_at: <YYYY-MM-DD> | null
    bound_by: human:<id> | agent:<id> | null
```

## Fields

| Field | Required | Rule |
|---|---|---|
| `cell_owner_role` | yes, single | Snake_case role slug (e.g. `founder`, `lead`, `maintainer`) holding default decision authority. Never a person's name; never the literal `unresolved`. |
| `decision_owner_roles` | yes, all ten keys | Each canonical decision class maps to a role slug or the literal `unresolved`. Omitting a key is invalid. |
| `role_bindings` | yes | Every role slug referenced by `cell_owner_role` or a non-`unresolved` class value must have an entry, even when unbound. |
| `role_bindings.*.human_id` | yes | `human:<id>` of the bound participant, or `null` if unbound. |
| `role_bindings.*.display_name` | yes | Display name mirror; `null` when `human_id` is `null`. |
| `role_bindings.*.bound_at` | yes | Date the binding was set; `null` when unbound. |
| `role_bindings.*.bound_by` | yes | Who set the binding; `null` when unbound. An agent may record a binding only on explicit human instruction. |

The ten decision class keys are exactly those of `docs/teamcell-gate-matrix.md`.
A class value need not equal `cell_owner_role`; a class may be delegated to a
different role (e.g. `legal_privacy: legal_advisor`). A class whose value
equals `cell_owner_role` defers to the Cell's default owner role.

## The two unresolved states

Tools must keep these two states distinguishable:

| State | Shape | Human Gate for that class |
|---|---|---|
| Decision class unresolved | `decision_owner_roles.<class>: unresolved` | cannot be routed; surfaced as blocked pending role assignment |
| Role unbound | `<class>: <role-slug>` and `role_bindings.<role-slug>.human_id: null` | surfaced as blocked pending appointment |

**Hard rule:** neither state may be silently defaulted to any name — no real
participant, no prior owner, no placeholder that looks like a name. The only
valid representations of "no one assigned" are `unresolved` and
`human_id: null`. A tool that cannot resolve an owner renders one of these two
states; it never guesses.

## Composition with `TEAM-PROFILE.md` participants

`participants[]` remains the single source of truth for who is on the Cell:

```yaml
participants:
  - human_id: human:<id>
    display_name: <name>
    github: <username> | null
    role: <org-facing label, e.g. owner | collaborator>
    decision_authority: true | false
```

- A non-null `role_bindings.<slug>.human_id` must reference a `human_id`
  present in `participants[]`; otherwise it is a dangling, invalid reference.
- `participants[].role` is an org-facing vocabulary, separate from the
  decision-class role slugs; the two need not share values. One person may
  hold several bindings, or each role may be held by a different person.
- The existing rule that exactly one participant carries
  `decision_authority: true` is unchanged. Keeping that participant equal to
  the `cell_owner_role` binding is recommended, not mandated.

## Legacy flat-field mirroring

The flat fields `decision_owner`, `decision_owner_id` and
`decision_owner_display` in `TEAM-PROFILE.md` are retained for older tooling,
but only as a derived mirror of `role_bindings.<cell_owner_role>`:

- bound owner role: `human_id` → `decision_owner_id`; `display_name` →
  `decision_owner` and `decision_owner_display`;
- unbound owner role: all three flat fields are `null`. A flat field showing a
  name while the binding is unbound is a drift defect.

## Validation expectations

A conforming validator checks at least:

- `cell_owner_role` is present, non-empty and not `unresolved`;
- `decision_owner_roles` has exactly the ten canonical keys;
- every referenced role slug has a `role_bindings` entry;
- every non-null `human_id` resolves to a `participants[]` row;
- legacy flat fields, if present, follow the mirroring rule.

## Example (illustrative, not a default)

```yaml
cell_owner_role: lead
decision_owner_roles:
  routine_work: lead
  material_scope_change: lead
  priority_change: lead
  budget_change: unresolved
  customer_promise: lead
  legal_privacy: legal_advisor
  people_impacting: lead
  irreversible_action: lead
  security_change: unresolved
  external_visibility: lead
role_bindings:
  lead:
    human_id: human:example-lead
    display_name: "Example Lead"
    bound_at: 2026-07-14
    bound_by: human:example-lead
  legal_advisor:
    human_id: null
    display_name: null
    bound_at: null
    bound_by: null
```

This shows all three states: a bound default role (`lead`), a class delegated
to an unbound role (`legal_privacy`), and classes with no role chosen
(`budget_change`, `security_change`).

## Out of scope

- Multiple humans bound to one role.
- The mechanism that keeps the two copies in sync.
