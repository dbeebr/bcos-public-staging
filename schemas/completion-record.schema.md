# Schema — Completion Record

A task is done when — and only when — a Completion Record is appended to the
task file and committed. This is the mechanism that separates "an agent said
it finished" from "the work is verifiably finished".

## Required fields

```yaml
status: done
completed_by: <human-or-agent-id>
completed_date: YYYY-MM-DD
commit_sha: <hash of the commit containing the substantive change>
changed_files:
  - <path>: <one-line annotation of what changed and why>
validation:
  <check-name>: pass | fail | <output summary>   # at minimum: git diff --check
recommendation_only_ending: false
```

## Required fields for agent completions

```yaml
on_behalf_of_human_id: human:<id>
```

## Recommended fields

```yaml
proof: <path>                 # when the claim needs standalone evidence
follow_up: <path or none>     # routed follow-up work — never prose-only
human_gate_required: []       # gates this work surfaced, or empty
accepted_risks:
  - <risk knowingly left open>
notes: <anything the next reader needs>
procedures_applied:           # what was loaded AND applied, with evidence
  - <PROCEDURE-ID>: loaded <path>@<version>; applied: <evidence>
  - none: <reason>            # when no procedure applied
closing_learning: none        # or: pattern/correction, evidence, scope, route
```

## Rules

1. **No completion without a commit.** If the remote exists, verify the push;
   record the SHA you verified, not the SHA you hope for.
2. **`recommendation_only_ending: false` is a claim, not a formality.** If the
   session produced advice about durable work, that advice must exist as a
   task, gate, or handoff file before the record is written.
3. **Failed validation blocks the record.** Fix it or record the task as not
   done with a handoff explaining the state.
4. **The record is append-only.** Corrections are new records or new tasks,
   never edits that rewrite what was claimed.

See `examples/setbrain-cell/work/TASK-20260701-001-seed-set-brief-guide.md` for
a complete worked example.

## Teamcell Lite (operating profile)

The Teamcell Lite kit (`distribution/teamcell-lite/`) implements this schema
in its stricter operating form. Its `AGENTS.md` and `work/TEMPLATE.task.md`
require, before `work_status: done`: `status: done`, `completed_by` (or
`agent`), `completed_date`, `substantive_commit_sha` (or `commit_sha`),
`completion_record_commit_sha` (`same` or a SHA),
`remote_head_verified_at_completion` (the verified origin SHA, or
`local-only` when the Cell has no `origin`), `changed_files`, `validation`
(including `./scripts/validate-cell.sh` and `git diff --check`),
`build_drift`, `follow_up_routing`, `human_gate_required`,
`recommendation_only_ending: false`, `handoff_anchor`, `accepted_risks`,
`notes`, `procedures_applied` and `closing_learning` (the last two only warn
when missing, so older records stay valid).

The Cell's `./scripts/validate-cell.sh` enforces this through
`scripts/validate-completion.py`. It fails when:

- a done work item has no Completion Record, a record whose `status` is not
  `done`, a missing field, or a value still in template form (`<...>`,
  `YYYY-MM-DD`, `a | b`);
- the Definition of Done still has an unchecked `- [ ]` item;
- a SHA is not a full 40-character SHA, does not exist in the repository, or
  the recorded remote head does not contain the substantive commit;
- `local-only` is recorded although an `origin` remote exists;
- a recorded validation says `fail`;
- a Completion Record says done while `work_status` is not `done` (status
  drift in the other direction);
- a `procedures_applied` entry claims `applied` without `loaded <path>`, or
  names a procedure that is neither in the Cell's Procedure Index nor an
  existing path — naming a procedure is not evidence of using it.

Pre-existing validator failures are handled by exact failure identity, never
by count: `./scripts/validate-cell.sh --baseline <file>` blocks any failure
not listed in the baseline, even when the total is unchanged (the kit's
`playbooks/VALIDATOR-BASELINE.playbook.md`).
