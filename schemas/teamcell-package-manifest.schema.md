# Schema — Teamcell Package Manifest

Defines which package owns which path in the Teamcell Lite template kit, so a
baseline-only install copies only baseline paths and optional packages are
copied only when explicitly selected.

The manifest lives at `packages/PACKAGES.yaml` inside the kit
(`distribution/teamcell-lite/bootstrap-kit/packages/PACKAGES.yaml`) and is
installed into every Cell as reference metadata.

## Shape

```yaml
schema_version: "0.1"
packages:
  - package_id: <string>            # stable slug; matches installed_packages[].package_id in the receipt
    optional: <boolean>             # false for exactly one package (the baseline)
    depends_on: [<package_id>]      # packages that must also be selected
    source_root: <path>             # kit-relative root of this package's files
    target_root: <path>             # Cell-relative install root; "." = same relative path
    exclude_source_roots: [<path>]  # sub-paths owned by a different package
    installer: <path>               # optional; script used instead of a 1:1 copy
    onboarding_entries: [<path>]    # Cell-relative onboarding pages that exist iff installed
    onboarding_source: <path>       # optional; source of an onboarding entry that is not a 1:1 copy
    description: <string>
```

## Rules

1. Exactly one package has `optional: false` — the baseline. Its
   `exclude_source_roots` covers every optional package's source, so the
   baseline and optional packages partition the kit with no overlap.
2. `depends_on` is resolved by auto-selecting the dependency, never by
   refusing the install.
3. A Cell's receipt `installed_packages` lists exactly the baseline plus every
   selected optional package, including auto-selected dependencies — never a
   package whose files are absent, never files present without their owning
   package declared.
4. An `onboarding_entries` path exists on disk only while its package is
   installed. No onboarding page may link to an uninstalled package.
5. Ownership is prefix-based. Adding a file inside a declared `source_root`
   (and outside any nested `exclude_source_roots`) never requires a manifest
   edit.
6. Unknown package ids, or selecting a non-optional package as optional, are
   refused by the installer.

## Teamcell Lite packages

| `package_id` | Optional | Depends on | Source root | Installs to | Content |
|---|---|---|---|---|---|
| `teamcell-lite-baseline` | no — always installed | — | `.` (excluding `profiles/plus`) | `.` | The complete Lite Cell, copied 1:1. |
| `teamcell-plus-profile` | yes | — | `profiles/plus` (excluding the capability pack) | `.` | Additive overlay (extra scripts, `ONBOARDING.md`, `docs/CONTRACTS-V1.md`, learning-candidate history). Never rewrites a baseline file except one `CONTEXT_INDEX.md` append. Uses its own installer script. |
| `team-capability-pack` | yes | `teamcell-plus-profile` | `profiles/plus/apps/team-capability-pack` | `apps/team-capability-pack` | Opt-in app with three bounded skills plus the `playbooks/onboarding/SKILL-PLAYGROUND.html` onboarding page. Uses its own installer script. |

Selecting `team-capability-pack` auto-selects `teamcell-plus-profile`.
Optional packages are selected at install time with
`--optional-package <package_id>` (repeatable) on
`scripts/teamcell-install-preview.py`; the preview lists every package that
will be installed before anything is written.

## Reconciliation rule

An installed Cell must match its declared packages structurally. A mismatch
in either direction is a failure, not a warning.

| Path in the Cell | Must be present iff |
|---|---|
| `profiles/` | never — distribution source material, not installed |
| `ONBOARDING.md`, `docs/CONTRACTS-V1.md` | `teamcell-plus-profile` installed |
| `apps/team-capability-pack/` | `team-capability-pack` installed |
| `playbooks/onboarding/SKILL-PLAYGROUND.html` | `team-capability-pack` installed |

These checks are enforced in two places:

- `scripts/generate-teamcell-installation-receipt.py` refuses to write a
  receipt when `installed_packages` and the installed tree disagree.
- `scripts/validate-cell.sh`, shipped inside every Cell, re-derives the same
  expectations from well-known paths (it does not parse the manifest at
  runtime) and fails on any mismatch.

## Conformance

`scripts/teamcell-install-preview.py` resolves package selection against this
manifest for `new_from_template` installs.
