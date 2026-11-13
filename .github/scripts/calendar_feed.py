"""Build calendar.ics, the church calendar feed people subscribe to.

Reads data/site.json and writes calendar.ics at the repository root. It follows
the same rules as the Calendar page (src2.html): weekly activities, monthly
events, one-time events, canceled dates, one-date changes and labels.

Each date is written as its own event (no repeat rules), so canceled and
changed dates always match the website. The feed covers 2 months back through
12 months ahead and is rebuilt after every Save Changes and once a day.

Usage: python .github/scripts/calendar_feed.py [site.json] [calendar.ics]
No keys are used or needed.
"""
import calendar
import json
import sys
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/New_York")
NAME = "Rocky Hock Baptist Church"
ADDRESS = "113 Rocky Hock Church Road, Edenton, NC 27932"
SITE = "https://hctynch.github.io/rhbc-website/#calendar"
DAYNAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

src = sys.argv[1] if len(sys.argv) > 1 else "data/site.json"
out_path = sys.argv[2] if len(sys.argv) > 2 else "calendar.ics"
with open(src, encoding="utf-8") as f:
    st = json.load(f)
weekly = st.get("weekly") or []
monthly = st.get("monthly") or []
events = st.get("events") or []
changes = st.get("schedChanges") or []
overrides = st.get("overrides") or []
bulletins = st.get("bulletins") or []


def jsdow(d):  # Sunday = 0, like JavaScript getDay()
    return (d.weekday() + 1) % 7


def key(d):
    return d.isoformat()


def from_key(k):
    return date.fromisoformat(k[:10])


# ---- monthly events (moMatches / moOn / moInst in src2.html) ----
def mo_matches(m, k):
    d = from_key(k)
    ym = k[:7]
    if m.get("from") and ym < m["from"]:
        return False
    if m.get("until") and ym > m["until"]:
        return False
    if k in (m.get("skip") or []):
        return False
    if m.get("mode") == "day":
        return d.day == int(m.get("day") or 0)
    if jsdow(d) != int(m.get("dow") or 0):
        return False
    dim = calendar.monthrange(d.year, d.month)[1]
    n = int(m.get("n") or 0)
    return d.day + 7 > dim if n == -1 else -(-d.day // 7) == n


def mo_move(m, k):
    return next((x for x in (m.get("moves") or []) if x.get("to") == k), None)


def mo_on(m, k):
    if mo_move(m, k):
        return True
    if any(x.get("from") == k for x in (m.get("moves") or [])):
        return False
    return mo_matches(m, k)


# ---- canceled weekly activities (cxIds / canceledOn) ----
def cx_ids(c, dow):
    if not c or c.get("mode") not in ("all", "some"):
        return []
    day = [w["id"] for w in weekly if w.get("dow") == dow]
    return day if c["mode"] == "all" else [i for i in (c.get("ids") or []) if i in day]


def canceled_on(k):
    dow = jsdow(from_key(k))
    out = set()
    for e in events:
        if e.get("date") == k and e.get("cancels"):
            out.update(cx_ids(e["cancels"], dow))
    for m in monthly:
        if m.get("title") and m.get("cancels") and mo_on(m, k):
            out.update(cx_ids(m["cancels"], dow))
    for c in changes:
        if c.get("date") == k:
            out.update(cx_ids(c, dow))
    return out


def names(ids):
    return [w["title"] for w in weekly if w["id"] in ids]


def and_list(a):
    return ", ".join(a[:-1]) + " & " + a[-1] if len(a) > 1 else (a[0] if a else "")


# ---- labels on weekly activities (attachOK / mainWorshipId / labelsFor) ----
def attach_ok(e):
    if not e.get("attach"):
        return False
    w = next((x for x in weekly if x["id"] == e["attach"]), None)
    return bool(w) and w.get("dow") == jsdow(from_key(e["date"])) and w["id"] not in canceled_on(e["date"])


def cats(x):
    c = x.get("cats")
    return c if isinstance(c, list) else ([x["cat"]] if x.get("cat") else [])


def main_worship_id():
    sun = [w for w in weekly if w.get("dow") == 0]
    w = (next((w for w in sun if w["id"] == "worship"), None)
         or next((w for w in sun if "worship" in cats(w) and "10:00" <= (w.get("start") or "") <= "12:30"), None)
         or next((w for w in sun if "worship" in (w.get("title") or "").lower()), None))
    return w["id"] if w else ""


MAIN = main_worship_id()


def labels_for(wid, k):
    out = [e["title"] for e in events if e.get("date") == k and e.get("attach") == wid]
    if wid and wid == MAIN:
        b = next((x for x in bulletins if (x.get("d") or "")[:10] == k and x.get("t")), None)
        if b and not any(t.strip().lower() == b["t"].strip().lower() for t in out):
            out.insert(0, b["t"])
    return out


# ---- writing the feed ----
def esc(s):
    return (s or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\r", "").replace("\n", "\\n")


def fold(line):
    """Wrap long lines at 75 bytes, as the calendar standard requires."""
    b = line.encode("utf-8")
    if len(b) <= 75:
        return line
    parts, cur, size = [], "", 0
    for ch in line:
        n = len(ch.encode("utf-8"))
        if size + n > (75 if not parts else 74):
            parts.append(cur)
            cur, size = "", 0
        cur += ch
        size += n
    parts.append(cur)
    return "\r\n ".join(parts)


def utc(k, hm):
    h, m = (int(x) for x in hm.split(":"))
    d = from_key(k)
    return datetime(d.year, d.month, d.day, h, m, tzinfo=TZ).astimezone(timezone.utc)


items = []  # (sort key, lines)


def add(uid, k, title, start="", end="", loc="", desc="", url=""):
    lines = ["BEGIN:VEVENT", "UID:" + uid + "@rhbc-website", "DTSTAMP:{STAMP}"]
    if start:
        s = utc(k, start)
        e = utc(k, end) if end and end > start else s + timedelta(hours=1)
        lines += ["DTSTART:" + s.strftime("%Y%m%dT%H%M%SZ"), "DTEND:" + e.strftime("%Y%m%dT%H%M%SZ")]
    else:
        d = from_key(k)
        lines += ["DTSTART;VALUE=DATE:" + d.strftime("%Y%m%d"),
                  "DTEND;VALUE=DATE:" + (d + timedelta(days=1)).strftime("%Y%m%d"),
                  "TRANSP:TRANSPARENT"]
    lines.append("SUMMARY:" + esc(title))
    if loc:
        lines.append("LOCATION:" + esc(loc))
    body = "\n\n".join(x for x in [(desc or "").strip(), url] if x)
    if body:
        lines.append("DESCRIPTION:" + esc(body))
    if url:
        lines.append("URL:" + url)
    lines.append("END:VEVENT")
    items.append(((k, start or "", title), lines))


today = datetime.now(TZ).date()
first = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
first = (first - timedelta(days=1)).replace(day=1)  # first day of 2 months back
last_month = date(today.year + (today.month + 11) // 12, (today.month + 11) % 12 + 1, 1)
last = last_month.replace(day=calendar.monthrange(last_month.year, last_month.month)[1])

d = first
while d <= last:
    k = key(d)
    dow = jsdow(d)
    cx = canceled_on(k)
    # one-time events (an event attached to a weekly activity shows as its label instead)
    for e in events:
        if e.get("date") == k and e.get("title") and not attach_ok(e):
            add("e-" + e["id"], k, e["title"], e.get("start") or "", e.get("end") or "",
                e.get("loc") or "", e.get("desc") or "", e.get("url") or "")
    # monthly events
    for m in monthly:
        if m.get("title") and mo_on(m, k):
            mv = mo_move(m, k)
            s, en = m.get("start") or "", m.get("end") or ""
            if mv and mv.get("start"):
                s, en = mv["start"], mv.get("end") or ""
            add("m-" + m["id"] + "-" + k, k, m["title"], s, en, m.get("loc") or "", m.get("note") or "")
    # weekly activities, minus canceled ones, with one-date changes
    for w in weekly:
        if w.get("dow") != dow or w["id"] in cx:
            continue
        s, en, loc = w.get("start") or "", w.get("end") or "", w.get("loc") or ""
        ov = next((o for o in overrides if o.get("wid") == w["id"] and o.get("date") == k), None)
        if ov:
            if ov.get("start"):
                s, en = ov["start"], ov.get("end") or ""
            if ov.get("loc"):
                loc = ov["loc"]
        labels = labels_for(w["id"], k)
        title = w["title"] + (" – " + ", ".join(labels) if labels else "")
        add("w-" + w["id"] + "-" + k, k, title, s, en, loc, w.get("note") or "")
    # schedule changes (holiday weeks and other cancellations)
    for c in changes:
        if c.get("date") != k:
            continue
        n = names(cx_ids(c, dow))
        if not n:
            continue
        if c["mode"] == "all":
            t = "No Regular " + DAYNAMES[dow] + " Activities"
        else:
            t = n[0] + " Canceled" if len(n) == 1 else "Some " + DAYNAMES[dow] + " Activities Canceled"
        desc = "\n".join(x for x in [c.get("note") or "", "" if c["mode"] == "all" else "Canceled: " + and_list(n)] if x)
        add("c-" + c["id"], k, t, desc=desc)
    d += timedelta(days=1)

items.sort(key=lambda x: x[0])
head = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Rocky Hock Baptist Church//Church Calendar//EN",
        "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
        "X-WR-CALNAME:" + esc(NAME), "X-WR-TIMEZONE:America/New_York",
        "X-WR-CALDESC:" + esc(NAME + ", " + ADDRESS + ". Full calendar: " + SITE),
        "REFRESH-INTERVAL;VALUE=DURATION:PT6H", "X-PUBLISHED-TTL:PT6H"]
body = head + [l for _, ls in items for l in ls] + ["END:VCALENDAR"]


def render(stamp):
    return "\r\n".join(fold(l.replace("{STAMP}", stamp)) for l in body) + "\r\n"


# Keep the old time stamp when nothing else changed, so the file only changes when the calendar does.
try:
    with open(out_path, encoding="utf-8", newline="") as f:
        old = f.read()
    old_stamp = next((l[8:] for l in old.split("\r\n") if l.startswith("DTSTAMP:")), None)
except FileNotFoundError:
    old, old_stamp = "", None
if old_stamp and render(old_stamp) == old:
    print("calendar.ics unchanged:", len(items), "events")
else:
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        f.write(render(datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")))
    print("calendar.ics written:", len(items), "events,", first, "to", last)
