---
name: demo-plan
description: Plan a tailored Sprout demo for a prospect on the shared demo tenant, with an SE approval gate before anything is built. Use when an SE says "plan a demo for <company>", "prep a Sprout demo for <prospect>", "start a demo run", or "build the demo plan". Uses the tenant index and the industry playbook; hands off to demo-tailor for research, data, overlay, and talk track.
---

# Plan a Sprout demo

**Rules first.** Read `CLAUDE.md` in the repo (or
`${CLAUDE_PLUGIN_ROOT}/CLAUDE.md`) and follow it. The essentials: no build
before a human SE approves the plan; the demo tenant only; prospect names never
in public posts; generated numbers are never the prospect's results.

**Where to work.** Use a clone of `jbaumtana/spt` if the current folder has
`context/tenant-index.md`. Otherwise read from `${CLAUDE_PLUGIN_ROOT}` and
write the run folder in the current folder. Run folders hold prospect
information and are never committed. The script is `python3 tools/sprout_api.py`
in a clone, `python3 ${CLAUDE_PLUGIN_ROOT}/tools/sprout_api.py` otherwise.

## Steps
1. **Context.** Read `context/tenant-index.md`, `context/tenant-baseline.md`,
   `context/click-paths/`, and the playbook in `context/playbooks/` for the
   prospect's industry. No playbook? Offer the `add-playbook` skill, or carry
   on with the closest one and note the gap.
2. **Ask in one round** (AskUserQuestion): which company exactly, demo date and
   length, attendees, what discovery said. "Nothing yet" is fine; mark those
   TODO.
3. **Brief.** Research the prospect (demo-tailor `prospect-brief` if
   installed, else web search with sources). Write
   `runs/<YYYY-MM-DD>-<slug>/brief.yaml` (schema: `schemas/prospect-brief.schema.json`)
   and a readable brief. Mark every inferred pain as an inference.
4. **Plan.** Write `runs/<run>/plan.md` following `examples/demo-plan.example.md`.
   Each screen answers one pain. Use only screens, profiles, topics, and tags
   that appear in the index, click paths, or the playbook's Tenant fit. Default
   to the overlay with no tenant writes. Leave **Approved by** as
   `_(SE name)_`.
5. **Stop.** Show the plan and ask the SE to approve it in their own words.
   Never fill in the approval line yourself before they do. Any later change
   to the plan clears the approval.
6. **After approval:** take a before inventory
   (`python3 tools/sprout_api.py inventory --out runs/<run>/inventory-before.json --run runs/<run>`),
   then demo-tailor `demo-data-pack` and `demo-narrative` into the run folder.
   Build the overlay with `python3 tools/overlay_payload.py build runs/<run>/data-pack/demo-data.json`
   (it validates before writing), not by hand.
   The live overlay (`demo-overlay`) needs a session on the SE's computer with
   Claude in Chrome. Inject `tools/overlay/overlay-engine.js` from this repo
   (the fixed copy), not demo-tailor's own engine. Finish with an after inventory and `diff`.
