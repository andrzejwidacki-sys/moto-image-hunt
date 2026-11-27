"""Pobiera stronę filmu (jak cc_hunt.py) i zapisuje: wiersz License, tytuł, kanał, datę, pełny opis, fragmenty wokół słowa License. Args: <id> <outdir>"""
import json, re, sys, os, urllib.request
VID, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36", "Accept-Language": "en-US,en;q=0.9", "Cookie": "CONSENT=YES+1; SOCS=CAI"}
p = urllib.request.urlopen(urllib.request.Request(f"https://www.youtube.com/watch?v={VID}&hl=en", headers=UA), timeout=30).read().decode("utf-8", "replace")
r = {"id": VID, "page_bytes": len(p)}
m = re.search(r'"text":"License"\}\]\},"contents":\[\{"runs":\[\{"text":"([^"]+)"', p); r["license_row"] = m.group(1) if m else None
m2 = re.search(r'"shortDescription":"((?:[^"\\]|\\.)*)"', p); r["description"] = json.loads('"' + m2.group(1) + '"') if m2 else None
for k, rx in (("title", r'"title":"((?:[^"\\]|\\.)*)","lengthSeconds"'), ("owner", r'"ownerChannelName":"([^"]+)"'), ("publishDate", r'"publishDate":"([^"]+)"'), ("uploadDate", r'"uploadDate":"([^"]+)"'), ("viewCount", r'"viewCount":"(\d+)"'), ("lengthSeconds", r'"lengthSeconds":"(\d+)"'), ("isUnlisted", r'"isUnlisted":(true|false)'), ("isLive", r'"isLiveContent":(true|false)'), ("category", r'"category":"([^"]+)"')):
    mm = re.search(rx, p); r[k] = mm.group(1) if mm else None
r["license_ctx"] = [p[max(0, x.start() - 200): x.end() + 300] for x in re.finditer(r'(?i)creative commons|"License"', p)][:6]
r["chapters_in_page"] = bool(re.search(r'"chapters"', p))
json.dump(r, open(f"{OUT}/page.json", "w"), ensure_ascii=False, indent=1)
print({k: (v if k not in ("description", "license_ctx") else (len(v) if v else v)) for k, v in r.items()})
