---
name: demo-overlay
description: Build, validate, and apply the prospect overlay for an approved Sprout demo plan, with no tenant writes. Use when an SE says "build the overlay for <prospect>", "apply the overlay", "get the demo ready", "make the run sheet", or "revert the overlay". Needs an approved plan in runs/<run>/plan.md and, to apply live, Claude in Chrome.
---

# Demo overlay

**Rules first.** Read `CLAUDE.md` and follow it. Do nothing until
`runs/<run>/plan.md` has `approval.approved_by` filled in by a human SE. The
overlay changes only what's on screen; it makes no tenant writes. Watermark off.
Generated numbers are never the prospect's results.

## Steps
1. Read the run's `plan.md`, `context/tenant-index.md`,
   `context/tenant-index-ui.md`, and `context/click-paths/app-map.json`. Use
   only screens, profiles, tags, and topics found there.
2. Write `runs/<run>/data-pack/demo-data.json` (relabels, sample captions,
   `outOfClickPath` for seed labels left alone, brand colors). Keep copy free of
   health or efficacy claims; personas are invented.
3. Build and validate: `python3 tools/overlay_payload.py build runs/<run>/data-pack/demo-data.json`, then `check`. Fix every error; never hand-edit the payload.
4. Write `runs/<run>/run-sheet.md`: timed screens, what to say, guardrails, and a
   pre-call checklist. Flag screens whose selectors aren't in the app map yet.
5. To apply live (Claude in Chrome only): confirm the tab is the tenant named in
   `context/tenant-baseline.md`, inject `tools/overlay/overlay-engine.js`, call
   `__demoTailor.apply(payload)`, and screenshot each screen to verify. Offer
   `__demoTailor.revert()` after the demo.
6. Close with `python3 tools/sprout_api.py inventory` and `diff` against the
   before inventory; the diff should show no tenant changes.
