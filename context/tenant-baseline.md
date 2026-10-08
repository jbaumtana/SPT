# Demo tenant baseline

The known-good starting state. Reset returns the tenant to this.

- **Tenant name:** Secure Patient Technology. The first **shared** demo tenant, on production Sprout and used as a sandbox. Agents confirm the session is in this tenant at the start. (Several tenants exist, some shared and some solo.)
- **Customer ID:** `2160354`
- **Login:** the agent acts as the SE through the browser extension, in the SE's own session. API credentials are injected by the cloud environment's proxy for `*.sproutsocial.com` (no key in the shell or in this file). Verified 2026-10-08: `GET /v1/metadata/client` returns only customer `2160354` ("SPT"), so the token can't reach any other customer
- **Reset procedure today:** None. Planned approach in [docs/tenant-snapshots.md](../docs/tenant-snapshots.md)
- **Existing tooling:** None
- **Source:** profile export [`sources/profiles-2026-10-07.csv`](sources/profiles-2026-10-07.csv), cross-checked against the API metadata reads on 2026-10-08

## Groups
Every profile on one post must be in the same group (`docs/api-coverage.md`).

| Group | Group ID | Role in demos |
| --- | --- | --- |
| **Secure Patient Technology** | `2510938` | Demo brand for **Healthcare** (default group for this project) |
| Snouts, Paws & Tails | `2239667` | Second demo brand (pet care, retail, multi-location). Not mapped to a playbook yet |
| SPT Personas | `2708092` | Fake customer profiles that send inbox messages |
| Healthcare Tech | `2510941` | Not ours. Leave alone |
| TEST | `2808685` | Not ours. Leave alone |

## Demo brand profiles: Secure Patient Technology (group `2510938`)
| Network | Name | Handle | Sprout ID | Notes |
| --- | --- | --- | --- | --- |
| X | SecurePatientTechnology | @SecurePatientIT | 7139160 | **Receives the seeded inbox messages** from the personas |
| Instagram | Secure Patient Technology | securepatientit | 7140859 | |
| LinkedIn | Secure Patient Technology | secure-patient-technology | 7139172 | |
| Threads | securepatientit | securepatientit | 7213583 | |
| Bluesky | (no display name) | securepatientit.bsky.social | 7167703 | |
| Yelp | Secure Patient Technology | (Wilton, CT listing) | 7314445 | Reviews in the Sprout UI only. **Not available via the API** |
| Reddit user | SPTJackie | SPTJackie | 7485688 | Shared with Snouts, Paws & Tails. Not returned by the API metadata call |

No Facebook, TikTok, YouTube, or Google Business profile in this group.
Facebook and Google Business only exist under Snouts, Paws & Tails.

## Inbox seeding personas (group: SPT Personas)
Three fake customer profiles, all cleared for seeding. They're **connected to Sprout**, so messages can be
sent from inside Sprout or on X directly. See CLAUDE.md rule 3.

| Network | Handle | Persona | Sprout ID | Credentials |
| --- | --- | --- | --- | --- |
| X | @EmilyNMarketing | Emily Nguyen | 7371059 | Password manager, never this file |
| X | @dublindrforkids | Liam O'Sullivan | 7371093 | Password manager, never this file |
| Instagram | drarlettabrown | Arletta Brown | 7599412 | Cleared for seeding (Oct 2026). Credentials in password manager |

## Second demo brand: Snouts, Paws & Tails
Pet care brand with the widest network coverage in the tenant: Facebook,
Instagram, X, LinkedIn, Threads, Bluesky, TikTok, Pinterest, Reddit
(subreddit + user), Snapchat, WhatsApp, Google Business, two Yelp listings,
two Google Analytics properties, and Meta + LinkedIn ad accounts. Full list
in the profile export.

A few profiles in this group look like leftovers from other demos (LinkedIn
"Summit Active", TikTok "sproutcoffeeco", LinkedIn ad accounts "FTB" and
"Sprout's Ad Account"). Leave them alone. They aren't ours to clean up.

Ad accounts and Yelp aren't available through the API.

## Groups, users, and roles
The tenant has **506 users** (Sprout staff, shared tenant). Don't copy the
user list into this repo; read it from `GET /v1/2160354/metadata/customer/users`
when needed.

| User (persona) | Role / permissions | Used to demo |
| --- | --- | --- |
| TODO | | Approval workflow |

### Teams and case queues (API, 2026-10-08)
SPT-relevant: team **Secure Patient Tech Marketing Team** (`18934`), queues
**Secure Patient Technology Unassigned** (`17591`), **Secure Patient FAQ IRL**
(`17414`), **HCT Technical Support** (`17163`), plus the shared
**Positive Sentiment** (`17256`), **Negative Sentiment** (`17257`), and
**Malicious and Spam** (`17600`). Other teams and queues belong to Snouts,
Paws & Tails.

### Tags (API, 2026-10-08)
323 tags, 155 active. Active **campaign** tags in the SPT group (`2510938`) or
any group:

| Tag ID | Campaign | Scope |
| --- | --- | --- |
| 3867971 | Tech -  Infographics | SPT |
| 3867974 | Tech - Influencer Marketing Campaign | SPT |
| 3867977 | Tech - Compliance Campaign | SPT |
| 3867978 | Tech - Webinar Event | SPT |
| 3867984 | Tech - Event | SPT |
| 3867986 | Tech - Executives | SPT |
| 3867987 | Tech - Hiring Campaign | SPT |
| 3934589 | Tech - FAQ | SPT |
| 4178450 | Life, Illuminated | SPT |
| 4187011 | Community Hypertension Program | SPT |
| 4357351 | Patient Portal Launch | SPT |
| 4020464 | Tech - Security Breach Awareness | any group |
| 4020475 | Tech - ViVE 2025 Event | any group |

There's also an active SPT campaign tag named after a real health system
(`4162648`), left from an earlier demo. Not ours to remove, but **don't apply
it to seeded drafts** and steer the click path away from it. All other
"Tech - …" labels in the SPT group are archived. No vertical seeding tag
exists yet (the API can't create one, so an SE adds it by hand).

## Reports
Report history comes from **real data** on the social profiles authorized in
this tenant (D6). It can't be seeded. Keep report screens to what those
profiles really show, and use the overlay for any prospect-specific numbers.

## Pre-seeded content
- Publishing calendar: TODO (how many weeks, which campaigns)
- Smart Inbox: TODO (message types, sentiment mix). API read 2026-10-08: the SPT brand profiles logged 100+ messages in the two weeks to Oct 8, mostly the brand's own posts (X, Bluesky, Threads, Instagram) plus a few Instagram comments and X mentions
- Reports: TODO (which have history, date range)
- Listening topics (API, 2026-10-08): SPT group has **Secure Patient Tech** (Brand Health), **Healthcare Tech Industry** (Industry Insights), and **Credit Unions Industry** (Industry Insights). The other 11 topics belong to Snouts, Paws & Tails
- Asset library: TODO

## Standard click path
1. TODO
2. TODO

## What can't be changed per prospect (and must be talked around)
- TODO
