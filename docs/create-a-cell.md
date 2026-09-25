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

## Install path: a ready Teamcell Lite Cell

The fastest way to a working Cell is the Teamcell Lite kit in
`distribution/teamcell-lite/`. It ships the core tier, a validator, a daily
start command and optional packages, and it installs from a plain clone of
this repository — no account, token or private repository needed.

**Requirements:** Git with your name and e-mail configured
(`git config --global user.name ...` / `user.email ...`), Python 3 with
PyYAML (`python3 -m pip install --user pyyaml`), a POSIX shell. The GitHub CLI
is not needed; cloning this public repository and installing locally require
no GitHub account or token. External AI services may require their own
accounts or credentials if you use the optional instruction-block step below.
This release candidate was tested on macOS only (Python 3.12
with PyYAML 6; the Cell-side instruction renderer and validators also with
the macOS system Python 3.9 without PyYAML). Linux and WSL on Windows are
expected to behave the same but were not run for this release.

Run these commands exactly as written; only change the value of `MY_ID`:

<!-- quickstart:start -->
```sh
# Your stable participant id: lowercase letters, digits and hyphens.
MY_ID='your-name'

git clone https://github.com/dbeebr/bcos-public-staging.git bcos
cd bcos

# 1. Preview: writes nothing. Optional packages: add
#    --optional-package teamcell-plus-profile, or
#    --optional-package team-capability-pack (selects Plus too).
python3 scripts/teamcell-install-preview.py ../my-cell --mode new_from_template

# 2. Read the preview (source, kit integrity, packages, files, governance),
#    then confirm exactly that target: the same command plus --confirm.
python3 scripts/teamcell-install-preview.py ../my-cell --mode new_from_template \
  --confirm --confirmed-by "human:$MY_ID"

# 3. Write the durable installation receipt.
python3 scripts/generate-teamcell-installation-receipt.py ../my-cell

# 4. Commit the installed Cell, then start it.
cd ../my-cell
git add -A
git commit -m "Install Teamcell Lite"
./scripts/start-cell.sh
```
<!-- quickstart:end -->

Optional, interactive — generate the project instruction block for your
agents (ChatGPT, Claude, Copilot, Gemini or a local model host), rendered
from the Cell's one shared instruction core, with its procedure index and a
ChatGPT size check; then commit the generated files:

```sh
../bcos/scripts/personalize-team-cell.sh "$PWD"
```

Then replace the fictional example team in `TEAM-PROFILE.md`, select a
governance profile in `.bcos/CELL-GOVERNANCE.yaml` when ready, and create
your first work item as `work/TASK-YYYYMMDD-NNN-<slug>.md` from
`work/TEMPLATE.task.md`. It is executable once
`python3 scripts/validate-completion.py --ready <path>` reports READY; what
nobody knows yet stays marked `OPEN: ...` instead of being guessed.

What each step guarantees:

- The preview never writes. A non-empty target, an unknown package or an
  ambiguous request is refused before anything is created.
- The preview shows `kit_integrity`: `verified` when the kit matches
  `distribution/teamcell-lite/SOURCE-MANIFEST.json`, otherwise the receipt
  records the version as `+local-modifications`.
- The receipt records source commit, version, packages and every installed
  file; it refuses when packages and files disagree with the tree.
- This distribution installs new Cells only (`new_from_template`). It
  refuses `hydrate_existing_repo` (known defect in this release: its
  post-install closeout fails after files were written) and
  `clone_existing_cell` (not validated) before anything is previewed or
  written; see `teamcell-install-semantics.md`.
- Running `scripts/bootstrap-team-cell.sh` directly is not a supported entry
  point — it skips preview, confirmation, governance file and receipt.

The rest of this page describes the manual path: building the same core tier
by hand, which is also how to understand what the kit contains.

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

Install the Teamcell Lite kit (above), copy the templates from `templates/`
in this starter, or copy the whole `examples/setbrain-cell/` and replace its
fictional content. Put artifact
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
`examples/setbrain-cell/` for the full worked shape, including the promotion
decision record.

## 6. How agents start (the short version)

An agent entering a well-formed Cell needs no briefing:

```text
read the Cell entry (AGENTS.md → PROJECT.md → CONTEXT_INDEX.md)
→ read the assigned task → run its format check (validate-completion.py
--ready; stop on open items) → check the Procedure Index, load matching
procedures in full → do only what the task allows → append the Completion
Record (with the procedures actually applied) → commit
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

The worked chain in `examples/setbrain-cell/README.md` shows all three in
eight files.
