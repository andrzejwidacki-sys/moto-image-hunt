"""Pobranie filmu przez instancje Invidious (omija blokadę IP runnera, jeśli instancja ma własny dostęp). Args: <id> <outdir>"""
import json, sys, os, urllib.request, urllib.error, time
VID, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
HOSTS = ["inv.nadeko.net", "invidious.nerdvpn.de", "yt.chocolatemoo53.com", "invidious.tiekoetter.com", "yewtu.be", "invidious.privacyredirect.com",
         "iv.melmac.space", "invidious.f5.si", "invidious.materialio.us", "inv.thepixora.com", "invidious.lunar.icu", "invidious.jing.rocks", "invidious.perennialte.ch", "yt.artemislena.eu", "invidious.protokolla.fi"]
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"}
log = open(f"{OUT}/inv.log", "w")
def L(*a): s = " ".join(str(x) for x in a); print(s, flush=True); log.write(s + "\n"); log.flush()
for h in HOSTS:
    try:
        r = urllib.request.urlopen(urllib.request.Request(f"https://{h}/api/v1/videos/{VID}?local=true", headers=UA), timeout=40)
        j = json.loads(r.read().decode())
    except Exception as e: L(h, "API FAIL", str(e)[:120]); continue
    if "error" in j: L(h, "ERR", j["error"][:120]); continue
    fs = j.get("formatStreams", []); L(h, "OK streams:", [(f.get("itag"), f.get("qualityLabel")) for f in fs], "adaptive:", len(j.get("adaptiveFormats", [])))
    json.dump({k: j.get(k) for k in ("title", "author", "lengthSeconds", "license", "description")}, open(f"{OUT}/inv_meta.json", "w"), ensure_ascii=False)
    ad = j.get("adaptiveFormats", []); L("adaptive:", [(f.get("itag"), f.get("type", "")[:30], f.get("qualityLabel"), f.get("clen") or f.get("contentLength")) for f in ad])
    if not fs and ad:
        def fetch(f, name):
            u = f["url"]; u = u if u.startswith("http") else f"https://{h}{u}"; n = 0; t = time.time()
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=300) as r, open(f"{OUT}/{name}", "wb") as o:
                while True:
                    b = r.read(1 << 20)
                    if not b: break
                    o.write(b); n += len(b)
            L(h, "adaptive download", name, f.get("itag"), f.get("qualityLabel"), n, "B", round(time.time() - t), "s"); return n
        vids = [f for f in ad if f.get("type", "").startswith("video/mp4") and "avc1" in f.get("type", "") and int((f.get("qualityLabel") or "0p").split("p")[0] or 0) <= int(os.environ.get("Q", "720"))]
        auds = [f for f in ad if f.get("type", "").startswith("audio/mp4")]
        vids.sort(key=lambda f: -int((f.get("qualityLabel") or "0p").split("p")[0] or 0)); auds.sort(key=lambda f: -int(f.get("bitrate") or 0))
        try:
            if vids and auds:
                nv = fetch(vids[0], "v.mp4"); na = fetch(auds[0], "a.m4a")
                if nv > 1_000_000 and na > 100_000:
                    import subprocess
                    p = subprocess.run(["ffmpeg", "-y", "-i", f"{OUT}/v.mp4", "-i", f"{OUT}/a.m4a", "-c", "copy", "-movflags", "+faststart", f"{OUT}/video.mp4"], capture_output=True, text=True)
                    L("ffmpeg rc", p.returncode, p.stderr[-600:])
                    pr = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_name,width,height,avg_frame_rate", "-of", "default=nw=1", f"{OUT}/video.mp4"], capture_output=True, text=True); L("probe", pr.stdout.replace("\n", " "), pr.stderr[-200:])
                    os.remove(f"{OUT}/v.mp4"); os.remove(f"{OUT}/a.m4a")
                    n = os.path.getsize(f"{OUT}/video.mp4"); L("merged", n)
                    if n > 90_000_000:
                        p = subprocess.run(["ffmpeg", "-y", "-i", f"{OUT}/video.mp4", "-c", "copy", "-f", "segment", "-segment_time", "180", "-reset_timestamps", "1", f"{OUT}/seg_%02d.mp4"], capture_output=True, text=True); L("segment rc", p.returncode, p.stderr[-300:]); os.remove(f"{OUT}/video.mp4")
                    open(f"{OUT}/source.txt", "w").write(f"{h} adaptive {vids[0].get('itag')} {vids[0].get('qualityLabel')}"); sys.exit(0)
        except Exception as e: L(h, "ADAPTIVE FAIL", str(e)[:160])
    for f in sorted(fs, key=lambda f: -int((f.get("qualityLabel") or "0p")[:-1] or 0)):
        u = f["url"]; u = u if u.startswith("http") else f"https://{h}{u}"
        try:
            t = time.time(); n = 0
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=120) as r, open(f"{OUT}/video.mp4", "wb") as o:
                while True:
                    b = r.read(1 << 20)
                    if not b: break
                    o.write(b); n += len(b)
            L(h, "download", f.get("itag"), f.get("qualityLabel"), n, "B", round(time.time() - t), "s")
            if n > 5_000_000: open(f"{OUT}/source.txt", "w").write(f"{h} itag {f.get('itag')} {f.get('qualityLabel')}"); sys.exit(0)
        except Exception as e: L(h, "DL FAIL", f.get("itag"), str(e)[:120])
sys.exit(1)
