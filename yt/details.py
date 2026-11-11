"""Dla listy id filmów: miniatura (i.ytimg.com), tytuł/autor (oEmbed), opis i dane z HTML strony / yt-dlp (kilka klientów).
Użycie: python details.py <results.json> <katalog wyjścia>"""
import json, sys, os, re, urllib.request, urllib.parse, html
IN, OUT = sys.argv[1], sys.argv[2]; os.makedirs(f"{OUT}/thumbs", exist_ok=True)
rows = json.load(open(IN)); ids = {}
for r in rows:
    d = ids.setdefault(r["id"], {"id": r["id"], "queries": set(), "modes": set(), "known": {}})
    d["queries"].add(r["query"]); d["modes"].add(r["mode"])
    if "error" not in r: d["known"] = r
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36", "Accept-Language": "en-US,en;q=0.9", "Cookie": "CONSENT=YES+1; SOCS=CAI"}
def get(url, binary=False, timeout=25):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as f:
        b = f.read(); return b if binary else b.decode("utf-8", "replace")
def jstr(page, key):
    m = re.search(r'"%s":"((?:[^"\\]|\\.)*)"' % key, page)
    if not m: return None
    try: return json.loads('"' + m.group(1) + '"')
    except Exception: return m.group(1)
res = []
for vid, d in ids.items():
    o = {"id": vid, "url": f"https://www.youtube.com/watch?v={vid}", "queries": sorted(d["queries"]), "modes": sorted(d["modes"])}
    try:
        j = json.loads(get("https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(o["url"]))); o["title"] = j.get("title"); o["channel"] = j.get("author_name")
    except Exception as e: o["oembed_error"] = str(e)[:100]
    for q in ("maxresdefault", "hqdefault"):
        try:
            b = get(f"https://i.ytimg.com/vi/{vid}/{q}.jpg", True)
            if len(b) > 3000: open(f"{OUT}/thumbs/{vid}.jpg", "wb").write(b); o["thumb"] = f"thumbs/{vid}.jpg"; break
        except Exception: pass
    k = d["known"]
    if k: o.update({x: k.get(x) for x in ("title", "channel", "license", "duration_s", "views", "upload_date", "language", "description") if k.get(x) is not None})
    if not o.get("description"):
        try:
            p = get(o["url"] + "&hl=en&bpctr=9999999999&has_verified=1")
            o["description"] = jstr(p, "shortDescription"); o["title"] = o.get("title") or jstr(p, "title"); o["channel"] = o.get("channel") or jstr(p, "author")
            if not o.get("description"):
                m = re.search(r'<meta (?:name|property)="(?:og:)?description" content="([^"]*)"', p)
                if m: o["description"] = html.unescape(m.group(1)); o["description_src"] = "meta (skrócony)"
            def num(x):
                try: return int(re.sub(r"\D", "", x))
                except Exception: return None
            ls = jstr(p, "lengthSeconds"); vc = jstr(p, "viewCount")
            if ls and not o.get("duration_s"): o["duration_s"] = num(ls)
            if vc and not o.get("views"): o["views"] = num(vc)
            o["page_len"] = len(p); o["has_player_response"] = "ytInitialPlayerResponse" in p; o["has_consent"] = "consent.youtube.com" in p
            if "Creative Commons" in p: o["license"] = "Creative Commons Attribution license (reuse allowed)"
            if not o.get("description"): o["page_note"] = "strona bez opisu (bot-check/consent?)"
        except Exception as e: o["page_error"] = str(e)[:100]
    res.append(o); print(vid, o.get("title"), "| opis:", bool(o.get("description")), "| miniatura:", bool(o.get("thumb")), flush=True)
json.dump(res, open(f"{OUT}/details.json", "w"), ensure_ascii=False, indent=1)
