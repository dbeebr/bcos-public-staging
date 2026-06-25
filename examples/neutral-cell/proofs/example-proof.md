---
id: PROOF-20260101-001
title: "Proof that CONTRIBUTING.md draft is committed"
status: verified
created: 2026-01-02
created_by: human:alex
task_ref: TASK-20260101-001
claim: "CONTRIBUTING.md was committed to the local main branch and pushed to origin"
---

# PROOF-20260101-001 — Proof That CONTRIBUTING.md Draft Is Committed

## Claim

`CONTRIBUTING.md` was committed to the `main` branch of `example-project` and
pushed to `origin/main` as part of completing TASK-20260101-001.

## Evidence

### Evidence Item 1 — Commit SHA

- **Type:** git commit
- **Source:** local repository after task completion
- **Artifact:** `a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2`
- **Timestamp:** 2026-01-02 14:30
- **Verifier:** git log

### Evidence Item 2 — Push Confirmation

- **Type:** push to origin/main
- **Source:** git push output
- **Artifact:** `origin/main` HEAD equals local HEAD
- **Timestamp:** 2026-01-02 14:31
- **Verifier:** `git rev-parse HEAD` and `git rev-parse origin/main` match

### Evidence Item 3 — Validation Pass

- **Type:** validation command output
- **Source:** `git diff --check` run before commit
- **Artifact:** exit code 0, no whitespace errors
- **Timestamp:** 2026-01-02 14:29
- **Verifier:** exit code

## Verification Method

```bash
git fetch origin main
git log --oneline origin/main | grep a1b2c3d
git show a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2 --stat
```

## Result

- **Claim supported:** yes
- **Confidence:** high
- **Limits:** This proof covers commit and push only. Publication to a public
  remote requires the Human Gate in `human-gates/example-human-gate.md`.

## Notes

The contribution guide is committed locally and on the team's private remote.
It has not been published publicly. That step awaits gate approval.
