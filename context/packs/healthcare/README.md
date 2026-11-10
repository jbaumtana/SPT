# Healthcare pack (v1)

Built from [the playbook](../../playbooks/healthcare.md) for the Secure Patient
Technology brand group (`2510938`). Prospect-neutral. Illustrative sample data.

| Content | Count |
| --- | --- |
| Scheduled posts (X, Instagram, LinkedIn, Threads) | 18, across patient education, privacy, community, provider spotlights, careers, events |
| Pending-approval post (clinical, then compliance review) | 1 |
| Seasonal library (dated copy, kept out of the rotation) | 4 |
| Inbox messages from the seeding personas | 20: 12 positive, 5 neutral, 3 negative (a billing cluster) |
| Campaign labels | 5, covering the 9 seed campaign labels in the click path (the tenant's "Life, Illuminated" test item is left alone) |

Files: `demo-data.json` is the source of truth. `overlay-payload.json` is built
from it, so regenerate it rather than editing it:

```bash
python3 tools/overlay_payload.py build context/packs/healthcare/demo-data.json
python3 tools/check_pack.py context/packs/healthcare/demo-data.json
```

## Known limits
- The approval card's author line still shows a real tenant user until the `approvals.authorName` selector (S4) is recorded in `app-map.json`. The build warns about it.
- Posts are `visibility: draft`. Nothing here is loaded into the tenant or published. That is the Hands workstream, and needs an approved plan.
- Payer ("members", no service lines) needs its own variant. TODO, per the playbook's Gaps.
- No reports or metrics are generated. Report history can't be seeded (open-questions D6).
- Review the 20 inbox messages and the invented user names before the first live demo. They were written from the playbook's scenarios, not from a real deal.
