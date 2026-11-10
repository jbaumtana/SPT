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
  overlayVisuals {charts, images}        both off unless true; mirrors plan.md overlay_visuals
  charts[]  {id, screen, target, type: bar|line|donut, title, categories, series: [{name, values}]}
            replaces the chart at app-map screens[screen].charts[target] with a drawn SVG
  kpis[]    {id, screen, target, derivedFrom: {chart, agg: sum|last|first|max|avg, series?}, format?}
            or {value}; the number comes from the same chart data so tiles and chart tie out
  images[]  {id, screen, target, action: swap|hide, src: "monogram" | data URI, scope?}
"""

import argparse
import base64
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


# ---- Visuals: charts, KPI tiles, images (reports and thumbnails) ----

SVG_W, SVG_H = 640, 280


def _tints(primary, accent):
    return [primary, accent, "#6B7B8C", "#9FB3C8", "#3D4F5F", "#C5D3E0"]


def _fmt_number(v, fmt=None):
    if fmt == "pct1":
        return f"{v:.1f}%"
    if fmt == "compact" and abs(v) >= 1000:
        return f"{round(v / 1000, 2):g}K"
    return f"{round(v):,}"


def _agg(values, how):
    if how == "sum":
        return sum(values)
    if how == "last":
        return values[-1]
    if how == "first":
        return values[0]
    if how == "max":
        return max(values)
    if how == "avg":
        return sum(values) / len(values)
    raise PayloadError(f"unknown agg {how}")


def kpi_value(kpi, charts_by_id):
    if "value" in kpi:
        return str(kpi["value"])
    d = kpi["derivedFrom"]
    chart = charts_by_id.get(d["chart"])
    if not chart:
        raise PayloadError(f"kpi {kpi['id']} reads chart {d['chart']}, which isn't in charts[]")
    series = chart["series"][d.get("series", 0)]
    return _fmt_number(_agg(series["values"], d["agg"]), kpi.get("format"))


def chart_svg(chart, colors):
    """Draw one chart as inline SVG. Text inherits the page font and colour; series use the brand colours."""
    esc = html.escape
    title = esc(chart.get("title", ""))
    cats, series = chart["categories"], chart["series"]
    for s_ in series:
        if len(s_["values"]) != len(cats):
            raise PayloadError(f"chart {chart['id']}: series {s_['name']} has {len(s_['values'])} values for {len(cats)} categories")
    pal = _tints(*colors)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SVG_W} {SVG_H}" role="img" '
           f'style="width:100%;height:auto;display:block;font-family:inherit;font-size:12px;color:inherit" '
           f'aria-label="{title}"><title>{title}</title>']
    kind = chart["type"]
    left, right, top, bottom = 48, 16, 16, 44 if len(series) > 1 else 30
    pw, ph = SVG_W - left - right, SVG_H - top - bottom
    if kind == "donut":
        vals = series[0]["values"]
        total = sum(vals) or 1
        cx, cy, r, w = 110, SVG_H / 2, 90, 34
        import math
        angle = -math.pi / 2
        for i, v in enumerate(vals):
            a2 = angle + 2 * math.pi * v / total
            x1, y1, x2, y2 = cx + r * math.cos(angle), cy + r * math.sin(angle), cx + r * math.cos(a2), cy + r * math.sin(a2)
            ri = r - w
            xi1, yi1, xi2, yi2 = cx + ri * math.cos(a2), cy + ri * math.sin(a2), cx + ri * math.cos(angle), cy + ri * math.sin(angle)
            big = 1 if a2 - angle > math.pi else 0
            out.append(f'<path d="M{x1:.1f} {y1:.1f}A{r} {r} 0 {big} 1 {x2:.1f} {y2:.1f}L{xi1:.1f} {yi1:.1f}'
                       f'A{ri} {ri} 0 {big} 0 {xi2:.1f} {yi2:.1f}Z" fill="{pal[i % len(pal)]}"/>')
            angle = a2
        for i, (c, v) in enumerate(zip(cats, vals)):
            y = 70 + i * 24
            out.append(f'<rect x="250" y="{y - 10}" width="12" height="12" rx="2" fill="{pal[i % len(pal)]}"/>'
                       f'<text x="270" y="{y}" fill="currentColor">{esc(c)}</text>'
                       f'<text x="{SVG_W - 16}" y="{y}" text-anchor="end" fill="currentColor">{esc(_fmt_number(v / total * 100, "pct1"))}</text>')
    else:
        vmax = max(max(s_["values"]) for s_ in series) or 1
        step = 10 ** (len(str(int(vmax))) - 1)
        top_v = -(-vmax // step) * step
        for g in range(5):
            y = top + ph - ph * g / 4
            out.append(f'<line x1="{left}" x2="{SVG_W - right}" y1="{y:.1f}" y2="{y:.1f}" stroke="currentColor" stroke-opacity=".15"/>'
                       f'<text x="{left - 8}" y="{y + 4:.1f}" text-anchor="end" fill="currentColor" fill-opacity=".7">{esc(_fmt_number(top_v * g / 4, "compact"))}</text>')
        n = len(cats)
        slot = pw / n
        for i, c in enumerate(cats):
            out.append(f'<text x="{left + slot * (i + .5):.1f}" y="{top + ph + 18}" text-anchor="middle" fill="currentColor" fill-opacity=".7">{esc(c)}</text>')
        if kind == "bar":
            bw = slot * 0.7 / len(series)
            for si, s_ in enumerate(series):
                for i, v in enumerate(s_["values"]):
                    h = ph * v / top_v
                    x = left + slot * i + slot * 0.15 + bw * si
                    out.append(f'<rect x="{x:.1f}" y="{top + ph - h:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="2" fill="{pal[si % len(pal)]}"/>')
        elif kind == "line":
            for si, s_ in enumerate(series):
                pts = " ".join(f"{left + slot * (i + .5):.1f},{top + ph - ph * v / top_v:.1f}" for i, v in enumerate(s_["values"]))
                out.append(f'<polyline points="{pts}" fill="none" stroke="{pal[si % len(pal)]}" stroke-width="2.5" stroke-linejoin="round"/>')
        else:
            raise PayloadError(f"chart {chart['id']}: unknown type {kind}")
        if len(series) > 1:
            x = left
            for si, s_ in enumerate(series):
                out.append(f'<rect x="{x}" y="{SVG_H - 14}" width="10" height="10" rx="2" fill="{pal[si % len(pal)]}"/>'
                           f'<text x="{x + 16}" y="{SVG_H - 5}" fill="currentColor">{esc(s_["name"])}</text>')
                x += 24 + 7 * len(s_["name"])
    out.append("</svg>")
    return "".join(out)


def monogram_uri(initials, color):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96"><rect width="96" height="96" fill="{html.escape(color)}"/>'
           f'<text x="48" y="48" text-anchor="middle" dominant-baseline="central" font-family="sans-serif" font-size="40" '
           f'font-weight="600" fill="#fff">{html.escape(initials)}</text></svg>')
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def _lookup(screens, screen, bucket, key, what, warnings):
    entry = screens.get(screen, {}).get(bucket, {}).get(key)
    if not entry:
        warnings.append(f"{what} needs app-map screens.{screen}.{bucket}.{key}, which isn't recorded yet (browser pass, docs/browser-pass.md): skipped")
        return None
    return entry if isinstance(entry, str) else entry["selector"]


def visual_rules(data, app_map):
    """Selector rules for charts, KPI tiles and images. Both groups are off unless plan.md switched them on."""
    warnings, rules = [], []
    screens = app_map["screens"]
    opts = data.get("overlayVisuals") or {}
    colors = (data["workspace"]["brandColors"]["primary"], data["workspace"]["brandColors"]["accent"])
    charts = data.get("charts", [])
    if charts and not opts.get("charts"):
        warnings.append("charts[] present but overlayVisuals.charts is off: charts and KPI tiles skipped")
    if opts.get("charts"):
        by_id = {c["id"]: c for c in charts}
        for c in charts:
            sel = _lookup(screens, c.get("screen", "reports"), "charts", c["target"], f"chart {c['id']}", warnings)
            if sel:
                rules.append({"selector": sel, "action": "replaceWith", "id": c["id"], "value": chart_svg(c, colors), "_chart": c["id"]})
        for k in data.get("kpis", []):
            sel = _lookup(screens, k.get("screen", "reports"), "kpis", k["target"], f"kpi {k['id']}", warnings)
            if sel:
                rules.append({"selector": sel, "action": "text", "value": kpi_value(k, by_id), "_kpi": k["id"]})
    images = data.get("images", [])
    if images and not opts.get("images"):
        warnings.append("images[] present but overlayVisuals.images is off: image rules skipped")
    if opts.get("images"):
        name = data["workspace"].get("name") or data["workspace"].get("brandName") or ""
        for im in images:
            sel = _lookup(screens, im["screen"], "images", im["target"], f"image {im['id']}", warnings)
            if not sel:
                continue
            if im["action"] == "hide":
                rule = {"selector": sel, "action": "hide", "value": ""}
            else:
                src = im["src"]
                if src == "monogram":
                    initials = im.get("initials") or "".join(w[0] for w in name.split()[:2]).upper() or "SM"
                    src = monogram_uri(initials, colors[0])
                rule = {"selector": sel, "action": "image", "value": src}
            if im.get("scope"):
                rule["scope"] = im["scope"]
            rule["_image"] = im["id"]
            rules.append(rule)
    return rules, warnings


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

    vrules, vwarnings = visual_rules(data, app_map)
    rules += vrules
    warnings += vwarnings

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
    for r in payload.get("selectorRules", []):
        v = r.get("value")
        if r.get("action") == "replaceWith":
            body = re.sub(r'xmlns="http://www\.w3\.org/2000/svg"', "", v)
            if re.search(r"<script|<iframe|\son\w+\s*=|javascript:", body, re.I):
                problems.append(f"replaceWith rule on {r['selector']} contains script or an event handler")
            if re.search(r"https?://", body, re.I):
                problems.append(f"replaceWith rule on {r['selector']} loads an external URL; inline it")
        if r.get("action") == "image":
            if not (isinstance(v, str) and re.match(r"data:image/(png|jpeg|gif|webp|svg\+xml)[;,]", v)):
                problems.append(f"image rule on {r['selector']} must be a data:image/ URI (a hosted URL can be blocked or change)")
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
