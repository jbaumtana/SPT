"""Tests for check_pack.py. Each case breaks the Healthcare pack one way and expects that error."""

import copy
import json
import unittest
from pathlib import Path

import check_pack as cp

ROOT = Path(__file__).resolve().parent.parent
PACK = json.loads((ROOT / "context/packs/healthcare/demo-data.json").read_text())
SCHEMA = json.loads(cp.SCHEMA.read_text())
TENANT = cp.TENANT_INDEX.read_text()
UI = (ROOT / "context/tenant-index-ui.md").read_text()
BLOCKED = set(json.loads(cp.CONFIG.read_text())["blocked_tag_ids"])


def run(d, prospect=None):
    return cp.check(d, prospect, TENANT, UI, SCHEMA, blocked_tags=BLOCKED)


def broken(fn):
    d = copy.deepcopy(PACK)
    fn(d)
    return d


class PackTests(unittest.TestCase):
    def has(self, errs, text):
        self.assertTrue(any(text in e for e in errs), f"expected '{text}' in {errs}")

    def test_committed_pack_is_clean(self):
        self.assertEqual(run(copy.deepcopy(PACK)), [])

    def test_real_org_name_is_caught(self):
        self.has(run(broken(lambda d: d["posts"][0].update(caption="See us at ViVE next week"))), "blocklisted")

    def test_outcome_claim_and_percent_are_caught(self):
        self.has(run(broken(lambda d: d["posts"][0].update(caption="Our program cures back pain"))), "outcome claim")
        self.has(run(broken(lambda d: d["posts"][1].update(caption="Patients love us, 94% say so"))), "outcome claim")

    def test_private_details_are_caught(self):
        self.has(run(broken(lambda d: d["inbox"][0].update(text="Call me at 555-123-4567"))), "phone number")

    def test_year_and_placeholder_are_caught(self):
        self.has(run(broken(lambda d: d["posts"][0].update(caption="Join us in 2027"))), "year")
        self.has(run(broken(lambda d: d["posts"][0].update(caption="Join [Action 1] today"))), "placeholder")

    def test_prospect_name_in_industry_pack_and_public_copy(self):
        self.has(run(broken(lambda d: d["meta"].update(prospect="Acme Health"))), "prospect-neutral")
        def pub(d):
            d["meta"]["allowPublic"] = True
            d["posts"][0].update(visibility="public", caption="Acme Health cares")
        self.has(run(broken(pub), prospect="Acme Health"), "prospect name")

    def test_public_needs_an_approved_plan(self):
        self.has(run(broken(lambda d: d["posts"][0].update(visibility="public"))), "allowPublic")

    def test_dated_copy_stays_out_of_industry_posts(self):
        self.has(run(broken(lambda d: d["posts"][0].update(pinDate="2026-10-15", dateSensitive=True))), "seasonalLibrary")

    def test_unknown_profile_and_blocked_tag(self):
        self.has(run(broken(lambda d: d["profiles"][0].update(sproutProfileId=9999999))), "tenant-index")
        self.has(run(broken(lambda d: d["campaigns"][0].update(tenantTagId=4162648))), "blocked")

    def test_only_seeding_personas_send_inbox_messages(self):
        self.has(run(broken(lambda d: d["inbox"][0].update(senderHandle="@somerealperson"))), "seeding handle")

    def test_sentiment_mix_must_match(self):
        def f(d):
            for m in d["inbox"][:3]:
                m["sentiment"] = "negative"
        self.has(run(broken(f)), "sentiment")

    def test_approval_needs_a_compliance_step(self):
        def f(d):
            d["approvals"][0]["steps"] = [{"name": "Clinical content review", "approver": "u-clinical"}]
        self.has(run(broken(f)), "compliance step")

    def test_unreal_user_flag_and_schema(self):
        self.has(run(broken(lambda d: d["users"][0].update(isFictional=False))), "schema")

    def test_customer_pack_needs_a_plan(self):
        def f(d):
            d["meta"].update(track="customer", prospect="Acme Health", planPath=None)
        self.has(run(broken(f), prospect="Acme Health"), "no plan, no build")

    def test_caption_length(self):
        self.has(run(broken(lambda d: d["posts"][2].update(caption="x" * 300))), "limit")

    def test_uncovered_seed_label_is_caught_through_overlay_check(self):
        self.has(run(broken(lambda d: d["campaigns"][0].update(replaces=[]))), "seed label")


if __name__ == "__main__":
    unittest.main()
