# Rules for agents working in this repo

This project automates tailored Sprout Social demos. The workflow is
**plan → approve → execute → verify → roll back**. Follow it every time.

## Hard rules

1. **No plan, no build.** For every new prospect, produce `runs/<run>/plan.md`
   from `schemas/demo-plan.schema.json` first. Do not generate a data pack, a
   script, or touch any tenant until the plan's `approval.approved_by` is filled
   in by a human SE.
2. **The sandbox tenant only.** The demo tenant runs on **production
   Sprout** and is used as a sandbox, and there's no technical guard (S4). So
   the guard is you: before any action, check that the tenant name and
   customer ID shown in the app or API match the ones in
   `context/tenant-baseline.md`. If they don't, or you can't tell, stop and
   ask. The SE's login may reach other tenants. Never act in them. Never use
   real customer data. The first tenant is **shared**: confirm the SE has
   reserved it before any tenant write.
3. **No live network activity, with one narrow exception.** Never publish,
   like, comment, follow, or DM on a real social network. In the Sprout app,
   that means never clicking Send, Publish, Post now, or an approval that
   releases a post. Leave drafts as drafts. Don't change settings, users, or
   connected profiles either. The only exception
   is inbox seeding on X: the two fake customer profiles listed in
   `context/tenant-baseline.md` may send messages **only to the demo brand's
   own X profile**, never to or about anyone else, in volumes and wording
   approved in the plan, and each message is logged in the manifest. These
   messages are permanent in Sprout (D8), so they must be prospect-neutral,
   seeded once per vertical and reused. Legal has
   cleared this (L3), so an agent may send them through the browser.
4. **Sample data stays sample data.** No on-screen disclaimer is needed
   (L2), so turn the overlay watermark off. But generated metrics are still
   never described as the prospect's real results, a benchmark, or a promise. Commenters, DM
   senders, and reviewers are invented personas, never real named people.
5. **API writes are permanent.** The Sprout API can't update or delete. Only
   write to the demo customer ID, never put a prospect's name in an API write
   (use the overlay), scheduled drafts are fine (they stay
   drafts, D9), and log every `publishing_post_id` returned (one per
   profile per time, because of fan-out). See `docs/api-coverage.md`.
6. **Every tenant change gets logged.** In Phase 3 and later, write each change
   to `runs/<run>/manifest.json` before making it, so the reset can undo it.
7. **Read the context layer first.** Start from `context/tenant-baseline.md`
   and the matching `context/playbooks/*.md`. Don't make up a Sprout feature,
   screen, or report name. If it isn't in `context/`, ask.

## Where things go

- Reusable, prospect-agnostic knowledge → `context/`
- Anything about one specific prospect → `runs/` (git-ignored)
- If a demo goes well, offer to fold what generalizes into its playbook
  (demo-tailor `industry-playbook` skill).
