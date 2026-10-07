# Sprout API coverage

**What we know:** the Sprout public API is mostly **read**. The only **write**
is creating drafts (plus uploading media for them). **There is no delete**,
and no update.

**Source:** the official docs at <https://api.sproutsocial.com/docs/> (not yet
read directly: the agent sandbox blocks that domain) and the open-source
[kodowjam/sprout-social-mcp-server](https://github.com/kodowjam/sprout-social-mcp-server)
(commit `9a5459f`, Sep 2026). That repo wraps 11 calls. The official API may
have more read endpoints (for example inbox messages or listening). Confirm
those against the docs before planning around them.

## Endpoints confirmed in the MCP server

Base URL `https://api.sproutsocial.com`, `Authorization: Bearer <token>`.
`{cid}` is the customer ID.

| Area | Method + path | R/W | What it gives us |
| --- | --- | --- | --- |
| Account | `GET /v1/metadata/client` | R | Customer ID(s) for the token |
| Account | `GET /v1/{cid}/metadata/customer` | R | Connected profiles: IDs, network, group IDs |
| Account | `GET /v1/{cid}/metadata/customer/tags` | R | Tags |
| Account | `GET /v1/{cid}/metadata/customer/users` | R | Users |
| Publishing | `POST /v1/{cid}/publishing/posts` | **W** | Create a **draft** post (see below) |
| Publishing | `GET /v1/{cid}/publishing/posts/{id}` | R | One post by ID. No "list drafts" call is used |
| Media | `POST /v1/{cid}/media/` | **W** | Upload image/video (by URL or multipart, 50 MB max in the wrapper). Expires in 24 h unless attached to a post |
| Analytics | `POST /v1/{cid}/analytics/profiles` | R | Profile metrics over a date range |
| Analytics | `POST /v1/{cid}/analytics/posts` | R | Per-post metrics. 50 per page |

The wrapper throttles to **60 requests/minute** and retries on 429/5xx. Treat
that as the working rate limit until the docs confirm it.

### The draft-create body

```json
{
  "is_draft": true,
  "customer_profile_ids": ["<profile id>", "..."],
  "text": "Post copy",
  "group_id": 123,
  "delivery": { "type": "SCHEDULED", "scheduled_times": ["2026-10-20T14:00:00Z"] },
  "media": [{ "media_id": "<from /media>", "media_type": "PHOTO" }],
  "tag_ids": [42]
}
```

## ⚠️ Risk: scheduled drafts may publish for real

The MCP server's own docs say: *"Posts are created as drafts. Whether scheduled
drafts auto-publish depends on your Sprout account's approval workflow
settings."* The demo tenant's profiles are real network accounts, so a
scheduled draft could go live on a real network, and **we can't delete it via
the API.**

Until this is tested on a throwaway profile:
- Never send `delivery` (no `scheduled_at`). Create unscheduled drafts only.
- Check the demo tenant's approval workflow so nothing publishes without a person approving it.

(Tracked as D9 in [open-questions.md](open-questions.md).)

## What this means for each building block

| Block | API can do | Everything else |
| --- | --- | --- |
| Synthetic posts in composer/calendar | ✅ Create drafts, with media and tags | Can't edit or remove them via API |
| Inbox messages | ❌ No write | The two fake X profiles (CLAUDE.md rule 3) or overlay |
| Listening topics | ❌ No write | Set up once by hand, overlay prospect names |
| Reports / analytics | ✅ Read only | History comes from real activity. Overlay for prospect-specific numbers |
| Tags | Read only | Create the tags we need once, by hand |
| Users, profiles, groups | Read only | Set up once by hand (tenant baseline) |
| Reset | ❌ No delete | Browser automation or by hand. See below |
| **"Diagnose" mode (customer-risk pillar)** | ✅ Profiles, users, tags, and analytics are all readable | Good fit: it's read-only by design |

## The strategy this forces: seed per vertical, overlay per prospect

With no delete, every API write is permanent unless someone removes it in the
UI. So:

1. **Never write a prospect's name to the tenant.** Prospect names, logos,
   and handles go on via the overlay only. That removes most of the need to
   reset, and the confidentiality risk with it.
2. **Seed a reusable draft set once per vertical.** For example, about 40
   Healthcare drafts written in the playbook's voice with no company name.
   Tag them with a fixed vertical tag (created by hand, since the API can't
   create tags). Every Healthcare demo reuses them, and the overlay makes
   them look like the prospect's.
3. **Log every API write in `manifest.json`** (the returned post ID, run,
   and tag). `GET /publishing/posts/{id}` lets us check what's still there,
   because there's no list call.
4. **Cleanup is a browser-automation task (or a person's).** If a draft does
   need removing, the agent opens the post in the Sprout UI and deletes it,
   with the SE watching and the manifest as the checklist.

## Using the MCP server itself

It's a handy reference, but don't connect it to a Sprout token as-is:
- It's a single-maintainer third-party package. Pin a reviewed version, or
  write our own thin client (we only need about 6 calls).
- It has no guard against a non-demo account. Any client we use should refuse
  every customer ID except the demo tenant's, and refuse `delivery` until D9
  is answered.
- The API token is a Security question (S2): who issues it, how it's scoped,
  where it's stored.
