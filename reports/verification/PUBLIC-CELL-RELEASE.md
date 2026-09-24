# Release Verification — Teamcell Lite v0.4 (teamcell-lite-v0.4.0-rc.7)

This report records how the installable Teamcell Lite release candidate in
this repository was verified before publication. It is distribution
evidence: it is not installed into Cells and does not prove anything about a
particular Cell (each installed Cell keeps its own receipt and closeout
proof). Release candidate 7 is a documentation-only alignment update over
candidate 6: it corrects several public-facing descriptions (README,
`docs/public-private-boundary.md`, `SECURITY.md`, `SUPPORT.md`,
`CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` and this report) that still described
the pre-publication state — unpublished, Teamcell Lite excluded, docs-only,
no runtime code — after the staging publication had already happened.
Candidate 6 was itself a documentation-only staging update over candidate 5:
it disclosed two known limitations surfaced by post-candidate-5 real-world
testing (see "Scope and limits" below). Neither candidate 6 nor candidate 7
carries any kit, installer, template or schema change — the kit tree hash is
unchanged since candidate 5. Release candidate 5 itself fixed a real gap
candidate 4's own kit shipped
with: `docs/teamcell-gate-matrix.md` (which decision classes need a Human
Gate under which governance profile) was referenced from four kit files but
never installed into a Cell, so an installed Cell could not answer that
question locally. Candidate 5 ships that file plus the three schemas its own
text operationally depends on
(`schemas/teamcell-governance-profile.schema.md`,
`schemas/teamcell-cell-ownership.schema.md`,
`schemas/completion-record.schema.md`) at the template root, picked up by
the baseline package automatically (source root ".", no
`packages/PACKAGES.yaml` change needed — the same mechanism candidate 4 used
for `LICENSE`). Nothing else changed against candidate 4: same MIT/CC BY 4.0
scope, same handoff-format/role-rule/P3 content; every check below was
re-run from scratch against this release's own tree at the time it was
built, never carried over from an earlier candidate's run. The full checked
chronology: candidate 5 (2026-09-22) introduced this suite's 309 checks and
passed 309/309 against its own tree; candidate 6 (2026-09-23, documentation
only) re-ran the identical, unmodified suite from scratch against its own
tree and again passed 309/309; candidate 7 (2026-09-23, documentation only —
this candidate) again re-ran the identical, unmodified suite from scratch
against its own tree — see "How it was verified" below for its own dated
result. See this file's own revision history for any later candidate.

## What was released

| Part | Location |
|---|---|
| Installable kit (baseline + optional packages) | `distribution/teamcell-lite/bootstrap-kit/` |
| Provenance, version, per-file hashes, kit tree hash | `distribution/teamcell-lite/SOURCE-MANIFEST.json` |
| Installer tools | `scripts/teamcell-install-preview.py`, `teamcell-install-preflight.sh`, `bootstrap-team-cell.sh`, `resolve-cell-identity.py`, `generate-teamcell-installation-receipt.py`, `personalize-team-cell.sh` |
| Contracts | `docs/teamcell-install-semantics.md`, `docs/teamcell-gate-matrix.md`, `docs/project-instruction-inheritance.md`, `schemas/teamcell-*.schema.md` |
| License texts and scope index | `LICENSE`, `LICENSES/MIT.txt`, `LICENSES/CC-BY-4.0.txt`; embedded copy at `distribution/teamcell-lite/bootstrap-kit/LICENSE` |
| Gate matrix + its dependent schemas, embedded in the kit | `distribution/teamcell-lite/bootstrap-kit/docs/teamcell-gate-matrix.md`, `distribution/teamcell-lite/bootstrap-kit/schemas/{teamcell-governance-profile,teamcell-cell-ownership,completion-record}.schema.md` |

Kit tree hash and file count: see `SOURCE-MANIFEST.json` (`kit.tree_sha256`,
`kit.file_count`). The installer recomputes the hash at preview time and
reports `kit_integrity: verified` when it matches.

Two template files are deliberately not part of the kit (listed with reasons
in `SOURCE-MANIFEST.json`): a maintainer-side owner watch list, and a
historical seed validation report of an earlier template version.

Present since candidate 2 (unchanged since; not introduced by this
candidate — verified against candidate 2's own export manifest): every Cell ships one shared project-instruction core
(`templates/PROJECT-INSTRUCTIONS.template.md`), a Cell profile
(`.bcos/CELL-PROFILE.yaml`) and `scripts/render-instructions.py`, which
renders the paste block for app projects (with a ChatGPT size check), a
generated Procedure Index in `CONTEXT_INDEX.md`, and — for local model hosts
— a capability-dependent instruction block, a context pack and a
machine-readable profile.

New in candidate 3: planning may persist tasks and hand authorized execution
over, while implementation stays the execution step, and role, capability
and authority are kept separate. A planner writes tasks in the format of the
Cell's current task template (from the repository, or from a planning context
pack that carries the template) and marks what it does not know as
`OPEN: ...`. Before execution a task passes a format check
(`python3 scripts/validate-completion.py --ready <task>`; `--fix` only for
rule-derivable technical fields), an executor context pack is refused for a
task that fails it, and `start-cell.sh` shows whether the active item is
ready. When no procedure fits, agents say so instead of implying that a
specific package is missing.

## How it was verified

All checks ran against a fresh clone of the release candidate with an
isolated home directory, no global Git configuration, no GitHub CLI on the
`PATH` and no tokens — the situation of a new user without access to any
private repository. Python 3 with PyYAML was the only added requirement.

Result, candidate 5 (2026-09-22), the suite's introduction: **309 of 309
checks passed, 0 failed** against candidate 5's own tree (288 checks
originating from candidate 4's suite, re-run from scratch — not reused as
old evidence — plus 21 new gate-matrix-availability checks). Every later
candidate's own dated re-run result is recorded in this file's revision
history and in the private task's evidence, not restated here as if newly
run today.

| Area | What was checked |
|---|---|
| Documented quickstart | The command block in `docs/create-a-cell.md` is extracted between its markers and run as written (only the clone URL points at the candidate): the preview writes nothing, the confirmed install passes, the receipt is written, the Cell is committed before `start-cell.sh` runs, and the Cell validates. |
| Missing prerequisite | Without PyYAML the installer refuses with exit 5 and a repair hint, no traceback, no files. |
| Baseline / Baseline + Plus / Baseline + Plus + Capability Pack | For each combination: preview writes nothing and shows source commit, version, `kit_integrity: verified` and every package; confirmed install passes its closeout; receipt, preview and the installed file tree list exactly the same files; `validate-cell.sh` passes with zero failures; `start-cell.sh` runs and generates `START-HERE.html`; `profiles/` is never installed; package-specific files are present or absent as declared. |
| Plus and Capability Pack | Plus files and `validate-cell-plus.sh`; all three skills installed, every reference resolves, `validate-skill-playground.py` passes, no unresolved placeholders under `apps/`. |
| Governance at install | Governance profile, owner role and binding given at install time land in `.bcos/CELL-GOVERNANCE.yaml` and `TEAM-PROFILE.md`; the Cell validates. |
| Personalization and start | The personalizer asks for surfaces and, separately, the agents' role; it renders through the Cell's own renderer; the paste block records its render inputs and hashes; activation notes stay thin; the role/title answer is kept; activation is recorded as self-reported only; `start-cell.sh` reports the instruction lifecycle. |
| Procedure Index | For each package combination the index lists exactly the installed, active procedures (2 / 3 / 6); `render-instructions.py check` passes; a baseline block names no optional-package procedure; no procedure full text appears in a block. |
| ChatGPT budget | Nine renders (three package combinations × planner / executor / both) with long names and paths, umlauts and emoji stay at or below 7200, measured as the larger of Unicode code points and UTF-16 code units; the renderer's reported numbers equal an independent count; every block keeps all mandatory rules (including the authority, planning/handoff, format-check and "no matching procedure" rules for its role), the right role sections, existing paths only and the Cell's current index version. A catalog of 33 procedures stays within 7200 by routing the playbook group through its named sub-index; a block over the 8000 hard limit is refused without cutting anything. |
| Local host profiles | Capability declarations `none`, read-only and with tools render the matching capability ceiling; undeclared capabilities leave the agent to classify itself; an unknown capability is refused. |
| Context pack and profile | The task context pack carries the rendered block, the Cell entry files, the task and the full text of its selected procedures, marks itself `persisted: false`, reports tokens as an estimate unless a tokenizer command is given, refuses (without cutting) when it exceeds the token budget after reserves, and names a procedure of an uninstalled package as not included. A planning pack carries the current task template with its hash and Git blob; a procedure group the block routes via a sub-index travels as full index lines. The machine-readable profile lists entry, declared capabilities, index entries with hashes, task template and format check. |
| Task format check before execution | A complete task in the template's format is READY. A draft without frontmatter is not: rule-derivable fields (kind, ID from the file name, created from the ID, title from the heading) are offered as fixes, actor identity is reported open; `--fix` adds the frontmatter, writes missing identity as a visible `OPEN:` marker, leaves the body byte-identical and keeps the draft not ready, while the Cell validator accepts it as a structurally valid draft. A task with only technical gaps becomes READY with `--fix` alone and nothing else changes. Open content, a procedure that is not in the Cell's index, an ID that differs from the file name or is already used, a done item, a section copied unchanged from the template and a start prompt that does not name the work item each block execution; the template itself is not executable. A planner's explicit `OPEN:` on a field that has a rule default is kept and blocks; a partly filled ID such as `TASK-20260922-NNN` in the frontmatter, the start prompt path and the body is derived from the file name; a quoted mention of the marker is not an open item; an open task that keeps the template's unfilled Completion Record is not reported as status drift. |
| Handoff and roles | An executor context pack without a task is refused, and one for a task that fails the format check is refused with exit 5 and the open items named; `--allow-draft` marks it NOT READY; a ready task's pack records the passed check. A planner may still load a draft together with the template. `start-cell.sh` shows a not-ready active draft and routes to completing it, and a ready item as ready. The role label no longer says a planner "does not execute"; capability and authority text is identical for every role. A missing task template path fails the renderer check. |
| Snapshot identity | Identical inputs render byte-identical blocks; a different fact changes only the inputs hash of the snapshot line, whose index, core and profile hashes are the Cell's own; a personalized instruction file re-renders byte-identically from its recorded inputs and equals a fresh render with its recorded block hash. |
| Drift | A procedure changed without regenerating the index fails validation; after regeneration the rendered block is reported stale; `refresh` clears it; a hand-edited block fails; a removed procedure file fails. The renderer check and the completion validator also run on the system Python 3.9 without PyYAML. |
| Honest completion | The validator passes a correct done item and fails, each with a specific message: template placeholders, an unchecked Definition-of-Done item, a non-existent commit SHA, a recorded failed validation, status drift, `local-only` with an `origin` remote, and a remote head that does not contain the substantive commit. |
| Procedure evidence | A procedure recorded as applied without being loaded fails, as does a procedure that is not in the Cell; `none: <reason>` and a routed `closing_learning` pass; older records without the two fields only warn; a template placeholder left in the field fails. |
| Validator baseline | `--write-baseline` records exact failure identities; unchanged known failures pass against the baseline while the plain run still fails; replacing one known failure with a different one at the same total count is blocked as NEW and the repaired one is reported as RESOLVED. |
| Capability class and owner tripwire | Legacy `agent_capability_class` values warn, unknown values fail; an owner identity from `.bcos/owner-denylist.txt` fails outside a documentation fence. |
| Installer refusals | Non-empty target, `--confirm` without `--confirmed-by`, unknown or non-optional package, ambiguous instruction, unshipped variant, locally modified kit, receipt/tree mismatches. |
| Unvalidated install modes | This distribution refuses `hydrate_existing_repo` (by mode, by instruction and with `--confirm`) and `clone_existing_cell` before anything is previewed or written; the target stays unchanged; `--help` names the rule. |
| Repository hygiene | No key material; no personal or private project names outside the documented references below; `git diff --check` clean; the clone stays clean after all tests. |
| License integration | `LICENSE`, `LICENSES/MIT.txt` and `LICENSES/CC-BY-4.0.txt` exist at the candidate root; `LICENSES/CC-BY-4.0.txt` is byte-identical to the pre-rc.4 `LICENSE` body (no CC BY-licensed file's license text changed); `LICENSES/MIT.txt` is the unmodified upstream MIT text with the recorded copyright line; `distribution/teamcell-lite/bootstrap-kit/LICENSE` exists and is byte-identical to `LICENSES/MIT.txt`; for every combination the confirmed install's file tree contains the Cell-root `LICENSE` and the preview/receipt/kit-tree-hash reconcile it like any other baseline file (no `packages/PACKAGES.yaml` change was needed — it declares package membership by source-root prefix, not an exhaustive file list); `schemas/`, `scripts/` (the six tools) and `distribution/` contain no path also claimed by the CC BY scope list in `LICENSE`. |
| Gate matrix availability | `docs/teamcell-gate-matrix.md` and its three referenced schemas are installed at their documented relative paths in every package combination; `PROJECT.md`, `AGENTS.md`, `human-gates/TEMPLATE.human-gate.md` and `.bcos/CELL-GOVERNANCE.yaml.template`'s own references to them resolve inside the installed Cell (no distribution-root access needed); `validate-cell.sh` fails if any of the four files is later removed (regression test). |

## References to private upstreams (by design, no access needed)

The tested distribution path needs no access to any private repository. The
release does contain these references:

- `SOURCE-MANIFEST.json` names the private upstream template and tool
  repositories as labels with commit SHAs, for provenance only.
- The installer tools keep functional default repository names for a private
  operator path. They are used only when a checkout has no
  `SOURCE-MANIFEST.json`, which is never the case in this distribution.
- Tool comments carry internal provenance IDs (task and pattern numbers)
  without their content.
- `docs/public-private-boundary.md` names an internal product by name, as it
  did before this release.

## Scope and limits

- Install modes: only `new_from_template` is offered and validated.
  `hydrate_existing_repo` has a known defect in this release (its
  post-install closeout fails after files were written) and is refused;
  `clone_existing_cell` is not validated and is refused
  (`docs/teamcell-install-semantics.md`).
- Platform: verified on macOS only, with Python 3.12 and PyYAML 6 for the
  installer; the Cell-side renderer and validators additionally with the
  macOS system Python 3.9 without PyYAML. Linux and WSL on Windows are
  expected to behave the same but were not run for this release.
- Instruction blocks: the checks above prove what the rendered text contains
  and that it stays within budget. Whether a particular model follows it was
  not verified by this release. No local model host was run; the local
  outputs were checked as renders only.
- Activation of generated instruction blocks in external apps is recorded as
  self-reported only; no external app setting was tested.
- Context pack generation (`scripts/render-instructions.py context-pack`)
  does not yet automatically include a Cell's identity and governance files
  (`TEAM-PROFILE.md`, `.bcos/CELL-PROFILE.yaml`, `.bcos/CELL-GOVERNANCE.yaml`,
  `docs/teamcell-gate-matrix.md`) or a specific inbox entry, and does not warn
  when it omits them. A real external-model test that needed this context
  added the files manually, each labeled as a manual addition. This is a
  known generator gap, not a claimed capability; it does not block the
  installer, the renderer's own checks, or Cell validation.
- Two schema files (`schemas/teamcell-package-manifest.schema.md`,
  `schemas/teamcell-installation-receipt.schema.md`) are referenced only
  from `packages/PACKAGES.yaml` and the receipt generator, not cross-linked
  from the gate matrix or governance docs the way the three shipped
  gate-matrix schemas are. This is a known, pre-existing documentation gap;
  it does not affect installer or validator behavior.
- Team readiness (hosted repository, two committers, first real agent run)
  is a property of each Cell, reported by its own `validate-cell.sh`.
- Licensing: an approved decision recorded in dbeebr/bcos DECISION_LOG.md
  ("Teamcell Public Release — MIT / CC BY 4.0", 2026-09-22) is applied in
  this candidate — MIT for the operative Cell package (`distribution/`,
  `scripts/`, `schemas/`), CC BY 4.0 retained unchanged for existing
  explanatory documentation and teaching examples; see `LICENSE` for the
  exact scope table. This is a decision on files whose rights holder
  controls the rights to publish them (this candidate's own authored/aligned
  content, the bcos-teamcell-lite-template source, and the six installer
  tools); it does not relicense any third-party material, and none is known
  to be present in this release.
