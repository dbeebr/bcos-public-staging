---
bcos_type: doc
kind: prompt
id: DJBRAIN-APP-SET-BRIEF-PROMPT
title: "djbrain prompt — generate a set brief"
status: active
created: 2026-07-01
created_by: example-agent
created_by_type: agent
created_by_id: agent:example-agent
created_by_display: "Example Agent"
on_behalf_of_human_id: human:alex-rivera
surface: apps
app_id: djbrain
related:
  - ../knowledge/genre-notes.md
  - ../knowledge/venue-profiles.md
---

# Prompt — Generate a Set Brief

*(Fictional example of a versioned prompt payload.)*

## Inputs the agent must load first

- `../knowledge/genre-notes.md` — only the genre sections the booking needs
- `../knowledge/venue-profiles.md` — only the venue being booked

## Prompt payload

```text
Write a one-page set brief for the booking below.

Use exactly five parts in this order: Hook, Genre line, Arc, Venue fit,
Practicals. Use only genre vocabulary and venue facts from the loaded
knowledge files — if something is missing, say "not in djbrain yet" instead
of inventing it. Text only: no images, no links to photos.

Booking: {{date, venue, slot, audience notes}}
```

## Versioning rule

Changing this payload is a knowledge change: route it through a `work/` task
(see the update playbook). The distilled five-part pattern lives in the
Cell-level `library/PATTERN-set-brief.md`; this file is the operating original.
