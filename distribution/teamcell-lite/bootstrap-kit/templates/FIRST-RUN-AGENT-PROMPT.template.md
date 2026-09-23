---
bcos_type: prompt
id: FIRST-RUN-AGENT-PROMPT
title: First Run Agent Prompt (Generalized)
created_by: personalize-team-cell
agent_model: interactive-shell
created: __CREATED_DATE__
status: draft
---

# First Run Agent Prompt (Generalized) — __CELL_NAME__

Hand this prompt to the first agent session you run in this Cell, whichever
agent/app surface you selected during personalization. It proves one real
work loop end to end and records `reports/verification/FIRST-RUN-INSTALL-HANDOFF.md`,
which `./scripts/validate-cell.sh` checks for first-use readiness.

```text
0. Workspace verification (hard stop, do this first)
   Before reading or writing anything:
   a. Confirm the currently open workspace folder is exactly:
      __TARGET_PATH__
   b. Confirm this repository/cell identity matches exactly:
      __REPOSITORY__ (cell name: __CELL_NAME__)
   c. If the expected path above does not exist, stop immediately and output:
      STOP: workspace_path_missing
      Expected: __TARGET_PATH__
      No files were changed.
      Next action: reopen VS Code on the expected folder or rerun the
      installer/wizard for the current folder.
   d. If the currently open workspace path or repository identity differs
      from the values above, stop immediately and output:
      STOP: workspace_identity_mismatch
      Expected: __TARGET_PATH__ (__REPOSITORY__)
      Actual: <actual path/repo/cell if available>
      No files were changed.
      Next action: reopen VS Code on the expected folder or rerun the
      installer/wizard for the actual folder.
   e. Do not search the broader local filesystem for alternate BCOS-like
      repos.
   f. Do not proceed in a different repository just because it also has
      AGENTS.md or Team Cell markers — those alone do not prove identity.
   Only continue to step 1 once the workspace path and identity are
   confirmed to match exactly.

1. Identity declaration
   Before writing anything, declare:
   agent_id: <stable identifier>
   capability_class: local-worker | git-only-worker | chat-reviewer | read-only-observer

2. Capability class
   Determines whether you may write locally and/or commit/push. If you are
   unsure which class you are, declare read-only-observer and ask.

3. Context package (read only these, do not load the whole repository)
   - the Cell entry, in order: __SESSION_ENTRY__
     (listed under session_entry in .bcos/CELL-PROFILE.yaml)
   - TEAM-PROFILE.md
   - inbox/INBOX.md
   - work/README.md
   - the active work item (see step 4a)
   Then check the Procedure Index in CONTEXT_INDEX.md against that work
   item. Load a matching procedure's full file before applying it, or note
   "none" with a reason. An index line is not loaded content.

4. Allowed actions
   - Read the repository instruction files above.
   a. Find the active work item the way ./scripts/start-cell.sh does:
      among work/TASK-*.md and work/WORK-*.md (never TEMPLATE*.md), the
      first with `work_status: in-progress`, else `needs-review`, else
      `open`. Read only that file, not the whole work/ directory.
   - If no such work item exists yet, create exactly one draft work item
     work/TASK-YYYYMMDD-NNN-<slug>.md (from work/TEMPLATE.task.md) from the
     first inbox item. Do not mark it accepted. Preserve the append-only
     inbox. Write facts, IDs or approvals you do not have as "OPEN: <what>";
     never invent them.
   - Create the proof handoff described in step 7.

5. Forbidden actions
   - mutate_canonical_truth_without_human_decision
   - rely_on_chat_only_state
   - claim_completion_without_git_evidence

6. Git truth verification
   Before any completion claim, run:
   ./scripts/validate-cell.sh
   git status --short --untracked-files=all

7. Work item state
   Report which work item you identified as active in step 4a (or which one
   you created) and the result of
   python3 scripts/validate-completion.py --ready <that work item>
   (READY, or its open items — a new draft is usually not ready yet). Do not
   mark it accepted or done yourself.

8. Proof handoff
   Create reports/verification/FIRST-RUN-INSTALL-HANDOFF.md (if it does not
   already exist). Frontmatter: bcos_type: report, kind:
   first_run_install_handoff, surface: reports, id:
   FIRST-RUN-INSTALL-HANDOFF, title, status: draft, created, created_by,
   agent_model, the actor identity fields from AGENTS.md, and: cell_id,
   cell_name, hosted_repository (or null), hosted_repository_url (or null),
   hosted_head (verified SHA or null), first_inbox_item,
   created_first_task_path, instruction_files_used, validation_command,
   validation_result, git_status_command, git_status_result,
   team_policy_placeholders_remaining, readiness_status
   (local-only | hosted | team-ready), procedures_checked (the index
   version you saw and the procedures you selected, loaded and applied, or
   none with a reason), open_proof_items. Record only what you verified;
   unknown values stay null.

Repository: __REPOSITORY__
Local workspace: __TARGET_PATH__
Preferred communication tone: __TONE__
Primary working language: __LANGUAGE__

Do not mark the task accepted. Do not claim completion. Do not set accepted
truth.
```
