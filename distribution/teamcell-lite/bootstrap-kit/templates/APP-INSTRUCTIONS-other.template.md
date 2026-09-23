---
bcos_type: app_instruction_block
id: APP-INSTRUCTIONS-OTHER
title: "Other App Project Instructions — __CELL_NAME__"
created_by: personalize-team-cell
agent_model: interactive-shell
created: __CREATED_DATE__
status: draft
semantic_source: instructions/PROJECT-INSTRUCTIONS.md
inheritance_contract: docs/project-instruction-inheritance.md (Teamcell distribution)
contract_version: "2.0"
---

# Other App Project Instructions — __CELL_NAME__

This app is an activation surface, not a separate behavioral source.
Paste the complete fenced block from `instructions/PROJECT-INSTRUCTIONS.md`
(this Cell's one agent-agnostic project instruction body) into the app's per-project or per-workspace custom instructions. Do not
paste it into an account-wide or global preferences layer — that layer
should only hold stable preferences that apply across every project.

The block in `instructions/PROJECT-INSTRUCTIONS.md` is rendered by
`scripts/render-instructions.py` from the Cell's one shared core, its
profile and its Procedure Index; the file states its measured size, the
role it was rendered for (planner, executor or both) and the index version.
When the Cell's procedures change, re-render
(`python3 scripts/render-instructions.py refresh`) and re-paste: the app
keeps the old text until you do.

Local model hosts (no model download, no new server, nothing activated
automatically) get outputs rendered for the capabilities the host really
provides. Declare them with `--caps` from `file_read, git_read, git_write,
tools, network, persistent_memory`; anything not declared is unavailable,
and the host enforces tool rights independently of any prompt. A model's
chat template and system-role handling are the host's integration work.

- Instruction block for a host without tools:
  `python3 scripts/render-instructions.py block --surface local --role executor --caps none`
- Planning context pack (instructions, Cell entry files and the Cell's
  current task template with its sha256 and Git blob) for a planner without
  file access:
  `python3 scripts/render-instructions.py context-pack --surface local --caps none --role planner`
- Task context pack (instructions, Cell entry files, the work item and the
  full text of its procedures) for manual or host-side insertion — refused
  (exit 5) while the work item fails
  `python3 scripts/validate-completion.py --ready <work item>`:
  `python3 scripts/render-instructions.py context-pack --surface local --caps none --role executor --task work/<TASK-file>.md --token-budget <n> --reserve-response <n> --reserve-task <n>`
  — add `--tokenizer-cmd "<command printing a token count>"` to measure with
  the host's tokenizer; without it the token count is an estimate only. An
  oversize pack is refused, never cut.
- Machine-readable profile for a host with retrieval or tools:
  `python3 scripts/render-instructions.py profile-json --surface local --caps file_read,git_read`

Without write access the model delivers a complete candidate artifact or
handoff marked `persisted: false`; with write access the Cell's gates,
bounded write set and verification apply unchanged.

This file does not duplicate that body. It only records:

- paste destination: the app's per-project or per-workspace custom instructions, scoped to work on __REPOSITORY__;
- likely initial capability (provisional — the block itself re-classifies
  at session start from actual access): `chat-reviewer` unless the app demonstrably has repository access; declare `read-only-observer` when unsure. The product name does
  not itself establish authority or Git capability;
- activation truth: recorded only as self-reported. Git cannot verify an
  external project setting directly.

This file does not claim that the paste happened — see
`reports/verification/POST-INSTALL-PERSONALIZATION.md` for the
generated/reviewed/activated-self-reported lifecycle state.
