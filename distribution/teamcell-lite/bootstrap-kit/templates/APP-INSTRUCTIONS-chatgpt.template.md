---
bcos_type: app_instruction_block
id: APP-INSTRUCTIONS-CHATGPT
title: "ChatGPT Project Instructions — __CELL_NAME__"
created_by: personalize-team-cell
agent_model: interactive-shell
created: __CREATED_DATE__
status: draft
semantic_source: instructions/PROJECT-INSTRUCTIONS.md
inheritance_contract: docs/project-instruction-inheritance.md (Teamcell distribution)
contract_version: "2.0"
---

# ChatGPT Project Instructions — __CELL_NAME__

ChatGPT is an activation surface, not a separate behavioral source. Paste
the complete fenced block from `instructions/PROJECT-INSTRUCTIONS.md` (this
Cell's one agent-agnostic project instruction body) into this ChatGPT
Project's custom instructions. Do not paste it into personal account-wide
"Custom Instructions" — that layer should only hold stable preferences that
apply across every project.

The block in `instructions/PROJECT-INSTRUCTIONS.md` is rendered by
`scripts/render-instructions.py` from the Cell's one shared core, its
profile and its Procedure Index; the file states its measured size, the
role it was rendered for (planner, executor or both) and the index version.
When the Cell's procedures change, re-render
(`python3 scripts/render-instructions.py refresh`) and re-paste: the app
keeps the old text until you do.

ChatGPT's project instruction field is budgeted: the rendered block targets
at most 7200 characters and never exceeds 8000, counted conservatively as
the larger of Unicode code points and UTF-16 code units (this does not
claim which count ChatGPT itself uses). If you add your own lines after
pasting, keep the total under 8000; the renderer never cuts rules to fit —
it routes whole procedure groups through their sub-index or refuses.

Planning without a repository connector: give the Project the planning
context pack (`python3 scripts/render-instructions.py context-pack --surface
chatgpt --role planner`), which carries the Cell's current task template, so
the task it returns has the right format. Whoever persists the returned
task runs `python3 scripts/validate-completion.py --ready <task>` before any
execution starts; open facts, IDs or approvals stay with the planner or
decision owner.

This file does not duplicate that body. It only records:

- paste destination: a ChatGPT Project's custom instructions, scoped to
  work on __REPOSITORY__;
- likely initial capability (provisional — the block itself re-classifies
  at session start from actual access): `chat-reviewer` unless a
  repository connector is actually configured for this Project, in which
  case `git-only-worker`. The product name `ChatGPT` does not itself
  establish authority or Git capability;
- activation truth: recorded only as self-reported below. Git cannot
  verify an external Project setting directly.

This file does not claim that the paste happened — see
`reports/verification/POST-INSTALL-PERSONALIZATION.md` for the
generated/reviewed/activated-self-reported lifecycle state.
