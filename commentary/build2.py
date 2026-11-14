#!/usr/bin/env python3
"""Montaż komentarza v2 (dynamiczny). Użycie (SP, SRC, TTS2_PL, TTS2_EN, MUSIC w środowisku):
  build2.py plan LANG       - wypisuje plan scen z czasami (po TTS)
  build2.py render LANG     - sceny wideo (wznawialne, Pool(2))
  build2.py concat LANG     - łączy sceny (-c copy)
  build2.py mix LANG        - miks, pomiary przerw/poziomów
  build2.py master LANG     - loudnorm 2-pass + mux
  build2.py docs            - CREDITS_v2.md
Zasady (audyt VidIQ): lektor przez cały fragment oryginału, przerwy <= 3 s, hard cuts, liczby na ekranie, stempel werdyktu."""
import json, math, os, subprocess, sys, wave
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).parent))
import build as b          # narzędzia z v1 (wymaga SP w środowisku)
import data2 as d

W, H, FPS, SR = b.W, b.H, b.FPS, b.SR
SP = b.SP
WD2 = SP / "cm2"
PH = b.PH
ACCENT = b.ACCENT
LEAD, GAP = 0.12, 0.28
LEAD_ORIG = 0.15


def orig_lead(sents, window_s):
    """luz w oknie oryginału dzielona po połowie przed i po mowie (przerwy <= 3 s po obu stronach)."""
    span = sum(len(x) for x in sents) / SR + GAP * (len(sents) - 1)
    return max(LEAD_ORIG, (window_s - span) / 2)
CARD2_S, CARD2_HIT = 1.4, 0.42
CRED_S = 5.0
NCH = len(d.CH)

b.MOVES.update({
    "machu2@h1": ((0.50, 0.45, 1.00), (0.50, 0.52, 1.28)),
    "machu1@h2": ((0.58, 0.55, 1.28), (0.45, 0.50, 1.00)),
    "ometepe1@1": ((0.60, 0.50, 1.25), (0.45, 0.52, 1.00)),
})
PROMISE_BG = ["machu1", "burning1", "copper1", "grand1", "nepal3", "machu2", "nepal3", "utah3",
              "fuego1", "copper2", "burning1", "ometepe1", "grand3", "machu1"]


# ---------- czas i narracja ----------
def li_of(lang):
    return 0 if lang == "pl" else 1


def narr(lang, key, n):
    dd = Path(os.environ["TTS2_PL" if lang == "pl" else "TTS2_EN"])
    f = dd / (f"piper_{key}_pl_pl_PL-gosia-medium.wav" if lang == "pl" else f"kokoro_{key}_en_af_heart.wav")
    x, sr = b.read_wav(f)
    return [b.to48(s, sr) for s in b.split_by_silence(x, sr, n)]


def timeline2(sents, tail, lead=LEAD):
    dur = [len(s) / SR for s in sents]
    starts, t = [], lead
    for di in dur:
        starts.append(t); t += di + GAP
    total = starts[-1] + dur[-1] + tail
    return dur, starts, math.ceil(total * FPS)


def win_frames(wid):
    s, e = d.WINDOWS[wid]
    return int(round((e - s) * FPS))


# ---------- plan scen ----------
def plan(lang):
    P = []
    P.append(dict(id="hook1", kind="photos", key="w0a", pairs=d.HOOK1, shots=[("machu2", [0, 1, 2], "machu2@h1")],
                  pops={1: ("1912", "1912")}, chip=None, verdict=None, tail=0.10))
    P.append(dict(id="hook2", kind="photos", key="w0b", pairs=d.HOOK2, shots=[("machu1", [0, 1, 2], "machu1@h2")],
                  pops={2: ("100+ lat", "100+ years")}, chip=None, verdict=None, tail=0.10))
    P.append(dict(id="hook3", kind="orig", key="w0c", pairs=d.HOOK3, win="machu", chip=None))
    P.append(dict(id="promise", kind="promise", key="w0d", pairs=d.HOOK4, tail=0.25))
    for n, ch in enumerate(d.CH, 1):
        chip = f"{n}/{NCH} · {ch['mech'][lang]}"
        if ch["a"]:
            P.append(dict(id=f"{ch['id']}_orig", kind="orig", key=f"w{n}a", pairs=ch["a"], win=ch["id"], chip=chip))
        P.append(dict(id=f"{ch['id']}_card", kind="card", ch=ch, n=n))
        P.append(dict(id=f"{ch['id']}_photos", kind="photos", key=f"w{n}b", pairs=ch["b"],
                      shots=[(pid, idx, None) for pid, idx in ch["shots"]], pops=ch["pops"], chip=chip,
                      verdict=ch["verdict"], tail=1.2))
    P.append(dict(id="outro", kind="outro", key="w9", pairs=d.OUTRO, tail=0.8))
    for k in range(len(b.paginate(credit_lines(lang), per=24))):
        P.append(dict(id=f"credits_{k}", kind="credits", page=k))
    return P


def spec_out(spec, lang):
    return WD2 / lang / f"{spec['id']}.mp4"


# ---------- elementy graficzne ----------
def shadow_text(text, size, maxw, fill, path=b.FONT_B):
    """tekst bez tła, z miękkim cieniem (RGBA)."""
    f = b.font(path, size)
    d0 = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    lines = b.wrap(d0, text, f, maxw)
    lh = int(size * 1.22)
    w = int(max(d0.textlength(l, font=f) for l in lines)) + 60
    h = lh * len(lines) + 60
    sh_ = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sh_)
    for i, l in enumerate(lines):
        x = int((w - d0.textlength(l, font=f)) / 2)
        ds.text((x + 4, 30 + i * lh + 6), l, font=f, fill=(0, 0, 0, 230))
    sh_ = sh_.filter(ImageFilter.GaussianBlur(7))
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    im.alpha_composite(sh_)
    dr = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        x = int((w - d0.textlength(l, font=f)) / 2)
        dr.text((x, 30 + i * lh), l, font=f, fill=fill + (255,))
    return np.asarray(im)


def scaled(rgba, s):
    if abs(s - 1) < 1e-3:
        return rgba
    im = Image.fromarray(rgba, "RGBA")
    return np.asarray(im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BICUBIC))


def blend_c(frame, rgba, cx, cy, alpha=1.0):
    b.blend(frame, rgba, int(cx - rgba.shape[1] / 2), int(cy - rgba.shape[0] / 2), alpha)


def stamp_img(code, lang, size=100):
    v = d.VERDICT[code]
    txt, rgb = v[lang], v["rgb"]
    f = b.font(b.FONT_B, size)
    d0 = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    tw = int(d0.textlength(txt, font=f))
    pad = int(size * 0.38)
    w, h = tw + 2 * pad, int(size * 1.25) + 2 * pad
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.rounded_rectangle((0, 0, w - 1, h - 1), radius=int(size * 0.25), fill=(8, 10, 14, 215), outline=rgb + (255,), width=max(6, size // 12))
    dr.text((pad, pad - size // 10), txt, font=f, fill=rgb + (255,))
    im = im.rotate(5, expand=True, resample=Image.BICUBIC)
    return np.asarray(im)


def slam_frame(frame, stamp, t, cx, cy):
    """t = czas od uderzenia stempla; wjazd 0.2 s, błysk, drżenie."""
    if t < 0:
        return frame
    p = min(1.0, t / 0.2)
    s = 2.3 - 1.3 * (1 - (1 - p) ** 3)
    a = min(1.0, p * 3)
    dx = dy = 0
    if 0.2 <= t < 0.5:
        k = (0.5 - t) / 0.3
        dx, dy = int(9 * k * math.sin(t * 90)), int(7 * k * math.cos(t * 70))
    blend_c(frame, scaled(stamp, s), cx + dx, cy + dy, a)
    if 0.17 <= t < 0.27:
        frame = np.clip(frame.astype(np.float32) + 45 * (1 - (t - 0.17) / 0.1), 0, 255).astype(np.uint8)
    return frame


def caption_boxes(pairs, lang):
    li = li_of(lang)
    return [b.text_box(d.disp(p[li]), size=40, maxw=1560) for p in pairs]


def pop_boxes(pops, lang):
    li = li_of(lang)
    out = {}
    for k, v in pops.items():
        out[k] = shadow_text(v[li], 150, 1500, ACCENT)
    return out


def credit_tag2(pid, lang):
    return b.text_box(b.credit_tag(pid, lang), size=26, maxw=900, path=b.FONT_R, bg=(8, 10, 14, 150), pad=(18, 10))


def src_tag(lang):
    return b.text_box(f"{'Źródło' if lang == 'pl' else 'Source'}: {d.SRC['author']} · CC BY", size=28, maxw=900, path=b.FONT_M, bg=(8, 10, 14, 170), pad=(20, 12))


def chip_box(txt):
    return b.text_box(txt, size=36, maxw=1100, path=b.FONT_B, fill=(10, 12, 18), bg=ACCENT + (235,), pad=(24, 12))


def overlay_common(frame, t, dur, starts, caps, pops, popbox, chip, tag):
    if chip is not None:
        b.blend(frame, chip, 40, 36)
    if tag is not None:
        b.blend(frame, tag, W - tag.shape[1] - 40, 36)
    for si in range(len(dur)):
        s0, s1 = starts[si] - 0.05, starts[si] + dur[si] + 0.25
        if s0 <= t <= s1:
            al = min(1.0, (t - s0) / 0.12)
            c = caps[si]
            b.blend(frame, c, (W - c.shape[1]) // 2, H - c.shape[0] - 56, al)
        if si in pops and starts[si] - 0.02 <= t <= starts[si] + dur[si] + 0.45:
            q = t - starts[si]
            s = 1.0 + 0.28 * max(0.0, 1 - q / 0.18) ** 2
            pb = scaled(popbox[si], s)
            blend_c(frame, pb, W * 0.5, H * 0.34)
    return frame


# ---------- sceny ----------
def render_photos2(args):
    spec, lang = args
    out = spec_out(spec, lang)
    sents = narr(lang, spec["key"], len(spec["pairs"]))
    dur, starts, frames = timeline2(sents, spec["tail"])
    if b.valid(out, frames):
        return str(out), frames
    shots = []
    for pid, idx, ov in spec["shots"]:
        shots.append((pid, idx, ov, Image.open(PH / f"{pid}.jpg").convert("RGB")))
    bounds = [0.0]
    for k in range(1, len(shots)):
        a = shots[k - 1][1][-1]; c = shots[k][1][0]
        bounds.append((starts[a] + dur[a] + starts[c]) / 2)
    bounds.append(frames / FPS)
    XF = 0.12
    caps = caption_boxes(spec["pairs"], lang)
    popbox = pop_boxes(spec["pops"], lang) if spec.get("pops") else {}
    chip = chip_box(spec["chip"]) if spec.get("chip") else None
    tags = {pid: credit_tag2(pid, lang) for pid, _, _, _ in shots}
    stamp = stamp_img(spec["verdict"], lang) if spec.get("verdict") else None
    pipe, tmp = b.ffmpeg_pipe(out)
    for fr in range(frames):
        t = fr / FPS
        acc = np.zeros((H, W, 3), np.float32); wsum = 0.0; cur = shots[0][0]
        for k, (pid, idx, ov, im) in enumerate(shots):
            lo = bounds[k] - (XF if k > 0 else 0)
            hi = bounds[k + 1] + (XF if k < len(shots) - 1 else 0)
            if not (lo <= t <= hi):
                continue
            if k > 0 and t < bounds[k] + XF:
                a = b.smooth((t - (bounds[k] - XF)) / (2 * XF))
            elif k < len(shots) - 1 and t > bounds[k + 1] - XF:
                a = 1 - b.smooth((t - (bounds[k + 1] - XF)) / (2 * XF))
            else:
                a = 1.0
            mvk = b.MOVES[ov] if ov else b.MOVES.get(f"{pid}@{k}", b.MOVES[pid])
            acc += b.photo_frame(im, mvk, (t - lo) / (hi - lo)).astype(np.float32) * a
            wsum += a
            if a >= 0.5:
                cur = pid
        frame = (acc / max(wsum, 1e-6)).astype(np.uint8)
        frame = overlay_common(frame, t, dur, starts, caps, spec.get("pops") or {}, popbox, chip, tags[cur])
        if stamp is not None:
            frame = slam_frame(frame, stamp, t - starts[-1], W * 0.5, H * 0.42)
        pipe.stdin.write(frame.tobytes())
    b.finish_pipe(pipe, tmp, out)
    return str(out), frames


def render_orig2(args):
    spec, lang = args
    out = spec_out(spec, lang)
    s0, e0 = d.WINDOWS[spec["win"]]
    frames = win_frames(spec["win"])
    sents = narr(lang, spec["key"], len(spec["pairs"]))
    dur, starts, _ = timeline2(sents, 0.0, orig_lead(sents, frames / FPS))
    end = starts[-1] + dur[-1]
    if end > frames / FPS - 0.12:
        raise RuntimeError(f"{spec['id']} {lang}: lektor {end:.2f}s dłuższy niż fragment {frames / FPS:.2f}s")
    if b.valid(out, frames):
        return str(out), frames
    caps = caption_boxes(spec["pairs"], lang)
    chip = chip_box(spec["chip"]) if spec.get("chip") else None
    tag = src_tag(lang)
    cmd = ["ffmpeg", "-loglevel", "error", "-ss", f"{s0:.3f}", "-i", os.environ["SRC"], "-t", f"{frames / FPS + 0.2:.3f}",
           "-vf", f"scale={W}:{H}:flags=lanczos,fps={FPS},setsar=1", "-an", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    dec = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    pipe, tmp = b.ffmpeg_pipe(out)
    for fr in range(frames):
        raw = dec.stdout.read(W * H * 3)
        if len(raw) < W * H * 3:
            raise RuntimeError(f"{spec['id']}: za mało klatek ({fr}/{frames})")
        frame = np.frombuffer(raw, np.uint8).reshape(H, W, 3).copy()
        frame = overlay_common(frame, fr / FPS, dur, starts, caps, {}, {}, chip, tag)
        pipe.stdin.write(frame.tobytes())
    dec.stdout.close(); dec.terminate()
    b.finish_pipe(pipe, tmp, out)
    return str(out), frames


def bg_gradient():
    base = np.zeros((H, W, 3), np.uint8)
    yy = np.linspace(0, 1, H)[:, None]
    base[:] = (np.array([10, 14, 22]) * (1 - yy) + np.array([22, 30, 44]) * yy)[:, None, :].astype(np.uint8)
    return base


def render_card2(args):
    spec, lang = args
    out = spec_out(spec, lang)
    frames = int(round(CARD2_S * FPS))
    if b.valid(out, frames):
        return str(out), frames
    ch = spec["ch"]
    main = b.text_box("And what it really looks like", size=104, maxw=1700, path=b.FONT_B, bg=None, pad=(0, 0))
    sub = b.text_box(ch["name"][lang], size=46, maxw=1500, path=b.FONT_M, bg=None, fill=(210, 215, 225), pad=(0, 0))
    mech = b.text_box(f"{spec['n']}/{NCH} · {ch['mech'][lang]}", size=40, maxw=900, path=b.FONT_B, bg=None, fill=ACCENT, pad=(0, 0))
    base = bg_gradient()
    pipe, tmp = b.ffmpeg_pipe(out)
    hit = CARD2_HIT
    for fr in range(frames):
        t = fr / FPS
        f = base.copy()
        lw = int(900 * b.smooth(t / hit))
        f[H // 2 + 90:H // 2 + 96, (W - lw) // 2:(W + lw) // 2] = ACCENT
        blend_c(f, mech, W / 2, H // 2 - 190, b.smooth((t - 0.1) / 0.25))
        if t >= hit:
            a = b.smooth((t - hit) / 0.18)
            b.blend(f, main, (W - main.shape[1]) // 2, H // 2 - 80 - int(10 * (1 - a)), a)
            b.blend(f, sub, (W - sub.shape[1]) // 2, H // 2 + 130, b.smooth((t - hit - 0.1) / 0.2))
            if t - hit < 0.06:
                f = np.clip(f.astype(np.float32) + 90 * (1 - (t - hit) / 0.06), 0, 255).astype(np.uint8)
        pipe.stdin.write(f.tobytes())
    b.finish_pipe(pipe, tmp, out)
    return str(out), frames


def render_promise(args):
    spec, lang = args
    out = spec_out(spec, lang)
    li = li_of(lang)
    sents = narr(lang, spec["key"], len(spec["pairs"]))
    dur, starts, frames = timeline2(sents, spec["tail"])
    if b.valid(out, frames):
        return str(out), frames
    n = len(sents)
    bounds = [0.0] + [(starts[k] + dur[k] + starts[k + 1]) / 2 for k in range(n - 1)] + [frames / FPS]
    imgs = {pid: Image.open(PH / f"{pid}.jpg").convert("RGB") for pid in set(PROMISE_BG)}
    tags = {pid: credit_tag2(pid, lang) for pid in imgs}
    wordidx = {k: i for i, k in enumerate(d.HOOK4_WORD_IDX)}
    texts = {}
    for k, p in enumerate(spec["pairs"]):
        txt = d.disp(p[li]).rstrip(".")
        if k in wordidx:
            texts[k] = shadow_text(d.MECH_WORDS[lang][wordidx[k]].upper(), 200, 1700, ACCENT)
        else:
            texts[k] = shadow_text(txt, 86, 1500, (255, 255, 255))
    caps = caption_boxes(spec["pairs"], lang)
    pipe, tmp = b.ffmpeg_pipe(out)
    for fr in range(frames):
        t = fr / FPS
        k = max(i for i in range(n) if bounds[i] <= t + 1e-9) if t < bounds[-1] else n - 1
        pid = PROMISE_BG[k]
        prog = (t - bounds[k]) / max(bounds[k + 1] - bounds[k], 1e-6)
        m0, m1 = b.MOVES[pid]
        mvk = (m0, m1) if k % 2 == 0 else (m1, m0)   # sprawdzone kadry (np. bez skrzydła samolotu na burning1)
        frame = b.photo_frame(imgs[pid], mvk, prog)
        frame = (frame.astype(np.float32) * 0.46).astype(np.uint8)
        q = t - bounds[k]
        s = 1.0 + 0.22 * max(0.0, 1 - q / 0.16) ** 2
        blend_c(frame, scaled(texts[k], s), W / 2, H / 2 - 20)
        tg = tags[pid]
        b.blend(frame, tg, W - tg.shape[1] - 40, 36)
        if k in wordidx:  # licznik mechanizmów
            dots = b.text_box(f"{wordidx[k] + 1}/7", size=34, maxw=300, path=b.FONT_B, bg=(8, 10, 14, 150), pad=(20, 10))
            b.blend(frame, dots, 40, 36)
        pipe.stdin.write(frame.tobytes())
    b.finish_pipe(pipe, tmp, out)
    return str(out), frames


def render_outro(args):
    spec, lang = args
    out = spec_out(spec, lang)
    li = li_of(lang)
    sents = narr(lang, spec["key"], len(spec["pairs"]))
    dur, starts, frames = timeline2(sents, spec["tail"])
    if b.valid(out, frames):
        return str(out), frames
    tally = d.tally()
    stamps = [(code, idx, stamp_img(code, lang, 62)) for code, idx in d.OUTRO_TALLY]
    counts = {c: shadow_text(f"{tally[c]}×", 110, 400, d.VERDICT[c]["rgb"]) for c, _ in d.OUTRO_TALLY}
    texts = [shadow_text(d.disp(p[li]), 84, 1500, (255, 255, 255)) for p in spec["pairs"]]
    caps = caption_boxes(spec["pairs"], lang)
    base = bg_gradient()
    pipe, tmp = b.ffmpeg_pipe(out)
    for fr in range(frames):
        t = fr / FPS
        f = base.copy()
        for row, (code, idx, st) in enumerate(stamps):
            if t >= starts[idx]:
                y = 215 + row * 175
                blend_c(f, counts[code], 560, y)
                f = slam_frame(f, st, t - starts[idx], 1180, y)
        k = max([i for i in range(len(starts)) if starts[i] - 0.05 <= t] or [0])
        if k not in (1, 2, 3):
            q = t - starts[k]
            s = 1.0 + 0.2 * max(0.0, 1 - q / 0.16) ** 2
            blend_c(f, scaled(texts[k], s), W / 2, 790 if k >= 4 else 480)
        pipe.stdin.write(f.tobytes())
    b.finish_pipe(pipe, tmp, out)
    return str(out), frames


def credit_lines2(lang):
    return credit_lines(lang)


def credit_lines(lang):
    pl = lang == "pl"
    m = b.manifest()
    L = [("h", "Źródła i licencje" if pl else "Credits and licences"),
         ("p", ("Film oryginalny: " if pl else "Original video: ") + f"„{d.SRC['title']}” — {d.SRC['author']} — {d.SRC['url']}"),
         ("p", "Licencja: Creative Commons Attribution (CC BY), wg strony filmu na YouTube. Fragmenty do 7 s jako cytat; muzyka i ujęcia w oryginale mogą mieć własne prawa." if pl
          else "Licence: Creative Commons Attribution (CC BY), per the YouTube video page. Excerpts up to 7 s used as quotation; music and footage inside the original may carry their own rights.")]
    for ch in d.CH:
        L.append(("s", ch["name"][lang]))
        seen = set()
        for pid, _ in ch["shots"]:
            if pid in seen:
                continue
            seen.add(pid)
            L.append(("p", f"{b.artist(pid, lang)} — {m[pid]['license']} — {m[pid]['page']}"))
    L.append(("s", "Dźwięk" if pl else "Sound"))
    L.append(("p", "Muzyka: „Transformations 3”, HoliznaCC0 (CC0 1.0), Free Music Archive" if pl else "Music: “Transformations 3” by HoliznaCC0 (CC0 1.0), Free Music Archive"))
    L.append(("p", "Lektor: Piper pl_PL-gosia-medium (synteza mowy)" if pl else "Voice: Kokoro-82M, af_heart (Apache-2.0), synthetic speech"))
    L.append(("p", "Zmiany w zdjęciach: kadrowanie 16:9, ruch kamery, bez korekty kolorów." if pl else "Changes to photos: 16:9 crop and camera move, no colour grading."))
    return L


def render_credits2(args):
    spec, lang = args
    out = spec_out(spec, lang)
    frames = int(CRED_S * FPS)
    if b.valid(out, frames):
        return str(out), frames
    pg = b.paginate(credit_lines(lang), per=24)[spec["page"]]
    fh, fs, fp = b.font(b.FONT_B, 50), b.font(b.FONT_M, 32), b.font(b.FONT_R, 25)
    im = Image.new("RGB", (W, H), (12, 16, 24))
    dr = ImageDraw.Draw(im)
    y = 60
    for kind, txt in pg:
        if kind == "h":
            dr.text((90, y), txt, font=fh, fill=(255, 255, 255)); y += 84
        elif kind == "s":
            y += 6; dr.text((90, y), txt, font=fs, fill=ACCENT); y += 48
        else:
            for line in b.wrap(dr, txt, fp, W - 180):
                dr.text((90, y), line, font=fp, fill=(214, 220, 230)); y += 34
    base = np.asarray(im)
    pipe, tmp = b.ffmpeg_pipe(out)
    for fr in range(frames):
        t = fr / FPS
        fa = 1 - b.smooth((t - (CRED_S - 0.3)) / 0.3) if spec["page"] == -1 else 1.0
        pipe.stdin.write(base.tobytes())
    b.finish_pipe(pipe, tmp, out)
    return str(out), frames


RENDER = {"photos": render_photos2, "orig": render_orig2, "card": render_card2, "promise": render_promise,
          "outro": render_outro, "credits": render_credits2}


def run_one(args):
    spec, lang = args
    return spec["id"], RENDER[spec["kind"]](args)


def cmd_plan(lang):
    t = 0.0
    for sp in plan(lang):
        if sp["kind"] == "card":
            dur = CARD2_S
        elif sp["kind"] == "credits":
            dur = CRED_S
        elif sp["kind"] == "orig":
            dur = win_frames(sp["win"]) / FPS
            sents = narr(lang, sp["key"], len(sp["pairs"]))
            ld = orig_lead(sents, dur)
            dd, st, _ = timeline2(sents, 0, ld)
            print(f"   voice {st[0]:.2f}-{st[-1] + dd[-1]:.2f} / {dur:.2f}")
        else:
            sents = narr(lang, sp["key"], len(sp["pairs"]))
            dd, st, fr = timeline2(sents, sp["tail"])
            dur = fr / FPS
            shots = sp.get("shots")
            if shots:
                bd = [0.0]
                for k in range(1, len(shots)):
                    a = shots[k - 1][1][-1]; c = shots[k][1][0]
                    bd.append((st[a] + dd[a] + st[c]) / 2)
                bd.append(dur)
                print("   shots:", [(s[0], round(bd[i + 1] - bd[i], 1)) for i, s in enumerate(shots)])
        print(f"{t:7.1f}s  {sp['id']:16s} {sp['kind']:8s} {dur:5.1f}s")
        t += dur
    print(f"RAZEM {t:.1f} s ({t / 60:.2f} min)")


def cmd_render(lang):
    (WD2 / lang).mkdir(parents=True, exist_ok=True)
    specs = plan(lang)
    with Pool(2) as pool:
        for sid, r in pool.imap(run_one, [(s, lang) for s in specs]):
            print("ok", sid, r[1], flush=True)


def cmd_concat(lang):
    specs = plan(lang)
    lst = WD2 / lang / "concat.txt"
    lst.write_text("".join(f"file '{spec_out(s, lang)}'\n" for s in specs))
    out = WD2 / lang / "video_silent.mp4"
    tmp = str(out) + ".tmp.mp4"
    b.sh(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", "-f", "mp4", tmp])
    os.replace(tmp, out)
    print("concat ok", out)


# ---------- dźwięk ----------
def synth_card_fx2():
    rng = np.random.default_rng(7)
    n = int(CARD2_S * SR)
    t = np.arange(n) / SR
    from scipy.signal import butter, sosfilt
    noise = rng.standard_normal(n).astype(np.float32)
    whoosh = np.zeros(n, np.float32)
    hit_t = CARD2_HIT
    for fc in (250, 500, 1000, 2000, 4000, 8000):
        sos = butter(2, [fc / 1.5, min(fc * 1.5, 20000)], btype="band", fs=SR, output="sos")
        band = sosfilt(sos, noise)
        centre = 250 * 2 ** (np.clip(t / hit_t, 0, 1) * 4.5)
        whoosh += band * np.exp(-((np.log2(fc) - np.log2(centre)) / 0.8) ** 2)
    whoosh *= np.where(t < hit_t, (t / hit_t) ** 2.2, np.exp(-(t - hit_t) * 9))
    whoosh /= np.abs(whoosh).max() + 1e-9
    th = np.clip(t - hit_t, 0, None) * (t >= hit_t)
    sub = np.sin(2 * np.pi * 55 * th) * np.exp(-th * 5) * (t >= hit_t)
    chime = np.zeros(n, np.float32)
    for f0, off, amp in ((659.25, 0.0, 0.5), (987.77, 0.10, 0.4), (1318.5, 0.2, 0.25)):
        tt = np.clip(t - hit_t - off, 0, None) * (t >= hit_t + off)
        chime += amp * np.sin(2 * np.pi * f0 * tt) * np.exp(-tt * 4.5) * (t >= hit_t + off)
    x = 0.55 * whoosh + 0.7 * sub + 0.45 * chime
    x *= np.minimum(1, (CARD2_S - t) / 0.1)
    x = (x / (np.abs(x).max() + 1e-9) * 0.6).astype(np.float32)
    return np.stack([x, x], 1)


def synth_stamp_fx():
    rng = np.random.default_rng(11)
    n = int(0.7 * SR)
    t = np.arange(n) / SR
    thump = np.sin(2 * np.pi * (90 - 40 * np.clip(t / 0.25, 0, 1)) * t) * np.exp(-t * 11)
    from scipy.signal import butter, sosfilt
    sos = butter(2, [200, 3500], btype="band", fs=SR, output="sos")
    click = sosfilt(sos, rng.standard_normal(n)) * np.exp(-t * 55)
    x = 0.9 * thump + 0.35 * click / (np.abs(click).max() + 1e-9)
    x *= np.minimum(1, (0.7 - t) / 0.08)
    x = (x / (np.abs(x).max() + 1e-9) * 0.65).astype(np.float32)
    return np.stack([x, x], 1)


def orig_audio(wid):
    s, e = d.WINDOWS[wid]
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{s:.3f}", "-t", f"{win_frames(wid) / FPS:.3f}", "-i", os.environ["SRC"],
                        "-vn", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, dtype="<f4").reshape(-1, 2).copy()


def cmd_mix(lang, orig_lufs=-26.0, music_below=15.0):
    import pyloudnorm as pyln
    specs = plan(lang)
    durs, starts_s = [], []
    t = 0.0
    for sp in specs:
        fr = b.nframes(spec_out(sp, lang))
        durs.append(fr / FPS); starts_s.append(t); t += fr / FPS
    total = t
    N = int(round(total * SR))
    voice = np.zeros((N, 2), np.float32); fx = np.zeros((N, 2), np.float32)
    orig = np.zeros((N, 2), np.float32); music = np.zeros((N, 2), np.float32)
    mask = np.zeros(N, bool)
    meter = pyln.Meter(SR)
    cfx, sfx = synth_card_fx2(), synth_stamp_fx()
    segs = []  # (t0, t1) mowy w sekundach
    for sp, dur, t0 in zip(specs, durs, starts_s):
        s = int(round(t0 * SR))
        k = sp["kind"]
        if k == "card":
            fx[s:s + len(cfx)] += cfx[:N - s]
            continue
        if k == "credits":
            continue
        sents = narr(lang, sp["key"], len(sp["pairs"]))
        if k == "orig":
            dd, st, _ = timeline2(sents, 0, orig_lead(sents, dur))
            x = orig_audio(sp["win"])
            x *= 10 ** ((orig_lufs - meter.integrated_loudness(x)) / 20)
            n = min(len(x), int(dur * SR), N - s)
            ramp = np.ones(n, np.float32); a = int(0.2 * SR)
            ramp[:a] = np.linspace(0, 1, a); ramp[-a:] = np.linspace(1, 0, a)
            orig[s:s + n] += x[:n] * ramp[:, None]
        else:
            dd, st, _ = timeline2(sents, sp.get("tail", 0.2))
        for sn, ts in zip(sents, st):
            a = s + int(ts * SR)
            voice[a:a + len(sn), 0] += sn; voice[a:a + len(sn), 1] += sn
            mask[a:a + len(sn)] = True
            segs.append((t0 + ts, t0 + ts + len(sn) / SR))
        if k == "photos" and sp.get("verdict"):
            a = s + int(st[-1] * SR)
            fx[a:a + len(sfx)] += sfx[:N - a]
        if k == "outro":
            for code, idx in d.OUTRO_TALLY:
                a = s + int(st[idx] * SR)
                fx[a:a + len(sfx)] += sfx[:N - a]
    mus = b.read_f32(os.environ["MUSIC"])
    mus *= 10 ** ((-16 - meter.integrated_loudness(mus)) / 20)
    reps = int(math.ceil(N / len(mus)))
    music[:] = np.concatenate([mus] * reps)[:N]
    f_in, f_out = int(0.5 * SR), int(2.0 * SR)
    music[:f_in] *= np.linspace(0, 1, f_in)[:, None]; music[-f_out:] *= np.linspace(1, 0, f_out)[:, None]
    cred0 = int(round(starts_s[[i for i, s_ in enumerate(specs) if s_["kind"] == "credits"][0]] * SR))
    music[cred0:] *= 2.0
    gv = 10 ** ((-16 - meter.integrated_loudness(voice[mask])) / 20)
    voice *= gv
    gm = 10 ** (((-16 - music_below) - meter.integrated_loudness(music[mask])) / 20)
    music *= gm
    fx *= 10 ** (-3 / 20)
    mix = voice + music + fx + orig
    sf = WD2 / lang
    np.save(sf / "stem_voice.npy", voice.astype(np.float16)); np.save(sf / "stem_music.npy", music.astype(np.float16))
    # najdłuższe przerwy w mowie
    segs.sort()
    gaps = [(segs[i + 1][0] - segs[i][1], segs[i][1]) for i in range(len(segs) - 1)]
    gaps.sort(reverse=True)
    words = sum(len(" ".join(d.spoken(p[li_of(lang)]) for p in sp["pairs"]).split()) for sp in specs if "pairs" in sp)
    speech_s = sum(e - s_ for s_, e in segs)
    stats = {"total_s": total, "speech_s": speech_s, "speech_share": speech_s / total, "words": words,
             "wpm": words / (total / 60), "words_per_speech_min": words / (speech_s / 60),
             "longest_gaps_s": [(round(g, 2), round(at, 1)) for g, at in gaps[:6]],
             "voice_on_speech_LUFS": float(meter.integrated_loudness(voice[mask])),
             "music_on_speech_LUFS": float(meter.integrated_loudness(music[mask])),
             "orig_target_LUFS": orig_lufs, "peak_mix": float(np.abs(mix).max())}
    stats["voice_minus_music_dB"] = stats["voice_on_speech_LUFS"] - stats["music_on_speech_LUFS"]
    json.dump(stats, open(sf / "mix_stats.json", "w"), indent=1)
    print(json.dumps(stats, indent=1))
    pk = float(np.abs(mix).max())
    if pk > 0.9:
        mix = mix * (0.9 / pk)
    pcm = (np.clip(mix, -1, 1) * 32767).astype("<i2")
    with wave.open(str(sf / "mix_raw.wav"), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())


def cmd_master(lang):
    sf = WD2 / lang
    raw = sf / "mix_raw.wav"
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(raw), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True)
    j = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
    flt = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
           f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true:print_format=summary,alimiter=limit=0.75:level=disabled")
    mast = sf / "mix_master.wav"
    b.sh(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-af", flt, "-ar", str(SR), "-c:a", "pcm_s16le", str(mast)])
    out = sf / f"film1_v2_{lang}.mp4"
    tmp = str(out) + ".tmp.mp4"
    b.sh(["ffmpeg", "-y", "-loglevel", "error", "-i", str(sf / "video_silent.mp4"), "-i", str(mast), "-map", "0:v", "-map", "1:a",
          "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-f", "mp4", tmp])
    os.replace(tmp, out)
    print("final", out)


def cmd_docs():
    m = b.manifest()
    L = ["# Źródła i licencje / Credits and licences (v2)", "", "## Film oryginalny / Original video", "",
         f"- „{d.SRC['title']}” — {d.SRC['author']} — {d.SRC['url']}",
         f"- Licencja / Licence: {d.SRC['license']} (YouTube: Creative Commons Attribution, CC BY 3.0)",
         "- Użyte fragmenty / Excerpts used (s): " + ", ".join(f"{k} {a:.1f}–{e:.1f}" for k, (a, e) in d.WINDOWS.items()), "",
         "## Zdjęcia / Photos (Wikimedia Commons)", ""]
    for ch in d.CH:
        L.append(f"### {ch['name']['pl']} / {ch['name']['en']}")
        seen = set()
        for pid, _ in ch["shots"]:
            if pid in seen:
                continue
            seen.add(pid)
            x = m[pid]
            lu = b.LIC_URL.get(x["license"], "") or x.get("license_url", "")
            L.append(f"- **{x['title'].replace('File:', '')}** — {b.artist(pid, 'en')} — {x['license']}" + (f" ({lu})" if lu else "") + f" — {x['page']}")
        L.append("- Źródła faktów / fact sources: " + ", ".join(ch["sources"]))
        L.append("")
    L += ["## Dodatkowo użyte w zimnym starcie / Also used in the opening", "- machu1, machu2 (jak wyżej / as above)", "",
          "## Zmiany / Changes",
          "- Zdjęcia: kadrowanie 16:9, ruch kamery; bez korekty kolorów. / Photos: 16:9 crop and camera move; no colour grading.",
          "- Oryginał: fragmenty ≤7 s, skalowanie do 1080p, dźwięk oryginału ściszony pod lektorem. / Original: excerpts ≤7 s, scaled to 1080p, original sound lowered under the voice-over.", "",
          "## Dźwięk / Sound",
          "- Muzyka / Music: „Transformations 3”, HoliznaCC0, CC0 1.0 — https://freemusicarchive.org/music/holiznacc0/transformations/transformations-3/",
          "- Lektor PL: Piper pl_PL-gosia-medium. Lektor EN: Kokoro-82M, af_heart (Apache-2.0). Synthetic speech.",
          "- Efekty planszy i stempla generowane w kodzie. / Card and stamp sounds generated in code.", ""]
    out = WD2 / "CREDITS_v2.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    c = sys.argv[1]
    WD2.mkdir(parents=True, exist_ok=True)
    if c == "plan": cmd_plan(sys.argv[2])
    elif c == "render": cmd_render(sys.argv[2])
    elif c == "concat": cmd_concat(sys.argv[2])
    elif c == "mix": cmd_mix(sys.argv[2])
    elif c == "master": cmd_master(sys.argv[2])
    elif c == "docs": cmd_docs()
    else: raise SystemExit(c)
