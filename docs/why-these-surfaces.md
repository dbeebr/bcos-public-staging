# Why These Surfaces

BCOS surfaces are not arbitrary folders. Each one exists because a specific operating
problem was observed, evaluated, and resolved through a deliberate decision process.

This document explains the reasoning behind the current BCOS surface model. If you are
wondering why the repository is organized this way — why Library exists, why History and
Reports are separate, why there is no top-level code surface — this is where to look.

The goal is transparency: you should be able to evaluate whether these decisions match
your own operating problems. If they do, the structure will feel natural. If they do not,
you should understand why the choices were made and whether they need adapting for your
context.

---

## Library: Where Proven Knowledge Lives

Operating teams — whether human, AI-agent-assisted, or fully distributed — produce
knowledge alongside their work product. A task template that proved clearer than the
default. A decision pattern that resolved a recurring question. A handoff format that
transferred context reliably.

Without a dedicated surface, this knowledge scatters across archived tasks and old
decisions. Teams keep solving problems they have already solved.

Library is the surface for knowledge that has been proven through use and is worth reusing.
It is curated, not comprehensive — only artifacts that have demonstrated their value earn
a place.

Library is separate from History because they answer different questions. History records
what happened: comprehensive, chronological, audit-oriented. Library holds what should be
reused: selective, timeless, action-oriented. History feeds Library through distillation;
the best of what happened becomes a reusable pattern. Both are needed.

---

## History: The Chronological Record

History is the surface that keeps the record complete and the accountability intact.

It holds what happened — completed tasks, resolved decisions, accepted reviews, evidence
trails. History is not curated; it is comprehensive. Its value is not "what should I
reuse?" but "what actually happened, when, and why?"

History protects accountability. When a decision was made and later questioned, History
is where the evidence lives. When work crossed sessions and something went wrong, History
is where you trace the chain.

A common temptation in knowledge management is to merge History and Library into one
surface — a single "knowledge base" that holds everything. The result is a surface that
does everything and helps with nothing, because finding a proven pattern requires scanning
past every raw record.

BCOS keeps History and Library separate because they answer different questions:

- **History** answers: "What happened?" — comprehensive, chronological, audit-oriented.
- **Library** answers: "What should I reuse?" — curated, timeless, action-oriented.

The relationship is directional: History feeds Library. A decision pattern that proved
useful multiple times is worth distilling into a Library entry. But the raw decision
records stay in History — they are the evidence that the pattern is real.

---

## Reports: Analytical Outputs Stay Findable

Reports are evaluations, analyses, and explorations — point-in-time documents that inform
decisions. They are not chronological records (that is History) and not curated patterns
(that is Library).

Reports stay top-level because folder names are the cheapest routing signal for both humans
and AI agents. An agent scanning a repository sees `reports/` and knows immediately where
analytical outputs live. Burying reports inside History would save one folder at the cost
of making every report harder to find.

When a report produces a reusable insight, that insight can be distilled into a Library
entry. The report itself stays in `reports/` as the source evidence.

---

## Work: Active Execution

`work/` is the surface for in-progress work: tasks being executed, drafts in flight,
active deliverables. It is scoped, bounded, and temporary — work that is not yet
complete, not yet evidence, not yet history.

Work is the entry point. Everything that eventually becomes a History record, a Library
entry, or a proof began as something in `work/`.

---

## Human Gates: Accountable Decision Points

`human-gates/` is the surface where work pauses for human judgment.

Some steps should not be automated or delegated: publishing content, changing repository
visibility, approving a license, committing to a public interface, making irreversible
changes. Human Gates mark these points explicitly.

A Human Gate records who decides, what they are deciding, what evidence they reviewed,
and what they approved. It is not a meeting or a process step — it is a durable record
of a deliberate human decision at a specific moment.

The surface exists separately because accountability must remain intact. A Human Gate
cannot be bypassed by an agent or completed by inference. It is the mechanism that keeps
the Cell honest about where human judgment is required.

---

## Playbooks: Repeatable Procedures

`playbooks/` holds step-by-step procedures that a Cell has followed successfully and
would follow again. Not templates (those are Library), not analyses (those are Reports),
but repeatable operational sequences.

Playbooks reduce friction for recurring work: onboarding a new participant, preparing
a review, running a validation cycle, executing a deployment pattern. Once a procedure
has been run successfully and is stable, it earns a place in `playbooks/`.

---

## Scripts: Cell Infrastructure

`scripts/` holds the tooling that serves the Cell itself — validators, linters, setup
scripts, automation helpers used in Cell operations. These are not outputs of Cell work;
they are what makes Cell operations reliable.

Scripts are infrastructure. They support the Cell's operating processes: checking that
artifacts are well-formed, validating that conventions are followed, ensuring that
commits meet quality standards.

---

## Why There Is No Code Surface

BCOS is a knowledge operating layer. Most teams using it coordinate decisions, handoffs,
and context — they do not write software as part of Cell operation.

But some teams do produce small scripts, automations, and helper tools during their work.
BCOS handles this without a dedicated top-level surface, using a clear routing path:

- **Active code work** starts in `work/` as a task deliverable, scoped and bounded.
- **Cell infrastructure** (validators, linters, setup scripts) lives in `scripts/`, which
  serves the Cell itself.
- **Proven reusable helpers** — scripts or tools that have been used successfully multiple
  times — may be curated into `library/tools/` after human approval.
- **Maintained software** with its own lifecycle, tests, and releases belongs in a separate
  repository.

Adding a code surface to every Cell would imply that writing code is expected. For most
teams — especially those using BCOS for decision-making, project coordination, or
distributed knowledge work — a code surface would be confusing and unnecessary.

The decision to defer a code surface is itself evidence-backed: the routing path above
handles real code-like work without requiring a new top-level folder. If future operating
evidence shows that a dedicated code surface is needed, it can be added. The decision
is deferred, not rejected.

---

## How Reports, History, and Library Work Together Over Time

The three surfaces form a lifecycle:

```text
A question is asked → Reports produces an analysis
  → The analysis informs a decision → The decision is recorded in History
  → If the decision pattern recurs and proves useful → distill into Library
  → Library makes the next similar decision faster
```

Reports are not dead ends. They are the thinking layer. History is the evidence layer.
Library is the reuse layer. Each feeds the next.

Over time, a well-operated Cell accumulates a Library that reflects its real operating
experience — not theory, not aspirations, but patterns that have been tested in real work
and proven worth keeping.

---

## Evidence-Backed Design

BCOS surfaces are not prescribed by a framework. They emerge from operating experience.

Each surface was added (or deferred) based on observed routing problems: knowledge with no
clear home, analytical outputs that were being buried under chronological records, pressure
to add surfaces that most teams do not need. Each decision was evaluated against multiple
options, decided by a human, and documented with rationale.

This matters because it means the structure reflects real needs, not theory. If a surface
exists, there is evidence behind it. If a surface does not exist, there is a reason it was
deferred. The shape of a BCOS Cell is designed to reduce friction and protect accountability
— not to seem comprehensive.

---

## How a Small Team or Public Reader Should Understand the Shape of a Cell

If you are looking at a BCOS Cell for the first time, here is how to read it:

- **Start with the Context Index** — it tells you what to read and what to skip.
- **`work/`** shows you what is active right now.
- **`reports/`** shows you what has been analyzed.
- **`decisions/`** shows you what has been settled.
- **`history/`** shows you the full record of what happened.
- **`library/`** shows you what the Cell has learned and kept.
- **`playbooks/`** shows you how recurring procedures are run.
- **`human-gates/`** shows you where human judgment was required.
- **`scripts/`** serves the Cell's operations — you rarely need to read it for work context.

The surfaces are routing signals. Each one tells a human or an AI agent where to look for
a specific type of context without opening every file. That is the design.

A Cell with a growing Library has been operating long enough to know what it has learned.
A Cell with a clear separation between History and Library has the discipline to distinguish
between "what happened" and "what should be reused." A Cell with explicit Human Gates has
a clear boundary between automated execution and human judgment.

These are not bureaucratic features. They are the evidence that the Cell is working.
