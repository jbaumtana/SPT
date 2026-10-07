# runs/

One folder per demo, named `YYYY-MM-DD-<prospect-slug>/`. Contents are
git-ignored because they hold prospect info from discovery.

```
2026-10-14-bayline-health/
  brief.yaml          Intake (matches schemas/prospect-brief.schema.json)
  plan.md             Demo plan, with the SE's approval line filled in
  data-pack/          Output of demo-data-pack (JSON, CSV, paste-ready)
  run-sheet.md        Output of demo-narrative
  manifest.json       Phase 3+: every change made to a tenant, so it can be reverted
```

The plan's approval line is the gate. No agent builds `data-pack/` until it is
filled in.
