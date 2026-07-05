# Schema — Routing Frontmatter

Every BCOS artifact is a markdown file with YAML frontmatter. The frontmatter
is the routing layer: it lets a human or an agent decide what a file is
without reading it.

## Core profile (required on every artifact)

```yaml
bcos_type: task | decision | report | record | proof | handoff | doc | template | index | state | schema | skill
id: <STABLE-ID>              # never reused, never changed after creation
title: "<human-readable title>"
status: draft | active | ready | done | archived
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
- `record` covers proofs, handoffs, human gates, and history records when a
  dedicated type is not needed; the `kind` field distinguishes them.

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
agent_capability_class: local-worker | chat-reviewer | coding-agent | design-agent | automation
```

Work items add `work_status:`; human gates add `gate_status:`,
`decision_owner_id:`, `decision_owner_display:`, `reviewer_ids:`.

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
