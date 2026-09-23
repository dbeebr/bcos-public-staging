---
bcos_type: skill
kind: capability_skill
surface: apps
domain: operations
package: team-capability-pack
id: SKILL-BUSINESS-ANALYST
title: "Business Analyst"
version: 1.0.0
status: active
procedure_kind: "skill"
use_when: "A business goal, process, priority or stakeholder situation is unclear and needs a structured read before anyone decides"
not_when: "The outcome is already accepted (Requirements Engineering) or a team interaction needs designing (Team Event Planner)"
phase: "plan"
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

# Business Analyst

## Purpose

Turn an insufficiently framed business question, goal, process, or
stakeholder situation into a decision-ready analysis: a measurable
outcome, the people who own the decision, the current state, what is
evidence versus what is hypothesis, the real options with trade-offs, and
a routed recommendation — or an explicit Human Gate when the fork is not
this skill's to resolve.

## Trigger Conditions

Use this skill when a request:

- states a business goal, pain point, or ambiguous priority without a
  measurable outcome attached ("we should improve X", "why is Y not
  working", "should we do A or B");
- asks for a read on a process, a stakeholder situation, or a trade-off
  before any commitment to build or decide anything;
- surfaces conflicting stakeholder positions that need mapping before a
  decision can be made;
- explicitly asks for "an analysis," "options," or "a recommendation" on a
  business (not purely technical) question.

Do **not** trigger when the outcome is already accepted and the request is
about turning it into buildable specification (route to Requirements
Engineering instead) or about designing a team interaction (route to Team
Event Planner instead).

## Required Inputs

- the business question or goal, in the requester's own words;
- who is asking and, if known, who owns the decision;
- any existing evidence already available in the Cell (`work/`,
  `history/`, `decisions/` if present, prior `CellUpdate`s) — this skill
  reads what exists, it does not go and interview people;
- if brand/journey-sensitive: a pointer to the installed domain brain
  (e.g. `apps/brand-brain/`), loaded only via its own bounded index.

If the decision owner is unknown, name that as an open question in the
output rather than guessing.

## Output Contract

A single Markdown analysis artifact with these sections, in order:

1. **Problem framing** — the question restated, and the measurable outcome
   that would tell the owner the question is answered.
2. **Stakeholders and decision owner** — who is affected, who decides.
3. **Current state** — what is actually true today, cited to its source.
4. **Evidence vs. hypothesis** — two explicit, visually separated lists.
   Every claim in "Evidence" carries a source reference (a file path, a
   commit, a prior `CellUpdate`, or a named person's statement with date).
   Every claim that cannot be sourced goes in "Hypothesis," never mixed in
   with evidence.
5. **Options** — at least two real options (never a single
   foregone-conclusion option dressed as analysis), each with trade-offs,
   risks, and dependencies.
6. **Recommendation or Human Gate** — either a recommendation with its
   confidence and the evidence it rests on, or an explicit statement that
   this is a strategic fork requiring a Human Gate, naming exactly what
   the owner must decide.
7. **Routing** — where this artifact lands (see Canonical Routing) and
   what happens next if accepted.

## Stepwise Workflow

1. Restate the problem and propose a measurable outcome; if the requester
   disagrees, use their correction, don't argue for the skill's framing.
2. Identify the decision owner and other stakeholders.
3. Gather current-state facts strictly from committed Cell artifacts (and,
   if flagged brand-sensitive, the domain brain's bounded pointer) — never
   invent or infer facts not actually present.
4. Separate every claim into Evidence or Hypothesis as it is gathered, not
   as an afterthought.
5. Generate at least two genuinely distinct options with real trade-offs.
6. Decide: is this a routine, evidence-decidable call, or a genuine
   strategic fork? If routine, recommend with stated confidence. If
   strategic, do not recommend — name the Human Gate instead.
7. Route the artifact (see below) and stop. Do not silently continue into
   implementation planning.

## Quality Gates

- every "Evidence" line has a resolvable source reference;
- the "Hypothesis" list is non-empty whenever any claim could not be
  sourced (an analysis with zero hypotheses on a genuinely ambiguous
  question is a warning sign, not a strength);
- at least two options are present with distinct trade-offs;
- the output ends in exactly one of: a stated recommendation, or a named
  Human Gate — never both, never neither;
- no unresolved template placeholder tokens (an un-filled marker left in the output).

## Non-Authority Boundaries

This skill must not:

- invent customer, market, or business evidence not actually present in
  the Cell's committed record or a cited external source;
- decide strategy, priority, or scope on the decision owner's behalf —
  recommending is not deciding;
- silently change an existing accepted scope or priority;
- convert its own analysis into implementation work automatically — a
  recommendation becomes a `WorkItem` for building only after the owner
  accepts it (see Requirements Engineering for that next step).

## Privacy Boundaries

- do not include personal data beyond what is already committed in the
  Cell's own artifacts;
- do not name individuals as sources of unflattering "current state"
  claims without their claim being independently evidenced — attribute
  claims to roles or committed artifacts where possible;
- do not export or reference material outside this Cell's and its
  explicitly linked domain brain's authorized scope.

## Human Gate Conditions

Route to a Human Gate instead of a recommendation when:

- the options carry materially different risk, cost, or reversibility and
  no accepted policy resolves which matters more;
- stakeholders hold genuinely conflicting, unresolved positions that this
  analysis cannot adjudicate;
- the recommendation would change an existing accepted decision, priority,
  or committed roadmap item.

A Human Gate from this skill must name: the exact question, the options,
and the evidence for each — never just "please decide."

## Canonical Routing

| Situation | Routes to |
|---|---|
| Recommendation accepted or routine | new `work/` `WorkItem`, citing this analysis |
| Genuine strategic fork | new `human-gates/` `HumanGate`, per the conditions above |
| Notable, repeatable pattern observed while analyzing (not the analysis itself) | `history/learning-candidates/` `LearningCandidate` |
| Cell-visible milestone (e.g. a major recommendation accepted) | `CellUpdate`, authored by the Cell operator, not auto-generated by this skill |

This skill never creates a `CompletionRecord` directly — that closes a
`WorkItem`, which this skill's analysis may lead to but does not itself
constitute.

## Bounded Context-Loading Route

Load only: this file, the specific committed Cell artifacts the analysis
actually cites, and — only if the request is brand/journey-sensitive — the
domain brain's own bounded index pointer (not its full content). Do not
load Requirements Engineering or Team Event Planner while running this
skill; route to them as a separate, later step if their trigger applies.

## Positive Example

Request: "Loyalty point expiry complaints are up — should we extend the
expiry window?"

Correct handling: frame the measurable outcome ("reduce expiry-related
complaint volume without a material breakage-cost increase"), identify the
decision owner (Loyalty Product Owner), pull current-state facts from
committed Cell evidence (e.g. a prior `CellUpdate` or `work/` item
recording complaint volume, if one exists — otherwise state plainly that
no committed volume data exists yet, as a Hypothesis-list item, not an
invented number), separate evidence from hypothesis explicitly, present at
least two options (e.g. "extend expiry window" vs. "improve expiry
notice timing" vs. "no change, monitor") with trade-offs, and either
recommend the evidence-supported option or open a Human Gate if the
cost/reversibility trade-off is unresolved. Routes to a `work/` `WorkItem`
or a `human-gates/` entry, not a prose-only chat reply.

## Negative Example

Request: "Loyalty point expiry complaints are up — should we extend the
expiry window?"

Incorrect handling that this skill must avoid: immediately recommending
"yes, extend the window" without checking whether any committed complaint
data exists; inventing a plausible-sounding complaint number instead of
marking it as unknown; presenting only one option framed as if it were the
only sensible choice; silently creating a `WorkItem` to implement the
extension without first routing the recommendation for the decision
owner's acceptance; or ending the interaction with prose recommendations
only and no routed artifact.
