---
bcos_type: doc
id: TEAMCELL-PLUS-PROFILE-README
title: "Teamcell Plus — additive profile overlay"
status: active
created: 2026-07-12
created_by: claude-code-main
agent_model: claude-code-main
related:
  - docs/EXPANSION-PROFILE.md
---

# Teamcell Plus — additive profile overlay

Teamcell Plus is **additive** on top of Teamcell Lite (`../../`), derived
from running earlier team Cells. Lite defaults are never modified
by installing Plus — every file here is new, and the installer only adds
files, never rewrites a Lite baseline file, except the two additive
appends noted below.

## What Plus adds over Lite

1. **Engagement loop**: `scripts/post-cell-update.sh` (publish a Cell Update
   as a GitHub Issue, label `cell-update`) and `scripts/morning-pulse.sh`
   (bounded observer, manual-trigger, idempotent, no-change-silent).
2. **Onboarding**: `ONBOARDING.md.template` — one-page, ten-question,
   half-AI-affine-team-first onboarding (replaces nothing; Lite's own
   onboarding deck at `../../playbooks/onboarding/` stays available).
3. **Contract reference**: `docs/CONTRACTS-V1.md` — the eight v1 Plus
   contracts (`CellIdentity`, `ActorIdentity`, `WorkItem`, `HumanGate`,
   `CompletionRecord`, `CellUpdate`, `NotificationPolicy`,
   `LearningCandidate`).
4. **Hardened Human Gate rule**: a Plus-only validator check (see
   `scripts/validate-cell-plus.sh`) — an implementation commit referencing a
   gate ID may not land before that gate's `gate_status` is `accepted`. This
   answers a failure observed repeatedly in an operating Cell
   (implementation landed before its gate was accepted).
5. **`history/learning-candidates/`** — a non-canonical, human-gated
   learning buffer.

## What Plus deliberately does not add

No dashboard runtime, no PWA, no native app, no Shell, no Discussion-based interaction,
no recurring-schedule automation, no `CellSnapshot`/`BriefContract`/
`KnowledgeSource`/`ArtifactEnvelope`/separate `LearningExport` contracts.
The underlying evidence inventory stays with the BCOS maintainers and is not
part of this distribution.

## Install

The Teamcell installer runs `scripts/install-plus-profile.sh <target-cell-dir>`
when this package is selected (`--print-targets` lists the files it will
create, for the preview). It copies this overlay into
an already-Lite-installed Cell directory, additive-only, and appends the
`profiles/plus` marker line to the target's `CONTEXT_INDEX.md` (the one
permitted mutation of a Lite file — a routing pointer, not a behavior
change).

## License

Installing this profile requires an already-Lite-installed Cell, which
already carries the baseline package's `LICENSE` (MIT) at its root. This
overlay's files are covered by that same `LICENSE`; no separate license file
is added by this package.
