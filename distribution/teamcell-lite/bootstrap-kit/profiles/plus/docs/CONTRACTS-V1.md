---
bcos_type: doc
id: TEAMCELL-PLUS-CONTRACTS-V1
title: "Teamcell Plus — v1 contract reference"
status: active
created: 2026-07-12
created_by: claude-code-main
agent_model: claude-code-main
related:
  - profiles/plus/README.md
---

# Teamcell Plus — v1 contract reference

Decided by the BCOS maintainers from operating evidence of earlier Cells (decision record not part of this distribution).
Eight contracts, each expressed as required frontmatter fields on the file
type named, not as a separate schema file.

| Contract | Where it lives | Required fields |
|---|---|---|
| `CellIdentity` | `TEAM-PROFILE.md` | `participants[]` (human_id, github, role, decision_authority), `agents[]` (agent_id, model, capability_class) |
| `ActorIdentity` | every artifact's frontmatter | `created_by`, `created_by_type`, `created_by_id`, `on_behalf_of_human_id` (when an agent writes for a human) |
| `WorkItem` | `work/TASK-*.md` (`work/WORK-*.md` legacy) | `status`, `work_status`, `created_by*`, `on_behalf_of_human_id` (see `work/TEMPLATE.task.md`) |
| `HumanGate` | `human-gates/*.md` | `gate_status` (`draft`\|`open`\|`accepted`\|`changes-requested`\|`rejected`\|`withdrawn`), `decision_class`, `decision_owner_role`, `decision_owner_id`. **Hardened rule**: no commit referencing this gate's ID may land with a message implying implementation while `gate_status != accepted`. |
| `CompletionRecord` | appended to the closing work item | the full field list in `AGENTS.md` "Completion", checked by `scripts/validate-completion.py` |
| `CellUpdate` | GitHub Issue, label `cell-update` | plain-language body, links to the `WorkItem`/`HumanGate`/commit it concerns, actor attribution line |
| `NotificationPolicy` | `profiles/plus/scripts/morning-pulse.sh` config block + Cell Update mentions | recipients (explicit, no default-all), channel (GitHub notifications only for v1), receipt log = the Issue's own comment/reaction thread |
| `LearningCandidate` | `history/learning-candidates/*.md` | `status` (`candidate`\|`observed_once`\|`repeated`\|`ready_for_bcos_review`), non-canonical, human-gated promotion only |

Rejected for v1: `ArtifactEnvelope`,
`ContextIndex`-as-schema (kept as a template, not validated), `CellSnapshot`,
`BriefContract`-as-schema, separate `DeliveryReceipt`/`InteractionReceipt`
(merged into `NotificationPolicy`), separate `LearningExport` (the promotion
status on `LearningCandidate` already is the export step), `KnowledgeSource`,
merged `CellEvent` into `CellUpdate`.
