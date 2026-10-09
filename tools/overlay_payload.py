"""Build and check overlay payloads (docs/overlay-fix-plan.md, Phase 3).

  python3 tools/overlay_payload.py build runs/<run>/data-pack/demo-data.json   # writes overlay-payload.json beside it
  python3 tools/overlay_payload.py check runs/<run>/data-pack/overlay-payload.json --data runs/<run>/data-pack/demo-data.json

Inputs: the run's demo-data.json, context/click-paths/app-map.json (selectors),
and context/tenant-index-ui.md (seed labels for the coverage check).

demo-data.json fields this reads, beyond the data-pack schema:
  posts[].pinDate "YYYY-MM-DD" | null    the caption only makes sense on that day
  posts[].dateSensitive true | false     wording tied to a date ("starts today")
  campaigns[].replaces [seed labels]     tenant campaign names this campaign covers (D2)
  relabels [[find, replace], ...]        brand, handle, topic, workflow, team, queue names
  outOfClickPath [labels]                seed labels deliberately left alone (D4)
"""

import argparse
import datetime as dt
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_MAP = ROOT / "context" / "click-paths" / "app-map.json"
UI_INDEX = ROOT / "context" / "tenant-index-ui.md"


class PayloadError(Exception):
    pass


def _date_attr(iso, fmt):
    d = dt.date.fromisoformat(iso)
    if fmt != "MM/DD/YYYY":
        raise PayloadError(f"unsupported date format {fmt}")
    return d.strftime("%m/%d/%Y")


def build(data, app_map):
    """Return (payload, warnings)."""
    warnings = []
    screens = app_map["screens"]
    cal, appr, comp = screens["publishingCalendar"], screens["approvals"], screens["composer"]

    # Text rules: hand relabels plus campaign labels generated from the data (D2), longest first.
    pairs = [tuple(p) for p in data.get("relabels", [])]
    for c in data.get("campaigns", []):
        pairs += [(seed, c["name"]) for seed in c.get("replaces", [])]
    seen, text_rules = set(), []
    for find, repl in pairs:
        if find.lower() in seen or find == repl:
            continue
        seen.add(find.lower())
        text_rules.append({"find": find, "replace": repl, "caseAware": True})
    text_rules.sort(key=lambda r: -len(r["find"]))

    posts = data.get("posts", [])
    approval_ids = {a["postId"] for a in data.get("approvals", [])}
    scheduled = [p for p in posts if p["status"] == "scheduled" and p["id"] not in approval_ids]
    rotating = [p["caption"] for p in scheduled if not p.get("dateSensitive") and not p.get("pinDate")]
    if not rotating:
        raise PayloadError("no date-neutral captions to rotate")

    caption_sel = cal.get("wholeCaption")
    if not caption_sel:
        caption_sel = cal["selectors"]["calendarCaption"]
        warnings.append("app-map has no calendar wholeCaption selector; using the per-piece selector (S1)")
    rules = []
    # D1: pinned captions become scoped rules; date-sensitive ones never rotate.
    for p in scheduled:
        if p.get("pinDate"):
            if not cal.get("dateAttr"):
                raise PayloadError("pinned captions need publishingCalendar.dateAttr in app-map")
            scope = f"[{cal['dateAttr']}='{_date_attr(p['pinDate'], cal.get('dateFormat', 'MM/DD/YYYY'))}']"
            rules.append({"selector": caption_sel, "action": "text", "scope": scope, "perScope": 1,
                          "value": p["caption"], "_post": p["id"]})
        elif p.get("dateSensitive"):
            warnings.append(f"{p['id']} is date-sensitive with no pinDate, so it's left out of the overlay")
    general = {"selector": caption_sel, "action": "text", "value": rotating}
    if cal.get("postKeyAttr"):
        general["keyAttr"] = cal["postKeyAttr"]  # E3: same post, same caption
    rules.append(general)

    by_id = {p["id"]: p for p in posts}
    for a in data.get("approvals", []):
        draft = by_id[a["postId"]]
        rules.append({"selector": appr["selectors"]["approvalCaption"], "action": "text",
                      "value": [draft["caption"]] + rotating[:5], "_post": draft["id"]})
        author_sel = appr["selectors"].get("authorName")
        if author_sel:
            persona = next(u for u in data["users"] if u["id"] == a["requestedBy"])
            rules.append({"selector": author_sel, "action": "text", "value": persona["name"]})  # D3: by selector only
        else:
            warnings.append("no approvals.authorName selector yet (S4): the approval author line still shows a real user")
        break  # one scripted approval card per run

    avatar = comp["selectors"].get("profileAvatar")
    logo = data.get("workspace", {}).get("logoDataUri")
    if avatar and logo:
        rules.append({"selector": avatar, "action": "attr", "attr": "src", "value": logo})

    payload = {
        "_note": data.get("_note", "Illustrative sample data."),
        "_generatedBy": "tools/overlay_payload.py",
        "textRules": text_rules,
        "selectorRules": rules,
        "cssVars": {"--brand-primary": data["workspace"]["brandColors"]["primary"],
                    "--brand-accent": data["workspace"]["brandColors"]["accent"]},
        "avoidSelectors": ["script", "style", "textarea", "input", "[contenteditable]"],
        "injectCss": "",
    }
    return payload, warnings


def seed_labels(ui_text):
    """Campaign, workflow, and topic labels the browser pass saw on screen."""
    labels = set()
    for line in ui_text.splitlines():
        m = re.search(r"\*\*Campaigns shown:\*\*\s*(.+?)\.?$", line) or re.search(r"Campaigns on items:\s*(.+?)\.?$", line)
        if m:
            labels |= {s.strip() for s in re.split(r",(?![^,]*Illuminated)", m.group(1)) if s.strip()}
        for w in re.findall(r'"([^"]+?) - Step \d+"', line):
            labels.add(w)
        m = re.match(r"\|\s*([^|]+?)\s*\|\s*(Brand Health|Industry Insights|Competitive Analysis|Custom Topic)\s*\|", line)
        if m:
            labels.add(m.group(1))
    return labels


def check(payload, data=None, ui_text=None):
    """Return a list of problems (empty means OK). Implements D6, plus D1 and D4 when data is given."""
    problems = []
    finds = [r["find"] for r in payload.get("textRules", [])]
    for i, a in enumerate(finds):  # shorter find listed before a longer one that contains it
        for b in finds[i + 1:]:
            if a.lower() in b.lower() and a.lower() != b.lower():
                problems.append(f'text rule "{a}" comes before "{b}", which contains it')
    for r in payload.get("selectorRules", []):
        vals = r["value"] if isinstance(r["value"], list) else [r["value"]]
        if r.get("action") == "html":
            for v in vals:
                if v != html.escape(html.unescape(v), quote=False) and not r.get("allowMarkup"):
                    problems.append(f"html rule on {r['selector']} has unescaped markup")
    if data:
        sensitive = {p["caption"]: p["id"] for p in data.get("posts", []) if p.get("dateSensitive") or p.get("pinDate")}
        approval_posts = {a["postId"] for a in data.get("approvals", [])}
        for r in payload.get("selectorRules", []):
            vals = r["value"] if isinstance(r["value"], list) else [r["value"]]
            for v in vals:
                pid = sensitive.get(v)
                if pid and pid not in approval_posts and not (r.get("scope") and not isinstance(r["value"], list)):
                    problems.append(f"date-sensitive caption {pid} is in an unpinned rule on {r['selector']}")
    if data and ui_text:
        covered = [f.lower() for f in finds]
        skip = {s.lower() for s in data.get("outOfClickPath", [])}
        for label in sorted(seed_labels(ui_text)):
            if label.lower() in skip:
                continue
            if not any(f in label.lower() for f in covered):
                problems.append(f'seed label "{label}" has no rule and isn\'t listed in outOfClickPath')
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("data")
    c = sub.add_parser("check")
    c.add_argument("payload")
    c.add_argument("--data")
    args = ap.parse_args(argv)
    ui_text = UI_INDEX.read_text() if UI_INDEX.exists() else None
    if args.cmd == "build":
        data = json.loads(Path(args.data).read_text())
        payload, warnings = build(data, json.loads(APP_MAP.read_text()))
        problems = check(payload, data, ui_text)
        for w in warnings:
            print(f"warning: {w}")
        if problems:
            print("\n".join(f"error: {p}" for p in problems))
            return 1
        out = Path(args.data).with_name("overlay-payload.json")
        out.write_text(json.dumps(payload, indent=2) + "\n")
        print(f"Wrote {out}: {len(payload['textRules'])} text rules, {len(payload['selectorRules'])} selector rules")
        return 0
    payload = json.loads(Path(args.payload).read_text())
    data = json.loads(Path(args.data).read_text()) if args.data else None
    problems = check(payload, data, ui_text)
    print("\n".join(problems) if problems else "OK")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
