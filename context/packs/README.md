# Industry data packs

Prospect-neutral, committed, reusable. One folder per vertical. Customer packs
derive from these and live in `runs/` (git-ignored). Workflow:
[skills/data-pack/SKILL.md](../../skills/data-pack/SKILL.md). Contract:
[schemas/demo-data.schema.json](../../schemas/demo-data.schema.json).

| Pack | Status |
| --- | --- |
| [healthcare](healthcare/) | v1, validated 2026-11-04 |
| public-sector | not started |
| travel-hospitality | not started |

`blocklist.txt` lists real organizations that must never appear. Extend it, don't trim it.

Validate any pack: `python3 tools/check_pack.py context/packs/<vertical>/demo-data.json`
