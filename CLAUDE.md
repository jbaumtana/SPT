# Rules for agents working in this repo

This project automates tailored Sprout Social demos. The workflow is
**plan → approve → execute → verify → roll back**. Follow it every time.

## Hard rules

1. **No plan, no build.** For every new prospect, produce `runs/<run>/plan.md`
   from `schemas/demo-plan.schema.json` first. Do not generate a data pack, a
   script, or touch any tenant until the plan's `approval.approved_by` is filled
   in by a human SE.
2. **The sandbox tenant only.** The demo tenant runs on production Sprout and
   is used as a sandbox. The browser session only reaches the tenant the SE is
   logged into (S4), so at the start of each session confirm it's the tenant
   named in `context/tenant-baseline.md`. If it isn't, stop and ask. Never use
   real customer data. The first tenant is **shared**: confirm the SE has
   reserved it before any tenant write.
3. **Live activity only between accounts we own.** The agent may act in the
   browser as the SE, including publishing, but only:
   - from the demo tenant's own profiles, or the seeding personas (two on X,
     one on Instagram) listed in `context/tenant-baseline.md`
   - with content and volume approved in the plan, each item logged in the
     manifest
   - never liking, replying to, following, mentioning, or DMing an account we
     don't own, and never changing settings, users, or connected profiles

   **Where the prospect's name can go:** drafts, scheduled drafts, approvals,
   and DMs between our own accounts are fine, since none of them is public.
   **Publicly published posts stay prospect-neutral:** no prospect name, logo,
   or look-alike copy. A public post in a real company's name, on an account
   that isn't theirs, reads as impersonation and breaks the networks'
   impersonation rules. Use drafts or the overlay to show the prospect's
   content instead.
4. **Sample data stays sample data.** No on-screen disclaimer is needed
   (L2), so turn the overlay watermark off. But generated metrics are still
   never described as the prospect's real results, a benchmark, or a promise. Commenters, DM
   senders, and reviewers are invented personas, never real named people.
5. **API writes are permanent.** The Sprout API can't update or delete. Only
   write to the demo customer ID. Prospect names are fine in drafts, but in a
   shared tenant they stay for everyone to see, so tag them with the run ID and
   clear them in the browser afterward. Scheduled drafts are fine (they stay
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
