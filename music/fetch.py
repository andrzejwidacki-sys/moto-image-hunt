"""Pobiera utwory CC0 z Free Music Archive (strony utworów), zapisuje dowody licencji.
Uruchamiane na runnerze Actions. Wyjście: music-out/<slug>.mp3, <slug>.page.html (skrócone), manifest.json"""
import json, os, re, subprocess, sys, urllib.request, html

OUT = os.environ.get("OUT", "music-out")
os.makedirs(OUT, exist_ok=True)
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
TRACKS = [t for t in os.environ["TRACK_URLS"].split() if t]

def get(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*", "Referer": "https://freemusicarchive.org/"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
        return r.status, r.headers.get("content-type", ""), data

man = []
for url in TRACKS:
    slug = re.sub(r"[^a-z0-9]+", "-", url.lower().split("freemusicarchive.org/")[-1]).strip("-")
    rec = {"page": url, "slug": slug}
    try:
        st, ct, body = get(url)
        page = body.decode("utf-8", "replace")
        rec["page_status"] = st
        # dowody licencji
        lic = re.findall(r"[^<>\n]{0,80}(?:licensed under|CC0|creativecommons\.org/[a-z/\.0-9-]+)[^<>\n]{0,120}", page)
        rec["license_evidence"] = list(dict.fromkeys(l.strip() for l in lic))[:12]
        urls = re.findall(r"https?:(?:\\?/){2}[^\"'\s<>]+?\.mp3[^\"'\s<>]*", page)
        urls = list(dict.fromkeys(u.replace("\\/", "/").replace("&amp;", "&") for u in urls))
        rec["mp3_candidates"] = urls[:10]
        m = re.search(r"data-track-info='([^']+)'", page)
        if m:
            try: rec["track_info"] = json.loads(html.unescape(m.group(1)))
            except Exception as e: rec["track_info_err"] = str(e)
        if urls:
            try:
                st2, ct2, audio = get(urls[0])
                rec["mp3_status"], rec["mp3_ct"], rec["mp3_bytes"] = st2, ct2, len(audio)
                if audio[:3] == b"ID3" or audio[:2] == b"\xff\xfb" or len(audio) > 100000:
                    p = f"{OUT}/{slug}.mp3"; open(p, "wb").write(audio)
                    pr = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration,bit_rate:format_tags=title,artist,copyright,license", "-of", "json", p], capture_output=True, text=True)
                    rec["ffprobe"] = json.loads(pr.stdout or "{}")
            except Exception as e:
                rec["mp3_error"] = repr(e)
        else:
            rec["page_head"] = page[:600]
        open(f"{OUT}/{slug}.page.txt", "w").write(page[:200000])
    except Exception as e:
        rec["error"] = repr(e)
    man.append(rec)
    print(json.dumps({k: v for k, v in rec.items() if k != "page_head"}, ensure_ascii=False)[:1500])
json.dump(man, open(f"{OUT}/manifest.json", "w"), ensure_ascii=False, indent=1)
