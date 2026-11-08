#!/usr/bin/env python3
"""Buduje obraz (bez dźwięku) filmu 'Indie. Pięć twarzy wody' w wybranym języku.
Użycie: FILM_LANG=pl INDIA_PHOTOS=/ścieżka FILM_DURS="13 13 13 13 13" build_india.py render|preview [s0,s1,...]
INDIA_PHOTOS: katalog z plikami zdjęć (nazwy z india/photos.json). Wyjście: $FILM_OUT/s0..s6.mp4 (+ concat.txt)."""
import json, os, subprocess, sys
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
Image.MAX_IMAGE_PIXELS = None

HERE = os.path.dirname(os.path.abspath(__file__))
LANG = os.environ["FILM_LANG"]
CAP = json.load(open(f"{HERE}/../india/captions.json"))[LANG]
PH = json.load(open(f"{HERE}/../india/photos.json"))
PDIR = os.environ["INDIA_PHOTOS"]
OUT = os.environ["FILM_OUT"]
W, H, FPS = 1920, 1080, 30
if LANG == "hi":
    FONT_B, FONT_R = "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf", "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
else:
    FONT_B, FONT_R = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
MUSIC_LINE = {"en": "Music", "es": "Música", "hi": "संगीत", "pl": "Muzyka"}
durs = [float(x) for x in os.environ.get("FILM_DURS", "13 13 13 13 13").split()]
TITLE_S, END_S = 5.0, 8.0
SCENES = [dict(name="s0", kind="title", dur=TITLE_S)]
for i in range(5):
    SCENES.append(dict(name=f"s{i+1}", kind="photo", n=i, dur=durs[i], tag=CAP["tags"][i], sub=CAP["subs"][i]))
SCENES.append(dict(name="s6", kind="end", dur=END_S))

_cache = {}
def load(n):
    if n not in _cache:
        p = PH[n]
        im = Image.open(f"{PDIR}/{p['file']}").convert("RGB")
        if p["crop"]:
            im = im.crop(tuple(p["crop"]))
        if im.width > 7000:                      # panorama: lżejsza kopia robocza (okno nadal > 3000 px szer.)
            im = im.resize((7000, round(im.height * 7000 / im.width)), Image.LANCZOS)
        _cache[n] = im
    return _cache[n]

ease = lambda t: t * t * (3 - 2 * t)
lerp = lambda a, b, t: tuple(a[i] + (b[i] - a[i]) * t for i in range(len(a)))

def window(im, f):
    cx, cy, z = f
    iw, ih = im.size
    w = min(iw, ih * 16 / 9) / z
    h = w * 9 / 16
    x0 = min(max(cx * iw - w / 2, 0), iw - w)
    y0 = min(max(cy * ih - h / 2, 0), ih - h)
    return (x0, y0, x0 + w, y0 + h)

def font(path, size):
    return ImageFont.truetype(path, size)

def wrap(d, text, f, maxw):
    lines, cur = [], ""
    for wd in text.split(" "):
        trial = (cur + " " + wd).strip()
        if d.textlength(trial, font=f) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur); cur = wd
    lines.append(cur)
    return lines

def draw_sub(img, text):
    d = ImageDraw.Draw(img, "RGBA")
    f = font(FONT_B, 46)
    lines = wrap(d, text, f, 1600)
    lh = 62 if LANG == "hi" else 60
    bh = lh * len(lines) + 36
    y0 = H - bh - 54
    d.rounded_rectangle((120, y0, W - 120, y0 + bh), 18, fill=(0, 0, 0, 150))
    for i, ln in enumerate(lines):
        d.text(((W - d.textlength(ln, font=f)) / 2, y0 + 16 + i * lh), ln, font=f, fill=(255, 255, 255, 255))

def draw_tag(img, text):
    d = ImageDraw.Draw(img, "RGBA")
    f = font(FONT_B, 34)
    tw = d.textlength(text, font=f)
    d.rounded_rectangle((60, 54, 60 + tw + 44, 54 + 62), 14, fill=(0, 0, 0, 150))
    d.text((82, 54 + 10), text, font=f, fill=(255, 255, 255, 255))

def photo_frame(sc, t):
    p = PH[sc["n"]]
    im = load(sc["n"])
    box = window(im, lerp(p["start"], p["end"], ease(t)))
    img = im.resize((W, H), Image.BICUBIC, box=box)
    draw_tag(img, sc["tag"])
    draw_sub(img, sc["sub"])
    return img

def title_frame(sc, t):
    im = load(0)
    box = window(im, (0.5, 0.5, 1.0 + 0.04 * t))
    img = im.resize((W, H), Image.BICUBIC, box=box).filter(ImageFilter.GaussianBlur(10))
    img = Image.eval(img, lambda v: int(v * 0.45))
    d = ImageDraw.Draw(img, "RGBA")
    sec = t * sc["dur"]
    a1 = min(1.0, max(0.0, (sec - 0.5) / 0.8))
    a2 = min(1.0, max(0.0, (sec - 1.5) / 0.8))
    f1, f2 = font(FONT_B, 150), font(FONT_R, 64)
    t1, t2 = CAP["title"]
    d.text(((W - d.textlength(t1, font=f1)) / 2, 390), t1, font=f1, fill=(255, 255, 255, int(255 * a1)))
    d.text(((W - d.textlength(t2, font=f2)) / 2, 590), t2, font=f2, fill=(235, 235, 235, int(255 * a2)))
    return img

def end_lines():
    short = [tg.split(",")[0] for tg in CAP["tags"]]
    lines = [(CAP["credits_head"], "head")]
    for tg, p in zip(short, PH):
        lines.append((f"{tg} — {p['author']}, {p['license']}", "r"))
    lines += [(CAP["changes"], "r"), ("", "r"), (f"{CAP['music']}: HoliznaCC0 — Transformations 3 — CC0 1.0", "r"), (CAP["links"], "r")]
    return lines

def end_frame(sc, t):
    img = Image.new("RGB", (W, H), (11, 11, 12))
    d = ImageDraw.Draw(img)
    lines = end_lines()
    step = 66
    y = (H - step * len(lines)) // 2
    for ln, kind in lines:
        f = font(FONT_B if kind == "head" else FONT_R, 46 if kind == "head" else 38)
        d.text(((W - d.textlength(ln, font=f)) / 2, y), ln, font=f, fill=(255, 255, 255) if kind == "head" else (220, 220, 220))
        y += step
    return img

def frame(sc, i):
    n = int(round(sc["dur"] * FPS))
    t = i / max(n - 1, 1)
    img = {"title": title_frame, "photo": photo_frame, "end": end_frame}[sc["kind"]](sc, t)
    sec = i / FPS
    fade = min(1.0, sec / 0.5, (sc["dur"] - sec) / (1.0 if sc["name"] == "s6" else 0.5))
    return np.clip(np.asarray(img, dtype=np.float32) * max(fade, 0.0), 0, 255).astype(np.uint8)

def render(sc):
    tmp, final = f"{OUT}/{sc['name']}.tmp.mp4", f"{OUT}/{sc['name']}.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(int(round(sc["dur"] * FPS))):
        p.stdin.write(frame(sc, i).tobytes())
    p.stdin.close()
    if p.wait() == 0:
        os.replace(tmp, final)
    return sc["name"], p.returncode

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    only = sys.argv[2].split(",") if len(sys.argv) > 2 else None
    todo = [sc for sc in SCENES if not only or sc["name"] in only]
    if sys.argv[1] == "preview":
        for sc in todo:
            Image.fromarray(frame(sc, int(sc["dur"] * FPS * 0.5))).save(f"{OUT}/prev_{sc['name']}.png")
    else:
        with Pool(min(len(todo), os.cpu_count() or 2)) as pool:
            print(pool.map(render, todo))
        open(f"{OUT}/concat.txt", "w").write("".join(f"file '{OUT}/{sc['name']}.mp4'\n" for sc in SCENES))
