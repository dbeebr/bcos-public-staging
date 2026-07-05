---
bcos_type: record
kind: proof
id: PROOF-20260701-001
title: "Proof — set-brief guide seeded and validated"
status: done
created: 2026-07-01
created_by: example-agent
created_by_type: agent
created_by_id: agent:example-agent
created_by_display: "Example Agent"
on_behalf_of_human_id: human:alex-rivera
surface: proofs
related:
  - ../work/TASK-20260701-001-seed-set-brief-guide.md
---

# PROOF-20260701-001 — Set-Brief Guide Validation

*(Fictional example.)*

## Claim

TASK-20260701-001 is complete: djbrain can answer "write a set brief" with a
canonical format backed by genre notes, under the text-only posture of
HUMAN-GATE-20260630-001.

## Evidence

1. **Deliverables exist** — `apps/djbrain/knowledge/genre-notes.md`,
   `apps/djbrain/knowledge/venue-profiles.md`,
   `apps/djbrain/prompts/set-brief.prompt.md`, each with routing frontmatter.
2. **Gate posture respected** — repository-wide scan for image embeds in brief
   materials: none found.
3. **First real use** — Sam produced a brief for the fictional "Harbor Loft"
   booking using only djbrain content; the promoter accepted it without a
   format question. That closes the original inbox request of 2026-06-30.

## Why this is proof and not a report

A report analyzes; a proof closes a claim. This record exists so the task's
`status: done` never has to be taken on faith. Anyone auditing the Cell can
re-run the scan and re-read the deliverables.
