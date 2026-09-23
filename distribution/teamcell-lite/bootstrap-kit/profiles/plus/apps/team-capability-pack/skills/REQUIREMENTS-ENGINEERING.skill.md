---
bcos_type: skill
kind: capability_skill
surface: apps
domain: operations
package: team-capability-pack
id: SKILL-REQUIREMENTS-ENGINEERING
title: "Requirements Engineering"
version: 1.0.0
status: active
procedure_kind: "skill"
use_when: "An accepted outcome or decision must become specific, testable, traceable requirements"
not_when: "The outcome itself is still undecided (Business Analyst first)"
phase: "plan, execute"
created: 2026-07-12
created_by: claude-sonnet-5-bcos-orchestrator
created_by_type: agent
created_by_id: agent:claude-sonnet-5-bcos-orchestrator
created_by_display: "Claude Sonnet 5 (BCOS orchestrator session)"
created_by_github: null
on_behalf_of_human_id: "human:{{CELL_OWNER_ID}}"
agent_id: agent:claude-sonnet-5-bcos-orchestrator
agent_model: claude-sonnet-5
agent_capability_class: local-worker
canonicality: 50
confidence: 0.8
---

# Requirements Engineering

## Purpose

Turn an already-accepted outcome or decision into traceable, testable
requirements: functional and non-functional, with assumptions,
constraints, dependencies, open conflicts named rather than hidden, stable
identifiers, and acceptance criteria a later build/verification step can
actually check.

## Trigger Conditions

Use this skill when a request:

- references a decision, recommendation, or outcome that is already
  accepted (by a decision owner, a Human Gate resolution, or an accepted
  Business Analyst recommendation) and needs to become specific, buildable
  work;
- asks for "requirements," "acceptance criteria," or "a spec" for
  something already agreed to happen;
- needs traceability from a piece of work back to the decision that
  authorized it.

Do **not** trigger when the outcome itself is still undecided (route to
Business Analyst first) or when the request is about designing a team
interaction rather than a deliverable (route to Team Event Planner).

## Required Inputs

- the accepted source decision or outcome, with a reference to where it
  was accepted (a `WorkItem`, an accepted Business Analyst analysis, a
  resolved `HumanGate`, or an explicit human instruction recorded in a
  durable artifact);
- any existing constraints already on record (technical, legal, brand,
  timeline);
- the intended consumer of the requirements (who builds, who verifies).

If no accepted source can be named, this skill must stop and say so — it
does not manufacture an accepted source to proceed.

## Output Contract

A single Markdown requirements artifact with these sections, in order:

1. **Source** — an explicit, resolvable reference to the accepted
   decision/outcome this specifies. No source reference, no requirements
   document.
2. **Functional requirements** — each with a stable identifier
   (`REQ-<slug>-NNN`), a testable statement, and a trace back to the
   source.
3. **Non-functional requirements** — same identifier scheme, covering
   whichever of performance, privacy, accessibility, or reliability are
   actually relevant; omit categories that don't apply rather than padding.
4. **Assumptions and constraints** — named explicitly, not folded silently
   into the requirements themselves.
5. **Open conflicts or ambiguities** — anything the source decision left
   unresolved, named plainly rather than quietly resolved by this skill's
   own judgment.
6. **Acceptance criteria** — one or more testable criteria per
   requirement, phrased so a later verification step can check pass/fail
   without re-interpreting intent.
7. **Change-impact note** — if this specification amends a prior one,
   what changed and why.
8. **Routing** — where this artifact lands (see Canonical Routing).

## Stepwise Workflow

1. Resolve and cite the accepted source. If it cannot be found or is
   itself still pending acceptance, stop and report that rather than
   proceeding on an assumed acceptance.
2. Elicit functional requirements strictly from the accepted source's
   actual content plus any explicitly supplied constraints — do not
   introduce scope the source never accepted.
3. Identify non-functional requirements that genuinely apply; do not
   include a category (e.g. "performance") with no real content behind it.
4. Assign each requirement a stable, unique identifier.
5. Write acceptance criteria per requirement before considering the
   document done — a requirement without a testable criterion is
   incomplete.
6. Surface every conflict, ambiguity, or gap explicitly rather than
   silently picking a resolution.
7. Check every requirement traces to the cited source; anything that does
   not trace is either dropped or explicitly flagged as new scope needing
   its own acceptance (see Quality Gates and Non-Authority).
8. Route the artifact and stop.

## Quality Gates

- every requirement has a stable identifier and traces to the cited
  source;
- every requirement has at least one testable acceptance criterion;
- the "Open conflicts" section is present even when empty (state "none
  identified," don't omit the section);
- no requirement exists that isn't traceable to the accepted source or
  explicitly flagged as new, not-yet-accepted scope;
- no unresolved template placeholder tokens (an un-filled marker left in the output).

## Non-Authority Boundaries

This skill must not:

- turn an unapproved idea, a still-open Business Analyst option, or a
  merely-discussed possibility into a requirement — only an accepted
  source may become a requirement;
- hide ambiguity or conflict to make the document look cleaner;
- produce a heavyweight specification when the accepted source is small
  enough for a lightweight `WorkItem` description to suffice — match
  formality to the actual size and risk of the change;
- replace product, architecture, legal, or design authority — a
  requirement this skill cannot resolve without one of those owners'
  judgment becomes an open conflict, not a silent assumption.

## Privacy Boundaries

- do not include personal data beyond what the accepted source itself
  already contains;
- do not restate confidential brand/domain-brain content inline — cite it.

## Human Gate Conditions

Route to a Human Gate instead of silently resolving when:

- the accepted source is ambiguous about scope boundaries in a way that
  materially changes cost, risk, or timeline depending on interpretation;
- a non-functional requirement (e.g. a privacy or compliance constraint)
  is contested or unclear;
- change-impact analysis shows this specification would alter a
  previously accepted, already-in-progress requirement set.

## Canonical Routing

| Situation | Routes to |
|---|---|
| Requirements accepted as specified | new or updated `work/` `WorkItem`, tracing to the source decision |
| Open conflict needing a decision | new `human-gates/` `HumanGate`, naming the exact conflict |
| Repeatable elicitation pattern observed | `history/learning-candidates/` `LearningCandidate` |
| A `WorkItem` this specification completes | `CompletionRecord` on that `WorkItem`, authored when the work is actually done — not by this skill at specification time |

## Bounded Context-Loading Route

Load only: this file, the cited accepted source artifact, and any
explicitly supplied constraint documents. Do not load Business Analyst or
Team Event Planner while running this skill.

## Positive Example

Source: an accepted Business Analyst recommendation to "improve expiry
notice timing" (cited by its `work/` path). Correct handling: derive
functional requirements directly from that accepted scope only (e.g.
"REQ-EXPIRY-NOTICE-001: send a notice N days before point expiry"),
non-functional requirements that genuinely apply (e.g. delivery-channel
reliability if that was part of the accepted scope), explicit acceptance
criteria per requirement, and an explicit note if the source left the
exact value of N undecided — surfaced as an open conflict, not silently
picked by this skill.

## Negative Example

Same source. Incorrect handling this skill must avoid: adding a
requirement for "extend the expiry window" because it was *discussed* as
an option in the Business Analyst analysis but was **not** the accepted
outcome; picking a specific value for N without evidence and presenting it
as decided rather than as an open conflict; or omitting acceptance
criteria because "it's obvious what done looks like."
