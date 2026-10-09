"""Tests for sprout_api.py. A fake transport stands in for Sprout; nothing here touches the tenant.

Run: python3 -m unittest discover -s tools
"""

import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

import sprout_api as sa

CID = sa.CUSTOMER_ID
SPT, PERSONAS = 2510938, 2708092

PROFILES = [
    {"customer_profile_id": 7139160, "network_type": "twitter", "name": "SPT", "groups": [SPT]},
    {"customer_profile_id": 7140859, "network_type": "fb_instagram_account", "name": "SPT", "groups": [SPT]},
    {"customer_profile_id": 7485688, "network_type": "reddit_user", "name": "SPTJackie", "groups": [SPT]},
    {"customer_profile_id": 7371059, "network_type": "twitter", "name": "Emily", "groups": [PERSONAS]},
]
TAGS = [
    {"tag_id": 3867977, "text": "Tech - Compliance Campaign", "type": "CAMPAIGN", "active": True, "any_group": False, "groups": [SPT]},
    {"tag_id": 4162648, "text": "Real company", "type": "CAMPAIGN", "active": True, "any_group": False, "groups": [SPT]},
    {"tag_id": 3936839, "text": "Archived", "type": "LABEL", "active": False, "any_group": False, "groups": [SPT]},
    {"tag_id": 3230184, "text": "Pets", "type": "LABEL", "active": True, "any_group": False, "groups": [2239667]},
    {"tag_id": 4020464, "text": "Any group", "type": "CAMPAIGN", "active": True, "any_group": True, "groups": []},
]


def future(minutes=60):
    return (dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")


class FakeSprout:
    def __init__(self, drop=(), post_status=200):
        self.calls, self.drop, self.post_status, self.next_id = [], set(drop), post_status, 9000

    def __call__(self, method, url, body, headers):
        path = url[len(sa.BASE_URL):]
        self.calls.append((method, path, body))
        if path == "/v1/metadata/client":
            return 200, json.dumps({"data": [{"customer_id": CID, "name": "SPT"}]}).encode()
        if path == f"/v1/{CID}/metadata/customer":
            return 200, json.dumps({"data": PROFILES}).encode()
        if path == f"/v1/{CID}/metadata/customer/tags":
            return 200, json.dumps({"data": TAGS}).encode()
        if path == f"/v1/{CID}/publishing/posts" and method == "POST":
            if self.post_status != 200:
                return self.post_status, b'{"error": "boom"}'
            req = json.loads(body)
            times = (req.get("delivery") or {}).get("scheduled_times") or [None]
            data = []
            for pid in req["customer_profile_ids"]:
                if pid in self.drop:
                    continue
                for t in times:
                    self.next_id += 1
                    data.append({"customer_profile_id": str(pid), "internal": {"publishing": {
                        "publishing_post_id": self.next_id, "is_draft": True,
                        "deliveries": [{"scheduled_time": t}] if t else [],
                        "perma_link": f"https://app.sproutsocial.com/publishing/activity/x/{self.next_id}"}}})
            return 200, json.dumps({"data": data}).encode()
        return 404, b'{"error": "not found"}'


class NoWait:
    def wait(self):
        pass


def client(fake):
    return sa.SproutClient(transport=fake, limiter=NoWait())


def approved_run(tmp, approver="Jaclyn Q"):
    run = Path(tmp) / "2026-10-08-test"
    run.mkdir()
    (run / "plan.md").write_text(f"## Approval\n- **Approved by:** {approver}\n- **Approved at:** now\n")
    return run


class LockTests(unittest.TestCase):
    def test_other_customer_refused(self):
        with self.assertRaises(sa.GuardrailError):
            sa.SproutClient(customer_id=1234)

    def test_delete_put_patch_and_other_paths_refused(self):
        fake = FakeSprout()
        c = client(fake)
        for method, path in [("DELETE", f"/v1/{CID}/publishing/posts/1"),
                             ("PUT", f"/v1/{CID}/publishing/posts/1"),
                             ("PATCH", f"/v1/{CID}/publishing/posts/1"),
                             ("GET", "/v1/9999/metadata/customer"),
                             ("POST", "/v1/9999/publishing/posts"),
                             ("POST", f"/v1/{CID}/publishing/posts/1/publish")]:
            with self.assertRaises(sa.GuardrailError, msg=f"{method} {path}"):
                c.request(method, path)
        self.assertEqual(fake.calls, [])

    def test_rate_limiter_waits_after_60(self):
        t = [0.0]
        slept = []

        def sleep(s):
            slept.append(s)
            t[0] += s
        rl = sa.RateLimiter(per_minute=60, clock=lambda: t[0], sleep=sleep)
        for _ in range(61):
            rl.wait()
        self.assertEqual(len(slept), 1)
        self.assertGreaterEqual(slept[0], 60)


class ApprovalGateTests(unittest.TestCase):
    def test_unapproved_plan_blocks_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = approved_run(tmp, approver="_(SE name)_")
            with self.assertRaises(sa.GuardrailError):
                sa.Manifest(run)
            (run / "plan.md").unlink()
            with self.assertRaises(sa.GuardrailError):
                sa.Manifest(run)

    def test_approved_plan_allows_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(sa.Manifest(approved_run(tmp)).approved_by, "Jaclyn Q")


class DraftTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.manifest = sa.Manifest(approved_run(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def assert_refused(self, **kw):
        fake = FakeSprout()
        args = dict(group_id=SPT, profile_ids=[7139160], text="hi")
        args.update(kw)
        with self.assertRaises(sa.GuardrailError):
            client(fake).create_draft(self.manifest, **args)
        self.assertFalse([c for c in fake.calls if c[0] == "POST"], "nothing may be written")
        self.assertEqual(self.manifest.data["entries"], [])

    def test_refuses_reddit(self):
        self.assert_refused(profile_ids=[7485688])

    def test_refuses_profile_outside_group(self):
        self.assert_refused(profile_ids=[7139160, 7371059])

    def test_refuses_unknown_profile(self):
        self.assert_refused(profile_ids=[1])

    def test_refuses_blocked_archived_and_foreign_tags(self):
        for tag in (4162648, 3936839, 3230184, 1):
            self.assert_refused(tag_ids=[tag])

    def test_refuses_past_times(self):
        self.assert_refused(scheduled_times=["2020-01-01T00:00:00Z"])

    def test_fan_out_logged_and_always_draft(self):
        fake = FakeSprout()
        posts, dropped = client(fake).create_draft(
            self.manifest, SPT, [7139160, 7140859], "hello", [future(60), future(120)], tag_ids=[3867977, 4020464])
        self.assertEqual(len(posts), 4)
        self.assertEqual(dropped, [])
        sent = json.loads([c for c in fake.calls if c[0] == "POST"][0][2])
        self.assertIs(sent["is_draft"], True)
        saved = json.loads((self.manifest.path).read_text())
        self.assertEqual(saved["entries"][0]["status"], "done")
        self.assertEqual(len(self.manifest.publishing_post_ids()), 4)

    def test_silent_drop_recorded(self):
        posts, dropped = client(FakeSprout(drop={7140859})).create_draft(self.manifest, SPT, [7139160, 7140859], "x")
        self.assertEqual(dropped, [7140859])
        self.assertEqual(self.manifest.data["entries"][0]["dropped_profile_ids"], [7140859])

    def test_manifest_written_before_request_and_kept_on_failure(self):
        fake = FakeSprout(post_status=500)
        seen = []
        orig = fake.__call__

        def spy(method, url, body, headers):
            if method == "POST":
                seen.append(json.loads(self.manifest.path.read_text())["entries"][-1]["status"])
            return orig(method, url, body, headers)
        with self.assertRaises(sa.ApiError):
            client(spy).create_draft(self.manifest, SPT, [7139160], "x")
        self.assertEqual(seen, ["pending"])
        self.assertEqual(self.manifest.data["entries"][0]["status"], "failed")


class IndexTests(unittest.TestCase):
    def test_render_index(self):
        inv = {"taken_at": "2026-10-09T00:00:00Z", "customer_id": CID, "token_sees_customers": [CID],
               "window": ["2026-09-09T00:00:00Z", "2026-10-09T00:00:00Z"],
               "groups": {str(SPT): "Secure Patient Technology", str(PERSONAS): "SPT Personas"},
               "tags": {str(t["tag_id"]): t for t in TAGS},
               "teams": {"1": "Team A"}, "queues": {"2": "Queue B"}, "users": ["1", "2", "3"],
               "persona_messages": {"g1": {"from": "arlettabrown353", "post_type": "TWEET"}},
               "cases": {"9": {"status": "OPEN"}}}
        topics = [{"name": "Secure Patient Tech", "topic_type": "BRAND_HEALTH", "group_id": SPT}]
        md = sa.render_index(inv, PROFILES, topics)
        self.assertIn("| twitter | Emily |  | 7371059 |", md)
        self.assertIn("4162648 | _(name withheld", md)
        self.assertNotIn("Real company", md)
        self.assertNotIn("Archived", md.split("Archived tags")[1])  # archived tag texts aren't listed
        self.assertIn("| Secure Patient Tech | BRAND_HEALTH | Secure Patient Technology |", md)
        self.assertIn("**Users:** 3", md)
        self.assertIn("1 from arlettabrown353 (TWEET)", md)
        self.assertNotIn("@", md.replace("arlettabrown353", ""))  # no emails


class DiffTests(unittest.TestCase):
    def test_diff(self):
        a = {"taken_at": "1", "tags": {"1": {"text": "a"}}, "users": ["1", "2"]}
        b = {"taken_at": "2", "tags": {"1": {"text": "b"}, "2": {"text": "c"}}, "users": ["1"]}
        d = sa.diff(a, b)
        self.assertEqual(list(d["tags"]["added"]), ["2"])
        self.assertEqual(list(d["tags"]["changed"]), ["1"])
        self.assertEqual(list(d["users"]["removed"]), ["2"])
        self.assertEqual(sa.diff(a, a), {})


if __name__ == "__main__":
    unittest.main()
