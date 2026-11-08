"""Pobiera wybrane pliki z Wikimedia Commons (miniatura o zadanej szerokości) + metadane licencji. Uruchamiane na runnerze Actions."""
import json, os, re, time, urllib.parse, urllib.request

OUT = os.environ.get("OUT", "photos-out"); os.makedirs(OUT, exist_ok=True)
UA = "places-download/1.0 (https://github.com/andrzejwidacki-sys/moto-image-hunt; licence-checked video project)"
ITEMS = json.loads(os.environ["ITEMS"])   # [{"id": "...", "title": "File:...", "width": 3840}]

def get(url, binary=False):
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=120) as r:
                d = r.read(); return d if binary else json.loads(d)
        except Exception as e:
            err = e; time.sleep(3 + 4 * i)
    raise err

man = []
for it in ITEMS:
    rec = dict(it)
    try:
        q = urllib.parse.urlencode(dict(action="query", format="json", formatversion="2", titles=it["title"], prop="imageinfo|categories",
              iiprop="url|size|mime|extmetadata|sha1", iiurlwidth=it.get("width", 3840), cllimit=50))
        d = get("https://commons.wikimedia.org/w/api.php?" + q)
        pg = d["query"]["pages"][0]; ii = pg["imageinfo"][0]; md = ii["extmetadata"]
        v = lambda k: re.sub(r"<[^>]+>", "", md.get(k, {}).get("value", "") or "").strip()
        rec.update(orig_w=ii["width"], orig_h=ii["height"], license=v("LicenseShortName"), license_url=md.get("LicenseUrl", {}).get("value", ""),
                   artist=v("Artist"), credit=v("Credit"), description=v("ImageDescription")[:400], date=v("DateTimeOriginal"),
                   attribution_required=v("AttributionRequired"), restrictions=v("Restrictions"), usage_terms=v("UsageTerms"),
                   page=ii["descriptionurl"], sha1=ii.get("sha1"), categories=[c["title"] for c in pg.get("categories", [])][:30])
        turl = ii.get("thumburl") or ii["url"]
        data = get(turl, binary=True)
        fn = f"{it['id']}.jpg"
        open(f"{OUT}/{fn}", "wb").write(data)
        rec.update(file=fn, bytes=len(data), source_url=turl)
    except Exception as e:
        rec["error"] = repr(e)
    man.append(rec); print({k: rec.get(k) for k in ("id", "license", "artist", "orig_w", "orig_h", "bytes", "error")}, flush=True)
json.dump(man, open(f"{OUT}/manifest.json", "w"), ensure_ascii=False, indent=1)
