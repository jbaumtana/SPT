---
name: demo-plan
description: Plan a tailored Sprout demo for a prospect on the shared demo tenant, with an SE approval gate before anything is built. Use when an SE says "plan a demo for <company>", "prep a Sprout demo for <prospect>", "start a demo run", "build the demo plan", or "get me ready for my <company> demo". This is the starting point; it hands off to demo-overlay after approval.
---

# Plan a Sprout demo

The user is a Sprout SE, not a developer. Never show file paths, commands, JSON
or code in what you say to them. Talk about screens, profiles, and what they
will see. Do the file work quietly.

## Ground rules (always)
- **No plan, no build.** Nothing is prepared until the SE approves the plan in
  their own words. Never fill in the approval yourself. Any later change to the
  plan clears the approval.
- **Sandbox tenant only** (Secure Patient Technology). It is shared. Never use
  real customer data. Confirm the SE has reserved it before touching anything.
- **Default is look-only:** the demo changes what's on screen (overlay), not the
  tenant. No posts, likes, replies, follows, DMs, or settings changes.
- **Prospect names stay off anything public.** Fine in overlay and drafts;
  never in a published post.
- Numbers are sample data, never the prospect's results, a benchmark, or a promise.
- Use only screens, profiles, tags and topics that appear in the bundled
  tenant notes. Don't invent a Sprout feature or report name; if unsure, ask.
  The full rules are in the bundled `CLAUDE.md`.

## Where things live
- **Bundled notes (read-only):** the plugin's `context/` folder (tenant index,
  baseline, playbooks, click paths) and `CLAUDE.md`.
- **The SE's work:** a folder named `sprout-demo-runs` in the folder the SE
  gave you access to. Make it if missing. Each demo gets
  `sprout-demo-runs/<YYYY-MM-DD>-<company>/`. Keep prospect info only there.
  If the SE hasn't shared a folder, ask them to pick one first.

## Steps
1. **Read** the tenant index, tenant baseline, and the playbook for the
   prospect's industry (if none exists, say so and use the closest).
2. **Ask in one round** (AskUserQuestion): exact company, demo date and length,
   who's attending, what discovery said about their pain. "Nothing yet" is fine.
3. **Research** the prospect with web search, with sources. Mark every
   inferred pain as an inference.
4. **Write the plan** in the run folder as `plan.md`, following
   `examples/demo-plan.example.md`: story, screens (each tied to one pain, with
   minutes), profiles and tags to show, risks, open items. Leave
   **Approved by** blank.
5. **Stop and show the plan** in plain language. Ask the SE to approve or edit.
6. **After approval,** offer the next step: the `demo-overlay` skill (builds the
   on-screen branding and the run sheet). The Sprout API is optional and
   usually not available in Cowork; skip any API step if there is no token.
