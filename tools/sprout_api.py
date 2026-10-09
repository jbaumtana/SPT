"""Thin Sprout API client, locked to the demo tenant.

What it will do (CLAUDE.md rules 1, 2, 5, 6):
- Talk to the one customer in config.json only. Any other customer ID is refused.
- Send only the calls on ALLOWED: reads, plus creating drafts and uploading
  media for them. There's no delete, update, or publish call to send, and
  those stay browser-only even if the API adds them.
- Before every write, check the run's plan is approved and log the write to
  runs/<run>/manifest.json. After it, record every publishing_post_id (fan-out)
  and any profile Sprout silently dropped.
- Refuse Reddit profiles, profiles outside the post's group, archived tags,
  tags from another group, and tags on BLOCKED_TAG_IDS.
- Stay under 60 requests a minute.

Credentials: none here. In the cloud environment the proxy adds them to every
request to *.sproutsocial.com. Elsewhere, set SPROUT_API_TOKEN.

CLI:
  python3 tools/sprout_api.py check
  python3 tools/sprout_api.py index                      # writes context/tenant-index.md
  python3 tools/sprout_api.py inventory --out before.json [--run runs/<run>] [--days 14]
  python3 tools/sprout_api.py diff before.json after.json
  python3 tools/sprout_api.py drafts --run runs/<run> --file drafts.json
"""

import argparse
import collections
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

# Tenant settings live in config.json at the repo (plugin) root; SPT_CONFIG overrides the path.
CONFIG = json.loads(Path(os.environ.get("SPT_CONFIG") or Path(__file__).resolve().parent.parent / "config.json").read_text())
CUSTOMER_ID = int(CONFIG["customer_id"])
DEMO_BRAND_GROUP_ID = int(CONFIG["demo_brand_group_id"])
BASE_URL = "https://api.sproutsocial.com"

# Active tag named after a real health system, left from an earlier demo.
# Not ours to remove, so never apply it (context/tenant-baseline.md).
BLOCKED_TAG_IDS = {int(t) for t in CONFIG.get("blocked_tag_ids", [])}

# Reddit is browser-only (CLAUDE.md rule 5). Matched on network_type prefix.
BROWSER_ONLY_NETWORK_PREFIXES = ("reddit",)

# The Messages endpoint rejects these profile types (no API data, docs/api-coverage.md).
NO_MESSAGES_NETWORK_PREFIXES = ("reddit", "yelp", "trustpilot", "tripadvisor", "glassdoor")

# Seeding personas (context/tenant-baseline.md), matched on from.screen_name.
PERSONA_SCREEN_NAMES = {s.lower() for s in CONFIG.get("persona_screen_names", [])}

_CID = str(CUSTOMER_ID)
ALLOWED = [
    ("GET", r"/v1/metadata/client"),
    ("GET", rf"/v1/{_CID}/metadata/customer(/(tags|groups|users|topics|teams|queues))?"),
    ("POST", rf"/v1/{_CID}/analytics/(profiles|posts)"),
    ("POST", rf"/v1/{_CID}/messages"),
    ("POST", rf"/v1/{_CID}/listening/topics/[0-9a-f-]+/(messages|metrics)"),
    ("POST", rf"/v1/{_CID}/cases/filter"),
    ("GET", rf"/v1/{_CID}/publishing/posts/\d+"),
    ("POST", rf"/v1/{_CID}/publishing/posts"),  # drafts only, see create_draft
    ("POST", rf"/v1/{_CID}/media/"),
]
WRITE_PATHS = (rf"/v1/{_CID}/publishing/posts", rf"/v1/{_CID}/media/")

MESSAGE_FIELDS = ["created_time", "post_type", "from.guid", "from.name", "from.screen_name", "customer_profile_id"]


class GuardrailError(Exception):
    """A request the rules don't allow. Never retried, never worked around."""


class ApiError(Exception):
    def __init__(self, status, body):
        super().__init__(f"HTTP {status}: {body[:500]}")
        self.status = status
        self.body = body


def _now():
    return dt.datetime.now(dt.timezone.utc)


def _iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def _filter_time(t):
    # Filters reject a trailing Z ("created_time.in(...)" is read as UTC).
    return t.strftime("%Y-%m-%dT%H:%M:%S")


def urllib_transport(method, url, body, headers):
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


class RateLimiter:
    def __init__(self, per_minute=60, clock=time.monotonic, sleep=time.sleep):
        self.per_minute, self.clock, self.sleep = per_minute, clock, sleep
        self.sent = collections.deque()

    def wait(self):
        while True:
            now = self.clock()
            while self.sent and now - self.sent[0] >= 60:
                self.sent.popleft()
            if len(self.sent) < self.per_minute:
                self.sent.append(now)
                return
            self.sleep(60 - (now - self.sent[0]) + 0.05)


class SproutClient:
    def __init__(self, customer_id=CUSTOMER_ID, transport=urllib_transport, limiter=None):
        if int(customer_id) != CUSTOMER_ID:
            raise GuardrailError(f"customer {customer_id} is not the demo tenant ({CUSTOMER_ID})")
        self.transport = transport
        self.limiter = limiter or RateLimiter()
        self._cache = {}

    # -- transport -------------------------------------------------------

    def request(self, method, path, json_body=None, form=None):
        if not any(m == method and re.fullmatch(p, path) for m, p in ALLOWED):
            raise GuardrailError(f"{method} {path} isn't on the allowed list")
        headers = {"Accept": "application/json"}
        token = os.environ.get("SPROUT_API_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        body = None
        if json_body is not None:
            body = json.dumps(json_body).encode()
            headers["Content-Type"] = "application/json"
        elif form is not None:
            boundary = uuid.uuid4().hex
            parts = [f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n' for k, v in form.items()]
            body = ("".join(parts) + f"--{boundary}--\r\n").encode()
            headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        self.limiter.wait()
        status, raw = self.transport(method, BASE_URL + path, body, headers)
        text = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else raw
        if status != 200:
            raise ApiError(status, text)
        return json.loads(text)

    def _cached(self, path):
        if path not in self._cache:
            self._cache[path] = self.request("GET", path)["data"]
        return self._cache[path]

    # -- reads -----------------------------------------------------------

    def verify_tenant(self):
        """The token must see the demo tenant. Returns every customer it sees."""
        customers = self.request("GET", "/v1/metadata/client")["data"]
        if CUSTOMER_ID not in {int(c["customer_id"]) for c in customers}:
            raise GuardrailError(f"token can't see the demo tenant {CUSTOMER_ID}: {customers}")
        return customers

    def metadata(self, kind=""):
        return self._cached(f"/v1/{_CID}/metadata/customer" + (f"/{kind}" if kind else ""))

    def profiles(self):
        return {int(p["customer_profile_id"]): p for p in self.metadata()}

    def tags(self):
        return {int(t["tag_id"]): t for t in self.metadata("tags")}

    def messages(self, filters, fields=MESSAGE_FIELDS, max_pages=20):
        out, cursor = [], None
        for _ in range(max_pages):
            body = {"filters": filters, "fields": fields, "limit": 100, "sort": ["created_time:desc"]}
            if cursor:
                body["page_cursor"] = cursor
            resp = self.request("POST", f"/v1/{_CID}/messages", json_body=body)
            out += resp.get("data", [])
            cursor = (resp.get("paging") or {}).get("next_cursor")
            if not cursor:
                break
        return out

    def cases(self, start, end, max_pages=20):
        out, cursor = [], None
        for _ in range(max_pages):
            body = {"filters": [f"latest_activity_time.in({_filter_time(start)}..{_filter_time(end)})"], "limit": 100}
            if cursor:
                body["page_cursor"] = cursor
            resp = self.request("POST", f"/v1/{_CID}/cases/filter", json_body=body)
            out += resp.get("data", [])
            cursor = (resp.get("paging") or {}).get("next_cursor")
            if not cursor:
                break
        return out

    def get_draft(self, publishing_post_id):
        return self.request("GET", f"/v1/{_CID}/publishing/posts/{int(publishing_post_id)}")["data"]

    # -- writes (manifest first) ------------------------------------------

    def upload_media_url(self, manifest, media_url):
        """Link-download upload. Media expires in 24h unless a draft uses it."""
        entry = manifest.begin("media", {"media_url": media_url})
        try:
            data = self.request("POST", f"/v1/{_CID}/media/", form={"media_url": media_url})["data"][0]
        except Exception as e:
            manifest.fail(entry, e)
            raise
        manifest.finish(entry, media_id=data["media_id"], expiration_time=data.get("expiration_time"))
        return data["media_id"]

    def check_draft(self, group_id, profile_ids, scheduled_times=(), tag_ids=()):
        """Every check create_draft runs before writing. Raises GuardrailError."""
        if not profile_ids:
            raise GuardrailError("a draft needs at least one profile")
        profiles = self.profiles()
        for pid in profile_ids:
            p = profiles.get(int(pid))
            if p is None:
                raise GuardrailError(f"profile {pid} isn't in the demo tenant")
            if str(p["network_type"]).lower().startswith(BROWSER_ONLY_NETWORK_PREFIXES):
                raise GuardrailError(f"profile {pid} is {p['network_type']}, which is browser-only")
            if int(group_id) not in [int(g) for g in p.get("groups", [])]:
                raise GuardrailError(f"profile {pid} isn't in group {group_id}; every profile on a post must be")
        tags = self.tags()
        for tid in tag_ids:
            t = tags.get(int(tid))
            if int(tid) in BLOCKED_TAG_IDS:
                raise GuardrailError(f"tag {tid} is blocked (named after a real company)")
            if t is None or not t.get("active"):
                raise GuardrailError(f"tag {tid} doesn't exist or is archived")
            if not t.get("any_group") and int(group_id) not in [int(g) for g in t.get("groups", [])]:
                raise GuardrailError(f"tag {tid} ({t['text']}) belongs to another group")
        now = _now()
        for s in scheduled_times:
            when = dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
            if when <= now + dt.timedelta(minutes=5):
                raise GuardrailError(f"scheduled time {s} must be at least 5 minutes in the future")

    def create_draft(self, manifest, group_id, profile_ids, text, scheduled_times=(), media=(), tag_ids=()):
        """Create a draft (scheduled or not). Never publishes: is_draft is always true."""
        self.check_draft(group_id, profile_ids, scheduled_times, tag_ids)
        body = {"group_id": int(group_id), "customer_profile_ids": [int(p) for p in profile_ids],
                "is_draft": True, "text": text}
        if scheduled_times:
            body["delivery"] = {"scheduled_times": list(scheduled_times), "type": "SCHEDULED"}
        if media:
            body["media"] = list(media)
        if tag_ids:
            body["tag_ids"] = [int(t) for t in tag_ids]
        entry = manifest.begin("draft", body)
        try:
            data = self.request("POST", f"/v1/{_CID}/publishing/posts", json_body=body)["data"]
        except Exception as e:
            manifest.fail(entry, e)
            raise
        posts = []
        for d in data:
            pub = d["internal"]["publishing"]
            posts.append({"publishing_post_id": pub["publishing_post_id"],
                          "customer_profile_id": int(d["customer_profile_id"]),
                          "is_draft": pub.get("is_draft"),
                          "scheduled_time": (pub.get("deliveries") or [{}])[0].get("scheduled_time"),
                          "perma_link": pub.get("perma_link")})
        returned = {p["customer_profile_id"] for p in posts}
        dropped = sorted(set(body["customer_profile_ids"]) - returned)
        manifest.finish(entry, posts=posts, dropped_profile_ids=dropped,
                        undo="Browser: delete each draft (perma_link) from the Publishing calendar")
        if any(p["is_draft"] is False for p in posts):
            raise GuardrailError(f"Sprout returned a non-draft post; check it in the browser now: {posts}")
        return posts, dropped


# -- run folder: approval gate and manifest ---------------------------------

def plan_approved_by(run_dir):
    """The SE name on the plan's 'Approved by' line, or None."""
    plan = Path(run_dir) / "plan.md"
    if not plan.exists():
        return None
    m = re.search(r"\*\*Approved by:\*\*\s*(.+)", plan.read_text())
    name = m.group(1).strip() if m else ""
    if not name or name.startswith("_(") or name.lower() in {"tbd", "todo", "null", "none", "-"}:
        return None
    return name


class Manifest:
    """runs/<run>/manifest.json. Each write is saved before it's sent."""

    def __init__(self, run_dir):
        self.run_dir = Path(run_dir)
        self.approved_by = plan_approved_by(self.run_dir)
        if not self.approved_by:
            raise GuardrailError(f"{self.run_dir / 'plan.md'} has no 'Approved by' name, so no tenant writes")
        self.path = self.run_dir / "manifest.json"
        if self.path.exists():
            self.data = json.loads(self.path.read_text())
        else:
            self.data = {"run_id": self.run_dir.name, "customer_id": CUSTOMER_ID, "entries": []}

    def _save(self):
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self.data, indent=2) + "\n")
        tmp.replace(self.path)

    def begin(self, kind, request):
        entry = {"seq": len(self.data["entries"]) + 1, "kind": kind, "status": "pending",
                 "started_at": _iso(_now()), "approved_by": self.approved_by, "request": request}
        self.data["entries"].append(entry)
        self._save()
        return entry

    def finish(self, entry, **result):
        entry.update(status="done", finished_at=_iso(_now()), **result)
        self._save()

    def fail(self, entry, error):
        # A failed call may still have created something, so keep the entry for the reset checklist.
        entry.update(status="failed", finished_at=_iso(_now()), error=str(error)[:1000])
        self._save()

    def publishing_post_ids(self):
        return [p["publishing_post_id"] for e in self.data["entries"] for p in e.get("posts", [])]


# -- inventory and diff ------------------------------------------------------

def inventory(client, days=14, manifest_path=None):
    end = _now()
    start = end - dt.timedelta(days=days)
    customers = client.verify_tenant()
    inv = {"taken_at": _iso(end), "customer_id": CUSTOMER_ID, "window": [_iso(start), _iso(end)],
           "token_sees_customers": sorted(int(c["customer_id"]) for c in customers)}
    inv["profiles"] = {str(k): {"network_type": v["network_type"], "name": v.get("name"), "groups": v.get("groups")}
                       for k, v in client.profiles().items()}
    inv["groups"] = {str(g["group_id"]): g["name"] for g in client.metadata("groups")}
    inv["tags"] = {str(k): {"text": v["text"], "type": v.get("type"), "active": v.get("active"),
                            "groups": v.get("groups")} for k, v in client.tags().items()}
    inv["topics"] = {t["id"]: t["name"] for t in client.metadata("topics")}
    inv["teams"] = {str(t["id"]): t["name"] for t in client.metadata("teams")}
    inv["queues"] = {str(q["id"]): q["name"] for q in client.metadata("queues")}
    inv["users"] = sorted(str(u["id"]) for u in client.metadata("users"))  # IDs only, no names or emails

    # Inbox: messages from the seeding personas to the demo brand profiles.
    profiles = client.profiles()
    brand_ids = [pid for pid, p in profiles.items()
                 if DEMO_BRAND_GROUP_ID in [int(g) for g in p.get("groups", [])]
                 and not str(p["network_type"]).lower().startswith(NO_MESSAGES_NETWORK_PREFIXES)]
    msgs = client.messages([f"group_id.eq({DEMO_BRAND_GROUP_ID})", f"customer_profile_id.eq({', '.join(map(str, brand_ids))})",
                            f"created_time.in({_filter_time(start)}..{_filter_time(end)})"], fields=MESSAGE_FIELDS + ["guid"])
    inv["persona_messages"] = {
        m["guid"]: {"created_time": m.get("created_time"), "post_type": m.get("post_type"),
                    "from": (m.get("from") or {}).get("screen_name"), "to_profile": m.get("customer_profile_id")}
        for m in msgs if str((m.get("from") or {}).get("screen_name", "")).lower() in PERSONA_SCREEN_NAMES}

    # Cases: the endpoint takes at most one week per request.
    cases, s = {}, start
    while s < end:
        e = min(s + dt.timedelta(days=7), end)
        for c in client.cases(s, e):
            cid = str(c.get("case_id") or c.get("id"))
            cases[cid] = {k: c.get(k) for k in ("status", "priority", "queue_id", "type") if k in c}
        s = e
    inv["cases"] = cases

    # Drafts: there's no list call, so check each ID the manifest logged.
    drafts = {}
    if manifest_path and Path(manifest_path).exists():
        data = json.loads(Path(manifest_path).read_text())
        for e in data.get("entries", []):
            for p in e.get("posts", []):
                pid = p["publishing_post_id"]
                try:
                    found = client.get_draft(pid)
                    drafts[str(pid)] = "present" if found else "missing"
                except ApiError as err:
                    drafts[str(pid)] = "missing" if err.status == 404 else f"error {err.status}"
    inv["manifest_drafts"] = drafts
    return inv


# -- tenant index ------------------------------------------------------------

def render_index(inv, profiles, topics):
    """The tenant index as Markdown: facts only, no user names or emails.

    inv is an inventory(); profiles and topics are the raw metadata lists
    (they carry the handle, topic group, and topic type the inventory drops).
    """
    groups = {int(k): v for k, v in inv["groups"].items()}
    gname = lambda g: groups.get(int(g), f"group {g}")
    out = [
        "# Tenant index",
        "",
        f"**Generated** {inv['taken_at'][:10]} by `python3 tools/sprout_api.py index`. Don't edit by hand;",
        "refresh it instead. Hand-written notes (personas, landmines, what's ours) live in",
        "[tenant-baseline.md](tenant-baseline.md).",
        "",
        f"- **Customer:** `{inv['customer_id']}`. The API token sees only: {', '.join(map(str, inv['token_sees_customers']))}",
        f"- **Users:** {len(inv['users'])} (names and emails deliberately not listed)",
        "- **Not visible to the API:** Reddit profiles, publishing calendar contents (no list call), report names,",
        "  Trellis, screen layouts. Those come from a browser pass ([click-paths/](click-paths/)).",
        "",
        "## Groups and profiles",
    ]
    by_group = {}
    for p in profiles:
        for g in p.get("groups") or [None]:
            by_group.setdefault(g, []).append(p)
    for g in sorted(by_group, key=lambda g: gname(g) if g else ""):
        out += ["", f"### {gname(g) if g else 'No group'} (`{g}`)", "",
                "| Network | Name | Handle | Profile ID |", "| --- | --- | --- | --- |"]
        for p in sorted(by_group[g], key=lambda p: (p["network_type"], str(p.get("name")))):
            out.append(f"| {p['network_type']} | {p.get('name') or ''} | {p.get('native_name') or ''} | {p['customer_profile_id']} |")

    empty = sorted(g for g in groups if g not in by_group)
    if empty:
        out += ["", "Groups with no profiles: " + ", ".join(f"{gname(g)} (`{g}`)" for g in empty)]

    tags = inv["tags"]
    active = {k: t for k, t in tags.items() if t.get("active")}
    out += ["", "## Tags", "",
            f"{len(tags)} tags, {len(active)} active. Archived tags aren't listed.", ""]
    scope = lambda t: "any group" if not t.get("groups") else ", ".join(gname(g) for g in t["groups"])
    camp = sorted((k, t) for k, t in active.items() if t.get("type") == "CAMPAIGN")
    out += ["### Active campaigns", "", "| Tag ID | Campaign | Group |", "| --- | --- | --- |"]
    for k, t in sorted(camp, key=lambda kt: (scope(kt[1]), kt[1]["text"])):
        text = "_(name withheld: real company, never use)_" if int(k) in BLOCKED_TAG_IDS else t["text"].strip()
        out.append(f"| {k} | {text} | {scope(t)} |")
    labels = {}
    for k, t in active.items():
        if t.get("type") != "CAMPAIGN":
            labels.setdefault(scope(t), []).append(t["text"].strip())
    out += ["", "### Active labels", ""]
    for s in sorted(labels):
        out.append(f"- **{s}** ({len(labels[s])}): " + ", ".join(sorted(labels[s], key=str.lower)))

    out += ["", "## Listening topics", "", "| Topic | Type | Group |", "| --- | --- | --- |"]
    for t in sorted(topics, key=lambda t: (gname(t.get("group_id")), t["name"])):
        out.append(f"| {t['name']} | {t.get('topic_type', '')} | {gname(t.get('group_id'))} |")

    out += ["", "## Teams and case queues", "",
            "- **Teams:** " + ", ".join(f"{v} (`{k}`)" for k, v in sorted(inv["teams"].items(), key=lambda kv: kv[1])),
            "- **Queues:** " + ", ".join(f"{v} (`{k}`)" for k, v in sorted(inv["queues"].items(), key=lambda kv: kv[1]))]

    start, end = inv["window"][0][:10], inv["window"][1][:10]
    pm = inv["persona_messages"]
    per = {}
    for m in pm.values():
        per[(m["from"], m["post_type"])] = per.get((m["from"], m["post_type"]), 0) + 1
    status = {}
    for c in inv["cases"].values():
        status[c.get("status", "?")] = status.get(c.get("status", "?"), 0) + 1
    out += ["", f"## Activity, {start} to {end}", "",
            f"- **Persona messages to the demo brand:** {len(pm)}"
            + (" (" + ", ".join(f"{n} from {f} ({pt})" for (f, pt), n in sorted(per.items())) + ")" if per else ""),
            f"- **Cases (whole tenant):** {len(inv['cases'])}"
            + (" (" + ", ".join(f"{n} {s.lower()}" for s, n in sorted(status.items())) + ")" if status else ""),
            ""]
    return "\n".join(out)


def tenant_index(client, days=30):
    inv = inventory(client, days=days)
    return render_index(inv, list(client.profiles().values()), client.metadata("topics"))


def diff(before, after):
    """Per section: keys added, removed, and changed."""
    out = {}
    for section in sorted((set(before) | set(after)) - {"window", "taken_at"}):
        a, b = before.get(section), after.get(section)
        if isinstance(a, list) and isinstance(b, list):
            a, b = dict.fromkeys(a, True), dict.fromkeys(b, True)
        if not (isinstance(a, dict) and isinstance(b, dict)):
            continue
        added = sorted(set(b) - set(a))
        removed = sorted(set(a) - set(b))
        changed = sorted(k for k in set(a) & set(b) if a[k] != b[k])
        if added or removed or changed:
            out[section] = {"added": {k: b[k] for k in added}, "removed": {k: a[k] for k in removed},
                            "changed": {k: {"before": a[k], "after": b[k]} for k in changed}}
    return out


# -- CLI ---------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="confirm the token reaches the demo tenant")
    p = sub.add_parser("inventory", help="read-only snapshot of the tenant")
    p.add_argument("--out", required=True)
    p.add_argument("--run", help="run folder whose manifest drafts to check")
    p.add_argument("--days", type=int, default=14)
    p = sub.add_parser("index", help="write the tenant index (Markdown) for agents and SEs to read")
    p.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "context" / "tenant-index.md"))
    p.add_argument("--days", type=int, default=30)
    p = sub.add_parser("diff", help="compare two inventory files")
    p.add_argument("before")
    p.add_argument("after")
    p = sub.add_parser("drafts", help="create the drafts in a JSON file (needs an approved plan)")
    p.add_argument("--run", required=True)
    p.add_argument("--file", required=True,
                   help='JSON list of {"group_id", "profile_ids", "text", "scheduled_times"?, "media_urls"?, "tag_ids"?}')
    args = ap.parse_args(argv)

    if args.cmd == "diff":
        d = diff(json.loads(Path(args.before).read_text()), json.loads(Path(args.after).read_text()))
        print(json.dumps(d, indent=2) if d else "No differences.")
        return 1 if d else 0

    client = SproutClient()
    if args.cmd == "check":
        customers = client.verify_tenant()
        print(f"OK: token reaches demo tenant {CUSTOMER_ID}. Customers visible: {customers}")
    elif args.cmd == "inventory":
        manifest_path = Path(args.run) / "manifest.json" if args.run else None
        inv = inventory(client, days=args.days, manifest_path=manifest_path)
        Path(args.out).write_text(json.dumps(inv, indent=2) + "\n")
        print(f"Wrote {args.out}: " + ", ".join(f"{k} {len(v)}" for k, v in inv.items() if isinstance(v, (dict, list))))
    elif args.cmd == "index":
        Path(args.out).write_text(tenant_index(client, days=args.days))
        print(f"Wrote {args.out}")
    elif args.cmd == "drafts":
        manifest = Manifest(args.run)
        specs = json.loads(Path(args.file).read_text())
        for spec in specs:  # check them all before writing any
            client.check_draft(spec["group_id"], spec["profile_ids"], spec.get("scheduled_times", ()), spec.get("tag_ids", ()))
        for spec in specs:
            media = [{"media_id": client.upload_media_url(manifest, u), "media_type": "PHOTO"}
                     for u in spec.get("media_urls", [])]
            posts, dropped = client.create_draft(manifest, spec["group_id"], spec["profile_ids"], spec["text"],
                                                 spec.get("scheduled_times", ()), media, spec.get("tag_ids", ()))
            print(f"Created {len(posts)} draft(s): {[p['publishing_post_id'] for p in posts]}"
                  + (f"  DROPPED profiles {dropped}" if dropped else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
