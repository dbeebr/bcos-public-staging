---
bcos_type: app_instruction_block
id: APP-INSTRUCTIONS-CLAUDE
title: "Claude Project Instructions — __CELL_NAME__"
created_by: personalize-team-cell
agent_model: interactive-shell
created: __CREATED_DATE__
status: draft
semantic_source: instructions/PROJECT-INSTRUCTIONS.md
inheritance_contract: docs/project-instruction-inheritance.md (Teamcell distribution)
contract_version: "2.0"
---

# Claude Project Instructions — __CELL_NAME__

Claude/Cowork is an activation surface, not a separate behavioral source.
Paste the complete fenced block from `instructions/PROJECT-INSTRUCTIONS.md`
(this Cell's one agent-agnostic project instruction body) into this
Claude Project's custom instructions. Do not paste it into Claude's global
personal preferences — that layer should only hold stable preferences that
apply across every project.

The block in `instructions/PROJECT-INSTRUCTIONS.md` is rendered by
`scripts/render-instructions.py` from the Cell's one shared core, its
profile and its Procedure Index; the file states its measured size, the
role it was rendered for (planner, executor or both) and the index version.
When the Cell's procedures change, re-render
(`python3 scripts/render-instructions.py refresh`) and re-paste: the app
keeps the old text until you do.

This file does not duplicate that body. It only records:

- paste destination: a Claude Project's custom instructions, scoped to
  work on __REPOSITORY__;
- likely initial capability (provisional — the block itself re-classifies
  at session start from actual access): `local-worker` when this is
  Claude Code or Cowork with local repository access at __TARGET_PATH__,
  `chat-reviewer` for Claude Chat without it. The product names `Claude`,
  `Cowork` or `Claude Code` do not themselves establish authority or Git
  capability;
- activation truth: recorded only as self-reported below. Git cannot
  verify an external Project setting directly.

This file does not claim that the paste happened — see
`reports/verification/POST-INSTALL-PERSONALIZATION.md` for the
generated/reviewed/activated-self-reported lifecycle state.
