---
name: demo-overlay
description: Get an approved Sprout demo ready: build the prospect's on-screen branding (overlay), write the run sheet, apply the overlay in Chrome, and revert it afterward. Use when an SE says "build the overlay for <prospect>", "get the demo ready", "make the run sheet", "apply the overlay", or "revert the overlay". Needs an approved plan from demo-plan.
---

# Demo overlay

The user is an SE, not a developer: no paths, code or JSON in what you say.
Describe the result ("Your Lilly branding is ready; here's the run sheet").

## Gate
Open the run's `plan.md` in `sprout-demo-runs/<run>/`. If **Approved by** is
blank, stop and send them to `demo-plan`. Follow the plan's ground rules (look
at the demo-plan skill): overlay only, no tenant writes, nothing public carries
the prospect's name, sample data is never the prospect's results, no health
or efficacy claims, invented personas only.

## Steps
1. **Selectors:** use `sprout-demo-runs/_app-map/` if present, else the bundled
   `context/click-paths/`. If a planned screen (Listening, Reports) has no
   selectors, tell the SE and offer the `browser-pass` skill first, or continue
   knowing that screen won't be relabeled.
2. **Content:** write `data-pack/demo-data.json` in the run folder: relabels,
   six or more date-neutral sample captions, brand colors, and
   `outOfClickPath` for tenant names left alone.
3. **Build** the overlay file with the bundled script, quietly:
   `python3 <plugin>/tools/overlay_payload.py build <run>/data-pack/demo-data.json --app-map <app-map> --ui-index <ui-index>`
   then `check`. Fix every error. If Python can't run, build the same rules by
   hand from the script's documented format and say it wasn't machine-checked.
4. **Run sheet:** write `run-sheet.md`: timed screens, what to say, what to
   click, guardrails, and a pre-call checklist.
5. **Apply live** (Claude in Chrome): confirm the open tab is Secure Patient
   Technology and the SE has reserved it; load the bundled
   `tools/overlay/overlay-engine.js`; `__demoTailor.apply(payload)`; screenshot
   each planned screen and report what didn't change.
6. **After the demo,** offer `__demoTailor.revert()` and confirm the tab is back
   to normal. Tell the SE no tenant data was changed.
