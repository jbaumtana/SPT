---
name: add-playbook
description: Add or update an industry playbook for Sprout demos in context/playbooks/. Use when an SE says "add a playbook for <industry>", "create the <vertical> playbook", "update the healthcare playbook", "save what worked in this demo", or "what playbooks do we have". Maps the vertical onto the real demo tenant using context/tenant-index.md.
---

# Add or update a Sprout demo playbook

A playbook holds what's true for **every** prospect in one vertical. The
tenant index holds what's in the tenant. The prospect layer lives in `runs/`.
Keep the three apart.

**Where to work.** Playbooks are shared, so they're written in a clone of
`jbaumtana/spt` (the current folder has `context/tenant-index.md`) and
committed. Without a clone, read from `${CLAUDE_PLUGIN_ROOT}/context/` and give
the SE the finished playbook to add through a pull request.

## Steps

1. **Read first:** `context/playbooks/_template.md`, the existing playbooks in
   `context/playbooks/` (list them for the SE), and `context/tenant-index.md`.
   If the index is older than 30 days, offer to refresh it with
   `python3 tools/sprout_api.py index` (read-only).
2. **Ask in one round** (AskUserQuestion), only for what's missing:
   - Vertical name, and who's usually in the room
   - The 2 to 4 pains that come up on every call
   - Landmines and any approved answers to common objections
   - Sources: won deals, SE notes, enablement docs (files can go in `context/sources/`)
3. **Write** `context/playbooks/<vertical-slug>.md` from the template. For an
   update, edit in place, bump "Last updated", and keep the SE's wording.
4. **Fill "Tenant fit" from the index only.** Pick the demo brand group,
   profiles, listening topics, and campaign tags by their names and IDs in
   `tenant-index.md`. If nothing fits, say so under **Gaps** and suggest the
   overlay. Never invent a profile, topic, tag, screen, or report.
5. **Check before saving:**
   - No real company or person names (prospect-neutral)
   - Every screen in the story arc appears in the index or `context/click-paths/`
   - Every ID in Tenant fit appears in the index
   - Gaps say TODO, never a guess. Approved answers come from the SE, not general knowledge
   - Never use tag `4162648`
6. **Commit** the playbook on the current branch with a one-line message, and
   tell the SE what's still TODO.

## Saving what worked after a demo

When an SE says a demo went well, read its `runs/<run>/plan.md` and
`run-sheet.md`, and propose only what generalizes: vocabulary, story beats,
data patterns, objections, what didn't work. Show the diff and let the SE
confirm before writing. Never copy the prospect's name, handles, or brief.
