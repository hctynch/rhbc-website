"""One-time import of past newsletter PDFs from the old WordPress site.
Reads .github/import/newsletters.json, downloads each PDF, saves it under newsletters/YYYY/,
and adds it to data/site.json. Skips anything that isn't a real PDF or already exists."""
import json, os, time, urllib.request

LIST = ".github/import/newsletters.json"
SITE = "data/site.json"
CAP = 600 * 1024 * 1024  # stop if the import would add more than 600 MB

items = json.load(open(LIST))
site = json.load(open(SITE))
have = {b["d"] for b in site.get("newsletters", [])}
added, failed, total = [], [], 0

for it in items:
    if it["d"] in have:
        continue
    data = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(it["url"], headers={"User-Agent": "RHBC-site-import"})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            break
        except Exception as e:
            err = str(e)
            time.sleep(3)
    if not data or not data.startswith(b"%PDF"):
        failed.append((it["d"], it["url"], "not a PDF" if data else err))
        continue
    if total + len(data) > CAP:
        failed.append((it["d"], it["url"], "size cap reached"))
        continue
    os.makedirs(os.path.dirname(it["path"]), exist_ok=True)
    open(it["path"], "wb").write(data)
    total += len(data)
    site["newsletters"].append({"d": it["d"], "t": it.get("t", ""), "a": it["path"]})
    added.append(it["d"])

site["newsletters"].sort(key=lambda b: b["d"], reverse=True)
with open(SITE, "w") as f:
    json.dump(site, f, ensure_ascii=False, indent=1)
print(f"Added {len(added)} newsletters, {total/1048576:.1f} MB")
print("Failed:", json.dumps(failed, indent=1))
