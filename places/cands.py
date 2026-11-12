"""Kandydaci na zdjęcia z Wikimedia Commons (CC0 / PD / CC BY, >=MIN_W px, poziome) + miniatury 480 px do oglądania.
Env: QUERIES = {"miejsce": ["zapytanie1", "zapytanie2"]}, MIN_WIDTH, PER (ile na miejsce), OUT"""
import json, os, re, time, urllib.parse, urllib.request
OUT = os.environ.get("OUT", "cands-out"); os.makedirs(f"{OUT}/t", exist_ok=True)
UA = "places-cands/1.0 (https://github.com/andrzejwidacki-sys/moto-image-hunt; licence-checked commentary video project)"
Q = json.loads(os.environ["QUERIES"]); MINW = int(os.environ.get("MIN_WIDTH", "2400")); PER = int(os.environ.get("PER", "14"))
def get(url, binary=False):
    err = None
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=90) as r:
                d = r.read(); return d if binary else json.loads(d)
        except Exception as e: err = e; time.sleep(3 + 4 * i)
    raise err
def api(**p):
    p.update(format="json", formatversion="2"); return get("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(p))
def strip(h): return re.sub(r"<[^>]+>", "", h or "").strip()
def klass(lic, url):
    l = (lic or "").lower()
    if "cc0" in l or "public domain dedication" in l or "publicdomain/zero" in (url or ""): return "CC0"
    if "public domain" in l or l in ("pd", "pd-self") or l.startswith("pd-"): return "PD"
    if re.search(r"\bnc\b|non-?commercial|-nd\b| nd\b", l): return "NO"
    if "cc by-sa" in l or "cc-by-sa" in l: return "BY-SA"
    if "cc by" in l or "cc-by" in l: return "BY"
    return "CHECK"
def search(q):
    d = api(action="query", generator="search", gsrsearch=q + " filetype:bitmap", gsrnamespace=6, gsrlimit=50, prop="imageinfo",
            iiprop="url|size|mime|extmetadata", iiurlwidth=480, iiextmetadatafilter="LicenseShortName|LicenseUrl|Artist|ImageDescription|DateTimeOriginal|Restrictions")
    out = []
    for pg in d.get("query", {}).get("pages", []) or []:
        ii = (pg.get("imageinfo") or [{}])[0]; md = ii.get("extmetadata", {}); lic = md.get("LicenseShortName", {}).get("value", ""); lu = md.get("LicenseUrl", {}).get("value", "")
        out.append(dict(title=pg["title"], w=ii.get("width", 0), h=ii.get("height", 0), lic=lic, klass=klass(lic, lu), artist=strip(md.get("Artist", {}).get("value", ""))[:90],
                        desc=strip(md.get("ImageDescription", {}).get("value", ""))[:160], date=strip(md.get("DateTimeOriginal", {}).get("value", ""))[:20], restr=strip(md.get("Restrictions", {}).get("value", "")),
                        thumb=ii.get("thumburl", ""), page=ii.get("descriptionurl", ""), index=pg.get("index", 0)))
    return out
res = {}
for place, qs in Q.items():
    seen = {}; 
    for q in qs:
        try: rows = search(q)
        except Exception as e: print("FAIL", q, e); continue
        for r in sorted(rows, key=lambda r: r["index"]):
            if r["title"] in seen: continue
            if r["w"] >= MINW and r["w"] > r["h"] * 1.15 and r["klass"] in ("CC0", "PD", "BY") and not r["restr"]: seen[r["title"]] = r
        print(place, q, len(rows), "-> kandydatów", len(seen), flush=True)
    pick = sorted(seen.values(), key=lambda r: ({"CC0": 0, "PD": 0, "BY": 1}[r["klass"]], r["index"]))[:PER]
    for i, r in enumerate(pick):
        fn = f"{place}_{i:02d}.jpg"
        try: open(f"{OUT}/t/{fn}", "wb").write(get(r["thumb"], True)); r["tfile"] = fn
        except Exception as e: r["terr"] = str(e)[:80]
    res[place] = pick
json.dump(res, open(f"{OUT}/cands.json", "w"), ensure_ascii=False, indent=1)
