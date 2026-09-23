---
bcos_type: skill
kind: capability_skill
surface: apps
domain: operations
package: team-capability-pack
id: SKILL-TEAM-EVENT-PLANNER
title: "Team Event Planner"
version: 1.0.0
status: active
procedure_kind: "skill"
use_when: "A team meeting, workshop, review or retrospective needs an objective, agenda and facilitation design"
not_when: "Individual analysis or a specification task; never schedules or invites anyone"
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

# Team Event Planner

## Purpose

Turn a concrete team outcome (a decision to make together, a plan to
align on, a retrospective to hold) into a facilitation-ready event design:
objective, roles, pre-read, agenda, facilitation method, accessibility,
decision-capture plan, and post-event routing — **as a design artifact
only**. This skill never schedules, invites, or sends anything.

## Trigger Conditions

Use this skill when a request:

- asks to plan, design, or structure a team meeting, workshop, review, or
  retrospective;
- names a team-level outcome that needs a group interaction to reach
  (e.g. "we need to align on the roadmap," "let's retro the last
  release");
- asks for an agenda, facilitation approach, or meeting design, whether or
  not scheduling is mentioned.

Do **not** trigger for a purely individual analysis question (route to
Business Analyst) or a specification task (route to Requirements
Engineering). If a request also asks to actually schedule or invite
people, this skill still produces the design — scheduling/inviting is out
of scope entirely (see Non-Authority Boundaries), not merely gated.

## Required Inputs

- the team outcome or objective this event should achieve;
- who needs to be involved and in what decision role (decider,
  contributor, informed);
- any existing constraints (time available, remote/hybrid mix, prior
  related events);
- if brand/journey-sensitive material will be discussed: a pointer to the
  installed domain brain's bounded index.

If the objective is not yet clear enough to design around, this skill
should say so rather than inventing one — a vague "let's sync" request may
need a quick Business Analyst framing pass first.

## Output Contract

A single Markdown event design artifact with these sections, in order:

1. **Objective and expected outcome** — what must be true after the event
   that wasn't true before (a decision made, a plan aligned, a set of
   actions owned) — not merely "discussed."
2. **Participants and decision roles** — who is a decider, contributor, or
   informed-only, and why.
3. **Pre-read and preparation** — what participants need to review or
   prepare beforehand, and by when.
4. **Agenda** — timed segments with a stated purpose each.
5. **Facilitation method and materials** — how each segment runs
   (discussion, silent brainstorm, dot-voting, etc.) and what materials it
   needs.
6. **Accessibility and remote/hybrid considerations** — concrete
   accommodations (captioning, async participation path, time-zone
   fairness, materials shared in advance), not a generic statement that
   accessibility "will be considered."
7. **Decision capture plan** — exactly how decisions and dissent get
   recorded during the event (who scribes, what template, where it's
   filed).
8. **Action ownership** — how actions get assigned and tracked
   post-event, not left only in free-text notes.
9. **Post-event routing** — where the record of what happened lands (see
   Canonical Routing).
10. **Explicit non-actions** — a one-line statement that this design does
    not schedule the event, invite participants, or send any message; that
    remains a human's explicit action.

## Stepwise Workflow

1. Confirm the objective is concrete enough to design around; if not,
   name what's missing rather than guessing.
2. Map participants to decision roles.
3. Design pre-read scoped to what's actually needed — avoid asking people
   to read everything.
4. Build a timed agenda matched to the objective (a decision needs
   discussion + a decision moment; a retro needs safe reflection + action
   capture) — do not default to a generic one-size-fits-all agenda.
5. Choose a facilitation method per segment, not one method for the whole
   event.
6. Design concrete accessibility/remote-hybrid accommodations.
7. Design the decision-capture and action-ownership mechanics before the
   event, not as an afterthought.
8. State the post-event routing destination.
9. State explicitly that scheduling/inviting/messaging is out of scope and
   remains a human action.
10. Route the artifact and stop.

## Quality Gates

- the objective names a concrete "what's different after" outcome, not
  just a topic;
- every participant has a stated decision role;
- the agenda's segments each state a purpose and a facilitation method;
- accessibility accommodations are concrete, not boilerplate;
- a decision-capture mechanism and an action-ownership mechanism are both
  present;
- the "explicit non-actions" line is present verbatim in every output;
- no unresolved template placeholder tokens (an un-filled marker left in the output).

## Non-Authority Boundaries

This skill must not, under any circumstance, even if asked directly:

- schedule the event on any calendar;
- send invitations, reminders, or any external message to participants;
- expose personal data (contact details, availability, personal
  schedules) beyond what is already committed in the Cell's own records;
- optimize the design for entertainment value when the event has a
  concrete business outcome — facilitation choices serve the objective,
  not novelty;
- leave decisions or actions recorded only in free-text meeting notes with
  no structured capture/ownership mechanism.

If asked to schedule or invite, this skill still produces the design and
then states plainly that scheduling/inviting is a separate human action it
does not perform — it does not refuse to help entirely.

## Privacy Boundaries

- do not list personal contact information, availability data, or
  out-of-office details beyond what is already committed and necessary for
  the design;
- do not disclose one participant's private input to others without their
  consent already being on record.

## Human Gate Conditions

Route to a Human Gate instead of finalizing the design when:

- the objective itself is contested (different stakeholders want the
  event to achieve different things) — that is a decision-owner question,
  not a facilitation-design question;
- the participant list would need to include someone outside the Cell's
  normal authorized audience;
- the event's decision would materially change an existing accepted
  priority or roadmap commitment.

## Canonical Routing

| Situation | Routes to |
|---|---|
| Design accepted, event will happen | new `work/` `WorkItem` holding the design, pre-event |
| Objective contested or audience question | new `human-gates/` `HumanGate` |
| Post-event: decisions/actions captured | append to the same `WorkItem`, or a new `CellUpdate` if the outcome is Cell-visible |
| Post-event: the work this event was for is complete | `CompletionRecord` on the relevant `WorkItem` (authored when the actual follow-through work closes, not by this skill at design time) |
| Repeatable facilitation pattern observed | `history/learning-candidates/` `LearningCandidate` |

## Bounded Context-Loading Route

Load only: this file, the stated objective/constraints, and — only if
brand/journey-sensitive material will be discussed — the domain brain's
bounded index pointer. Do not load Business Analyst or Requirements
Engineering while running this skill.

## Positive Example

Request: "We need to align the team on next quarter's loyalty roadmap
priorities." Correct handling: objective = "a ranked, team-agreed
priority list for next quarter exists after the event," decision roles
mapped (Product Owner = decider, engineers/design = contributors),
pre-read = the current backlog and any accepted Business Analyst
analyses, agenda with a framing segment + a structured prioritization
method (e.g. dot-voting) + a decision-confirmation segment, concrete
accessibility notes (materials shared 48h ahead, async input channel for
a time-zone-remote teammate), a named scribe and a decision-capture
template, actions assigned with owners, routed to a pre-event `WorkItem`,
and the explicit statement that scheduling/inviting remains a human
action.

## Negative Example

Same request. Incorrect handling this skill must avoid: producing a
generic "1. Intros 2. Discussion 3. Wrap-up" agenda with no facilitation
method tied to the actual prioritization objective; describing
accessibility as "we'll make sure it's accessible" with no concrete
accommodation; leaving decision capture as "someone will take notes"; or,
worst, actually creating a calendar invite or drafting a message to send
to participants instead of stopping at the design.
