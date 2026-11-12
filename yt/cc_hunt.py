"""Szuka filmów z filtrem CC na YouTube, potem WERYFIKUJE licencję na stronie każdego filmu (wiersz License)
i oznacza ryzyka (reupload, 'all rights', cudze materiały). Args: <queries |> <N per query> <outdir>"""
import json, sys, os, re, time, urllib.parse, urllib.request
import yt_dlp
queries = [q.strip() for q in sys.argv[1].split("|") if q.strip()]; N = int(sys.argv[2]); OUT = sys.argv[3]
os.makedirs(OUT, exist_ok=True)
CC = "EgIwAQ%253D%253D"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36", "Accept-Language": "en-US,en;q=0.9", "Cookie": "CONSENT=YES+1; SOCS=CAI"}
opts = {"quiet": True, "no_warnings": True, "skip_download": True, "extract_flat": "in_playlist", "playlistend": N}
cands = {}
for q in queries:
    try:
        with yt_dlp.YoutubeDL(opts) as y:
            ents = [e for e in (y.extract_info(f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(q)}&sp={CC}", download=False) or {}).get("entries", []) if e and e.get("id") and len(e["id"]) == 11]
    except Exception as e: print("FAIL", q, str(e)[:120]); ents = []
    print(f"{q} | {len(ents)}", flush=True)
    for e in ents:
        c = cands.setdefault(e["id"], {"id": e["id"], "title": e.get("title"), "channel": e.get("channel") or e.get("uploader"), "duration_s": e.get("duration"), "views": e.get("view_count"), "queries": []})
        c["queries"].append(q)
print("kandydaci:", len(cands), flush=True)
RISK = r"(?i)re-?upload|not my (own )?(video|content)|no copyright (infringement )?intended|all (video|image|rights)[^.\n]{0,40}(belong|reserved)|rights reserved|©|fair use|credit(s)? (to|goes)|footage (from|by)|original video|taken from|source:"
res = []
for vid, c in cands.items():
    try:
        p = urllib.request.urlopen(urllib.request.Request(f"https://www.youtube.com/watch?v={vid}&hl=en", headers=UA), timeout=30).read().decode("utf-8", "replace")
        m = re.search(r'\{"text":"License"\}\]?,"contents":\[\{"runs":\[\{"text":"([^"]+)"', p)
        c["license_row"] = m.group(1) if m else None
        c["is_cc_by"] = bool(m and "Creative Commons" in m.group(1))
        m2 = re.search(r'"shortDescription":"((?:[^"\\]|\\.)*)"', p)
        d = json.loads('"' + m2.group(1) + '"') if m2 else ""
        c["description"] = d
        c["risk_lines"] = [l.strip()[:200] for l in re.split(r"[\r\n]+", d) if re.search(RISK, l)][:6]
        c["publish_date"] = (re.search(r'"publishDate":"([^"]+)"', p) or [None, None])[1]
        c["is_live"] = '"isLiveContent":true' in p
        c["is_unlisted"] = '"isUnlisted":true' in p
        mm = re.search(r'"ownerChannelName":"([^"]+)"', p); c["owner"] = mm.group(1) if mm else c.get("channel")
        mc = re.search(r'"lengthSeconds":"(\d+)"', p); c["length_s"] = int(mc.group(1)) if mc else c.get("duration_s")
        mv = re.search(r'"viewCount":"(\d+)"', p); c["view_count"] = int(mv.group(1)) if mv else c.get("views")
    except Exception as e: c["error"] = str(e)[:150]
    res.append(c); print(vid, c.get("license_row"), len(c.get("risk_lines", [])), flush=True); time.sleep(0.4)
json.dump(res, open(f"{OUT}/cc.json", "w"), ensure_ascii=False, indent=1)
