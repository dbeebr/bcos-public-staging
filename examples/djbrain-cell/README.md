# djbrain Cell — Example Starter

This is a BCOS example Cell for an active domain brain called `djbrain`.

It shows the preferred pattern for a maintained domain capability:

```text
Cell governance at the root
Active capability under apps/djbrain/
Evidence in proofs/
Continuation in handoffs/
Reusable patterns distilled to library/
```

## Start here

1. Read `PROJECT.md`.
2. Read `AGENTS.md`.
3. Read `CONTEXT_INDEX.md`.
4. Read `apps/djbrain/README.md`.
5. Create work in `work/` before changing the app package.

## Structure

```text
README.md
PROJECT.md
AGENTS.md
CONTEXT_INDEX.md
TEAM.md
inbox/
work/
decisions/
human-gates/
reports/
proofs/
handoffs/
history/
library/
playbooks/
apps/
  djbrain/
    README.md
    CONTEXT_INDEX.md
    knowledge/
    prompts/
    reports/
    proofs/
```

## Rule of thumb

`djbrain` is an app package because it is active. It has its own context, prompts, outputs, and proof loop. When a pattern inside `djbrain` becomes generally reusable, distill that pattern into `library/`.
