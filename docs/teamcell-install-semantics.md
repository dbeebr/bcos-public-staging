# Teamcell Install Semantics

Defines the Teamcell installation modes, how a target state narrows the
candidate modes, what each mode may and may not do, and the mandatory
preview-before-mutation contract every install satisfies.

## Supported installation flow

```text
1. Preview            scripts/teamcell-install-preview.py <target> [options]      (no writes)
2. Human confirmation the human reviews the preview and explicitly agrees
3. Confirmed install  ... same command ... --confirm --confirmed-by human:<id>
4. Receipt            scripts/generate-teamcell-installation-receipt.py <target>
5. Personalization    scripts/personalize-team-cell.sh <target>                    (optional)
6. Daily start        cd <target> && ./scripts/start-cell.sh
```

`scripts/bootstrap-team-cell.sh` is the low-level copy primitive the installer
calls. Running it directly is not a supported user entry point: it skips the
preview, confirmation, governance file and receipt.

## Modes and release status

| Mode | Release status |
|---|---|
| `new_from_template` | Validated in this public release. |
| `hydrate_existing_repo` | Refused by this public distribution before any preview or write: it has a known defect in this release: its post-install closeout fails (exit 7) after files were written. |
| `clone_existing_cell` | Refused by this public distribution before any preview or write: not validated in this release. |

The refusal is data-driven: a distribution checkout accepts only the modes
listed under `validated_install_modes` in
`distribution/teamcell-lite/SOURCE-MANIFEST.json`. The contracts below still
describe all three modes, because a later release may validate them.

### `new_from_template`

Creates a new Cell from the vendored template kit
(`distribution/teamcell-lite/bootstrap-kit/`), plus any selected optional
packages (`schemas/teamcell-package-manifest.schema.md`).

- **Target precondition (hard):** does not exist, is empty, or contains only
  a bare `.git`. A populated target disqualifies this mode — the installer
  refuses, even when `--mode new_from_template` is given explicitly.
- **Permitted:** full scaffold write of the kit's baseline and selected
  packages, plus `.bcos/CELL-GOVERNANCE.yaml`.
- **Forbidden:** writing into a non-empty target, and falling back to another
  mode when the precondition fails.

### `hydrate_existing_repo` (refused in this public release)

Adds Teamcell scaffolding into an existing, populated repository without
disturbing its content.

- **Target precondition:** an existing repository the human explicitly named
  as the hydration target.
- **Permitted:** create files that do not already exist.
- **Forbidden:** overwriting, deleting or silently merging into existing
  files. Collisions are listed in the preview and left untouched unless the
  human makes an explicit per-file decision (`--include-existing <path>`).
- Never inferred from "target is non-empty" alone.

### `clone_existing_cell` (refused in this public release)

Creates a new Cell from another concrete, already-installed Cell.

- **Source:** an existing Cell (`--clone-source <owner/repo|path>`), resolved
  to an explicit commit SHA. It must be reachable.
- **Target precondition:** empty or populated; the source dictates behavior.
- **Permitted:** full copy, or a human-selected subset (`--clone-paths`).
- **Forbidden:** recording the source Cell as if it were the template. The
  receipt keeps the template-kit provenance in `source` and the source Cell in
  `source.clone_source`.

## Decision criteria

| Signal | `new_from_template` | `hydrate_existing_repo` | `clone_existing_cell` |
|---|---|---|---|
| Target has content beyond a bare `.git`? | No — disqualifying | Yes — defining signal, with explicit selection | Either |
| Source is the template kit? | Yes | Yes | No |
| Source is an existing Cell? | No | No | Yes — defining signal |
| May be inferred automatically? | Emptiness only fails to disqualify; it never confirms | Never | Never — requires an explicit source Cell |

No mode is auto-selected from target emptiness alone. Narrowing to one
candidate yields a *default shown in the preview*, not permission to skip
confirmation.

## Ambiguous instructions

A loose instruction (e.g. `--instruction "install Teamcell Lite"`) never
resolves directly to a mode, source or target.

1. Determine which modes are possible from the target state and explicit
   parameters.
2. Exactly one candidate: render the full preview and still require
   confirmation.
3. More than one candidate: refuse, list every candidate, and require
   disambiguation (`--mode` or `--clone-source`). `--confirm` is never honored
   while a request is ambiguous.
4. No candidate: refuse with an actionable message naming the failed
   precondition. Never fall through to a best guess.

## Mandatory preview contract

Before anything is created, changed or deleted, every install displays:

- source repository, authoritative commit SHA and version label;
- target path and repository;
- installation mode, named explicitly;
- the governance profile to be recorded — including `legacy_unresolved: true`
  when none is selected (the line is never omitted);
- owner and role configuration, including every class left `unresolved`;
- every package to be installed, with its own source commit;
- the exact files to be created or changed (for hydration, the real delta
  against the target, plus collisions);
- the rollback path available afterwards.

**No mutation without a distinct confirmation.** The installer refuses to
write without `--confirm`, and refuses `--confirm` without `--confirmed-by
human:<id>|agent:<id>`. An agent may confirm only on explicit human
instruction for that specific install. Showing the preview and proceeding
without a separate confirmation is non-compliant.

After confirmation, the installer writes an install manifest from which the
receipt is generated (`schemas/teamcell-installation-receipt.schema.md`). The
receipt must not record anything the preview did not show, and the preview
must not promise anything the receipt fails to record.

## Ownership and governance across modes

- `new_from_template`: ownership starts fully unresolved unless the human
  supplies values in the preview step (`--cell-owner-role`,
  `--owner-role CLASS=ROLE`, `--bind-role ROLE=HUMAN_ID[:DISPLAY]`). A profile
  is recorded only with `--governance-profile` plus `--governance-selected-by`;
  otherwise `legacy_unresolved: true`. The template ships no named owner.
- `hydrate_existing_repo`: existing governance/ownership state is never
  overwritten; if none exists, it starts unresolved.
- `clone_existing_cell`: the source Cell's `TEAM-PROFILE.md` and
  `.bcos/CELL-GOVERNANCE.yaml` do not automatically apply. They are reset to
  unresolved unless the human explicitly opts to carry them over
  (`--carry-over-governance`).

## Preflight

After confirmation and before mutation, `scripts/teamcell-install-preflight.sh`
checks: Git availability, Python 3 with PyYAML, target state, and read access
to every declared source. The GitHub CLI (installed and authenticated) is
required only when a declared source or package is a remote `owner/repo`;
installing from a clone of this distribution needs no GitHub login. VS Code
is reported as optional — any editor works. Each failed check exits non-zero
with actionable repair text, never a stack trace. The installer also refuses
up front, with a repair hint and exit code 5, when PyYAML is missing. A manual fallback (`--manual`) prints the
equivalent checklist for environments that cannot run a check live; the check
is still reported, never silently skipped.

## Closeout

After a confirmed mutation the installer runs the Cell's
`scripts/validate-cell.sh`, a non-interactive `scripts/start-cell.sh` smoke
test, a whitespace check, and a reconciliation that every working-tree path is
accounted for by the install. Results are written to
`.installation/INSTALL-CLOSEOUT-PROOF.md`. On failure the Cell is preserved,
not deleted.

## Installer exit codes

| Code | Meaning |
|---|---|
| 0 | Installed and closeout passed |
| 2 | Preview only — not confirmed |
| 3 | Ambiguous request refused |
| 4 | Refused — no valid candidate or failed precondition |
| 5 | Preflight failed |
| 6 | Mutation failed (target may be partially written) |
| 7 | Closeout failed (Cell preserved) |
| 64 | Usage error (e.g. `--confirm` without `--confirmed-by`) |
