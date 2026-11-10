#!/usr/bin/env python3
"""Obraz wersji 2 filmu 'Indie. Pięć twarzy wody': ujęcia 7–9 s z wolnym ruchem kamery, cięcia na oddech lektora (plan z v2_plan.py),
napisy zdanie po zdaniu, jednolita korekcja kolorów wszystkich kadrów, czarny kadr (zwrot akcji), karta końcowa z kredytami.
Użycie: FILM_LANG=pl INDIA_PHOTOS=dir FILM_PLAN=plan_pl.json FILM_OUT=dir build_india2.py render|preview|stats [segmenty]"""
import json, os, subprocess, sys
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont
Image.MAX_IMAGE_PIXELS = None

HERE = os.path.dirname(os.path.abspath(__file__))
LANG = os.environ["FILM_LANG"]
CAP = json.load(open(os.environ.get("FILM_CAPTIONS", f"{HERE}/../india/captions_v2.json")))[LANG]
SHOTS = json.load(open(os.environ.get("FILM_SHOTS", f"{HERE}/../india/photos_v2.json")))
PICK = SHOTS.pop("_pick", {})
def pick(name, n): return [SHOTS[name][i] for i in PICK.get(name, {}).get(str(n), range(n))]
PAN = 0.07   # połowa przesunięcia środka okna (<= ~15 % szerokości zdjęcia po przycięciu do okna)
def assign_moves(shots):
    """Naprzemiennie: najazd + w prawo, odjazd + w lewo. Zoom 1.00-1.14 (zmax na ujęcie, do 1.3 dla detalu)."""
    out = []
    for i, sh in enumerate(shots):
        z1 = sh.get("zmax", 1.14); cy = sh["start"][1]; sh = dict(sh)
        if i % 2 == 0: sh["start"], sh["end"] = [0.5 - PAN, cy, 1.0], [0.5 + PAN, cy, z1]
        else: sh["start"], sh["end"] = [0.5 + PAN, cy, z1], [0.5 - PAN, cy, 1.0]
        out.append(sh)
    return out
PLAN = json.load(open(os.environ["FILM_PLAN"]))
PDIR, OUT = os.environ["INDIA_PHOTOS"], os.environ["FILM_OUT"]
W, H, FPS, XF = 1920, 1080, 30, 0.7
DEV = LANG == "hi"
FB = "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if DEV else "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/freefont/FreeSans.ttf" if DEV else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
USED = {sg["name"]: sg["n_shots"] for sg in PLAN["segments"] if "n_shots" in sg}
SCENE_OF = {"s1": 0, "s2": 1, "s3": 2, "s4": 3, "s5": 4}
AMB_CREDITS = ["ezwa", "earthcalling", "Anthropic42 (en.wikipedia)"]

# ---------- jednolita korekcja kolorów ----------
def _small(im, n=400):
    s = im.copy(); s.thumbnail((n, n)); return np.asarray(s, dtype=np.float32) / 255.0

def _stats(a):
    lum = a @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    m = (lum > 0.06) & (lum < 0.94)                       # bez czerni i prześwietleń
    px = a[m] if m.sum() > 500 else a.reshape(-1, 3)
    g = px[:, 1].mean() + 1e-6
    mx, mn = px.max(1), px.min(1)
    return dict(rg=float(np.log(px[:, 0].mean() / g + 1e-6)), bg=float(np.log(px[:, 2].mean() / g + 1e-6)),
                lum=float(lum[m].mean() if m.any() else lum.mean()), sat=float(((mx - mn) / (mx + 1e-6)).mean()))

_raw = {}
def raw_image(shot):
    key = (shot["file"], tuple(shot["crop"] or ()))
    if key not in _raw:
        im = Image.open(f"{PDIR}/{shot['file']}").convert("RGB")
        if shot["crop"]: im = im.crop(tuple(shot["crop"]))
        _raw[key] = im
    return _raw[key]

def all_shots():
    seen, out = set(), []
    for v in SHOTS.values():
        for s in v:
            k = (s["file"], tuple(s["crop"] or ()))
            if k not in seen: seen.add(k); out.append(s)
    return out

_TARGET, STR = None, dict(wb=0.6, lum=0.9, sat=0.6)
def target():
    global _TARGET
    if _TARGET is None:
        st = [_stats(_small(raw_image(s))) for s in all_shots()]
        _TARGET = {k: float(np.median([x[k] for x in st])) for k in st[0]}
    return _TARGET

def grade(im, shot):
    """Jedna korekcja dla wszystkich ujęć: balans bieli i saturacja zbliżone do mediany zestawu, wspólna krzywa S,
    potem jasność dociągnięta do mediany (pomiar po krzywej), wspólny lekko ciepły ton."""
    t, s = target(), _stats(_small(im))
    a = np.asarray(im, dtype=np.float32) / 255.0
    gr = np.exp(STR["wb"] * (t["rg"] - s["rg"])); gb = np.exp(STR["wb"] * (t["bg"] - s["bg"]))
    a = np.clip(a * np.array([min(max(gr, 0.75), 1.33), 1.0, min(max(gb, 0.75), 1.33)], dtype=np.float32), 0, 1)
    gray = (a @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32))[..., None]
    sf = np.clip((t["sat"] / max(s["sat"], 0.05)) ** STR["sat"], 0.7, 1.25)
    a = np.clip(gray + (a - gray) * sf, 0, 1)
    a = a + 0.18 * (a * a * (3 - 2 * a) - a)               # łagodna krzywa S (wspólna)
    cur = _stats(np.asarray(Image.fromarray((a * 255).astype(np.uint8)).resize((400, max(1, round(400 * a.shape[0] / a.shape[1]))), Image.BILINEAR), dtype=np.float32) / 255.0)["lum"]
    gamma = float(np.clip(np.log(max(t["lum"], 0.05)) / np.log(max(cur, 0.05)), 0.65, 1.5)) ** STR["lum"]
    a = a ** gamma
    a = np.clip(a * np.array([1.015, 1.0, 0.985], dtype=np.float32), 0, 1)   # wspólny, lekko ciepły ton
    return Image.fromarray((a * 255 + 0.5).astype(np.uint8))

_graded = {}
def load(shot):
    key = (shot["file"], tuple(shot["crop"] or ()))
    if key not in _graded:
        im = raw_image(shot)
        if im.width > 7000: im = im.resize((7000, round(im.height * 7000 / im.width)), Image.LANCZOS)
        _graded[key] = grade(im, shot)
    return _graded[key]

# ---------- ruch kamery ----------
ease = lambda t: t * t * (3 - 2 * t)
lerp = lambda a, b, t: [a[i] + (b[i] - a[i]) * t for i in range(3)]
def window(im, f):
    cx, cy, z = f; iw, ih = im.size
    w = min(iw, ih * 16 / 9) / z; h = w * 9 / 16
    x0 = min(max(cx * iw - w / 2, 0), iw - w); y0 = min(max(cy * ih - h / 2, 0), ih - h)
    return (x0, y0, x0 + w, y0 + h)
def shot_img(shot, u):
    im = load(shot)
    return im.resize((W, H), Image.BICUBIC, box=window(im, lerp(shot["start"], shot["end"], ease(min(max(u, 0.0), 1.0)))))

_yy, _xx = np.mgrid[0:H, 0:W]
VIG = (1.0 - 0.22 * np.clip(((_xx - W / 2) / (W / 2)) ** 2 + ((_yy - H / 2) / (H / 2)) ** 2 - 0.35, 0, 1.2)).astype(np.float32)[..., None]

# ---------- teksty ----------
def font(p, s): return ImageFont.truetype(p, s)
def wrap(d, text, f, maxw):
    lines, cur = [], ""
    for wd in text.split(" "):
        tr = (cur + " " + wd).strip()
        if d.textlength(tr, font=f) <= maxw or not cur: cur = tr
        else: lines.append(cur); cur = wd
    lines.append(cur); return lines
def draw_sub(img, text):
    d = ImageDraw.Draw(img, "RGBA"); f = font(FB, 46)
    lines = wrap(d, text, f, 1600); lh = 62 if DEV else 60; bh = lh * len(lines) + 36; y0 = H - bh - 54
    d.rounded_rectangle((120, y0, W - 120, y0 + bh), 18, fill=(0, 0, 0, 150))
    for i, ln in enumerate(lines):
        d.text(((W - d.textlength(ln, font=f)) / 2, y0 + 16 + i * lh), ln, font=f, fill=(255, 255, 255, 255))
def draw_tag(img, text, alpha=1.0):
    d = ImageDraw.Draw(img, "RGBA"); f = font(FB, 34); tw = d.textlength(text, font=f)
    d.rounded_rectangle((60, 54, 60 + tw + 44, 116), 14, fill=(0, 0, 0, int(150 * alpha)))
    d.text((82, 64), text, font=f, fill=(255, 255, 255, int(255 * alpha)))
def cur_sub(seg, sec_abs, k):
    for (a, b), txt in zip(seg["sent_abs"], CAP["subs"][k]):
        if a - 0.15 <= sec_abs <= b + 0.35: return txt
    return None

def title_overlay(img, sec):
    a1 = min(1, max(0, (sec - 0.5) / 0.8)) * min(1, max(0, (5.0 - sec) / 0.7)); a2 = min(1, max(0, (sec - 1.4) / 0.8)) * min(1, max(0, (5.0 - sec) / 0.7))
    if a1 <= 0 and a2 <= 0: return img
    ov = Image.new("RGBA", (W, H), (0, 0, 0, int(95 * max(a1, a2)))); img = Image.alpha_composite(img.convert("RGBA"), ov)
    d = ImageDraw.Draw(img); f1, f2 = font(FB, 150), font(FR, 64); t1, t2 = CAP["title"]
    d.text(((W - d.textlength(t1, font=f1)) / 2, 330), t1, font=f1, fill=(255, 255, 255, int(255 * a1)))
    d.text(((W - d.textlength(t2, font=f2)) / 2, 530), t2, font=f2, fill=(240, 240, 240, int(255 * a2)))
    return img.convert("RGB")

def end_lines(d, f):
    names = [tg.split(",")[0] for tg in CAP["tags"]]
    order = ["s1", "s2", "s3", "s4", "s5"]
    lines = [(CAP["credits_head"], "head")]
    def who(keys):
        seen, parts = set(), []
        for k in keys:
            nsh = USED.get(k, len(SHOTS[k]))
            for p in pick(k, nsh):
                key = (p["author"], p["license"])
                if key not in seen: seen.add(key); parts.append(f"{p['author']} ({p['license']})")
        return parts
    for nm, k in zip(names, order):
        keys = [k] + (["hook", "payoff"] if k == "s1" else [])
        for j, ln in enumerate(wrap(d, f"{nm} — " + ", ".join(who(keys)), f, 1700)): lines.append((("   " if j else "") + ln, "r"))
    lines += [(CAP["changes"], "r"), ("", "r"), (f"{CAP['music']}: HoliznaCC0 — Transformations 3 — CC0 1.0", "r"),
              (f"{CAP['ambient']}: " + ", ".join(AMB_CREDITS) + " — public domain", "r"), (CAP["links"], "r")]
    return lines

# ---------- klatki ----------
def segment_frame(seg, i):
    sec = i / FPS; kind = seg["kind"]
    if kind == "black": return Image.new("RGB", (W, H), (0, 0, 0)), 1.0
    if kind == "end":
        img = Image.new("RGB", (W, H), (11, 11, 12)); d = ImageDraw.Draw(img); fr, fh = font(FR, 32), font(FB, 42)
        lines = end_lines(d, fr); step = min(58, (H - 120) // len(lines)); y = (H - step * len(lines)) // 2
        for ln, k in lines:
            f = fh if k == "head" else fr
            d.text(((W - d.textlength(ln, font=f)) / 2, y), ln, font=f, fill=(255, 255, 255) if k == "head" else (220, 220, 220)); y += step
        fade = min(1.0, sec / 0.6, (seg["dur"] - sec) / 1.0); return img, fade
    d = seg["dur"]; abs_t = seg["start"] + sec
    if kind in ("hook", "payoff"):
        shot = SHOTS[kind][0]; img = shot_img(shot, sec / d)
        txt = None
        for (a, b), t_ in zip(seg["sent_abs"], CAP["subs"][0 if kind == "hook" else 6]):
            if a - 0.15 <= abs_t <= b + 0.35: txt = t_
        if kind == "hook": img = title_overlay(img, sec)
        if txt: draw_sub(img, txt)
        fade = min(1.0, sec / (0.8 if kind == "hook" else 0.5), (d - sec) / (0.5 if kind == "hook" else 1.0))
        return img, fade
    # scena: n ujęć, cięcia (przenikanie) w środkach przerw między zdaniami
    k = SCENE_OF[seg["name"]]; shots = assign_moves(pick(seg["name"], seg["n_shots"])); cuts = seg["cuts"]
    bounds = [0.0] + list(cuts) + [d]
    j = max(i_ for i_ in range(len(shots)) if sec >= bounds[i_] - (XF / 2 if i_ else 0))
    def prog(m): return (sec - (bounds[m] - (XF / 2 if m else 0))) / ((bounds[m + 1] + (XF / 2 if m + 1 < len(shots) else 0)) - (bounds[m] - (XF / 2 if m else 0)))
    img = shot_img(shots[j], prog(j))
    if j + 1 < len(shots) and sec > bounds[j + 1] - XF / 2:
        img = Image.blend(img, shot_img(shots[j + 1], prog(j + 1)), min(1.0, (sec - (bounds[j + 1] - XF / 2)) / XF))
    draw_tag(img, CAP["tags"][k], min(1.0, sec / 0.6))
    txt = cur_sub(seg, abs_t, k + 1 if k < 4 else 5)
    if txt: draw_sub(img, txt)
    fade = min(1.0, sec / 0.5, (d - sec) / 0.5)
    return img, fade

NZ = np.random.default_rng(7).uniform(-0.7, 0.7, (H, W, 1)).astype(np.float32)   # stały ditheringu: usuwa prążkowanie nieba
def frame(seg, i):
    img, fade = segment_frame(seg, i)
    a = np.asarray(img, dtype=np.float32)
    if seg["kind"] in ("scene", "hook", "payoff"): a = a * VIG + NZ
    return np.clip(a * max(fade, 0.0), 0, 255).astype(np.uint8)

import hashlib
def _sig(seg):
    return hashlib.sha1(json.dumps([seg, SHOTS, PICK, CAP, PAN, open(__file__).read()], sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()
def _valid(final, seg):
    try:
        d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", final], capture_output=True, text=True).stdout)
        return abs(d - seg["dur"]) < 0.1 and open(final + ".sig").read() == _sig(seg)
    except Exception: return False
def render(seg):
    final = f"{OUT}/{seg['name']}.mp4"; tmp = final + ".tmp.mp4"
    if not os.environ.get("FORCE") and _valid(final, seg): return seg["name"], "skipped (valid)"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-crf", "19", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-movflags", "+faststart", tmp], stdin=subprocess.PIPE)
    for i in range(int(round(seg["dur"] * FPS))): p.stdin.write(frame(seg, i).tobytes())
    p.stdin.close(); rc = p.wait()
    if rc == 0:
        open(final + ".sig", "w").write(_sig(seg)); os.replace(tmp, final)
    return seg["name"], rc

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    segs = PLAN["segments"]; mode = sys.argv[1]
    if mode == "stats":     # kontrola jednolitości: statystyki przed i po korekcji
        rows = []
        for s in all_shots():
            b = _stats(_small(raw_image(s))); g = _stats(_small(load(s))); rows.append((s["id"], b, g))
        for key in ("rg", "bg", "lum", "sat"):
            print(key, "przed: sd=%.3f" % np.std([r[1][key] for r in rows]), "po: sd=%.3f" % np.std([r[2][key] for r in rows]))
        for r in rows: print(r[0], {k: round(v, 3) for k, v in r[1].items()}, "->", {k: round(v, 3) for k, v in r[2].items()})
        sys.exit()
    only = sys.argv[2].split(",") if len(sys.argv) > 2 else None
    todo = [s for s in segs if not only or s["name"] in only]
    if mode == "preview":
        for s in todo: Image.fromarray(frame(s, int(s["dur"] * FPS * 0.5))).save(f"{OUT}/prev_{s['name']}.png")
    else:
        with Pool(min(len(todo), os.cpu_count() or 2)) as pool: print(pool.map(render, todo))
        open(f"{OUT}/concat.txt", "w").write("".join(f"file '{OUT}/{s['name']}.mp4'\n" for s in segs))
