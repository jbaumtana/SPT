"""Tests for overlay_payload.py (docs/overlay-fix-plan.md, Phase 3). No network, no browser."""

import unittest

import overlay_payload as op

APP_MAP = {"screens": {
    "publishingCalendar": {"wholeCaption": "span[data-qa-message-text]", "postKeyAttr": "data-qa-msg",
                           "dateAttr": "data-qa-date", "dateFormat": "MM/DD/YYYY",
                           "selectors": {"calendarCaption": "span.piece"}},
    "approvals": {"selectors": {"approvalCaption": ".appr", "authorName": ".author"}},
    "composer": {"selectors": {"profileAvatar": "img.av"}},
}}


def data(**over):
    d = {
        "workspace": {"brandColors": {"primary": "#005EB8", "accent": "#00A3E0"}, "logoDataUri": "data:image/svg+xml;base64,AA"},
        "relabels": [["Secure Patient Technology", "BCBSA"], ["Compliance Approval [MF]", "Legal & Policy Review"]],
        "campaigns": [{"id": "c1", "name": "Policy Explainers", "replaces": ["Patient Portal Launch", "Tech - FAQ"]},
                      {"id": "c2", "name": "Open Enrollment 2027", "replaces": ["Tech - Hiring Campaign"]}],
        "posts": [
            {"id": "p1", "status": "scheduled", "caption": "Neutral one", "pinDate": None, "dateSensitive": False},
            {"id": "p2", "status": "scheduled", "caption": "Enrollment starts today", "pinDate": "2026-10-15", "dateSensitive": True},
            {"id": "p3", "status": "scheduled", "caption": "This week only", "pinDate": None, "dateSensitive": True},
            {"id": "p9", "status": "pending_approval", "caption": "CMS has announced updates", "pinDate": None, "dateSensitive": False},
        ],
        "approvals": [{"postId": "p9", "requestedBy": "u1"}],
        "users": [{"id": "u1", "name": "Dev Malhotra", "isFictional": True}],
        "outOfClickPath": ["Life, Illuminated"],
    }
    d.update(over)
    return d


class BuildTests(unittest.TestCase):
    def test_d1_pinned_caption_is_scoped_and_never_rotates(self):
        payload, warnings = op.build(data(), APP_MAP)
        rules = payload["selectorRules"]
        pinned = [r for r in rules if r.get("scope")]
        self.assertEqual(pinned[0]["scope"], "[data-qa-date='10/15/2026']")
        self.assertEqual(pinned[0]["value"], "Enrollment starts today")
        self.assertEqual(pinned[0]["perScope"], 1)  # one post per day, not every post that day
        for r in rules:
            if isinstance(r["value"], list):
                self.assertNotIn("Enrollment starts today", r["value"])
                self.assertNotIn("This week only", r["value"])
        self.assertTrue(any("p3" in w for w in warnings))  # date-sensitive without a pin is dropped, loudly

    def test_e3_general_rule_is_keyed_by_post(self):
        payload, _ = op.build(data(), APP_MAP)
        general = [r for r in payload["selectorRules"] if r["selector"] == "span[data-qa-message-text]" and not r.get("scope")]
        self.assertEqual(general[0]["keyAttr"], "data-qa-msg")

    def test_d2_campaign_labels_come_from_the_data(self):
        payload, _ = op.build(data(), APP_MAP)
        rules = {r["find"]: r["replace"] for r in payload["textRules"]}
        self.assertEqual(rules["Patient Portal Launch"], "Policy Explainers")
        self.assertEqual(rules["Tech - Hiring Campaign"], "Open Enrollment 2027")

    def test_d3_author_line_by_selector_with_persona(self):
        payload, _ = op.build(data(), APP_MAP)
        author = [r for r in payload["selectorRules"] if r["selector"] == ".author"]
        self.assertEqual(author[0]["value"], "Dev Malhotra")
        self.assertNotIn("Dev Malhotra", [r["replace"] for r in payload["textRules"]])

    def test_d3_missing_author_selector_warns(self):
        m = {"screens": dict(APP_MAP["screens"], approvals={"selectors": {"approvalCaption": ".appr"}})}
        _, warnings = op.build(data(), m)
        self.assertTrue(any("authorName" in w for w in warnings))

    def test_text_rules_longest_first(self):
        payload, _ = op.build(data(relabels=[["Tech", "X"], ["Tech Marketing Team", "Y"]]), APP_MAP)
        finds = [r["find"] for r in payload["textRules"]]
        self.assertLess(finds.index("Tech Marketing Team"), finds.index("Tech"))


class CheckTests(unittest.TestCase):
    def test_d6_shorter_find_before_longer_is_rejected(self):
        p = {"textRules": [{"find": "Coffee", "replace": "a"}, {"find": "Northwind Coffee", "replace": "b"}], "selectorRules": []}
        self.assertTrue(any("Coffee" in x for x in op.check(p)))

    def test_d6_unescaped_html_is_rejected(self):
        p = {"textRules": [], "selectorRules": [{"selector": "x", "action": "html", "value": "<img src=x onerror=alert(1)>"}]}
        self.assertTrue(op.check(p))
        p["selectorRules"][0]["value"] = "Fish &amp; chips"
        self.assertEqual(op.check(p), [])

    def test_d1_check_catches_sensitive_caption_in_rotation(self):
        p = {"textRules": [], "selectorRules": [{"selector": ".appr", "action": "text", "value": ["Enrollment starts today", "Neutral one"]}]}
        self.assertTrue(any("p2" in x for x in op.check(p, data())))

    def test_d4_coverage(self):
        ui = ('- **Campaigns shown:** Tech - Hiring Campaign, Tech - FAQ, Tech - Webinar Event.\n'
              '- Campaigns on items: Patient Portal Launch, Life, Illuminated.\n'
              '- 6 items. Workflows shown: "Compliance Approval Workflow - Step 1" and "Compliance Approval [MF] - Step 1".\n'
              '| Secure Patient Tech | Brand Health | 1 | |\n')
        payload, _ = op.build(data(), APP_MAP)
        problems = op.check(payload, data(), ui)
        missing = sorted(p.split('"')[1] for p in problems)
        self.assertEqual(missing, ["Compliance Approval Workflow", "Secure Patient Tech", "Tech - Webinar Event"])

    def test_built_payload_passes_its_own_check(self):
        payload, _ = op.build(data(), APP_MAP)
        self.assertEqual(op.check(payload, data()), [])


if __name__ == "__main__":
    unittest.main()
