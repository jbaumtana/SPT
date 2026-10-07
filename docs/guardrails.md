# Guardrails

A one-pager for the Security/IT and Legal conversations.

| Risk | Control |
| --- | --- |
| Agent acts on a production tenant or customer data | Demo tenants only (CLAUDE.md rule 2). Scoped demo-only credentials (S2). Technical guard requested (S4) |
| Fake activity on real social networks | Never publish or engage on real networks. All liveliness is seeded or overlaid |
| Sample metrics mistaken for real results | Labeled as sample data. Overlay watermark on by default. Talk track includes a disclosure line |
| Fabricated quotes from real people | Invented personas only for commenters, DM senders, and reviewers |
| Prospect info leaks | `runs/` is git-ignored. Retention terms confirmed with Security (S1) |
| API-created draft publishes live and can't be deleted via the API | Unscheduled drafts only until D9 is answered. API client locked to the demo customer ID |
| Leftover data between demos | Every tenant write is logged to a manifest before it's made, and reset walks the manifest backward |
| Unreviewed agent actions | The plan approval gate. Browser runs are visible to the SE |
| Regulated verticals (healthcare, public sector) | Playbooks carry compliance landmines. Generated copy must look like it would clear the prospect's legal review |
