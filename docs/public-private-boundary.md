# Public-Private Boundary in BCOS

## What This Public Staging Repository Includes

This extraction package is the curated public surface of the BCOS v0.1
concept plus the Teamcell Lite v0.4 distribution built on it (exact version:
[`distribution/teamcell-lite/SOURCE-MANIFEST.json`](../distribution/teamcell-lite/SOURCE-MANIFEST.json)).
It includes:

- **`README.md`** — Public overview and quickstart
- **`LICENSE`** — index: MIT for the operative Teamcell Lite Cell package
  (`distribution/`, `scripts/`, `schemas/`), CC BY 4.0 for docs, templates,
  and examples (unchanged); full texts in `LICENSES/`
- **`CONTRIBUTING.md`** — Contribution guidelines
- **`CODE_OF_CONDUCT.md`** — Community conduct policy
- **`SECURITY.md`** — Security disclosure policy
- **`SUPPORT.md`** — Support expectations for an experimental release
- **`docs/manifesto.md`** — Why context must survive the conversation
- **`docs/core-model.md`** — Public core model primitives
- **`docs/public-private-boundary.md`** — This file; explains the boundary
- **`templates/`** — Generic reusable task, decision, handoff, proof, and human-gate templates
- **`examples/neutral-cell/`** — A neutral, privacy-safe example cell
- **`examples/setbrain-cell/`** — A complete fictional operating Cell with a finished work loop and an active app package
- **`distribution/teamcell-lite/`** — The installable Teamcell Lite v0.4 kit (`bootstrap-kit/`) and its `SOURCE-MANIFEST.json` provenance/version/hash record
- **`scripts/`** — The installer: preview, preflight, bootstrap, receipt generation, personalization
- **`schemas/`** — The routing-frontmatter, completion-record and Teamcell package/receipt/governance/ownership contracts
- **`reports/verification/PUBLIC-CELL-RELEASE.md`** — How this release was checked before publication, and its known limits

## What This Repository Explicitly Excludes

The following are excluded from this public extraction package:

### Private Operating Repository

The private operating repository that generated this BCOS standard and
Teamcell Lite distribution is not published. That repository contains:

- private task history and operating records;
- raw session handoffs and in-progress notes;
- person-specific and organization-specific context;
- internal governance artifacts.

These are deliberately kept private. This public staging repository is a
curated extraction from that repository, not a copy or visibility flip of it.
Provenance labels (private upstream repository names and commit SHAs in
`SOURCE-MANIFEST.json`, or internal task/pattern IDs in tool comments) are
disclosed references for auditability, not a private access requirement —
nothing in this repository needs access to the private repository to clone,
install or validate.

### BCOS Product Internals

The following are excluded:

- **Lumen** — An internal AI-assisted operating product. Not included.
- **Command Center** — An internal operating interface. Not included.
- **MCP integrations** — Runtime integrations. Not included.
- **Private operating history and content** — the private repository's own
  task/decision/handoff/review history, and any real Cell's own operating
  data, participant identities or business content. Not included.

Teamcell Lite itself is no longer excluded: since the rollout recorded below,
this repository ships the installable Teamcell Lite v0.4 kit, its installer
tools (executable Python/shell scripts, not documents only), its schemas and
its release verification report as real, checked-out content — see "What
This Public Staging Repository Includes" above.

### Private Reference Categories

The following categories of content are excluded:

- References to specific private individuals, clients, or organizations
- Private project history, notes, and decisions belonging to private operating cells
- Credentials, tokens, secrets, API keys, or private endpoints
- Raw unprocessed operating records
- Internal tooling documentation not intended for public use

## Why This Boundary Exists

A real BCOS operating system accumulates private history. Publishing that history
raw would violate the trust of people whose names, projects, and decisions appear
in it.

The public-private boundary is not a limitation of BCOS. It is a feature:
responsible publication requires deliberate curation and human-approved release
gates.

## Publication Status

This extraction package is prepared inside the private operating repository.
A staging publication has already occurred: this content is published as
`dbeebr/bcos-public-staging`, a public GitHub repository. See
[`../reports/verification/PUBLIC-CELL-RELEASE.md`](../reports/verification/PUBLIC-CELL-RELEASE.md)
for the exact published commit, version label and what was checked
beforehand.

That staging publication was itself an explicitly human-approved decision
(recorded in the private repository's task history) covering the redaction
state, license and public naming actually shipped here — it is not an
informally leaked or accidental copy.

Any further change to this boundary — a broader visibility change, promoting
this staging content to a differently named or "stable" public repository,
or publishing additional private content beyond what is listed above — still
requires its own separate, explicit human approval. This page will be
updated when such a decision is made; until then, treat only what is listed
under "What This Public Staging Repository Includes" as published.
