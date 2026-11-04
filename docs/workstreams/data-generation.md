# Workstream: Synthetic data generation

Block 3 of the [architecture](../architecture.md). This page carves it out so
it can be planned, staffed and tested on its own. It covers only **making the
fake data**. Loading it into a tenant, resetting the tenant, and the demo
script are separate workstreams (see [Boundaries](#boundaries)).

## What it produces

Two tracks, one generator, different homes and different rules.

| | **Track A: Industry packs** | **Track B: Customer packs** |
| --- | --- | --- |
| Use | Reusable base for a vertical (Healthcare, Public Sector, Travel & Hospitality first) | One prospect's demo, built on the matching Track A pack |
| Prospect names | **Never.** Prospect-neutral | Allowed in overlay, drafts and approvals; **never in anything publicly published** (CLAUDE.md rule 3) |
| Lives in | `context/playbooks/<vertical>.md` (patterns) and `context/packs/<vertical>/` (generated, committed) | `runs/<run>/data-pack/` (git-ignored) |
| Can reach the tenant | Yes, as a seeded draft set or inbox set, logged in the manifest | Mostly overlay (nothing written). Drafts only when the plan says so, tagged with the run ID |
| Trigger | SE asks for a vertical pack, or a won demo generalizes | An approved `plan.md` (CLAUDE.md rule 1) |

`context/packs/` doesn't exist yet. It is the one new directory this workstream
proposes.

## Contents of a pack

From `data_to_generate` in `schemas/demo-plan.schema.json`:

- Brands and profiles (labels, handles, monogram/avatar)
- Posts (captions, content pillars, `pinDate`, `dateSensitive`)
- Campaigns (with `replaces` seed labels)
- Inbox messages and DMs (invented personas only, sentiment mix)
- Listening topics
- Report framing (what the overlay says; real report history can't be seeded, open-questions D6)
- `relabels` and `outOfClickPath` for the overlay

Outputs: `demo-data.json` (the source of truth), CSV/paste-ready views, and
`overlay-payload.json` built from it by `tools/overlay_payload.py`.

## Inputs

1. Approved `plan.md` (Track B) or a vertical name (Track A)
2. `context/playbooks/<vertical>.md`: vocabulary, content pillars, inbox scenarios, landmines
3. `context/personas.md`: the invented commenters and DM senders
4. `context/tenant-index.md`, `context/tenant-index-ui.md`: real labels that every rule must cover
5. `context/click-paths/app-map.json`: selectors
6. Brand kit (Phase 2, TBD): logo, colors, voice samples

## Current state

| Piece | Status |
| --- | --- |
| Playbooks | 3 exist (healthcare, public-sector, travel-hospitality); template and `add-playbook` skill exist. Status: starting hypotheses |
| Plan schema (`data_to_generate`) | Exists; counts and names only, no per-item shape |
| `demo-data.json` schema | **Missing.** `overlay_payload.py` reads fields "beyond the data-pack schema", but that schema lives in the external demo-tailor plugin, not this repo |
| Generator | **Not in this repo.** Lives in the demo-tailor `demo-data-pack` skill. Last run was BCBSA, hand-fixed afterwards |
| Overlay payload build and check (D1–D4, D6) | Done, with tests |
| D5 (neutral thumbnails) | Not started |
| BCBSA comparison against the hand-fixed payload | Not done; that file isn't in the repo |
| Track A packs | None generated |

## Gaps to close (proposed order)

1. **Vendor the `demo-data.json` schema** into `schemas/demo-data.schema.json`, derived from what `overlay_payload.py` reads. Everything else validates against it. This is the contract between generation and the rest of the system.
2. **Decide where the generator lives.** Keep calling demo-tailor `demo-data-pack`, or bring a Sprout-specific `skills/data-pack/` into this repo. Recommendation: bring it in, because the Sprout rules (no public prospect names, no real people, tenant labels) are hard-coded policy, not preferences.
3. **Add a pack validator** (`tools/check_pack.py`): schema, no real names, no prospect name in anything marked public, every tenant label covered, sentiment mix matches the plan, counts match `data_to_generate`.
4. **Generate Track A packs** for the three verticals, prospect-neutral, validated.
5. **Track B as a diff on Track A**: customer pack = vertical pack + relabels + pinned copy, so a new prospect is a small change, not a regeneration.
6. **D5** (optional neutral images) and the BCBSA regression comparison.

**Exit test:** for each of the three verticals, generate a Track A pack, derive a Track B pack from a sample brief, pass the validator with zero manual edits, and build an overlay payload that passes `check`.

## Rules this workstream must keep

From [CLAUDE.md](../../CLAUDE.md) and [guardrails.md](../guardrails.md):

- No plan, no build (rule 1). Track B generation starts only after `approval.approved_by` is filled in.
- Public posts are prospect-neutral (rule 3). The validator should fail any item marked `public` that contains the prospect name, logo or look-alike copy.
- Sample data stays sample data (rule 4). Metrics are never described as the prospect's real results, a benchmark, or a promise. Commenters, senders and reviewers are invented.
- Reports and ROI numbers are never generated as fact (architecture: Business Value pillar uses sourced numbers only).
- No made-up Sprout features, screens or report names (rule 7). Use only what's in `context/`.
- Generation itself touches no tenant. Anything that writes is the Hands workstream and gets logged first (rule 6).

## Boundaries

| Stays out of this workstream | Owner |
| --- | --- |
| Writing to the tenant (drafts, inbox seeding, publishing) | Hands (block 6, Phase 3) |
| Reset, rollback, manifest | Reset (block 7) |
| Run sheet and talk track | Demo script (block 4) |
| Logo and color extraction | Brand kit (block 5, Phase 2); this workstream only consumes it |
| Overlay engine and selectors | `tools/overlay/` and the browser pass; this workstream only emits the payload |

## Open questions for you

- Should Track A packs be committed (reusable, shared) or stay local like `runs/`? Proposed: committed, since they're prospect-neutral.
- Bring the generator into this repo (recommended) or keep depending on demo-tailor?
- Which vertical first? Healthcare has the most real-run history (BCBSA).
