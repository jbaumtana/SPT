---
name: browser-pass
description: Look through the Sprout demo tenant in Chrome, read-only, and record what's on each screen so overlays can target it (Listening, Reports, Calendar, Composer, Approvals, Inbox, Trellis). Use when an SE says "run the browser pass", "scan Listening and Reports", "refresh the app map", "Sprout's UI changed", or when a demo needs a screen the bundled notes don't cover. Needs Claude in Chrome and the SE logged into Sprout.
---

# Browser pass

The user is an SE, not a developer: no paths, code or JSON in what you say.
Narrate in plain language ("Looking at Listening now").

## Safety
Read-only. Never click save, send, publish, approve, delete, or anything in
Settings. Never leave text typed in a field. Never copy real people's names,
emails or message text into notes. Never try to log in: if Claude in Chrome
isn't connected or Sprout isn't open and signed in, ask the SE to do that and stop.

## Steps
1. Confirm the account shown is **Secure Patient Technology** (per the bundled
   `context/tenant-baseline.md`). If not, stop and ask the SE to switch.
2. Tell the SE what you'll visit, then look at, one at a time: Publishing
   calendar (month view), Composer (open, close without saving), Approvals,
   Smart Inbox, Listening (each topic in the SPT group), Reports (the list of
   report names), Trellis (open only, don't ask anything). Take a screenshot of each.
3. For overlay selectors, load the bundled `tools/overlay/overlay-engine.js` into
   the page with the browser JavaScript tool and use `__demoTailor.scan()` and
   `__demoTailor.cssPath()` on each screen, **including Listening and Reports**.
   Never guess selectors. Then call `__demoTailor.revert()`.
4. Save results in the SE's `sprout-demo-runs/_app-map/` folder (make it):
   `tenant-index-ui.md` (same style as the bundled one: report names exactly as
   listed, Trellis availability, calendar campaigns, inbox volume, anything
   belonging to another team) and `app-map.json` (start from the bundled
   `context/click-paths/app-map.json`; replace only what you scanned). Other
   skills use these in place of the bundled copies.
5. Check yourself: every report and screen name you wrote is visible in a
   screenshot you took.
6. Tell the SE, in plain language, what you found and what's new. If it
   generalizes beyond them, suggest sharing the two files with the plugin owner
   (jbaumtana) so everyone gets them.
