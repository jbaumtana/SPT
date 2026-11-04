---
name: data-pack
description: Generate and validate the synthetic data for a Sprout demo. Two modes. Industry pack ("build the <vertical> data pack", "refresh the healthcare pack") writes a prospect-neutral pack to context/packs/<vertical>/. Customer pack ("build the data pack for <prospect>", "tailor the pack") derives one from an approved plan into runs/<run>/data-pack/. Use after demo-plan approval, or when an SE wants a reusable vertical pack. Never touches a tenant.
---

# Generate a demo data pack

Generation only. Loading data into the tenant, reset, and the run sheet are
other workstreams ([docs/workstreams/data-generation.md](../../docs/workstreams/data-generation.md)).
The contract is [schemas/demo-data.schema.json](../../schemas/demo-data.schema.json).
The worked example is [context/packs/healthcare/](../../context/packs/healthcare/).

## Before anything

1. Read `CLAUDE.md`, `context/playbooks/<vertical>.md`, `context/personas.md`,
   `context/tenant-baseline.md`, `context/tenant-index.md`, `context/tenant-index-ui.md`.
   If the playbook is missing, stop and offer `add-playbook`. Never fill a gap
   from general knowledge: leave TODO and tell the SE.
2. **Customer mode only:** open `runs/<run>/plan.md`. If `approval.approved_by`
   is empty, stop. No plan, no build.

## Industry mode

1. Start from the playbook's vocabulary, content pillars, inbox scenarios and landmines.
2. Write `context/packs/<vertical>/demo-data.json` to the schema:
   - **Posts:** all evergreen. No dates, years, percentages, outcome claims, real organizations, or private details. Seasonal copy goes in `seasonalLibrary`, not `posts`. Cover every content pillar, and keep captions inside each network's limit.
   - **Campaigns:** each one `replaces` the seed labels it should cover from `tenant-index-ui.md`, mapped to the story, not alphabetically (D2). Use a `tenantTagId` only from `tenant-index.md`, never `4162648`.
   - **Inbox:** only the seeding personas in `tenant-baseline.md`, and only their handles. Include the playbook's scenarios, a negative cluster, and one wrong-channel private-details message whose route is `route-offline`. Declare the sentiment mix in `meta` and match it.
   - **Approvals:** one pending post, and the workflow must include a compliance step.
   - **Users:** invented, `isFictional: true`, stable across packs.
   - `reportFraming`: names from `tenant-index-ui.md` only, with framing and **no numbers**.
   - `relabels` and `outOfClickPath`: every seed label either has a rule or is listed as deliberately left alone.
3. Run both:
   ```bash
   python3 tools/overlay_payload.py build context/packs/<vertical>/demo-data.json
   python3 tools/check_pack.py context/packs/<vertical>/demo-data.json
   ```
   Fix every error. Don't edit the validator or `blocklist.txt` to get green.
4. Add or update `context/packs/<vertical>/README.md` (what's in it, last
   generated, what's TODO) and show the SE a summary. Commit.

## Customer mode

Build on the industry pack, don't regenerate it.

1. Copy `context/packs/<vertical>/demo-data.json` to `runs/<run>/data-pack/demo-data.json`.
   Set `meta.track: "customer"`, `basedOnPack`, `prospect`, `planPath`.
2. Apply only what the approved plan names: `relabels` for brand, handle, topic and
   team names; pick items from `seasonalLibrary`, move them into `posts`, and set
   `pinDate` plus `dateSensitive: true`; adjust campaign names and the inbox
   scenarios to the prospect's discovery pains.
3. The prospect's name may appear in overlay relabels, drafts, approvals and DMs
   between our own accounts. **It never appears in a post with `visibility: "public"`**
   (CLAUDE.md rule 3), and `allowPublic` stays false unless the plan lists live posting.
4. Validate with the prospect name:
   ```bash
   python3 tools/overlay_payload.py build runs/<run>/data-pack/demo-data.json
   python3 tools/check_pack.py runs/<run>/data-pack/demo-data.json --prospect "<Prospect>"
   ```
5. Hand off. Anything that writes to the tenant is the Hands step and is logged
   to `manifest.json` first. Generated metrics are never described as the
   prospect's real results, a benchmark, or a promise.

## Saving what worked

If a customer pack goes well, offer the generalizable parts (a better scenario,
a campaign mapping) as a diff to the industry pack, with the prospect stripped.
