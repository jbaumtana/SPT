# Demo tenant baseline

The known-good starting state. Reset returns the tenant to this.

- **Tenant name / ID:** TODO (the first **shared** demo tenant, on production Sprout and used as a sandbox. Agents check this name and ID before every action. Several tenants exist, some shared and some solo)
- **Login:** the agent acts as the SE through the browser extension, in the SE's own session. API credentials: TODO (password manager, never this file)
- **Customer ID:** TODO
- **Reset procedure today:** None. Planned approach in [docs/tenant-snapshots.md](../docs/tenant-snapshots.md)
- **Existing tooling:** None

## Profiles (connected social accounts)
| Network | Profile name in tenant | Seeded? | Notes |
| --- | --- | --- | --- |
| Instagram | TODO | | |
| Facebook | TODO | | |
| LinkedIn | TODO | | |
| X | TODO (demo brand profile) | | Receives seeded inbox messages |
| TikTok | TODO | | |
| YouTube | TODO | | |
| Google Business | TODO | | Key for Travel & Hospitality, multi-location |

## Inbox seeding accounts (not connected to the tenant)
Two fake customer profiles on X that send messages to the demo brand's X
profile so they arrive in the Smart Inbox. See CLAUDE.md rule 3.

| Handle | Persona | Credentials location |
| --- | --- | --- |
| TODO | TODO | Password manager, never this file |
| TODO | TODO | Password manager, never this file |

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
