# Demo tenant baseline

The known-good starting state. Reset returns the tenant to this.

- **Tenant name:** Secure Patient Technology. The first **shared** demo tenant, on production Sprout and used as a sandbox. Agents confirm the session is in this tenant at the start. (Several tenants exist, some shared and some solo.)
- **Customer ID:** `2160354`
- **Login:** the agent acts as the SE through the browser extension, in the SE's own session. API credentials live in the environment's secrets (`SPROUT_API_TOKEN`, or `SPROUT_CLIENT_ID` + `SPROUT_CLIENT_SECRET`), never in this file
- **Reset procedure today:** None. Planned approach in [docs/tenant-snapshots.md](../docs/tenant-snapshots.md)
- **Existing tooling:** None
- **Source:** profile export [`sources/profiles-2026-10-07.csv`](sources/profiles-2026-10-07.csv)

## Groups
Every profile on one post must be in the same group (`docs/api-coverage.md`).

| Group | Group ID | Role in demos |
| --- | --- | --- |
| **Secure Patient Technology** | `2510938` | Demo brand for **Healthcare** (default group for this project) |
| Snouts, Paws & Tails | `2239667` | Second demo brand (pet care, retail, multi-location). Not mapped to a playbook yet |
| SPT Personas | TODO | Fake customer profiles that send inbox messages |

## Demo brand profiles: Secure Patient Technology (group `2510938`)
| Network | Name | Handle | Sprout ID | Notes |
| --- | --- | --- | --- | --- |
| X | SecurePatientTechnology | @SecurePatientIT | 7139160 | **Receives the seeded inbox messages** from the personas |
| Instagram | Secure Patient Technology | securepatientit | 7140859 | |
| LinkedIn | Secure Patient Technology | secure-patient-technology | 7139172 | |
| Threads | securepatientit | securepatientit | 7213583 | |
| Bluesky | (no display name) | securepatientit.bsky.social | 7167703 | |
| Yelp | Secure Patient Technology | (Wilton, CT listing) | 7314445 | Reviews in the Sprout UI only. **Not available via the API** |
| Reddit user | SPTJackie | SPTJackie | 7485688 | Shared with Snouts, Paws & Tails |

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
| User (persona) | Role / permissions | Used to demo |
| --- | --- | --- |
| TODO | | Approval workflow |

## Reports
Report history comes from **real data** on the social profiles authorized in
this tenant (D6). It can't be seeded. Keep report screens to what those
profiles really show, and use the overlay for any prospect-specific numbers.

## Pre-seeded content
- Publishing calendar: TODO (how many weeks, which campaigns)
- Smart Inbox: TODO (volume, message types, sentiment mix)
- Reports: TODO (which have history, date range)
- Listening topics: TODO
- Asset library: TODO

## Standard click path
1. TODO
2. TODO

## What can't be changed per prospect (and must be talked around)
- TODO
