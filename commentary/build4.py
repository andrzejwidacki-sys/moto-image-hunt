#!/usr/bin/env python3
"""Montaż komentarza v4 (Bangalore, „godziny zamiast kilometrów”). Środowisko: SP, SRC (film źródłowy),
TTS2_PL, TTS2_EN (katalogi wav z kluczami v4..), MUSIC. Zdjęcia: $SP/blr/ph (jpg + manifest.json).
  build4.py plan LANG | render LANG | concat LANG | mix LANG | master LANG | docs
Zasady jak v3: lektor od pierwszej klatki klipu, stały podpis źródła w rogu, stempel werdyktu w trakcie sceny
(potem plakietka w rogu), licznik werdyktów w rogu, twarde cięcia."""
import json, math, os, subprocess, sys, wave
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import build as b
b.PH = b.SP / "blr" / "ph"          # zdjęcia tego filmu (przed importem build2)
import build2 as v2
import data4 as d

v2.d = d
W, H, FPS, SR = b.W, b.H, b.FPS, b.SR
SP = b.SP
WD4 = SP / "cm4"
PH = b.PH
ACCENT = b.ACCENT
CARD_S, CARD_HIT = 1.4, 0.42
VDELAY = 0.5
ORIG_TAIL = 0.55
NCH = len(d.CH)
NAMES_ARTIST = {"pond1": "Vyacheslav Argenberg", "pond2": "Vyacheslav Argenberg", "pond3": "Richard Mortel",
                "coorg1": "Vaishak Kallore", "coorg2": "Rohithrajjc (Wikivoyage)", "coorg3": "AlvaKedak",
                "gok1": "Happyshopper", "gok2": "Axis of eran", "gok3": "Adityamadhav83",
                "ooty1": "Netha Hussain", "ooty2": "Amalshaji27", "ooty3": "Prakhar",
                "chik2": "Bhonsley", "chik3": "Shreyas Malavalli",
                "mys1": "Hari R", "mys2": "Ezhuttukari (Malayalam Wikipedia)", "mys3": "Sugnyan"}
b.ARTIST.clear(); b.ARTIST.update(NAMES_ARTIST)
b.ARTIST_NOTE.clear()
b.LIC_URL["CC BY 2.5"] = "https://creativecommons.org/licenses/by/2.5/"

b.MOVES.clear()
b.MOVES.update({
    "pond1": ((0.45, 0.55, 1.00), (0.55, 0.55, 1.12)),
    "pond1~2": ((0.62, 0.58, 1.15), (0.45, 0.55, 1.00)),
    "pond2": ((0.50, 0.50, 1.00), (0.55, 0.55, 1.12)),
    "pond3": ((0.55, 0.50, 1.00), (0.50, 0.50, 1.12)),
    "coorg1": ((0.50, 0.55, 1.00), (0.55, 0.55, 1.10)),
    "coorg1~2": ((0.55, 0.55, 1.12), (0.45, 0.50, 1.00)),
    "coorg2": ((0.50, 0.55, 1.00), (0.50, 0.50, 1.15)),
    "coorg3": ((0.62, 0.55, 1.12), (0.55, 0.55, 1.00)),
    "gok1": ((0.50, 0.55, 1.00), (0.50, 0.50, 1.12)),
    "gok1@h1": ((0.55, 0.55, 1.25), (0.45, 0.50, 1.00)),
    "gok1~2": ((0.50, 0.50, 1.12), (0.55, 0.60, 1.00)),
    "gok2": ((0.50, 0.50, 1.00), (0.45, 0.55, 1.12)),
    "gok3": ((0.50, 0.50, 1.00), (0.50, 0.45, 1.10)),
    "gok3~2": ((0.50, 0.45, 1.10), (0.50, 0.55, 1.00)),
    "ooty1": ((0.45, 0.55, 1.00), (0.55, 0.50, 1.12)),
    "ooty1~2": ((0.50, 0.50, 1.12), (0.40, 0.55, 1.00)),
    "ooty2": ((0.50, 0.45, 1.00), (0.50, 0.40, 1.15)),
    "ooty3": ((0.60, 0.50, 1.00), (0.55, 0.50, 1.20)),
    "chik2": ((0.50, 0.50, 1.00), (0.50, 0.60, 1.12)),
    "chik2~2": ((0.50, 0.55, 1.12), (0.50, 0.50, 1.00)),
    "chik3": ((0.50, 0.50, 1.00), (0.50, 0.60, 1.15)),
    "mys1": ((0.55, 0.50, 1.00), (0.65, 0.50, 1.12)),
    "mys1@h2": ((0.62, 0.55, 1.25), (0.50, 0.50, 1.00)),
    "mys1~2": ((0.68, 0.50, 1.12), (0.55, 0.50, 1.00)),
    "mys2": ((0.50, 0.50, 1.00), (0.50, 0.45, 1.12)),
    "mys3": ((0.50, 0.50, 1.00), (0.45, 0.50, 1.12)),
    "coorg2~2": ((0.50, 0.50, 1.15), (0.55, 0.55, 1.00)),
    "ooty2~2": ((0.50, 0.40, 1.15), (0.45, 0.50, 1.00)),
    "chik3~2": ((0.50, 0.60, 1.15), (0.50, 0.50, 1.00)),
})


def li_of(lang):
    return 0 if lang == "pl" else 1


def narr(lang, key, n):
    return v2.narr(lang, key, n)


def spec_out(spec, lang):
    return WD4 / lang / f"{spec['id']}.mp4"


def win_frames(wid):
    s, e = d.WINDOWS[wid]
    return int(round((e - s) * FPS))


def chip_text(ch, lang):
    return f"{ch['n']}/{NCH} · {ch['name'][lang]}"


def plan(lang):
    P = []
    P.append(dict(id="hook1", kind="photos", key="v4h1", pairs=d.HOOK1, shots=d.HOOK1_SHOTS, pops=d.HOOK1_POPS, tail=0.10))
    P.append(dict(id="hook2", kind="photos", key="v4h2", pairs=d.HOOK2, shots=d.HOOK2_SHOTS, pops=d.HOOK2_POPS, tail=0.10))
    P.append(dict(id="promise", kind="promise", key="v4h3", pairs=d.HOOK3, tail=0.25))
    for cid in d.ORDER:
        ch = d.CH_BY[cid]
        n = ch["n"]
        P.append(dict(id=f"{cid}_orig", kind="orig", key=f"v4{n}a", pairs=ch["a"], win=cid, ch=ch))
        P.append(dict(id=f"{cid}_card", kind="card", ch=ch))
        P.append(dict(id=f"{cid}_photos", kind="photos", key=f"v4{n}b", pairs=ch["b"], shots=ch["shots"], pops=ch["pops"], ch=ch, tail=1.1))
    P.append(dict(id="outro", kind="outro", key="v4o", pairs=d.OUTRO, tail=0.6))
    P.append(dict(id="credits", kind="credits"))
    return P


# ---------- elementy graficzne ----------
def tally_img(codes):
    """sześć kółek: wypełnione kolorem werdyktu albo obrys."""
    r, gap = 15, 12
    w, h = NCH * (2 * r + gap) + 6, 2 * r + 10
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.rounded_rectangle((0, 0, w - 1, h - 1), radius=12, fill=(8, 10, 14, 170))
    for i in range(NCH):
        cx = 12 + r + i * (2 * r + gap) - 4
        cy = h // 2
        if i < len(codes) and codes[i]:
            dr.ellipse((cx - r, cy - r, cx + r, cy + r), fill=d.VERDICT[codes[i]]["rgb"] + (255,))
        else:
            dr.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(150, 158, 172, 255), width=3)
    return np.asarray(im)


def codes_before(n):
    return [d.CH[i]["verdict"] for i in range(n - 1)]


def overlay4(frame, t, dur, starts, caps, pops, popbox, chip, chip_t, tags, tally=None):
    if chip is not None and t >= chip_t:
        q = t - chip_t
        s = 1.0 + 0.25 * max(0.0, 1 - q / 0.2) ** 2
        b.blend(frame, v2.scaled(chip, s), 40, 36)
    if tally is not None:
        b.blend(frame, tally, 40, 224)
    y = 36
    for tg in tags:
        b.blend(frame, tg, W - tg.shape[1] - 40, y)
        y += tg.shape[0] + 8
    for si in range(len(dur)):
        s0, s1 = starts[si] - 0.05, starts[si] + dur[si] + 0.25
        if s0 <= t <= s1:
            al = min(1.0, (t - s0) / 0.12)
            c = caps[si]
            b.blend(frame, c, (W - c.shape[1]) // 2, H - c.shape[0] - 56, al)
        if si in pops and starts[si] - 0.02 <= t <= starts[si] + dur[si] + 0.45:
            q = t - starts[si]
            s = 1.0 + 0.28 * max(0.0, 1 - q / 0.18) ** 2
            v2.blend_c(frame, v2.scaled(popbox[si], s), W * 0.5, H * 0.34)
    return frame


# ---------- sceny ----------
def render_photos4(args):
    spec, lang = args
    out = spec_out(spec, lang)
    sents = narr(lang, spec["key"], len(spec["pairs"]))
    dur, starts, frames = v2.timeline2(sents, spec["tail"])
    if b.valid(out, frames):
        return str(out), frames
    ch = spec.get("ch")
    shots = [(pid, idx, ov, Image.open(PH / f"{pid}.jpg").convert("RGB")) for pid, idx, ov in spec["shots"]]
    bounds = [0.0]
    for k in range(1, len(shots)):
        a = shots[k - 1][1][-1]; c = shots[k][1][0]
        bounds.append((starts[a] + dur[a] + starts[c]) / 2)
    bounds.append(frames / FPS)
    XF = 0.12
    caps = v2.caption_boxes(spec["pairs"], lang)
    pops = spec.get("pops") or {}
    popbox = v2.pop_boxes(pops, lang) if pops else {}
    chip = None
    big = small = None
    tl_before = tl_after = None
    if ch:
        chip = v2.chip_box(chip_text(ch, lang))
        code = ch["verdict"]
        big = v2.stamp_img(code, lang, 100)
        small = v2.stamp_img(code, lang, 40)
        t_v = starts[ch["vi"]] + VDELAY
        hold = 1.4
        tl_before = tally_img(codes_before(ch["n"]))
        tl_after = tally_img(codes_before(ch["n"]) + [code])
    tags = {pid: v2.credit_tag2(pid, lang) for pid, _, _, _ in shots}
    srct = v2.src_tag(lang)
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
            mvk = b.MOVES[ov] if ov else b.MOVES[pid]
            p = (t - lo) / (hi - lo)
            acc += b.photo_frame(im, mvk, p).astype(np.float32) * a
            wsum += a
            if a >= 0.5:
                cur = pid
        frame = (acc / max(wsum, 1e-6)).astype(np.uint8)
        tl = None
        if ch:
            tl = tl_after if t >= t_v else tl_before
        frame = overlay4(frame, t, dur, starts, caps, pops, popbox, chip, 0.0, [srct, tags[cur]], tl)
        if ch and t >= t_v:
            q = t - t_v
            pos1 = (40 + small.shape[1] / 2, 114 + small.shape[0] / 2)
            if q < hold:
                frame = v2.slam_frame(frame, big, q, W * 0.5, H * 0.42)
            else:
                u = min(1.0, (q - hold) / 0.35)
                if u < 1.0:
                    e = b.smooth(u)
                    ratio = small.shape[1] / big.shape[1]
                    x = W * 0.5 + (pos1[0] - W * 0.5) * e; y = H * 0.42 + (pos1[1] - H * 0.42) * e
                    v2.blend_c(frame, v2.scaled(big, 1 + (ratio - 1) * e), x, y)
                else:
                    v2.blend_c(frame, small, *pos1)
        pipe.stdin.write(frame.tobytes())
    b.finish_pipe(pipe, tmp, out)
    return str(out), frames


def orig_times(lang, spec):
    sents = narr(lang, spec["key"], len(spec["pairs"]))
    dur, starts, _ = v2.timeline2(sents, 0.0, 0.10)
    return sents, dur, starts


def orig_frames_used(lang, spec):
    frames = win_frames(spec["win"])
    _, dur, starts = orig_times(lang, spec)
    end = starts[-1] + dur[-1]
    if end > frames / FPS - 0.12:
        raise RuntimeError(f"{spec['id']} {lang}: lektor {end:.2f}s dłuższy niż fragment {frames / FPS:.2f}s")
    return min(frames, int(math.ceil((end + ORIG_TAIL) * FPS)))


def render_orig4(args):
    spec, lang = args
    out = spec_out(spec, lang)
    s0, _ = d.WINDOWS[spec["win"]]
    sents, dur, starts = orig_times(lang, spec)
    frames = orig_frames_used(lang, spec)
    if b.valid(out, frames):
        return str(out), frames
    caps = v2.caption_boxes(spec["pairs"], lang)
    ch = spec["ch"]
    chip = v2.chip_box(chip_text(ch, lang))
    tl = tally_img(codes_before(ch["n"]))
    apop = ch.get("apop") or {}
    popbox = v2.pop_boxes(apop, lang)
    srct = v2.src_tag(lang)
    cmd = ["ffmpeg", "-loglevel", "error", "-ss", f"{s0:.3f}", "-i", os.environ["SRC"], "-t", f"{frames / FPS + 0.2:.3f}",
           "-vf", f"scale={W}:{H}:flags=lanczos,fps={FPS},setsar=1", "-an", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    dec = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    pipe, tmp = b.ffmpeg_pipe(out)
    for fr in range(frames):
        raw = dec.stdout.read(W * H * 3)
        if len(raw) < W * H * 3:
            raise RuntimeError(f"{spec['id']}: za mało klatek ({fr}/{frames})")
        frame = np.frombuffer(raw, np.uint8).reshape(H, W, 3).copy()
        frame = overlay4(frame, fr / FPS, dur, starts, caps, apop, popbox, chip, 0.0, [srct], tl)
        pipe.stdin.write(frame.tobytes())
    dec.stdout.close(); dec.terminate()
    b.finish_pipe(pipe, tmp, out)
    return str(out), frames


def render_card4(args):
    spec, lang = args
    out = spec_out(spec, lang)
    frames = int(round(CARD_S * FPS))
    if b.valid(out, frames):
        return str(out), frames
    ch = spec["ch"]
    main = b.text_box("A tak to wygląda naprawdę" if lang == "pl" else "And what it really looks like", size=104, maxw=1700, path=b.FONT_B, bg=None, pad=(0, 0))
    sub = b.text_box(ch["name"][lang], size=46, maxw=1500, path=b.FONT_M, bg=None, fill=(210, 215, 225), pad=(0, 0))
    srct = v2.src_tag(lang)
    tl = tally_img(codes_before(ch["n"]))
    chip = v2.chip_box(chip_text(ch, lang))
    base = v2.bg_gradient()
    pipe, tmp = b.ffmpeg_pipe(out)
    hit = CARD_HIT
    for fr in range(frames):
        t = fr / FPS
        f = base.copy()
        lw = int(900 * b.smooth(t / hit))
        f[H // 2 + 90:H // 2 + 96, (W - lw) // 2:(W + lw) // 2] = ACCENT
        if t >= hit:
            a = b.smooth((t - hit) / 0.18)
            b.blend(f, main, (W - main.shape[1]) // 2, H // 2 - 80 - int(10 * (1 - a)), a)
            b.blend(f, sub, (W - sub.shape[1]) // 2, H // 2 + 130, b.smooth((t - hit - 0.1) / 0.2))
            if t - hit < 0.06:
                f = np.clip(f.astype(np.float32) + 90 * (1 - (t - hit) / 0.06), 0, 255).astype(np.uint8)
        b.blend(f, chip, 40, 36)
        b.blend(f, tl, 40, 224)
        b.blend(f, srct, W - srct.shape[1] - 40, 36)
        pipe.stdin.write(f.tobytes())
    b.finish_pipe(pipe, tmp, out)
    return str(out), frames


LIMITS = {"F": ("≤ 11 h", "≤ 11 h"), "T": ("≤ 15 h", "≤ 15 h"), "N": ("> 15 h", "> 15 h")}


def render_promise4(args):
    spec, lang = args
    out = spec_out(spec, lang)
    li = li_of(lang)
    sents = narr(lang, spec["key"], len(spec["pairs"]))
    dur, starts, frames = v2.timeline2(sents, spec["tail"])
    if b.valid(out, frames):
        return str(out), frames
    n = len(sents)
    bounds = [0.0] + [(starts[k] + dur[k] + starts[k + 1]) / 2 for k in range(n - 1)] + [frames / FPS]
    imgs = {pid: Image.open(PH / f"{pid}.jpg").convert("RGB") for pid in set(d.PROMISE_BG)}
    tags = {pid: v2.credit_tag2(pid, lang) for pid in imgs}
    srct = v2.src_tag(lang)
    stamp_idx = {idx: code for code, idx in d.HOOK3_STAMPS}
    texts = {}
    for k, p in enumerate(spec["pairs"]):
        if k in stamp_idx:
            continue
        top = k >= 6
        texts[k] = v2.shadow_text(d.disp(p[li]), 72 if top else 86, 1450 if top else 1400, (255, 255, 255))
    stamps = {idx: v2.stamp_img(code, lang, 70) for code, idx in d.HOOK3_STAMPS}
    limits = {idx: v2.shadow_text(LIMITS[code][li], 70, 500, (255, 255, 255)) for code, idx in d.HOOK3_STAMPS}
    caps = v2.caption_boxes(spec["pairs"], lang)
    pipe, tmp = b.ffmpeg_pipe(out)
    for fr in range(frames):
        t = fr / FPS
        k = max(i for i in range(n) if bounds[i] <= t + 1e-9) if t < bounds[-1] else n - 1
        pid = d.PROMISE_BG[k]
        prog = (t - bounds[k]) / max(bounds[k + 1] - bounds[k], 1e-6)
        m0, m1 = b.MOVES[pid]
        mvk = (m0, m1) if k % 2 == 0 else (m1, m0)
        frame = b.photo_frame(imgs[pid], mvk, prog)
        frame = (frame.astype(np.float32) * 0.42).astype(np.uint8)
        for row, (code, idx) in enumerate(d.HOOK3_STAMPS):
            if t >= starts[idx]:
                yy = 420 + row * 140
                v2.blend_c(frame, limits[idx], W / 2 - 430, yy)
                frame = v2.slam_frame(frame, stamps[idx], t - starts[idx], W / 2 + 190, yy)
        if k in texts:
            q = t - starts[k]
            s = 1.0 + 0.22 * max(0.0, 1 - q / 0.16) ** 2
            v2.blend_c(frame, v2.scaled(texts[k], s), W / 2, 210 if k >= 6 else H / 2 - 20)
        b.blend(frame, srct, W - srct.shape[1] - 40, 36)
        tg = tags[pid]
        b.blend(frame, tg, W - tg.shape[1] - 40, 36 + srct.shape[0] + 8)
        c = caps[k]
        if k not in texts and starts[k] - 0.05 <= t <= starts[k] + dur[k] + 0.25:
            b.blend(frame, c, (W - c.shape[1]) // 2, H - c.shape[0] - 56, min(1.0, (t - starts[k] + 0.05) / 0.12))
        pipe.stdin.write(frame.tobytes())
    b.finish_pipe(pipe, tmp, out)
    return str(out), frames


def render_outro4(args):
    spec, lang = args
    out = spec_out(spec, lang)
    li = li_of(lang)
    sents = narr(lang, spec["key"], len(spec["pairs"]))
    dur, starts, frames = v2.timeline2(sents, spec["tail"])
    if b.valid(out, frames):
        return str(out), frames
    tally = d.tally()
    stamp_idx = {idx for _, idx in d.OUTRO_TALLY}
    stamps = [(code, idx, v2.stamp_img(code, lang, 70)) for code, idx in d.OUTRO_TALLY]
    counts = {c: v2.shadow_text(f"{tally[c]}×", 120, 400, d.VERDICT[c]["rgb"]) for c, _ in d.OUTRO_TALLY}
    texts = {k: v2.shadow_text(d.disp(p[li]), 64 if k in (6,) else 76, 1500, (255, 255, 255)) for k, p in enumerate(spec["pairs"]) if k not in stamp_idx}
    caps = v2.caption_boxes(spec["pairs"], lang)
    srct = v2.src_tag(lang)
    base = v2.bg_gradient()
    pipe, tmp = b.ffmpeg_pipe(out)
    for fr in range(frames):
        t = fr / FPS
        f = base.copy()
        k = max([i for i in range(len(starts)) if starts[i] - 0.05 <= t] or [0])
        if k < 7:
            for row, (code, idx, st) in enumerate(stamps):
                if t >= starts[idx]:
                    y = 200 + row * 160
                    v2.blend_c(f, counts[code], 700, y)
                    f = v2.slam_frame(f, st, t - starts[idx], 1230, y)
        if k in texts:
            q = t - starts[k]
            s = 1.0 + 0.2 * max(0.0, 1 - q / 0.16) ** 2
            y = 520 if k == 0 else (800 if k < 7 else H / 2 - 40)
            v2.blend_c(f, v2.scaled(texts[k], s), W / 2, y)
        b.blend(f, srct, W - srct.shape[1] - 40, 36)
        pipe.stdin.write(f.tobytes())
    b.finish_pipe(pipe, tmp, out)
    return str(out), frames


CREDITS_S = 7.0


def credit_rows(lang):
    m = b.manifest()
    rows = []
    for ch in d.CH:
        ids = []
        for pid, _, _ in ch["shots"]:
            if pid not in ids:
                ids.append(pid)
        parts = [f"{b.artist(p, lang)} ({m[p]['license']})" for p in ids]
        rows.append(f"{ch['name'][lang]}: " + " · ".join(parts))
    return rows


def render_credits4(args):
    spec, lang = args
    out = spec_out(spec, lang)
    frames = int(round(CREDITS_S * FPS))
    if b.valid(out, frames):
        return str(out), frames
    base = v2.bg_gradient()
    head = ("Wideo źródłowe" if lang == "pl" else "Source video") + f": „{d.SRC['title']}” — {d.SRC['author']} (CC BY) — {d.SRC['url']}"
    lines = [head, ""]
    lines.append(("Zdjęcia (Wikimedia Commons):" if lang == "pl" else "Photos (Wikimedia Commons):"))
    lines += credit_rows(lang)
    lines += ["",
              ("Czasy dojazdu: savaari.com, holidify.com. Wysokości i fakty: Wikipedia." if lang == "pl" else "Drive times: savaari.com, holidify.com. Heights and facts: Wikipedia."),
              ("Muzyka: „Transformations 3”, HoliznaCC0 (CC0). Lektor: mowa syntetyczna." if lang == "pl" else "Music: “Transformations 3”, HoliznaCC0 (CC0). Voice: synthetic speech.")]
    boxes = [b.text_box(t, size=30 if t else 18, maxw=1740, path=b.FONT_M if t != head else b.FONT_B, bg=None, pad=(0, 0)) if t else None for t in lines]
    ys, y = [], 90
    for bx in boxes:
        ys.append(y)
        y += (bx.shape[0] + 14) if bx is not None else 26
    pipe, tmp = b.ffmpeg_pipe(out)
    for fr in range(frames):
        f = base.copy()
        for bx, yy in zip(boxes, ys):
            if bx is not None:
                b.blend(f, bx, 90, yy)
        pipe.stdin.write(f.tobytes())
    b.finish_pipe(pipe, tmp, out)
    return str(out), frames


RENDER = {"photos": render_photos4, "orig": render_orig4, "card": render_card4, "promise": render_promise4,
          "outro": render_outro4, "credits": render_credits4}


def run_one(args):
    spec, lang = args
    return spec["id"], RENDER[spec["kind"]](args)


# ---------- komendy ----------
def cmd_plan(lang):
    t = 0.0
    for sp in plan(lang):
        if sp["kind"] == "card":
            dur = CARD_S
        elif sp["kind"] == "credits":
            dur = CREDITS_S
        elif sp["kind"] == "orig":
            sents, dd, st = orig_times(lang, sp)
            full = win_frames(sp["win"]) / FPS
            try:
                dur = orig_frames_used(lang, sp) / FPS
            except RuntimeError as e:
                print("   !!!", e); dur = win_frames(sp["win"]) / FPS
            print(f"   voice {st[0]:.2f}-{st[-1] + dd[-1]:.2f} / okno {full:.2f}, użyte {dur:.2f}")
        else:
            sents = narr(lang, sp["key"], len(sp["pairs"]))
            dd, st, fr = v2.timeline2(sents, sp["tail"])
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
    (WD4 / lang).mkdir(parents=True, exist_ok=True)
    specs = plan(lang)
    with Pool(2) as pool:
        for sid, r in pool.imap(run_one, [(s, lang) for s in specs]):
            print("ok", sid, r[1], flush=True)


def cmd_concat(lang):
    specs = plan(lang)
    lst = WD4 / lang / "concat.txt"
    lst.write_text("".join(f"file '{spec_out(s, lang)}'\n" for s in specs))
    out = WD4 / lang / "video_silent.mp4"
    tmp = str(out) + ".tmp.mp4"
    b.sh(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", "-f", "mp4", tmp])
    os.replace(tmp, out)
    print("concat ok", out)


def orig_audio(wid):
    s, e = d.WINDOWS[wid]
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{s:.3f}", "-t", f"{win_frames(wid) / FPS:.3f}", "-i", os.environ["SRC"],
                        "-vn", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, dtype="<f4").reshape(-1, 2).copy()


def stamp_times(sp, st):
    k = sp["kind"]
    if k == "photos" and sp.get("ch"):
        return [st[sp["ch"]["vi"]] + VDELAY]
    if k == "promise":
        return [st[i] for _, i in d.HOOK3_STAMPS]
    if k == "outro":
        return [st[i] for _, i in d.OUTRO_TALLY]
    return []


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
    v2.CARD2_S, v2.CARD2_HIT = CARD_S, CARD_HIT
    cfx = v2.synth_card_fx2()
    sfx = v2.synth_stamp_fx()
    segs = []
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
            dd, st, _ = v2.timeline2(sents, 0, 0.10)
            x = orig_audio(sp["win"])
            x *= 10 ** ((orig_lufs - meter.integrated_loudness(x)) / 20)
            n = min(len(x), int(dur * SR), N - s)
            ramp = np.ones(n, np.float32); a = int(0.2 * SR)
            ramp[:a] = np.linspace(0, 1, a); ramp[-a:] = np.linspace(1, 0, a)
            orig[s:s + n] += x[:n] * ramp[:, None]
        else:
            dd, st, _ = v2.timeline2(sents, sp.get("tail", 0.2))
        for sn, ts in zip(sents, st):
            a = s + int(ts * SR)
            voice[a:a + len(sn), 0] += sn; voice[a:a + len(sn), 1] += sn
            mask[a:a + len(sn)] = True
            segs.append((t0 + ts, t0 + ts + len(sn) / SR))
        for ts in stamp_times(sp, st):
            a = s + int(ts * SR)
            if a < N:
                seg = sfx[:N - a]
                fx[a:a + len(seg)] += seg
    mus = b.read_f32(os.environ["MUSIC"])
    mus *= 10 ** ((-16 - meter.integrated_loudness(mus)) / 20)
    reps = int(math.ceil(N / len(mus)))
    music[:] = np.concatenate([mus] * reps)[:N]
    f_in, f_out = int(0.5 * SR), int(1.5 * SR)
    music[:f_in] *= np.linspace(0, 1, f_in)[:, None]; music[-f_out:] *= np.linspace(1, 0, f_out)[:, None]
    gv = 10 ** ((-16 - meter.integrated_loudness(voice[mask])) / 20)
    voice *= gv
    gm = 10 ** (((-16 - music_below) - meter.integrated_loudness(music[mask])) / 20)
    music *= gm
    fx *= 10 ** (-3 / 20)
    mix = voice + music + fx + orig
    sf = WD4 / lang
    np.save(sf / "stem_voice.npy", voice.astype(np.float16)); np.save(sf / "stem_music.npy", music.astype(np.float16))
    np.save(sf / "stem_orig.npy", orig.astype(np.float16)); np.save(sf / "stem_mask.npy", mask)
    segs.sort()
    gaps = sorted([(segs[i + 1][0] - segs[i][1], segs[i][1]) for i in range(len(segs) - 1)], reverse=True)
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
    sf = WD4 / lang
    raw = sf / "mix_raw.wav"
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(raw), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True)
    j = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
    flt = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
           f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true:print_format=summary,alimiter=limit=0.75:level=disabled")
    mast = sf / "mix_master.wav"
    b.sh(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-af", flt, "-ar", str(SR), "-c:a", "pcm_s16le", str(mast)])
    out = sf / f"bangalore_{lang}.mp4"
    tmp = str(out) + ".tmp.mp4"
    b.sh(["ffmpeg", "-y", "-loglevel", "error", "-i", str(sf / "video_silent.mp4"), "-i", str(mast), "-map", "0:v", "-map", "1:a",
          "-c:v", "copy", "-af", "alimiter=limit=1:level=disabled", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-f", "mp4", tmp])
    os.replace(tmp, out)
    m = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(out), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    tail = m[m.rfind("Summary:"):]
    print("final", out); print(tail)
    (sf / "final_measure.txt").write_text(tail)


def used_photos():
    seen = []
    for pid in ([s[0] for s in d.HOOK1_SHOTS] + [s[0] for s in d.HOOK2_SHOTS] + list(d.PROMISE_BG)):
        if pid not in seen:
            seen.append(pid)
    for cid in d.ORDER:
        for pid, _, _ in d.CH_BY[cid]["shots"]:
            if pid not in seen:
                seen.append(pid)
    return seen


def scene_starts(lang):
    t, out = 0.0, {}
    for sp in plan(lang):
        out[sp["id"]] = t
        t += (CREDITS_S if sp["kind"] == "credits" else b.nframes(spec_out(sp, lang)) / FPS)
    return out, t


def fmt_t(x):
    x = int(x)
    return f"{x // 60}:{x % 60:02d}"


def cmd_docs():
    m = b.manifest()
    used = used_photos()
    L = ["# Źródła i licencje / Credits and licences (v4, Bangalore)", "", "## Film oryginalny / Original video", "",
         f"- „{d.SRC['title']}” — {d.SRC['author']} — {d.SRC['url']}",
         f"- Licencja / Licence: {d.SRC['license']}",
         "- Użyte fragmenty / Excerpts used (s): " + ", ".join(f"{k} {a:.1f}–{e:.1f}" for k, (a, e) in d.WINDOWS.items()),
         "- Odrzucone: fragment Yercaud (cudze zdjęcia z podpisami „Image Credits”). / Skipped: the Yercaud section (third-party images credited on screen).", "",
         "## Zdjęcia / Photos (Wikimedia Commons)", ""]
    for pid in used:
        x = m[pid]
        lu = b.LIC_URL.get(x["license"], "") or x.get("license_url", "")
        L.append(f"- **{x['title'].replace('File:', '')}** — {b.artist(pid, 'en')} — {x['license']}" + (f" ({lu})" if lu else "") + f" — {x['page']}")
    L += ["", "## Źródła faktów / Fact sources", ""]
    for ch in d.CH:
        L.append(f"- {ch['name']['en']}: " + ", ".join(ch["sources"]))
    L += ["", "## Zmiany / Changes",
          "- Zdjęcia: kadrowanie 16:9, ruch kamery, nakładki (stempel, liczniki); bez korekty kolorów. / Photos: 16:9 crop, camera move, overlays (stamp, counters); no colour grading.",
          "- Oryginał: fragmenty 5–7 s, skalowanie z 720p do 1080p, dźwięk oryginału ściszony pod lektorem. / Original: 5–7 s excerpts, upscaled from 720p to 1080p, original sound lowered under the voice-over.",
          "- Czasy dojazdu to wartości orientacyjne ze stron podróżniczych, bez postojów; próg werdyktu (11 h / 15 h w obie strony) to moja reguła. / Drive times are rough figures from travel sites, without stops; the verdict thresholds (11 h / 15 h round trip) are my own rule.", "",
          "## Dźwięk / Sound",
          "- Muzyka / Music: „Transformations 3”, HoliznaCC0, CC0 1.0 — https://freemusicarchive.org/music/holiznacc0/transformations/transformations-3/",
          "- Lektor PL: Piper pl_PL-gosia-medium. Lektor EN: Kokoro-82M, af_heart (Apache-2.0). Mowa syntetyczna / synthetic speech.",
          "- Dźwięki planszy i stempla generowane w kodzie. / Card and stamp sounds generated in code.", ""]
    out = WD4 / "CREDITS_v4.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print("wrote", out)
    for lang in ("pl", "en"):
        try:
            st, total = scene_starts(lang)
        except Exception as e:
            print("no timings for", lang, e); continue
        chap = [(st["hook1"], "Gokarna: 19 hours" if lang == "en" else "Gokarna: 19 godzin"),
                (st["promise"], "The test: hours, not kilometres" if lang == "en" else "Test: godziny, nie kilometry")]
        for cid in d.ORDER:
            ch = d.CH_BY[cid]
            chap.append((st[f"{cid}_orig"], f"{ch['n']}. {ch['name'][lang]} — {d.VERDICT[ch['verdict']][lang].title()}"))
        chap.append((st["outro"], "The count and your vote" if lang == "en" else "Podsumowanie i Twój głos"))
        lines = [f"{fmt_t(t)} {n}" for t, n in chap]
        head = {
            "en": ["Six places from one travel video, and what the road really costs: the author gives kilometres, I count the hours in the car (round trip). Drive times are rough figures from travel sites, without stops.",
                   f"Original footage: \"{d.SRC['title']}\" by {d.SRC['author']} (CC BY) — {d.SRC['url']}"],
            "pl": ["Sześć miejsc z jednego filmu podróżniczego i to, ile naprawdę kosztuje droga: autor podaje kilometry, ja liczę godziny w aucie (w obie strony). Czasy dojazdu to wartości orientacyjne ze stron podróżniczych, bez postojów.",
                   f"Materiał źródłowy: „{d.SRC['title']}” — {d.SRC['author']} (CC BY) — {d.SRC['url']}"]}[lang]
        cred = ["", "Photos (Wikimedia Commons):"] + [f"- {m[p]['title'].replace('File:', '')} — {b.artist(p, 'en')} — {m[p]['license']} — {m[p]['page']}" for p in used]
        cred += ["", "Music: Transformations 3 by HoliznaCC0 (CC0).", "Voice: synthetic (Piper / Kokoro)." if lang == "en" else "Lektor: mowa syntetyczna (Piper / Kokoro)."]
        txt = "\n".join(head + [""] + lines + cred)
        (WD4 / f"description_{lang}.txt").write_text(txt, encoding="utf-8")
        print("wrote description", lang, f"{total:.1f}s")


if __name__ == "__main__":
    c = sys.argv[1]
    WD4.mkdir(parents=True, exist_ok=True)
    if c == "plan": cmd_plan(sys.argv[2])
    elif c == "render": cmd_render(sys.argv[2])
    elif c == "concat": cmd_concat(sys.argv[2])
    elif c == "mix": cmd_mix(sys.argv[2])
    elif c == "master": cmd_master(sys.argv[2])
    elif c == "docs": cmd_docs()
    else: raise SystemExit(c)
