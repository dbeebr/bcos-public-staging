---
bcos_type: state
kind: inbox
surface: inbox
id: INBOX
title: "Team Inbox"
status: active
created: 2026-06-24
created_by: codex
created_by_type: agent
created_by_id: agent:codex
created_by_display: "Codex"
created_by_github: null
on_behalf_of_human_id: "human:{{CELL_OWNER_ID}}"
agent_id: agent:codex
agent_model: gpt-5
agent_capability_class: local-worker
append_only: true
---

# Team Inbox

Append-only raw intake. Do not edit or delete existing entries. Add a correction
as a new entry.

Entry format:

```text
[YYYY-MM-DD HH:MM] #tag - content
```

Tags:

`#task` `#decision` `#risk` `#source` `#question`

## Entries

<!-- Append below. -->
