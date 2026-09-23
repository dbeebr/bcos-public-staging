---
bcos_type: doc
kind: playbook
surface: playbooks
domain: operations
id: PLAYBOOK-VALIDATOR-BASELINE
title: "Validator Baseline and Delta Playbook"
status: active
procedure_kind: "playbook"
use_when: "validate-cell.sh already fails before your change and you must prove you added no new failure"
not_when: "A fresh Cell or the template fails, or the failure is yours: fix it instead"
phase: "execute, close"
created: 2026-09-21
created_by: claude
created_by_type: agent
created_by_id: agent:claude
created_by_display: "Claude"
created_by_github: null
on_behalf_of_human_id: "human:{{CELL_OWNER_ID}}"
agent_id: agent:claude
agent_model: claude-opus-5
agent_capability_class: local-worker
---

# Validator Baseline and Delta Playbook

Prove that a change added no new validator failure when the Cell already
fails validation for reasons outside that change. A known failure stays
visible and unfixed; it is never silently accepted.

## Trigger

- `./scripts/validate-cell.sh` fails before you have changed anything, and
  the failures are not yours to fix in the current work item.
- You are about to write "validation: pass" or "no new failures" in a
  Completion Record while the plain validator run fails.

## Not A Trigger

- A freshly installed Cell or the template itself fails validation. Repair
  the defect; never record a baseline to legitimize it.
- The failure is caused by your own change. Fix it.
- You only want fewer failures in the output. A baseline is evidence, not a
  filter.

## Inputs

- The current work item.
- `./scripts/validate-cell.sh` output from the state **before** your change
  (a clean checkout of the base commit; never stash or discard someone
  else's uncommitted work to obtain it).
- An existing baseline file, if the Cell already records one.

## Steps

1. **Record the before-state.** Before changing anything — or in a separate
   worktree of the base commit (`git worktree add ../cell-base <sha>`) when
   your change already started — run:

   ```sh
   ./scripts/validate-cell.sh --write-baseline reports/verification/VALIDATOR-BASELINE.txt
   ```

   The file lists one exact failure identity per line (rule text plus the
   affected path or field), with the recording time and commit. If a
   baseline file already exists and is committed, use it instead of
   rewriting it.
2. **Review each listed identity.** For every line, decide: known and out of
   scope (keep, route a repair work item), or actually caused by this work
   (remove it from the baseline and fix it). Do not keep a line you cannot
   explain.
3. **Make your change**, then compare by identity:

   ```sh
   ./scripts/validate-cell.sh --baseline reports/verification/VALIDATOR-BASELINE.txt
   ```

   - `NEW (blocking)`: a failure that is not in the baseline. It blocks even
     when the total failure count is unchanged (for example, one known
     failure disappeared and a different one appeared).
   - `KNOWN (still present, not fixed)`: report it as known, never as fixed.
   - `RESOLVED (remove from baseline)`: delete that line from the baseline
     in the same commit, so it cannot silently return later.
4. **Record the evidence** in the Completion Record `validation` block, for
   example:

   ```yaml
   - validation:
       - ./scripts/validate-cell.sh --baseline reports/verification/VALIDATOR-BASELINE.txt: pass (0 new, 2 known, 1 resolved)
       - git diff --check: pass
   ```

5. **Route every known failure** that you kept to a work item (or reference
   the existing one) in `follow_up_routing`.

## Output

- A committed baseline file whose every line is explained and routed.
- A validator run against that baseline with zero new failures.
- A Completion Record that distinguishes known, resolved and new failures.

## Validation

```sh
./scripts/validate-cell.sh --baseline reports/verification/VALIDATOR-BASELINE.txt
git diff --check
git status --short --untracked-files=all
```

## Limits

- Identity is the exact failure text. If a rule's wording changes between
  validator versions, record a fresh baseline on the base commit rather
  than editing lines by hand to make them match.
- A baseline covers failures only. Warnings are reported but never
  baselined.
