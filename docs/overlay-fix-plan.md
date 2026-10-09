# Overlay fix plan, from the BCBSA pre-flight (2026-10-09)

The BCBSA test run found problems the headless test missed. Part of the cause is that the test page was built from selectors, so it had none of Sprout's real structure, such as captions split into several pieces. This plan groups the fixes by where they belong in the code. Each fix comes with a test, so the same problem can't pass again.

## Paste this into the local session

> Read CLAUDE.md, docs/overlay-fix-plan.md, and runs/2026-10-08-bcbsa/preflight.md. Work through the plan in phase order, one commit per phase, tests first. Don't change the tenant.

---

## Phase 1: Engine (`overlay-engine.js`)

**Status: E1–E7 done (2026-10-09).** The engine now lives at `tools/overlay/overlay-engine.js` (v1.1.0-spt), with tests in `tools/overlay/test_engine.js`. Synthetic fixtures for now; S3 swaps in real-page copies.

| # | Problem seen | Fix | Test |
|---|---|---|---|
| E1 | **Old names came back.** React rewrote the topic page title in place, and "Healthcare Tech Industry" returned because the observer only watches for added and removed elements. | Also watch for in-place text changes (`characterData: true`) and re-run the text rules on just that text. Pause watching while the engine writes, so it doesn't trigger itself. | Fixture: change a text node's value after `apply()` and check the replacement holds. |
| E2 | **`wholeWord` broke on names ending in punctuation.** `\b` needs a letter or digit on the other side, so "Compliance Approval [MF]" followed by "-" never matched. | Replace `\b` with lookarounds, `(?<![\p{L}\p{N}_])` and `(?![\p{L}\p{N}_])` with the `u` flag, so the check works whatever the find string starts or ends with. | Unit test: `[MF]-`, `@handle,`, `#tag.`, and a name at the start or end of a text node. |
| E3 | **Captions shifted when the page redrew.** Values are assigned in page order through a counter, so a redraw moves every caption, and duplicate posts get different captions. | Add a stable-key option (`keyAttr`): take an attribute from the post's container, such as `data-id` or `data-qa-msg`, hash it, and use the hash to pick the value. The same post then always gets the same caption, and its X and Instagram copies can share one. | Fixture: apply, redraw the list in a different order, and check each post keeps its caption. |
| E4 | **Captions couldn't be tied to a date.** Pinning a date needed a hand-written `:not()` chain of selectors. | Add `scope` to selector rules, for example `{"scope": "[data-qa-date='10/15/2026']"}`, and give scoped rules priority over general ones. A matched element is then skipped by later rules (claimed once), instead of the current per-rule `markSeen`. | Fixture: a scoped rule and a general rule cover the same element, and the scoped value wins. |
| E5 | **Applying twice added to the undo log**, recording the CSS variables twice. | Make `apply()` revert first, or skip what's already recorded, so applying twice equals applying once. | Apply twice, revert once, and check the page matches the original exactly. |
| E6 | **No built-in leftover check.** Pre-flight needed hand-written JavaScript. | Add `audit({deny: [...], patterns: [...]})`. It returns visible leftover matches with each one's selector, using the same visibility rules as `scan()`. | Unit test against a fixture that contains seed strings. |
| E7 | **The page-side hotfix (`__bcbsaCD`) isn't cleaned up by `revert()`.** | E1 makes the hotfix unnecessary. `revert()` should disconnect every observer the engine owns. | Revert, mutate the page, and check nothing re-applies. |

## Phase 2: Selectors and the browser pass (`app-map.json`, `docs/browser-pass.md`)

| # | Problem seen | Fix |
|---|---|---|
| S1 | **The caption selector matched pieces of captions, not whole captions** (291 pieces across 66 posts). Hashtags and links are separate pieces, so the old SPT hashtags and links stayed on screen. | Record the selector for the **whole caption** (`span[data-qa-message-text]`) and record what's inside it (text, hashtag and link pieces). Add a field marking each selector as replacing the whole caption or one piece. |
| S2 | **Hashed class names break when Sprout ships a release.** | Prefer Sprout's own `data-qa-*` attributes. On the calendar these are `#publishing_calendar`, `[data-qa-date]`, `[data-qa-msg]` and `span[data-qa-message-text]`. Update the browser pass to check for `data-qa-*` and `id` first and fall back to hashed classes only when there's nothing else. Approvals and the Composer still need a re-scan for stable attributes. |
| S3 | **The selector test proved nothing**, because it ran on a page built from the selectors themselves. | During the browser pass, save a cleaned copy of the real page code for each screen: replace the text with lorem ipsum, keep the structure. Save these to `context/click-paths/fixtures/`. All engine and payload tests run against these copies. |
| S4 | **No map existed for the author line or post images.** | Add selectors for the approval author name and avatar, calendar and approval thumbnails, and the topic page title. |

## Phase 3: Data-pack generator (`demo-data-pack`)

| # | Problem seen | Fix |
|---|---|---|
| D1 | **Date-specific copy landed on the wrong day** ("Medicare Annual Enrollment starts today" on Oct 14 and on a Sep 19 approval). | Give each post `pinDate` and `dateSensitive: true/false`. Captions with a pinned date become scoped rules (E4). Date-sensitive captions are **never** put in a rotating list, and the approval rules never get them. |
| D2 | **The approval card's labels didn't match the story.** The CMS draft showed the campaign "Open Enrollment 2027" because "Patient Portal Launch" was mapped to it. | Map each label to its story: the approval card gets "Policy Explainers". Generate the label rules from `demo-data.json`, not by hand. |
| D3 | **The author line showed real tenant users**, not Dev Malhotra. | Relabel the author line by selector (S4) using the invented personas. Never write real user names as text rules, so the browser-pass "no real names in the repo" rule still holds. |
| D4 | **Some seed labels had no rule.** "Tech - FAQ" was patched in by hand. | Coverage check: every campaign, workflow, topic and handle string in `context/tenant-index-ui.md` must have a rule, or be listed as intentionally out of the click path. |
| D5 | **Off-message images**: SPT security graphics, a "15%" infographic, and a patient in a hospital bed next to a payer statement. | Optional rules that swap calendar and approval thumbnails for generated neutral images, matching the generated monogram, or hide the image on the approval card. These are off by default and switched on per run in `plan.md`. |
| D6 | **The emitted payload had no validation.** | Run `validate-payload` before writing: escape HTML in `html` values; reject rules where a shorter find string would match inside a longer one listed later (the "Coffee" before "Northwind Coffee" problem); flag `wholeWord` on find strings that end in punctuation (until E2 lands); and run the D1 checks. |

## Phase 4: Pre-flight automation (`tools/preflight` or a skill step)

| # | Fix |
|---|---|
| P1 | Write a script for each screen in the click path: go to the screen, `apply()`, `audit()` (E6), check that each card shows exactly one caption, save a screenshot, and print a pass/fail table to `runs/<id>/preflight.md`. This is the table I produced by hand, generated instead. |
| P2 | Deny list for each run: tenant seed names, real organizations from `tenant-index-ui.md` (NPAF, WIRED, ViVE, Fortune), `bit.ly`, `#` hashtags, `[Action`, landmine words from `brief.yaml`, and the Cases queue names. |
| P3 | Tenant checks to read from the browser pass or the API before writing the plan: disconnected profiles (LinkedIn), a topic's saved date range, and pop-ups waiting to show (the Listening "Feature update"). The plan generator should route around a disconnected network rather than add a "reconnect by hand" note. |
| P4 | Trellis check: run the prompt, then test the answer against the deny list, real company names and landmines, and return go or skip. Record that the chat now sits in Trellis history. |

## Not code: decisions or manual steps

- Reconnect LinkedIn in the tenant (or lead with X and Instagram). The approval card and Profile Performance both depend on it.
- Report numbers are small (386 impressions in September). Either accept "demo account" framing or pick a different report.
- Trellis answers come from the tenant's real listening data. Decide whether Trellis stays in healthcare-payer demos; the BCBSA answer was about providers.
- Clean up other teams' material: the Credit Unions topic, test reports, the "Life, Illuminated" approval, and the Cases queues.

## Order and size

1. **Phase 1, E1–E5** (engine; about half a day). Everything else depends on it.
2. **S1–S3** (selectors and real-page test copies; one browser pass). Needs a local session with Chrome.
3. **D1–D4 and D6** (generator and validation). Re-run the BCBSA data pack and check the result matches my hand-fixed payload in `runs/2026-10-08-bcbsa/data-pack/overlay-payload.json`.
4. **E6 and P1–P2** (automated pre-flight). Then re-run the BCBSA pre-flight from scratch as the acceptance test: zero leftovers and one caption per card on all 4 screens.
5. **D5, S4, P3 and P4** when there's time.
