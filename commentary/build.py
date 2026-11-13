#!/usr/bin/env python3
"""Montaż komentarza (film #1). Użycie:
  build.py prep                 - klipy oryginału (7 s) + dźwięk oryginału + efekt planszy
  build.py preview LANG         - kontrolne klatki ruchu kamery (pierwsza/środek/ostatnia)
  build.py render LANG          - wszystkie sceny wideo (wznawialne)
  build.py mix LANG             - miks dźwięku, loudnorm, pomiary, mux
Zmienne: SP (scratchpad), TTS_PL, TTS_EN (katalogi z wav), SRC (pełny film 1080p/720p)."""
import json, math, os, subprocess, sys, wave
from math import gcd
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import data

W, H, FPS = 1920, 1080, 30
SP = Path(os.environ["SP"])
WD = SP / "cm"
PH = SP / "ph"
FONT_R = "/usr/share/fonts/opentype/inter/Inter-Regular.otf"
FONT_M = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
FONT_B = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
SR = 48000
GAP, LEAD, TAIL = 0.55, 0.7, 1.3
CARD_S = 2.4
ORIG_S = 7.0  # maksimum


def orig_frames(pid):
    s, e = data.WINDOWS[pid]
    return int(round((e - s) * 30))
ACCENT = (255, 196, 61)

# ---------- ruch kamery: (cx, cy, zoom) początek -> koniec ----------
MOVES = {
    "nepal1": ((0.45, 0.37, 1.00), (0.48, 0.40, 1.10)),
    "nepal2": ((0.50, 0.50, 1.00), (0.55, 0.52, 1.12)),
    "nepal3": ((0.50, 0.50, 1.00), (0.74, 0.64, 1.35)),
    "machu1": ((0.50, 0.50, 1.00), (0.42, 0.55, 1.15)),
    "machu2": ((0.50, 0.45, 1.00), (0.50, 0.50, 1.12)),
    "machu3": ((0.45, 0.50, 1.00), (0.55, 0.50, 1.15)),
    "utah1": ((0.50, 0.50, 1.00), (0.50, 0.52, 1.12)),
    "utah3": ((0.50, 0.50, 1.00), (0.50, 0.55, 1.15)),
    "utah2": ((0.50, 0.50, 1.00), (0.55, 0.50, 1.25)),
    "fuego1": ((0.50, 0.50, 1.00), (0.50, 0.55, 1.45)),
    "fuego1@1": ((0.55, 0.55, 1.30), (0.45, 0.50, 1.00)),
    "fuego3": ((0.50, 0.44, 1.00), (0.60, 0.46, 1.15)),
    "copper1": ((0.50, 0.45, 1.00), (0.55, 0.50, 1.12)),
    "copper2": ((0.40, 0.50, 1.00), (0.60, 0.50, 1.12)),
    "burning1": ((0.62, 0.50, 1.00), (0.62, 0.52, 1.10)),
    "burning3": ((0.75, 0.50, 1.00), (0.60, 0.50, 1.12)),
    "grand2": ((0.40, 0.50, 1.00), (0.60, 0.50, 1.12)),
    "grand1": ((0.50, 0.50, 1.00), (0.45, 0.60, 1.30)),
    "grand3": ((0.50, 0.50, 1.00), (0.55, 0.55, 1.15)),
    "ometepe1": ((0.50, 0.55, 1.00), (0.50, 0.50, 1.12)),
    "ometepe2": ((0.50, 0.40, 1.00), (0.55, 0.50, 1.15)),
}

# ---------- autorzy i licencje zdjęć (ze stron Commons, patrz places/manifest) ----------
LIC_URL = {"CC BY 4.0": "https://creativecommons.org/licenses/by/4.0/",
           "CC BY 3.0": "https://creativecommons.org/licenses/by/3.0/",
           "CC BY 2.0": "https://creativecommons.org/licenses/by/2.0/",
           "CC0": "https://creativecommons.org/publicdomain/zero/1.0/",
           "Public domain": ""}
ARTIST = {"nepal1": "Lerian", "nepal2": "Vyacheslav Argenberg", "nepal3": "Vyacheslav Argenberg",
          "machu1": "Scott Umstattd", "machu2": "Hiram Bingham III (1912)", "machu3": "Tomas Sobek",
          "utah1": "CanyonlandsNPS", "utah2": "CanyonlandsNPS", "utah3": "CanyonlandsNPS",
          "fuego1": "Rick Thomas", "fuego3": "Pierre Markuse (Landsat 8 / USGS)", "copper1": "Jens Uhlenbrock",
          "copper2": "Jesus Alejandro Guer…",
          "burning1": "Steve Jurvetson", "burning3": "mypubliclands",
          "grand1": "Grand Canyon National Park", "grand2": "Bernard Spragg", "grand3": "Grand Canyon National Park",
          "ometepe1": "Ridiculopathy", "ometepe2": "Ridiculopathy"}


ARTIST_NOTE = {"copper2": {"pl": "nazwisko ucięte u źródła", "en": "name truncated at source"},
               "copper1": {"pl": "wg Commons", "en": "per Commons"}}


def artist(pid, lang):
    a = ARTIST[pid]
    n = ARTIST_NOTE.get(pid, {}).get(lang)
    return f"{a} ({n})" if n else a


def manifest():
    return {x["id"]: x for x in json.load(open(PH / "manifest.json"))}


def lic_of(pid):
    return manifest()[pid]["license"]


# ---------- narzędzia ----------
def font(path, size):
    return ImageFont.truetype(path, size)


def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        raise RuntimeError(f"{cmd[:6]} rc={r.returncode}\n{r.stderr[-800:]}")
    return r


def wrap(draw, text, fnt, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= maxw:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def text_box(text, size=40, maxw=1500, fill=(255, 255, 255), bg=(8, 10, 14, 170), pad=(28, 18), path=FONT_M, radius=14):
    f = font(path, size)
    d0 = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    lines = wrap(d0, text, f, maxw)
    lh = int(size * 1.3)
    w = int(max(d0.textlength(l, font=f) for l in lines)) + 2 * pad[0]
    h = lh * len(lines) + 2 * pad[1]
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if bg:
        d.rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=bg)
    for i, l in enumerate(lines):
        d.text((pad[0], pad[1] + i * lh + (lh - size) // 2 - 4), l, font=f, fill=fill)
    return np.asarray(im)


def blend(frame, rgba, x, y, alpha=1.0):
    h, w = rgba.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0 or alpha <= 0:
        return
    sub = rgba[y0 - y:y1 - y, x0 - x:x1 - x]
    a = sub[..., 3:4].astype(np.float32) / 255.0 * alpha
    reg = frame[y0:y1, x0:x1].astype(np.float32)
    frame[y0:y1, x0:x1] = (reg * (1 - a) + sub[..., :3].astype(np.float32) * a).astype(np.uint8)


def smooth(p):
    p = min(1.0, max(0.0, p))
    return p * p * (3 - 2 * p)


def ffmpeg_pipe(out, extra=()):
    tmp = str(out) + ".tmp.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS),
           "-video_track_timescale", "30000", *extra, "-f", "mp4", tmp]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE), tmp


def finish_pipe(p, tmp, out):
    p.stdin.close()
    rc = p.wait()
    if rc:
        raise RuntimeError(f"ffmpeg pipe rc={rc} for {out}")
    os.replace(tmp, out)


def nframes(path):
    r = sh(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", str(path)])
    return int(r.stdout.strip())


def valid(path, frames):
    try:
        return Path(path).exists() and nframes(path) == frames
    except Exception:
        return False


# ---------- dźwięk ----------
def read_wav(path):
    with wave.open(str(path), "rb") as w:
        sr, n, ch = w.getframerate(), w.getnframes(), w.getnchannels()
        x = np.frombuffer(w.readframes(n), dtype="<i2").astype(np.float32) / 32768.0
    if ch > 1:
        x = x.reshape(-1, ch).mean(1)
    return x, sr


def read_f32(path):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, dtype="<f4").reshape(-1, 2).copy()


def to48(x, sr):
    from scipy.signal import resample_poly
    g = gcd(SR, sr)
    return resample_poly(x, SR // g, sr // g).astype(np.float32)


def split_by_silence(x, sr, n_expected):
    """Dzieli klip na zdania: n-1 najdłuższych przerw z cyfrowej ciszy (generator TTS wstawia zera między zdaniami)."""
    quiet = np.abs(x) <= 3 / 32768
    idx = np.flatnonzero(~quiet)
    d = np.diff(idx)
    gaps = [(int(g), int(idx[g]), int(idx[g + 1])) for g in np.flatnonzero(d > int(0.08 * sr))]
    if len(gaps) < n_expected - 1:
        raise RuntimeError(f"za mało przerw: {len(gaps)} dla {n_expected} zdań")
    top = sorted(sorted(gaps, key=lambda q: q[2] - q[1], reverse=True)[:n_expected - 1], key=lambda q: q[1])
    lens = sorted((q[2] - q[1]) / sr for q in gaps)
    if len(gaps) > n_expected - 1 and lens[-n_expected] > 0.6 * lens[-(n_expected - 1)]:
        print("UWAGA: niejednoznaczne przerwy", [round(v, 2) for v in lens[-n_expected - 1:]], flush=True)
    bounds = [idx[0]] + [v for q in top for v in (q[1], q[2])] + [idx[-1] + 1]
    return [x[bounds[2 * k]:bounds[2 * k + 1] + (0 if k < n_expected - 1 else 0)] for k in range(n_expected)]


def narration(lang, key, n):
    d = Path(os.environ["TTS_PL" if lang == "pl" else "TTS_EN"])
    f = d / (f"piper_{key}_pl_pl_PL-gosia-medium.wav" if lang == "pl" else f"kokoro_{key}_en_af_heart.wav")
    x, sr = read_wav(f)
    segs = split_by_silence(x, sr, n)
    return [to48(s, sr) for s in segs]


def timeline(sents):
    d = [len(s) / SR for s in sents]
    starts, t = [], LEAD
    for di in d:
        starts.append(t); t += di + GAP
    total = starts[-1] + d[-1] + TAIL
    frames = math.ceil(total * FPS)
    return d, starts, frames


def synth_card_fx():
    rng = np.random.default_rng(7)
    n = int(CARD_S * SR)
    t = np.arange(n) / SR
    from scipy.signal import butter, sosfilt
    noise = rng.standard_normal(n).astype(np.float32)
    whoosh = np.zeros(n, np.float32)
    hit_t = 0.7
    for fc in (250, 500, 1000, 2000, 4000, 8000):
        sos = butter(2, [fc / 1.5, min(fc * 1.5, 20000)], btype="band", fs=SR, output="sos")
        band = sosfilt(sos, noise)
        centre = 250 * 2 ** (np.clip(t / hit_t, 0, 1) * 4.5)
        g = np.exp(-((np.log2(fc) - np.log2(centre)) / 0.8) ** 2)
        whoosh += band * g
    env = np.where(t < hit_t, (t / hit_t) ** 2.2, np.exp(-(t - hit_t) * 9))
    whoosh *= env
    whoosh /= np.abs(whoosh).max() + 1e-9
    th = np.clip(t - hit_t, 0, None) * (t >= hit_t)
    sub = np.sin(2 * np.pi * 55 * th) * np.exp(-th * 5) * (t >= hit_t)
    chime = np.zeros(n, np.float32)
    for f0, off, amp in ((659.25, 0.0, 0.5), (987.77, 0.12, 0.4), (1318.5, 0.26, 0.25)):
        tt = np.clip(t - hit_t - off, 0, None) * (t >= hit_t + off)
        chime += amp * np.sin(2 * np.pi * f0 * tt) * np.exp(-tt * 3.2) * (t >= hit_t + off)
    x = 0.55 * whoosh + 0.7 * sub + 0.45 * chime
    x *= np.minimum(1, (CARD_S - t) / 0.15)
    x = (x / (np.abs(x).max() + 1e-9) * 0.6).astype(np.float32)
    return np.stack([x, x], 1)


# ---------- sceny ----------
def credit_tag(pid, lang):
    return f"{'Foto' if lang == 'pl' else 'Photo'}: {artist(pid, lang)} · {lic_of(pid)}"


def place_label(i, p, lang):
    return text_box(f"{i + 1}/8 · {p['name'][lang]}", size=34, maxw=1100, path=FONT_M, bg=(8, 10, 14, 150), pad=(24, 14))


def mv(pid, k):
    return MOVES.get(f"{pid}@{k}", MOVES[pid])


def load_shots(place):
    shots = []
    for pid, idx in place["shots"]:
        im = Image.open(PH / f"{pid}.jpg").convert("RGB")
        shots.append((pid, idx, im))
    return shots


def window_box(im, mv, p):
    (cx0, cy0, z0), (cx1, cy1, z1) = mv
    e = smooth(p)
    cx, cy, z = cx0 + (cx1 - cx0) * e, cy0 + (cy1 - cy0) * e, z0 + (z1 - z0) * e
    iw, ih = im.size
    w = min(iw, ih * 16 / 9) / z
    h = w * 9 / 16
    x0 = min(max(cx * iw - w / 2, 0), iw - w)
    y0 = min(max(cy * ih - h / 2, 0), ih - h)
    return (x0, y0, x0 + w, y0 + h)


def photo_frame(im, mv, p):
    return np.asarray(im.resize((W, H), Image.BICUBIC, box=window_box(im, mv, p)))


def render_photos(args):
    i, lang = args
    place = data.PLACES[i]
    out = WD / lang / f"photos_{place['id']}.mp4"
    sents = narration(lang, f"cm{i + 1}", len(place["spoken"][lang]))
    d, starts, frames = timeline(sents)
    if valid(out, frames):
        return str(out), frames
    shots = load_shots(place)
    # granice ujęć: środek przerwy między zdaniami
    bounds = [0.0]
    for k in range(1, len(shots)):
        a = shots[k - 1][1][-1]
        b = shots[k][1][0]
        bounds.append((starts[a] + d[a] + starts[b]) / 2)
    bounds.append(frames / FPS)
    XF = 0.35
    label = place_label(i, place, lang)
    caps = [text_box(c, size=40, maxw=1560) for c in place["caption"][lang]]
    tags = {pid: text_box(credit_tag(pid, lang), size=26, maxw=900, path=FONT_R, bg=(8, 10, 14, 150), pad=(18, 10)) for pid, _, _ in shots}
    pipe, tmp = ffmpeg_pipe(out)
    for fr in range(frames):
        t = fr / FPS
        cur = shots[0][0]
        acc = np.zeros((H, W, 3), np.float32)
        wsum = 0.0
        for k, (pid, idx, im) in enumerate(shots):
            lo, hi = bounds[k] - (XF if k > 0 else 0), bounds[k + 1] + (XF if k < len(shots) - 1 else 0)
            if not (lo <= t <= hi):
                continue
            if k > 0 and t < bounds[k] + XF:
                a = smooth((t - (bounds[k] - XF)) / (2 * XF))
            elif k < len(shots) - 1 and t > bounds[k + 1] - XF:
                a = 1 - smooth((t - (bounds[k + 1] - XF)) / (2 * XF))
            else:
                a = 1.0
            prog = (t - lo) / (hi - lo)
            acc += photo_frame(im, mv(pid, k), prog).astype(np.float32) * a
            wsum += a
            if a >= 0.5:
                cur = pid
        frame = (acc / max(wsum, 1e-6)).astype(np.uint8)
        # fade-in z czerni 0.4 s, fade-out 0.3 s
        fa = smooth(t / 0.4) * (1 - smooth((t - (frames / FPS - 0.3)) / 0.3))
        blend(frame, label, 40, 36)
        tg = tags[cur]
        blend(frame, tg, W - tg.shape[1] - 40, 36)
        # podpis aktualnego zdania
        for si in range(len(d)):
            s0, s1 = starts[si] - 0.1, starts[si] + d[si] + 0.35
            if s0 <= t <= s1:
                al = min(smooth((t - s0) / 0.2), 1 - smooth((t - (s1 - 0.2)) / 0.2))
                c = caps[si]
                blend(frame, c, (W - c.shape[1]) // 2, H - c.shape[0] - 64, al)
        if fa < 1:
            frame = (frame.astype(np.float32) * fa).astype(np.uint8)
        pipe.stdin.write(frame.tobytes())
    finish_pipe(pipe, tmp, out)
    return str(out), frames


def render_card(i, lang):
    place = data.PLACES[i]
    out = WD / lang / f"card_{place['id']}.mp4"
    frames = int(round(CARD_S * FPS))
    if valid(out, frames):
        return out
    main = text_box("And what it really looks like", size=104, maxw=1700, path=FONT_B, bg=None, pad=(0, 0))
    sub = text_box(place["name"][lang], size=44, maxw=1500, path=FONT_M, bg=None, fill=(210, 215, 225), pad=(0, 0))
    base = np.zeros((H, W, 3), np.uint8)
    yy = np.linspace(0, 1, H)[:, None]
    base[:] = (np.array([10, 14, 22]) * (1 - yy) + np.array([22, 30, 44]) * yy)[:, None, :].astype(np.uint8)
    pipe, tmp = ffmpeg_pipe(out)
    hit = 0.7
    for fr in range(frames):
        t = fr / FPS
        f = base.copy()
        # linia akcentu rośnie do uderzenia
        lw = int(900 * smooth(t / hit))
        f[H // 2 + 90:H // 2 + 96, (W - lw) // 2:(W + lw) // 2] = ACCENT
        if t >= hit:
            a = smooth((t - hit) / 0.25)
            blend(f, main, (W - main.shape[1]) // 2, H // 2 - 80 - int(10 * (1 - a)), a)
            a2 = smooth((t - hit - 0.2) / 0.3)
            blend(f, sub, (W - sub.shape[1]) // 2, H // 2 + 130, a2)
            if t - hit < 0.07:  # krótki błysk w momencie uderzenia
                f = np.clip(f.astype(np.float32) + 90 * (1 - (t - hit) / 0.07), 0, 255).astype(np.uint8)
        fa = 1 - smooth((t - (CARD_S - 0.25)) / 0.25)
        if fa < 1:
            f = (f.astype(np.float32) * fa).astype(np.uint8)
        pipe.stdin.write(f.tobytes())
    finish_pipe(pipe, tmp, out)
    return out


def orig_tag(lang):
    return text_box(f"{'ORYGINAŁ' if lang == 'pl' else 'ORIGINAL'} · {data.SRC['author']} · CC BY", size=30, maxw=900, path=FONT_M, bg=(8, 10, 14, 170), pad=(20, 12))


def make_orig(i, full, lang):
    place = data.PLACES[i]
    s, e = data.WINDOWS[place["id"]]
    out = WD / f"orig_{lang}_{place['id']}.mp4"
    frames = orig_frames(place["id"])
    dur = frames / FPS
    if valid(out, frames):
        return
    tag = WD / f"orig_tag_{lang}.png"
    Image.fromarray(orig_tag(lang), "RGBA").save(tag)
    tmp = str(out) + ".tmp.mp4"
    fc = ("[0:v]scale=1920:1080:flags=lanczos,fps=30,setsar=1,format=rgb24[v];[v][1:v]overlay=40:H-h-40:format=auto,"
          f"fade=t=in:st=0:d=0.2,fade=t=out:st={dur - 0.3:.3f}:d=0.3,format=yuv420p[o]")
    sh(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{s:.3f}", "-i", str(full), "-i", str(tag), "-t", f"{dur:.3f}",
        "-filter_complex", fc, "-map", "[o]", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-r", "30", "-frames:v", str(frames), "-video_track_timescale", "30000", "-f", "mp4", tmp])
    os.replace(tmp, out)


def make_orig_audio(i, full):
    place = data.PLACES[i]
    s, e = data.WINDOWS[place["id"]]
    out = WD / f"orig_{place['id']}.wav"
    if out.exists():
        return
    sh(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{s:.3f}", "-i", str(full), "-t", f"{orig_frames(place['id']) / FPS:.3f}", "-vn", "-ac", "2", "-ar", str(SR), "-c:a", "pcm_f32le", str(out)])


def render_intro(lang):
    out = WD / lang / "intro.mp4"
    cm0 = narration(lang, "cm0", len(data.INTRO["spoken"][lang]))
    d, starts, frames = timeline(cm0)
    if valid(out, frames):
        return frames
    bg = Image.open(WD / "bg.jpg").convert("RGB").resize((W, H))
    bg = bg.filter(ImageFilter.GaussianBlur(14))
    bgn = (np.asarray(bg).astype(np.float32) * 0.35).astype(np.uint8)
    title = "Jak to naprawdę wygląda?" if lang == "pl" else "What does it really look like?"
    tt = text_box(title, size=100, maxw=1700, path=FONT_B, bg=None, pad=(0, 0))
    sub = text_box(f"{data.SRC['title']} — {data.SRC['author']}", size=40, maxw=1600, path=FONT_M, bg=None, fill=(220, 224, 232), pad=(0, 0))
    url = text_box(f"{data.SRC['url']}  ·  CC BY", size=32, maxw=1600, path=FONT_R, bg=None, fill=ACCENT, pad=(0, 0))
    caps = [text_box(c, size=40, maxw=1560) for c in data.INTRO["caption"][lang]]
    pipe, tmp = ffmpeg_pipe(out)
    for fr in range(frames):
        t = fr / FPS
        f = bgn.copy()
        a = smooth((t - 0.2) / 0.6)
        blend(f, tt, (W - tt.shape[1]) // 2, 330 - int(12 * (1 - a)), a)
        blend(f, sub, (W - sub.shape[1]) // 2, 500, smooth((t - 0.6) / 0.6))
        blend(f, url, (W - url.shape[1]) // 2, 570, smooth((t - 0.9) / 0.6))
        for si in range(len(d)):
            s0, s1 = starts[si] - 0.1, starts[si] + d[si] + 0.35
            if s0 <= t <= s1:
                al = min(smooth((t - s0) / 0.2), 1 - smooth((t - (s1 - 0.2)) / 0.2))
                c = caps[si]
                blend(f, c, (W - c.shape[1]) // 2, H - c.shape[0] - 64, al)
        fa = smooth(t / 0.5) * (1 - smooth((t - (frames / FPS - 0.3)) / 0.3))
        if fa < 1:
            f = (f.astype(np.float32) * fa).astype(np.uint8)
        pipe.stdin.write(f.tobytes())
    finish_pipe(pipe, tmp, out)
    return frames


def credit_lines(lang):
    L = []
    pl = lang == "pl"
    L.append(("h", "Źródła i licencje" if pl else "Credits and licences"))
    L.append(("p", ("Film oryginalny: " if pl else "Original video: ") + f"„{data.SRC['title']}” — {data.SRC['author']}"))
    L.append(("p", f"{data.SRC['url']} — licencja: Creative Commons Attribution (CC BY), wg strony filmu na YouTube" if pl
              else f"{data.SRC['url']} — licence: Creative Commons Attribution (CC BY), per the YouTube video page"))
    L.append(("p", "Fragmenty po 7 s użyte jako cytat do komentarza; muzyka i ujęcia w oryginale mogą mieć własne prawa." if pl
              else "7-second excerpts used as quotation for commentary; music and footage inside the original may carry their own rights."))
    for p in data.PLACES:
        L.append(("s", p["name"][lang]))
        for pid, _ in p["shots"]:
            m = manifest()[pid]
            L.append(("p", f"{artist(pid, lang)} — {m['license']} — {m['page']}"))
    L.append(("s", "Dźwięk" if pl else "Sound"))
    L.append(("p", "Muzyka: „Transformations 3”, HoliznaCC0 (CC0 1.0), Free Music Archive" if pl else "Music: “Transformations 3” by HoliznaCC0 (CC0 1.0), Free Music Archive"))
    L.append(("p", "Lektor: Piper pl_PL-gosia-medium (synteza mowy)" if pl else "Voice: Kokoro-82M, af_heart (Apache-2.0), synthetic speech"))
    L.append(("p", "Efekt planszy „And what it really looks like” wygenerowany programowo." if pl else "The “And what it really looks like” card sound is generated in code."))
    L.append(("p", "Zmiany w zdjęciach: kadrowanie 16:9, powolny ruch kamery, bez korekty kolorów." if pl else "Changes to photos: 16:9 crop and slow camera move, no colour grading."))
    return L


def paginate(lines, per=19):
    pages, cur, n = [], [], 0
    for kind, txt in lines:
        cost = 2 if kind in ("h", "s") else 1
        if n + cost > per and cur:
            pages.append(cur); cur, n = [], 0
        cur.append((kind, txt)); n += cost
    if cur:
        pages.append(cur)
    return pages


CRED_PAGE_S = 7.0


def render_credits(lang):
    pages = paginate(credit_lines(lang))
    outs = []
    fh, fs, fp = font(FONT_B, 54), font(FONT_M, 34), font(FONT_R, 27)
    for pi, pg in enumerate(pages):
        out = WD / lang / f"credits_{pi}.mp4"
        frames = int(CRED_PAGE_S * FPS)
        outs.append(out)
        if valid(out, frames):
            continue
        im = Image.new("RGB", (W, H), (12, 16, 24))
        d = ImageDraw.Draw(im)
        y = 70
        for kind, txt in pg:
            if kind == "h":
                d.text((90, y), txt, font=fh, fill=(255, 255, 255)); y += 90
            elif kind == "s":
                y += 8; d.text((90, y), txt, font=fs, fill=ACCENT); y += 52
            else:
                for line in wrap(d, txt, fp, W - 180):
                    d.text((90, y), line, font=fp, fill=(214, 220, 230)); y += 38
        base = np.asarray(im)
        pipe, tmp = ffmpeg_pipe(out)
        for fr in range(frames):
            t = fr / FPS
            fa = smooth(t / 0.4) * (1 - smooth((t - (CRED_PAGE_S - 0.4)) / 0.4))
            pipe.stdin.write((base.astype(np.float32) * fa).astype(np.uint8).tobytes() if fa < 1 else base.tobytes())
        finish_pipe(pipe, tmp, out)
    return outs


# ---------- polecenia ----------
def find_full():
    p = os.environ.get("SRC")
    if p and Path(p).exists():
        return Path(p)
    raise SystemExit("ustaw SRC=pełny film")


def cmd_prep():
    WD.mkdir(parents=True, exist_ok=True)
    full = find_full()
    if not (WD / "bg.jpg").exists():
        sh(["ffmpeg", "-y", "-loglevel", "error", "-ss", "170", "-i", str(full), "-frames:v", "1", "-q:v", "2", str(WD / "bg.jpg")])
    for i in range(len(data.PLACES)):
        make_orig(i, full, "pl")
        make_orig(i, full, "en")
        make_orig_audio(i, full)
        print("orig", data.PLACES[i]["id"], flush=True)


def cmd_preview(lang):
    outd = WD / "preview"
    outd.mkdir(parents=True, exist_ok=True)
    tiles = []
    for i, place in enumerate(data.PLACES):
        for k, (pid, idx) in enumerate(place["shots"]):
            im = Image.open(PH / f"{pid}.jpg").convert("RGB")
            for p in (0.0, 0.5, 1.0):
                f = Image.fromarray(photo_frame(im, mv(pid, k), p)).resize((640, 360))
                dr = ImageDraw.Draw(f)
                dr.text((8, 8), f"{pid} {p}", fill=(255, 255, 0), font=font(FONT_M, 22))
                tiles.append(f)
    cols = 6
    rows = math.ceil(len(tiles) / cols)
    sheet = Image.new("RGB", (cols * 640, rows * 360))
    for k, f in enumerate(tiles):
        sheet.paste(f, ((k % cols) * 640, (k // cols) * 360))
    n = 0
    per = 18
    for a in range(0, len(tiles), per):
        part = tiles[a:a + per]
        sh_ = Image.new("RGB", (cols * 640, math.ceil(len(part) / cols) * 360))
        for k, f in enumerate(part):
            sh_.paste(f, ((k % cols) * 640, (k // cols) * 360))
        sh_.resize((sh_.width * 2 // 3, sh_.height * 2 // 3)).save(outd / f"moves_{n}.jpg", quality=88)
        n += 1
    print("preview sheets", n)


def cmd_render(lang):
    (WD / lang).mkdir(parents=True, exist_ok=True)
    log = WD / f"progress_{lang}.log"
    render_intro(lang)
    print("intro", flush=True)
    for i in range(len(data.PLACES)):
        render_card(i, lang)
    print("cards", flush=True)
    render_credits(lang)
    with Pool(2) as pool:
        for out, frames in pool.imap(render_photos, [(i, lang) for i in range(len(data.PLACES))]):
            print("photos", out, frames, flush=True)
            open(log, "a").write(f"photos {out} {frames}\n")


def scene_list(lang):
    sc = [("intro", WD / lang / "intro.mp4")]
    for p in data.PLACES:
        sc += [("orig", WD / f"orig_{lang}_{p['id']}.mp4"), ("card", WD / lang / f"card_{p['id']}.mp4"), ("photos", WD / lang / f"photos_{p['id']}.mp4")]
    for k in range(len(paginate(credit_lines(lang)))):
        sc.append(("credits", WD / lang / f"credits_{k}.mp4"))
    return sc


def cmd_concat(lang):
    sc = scene_list(lang)
    lst = WD / lang / "concat.txt"
    lst.write_text("".join(f"file '{p}'\n" for _, p in sc))
    out = WD / lang / "video_silent.mp4"
    tmp = str(out) + ".tmp.mp4"
    sh(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", "-f", "mp4", tmp])
    os.replace(tmp, out)
    print("concat ok", out)


def cmd_mix(lang):
    import pyloudnorm as pyln
    sc = scene_list(lang)
    durs = [nframes(p) / FPS for _, p in sc]
    total = sum(durs)
    N = int(round(total * SR))
    voice = np.zeros((N, 2), np.float32)
    fx = np.zeros((N, 2), np.float32)
    orig = np.zeros((N, 2), np.float32)
    music = np.zeros((N, 2), np.float32)
    speech_mask = np.zeros(N, bool)
    meter = pyln.Meter(SR)
    # muzyka
    mus = read_f32(os.environ["MUSIC"])
    mus *= 10 ** ((-16 - meter.integrated_loudness(mus)) / 20)
    fxs = synth_card_fx()
    pos = 0.0
    mpos = 0
    sections = []   # (start_s, dur_s, kind)
    for (kind, p), dur in zip(sc, durs):
        s = int(round(pos * SR))
        pid = p.stem.split("_")[-1]
        if kind == "orig":
            x = read_f32(WD / f"orig_{pid}.wav")
            g = 10 ** ((-18 - meter.integrated_loudness(x)) / 20)
            x *= g
            n = min(len(x), int(orig_frames(pid) / FPS * SR))
            ramp = np.ones(n, np.float32)
            a = int(0.15 * SR); b = int(0.15 * SR)
            ramp[:a] = np.linspace(0, 1, a); ramp[-b:] = np.linspace(1, 0, b)
            orig[s:s + n] += x[:n] * ramp[:, None]
        elif kind == "card":
            fx[s:s + len(fxs)] += fxs[:N - s]
        elif kind in ("photos", "intro"):
            if kind == "intro":
                key, n_s = "cm0", len(data.INTRO["spoken"][lang])
            else:
                idx = [q["id"] for q in data.PLACES].index(pid)
                key, n_s = f"cm{idx + 1}", len(data.PLACES[idx]["spoken"][lang])
            sents = narration(lang, key, n_s)
            d, starts, frames = timeline(sents)
            for sn, st in zip(sents, starts):
                a = s + int(st * SR)
                voice[a:a + len(sn), 0] += sn; voice[a:a + len(sn), 1] += sn
                speech_mask[a:a + len(sn)] = True
            sections.append((s, int(dur * SR), kind))
        elif kind == "credits":
            sections.append((s, int(dur * SR), "credits"))
        pos += dur
    # muzyka pod lektorem i na planszach z napisami końcowymi
    for s, n, kind in sections:
        seg = np.zeros((n, 2), np.float32)
        take = mus[mpos:mpos + n] if mpos + n <= len(mus) else np.concatenate([mus[mpos:], mus[:n - (len(mus) - mpos)]])
        mpos = (mpos + n) % len(mus)
        seg[:len(take)] = take[:n]
        f = int(1.0 * SR)
        seg[:f] *= np.linspace(0, 1, f)[:, None]; seg[-f:] *= np.linspace(1, 0, f)[:, None]
        music[s:s + n] += seg * (2.0 if kind == "credits" else 1.0)
    # poziomy: lektor ~ -16 LUFS na oknach mowy, muzyka 16 dB niżej na tych samych oknach
    vm = voice[speech_mask]
    gv = 10 ** ((-16 - meter.integrated_loudness(vm)) / 20)
    voice *= gv
    mm = music[speech_mask]
    gm = 10 ** (((-16 - 16) - meter.integrated_loudness(mm)) / 20)
    music *= gm
    fx *= 10 ** (-3 / 20)
    mix = voice + music + fx + orig
    sf = WD / lang
    np.save(sf / "stem_voice.npy", voice.astype(np.float16)); np.save(sf / "stem_music.npy", music.astype(np.float16))
    stats = {"total_s": total,
             "voice_on_speech_LUFS": float(meter.integrated_loudness(voice[speech_mask])),
             "music_on_speech_LUFS": float(meter.integrated_loudness(music[speech_mask])),
             "peak_mix": float(np.abs(mix).max())}
    stats["voice_minus_music_dB"] = stats["voice_on_speech_LUFS"] - stats["music_on_speech_LUFS"]
    json.dump(stats, open(sf / "mix_stats.json", "w"), indent=1)
    print(json.dumps(stats, indent=1))
    wav = sf / "mix_raw.wav"
    pk = float(np.abs(mix).max())
    if pk > 0.9:
        mix = mix * (0.9 / pk)   # skala liniowa przed loudnorm (bez obcinania)
    pcm = (np.clip(mix, -1, 1) * 32767).astype("<i2")
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())


def cmd_master(lang):
    sf = WD / lang
    raw = sf / "mix_raw.wav"
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(raw), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True)
    j = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
    flt = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
           f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true:print_format=summary,alimiter=limit=0.84:level=disabled")
    mast = sf / "mix_master.wav"
    sh(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-af", flt, "-ar", str(SR), "-c:a", "pcm_s16le", str(mast)])
    out = sf / f"film1_commentary_{lang}.mp4"
    tmp = str(out) + ".tmp.mp4"
    sh(["ffmpeg", "-y", "-loglevel", "error", "-i", str(sf / "video_silent.mp4"), "-i", str(mast), "-map", "0:v", "-map", "1:a",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-f", "mp4", tmp])
    os.replace(tmp, out)
    print("final", out)


def cmd_docs():
    """CREDITS.md + opis do YouTube (PL/EN) z tych samych danych co plansza końcowa."""
    m = manifest()
    L = ["# Źródła i licencje / Credits and licences", "",
         "## Film oryginalny / Original video", "",
         f"- „{data.SRC['title']}” — {data.SRC['author']} — {data.SRC['url']}",
         f"- Licencja / Licence: {data.SRC['license']} (YouTube: Creative Commons Attribution, CC BY 3.0)",
         "- Użyte fragmenty / Excerpts used (s): " + ", ".join(f"{k} {a:.1f}–{b:.1f}" for k, (a, b) in data.WINDOWS.items()), "",
         "## Zdjęcia / Photos (Wikimedia Commons)", ""]
    for p in data.PLACES:
        L.append(f"### {p['name']['pl']} / {p['name']['en']}")
        seen = set()
        for pid, _ in p["shots"]:
            if pid in seen:
                continue
            seen.add(pid)
            x = m[pid]
            lu = LIC_URL.get(x["license"], "") or x.get("license_url", "")
            L.append(f"- **{x['title'].replace('File:', '')}** — {artist(pid, 'en')} — {x['license']}" + (f" ({lu})" if lu else "") + f" — {x['page']}")
        L.append("- Źródła faktów / fact sources: " + ", ".join(p["sources"]))
        L.append("")
    L += ["## Zmiany / Changes", "- Zdjęcia: kadrowanie 16:9, powolny ruch kamery; bez korekty kolorów. / Photos: 16:9 crop and slow camera move; no colour grading.",
          "- Oryginał: fragmenty ≤7 s, skalowanie do 1080p, wyciszenie na końcu fragmentu. / Original: excerpts ≤7 s, scaled to 1080p, fade-out at the end.", "",
          "## Dźwięk / Sound",
          "- Muzyka / Music: „Transformations 3”, HoliznaCC0, CC0 1.0 — https://freemusicarchive.org/music/holiznacc0/transformations/transformations-3/",
          "- Lektor PL: Piper pl_PL-gosia-medium (synteza mowy). Lektor EN: Kokoro-82M, af_heart (Apache-2.0), synthetic speech.",
          "- Efekt planszy „And what it really looks like” generowany w kodzie. / Card sound generated in code.", ""]
    out = WD / "CREDITS.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "prep": cmd_prep()
    elif c == "preview": cmd_preview(sys.argv[2])
    elif c == "render": cmd_render(sys.argv[2])
    elif c == "concat": cmd_concat(sys.argv[2])
    elif c == "mix": cmd_mix(sys.argv[2])
    elif c == "master": cmd_master(sys.argv[2])
    elif c == "docs": cmd_docs()
    else: raise SystemExit(c)
