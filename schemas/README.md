# Schemas

Field contracts for BCOS artifacts. These are written as markdown contracts —
readable by people, checkable by simple scripts — not as enforced tooling.

| Schema | Governs |
|---|---|
| `routing-frontmatter.schema.md` | the YAML frontmatter every artifact carries |
| `completion-record.schema.md` | the record that makes a task actually done |

The contracts are tiered. The **core profile** is what this starter teaches
and what the examples demonstrate. The **operating profile** adds
actor-identity and status fields for Cells run by teams and agents. The
**federation profile** is experimental — documented so tooling can adopt it
deliberately, required nowhere.
