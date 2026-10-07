# Open questions

These decide how much of this is automatable. Most of them are quick for the
right person to answer.

## Demo Engineering
| # | Question | Why it matters | Answer |
| --- | --- | --- | --- |
| D1 | What internal demo tooling exists today (seeders, scripts, tenant cloning)? | Might already cover the "hands" and reset | |
| D2 | Which objects can be created via public or internal API? (posts, inbox items, listening topics, reports, users, profiles) | Decides API vs browser split | |
| D3 | Can inbox messages, reviews, and engagement history be seeded without a real network connection? | Core to the "live" feel | |
| D4 | Can a demo tenant be snapshotted and restored? How long does it take? | Best rollback story | |
| D5 | How many demo tenants exist, and are they shared or one per SE? | Concurrency + reset cadence | |
| D6 | How does report/analytics history get populated in demo tenants? | Charts usually can't be overlaid | |
| D7 | Are there DOM/test IDs we can rely on, and how often does the UI change? | Browser automation stability | |

## Security / IT
| # | Question | Answer |
| --- | --- | --- |
| S1 | Is it OK to process prospect discovery notes with Claude? Under what data-retention terms? | |
| S2 | Which credentials can an agent use against demo tenants, and how are they scoped? | |
| S3 | Is Claude in Chrome / browser automation approved on demo domains? | |
| S4 | Is there a hard technical guard that keeps agents off production tenants? | |

## Legal / Brand
| # | Question | Answer |
| --- | --- | --- |
| L1 | Can we show a prospect's logo and brand colors in a demo without their written OK? | |
| L2 | Required disclaimer wording for illustrative sample data? | |

## SE team
| # | Question | Answer |
| --- | --- | --- |
| E1 | Where are today's best demo assets (Rovo/Confluence links)? | |
| E2 | Which 2–3 SEs pilot Phase 1? | |
| E3 | How long does tailoring take today (baseline for measuring time saved)? | |
