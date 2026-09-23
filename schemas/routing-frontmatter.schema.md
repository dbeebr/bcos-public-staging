# Schema — Routing Frontmatter

Every BCOS artifact is a markdown file with YAML frontmatter. The frontmatter
is the routing layer: it lets a human or an agent decide what a file is
without reading it.

## Core profile (required on every artifact)

```yaml
bcos_type: task | proposal | decision | council | review | brief | doc | synthesis | report | record | skill | schema | template | index | state | genesis_record
id: <STABLE-ID>              # never reused, never changed after creation
title: "<human-readable title>"
status: <lifecycle value>    # see "Lifecycle fields" below
created: YYYY-MM-DD
created_by: <human-or-agent-id>
```

Recommended on every routed artifact:

```yaml
surface: inbox | work | decisions | reports | history | proofs | handoffs | human-gates | playbooks | library | apps | project
related:
  - <path-or-id>             # the artifacts this one depends on or answers
```

Notes:

- Put specificity in `kind:` (for example `kind: human_gate`,
  `kind: playbook`, `kind: pattern`), not in new `bcos_type` values.
- `record` covers proofs, handoffs and history records; human gates are a
  `proposal` with `kind: human_gate`. The `kind` field distinguishes them —
  `proof` and `handoff` are kinds, not types.
- Two further types exist only for Teamcell personalization output:
  `app_instruction_block` and `prompt`. Do not use them elsewhere.

## Lifecycle fields

`status` records artifact trust. Recommended values: `draft | reviewed |
accepted`; guides, contracts and indexes that are in force use `active`. The
starter examples also use descriptive end states such as `done`, `decided`
or `archived`; any value is valid in the core profile as long as it is used
consistently within a Cell.

In team- and agent-operated Cells (the operating profile, implemented by the
Teamcell Lite kit under `distribution/teamcell-lite/`):

- work items add `work_status: open | in-progress | needs-review | done` —
  `done` only together with a complete Completion Record
  (`completion-record.schema.md`);
- human gates add `gate_status: draft | open | accepted | changes-requested |
  rejected | withdrawn`. The starter examples' `pending-human-decision`
  corresponds to `open`, and `approved` to `accepted`.

## Operating profile (team- and agent-operated Cells)

Actor identity — required on artifacts in governed surfaces:

```yaml
created_by_type: human | agent | system
created_by_id: human:<id> | agent:<id> | system:<id>
created_by_display: "<display name>"
on_behalf_of_human_id: human:<id> | null   # agents always act for a human
```

Agent-written artifacts additionally:

```yaml
agent_id: agent:<id>
agent_model: <model-or-tool>
agent_capability_class: local-worker | git-only-worker | chat-reviewer | read-only-observer | automation
```

`agent_capability_class` records the access the writer actually had, not its
product or model name: local shell and Git (`local-worker`), Git connector
only (`git-only-worker`), no verifiable write access (`chat-reviewer`),
inspect-only (`read-only-observer`), or an unattended script (`automation`).
The earlier values `coding-agent` and `design-agent` are legacy; the
Teamcell validator accepts them with a warning.

Work items add `work_status:`; human gates add `gate_status:`,
`decision_class:`, `decision_owner_role:`, `decision_owner_id:`,
`decision_owner_display:`, `reviewer_ids:` (see
`teamcell-cell-ownership.schema.md` for unresolved and unbound owners).

## Federation profile (experimental — adopt deliberately, required nowhere)

```yaml
cell_id: <stable-cell-id>    # only meaningful for multi-cell tooling
app_id: <app-id>             # recommended for artifacts under apps/<app-id>/
privacy: public | internal | private | sensitive   # useful when public extraction is planned
agent_scope: none | read | draft | execute | commit  # not enforced by any current tooling
```

## Design rule

A new user should be able to write a valid artifact after reading only the
core profile. Everything beyond it must earn its place in your Cell the same
way folders do: added when a real operating problem demands it.
