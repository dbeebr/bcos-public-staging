# BCOS Core Model

This document defines the minimum public vocabulary for **BCOS — Base Context Operating System**.

## Work

**Definition:** A bounded stream of effort that changes understanding, decisions, artifacts, systems, or outcomes.

**Why it exists:** Work needs continuity across people, agents, tools, and time.

**Minimal fields:**

- `id`
- `title`
- `status`
- `owner`
- `scope`
- `source`
- `evidence`

**Neutral example:** "Prepare a public onboarding kit for a documentation standard."

**What it is not:** A conversation, a mood, or an unbounded aspiration.

---

## Task

**Definition:** An executable contract for a specific unit of work.

**Why it exists:** Humans and agents need shared boundaries before acting.

**Minimal fields:**

- `id`
- `title`
- `status`
- `goal`
- `allowed_actions`
- `forbidden_actions`
- `inputs`
- `deliverables`
- `validation`

**Neutral example:** "Create three template files and validate Markdown formatting."

**What it is not:** A loose reminder or a chat instruction with no evidence standard.

---

## Agent

**Definition:** A human-directed or automated worker that can read context, perform actions, and produce evidence.

**Why it exists:** Different agents have different capabilities, risks, and authority.

**Minimal fields:**

- `agent_id`
- `capability_class`
- `allowed_actions`
- `forbidden_actions`
- `context_package`
- `evidence_required`

**Neutral example:** "A local coding agent that can edit files and commit changes after validation."

**What it is not:** An authority source. Agents can propose and execute inside boundaries; they do not become truth by speaking.

---

## Human Gate

**Definition:** A required human decision before costly, irreversible, sensitive, public, legal, architectural, or scope-changing action.

**Why it exists:** Not every step should be automated or delegated.

**Minimal fields:**

- `id`
- `decision_owner`
- `decision_required`
- `options`
- `risks`
- `approval_evidence`
- `status`

**Neutral example:** "Approve the license before publishing a public repository."

**What it is not:** A meeting for every small edit or reversible wording change.

---

## Evidence

**Definition:** Durable support for a claim about work, state, or completion.

**Why it exists:** Distributed work needs proof that can be inspected later.

**Minimal fields:**

- `claim`
- `source`
- `artifact`
- `timestamp`
- `verifier`
- `confidence`

**Neutral example:** "A validation command passed and its output was recorded."

**What it is not:** Confidence, memory, or a screenshot with no reproducible source.

---

## Proof

**Definition:** Evidence strong enough to close a claim under the task's completion standard.

**Why it exists:** Some evidence is suggestive; proof is sufficient for the specific contract.

**Minimal fields:**

- `proof_id`
- `claim`
- `evidence_items`
- `verification_method`
- `result`
- `limits`

**Neutral example:** "The pushed commit is visible on the remote default branch."

**What it is not:** A universal guarantee. Proof is always scoped to a claim.

---

## Decision

**Definition:** A recorded choice that changes what future work should assume.

**Why it exists:** Teams and agents need durable alignment without re-reading every discussion.

**Minimal fields:**

- `id`
- `title`
- `status`
- `decision`
- `rationale`
- `scope`
- `decided_by`
- `date`

**Neutral example:** "Use a docs-first public repository for v0.1."

**What it is not:** A suggestion, preference, or unresolved proposal.

---

## Handoff

**Definition:** A transfer record that lets another human or agent continue work from a known state.

**Why it exists:** Work often crosses sessions, people, and tools.

**Minimal fields:**

- `id`
- `from`
- `to`
- `current_state`
- `completed`
- `open_items`
- `risks`
- `next_actions`
- `evidence`

**Neutral example:** "The benchmark is complete; the proposal still needs license review."

**What it is not:** A status update without enough context to act.

---

## Cell

**Definition:** A bounded operating environment where BCOS files, people, agents, tools, and rules coordinate a stream of work.

**Why it exists:** Context needs a boundary. A cell defines what belongs together.

**Minimal fields:**

- `cell_id`
- `purpose`
- `participants`
- `repositories`
- `rules`
- `entry_points`
- `private_boundaries`

**Neutral example:** "A small project cell for maintaining an open documentation standard."

**What it is not:** A company, workspace, or repository by default. It may map to those, but it is an operating boundary.

---

## Context Index

**Definition:** A routing layer that tells humans and agents what to read for a given purpose.

**Why it exists:** Good context loading is selective, not exhaustive.

**Minimal fields:**

- `id`
- `purpose`
- `entry_points`
- `load_when`
- `do_not_load_by_default`
- `related_files`

**Neutral example:** "For contribution tasks, read README, CONTRIBUTING, SECURITY, and the active task."

**What it is not:** A full table of contents or an instruction to read everything.

---

## Library

**Definition:** The accumulated set of reusable patterns, proven templates, validated decision records, and trusted artifacts that a Cell has produced and would use again.

**Why it exists:** Structured work produces reusable capital. A Cell that has operated well holds a Library that lets new members, agents, or future Cells start from proven patterns rather than blank state.

**Minimal fields:**

- `scope`
- `entry_points`
- `artifact_types`
- `public_safe`
- `private_only`

**Neutral example:** "After twelve months of operating, a Cell's Library contains five validated decision templates, two proven task patterns, and three playbooks distilled from completed work."

**What it is not:** A folder full of notes. A Library is curated and proven, not a dump of every artifact the Cell has ever produced. In BCOS v0.1, Library is a core concept and primitive, not shipped tooling or a required top-level folder.

---

## Source of Truth

**Definition:** The durable artifact or system that has authority for a specific claim.

**Why it exists:** Distributed systems need conflict resolution.

**Minimal fields:**

- `claim_type`
- `authoritative_source`
- `fallback_source`
- `conflict_rule`
- `verification_method`

**Neutral example:** "The remote Git default branch is the source of truth for committed repository content."

**What it is not:** The most recent chat message or the loudest assertion.

---

## Public Surface

**Definition:** The curated subset of a BCOS system that is safe and useful to publish.

**Why it exists:** Real operating systems contain private context; public release requires selection.

**Minimal fields:**

- `scope`
- `included_content`
- `excluded_content`
- `redaction_rules`
- `license`
- `publication_gate`

**Neutral example:** "Publish templates and a neutral example; keep private task history out."

**What it is not:** A visibility flip of a private operating repository.

---

## Private Operating Layer

**Definition:** The internal context, history, records, and tooling that run a real BCOS cell but are not automatically public.

**Why it exists:** Operational truth can be useful and sensitive at the same time.

**Minimal fields:**

- `private_scope`
- `sensitive_categories`
- `access_rules`
- `redaction_policy`
- `promotion_gate`

**Neutral example:** "Internal project notes and raw session handoffs stay private unless sanitized."

**What it is not:** A failure of openness. It is the boundary that makes responsible publication possible.
