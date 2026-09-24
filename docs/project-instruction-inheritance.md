# Project Instruction Inheritance

## Decision

BCOS and every BCOS-governed Cell use **one agent-agnostic project-instruction
core** (contract version 2.0). Product, vendor and model names do not define
behavior or authority. An agent declares its capability at runtime from the
access it can actually verify. Role (planner, executor or both), app surface
and the host's real capabilities are three separate inputs; none of them is
derived from another. Planning and execution are work steps, not products:
planning may persist tasks and hand authorized execution over, and
implementation is the execution step. Authority comes only from the decision
owner and recorded gates — never from role, capability, task wording or a
model's suggestion.

```text
templates/PROJECT-INSTRUCTIONS.template.md   the one shared rule core
  + .bcos/CELL-PROFILE.yaml                  Cell entry, routing, where procedures live
  + Procedure Index (CONTEXT_INDEX.md)       generated from procedure frontmatter
                    ↓  scripts/render-instructions.py
  instructions/PROJECT-INSTRUCTIONS.md       the budget-checked paste block
  instructions/APP-INSTRUCTIONS-*.md         thin activation notes (where to paste)
  context pack / profile JSON                for local hosts, on demand
```

Application settings are activation surfaces only. Git remains the source of
truth.

## Capability classes

| `agent_capability_class` | Declared when the agent… |
|---|---|
| `local-worker` | works in a local checkout with shell/filesystem access |
| `git-only-worker` | writes only through a Git connector or API |
| `chat-reviewer` | has no repository write access |
| `read-only-observer` | may inspect but not write |
| `automation` | runs unattended (scheduled or triggered) |

These are the canonical values of `agent_capability_class` in
`schemas/routing-frontmatter.schema.md`. The legacy values `coding-agent` and
`design-agent` are still accepted, with a validator warning.

The same product can expose different capabilities in different sessions (a
chat product with no connector is a `chat-reviewer`; with a Git connector it
may be a `git-only-worker`). Product name is therefore never a proxy for
authority, evidence or available actions.

## The Cell instruction body

`instructions/PROJECT-INSTRUCTIONS.md` is the only complete instruction body in
a Cell. The installer's mandatory personalization step
(`scripts/personalize-cell.py`, run inside the new Cell) and the interactive
`scripts/personalize-team-cell.sh` (surfaces and role) call the Cell's own
`scripts/render-instructions.py`, which fills the core
with Cell facts (repository, Cell name, local path, bound human and role,
governance profile, tone, language, timezone — resolved from the installation
receipt, the Cell's governance file and personalization input) and with the
Cell profile and Procedure Index. The file records its render inputs, a source
hash and a block hash in its frontmatter.

Reusable templates never hardcode a real person or another Cell's repository.
If required evidence is absent, the rendered instruction shows an explicit
unresolved state; it never falls back to a prior owner or a default name.
Substitution is single-pass: user input is inserted literally.

## Mandatory inherited behavior

**Thinking co-worker.** The agent decides routine matters from available
evidence, thinks about automation and repeatability, explains material choices,
asks only at a genuine decision point, authority boundary or underivable fact,
produces copyable and executable outputs, and turns repeatable work into
procedures, work items or automation candidates. This stance never overrides
governance, decision ownership, customer commitments, budget, privacy,
security, irreversible-action or external-visibility gates.

**Git truth.** Git is the only source of truth for the Cell. Chat history,
memory and "done" statements are not proof. Read the current artifact before
status, completion or next-step claims; distinguish user-reported from
Git-verified state; do not claim completion without a committed and remotely
verified outcome when an `origin` exists.

**Durable artifacts.** No Cell-governed output exists only as chat prose. It
is committed, or supplied as a complete copy/paste artifact when write access
is unavailable.

| Output | Route (Teamcell Lite profile) |
|---|---|
| raw input | `inbox/INBOX.md` |
| executable work | `work/TASK-YYYYMMDD-NNN-<slug>.md` (earlier `work/WORK-*.md` stay valid) |
| human decision | `human-gates/` |
| evidence, review or accepted decision | `history/` (verification reports: `reports/verification/`) |
| reusable procedure | `playbooks/` |

The routing lines in a rendered block come from the Cell profile, so a Cell
with different real paths renders its own routes from the same core.

**Entry before work.** Before planning or changing anything, the agent loads
the Cell entry named in the profile (Teamcell Lite: `AGENTS.md` →
`PROJECT.md` → `CONTEXT_INDEX.md`), then the assigned task or gate, then the
procedures it needs. Without file or Git access it asks for them; a path it
has not read is not loaded context. A task's start prompt points to this
entry instead of repeating a file list.

**Procedures.** The agent checks the Procedure Index when a task or sub-task
starts, at every handover, at a phase change and when a new finding appears.
A matching procedure is loaded in full before it is applied, and its use is
recorded with evidence; naming a procedure is not using it. A reasoned `none`
is valid, and there is no per-message ritual. When nothing fits, the agent
says "no matching installed procedure found" and labels any general draft as
such. A missing index entry alone does not prove that a specific package is
absent; with a routed, unreadable or stale index the agent says it cannot
tell.

**Planning and handoff.** A planner persists everything the executor needs in
the task — scope, gates, acceptance, selected procedures with path/version,
access limits, return evidence and an executable start prompt — and records
who planned it on which surface. It writes the task in the format of the
Cell's current task template (`task_template` in `.bcos/CELL-PROFILE.yaml`),
read from the repository or, without access, from a planning context pack
that carries the template with its hash; facts, IDs or approvals it does not
have are marked `OPEN: <what>`, never invented. It persists only with write
access it actually has; otherwise it hands over a copy/paste artifact marked
`persisted: false`. A handoff never widens scope or authority, and no model
suggestion dispatches work by itself.

**Format check before execution.** A persisted task is executed only after it
passes the Cell's format check (`task_check`; Teamcell Lite:
`python3 scripts/validate-completion.py --ready <task>`). Fields a fixed rule
derives — constants, the ID from the file name, the created date from the
ID, the title from the heading, the task's own path in its start prompt —
may be filled with `--fix` inside the authorized write scope without a new
approval. Missing content, actor identity, IDs or approvals keep the task a
draft that is not executable, and an executor context pack for such a task
is refused. An executor re-reads the task and the entry itself and re-checks
the index; the planner's selection does not replace that.

**Complete work package.** Follow-up work is delivered as the smallest complete
package: goal and route (plan, build, design, review, repair or Human Gate);
target path; scope and non-goals; deliverables; gates and authority
boundaries; completion criteria and validation; an executable agent brief with
reasoning level; and a collision check when concurrent work exists. The human
should not have to ask separately for the prompt or brief.

**Learning loop.** Repeated failures, friction, governance misses, routing
defects or repeated human corrections become durable learning in the smallest
governed local artifact. At closing, the Completion Record's
`closing_learning` names a reusable pattern or correction with evidence and
scope limit and routes it (improve an existing procedure, propose a
candidate, or `none`); there is no duty to find one every time. Nothing is
promoted or activated automatically. Learning that concerns BCOS itself is
proposed upstream; a Cell never silently changes the upstream source.

**Session start and close.** Governed sessions start with:

```text
BCOS CELL MODE ACTIVE
agent_id: <actual agent id>
capability_class: local-worker | git-only-worker | chat-reviewer | read-only-observer | automation
repository: __REPOSITORY__
session_entry_point: <work item, gate or unspecified>
git_state: verified | unverified
```

They close with durable completion evidence — preferably the Completion Record
in the work item (`schemas/completion-record.schema.md`), including
`procedures_applied` (what was loaded and applied, with evidence, or `none`)
and `closing_learning`. A separate handoff, when needed, names agent, date,
Git state, final SHA or `PENDING`, changed files, task status, procedures,
open items and one concrete next action. No recommendation-only ending.

## Runtime capability rules

- **`local-worker`** — verify repository, branch, working tree and remote; read
  `AGENTS.md`, `PROJECT.md`, `CONTEXT_INDEX.md` and the assigned work or gate;
  edit and validate; commit, push and verify `origin/main`. A local commit or a
  tool's success message is not remote proof.
- **`git-only-worker`** — use only the connector actions actually available;
  read current remote artifacts first; verify resulting commits against the
  remote head; never claim local shell or filesystem evidence.
- **`chat-reviewer`** — claim no repository or completion evidence without
  verification; use read connectors when present; otherwise produce complete
  copy/paste artifacts with target path and commit message, marked
  `pending-verification` until Git confirms.
- **`read-only-observer`** — inspect and report with evidence; never write,
  approve or claim a mutation.

## Host capabilities and local model hosts

A render may declare the host's real capabilities (`file_read`, `git_read`,
`git_write`, `tools`, `network`, `persistent_memory`). Anything not declared is
unavailable, and no prompt or task text grants more; the rendered block
states the highest capability class those capabilities allow. Undeclared
capabilities (the usual case for a chat app) leave the agent to classify
itself from observed access. For local model hosts the renderer produces
three outputs from the same core: a compact instruction block for hosts
without tools, a context pack for manual or host-side insertion (a planning
pack carries the instructions, Cell entry files and the current task
template; a task pack adds the task and the full text of its procedures and
is built only for a task that passes the format check; both carry the full
index lines of any procedure group the block routes via a sub-index), and a
machine-readable profile for hosts with retrieval or tools. The host's chat
template, system-role handling and tool permissions remain the host's
integration work; nothing here runs, downloads or configures a model.

**Known gap:** the context pack does not yet automatically select or
include a Cell's identity and governance files (`TEAM-PROFILE.md`,
`.bcos/CELL-PROFILE.yaml`, `.bcos/CELL-GOVERNANCE.yaml`,
`docs/teamcell-gate-matrix.md`) or a specific inbox entry, and does not warn
when it silently omits them — pick the relevant procedures explicitly
(`--procedure <name>`, repeatable) and add any needed identity/governance/
inbox file to the pack by hand until this is fixed. See
`reports/verification/PUBLIC-CELL-RELEASE.md` ("Scope and limits") for the
evidence this was found against a real external-model test.

## Budgets

ChatGPT project instructions are budgeted: target 7200, hard limit 8000,
measured on the exact personalized paste text as the larger of Unicode code
points and UTF-16 code units (this does not claim which count the platform
uses). Over the target, whole procedure groups are routed through their named
sub-index (first by name, then by pointer only); a rule or entry is never cut.
Over the hard limit the renderer refuses. Local context packs use a token
budget with response and task reserves, measured with the host's tokenizer
when one is given and otherwise reported as an estimate, never as a pass.

## Activation wrappers

Per-product wrapper files are optional and thin. They record the paste
destination, the path of `instructions/PROJECT-INSTRUCTIONS.md`, the semantic
source and version, a provisional likely capability, and
generated/reviewed/activated (self-reported) state. They never duplicate the
instruction body, fork governance rules, or claim that external settings were
changed automatically.

## Generation and drift

`scripts/render-instructions.py` resolves nothing on its own that it cannot
record: every render stores its inputs, a source hash (core, profile, index,
renderer, inputs) and a hash of the block. `./scripts/validate-cell.sh` then
fails when the Procedure Index no longer matches the procedure files, when a
rendered block was edited by hand, or when it exceeds its hard limit, and it
warns when a render is stale. `render-instructions.py refresh` re-renders from
the recorded inputs; the new block must be pasted again, and its activation
stays self-reported.

An upstream wording change never silently rewrites existing Cells: propagation
is a versioned migration with a visible diff. New Cells get the latest accepted
baseline.

## Minimum validation

A conforming Cell instruction set proves: exactly one complete body; no
duplicated body in wrappers; no named-person fallback; repository and Cell
identity resolved or explicitly unresolved; Git truth, capability
self-classification, entry-before-work, procedure selection and loading,
co-worker stance, work-package and durable-artifact rules, planning/handoff
and role/authority separation, the format check before execution, the
"no matching procedure" rule, closing learning, and session start/close
behavior present; the Procedure Index lists only
available procedures; budgets met; no wrapper claiming automatic settings
changes; source, contract and version identified. File and render checks prove
the text; whether a given model follows it is a separate, observed question.
