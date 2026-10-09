---
name: tenant-index
description: Refresh or read the index of what's in the Sprout demo tenant (groups, profiles, tags, campaigns, listening topics, teams, queues, recent activity). Use when an SE says "refresh the tenant index", "what's in the demo tenant", "which profiles/topics/campaigns do we have", or before planning a demo when context/tenant-index.md is more than 30 days old.
---

# Tenant index

The index is generated from the Sprout API and never edited by hand.

**Where to work.** Most users only read the index: use the bundled copy of
`context/tenant-index.md`. Refreshing needs the Sprout API token and a clone of
`jbaumtana/spt`, which is a job for a tenant admin or the plugin owner. If an
SE asks for a refresh and there's no token, say so in plain language and ask them
to request one from the owner. Don't show commands.

## Read it
Answer from `context/tenant-index.md` plus the hand-written notes in
`context/tenant-baseline.md` (what's ours, personas, landmines). The API can't
see Reddit, calendar contents, report names, Trellis, or screen layouts. For
those, check `context/tenant-index-ui.md` if it exists, otherwise say they
come from the browser pass (`docs/browser-pass.md`).

## Refresh it (in a clone)
1. `python3 tools/sprout_api.py check`: the token must reach the customer in
   `config.json` and nothing else. Credentials come from `SPROUT_API_TOKEN` or
   the environment's proxy. If it fails, stop and say so.
2. `python3 tools/sprout_api.py index`. Read-only: about a dozen API calls.
3. `git diff --stat context/tenant-index.md`. Daily activity counts always
   change. Point out anything else that changed (new or removed profiles,
   tags, topics, groups) since it means someone changed the shared tenant.
4. Commit `context/tenant-index.md` with "Refresh tenant index".

Never copy user names or emails into the repo, and never print the name of a
tag in `blocked_tag_ids`.
