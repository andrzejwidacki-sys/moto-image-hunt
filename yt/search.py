"""Szuka filmów na YouTube (yt-dlp, bez pobierania): osobno z filtrem Creative Commons i bez filtra.
Wyjście: results.json + results.md. Argumenty: <zapytania rozdzielone |> <ile na zapytanie> <katalog wyjścia>"""
import json, sys, os, urllib.parse
import yt_dlp
queries = [q.strip() for q in sys.argv[1].split("|") if q.strip()]; N = int(sys.argv[2]); OUT = sys.argv[3]
os.makedirs(OUT, exist_ok=True)
CC = "EgIwAQ%253D%253D"   # filtr wyszukiwania YouTube: Creative Commons
base = {"quiet": True, "no_warnings": True, "skip_download": True, "extract_flat": "in_playlist", "playlistend": N}
def search(url):
    with yt_dlp.YoutubeDL(base) as y:
        return [e for e in (y.extract_info(url, download=False) or {}).get("entries", []) if e]
def meta(vid):
    opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    try:
        with yt_dlp.YoutubeDL(opts) as y: i = y.extract_info(f"https://www.youtube.com/watch?v={vid}", download=False)
        return {"id": vid, "title": i.get("title"), "channel": i.get("channel"), "license": i.get("license"), "duration_s": i.get("duration"),
                "views": i.get("view_count"), "likes": i.get("like_count"), "upload_date": i.get("upload_date"), "language": i.get("language"),
                "subtitles": sorted((i.get("subtitles") or {}).keys())[:12], "auto_captions": "yes" if i.get("automatic_captions") else "no",
                "description": (i.get("description") or "")[:400], "url": f"https://www.youtube.com/watch?v={vid}"}
    except Exception as e:
        return {"id": vid, "error": str(e)[:200], "url": f"https://www.youtube.com/watch?v={vid}"}
res = []
for q in queries:
    for mode, url in (("CC", f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(q)}&sp={CC}"), ("all", f"ytsearch{N}:{q}")):
        try: ids = [e["id"] for e in search(url) if e.get("id") and len(e["id"]) == 11]
        except Exception as e: print("SEARCH FAIL", mode, q, str(e)[:150]); ids = []
        print(f"{mode} | {q} | {len(ids)} wyników", flush=True)
        for v in ids[:N]:
            m = meta(v); m["query"] = q; m["mode"] = mode; res.append(m)
json.dump(res, open(f"{OUT}/results.json", "w"), ensure_ascii=False, indent=1)
with open(f"{OUT}/results.md", "w") as f:
    for r in res:
        if "error" in r: f.write(f"- ERR {r['url']} {r['error']}\n"); continue
        f.write(f"- [{r['mode']}] {r['title']} | {r['channel']} | {r['license']} | {r['duration_s']}s | {r['views']} wyśw. | napisy: {r['subtitles'] or r['auto_captions']} | {r['url']}\n")
