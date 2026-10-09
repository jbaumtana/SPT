# Context layer

What a good Sprout demo contains, written down so the agent doesn't have to
improvise. MeshMesh "maps your org" before acting. This folder is that map.

**Rule:** if it's true for every prospect in a vertical, it goes here. If it's
about one prospect, it goes in `runs/`.

| File | Contents | Source to pull from |
| --- | --- | --- |
| [tenant-index.md](tenant-index.md) | **Generated.** Everything the API can read: groups, profiles, tags, topics, teams, queues, recent activity. Refresh with `python3 tools/sprout_api.py index` | The API |
| [tenant-index-ui.md](tenant-index-ui.md) | **From the browser pass.** What the API can't see: report names, Trellis, calendar, approvals, inbox, listening. Selectors in [click-paths/app-map.json](click-paths/app-map.json) | Browser pass |
| [tenant-baseline.md](tenant-baseline.md) | Standard demo tenant: profiles, groups, users, what's pre-seeded | Demo Eng |
| [personas.md](personas.md) | Buyer personas (who's in the room) + in-product users | SE enablement |
| [report-templates.md](report-templates.md) | Reports we show, which pain each one answers | SE enablement |
| [listening-topics.md](listening-topics.md) | Topic query templates by vertical | SE / Listening specialists |
| [click-paths/](click-paths/) | Desired click paths through Sprout, screen by screen | SEs |
| [playbooks/](playbooks/) | One per vertical: vocabulary, story, tenant fit, data patterns, landmines. Start from [`_template.md`](playbooks/_template.md), or ask Claude to "add a playbook for <industry>" (`add-playbook` skill) | Won-deal demos, SEs |

Everything here is plain files in the repo. No Rovo, Confluence, or other
connector is required. To bring in existing material, put it in
[`sources/`](sources/) and ask an agent to fill in the matching file from it.

Items marked `TODO` need a real source. Don't let an agent fill them in from
general knowledge.
