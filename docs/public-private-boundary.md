# Public-Private Boundary in BCOS

## What BCOS Public v0.1 Includes

This extraction package (`public-extraction/`) is the curated public surface of
BCOS v0.1. It includes:

- **`README.md`** — Public overview and quickstart
- **`LICENSE`** — CC BY 4.0 for all docs, templates, and examples
- **`CONTRIBUTING.md`** — Contribution guidelines
- **`CODE_OF_CONDUCT.md`** — Community conduct policy
- **`SECURITY.md`** — Security disclosure policy
- **`SUPPORT.md`** — Support expectations for v0.1 experimental
- **`docs/manifesto.md`** — Why context must survive the conversation
- **`docs/core-model.md`** — Public core model primitives
- **`docs/public-private-boundary.md`** — This file; explains the boundary
- **`templates/`** — Generic reusable task, decision, handoff, proof, and human-gate templates
- **`examples/neutral-cell/`** — A neutral, privacy-safe example cell

## What BCOS Public v0.1 Explicitly Excludes

The following are excluded from this public extraction package:

### Private Operating Repository

The private operating repository that generated this BCOS standard is not
published. That repository contains:

- private task history and operating records;
- raw session handoffs and in-progress notes;
- person-specific and organization-specific context;
- internal governance artifacts.

These are deliberately kept private. BCOS public v0.1 is a curated extraction
from that repository, not a copy or visibility flip of it.

### BCOS Product Internals

The following are excluded from v0.1:

- **Teamcell Lite** — A specific BCOS cell template product that may be released
  separately in the future after its own sanitization and launch review.
- **Lumen** — An internal AI-assisted operating product. Not included.
- **Command Center** — An internal operating interface. Not included.
- **MCP integrations** — Runtime integrations. Not included.
- **Runtime code** — BCOS v0.1 is a docs-first release. No runtime is included.

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

This extraction package is prepared inside the private operating repository and
has not been published. Publication requires a separate launch Human Gate that
explicitly approves:

- the repository creation;
- the visibility change or new public repository;
- the final redaction state;
- the license;
- the public naming.

No publication has occurred as of this extraction date.
