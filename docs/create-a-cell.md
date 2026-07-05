# Create an Active Cell

This is the first-hour operational path: from cloning this starter to a
working Cell that a human and an agent can operate together. The concepts
behind each step live in `core-model.md`, `cell-story.md`, and
`why-these-surfaces.md`; this page is only about doing.

## 0. Decide what the Cell is for

One sentence. If you cannot write it, you do not need a Cell yet. Example:
"Run the shared work of our two-person events team and maintain our domain
knowledge."

## 1. Create the repository

A Cell is a Git repository. Private by default — publishing anything is a
separate, gated decision (`public-private-boundary.md`).

## 2. Lay down the core tier

Every Cell starts with five files and six folders:

```text
README.md          ← what this Cell is, in one screen
PROJECT.md         ← purpose, scope, trust model, data policy
AGENTS.md          ← how agents must operate here
CONTEXT_INDEX.md   ← what to read first, what to skip
TEAM.md            ← who participates, who decides
inbox/     work/     human-gates/     history/     playbooks/     scripts/
```

Copy the templates from `templates/` in this starter, or copy the whole
`examples/djbrain-cell/` and replace its fictional content. Put artifact
templates *in-surface* (`work/TEMPLATE.task.md`,
`human-gates/TEMPLATE.human-gate.md`) — that is where agents look.

Do not create more folders yet. Surfaces are added when they earn their place,
not upfront.

## 3. Write the three contracts

1. **`CONTEXT_INDEX.md`** — entry points, load-when rules, do-not-load rules.
   This is the routing layer; agents read it before anything else.
2. **`AGENTS.md`** — start protocol (confirm repo → `git status` → read
   PROJECT + CONTEXT_INDEX → read the assigned work item → load only what the
   task needs), routing table, and the completion contract. Keep it short;
   route details to playbooks.
3. **`TEAM.md`** — participants with stable IDs (`human:<name>`), exactly one
   decision owner. Agents act `on_behalf_of_human_id` — accountability always
   traces to a human.

## 4. Run the first loop

1. Append the first raw request to `inbox/INBOX.md`.
2. Create `work/TASK-YYYYMMDD-001-<slug>.md` from the template: goal, inputs,
   allowed/forbidden actions, deliverables, validation, Definition of Done.
3. If the task touches anything sensitive (publishing, spending, deleting,
   external commitments), create a human gate first and wait for the decision
   owner.
4. Execute. Commit.
5. Append the **Completion Record** to the task file: `status: done`, who
   completed it, changed files, validation results, commit SHA. Work without a
   Completion Record is not done — this is the single most important habit in
   BCOS.

## 5. Add surfaces when they earn their place

| Add | When |
|---|---|
| `decisions/` | resolved choices need to be findable apart from gates |
| `reports/` | analysis starts accumulating |
| `proofs/` | completion claims need standalone, auditable evidence |
| `handoffs/` | work crosses sessions, people, or agents |
| `library/` | a pattern has proven itself and will be reused |
| `apps/<app-id>/` | a domain knowledge area becomes an actively queried capability |

The `apps/` rule: **active capability → `apps/<app-id>/`; passive proven
pattern → `library/`.** An app package gets its own `README.md`,
`CONTEXT_INDEX.md`, `knowledge/`, `prompts/`, and its own proof loop. See
`examples/djbrain-cell/` for the full worked shape, including the promotion
decision record.

## 6. How agents start (the short version)

An agent entering a well-formed Cell needs no briefing:

```text
read CONTEXT_INDEX.md → read AGENTS.md → read the assigned task
→ do only what the task allows → append the Completion Record → commit
```

If your agent needs more than that to be safe, the fix is a better task file
or a better routing rule — not a longer chat prompt.

## 7. Prove, hand off, complete

- **Proof** closes a claim: strong enough that nobody has to take
  `status: done` on faith.
- **Handoff** carries continuation: where things stand, what is next, what to
  watch out for, anchored to a commit SHA and a Completion Record.
- **Completion** is a committed Completion Record plus verified push — never
  prose in a chat window.

The worked chain in `examples/djbrain-cell/README.md` shows all three in
eight files.
