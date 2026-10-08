# Roadmap

Each phase has an exit test. Don't start the next phase until the current one
passes.

## Phase 0: Map and discover (≈1 week)
- [ ] Answer [open-questions.md](open-questions.md) with Demo Engineering
- [x] Security/IT and Legal questions answered
- [ ] Collect existing demo assets into `context/sources/` (exports, PDFs, or copy-paste)
- [ ] Fill in demo-tailor `profile/product-profile.md` with Sprout's real terms and click path

**Exit:** we know what's automatable via API, what isn't, and who signs off.

## Phase 1: Brief → data pack + script (≈2–3 weeks)
- [ ] Fill in `context/` (baseline, personas, reports, listening, 3 playbooks)
- [ ] Lock the brief and plan schemas after trying them on 2 real (past) deals
- [ ] Run end to end for Healthcare, Public Sector, Travel & Hospitality
- [ ] Have 2–3 SEs use it on live deals. Collect time saved and what they edited

**Exit:** SEs choose to use it, and plan approval takes under 10 minutes.

## Phase 2: Brand kit (≈1 week)
- [ ] Pull the prospect's logo, colors, and voice samples from public sources
- [ ] Feed into the data pack (avatars, brand colors, caption voice)
- [x] Confirm the logo-usage policy with Legal/Brand (L1: allowed)

**Exit:** the pack looks like the prospect's without manual asset hunting.

## Phase 3: Hands + reset (≈3–4 weeks, built from scratch, since no tooling exists)
- [ ] Overlay route: map Sprout demo screens into `app-map.json`, test revert
- [ ] Thin API client, locked to the demo customer ID
- [ ] Seed one reusable draft set per vertical (no prospect names), with every write logged to `manifest.json`
- [ ] Shared-tenant reservation (calendar or Slack) before any tenant write
- [ ] Seed one prospect-neutral inbox set per vertical from the seeding personas: two on X, one on Instagram with two accounts (permanent in Sprout, D8)
- [ ] Reset: mark seeded items Complete, browser cleanup of drafts, before/after inventory diff ([tenant-snapshots.md](tenant-snapshots.md))
- [ ] Inbox seeding on X from the two fake profiles (cleared by Legal, L3)
- [ ] Verify step: walk the click path, screenshot each screen, diff against the plan

**Exit:** load → demo → reset three times in a row on one tenant, no leftovers.

## Phase 4: Extend
- [ ] Business Value: ROI model from the same brief (sourced numbers only)
- [ ] Customer risk: read-only "diagnose" scan against the tenant baseline
