"""Sprawdza dostępność wolnych zdjęć miejsc na Wikimedia Commons (licencja + rozmiar). Uruchamiane na runnerze Actions."""
import json, os, re, sys, time, urllib.parse, urllib.request

OUT = os.environ.get("OUT", "places-out"); os.makedirs(OUT, exist_ok=True)
UA = "places-probe/1.0 (https://github.com/andrzejwidacki-sys/moto-image-hunt; licence check for a video project)"
PLACES = json.loads(os.environ["PLACES"])   # {"id": "zapytanie", ...}
MINW = int(os.environ.get("MIN_WIDTH", "2400"))

def api(**p):
    p.update(format="json", formatversion="2")
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(p)
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
                return json.load(r)
        except Exception as e:
            time.sleep(2 + i * 3); err = e
    raise err

def strip(h): return re.sub(r"<[^>]+>", "", h or "").strip()

def klass(lic, url):
    l = (lic or "").lower()
    if "cc0" in l or "public domain dedication" in l or "publicdomain/zero" in (url or ""): return "CC0"
    if "public domain" in l or l in ("pd", "pd-self") or l.startswith("pd-"): return "PD"
    if re.search(r"\bnc\b|non-?commercial|-nd\b| nd\b", l): return "NO"
    if "cc by-sa" in l or "cc-by-sa" in l: return "BY-SA"
    if "cc by" in l or "cc-by" in l: return "BY"
    return "CHECK"

def search(q, featured=False):
    s = q + (' incategory:"Featured pictures on Wikimedia Commons"' if featured else "")
    d = api(action="query", generator="search", gsrsearch=s + " filetype:bitmap", gsrnamespace=6, gsrlimit=50,
            prop="imageinfo", iiprop="url|size|mime|extmetadata", iiextmetadatafilter="LicenseShortName|LicenseUrl|Artist|ImageDescription|DateTimeOriginal")
    rows = []
    for pg in (d.get("query", {}).get("pages", []) or []):
        ii = (pg.get("imageinfo") or [{}])[0]; md = ii.get("extmetadata", {})
        lic = md.get("LicenseShortName", {}).get("value", ""); lurl = md.get("LicenseUrl", {}).get("value", "")
        rows.append(dict(title=pg["title"], w=ii.get("width", 0), h=ii.get("height", 0), lic=lic, klass=klass(lic, lurl),
                         artist=strip(md.get("Artist", {}).get("value", ""))[:80], date=strip(md.get("DateTimeOriginal", {}).get("value", ""))[:20],
                         page="https://commons.wikimedia.org/wiki/" + urllib.parse.quote(pg["title"].replace(" ", "_")), url=ii.get("url", ""), index=pg.get("index", 0)))
    rows.sort(key=lambda r: r["index"])
    return rows

res = {}
for pid, q in PLACES.items():
    allr = search(q); feat = search(q, True)
    big = [r for r in allr if r["w"] >= MINW and r["w"] > r["h"]]
    ok = [r for r in big if r["klass"] in ("CC0", "PD", "BY")]
    sa = [r for r in big if r["klass"] == "BY-SA"]
    res[pid] = dict(query=q, found=len(allr), landscape_big=len(big), ok_cc0_pd_by=len(ok), by_sa=len(sa),
                    featured_found=len(feat), featured=feat[:6], top_ok=ok[:30], top_sa=sa[:4])
    print(pid, res[pid]["found"], res[pid]["landscape_big"], res[pid]["ok_cc0_pd_by"], res[pid]["by_sa"], res[pid]["featured_found"], flush=True)
json.dump(res, open(f"{OUT}/places.json", "w"), ensure_ascii=False, indent=1)
with open(f"{OUT}/places.md", "w") as f:
    f.write("| miejsce | znalezione | poziome ≥%d px | CC0/PD/BY | tylko BY-SA | wyróżnione |\n|---|---|---|---|---|---|\n" % MINW)
    for pid, r in res.items():
        f.write(f"| {pid} | {r['found']} | {r['landscape_big']} | {r['ok_cc0_pd_by']} | {r['by_sa']} | {r['featured_found']} |\n")
