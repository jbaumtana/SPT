# Guardrails

A one-pager for the Security/IT and Legal conversations.

| Risk | Control |
| --- | --- |
| Agent acts in the wrong tenant | The session only reaches the tenant the SE is logged into (S4). The agent confirms it's the sandbox at the start of each session (CLAUDE.md rule 2) |
| Agent publishes in a real company's name, or touches accounts we don't own | Publishing only from demo-owned accounts, with plan-approved content. Prospect names go in drafts and DMs, never in public posts. No interaction with outside accounts (CLAUDE.md rule 3) |
| Fake activity on real social networks | Never publish or engage on real networks. All liveliness is seeded or overlaid |
| Sample metrics mistaken for real results | No disclaimer required (L2). Metrics are never described as the prospect's real results, a benchmark, or a promise |
| Fabricated quotes from real people | Invented personas only for commenters, DM senders, and reviewers |
| Prospect info leaks | `runs/` is git-ignored. Security approved giving prospect notes to Claude (S1) |
| API-created draft publishes live and can't be deleted via the API | Confirmed that API posts stay drafts, even when scheduled (D9). API client locked to the demo customer ID |
| Leftover data between demos | Every tenant write is logged to a manifest before it's made, and reset walks the manifest backward |
| Unreviewed agent actions | The plan approval gate. Browser runs are visible to the SE |
| Regulated verticals (healthcare, public sector) | Playbooks carry compliance landmines. Generated copy must look like it would clear the prospect's legal review |
