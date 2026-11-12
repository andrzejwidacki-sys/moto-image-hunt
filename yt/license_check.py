"""Dla każdego id z select_ids.txt: pobiera stronę filmu i zapisuje fragmenty wokół słów o licencji, plus uwagi o prawach z opisu.
Wyjście: license.json"""
import json, re, sys, os, urllib.request
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36", "Accept-Language": "en-US,en;q=0.9", "Cookie": "CONSENT=YES+1; SOCS=CAI"}
res = []
for vid in open("yt/select_ids.txt").read().split():
    o = {"id": vid}
    try:
        p = urllib.request.urlopen(urllib.request.Request(f"https://www.youtube.com/watch?v={vid}&hl=en", headers=UA), timeout=30).read().decode("utf-8", "replace")
        o["page_len"] = len(p)
        o["cc_hits"] = [p[max(0, m.start() - 160):m.end() + 160].replace("\n", " ") for m in re.finditer(r"(?i)creative commons|reuse allowed", p)][:6]
        o["license_hits"] = [p[max(0, m.start() - 100):m.end() + 140].replace("\n", " ") for m in re.finditer(r'(?i)"(?:license|licenseInfos|licensedContent)"|standard youtube license', p)][:6]
        m = re.search(r'"playabilityStatus":\{"status":"([A-Z_]+)"', p); o["playability"] = m.group(1) if m else None
        o["is_unlisted"] = '"isUnlisted":true' in p; o["is_live"] = '"isLiveContent":true' in p
        o["category"] = (re.search(r'"category":"([^"]+)"', p) or [None, None])[1]
        o["publish_date"] = (re.search(r'"publishDate":"([^"]+)"', p) or [None, None])[1]
        o["has_meta_row_container"] = "metadataRowContainerRenderer" in p
        o["has_license_title_row"] = '{"text":"License"}' in p
        m2 = re.search(r'"shortDescription":"((?:[^"\\]|\\.)*)"', p); d = (m2.group(1) if m2 else "").encode().decode("unicode_escape", "ignore") if m2 else ""
        o["desc_rights"] = [l.strip()[:300] for l in re.split(r"[\n\r]+", d) if re.search(r"(?i)copyright|rights|licen|credit|source|fair use|©|prawa|reusable|creative", l)][:8]
        o["has_music_panel"] = "musicSection" in p or "Music in this video" in p
        o["content_id_markers"] = [x for x in ("copyright", "Content ID") if re.search(x, p)]
    except Exception as e: o["error"] = str(e)[:150]
    res.append(o); print(vid, o.get("playability"), "cc:", len(o.get("cc_hits", [])), "lic:", len(o.get("license_hits", [])), flush=True)
json.dump(res, open(f"{OUT}/license.json", "w"), ensure_ascii=False, indent=1)
