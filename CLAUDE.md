# Rules for agents working in this repo

This project automates tailored Sprout Social demos. The workflow is
**plan → approve → execute → verify → roll back**. Follow it every time.

## Hard rules

1. **No plan, no build.** For every new prospect, produce `runs/<run>/plan.md`
   from `schemas/demo-plan.schema.json` first. Do not generate a data pack, a
   script, or touch any tenant until the plan's `approval.approved_by` is filled
   in by a human SE.
2. **Demo tenants only.** Never act on a production tenant or a customer
   account, and never use real customer data. If you can't tell whether a
   tenant is a demo tenant, stop and ask.
3. **No live network activity, with one narrow exception.** Never publish,
   like, comment, follow, or DM on a real social network. The only exception
   is inbox seeding on X: the two fake customer profiles listed in
   `context/tenant-baseline.md` may send messages **only to the demo brand's
   own X profile**, never to or about anyone else, in volumes and wording
   approved in the plan, and each message is logged in the manifest. Until
   Legal answers L3, a person sends them, not an agent.
4. **Sample data stays sample data.** Generated metrics are never presented as
   the prospect's real results, a benchmark, or a promise. Commenters, DM
   senders, and reviewers are invented personas, never real named people.
5. **Every tenant change gets logged.** In Phase 3 and later, write each change
   to `runs/<run>/manifest.json` before making it, so the reset can undo it.
6. **Read the context layer first.** Start from `context/tenant-baseline.md`
   and the matching `context/playbooks/*.md`. Don't make up a Sprout feature,
   screen, or report name. If it isn't in `context/`, ask.

## Where things go

- Reusable, prospect-agnostic knowledge → `context/`
- Anything about one specific prospect → `runs/` (git-ignored)
- If a demo goes well, offer to fold what generalizes into its playbook
  (demo-tailor `industry-playbook` skill).
