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
