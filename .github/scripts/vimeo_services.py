"""Build data/services.json: the church's recorded worship services on Vimeo.

Runs in GitHub Actions with the repository secret VIMEO_TOKEN (a Vimeo
personal access token with the "Public" and "Private" scopes). Only reads.
"""
import json, os, sys, urllib.request, urllib.error, datetime
from zoneinfo import ZoneInfo

TOKEN = os.environ.get("VIMEO_TOKEN", "").strip()
EVENT = os.environ.get("VIMEO_EVENT", "1270700").strip()
MATCH = os.environ.get("VIMEO_MATCH", "Worship Service").strip().lower()
OUT = "data/services.json"
NY = ZoneInfo("America/New_York")
API = os.environ.get("VIMEO_API", "https://api.vimeo.com")
FIELDS = "uri,name,created_time,duration,player_embed_url,link,status"


def get(path):
    req = urllib.request.Request(API + path, headers={
        "Authorization": "bearer " + TOKEN,
        "Accept": "application/vnd.vimeo.*+json;version=3.4",
        "User-Agent": "rhbc-website-sync",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def from_event():
    """Live event clips (needs Vimeo's Live API; skipped if not available)."""
    ev = get(f"/live_events/{EVENT}")
    ids = []
    for c in ev.get("live_clips") or []:
        vid = c.get("video_id") or c.get("id") or (c.get("uri") or "").rsplit("/", 1)[-1]
        if vid:
            ids.append(str(vid))
    vids = []
    for vid in ids[:200]:
        try:
            vids.append(get(f"/videos/{vid}?fields={FIELDS}"))
        except urllib.error.HTTPError:
            pass
    return vids


def is_service(v):
    """Named like a worship service, or recorded on a Sunday morning (Eastern)."""
    if MATCH in (v.get("name") or "").lower():
        return True
    try:
        t = datetime.datetime.fromisoformat(v["created_time"].replace("Z", "+00:00")).astimezone(NY)
    except Exception:
        return False
    return t.weekday() == 6 and 10 <= t.hour < 13 and int(v.get("duration") or 0) >= 1800


def from_library():
    """The account's video library, newest first, filtered by name."""
    out, path = [], f"/me/videos?sort=date&direction=desc&per_page=100&fields={FIELDS}"
    while path and len(out) < 300:
        page = get(path)
        out += [v for v in page.get("data", []) if is_service(v)]
        path = (page.get("paging") or {}).get("next")
    return out


def tidy(v):
    vid = (v.get("uri") or "").rsplit("/", 1)[-1]
    if not vid.isdigit() or v.get("status") not in (None, "available"):
        return None
    h = ""
    emb = v.get("player_embed_url") or ""
    if "h=" in emb:
        h = emb.split("h=", 1)[1].split("&", 1)[0]
    else:  # unlisted links look like vimeo.com/<id>/<hash>
        parts = (v.get("link") or "").rstrip("/").split("/")
        if len(parts) >= 2 and parts[-2] == vid:
            h = parts[-1]
    t = datetime.datetime.fromisoformat(v["created_time"].replace("Z", "+00:00")).astimezone(NY)
    return {"id": vid, "h": h, "date": t.strftime("%Y-%m-%d"), "time": t.strftime("%H:%M"),
            "dur": int(v.get("duration") or 0)}


def main():
    if not TOKEN:
        print("VIMEO_TOKEN secret is not set; nothing to do.")
        return 0
    try:
        vids, source = from_event(), "event"
        if not vids:
            raise ValueError("no clips")
    except Exception as e:  # Live API needs an Enterprise plan; fall back to the library
        print("Event clips unavailable (%s); using the video library." % e)
        vids, source = from_library(), "library"
    rows = [r for r in map(tidy, vids) if r]
    seen, uniq = set(), []
    for r in sorted(rows, key=lambda r: (r["date"], r["time"]), reverse=True):
        if r["id"] not in seen:
            seen.add(r["id"]); uniq.append(r)
    new = {"source": source, "videos": uniq}
    try:
        old = json.load(open(OUT))
    except Exception:
        old = None
    if old and old.get("videos") == uniq:
        print("No change (%d services)." % len(uniq))
        return 0
    with open(OUT, "w") as f:
        json.dump(new, f, indent=1)
        f.write("\n")
    print("Wrote %d services from the %s." % (len(uniq), source))
    return 0


if __name__ == "__main__":
    sys.exit(main())
