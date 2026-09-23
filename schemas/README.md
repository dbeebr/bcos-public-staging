# Schemas

Field contracts for BCOS artifacts. These are written as markdown contracts —
readable by people, checkable by simple scripts — not as enforced tooling.

| Schema | Governs |
|---|---|
| `routing-frontmatter.schema.md` | the YAML frontmatter every artifact carries |
| `completion-record.schema.md` | the record that makes a task actually done |
| `teamcell-package-manifest.schema.md` | Teamcell Lite packages: baseline, optional Plus profile, optional Team Capability Pack |
| `teamcell-installation-receipt.schema.md` | the receipt an installed Teamcell Cell keeps: source, version, packages, files, rollback |
| `teamcell-governance-profile.schema.md` | `.bcos/CELL-GOVERNANCE.yaml`: the three governance profiles |
| `teamcell-cell-ownership.schema.md` | role-based ownership: `cell_owner_role`, `decision_owner_roles`, `role_bindings` |

The four `teamcell-*` schemas are enforced by the installer tools in
`scripts/` and by the validator shipped inside every installed Cell; the
other two are the general BCOS contracts the kit implements.

The contracts are tiered. The **core profile** is what this starter teaches
and what the examples demonstrate. The **operating profile** adds
actor-identity and status fields for Cells run by teams and agents. The
**federation profile** is experimental — documented so tooling can adopt it
deliberately, required nowhere.

## License

All schemas in this directory are MIT-licensed (`../LICENSE`,
`../LICENSES/MIT.txt`) — part of the operative Teamcell Lite Cell package,
not the CC BY 4.0 explanatory documentation.
