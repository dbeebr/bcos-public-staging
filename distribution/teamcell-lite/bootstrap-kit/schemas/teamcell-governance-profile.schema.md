---
bcos_type: schema
id: TEAMCELL-KIT-SCHEMA-GOVERNANCE-PROFILE
title: "Teamcell Governance Profile Schema (kit copy)"
status: active
created: 2026-09-22
created_by: claude-sonnet-5
created_by_type: agent
created_by_id: agent:claude-sonnet-5
created_by_display: "Claude Sonnet 5"
agent_id: agent:claude-sonnet-5
agent_model: claude-sonnet-5
agent_capability_class: local-worker
---

# Schema — Teamcell Governance Profile

> Kit-local copy, shipped so `docs/teamcell-gate-matrix.md`,
> `.bcos/CELL-GOVERNANCE.yaml.template` and `TEAM-PROFILE.md`'s own in-kit
> references resolve inside an installed Cell. Source of truth for edits is
> the public distribution's schemas/teamcell-governance-profile.schema.md —
> update there first, then re-sync here.

Defines `.bcos/CELL-GOVERNANCE.yaml`: the per-Cell, machine-readable record of
which governance profile the Cell has selected, its ownership configuration,
and who selected it and when. Values shown as examples are not defaults.

## File location and format

`.bcos/CELL-GOVERNANCE.yaml` at the Cell root. Plain YAML (not Markdown with
frontmatter) so shell or Python validators can parse it directly.

The template kit ships `.bcos/CELL-GOVERNANCE.yaml.template` with every field
unresolved. The installer writes `.bcos/CELL-GOVERNANCE.yaml` only if the
target does not already have one. Until the real file exists, its absence is a
valid pre-configuration state — never an error, and never licence to assume a
profile.

## Object shape

```yaml
schema_version: "0.1"

governance_profile: quick_build | operating_team | compliance_safety | null
legacy_unresolved: true | false

cell_owner_role: <role-slug> | null
decision_owner_roles:          # all ten classes, see ownership schema
  routine_work: <role-slug> | unresolved
  # ... remaining nine classes ...
role_bindings:
  <role-slug>:
    human_id: human:<id> | null
    display_name: <name> | null
    bound_at: <YYYY-MM-DD> | null
    bound_by: human:<id> | agent:<id> | null

selected_at: <YYYY-MM-DD> | null
selected_by: human:<id> | agent:<id> | null

profile_recommendation:        # optional; may be null
  recommended_profile: quick_build | operating_team | compliance_safety | null
  status: recommended_pending_confirmation | confirmed | overridden | null
  rationale: <string> | null
  recorded_at: <YYYY-MM-DD> | null
  recorded_by: human:<id> | agent:<id> | null
  confirming_gate: <repo-relative path to human-gates/*.md> | null
```

## Fields

| Field | Required | Rule |
|---|---|---|
| `schema_version` | yes | Schema version the file was written against, e.g. `"0.1"`. |
| `governance_profile` | yes | One of the three profiles, or `null`. `null` only together with `legacy_unresolved: true`. |
| `legacy_unresolved` | yes | `true` while no profile has been explicitly selected; `false` once a profile, `selected_at` and `selected_by` are set. |
| `cell_owner_role`, `decision_owner_roles`, `role_bindings` | yes | Same shape and semantics as `schemas/teamcell-cell-ownership.schema.md`. Before ownership is configured: `cell_owner_role: null`, every class `unresolved`, `role_bindings: {}`. |
| `selected_at` | when profile set | Date a human explicitly selected the profile; else `null`. |
| `selected_by` | when profile set | Who made the selection; else `null`. `agent:<id>` only when acting on explicit human instruction for this selection. |
| `profile_recommendation` | no | See below. |

### Profiles

| Profile | Intended use |
|---|---|
| `quick_build` | Early exploration and low-risk work. |
| `operating_team` | Default recommendation for normal team work. |
| `compliance_safety` | Regulated or high-risk work. |

Which decision classes require a Human Gate under each profile is defined in
`docs/teamcell-gate-matrix.md`; this schema only defines how a profile is
selected.

### `legacy_unresolved` is a valid state

`legacy_unresolved: true` is a first-class, valid, permanent-if-unaddressed
state — not an error that forces an immediate choice. No tool may silently
pick a profile (including `operating_team` "because it is the recommended
default"). A tool may *recommend*; only a recorded human decision sets
`governance_profile` or flips `legacy_unresolved` to `false`.

### `profile_recommendation`

Used when a tool has a basis to recommend a profile for an unresolved Cell
without assigning it.

- `status: recommended_pending_confirmation` — awaiting a human decision.
- `status: confirmed` — a human accepted it. Updating `governance_profile` and
  `legacy_unresolved` is a separate, explicit, human-triggered write, not a
  side effect of setting the status.
- `status: overridden` — a human chose a different profile.
- `confirming_gate` — the Human Gate file tracking the open decision, or
  `null` if none is open yet.

Omit the block (or set it to `null`) for a fresh Cell where a human selects a
profile directly during setup.

## Relationship to the installation receipt

At install time the installer snapshots this file's governance block into the
receipt's `governance` section (`schemas/teamcell-installation-receipt.schema.md`).
The receipt is a point-in-time record; `.bcos/CELL-GOVERNANCE.yaml` remains the
live source of truth and may change later (e.g. a profile is selected) without
a new receipt.

## Validation expectations

- `governance_profile` is one of the three values or `null`.
- `governance_profile` is `null` if and only if `legacy_unresolved: true`.
- If `governance_profile` is non-null, `selected_at` and `selected_by` are
  both non-null.
- The ownership block passes the ownership schema's checks.
- `profile_recommendation.status: confirmed` never coexists with
  `legacy_unresolved: true` and `governance_profile: null`.

## Example (illustrative, not a default)

```yaml
schema_version: "0.1"
governance_profile: null
legacy_unresolved: true
cell_owner_role: founder
decision_owner_roles:
  routine_work: founder
  material_scope_change: founder
  priority_change: founder
  budget_change: founder
  customer_promise: founder
  legal_privacy: founder
  people_impacting: founder
  irreversible_action: founder
  security_change: founder
  external_visibility: founder
role_bindings:
  founder:
    human_id: human:example-founder
    display_name: "Example Founder"
    bound_at: 2026-07-14
    bound_by: human:example-founder
selected_at: null
selected_by: null
profile_recommendation:
  recommended_profile: operating_team
  status: recommended_pending_confirmation
  rationale: "Example: single-founder Cell moving toward normal team operation."
  recorded_at: 2026-07-14
  recorded_by: agent:example-agent
  confirming_gate: human-gates/example-confirm-governance-profile.md
```

Resolved ownership, unresolved profile, recommendation awaiting confirmation.
