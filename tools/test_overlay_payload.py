"""Tests for overlay_payload.py (docs/overlay-fix-plan.md, Phase 3). No network, no browser."""

import unittest

import overlay_payload as op

APP_MAP = {"screens": {
    "publishingCalendar": {"wholeCaption": "span[data-qa-message-text]", "postKeyAttr": "data-qa-msg",
                           "dateAttr": "data-qa-date", "dateFormat": "MM/DD/YYYY",
                           "selectors": {"calendarCaption": "span.piece"}},
    "approvals": {"selectors": {"approvalCaption": ".appr", "authorName": ".author"}},
    "composer": {"selectors": {"profileAvatar": "img.av"}},
    "reports": {"selectors": {}, "charts": {"impressions": {"selector": "#chart-imp", "kind": "canvas"}, "mix": "#chart-mix"},
                "kpis": {"totalImpressions": "#kpi-imp"}},
}}
APP_MAP["screens"]["publishingCalendar"]["images"] = {"thumb": "img.thumb"}


def visuals(**over):
    d = {
        "overlayVisuals": {"charts": True, "images": True},
        "workspace": {"name": "Blue Cross Association", "brandColors": {"primary": "#005EB8", "accent": "#00A3E0"}, "logoDataUri": None},
        "charts": [
            {"id": "imp", "target": "impressions", "type": "line", "title": "Impressions <by> month",
             "categories": ["Jul", "Aug", "Sep"], "series": [{"name": "Impressions", "values": [1200, 1500, 1800]}]},
            {"id": "mix", "target": "mix", "type": "donut", "title": "Network mix",
             "categories": ["X", "Instagram"], "series": [{"name": "Share", "values": [60, 40]}]},
        ],
        "kpis": [{"id": "k1", "target": "totalImpressions", "derivedFrom": {"chart": "imp", "agg": "sum"}}],
        "images": [{"id": "i1", "screen": "publishingCalendar", "target": "thumb", "action": "swap", "src": "monogram"}],
    }
    d.update(over)
    return data(**d)


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


class VisualTests(unittest.TestCase):
    def rules(self, d):
        payload, warnings = op.build(d, APP_MAP)
        return payload, warnings, {r.get("_chart") or r.get("_kpi") or r.get("_image"): r for r in payload["selectorRules"]
                                   if r.get("_chart") or r.get("_kpi") or r.get("_image")}

    def test_off_by_default_even_when_the_data_has_visuals(self):
        d = visuals(overlayVisuals={})
        payload, warnings, found = self.rules(d)
        self.assertEqual(found, {})
        self.assertTrue(any("charts" in w for w in warnings) and any("images" in w for w in warnings))

    def test_chart_becomes_a_replaceWith_rule_with_escaped_svg(self):
        _, _, found = self.rules(visuals())
        imp = found["imp"]
        self.assertEqual((imp["selector"], imp["action"]), ("#chart-imp", "replaceWith"))
        self.assertIn("Impressions &lt;by&gt; month", imp["value"])
        self.assertNotIn("<by>", imp["value"])
        self.assertTrue(found["mix"]["value"].startswith("<svg"))  # app-map entry given as a bare string

    def test_kpi_is_derived_from_the_chart_so_they_tie_out(self):
        _, _, found = self.rules(visuals())
        self.assertEqual(found["k1"]["value"], "4,500")
        self.assertEqual(found["k1"]["action"], "text")

    def test_kpi_pointing_at_a_missing_chart_fails_the_build(self):
        d = visuals(kpis=[{"id": "k2", "target": "totalImpressions", "derivedFrom": {"chart": "nope", "agg": "sum"}}])
        with self.assertRaises(op.PayloadError):
            op.build(d, APP_MAP)

    def test_series_length_mismatch_fails_the_build(self):
        d = visuals(charts=[{"id": "imp", "target": "impressions", "type": "bar", "title": "t",
                             "categories": ["a", "b"], "series": [{"name": "s", "values": [1]}]}], kpis=[])
        with self.assertRaises(op.PayloadError):
            op.build(d, APP_MAP)

    def test_missing_selector_is_skipped_loudly(self):
        d = visuals(charts=[{"id": "x", "target": "unknown", "type": "bar", "title": "t", "categories": ["a"],
                             "series": [{"name": "s", "values": [1]}]}], kpis=[])
        _, warnings, found = self.rules(d)
        self.assertNotIn("x", found)
        self.assertTrue(any("charts.unknown" in w for w in warnings))

    def test_image_monogram_is_a_data_uri_and_hide_has_no_value(self):
        d = visuals(images=[{"id": "i1", "screen": "publishingCalendar", "target": "thumb", "action": "swap", "src": "monogram"},
                            {"id": "i2", "screen": "publishingCalendar", "target": "thumb", "action": "hide"}])
        _, _, found = self.rules(d)
        self.assertTrue(found["i1"]["value"].startswith("data:image/svg+xml;base64,"))
        self.assertEqual(found["i2"]["action"], "hide")

    def test_every_chart_type_draws(self):
        for kind in ("bar", "line", "donut"):
            d = visuals(charts=[{"id": "c", "target": "impressions", "type": kind, "title": "t", "categories": ["a", "b"],
                                 "series": [{"name": "s1", "values": [3, 5]}, {"name": "s2", "values": [2, 4]}]}], kpis=[])
            _, _, found = self.rules(d)
            self.assertIn("</svg>", found["c"]["value"])

    def test_built_visual_payload_passes_its_own_check(self):
        payload, _, _ = self.rules(visuals())
        self.assertEqual(op.check(payload, visuals()), [])


class VisualCheckTests(unittest.TestCase):
    def rule(self, **kw):
        return {"textRules": [], "selectorRules": [dict({"selector": ".c", "action": "replaceWith", "value": "<svg/>"}, **kw)]}

    def test_script_and_event_handlers_are_rejected(self):
        self.assertTrue(op.check(self.rule(value="<svg><script>x</script></svg>")))
        self.assertTrue(op.check(self.rule(value='<svg onload="x()"/>')))

    def test_external_urls_are_rejected_but_the_svg_namespace_is_fine(self):
        self.assertTrue(op.check(self.rule(value='<img src="https://cdn.example/a.png">')))
        self.assertEqual(op.check(self.rule(value='<svg xmlns="http://www.w3.org/2000/svg"/>')), [])

    def test_image_rules_need_a_data_uri(self):
        self.assertTrue(op.check(self.rule(action="image", value="https://cdn.example/a.png")))
        self.assertTrue(op.check(self.rule(action="image", value="data:text/html;base64,AA")))
        self.assertEqual(op.check(self.rule(action="image", value="data:image/png;base64,AA")), [])


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
