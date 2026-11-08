"""Pobiera strony na runnerze Actions i zapisuje je jako czysty tekst (do weryfikacji faktów)."""
import html, json, os, re, sys, urllib.request
from html.parser import HTMLParser

OUT = os.environ.get("OUT", "web-out"); os.makedirs(OUT, exist_ok=True)
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
URLS = [u for u in os.environ["URLS"].split() if u]

class T(HTMLParser):
    def __init__(s): super().__init__(); s.o = []; s.skip = 0
    def handle_starttag(s, t, a):
        if t in ("script", "style", "noscript", "svg"): s.skip += 1
        if t in ("p", "br", "li", "tr", "h1", "h2", "h3", "h4", "div"): s.o.append("\n")
    def handle_endtag(s, t):
        if t in ("script", "style", "noscript", "svg"): s.skip = max(0, s.skip - 1)
    def handle_data(s, d):
        if not s.skip: s.o.append(d)

man = []
for i, u in enumerate(URLS):
    slug = f"{i:02d}-" + re.sub(r"[^a-z0-9]+", "-", u.lower().split("://")[-1])[:70].strip("-")
    rec = {"url": u, "file": slug + ".txt"}
    try:
        req = urllib.request.Request(u, headers={"User-Agent": UA, "Accept-Language": "en"})
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read(3_000_000); ct = r.headers.get("content-type", ""); rec["status"] = r.status; rec["content_type"] = ct
        s = raw.decode("utf-8", "replace")
        if "json" in ct:
            try:
                d = json.loads(s); pages = d.get("query", {}).get("pages", {})
                s = "\n\n".join(f"## {p.get('title')}\n{p.get('extract','')}" for p in (pages.values() if isinstance(pages, dict) else pages))
            except Exception: pass
        elif "html" in ct:
            p = T(); p.feed(s); s = html.unescape("".join(p.o)); s = re.sub(r"\n\s*\n+", "\n", s)
        open(f"{OUT}/{slug}.txt", "w").write(s[:400000]); rec["chars"] = len(s)
    except Exception as e:
        rec["error"] = repr(e)
    man.append(rec); print(rec, flush=True)
json.dump(man, open(f"{OUT}/manifest.json", "w"), indent=1)
