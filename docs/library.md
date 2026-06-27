# Library

## What Library Means in BCOS

A Library is the accumulated set of reusable patterns, proven templates, validated decision records, and trusted artifacts that a Cell has produced and would use again.

It is not a folder full of notes. It is the idea that structured work, done well, produces something durable — patterns that future work can start from instead of starting from scratch.

## Why Library Matters

Every task completed under BCOS produces artifacts: decisions that clarified assumptions, templates that proved useful, handoff records that captured hard-won context, proofs that established what "done" looks like.

Without a Library concept, those artifacts accumulate but never compound. A new team member, a new agent, or a new Cell reads raw history — or worse, starts from blank state.

With a Library, the best of what a Cell has learned is curated, validated, and available. The longer a Cell operates well, the more valuable its Library becomes.

This is the compounding return on structured work.

## What Belongs in a Library

A Library contains artifacts that have been **validated through use** and are **worth reusing**:

- **Proven templates** — task structures, decision formats, or handoff patterns that worked well enough to become defaults.
- **Validated decision patterns** — recurring decision types where the rationale and structure have been tested.
- **Playbooks** — sequences of steps that a Cell has followed successfully and would follow again.
- **Distilled handoff records** — handoff patterns that reliably transfer context without losing critical information.

The common thread: everything in a Library has been used, tested, and found worth keeping.

## What Does Not Belong in a Library

- **Raw history** — unfiltered session logs, draft conversations, or work-in-progress notes.
- **Unvalidated drafts** — templates or patterns that have been proposed but never tested.
- **Private operating records** — internal records that contain sensitive context not suitable for reuse outside the Cell.
- **Everything the Cell has ever produced** — a Library is curated, not comprehensive.

A Library that contains everything is just an archive. Curation is what makes it useful.

## How Library Relates to Cells, Routers, and Modules

A **Cell** is the operating boundary. Work happens inside a Cell.

**Routers** (Context Index, agent configuration) tell humans and agents what to read and where to start.

A **Library** is what the Cell distills from its operating history — the reusable capital that outlasts any single task or session.

**Modules** (future) are shareable Library units: domain-specific templates, patterns, or extensions that can move between Cells or be shared with the community.

The sequence:

```text
Work happens inside a Cell
  → Routers direct attention
  → Tasks, Decisions, Handoffs, Proofs record what happened
  → The best patterns are distilled into the Library
  → The Library makes future work faster and more reliable
```

## Public and Private Libraries

A Cell's Library may contain patterns that are only useful internally — decision templates tied to proprietary processes, handoff formats that reference internal systems, or playbooks built around private tooling.

A **private Library** holds these internal patterns. They are valuable to the Cell but not suitable for public sharing.

A **public Library** holds patterns that are safe and useful to share: generic templates, common decision structures, reusable playbooks that do not depend on private context.

The public/private boundary applies to Libraries the same way it applies to all BCOS artifacts: share what is useful, keep what is sensitive, and make the boundary intentional.

## Community Contribution

The Library concept creates a natural contribution path for the BCOS community:

- **Share proven templates** — if your Cell has developed a task template or decision format that works well, contribute it.
- **Share neutral examples** — real patterns, stripped of private context, that show how BCOS works in practice.
- **Share playbooks** — step-by-step patterns that other Cells can adopt or adapt.

The standard for community Library contributions is the same as for any Library entry: it should be validated through use, not just proposed.

## Why Library Is a Surface

Library started as a concept — the idea that structured work produces reusable capital.
It became a dedicated surface when operating evidence showed that curated knowledge had
no clear home. Proven patterns were scattered across archived tasks and old decisions.
Teams kept relearning what they already knew.

Adding Library as a top-level surface gives curated knowledge a visible, findable
location. It is separate from History because mixing curated patterns with raw records
makes both harder to use: History becomes harder to scan, and Library becomes harder
to trust as a curated set.

See `docs/why-these-surfaces.md` for the full reasoning behind Library and every other
BCOS surface.

## Status

Library is a core primitive in BCOS v0.1. The concept is defined here and referenced in
the core model. In Teamcell Lite, `library/` is a first-class top-level surface — the
place where curated reusable knowledge, proven templates, and validated patterns live.
