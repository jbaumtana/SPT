"""Validate a demo data pack (docs/workstreams/data-generation.md).

  python3 tools/check_pack.py context/packs/healthcare/demo-data.json
  python3 tools/check_pack.py runs/<run>/data-pack/demo-data.json --prospect "Acme Health"

Checks, in order: schema, references, tenant IDs, rules from CLAUDE.md (no real
names, no prospect name in public posts, no claims, no private details),
sentiment mix, then the overlay payload build and check. Exit 1 on any error.
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schemas" / "demo-data.schema.json"
BLOCKLIST = ROOT / "context" / "packs" / "blocklist.txt"
TENANT_INDEX = ROOT / "context" / "tenant-index.md"
CONFIG = ROOT / "config.json"
PERSONA_HANDLES = {  # context/tenant-baseline.md, seeding personas
    "emily": {"@emilynmarketing"},
    "liam": {"@dublindrforkids"},
    "arletta": {"drarlettabrown", "@arlettabrown353"},
}
LIMITS = {"x": 280, "threads": 500, "bluesky": 300, "instagram": 2200, "linkedin": 3000}
CLAIMS = re.compile(r"\b(cures?|cured|guarantee[sd]?|clinically proven|proven to|reduces? (your )?risk|prevents?|"
                    r"best in class|#1|number one|results? (guaranteed|proven))\b|\d\s?%", re.I)
PRIVATE = [  # things that look like private details or contact data
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "SSN-like number"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", re.I), "email address"),
    (re.compile(r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b"), "phone number"),
    (re.compile(r"\b(MRN|DOB|date of birth)\b", re.I), "record number or birth date"),
]
PLACEHOLDER = re.compile(r"\[[^\]]+\]|\{[^}]+\}|\bTODO\b|lorem ipsum", re.I)


def blocklist():
    terms = []
    for line in BLOCKLIST.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            terms.append(line)
    return terms


def has_term(text, term):
    return re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text, re.I) is not None


def has_id(text, n):
    return re.search(rf"(?<!\d){n}(?!\d)", text) is not None


def texts(d):
    """Every (location, text) the audience could read."""
    for p in d["posts"]:
        yield f"post {p['id']}", p["caption"]
    for s in d.get("seasonalLibrary", []):
        yield f"seasonal {s['id']}", s["caption"]
    for m in d["inbox"]:
        yield f"inbox {m['id']}", m["text"] + " " + m.get("suggestedReply", "")
    for c in d["campaigns"]:
        yield f"campaign {c['id']}", c["name"]
    for l in d.get("listening", []):
        yield f"listening {l['topic']}", l["talkingPoint"]
    for r in d.get("reportFraming", []):
        yield f"report {r['report']}", r["framing"]


def check(d, prospect=None, tenant_text="", ui_text="", schema=None, terms=None, blocked_tags=()):
    errs = []
    terms = blocklist() if terms is None else terms
    meta = d.get("meta", {})
    try:
        import jsonschema
        for e in jsonschema.Draft202012Validator(schema).iter_errors(d):
            errs.append(f"schema: {'/'.join(map(str, e.path)) or '(root)'}: {e.message}")
        if errs:
            return errs  # later checks assume the shape
    except ImportError:
        errs.append("warning: jsonschema is not installed, so the schema check was skipped (pip install jsonschema)")

    # Track rules
    if meta["track"] == "industry" and meta["prospect"] is not None:
        errs.append("industry pack has a prospect name; industry packs are prospect-neutral")
    if meta["track"] == "customer" and not meta.get("planPath"):
        errs.append("customer pack has no planPath; no plan, no build (CLAUDE.md rule 1)")

    # Duplicate IDs and references
    for key in ("profiles", "campaigns", "posts", "users", "inbox"):
        ids = [x["id"] for x in d[key]]
        errs += [f"duplicate {key} id {i}" for i in sorted({i for i in ids if ids.count(i) > 1})]
    campaigns = {c["id"] for c in d["campaigns"]}
    posts = {p["id"]: p for p in d["posts"]}
    users = {u["id"] for u in d["users"]}
    for p in d["posts"]:
        if p["campaignId"] not in campaigns:
            errs.append(f"post {p['id']}: unknown campaign {p['campaignId']}")
        if not any(pr["network"] == p["network"] for pr in d["profiles"]):
            errs.append(f"post {p['id']}: no profile on {p['network']}")
        if len(p["caption"]) > LIMITS[p["network"]]:
            errs.append(f"post {p['id']}: caption is {len(p['caption'])} characters, over the {p['network']} limit")
        if p["pinDate"] and not p["dateSensitive"]:
            errs.append(f"post {p['id']}: has a pinDate but dateSensitive is false")
        if meta["track"] == "industry" and (p["pinDate"] or p["dateSensitive"]):
            errs.append(f"post {p['id']}: dated copy belongs in seasonalLibrary, not an industry pack's posts")
        if p["visibility"] == "public" and not meta.get("allowPublic"):
            errs.append(f"post {p['id']}: visibility is public but meta.allowPublic is not set by an approved plan")
    for a in d.get("approvals", []):
        if a["postId"] not in posts:
            errs.append(f"approval: unknown post {a['postId']}")
        elif posts[a["postId"]]["status"] != "pending_approval":
            errs.append(f"approval: post {a['postId']} is not pending_approval")
        for who in [a["requestedBy"]] + [s["approver"] for s in a["steps"]]:
            if who not in users:
                errs.append(f"approval: unknown user {who}")
        if not any("compliance" in s["name"].lower() for s in a["steps"]):
            errs.append("approval workflow has no compliance step (healthcare landmine, and good practice elsewhere)")

    # Tenant IDs (no made-up profiles or tags) and the blocked tag
    for pr in d["profiles"]:
        if not has_id(tenant_text, pr["sproutProfileId"]):
            errs.append(f"profile {pr['id']}: ID {pr['sproutProfileId']} is not in context/tenant-index.md")
    for c in d["campaigns"]:
        t = c["tenantTagId"]
        if t is not None and (t in blocked_tags or not has_id(tenant_text, t)):
            errs.append(f"campaign {c['id']}: tag {t} is blocked or not in context/tenant-index.md")

    # Inbox: only our personas, and the handle has to be theirs
    for m in d["inbox"]:
        if m["senderHandle"].lower() not in PERSONA_HANDLES[m["senderPersona"]]:
            errs.append(f"inbox {m['id']}: {m['senderHandle']} is not a seeding handle for {m['senderPersona']}")
        if len(m["text"]) > LIMITS[m["network"]]:
            errs.append(f"inbox {m['id']}: text is over the {m['network']} limit")
    # Sentiment mix against the declared mix (within 5 points)
    n = len(d["inbox"]) or 1
    for s, want in meta["sentimentMix"].items():
        got = 100 * sum(m["sentiment"] == s for m in d["inbox"]) / n
        if abs(got - want) > 5:
            errs.append(f"sentiment: declared {want}% {s}, inbox has {got:.0f}%")
    if sum(meta["sentimentMix"].values()) != 100:
        errs.append("sentimentMix does not add up to 100")

    # Content rules
    for where, text in texts(d):
        for t in terms:
            if has_term(text, t):
                errs.append(f"{where}: contains blocklisted real name '{t}'")
        if prospect and has_term(text, prospect):
            public = where.startswith("post ") and posts[where.split()[1]]["visibility"] == "public"
            if public or where.startswith(("seasonal", "inbox")):
                errs.append(f"{where}: prospect name in public-facing copy (CLAUDE.md rule 3)")
        if CLAIMS.search(text):
            errs.append(f"{where}: reads like an outcome claim or a number ('{CLAIMS.search(text).group(0)}')")
        for rx, label in PRIVATE:
            if rx.search(text):
                errs.append(f"{where}: contains a {label}")
        if PLACEHOLDER.search(text):
            errs.append(f"{where}: has a placeholder")
        if re.search(r"\b20[12]\d\b", text):
            errs.append(f"{where}: contains a year, which will go stale")
    if prospect is None and meta["track"] == "customer":
        errs.append("customer pack: pass --prospect so the public-copy check can run")

    # Overlay payload
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import overlay_payload as op
    try:
        payload, _ = op.build(d, json.loads(op.APP_MAP.read_text()))
        errs += [f"overlay: {p}" for p in op.check(payload, d, ui_text or None)]
    except (op.PayloadError, KeyError, StopIteration) as e:
        errs.append(f"overlay: {type(e).__name__}: {e}")
    return errs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("data")
    ap.add_argument("--prospect", help="prospect name, for the public-copy check on customer packs")
    args = ap.parse_args(argv)
    d = json.loads(Path(args.data).read_text())
    ui = (ROOT / "context" / "tenant-index-ui.md")
    errs = check(d, args.prospect or d.get("meta", {}).get("prospect"),
                 TENANT_INDEX.read_text(), ui.read_text() if ui.exists() else "",
                 json.loads(SCHEMA.read_text()), blocked_tags=set(json.loads(CONFIG.read_text()).get("blocked_tag_ids", [])))
    hard = [e for e in errs if not e.startswith("warning:")]
    print("\n".join(errs) if errs else "OK")
    if not hard:
        print(f"{len(d['posts'])} posts, {len(d['inbox'])} inbox messages, {len(d['campaigns'])} campaigns checked")
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
