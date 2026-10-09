# Sprout API coverage

**Bottom line:** the Sprout public API is **read-only except for creating
draft posts and uploading media for them.** It can't update or delete
anything, and it can't create inbox messages, listening topics, tags, users,
or reports.

**Our split (decided 2026-10-08):** the API is for reads and for creating
drafts and their media. These are **browser only**, even if the API ever
gains a way to do them:
- **Reddit:** the API doesn't return the Reddit profiles anyway
- **Deletions:** drafts, posts, seeded messages, anything
- **Publishing:** posting live or releasing a scheduled draft

**Source:** the official docs (<https://api.sproutsocial.com/docs/>), saved as
text in [`context/sources/sprout-api-docs-2026-10.txt`](../context/sources/sprout-api-docs-2026-10.txt).
The open-source [kodowjam/sprout-social-mcp-server](https://github.com/kodowjam/sprout-social-mcp-server)
wraps 11 of the 20 endpoints and matches the docs.

## Access, auth, limits

- **Plan:** API access depends on the account's plan. ✅ The demo account has it (D11). The user setting it up needs the *API Permissions* permission and must accept the Analytics API Terms (Settings → Global Features → API).
- **Auth:** OAuth 2.0 machine-to-machine (recommended: short-lived JWTs from client ID + secret) or a long-lived API token. Both are sent as `Authorization: Bearer …`.
- **In this repo's cloud environment:** the proxy adds the credential to every request to `*.sproutsocial.com`, so plain `curl` works with no header. ✅ Verified 2026-10-08: all seven metadata reads and `POST /messages` return 200, and the token only sees customer `2160354`.
- **Rate limits:** **60 requests/minute, 250,000/month.**
- **X data:** ✅ done for the demo account (D10). In general, the account has to accept Sprout's X Content EULA *and* pass a short X review before X data comes back through the API. X isn't available in Listening at all.
- **Messages filters:** `group_id.eq(…)` is required, times take no trailing `Z` (`created_time.in(2026-10-01T00:00:00..2026-10-08T00:00:00)`), and a Yelp profile in `customer_profile_id` fails the request (`not a supported type`).
- **Cases filters:** each date range covers one week at most. Results are tenant-wide (both brands), keyed by `id`.
- **Messages `fields`:** one unknown field fails the whole request with `400 Requested invalid fields`. `sentiment` is a Listening field, not an inbox one. Working set: `created_time`, `post_type`, `from.guid`, `from.name`, `from.screen_name`, `customer_profile_id`.
- **Excluded data:** paid/ads data, Yelp/Trustpilot/TripAdvisor/Glassdoor reviews, and Reddit listening messages. Google Business data is limited to the last 30 days.

## All endpoints

`{cid}` = customer ID. Base URL `https://api.sproutsocial.com`.

| Area | Endpoint | R/W | Use for us |
| --- | --- | --- | --- |
| Metadata | `GET /v1/metadata/client` | R | Find the demo customer ID |
| Metadata | `GET /v1/{cid}/metadata/customer` | R | Profiles (IDs, network, group) |
| Metadata | `GET /v1/{cid}/metadata/customer/tags` | R | Tags (active + archived) |
| Metadata | `GET /v1/{cid}/metadata/customer/groups` | R | Groups |
| Metadata | `GET /v1/{cid}/metadata/customer/users` | R | Users |
| Metadata | `GET /v1/{cid}/metadata/customer/topics` | R | Listening topics |
| Metadata | `GET /v1/{cid}/metadata/customer/teams` | R | Teams |
| Metadata | `GET /v1/{cid}/metadata/customer/queues` | R | Case queues |
| Analytics | `POST /v1/{cid}/analytics/profiles` | R | Profile metrics |
| Analytics | `POST /v1/{cid}/analytics/posts` | R | Post metrics |
| Inbox | `POST /v1/{cid}/messages` | R | Inbox messages received and sent, with tags, sender, and actions. Can filter by sender (`from.guid`) |
| Listening | `POST /v1/{cid}/listening/topics/{id}/messages` | R | Messages in a topic (no X) |
| Listening | `POST /v1/{cid}/listening/topics/{id}/metrics` | R | Topic metrics, sentiment |
| Publishing | `POST /v1/{cid}/publishing/posts` | **W** | **Create a draft post** |
| Publishing | `GET /v1/{cid}/publishing/posts/{id}` | R | One draft by ID |
| Media | `POST /v1/{cid}/media/` | **W** | Upload ≤ 50 MiB (file or public URL) |
| Media | `POST /v1/{cid}/media/submission` | **W** | Start multipart upload |
| Media | `POST /v1/{cid}/media/submission/{id}/part/{n}` | **W** | Upload a 5 MiB part |
| Media | `GET /v1/{cid}/media/submission/{id}` | R | Finish multipart upload |
| Cases | `POST /v1/{cid}/cases/filter` | R | Cases: status, priority, queue, assignee, messages |

There's no PUT, PATCH, or DELETE anywhere, and no "list drafts" call.

## Creating drafts: the details that matter

- `"is_draft": true` is required. *"Only posts created in draft status are supported at this time."*
- `delivery` (a scheduled time) is optional and **still creates a draft**. Times must be in the future.
- **Fan-out:** one request with N profiles creates N separate calendar posts, and N × T if there are T scheduled times. Each one gets its own `publishing_post_id`, so log them all.
- Every profile on a post must be in the **same group** (`group_id`).
- **Silent drops:** if the media doesn't suit one of the profiles (for example a PDF on Instagram), that profile is skipped with **no error**. Compare the profiles in the response with the profiles in the request.
- Instagram Stories / Mobile Publisher can't be created. They come through as regular media posts.
- Retrieving a post always shows `delivery_status: PENDING`, even after it's published. Use the Messages endpoint to see published posts.
- Uploaded media expires in **24 hours** unless it's attached to a post. Supported networks: Instagram, Facebook, Threads, X, LinkedIn, YouTube, TikTok, Pinterest, Google Business.

### Scheduled drafts (D9, confirmed)
Scheduled drafts created through the API **stay drafts**. They don't publish
unless a person releases them in Sprout. Scheduled times are allowed, which
fills the publishing calendar realistically.

## What this means for each building block

| Block | API | Everything else |
| --- | --- | --- |
| Posts in composer/calendar/approvals | ✅ Create drafts (with media, tags, and scheduled times) | Can't edit or remove via API |
| Inbox messages (permanent in Sprout, D8) | ❌ No create. ✅ **Can read** them to confirm seeding worked | The two fake X profiles send them (CLAUDE.md rule 3). X review done (D10), so these are readable |
| Cases | ❌ No create. ✅ Read | Seeded inbox messages turned into cases by hand or in the UI |
| Listening | ❌ No create. ✅ Read topics, messages, metrics | Set topics up once by hand. X isn't available in Listening |
| Reports / analytics | ✅ Read only | History comes from real activity. Overlay for prospect-specific numbers |
| Tags, groups, users, teams, queues | ✅ Read only | Set up once by hand in the tenant baseline |
| Reset | ❌ Nothing | Browser automation or by hand |
| **"Diagnose" (customer-risk pillar)** | ✅ Very strong: profiles, users, teams, queues, tags, analytics, inbox actions, cases, listening | Read-only by design |

## The strategy: seed once per vertical, overlay per prospect

With no delete, every API write is permanent unless someone removes it in the UI.

1. **Prospect names are allowed in drafts,** but the tenant is shared and drafts can't be deleted via the API. Tag prospect-specific drafts with the run ID and clear them in the browser afterward. Prefer the overlay when it's enough.
2. **Seed one reusable draft set per vertical** (for example about 40 Healthcare drafts, no company names). Tag them with a fixed vertical tag created by hand, since the API can't create tags. Every Healthcare demo reuses them.
3. **Log every `publishing_post_id`** returned (remember the fan-out) in `manifest.json`. Drafts can only be checked one by one using these IDs.
4. **Cleanup happens in the browser or by hand,** with the manifest as the checklist.

## The inventory snapshot, now fuller

Before and after each demo, read and compare:
- Metadata: profiles, groups, users, tags, topics, teams, queues
- **Inbox:** `POST /messages` filtered to the seeding personas (`from.guid`) and the demo window. This shows exactly which seeded messages exist
- **Cases:** `POST /cases/filter` for the demo window
- **Drafts:** `GET /publishing/posts/{id}` for each ID in the manifest

With the 60/min limit, a full inventory takes about a minute.

## Our client: `tools/sprout_api.py`

Standard-library Python, no install. It refuses any customer ID but
`2160354` and any call not on its allowed list (no delete, update, or publish
exists to send). Draft writes need an approved `runs/<run>/plan.md`, are saved
to `manifest.json` before they're sent, record every fan-out ID, and flag
silently dropped profiles. It also refuses Reddit profiles, archived or
other-group tags, and the blocked real-company tag.

```
python3 tools/sprout_api.py check                                  # token reaches the demo tenant
python3 tools/sprout_api.py index                                  # regenerate context/tenant-index.md
python3 tools/sprout_api.py inventory --out before.json --run runs/<run>
python3 tools/sprout_api.py diff before.json after.json            # exit 1 if anything changed
python3 tools/sprout_api.py drafts --run runs/<run> --file drafts.json
python3 -m unittest discover -s tools                              # tests, no network
```

## Using the MCP server

Treat it as a reference, not something to connect to the demo tenant as is:
- It's a single-maintainer third-party package. Pin a reviewed version or write our own thin client.
- It has no guard against a non-demo account. Our client should refuse every customer ID except the demo tenant's.
- It uses a long-lived API token. The docs recommend OAuth machine-to-machine, which is better for Security. (Most agent work goes through the browser as the SE (S2), so the API is mainly for reads and seeding drafts.)
- It doesn't log the fan-out IDs or check for silent profile drops.
