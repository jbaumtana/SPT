# Sprout Demo Automation (SPT)

Turn a prospect brief into a tailored, ready-to-run Sprout demo, with an SE
approving the plan before anything gets built and a clean way to reset afterward.

> **Status:** Phase 0, mapping and discovery. Nothing in this repo touches a
> Sprout tenant yet.

## The pattern (borrowed from MeshMesh)

We're copying MeshMesh's pattern, not its scale:

```
  plan  →  approve  →  execute (watchable)  →  verify  →  roll back
```

| Step | What it means here |
| --- | --- |
| **Plan** | Agent reads the prospect brief and the context layer, then proposes a demo plan |
| **Approve** | SE reviews the plan. Nothing gets generated or loaded without sign-off |
| **Execute** | Agent builds the data pack and script, then loads them (later phases) with a visible trail |
| **Verify** | Every screen in the click path is checked against the plan |
| **Roll back** | Tenant is re-seeded or the overlay is reverted, so the next demo starts clean |

## The building blocks

| # | Block | Where it lives | Phase |
| --- | --- | --- | --- |
| 1 | **Context layer**: tenant baseline, personas, report templates, listening topics, industry playbooks | [`context/`](context/) | 0–1 |
| 2 | **Intake**: prospect brief in, SE-approved demo plan out | [`schemas/`](schemas/), [`examples/`](examples/) | 1 |
| 3 | **Synthetic data generator**: brands, posts, engagement, inbox, sentiment | demo-tailor `demo-data-pack` skill | 1 |
| 4 | **Demo script**: click path and talk track | demo-tailor `demo-narrative` skill | 1 |
| 5 | **Brand kit automation**: logo, colors, voice | TBD | 2 |
| 6 | **Hands**: Sprout APIs/internal tooling, plus browser automation | demo-tailor `demo-overlay` skill + TBD | 3 |
| 7 | **Reset and rollback**: snapshot or re-seed the demo tenant | TBD (depends on Demo Eng) | 3 |

See [docs/architecture.md](docs/architecture.md) for how these fit together.

## First slice

**Prospect brief in → tailored demo data pack + demo script out.**

There's no tenant automation in the first slice. The output is files the SE
loads by hand (or skips). This shows the value without needing API access,
security sign-off, or a tenant reset story. See
[docs/roadmap.md](docs/roadmap.md).

## Building on what's already installed

The `demo-tailor` plugin already provides most of the first slice as skills:

| demo-tailor skill | Role in this project |
| --- | --- |
| `prospect-brief` | Intake: research + structured brief |
| `industry-playbook` | Reads and writes the playbooks in `context/playbooks/` |
| `demo-data-pack` | Synthetic data generator |
| `demo-narrative` | Demo script / run sheet |
| `demo-overlay` | Browser "hands" (overlay-only, revertible, for Phase 3) |

The work in this repo is **Sprout-specific context and the approval gate**. The
plugin is generic. This repo makes it Sprout-native.

## Repo layout

```
CLAUDE.md                 Rules every agent working here follows
context/                  The context layer (what a good Sprout demo contains)
  sources/                Drop-in folder for existing docs (exports, PDFs, notes)
  tenant-baseline.md      Standard demo tenant setup
  personas.md             Buyer and in-product personas
  report-templates.md     Reports we show and why
  listening-topics.md     Listening topic templates
  playbooks/              Healthcare, Public Sector, Travel & Hospitality
schemas/                  Prospect brief + demo plan (the approval artifact)
examples/                 A worked fictional example of each
docs/                     Architecture, roadmap, guardrails, open questions
tools/                    Sprout API client (locked to the tenant in config.json), index, inventory, diff
  overlay/                Overlay engine (fixed copy of demo-tailor's) + browser tests:
                          NODE_PATH=$(npm root -g) node tools/overlay/test_engine.js
skills/                   Plugin skills: tenant-index, add-playbook, demo-plan
.claude-plugin/           Plugin + marketplace manifests
config.json               Which tenant the plugin works on
runs/                     One folder per demo run (git-ignored, may hold prospect info)
```

## Install as a plugin

The repo is also a Claude plugin (`sprout-demo`) and its own marketplace (`spt`).

- **Claude Code:** `/plugin marketplace add jbaumtana/spt`, then `/plugin install sprout-demo@spt`
  (or `/plugin install sprout-demo --marketplace jbaumtana/spt` on 2.1.275+). Opening a clone of
  this repo offers it automatically (`.claude/settings.json`).
- **Claude Desktop / Cowork:** Customize → Plugins → add the `jbaumtana/spt` marketplace.

Always install from GitHub (`jbaumtana/spt`), never from a local folder: a local install copies
everything in the folder, including git-ignored prospect files in `runs/` and any `.env`.

| Skill | Say | Does |
| --- | --- | --- |
| `tenant-index` | "what's in the demo tenant?", "refresh the tenant index" | Reads or regenerates `context/tenant-index.md` from the API |
| `add-playbook` | "add a playbook for retail" | Writes `context/playbooks/<vertical>.md` with a Tenant fit checked against the index |
| `demo-plan` | "plan a demo for <company>" | Brief → plan → stops for SE approval → hands off to demo-tailor |

**Who changes what:** the index is generated, never hand-edited. Industries are
added as playbooks through pull requests. Prospect work stays in `runs/`, which
is never committed. To point the plugin at another tenant, change `config.json`
and refresh the index. Pairs with the `demo-tailor` plugin (research, data
pack, overlay, talk track).

## Getting started

1. Answer the Phase 0 questions in [docs/open-questions.md](docs/open-questions.md)
   (most of them are for Demo Engineering and Security).
2. Fill in `context/`. Drop any existing demo docs (exports, PDFs, copy-paste)
   into [`context/sources/`](context/sources/) and have an agent turn them
   into the context files. No connectors needed.
3. Fill in the demo-tailor `profile/product-profile.md` with Sprout's real
   object names and standard click path.
4. Run a first brief end to end using [examples/](examples/) as a template.
