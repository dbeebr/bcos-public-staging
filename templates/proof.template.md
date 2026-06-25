---
id: PROOF-YYYYMMDD-NNN
title: "Proof that [claim] is true"
status: draft
created: YYYY-MM-DD
created_by: human-or-agent-id
task_ref: TASK-ID (if applicable)
claim: "State the specific claim this proof supports"
---

# PROOF-YYYYMMDD-NNN — Title

## Claim

State the specific claim this proof is intended to support.

## Evidence

### Evidence Item 1

- **Type:** commit / validation output / review record / test result / other
- **Source:** where this evidence comes from
- **Artifact:** file path, commit SHA, or URL
- **Timestamp:** YYYY-MM-DD HH:MM
- **Verifier:** who or what verified it

### Evidence Item 2

- **Type:**
- **Source:**
- **Artifact:**
- **Timestamp:**
- **Verifier:**

## Verification Method

How can a future reader independently verify this proof?

```bash
# Example: check that the commit exists on origin
git fetch origin main
git log --oneline origin/main | grep <commit-sha>
```

## Result

- **Claim supported:** yes / no / partial
- **Confidence:** high / medium / low
- **Limits:** What does this proof not cover?

## Notes

Any additional context, caveats, or follow-up items.
