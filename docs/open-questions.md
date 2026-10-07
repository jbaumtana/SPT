# Open questions

These decide how much of this is automatable. Most of them are quick for the
right person to answer.

## Demo Engineering
| # | Question | Why it matters | Answer |
| --- | --- | --- | --- |
| D1 | What internal demo tooling exists today (seeders, scripts, tenant cloning)? | Might already cover the "hands" and reset | **None.** We build the hands and the reset ourselves |
| D2 | Which objects can be created via public or internal API? (posts, inbox items, listening topics, reports, users, profiles) | Decides API vs browser split | **Confirmed from the official docs:** 20 endpoints, all read except draft posts + media upload. No update or delete. Inbox messages, cases, and listening are readable. See [api-coverage.md](api-coverage.md) |
| D3 | Can inbox messages, reviews, and engagement history be seeded without a real network connection? | Core to the "live" feel | **Partly.** Two fake customer profiles on X send messages to the demo brand's X profile. Other networks: still unknown. See CLAUDE.md rule 3 |
| D4 | Can a demo tenant be snapshotted and restored? How long does it take? | Best rollback story | No platform snapshot. Plan: overlay + manifest teardown + inventory diff. See [tenant-snapshots.md](tenant-snapshots.md) |
| D5 | How many demo tenants exist, and are they shared or one per SE? | Concurrency + reset cadence | **Several, some shared and some solo.** Starting with **one shared tenant**, so SEs need to reserve it (see [tenant-snapshots.md](tenant-snapshots.md#shared-tenant-rules)) |
| D6 | How does report/analytics history get populated in demo tenants? | Charts usually can't be overlaid | **From real data** on social profiles authorized in Sprout. Report history can't be seeded, so prospect-specific numbers come from the overlay |
| D7 | Are there DOM/test IDs we can rely on, and how often does the UI change? | Browser automation stability | **Some stable element IDs, and the UI doesn't change often.** Overlay and browser automation are workable. Prefer the stable IDs in `app-map.json` |
| D8 | Does deleting an X post/DM remove the matching Sprout inbox item? | Decides whether seeded inbox messages can be reset | **No.** Deleting on X doesn't remove the item from Sprout, so seeded inbox messages are permanent |
| D9 | Does a *scheduled* draft created via the API ever publish without a person approving it? | A live post we can't delete via API. Until answered, API drafts are unscheduled only | **Confirmed: they stay drafts.** Scheduled drafts are allowed |
| D10 | Has the demo account accepted the X Content EULA and passed X's API review? | Needed to read the seeded X inbox messages through the API | **Yes.** X data is available through the API |
| D11 | Is the demo account on a plan with API access, and who has *API Permissions*? | No API without it | **Yes.** The plan includes API access, and API Permissions are in place |

## Security / IT
| # | Question | Answer |
| --- | --- | --- |
| S1 | Is it OK to process prospect discovery notes with Claude? Under what data-retention terms? | **Yes.** Prospect notes can be given to Claude |
| S2 | Which credentials can an agent use against demo tenants, and how are they scoped? (Sprout supports OAuth machine-to-machine with short-lived tokens, or long-lived API tokens) | **The agent acts as the SE** in the native Sprout app through the browser extension, using the SE's own session |
| S3 | Is Claude in Chrome / browser automation approved on demo domains? | **Yes.** Browser automation is approved |
| S4 | Is there a hard technical guard that keeps agents off production tenants? | **Yes.** The session only reaches the tenant the SE is logged into. The tenant is on production Sprout, used as a sandbox |

## Legal / Brand
| # | Question | Answer |
| --- | --- | --- |
| L1 | Can we show a prospect's logo and brand colors in a demo without their written OK? | **Yes.** Prospect logos can be used |
| L2 | Required disclaimer wording for illustrative sample data? | **No disclaimer needed** |
| L3 | Are the two fake X customer profiles OK under X's rules on automation and authenticity (labeled as test accounts, only interacting with our own demo profile)? Can an agent send from them, or only a person? | **Yes.** The X profiles are fine under X's rules, so an agent may send from them |

## SE team
| # | Question | Answer |
| --- | --- | --- |
| E1 | Where are today's best demo assets? (Export or copy them into `context/sources/`) | |
| E2 | Which 2–3 SEs pilot Phase 1? | |
| E3 | How long does tailoring take today (baseline for measuring time saved)? | |
