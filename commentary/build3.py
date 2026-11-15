#!/usr/bin/env python3
"""Montaż komentarza v3 (skrypt 3.0). Środowisko: SP, SRC, TTS2_PL, TTS2_EN (katalogi wav z kluczami v3w..), MUSIC.
  build3.py plan LANG | render LANG | concat LANG | mix LANG | master LANG | docs
Zasady: lektor wchodzi w tej samej klatce co klip źródłowy, stały podpis źródła w rogu przez cały film,
stempel werdyktu w trakcie sceny (potem plakietka w rogu), licznik x/7 przy zdaniu „mechanizm …", twarde cięcie na końcu."""
import json, math, os, subprocess, sys, wave
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import build as b
import build2 as v2
import data3 as d

v2.d = d   # funkcje v2 (stempel, podpisy) czytają dane z modułu d
W, H, FPS, SR = b.W, b.H, b.FPS, b.SR
SP = b.SP
WD3 = SP / "cm3"
PH = b.PH
ACCENT = b.ACCENT
CARD_S, CARD_HIT = 1.4, 0.42
VDELAY = 0.5
ORIG_TAIL = 0.55

b.ARTIST["ometepe3"] = "Ridiculopathy"
b.MOVES.update({
    "machu2~r": ((0.50, 0.52, 1.28), (0.50, 0.45, 1.00)),
    "nepal3~2": ((0.74, 0.64, 1.35), (0.60, 0.60, 1.05)),
    "utah1~2": ((0.50, 0.52, 1.12), (0.50, 0.50, 1.00)),
    "fuego3~2": ((0.60, 0.46, 1.15), (0.50, 0.44, 1.00)),
    "copper2~2": ((0.60, 0.50, 1.12), (0.40, 0.50, 1.00)),
    "burning1~2": ((0.62, 0.52, 1.10), (0.62, 0.50, 1.00)),
    "burning3~2": ((0.60, 0.50, 1.12), (0.75, 0.50, 1.00)),
    "ometepe3": ((0.50, 0.50, 1.00), (0.55, 0.45, 1.15)),
    "ometepe1~2": ((0.50, 0.50, 1.12), (0.50, 0.55, 1.00)),
    "grand3~2": ((0.55, 0.55, 1.15), (0.50, 0.50, 1.00)),
})
PROMISE_BG = ["machu1", "burning1", "copper1", "grand1", "nepal3", "utah3", "fuego1", "grand3", "copper2", "nepal1", "burning3", "utah1"]


# ---------- czas i narracja ----------
def orig_lead3(sents, window_s):
    """narracja wchodzi w pierwszej klatce klipu (skrypt 3.0): luz zostaje na końcu fragmentu."""
    return 0.10


def li_of(lang):
    return 0 if lang == "pl" else 1


def narr(lang, key, n):
    return v2.narr(lang, "v3" + key, n)


def spec_out(spec, lang):
    return WD3 / lang / f"{spec['id']}.mp4"


def win_frames(wid):
    s, e = d.WINDOWS[wid]
    return int(round((e - s) * FPS))


def mechno(ch):
    return 7 if ch["id"] == "machu" else ch["n"]


def chip_text(ch, lang):
    return f"↺ {ch['mech'][lang]}" if ch.get("repeat") else f"{mechno(ch)}/7 · {ch['mech'][lang]}"


def plan(lang):
    P = []
    P.append(dict(id="hook1", kind="photos", key="w0a", pairs=d.HOOK1, shots=[("machu2", [0, 1, 2], "machu2@h1")], pops={1: ("1912", "1912")}, tail=0.10))
    P.append(dict(id="hook2", kind="photos", key="w0b", pairs=d.HOOK2, shots=[("machu1", [0, 1, 2], "machu1@h2")], pops={}, tail=0.10))
    P.append(dict(id="hook3", kind="orig", key="w0c", pairs=d.HOOK3, win="coast"))
    P.append(dict(id="promise", kind="promise", key="w0d", pairs=d.HOOK4, tail=0.25))
    for pos, cid in enumerate(d.ORDER):
        ch = d.CH_BY[cid]
        n = ch["n"]
        if pos == 4:
            P.append(dict(id="midroll", kind="mid", key="wm", pairs=d.MID, tail=0.5))
        if ch.get("pre"):
            P.append(dict(id=f"{cid}_pre", kind="photos", key=f"w{n}p", pairs=ch["pre"], shots=[("machu2", [0, 1, 2], "machu2~r")], pops={1: ("1912", "1912")}, tail=0.10))
        P.append(dict(id=f"{cid}_orig", kind="orig", key=f"w{n}a", pairs=ch["a"], win=cid, ch=ch))
        P.append(dict(id=f"{cid}_card", kind="card", ch=ch))
        P.append(dict(id=f"{cid}_photos", kind="photos", key=f"w{n}b", pairs=ch["b"], shots=ch["shots"], pops=ch["pops"], ch=ch, tail=1.1))
    P.append(dict(id="outro", kind="outro", key="w9", pairs=d.OUTRO, tail=0.6))
    return P


# ---------- elementy graficzne ----------
def ring_img(r):
    s = int(2 * r + 40)
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    c = s // 2
    dr.ellipse((c - r - 3, c - r - 3, c + r + 3, c + r + 3), outline=(0, 0, 0, 200), width=14)
    dr.ellipse((c - r, c - r, c + r, c + r), outline=ACCENT + (255,), width=8)
    return np.asarray(im)


def schema_panel(lang):
    w, h = 560, 330
    im = Image.new("RGBA", (w, h), (8, 10, 14, 215))
    dr = ImageDraw.Draw(im)
    dr.rounded_rectangle((0, 0, w - 1, h - 1), radius=18, outline=(255, 255, 255, 90), width=3)
    f1, f2 = b.font(b.FONT_M, 26), b.font(b.FONT_B, 40)
    dr.text((28, 18), "SCHEMAT, nie mapa" if lang == "pl" else "DIAGRAM, not a map", font=f1, fill=(200, 205, 215, 255))
    for i in range(6):
        cx, cy = 28 + (i % 3) * 172, 72 + (i // 3) * 98
        lit = (i == 4)
        dr.rounded_rectangle((cx, cy, cx + 150, cy + 78), radius=14, fill=(ACCENT + (255,)) if lit else (70, 80, 96, 255))
    dr.text((28, 268), "widzisz 1 z 6" if lang == "pl" else "you see 1 of 6", font=f2, fill=(255, 255, 255, 255))
    return np.asarray(im)


def overlay3(frame, t, dur, starts, caps, pops, popbox, chip, chip_t, tags):
    if chip is not None and t >= chip_t:
        q = t - chip_t
        s = 1.0 + 0.25 * max(0.0, 1 - q / 0.2) ** 2
        b.blend(frame, v2.scaled(chip, s), 40, 36)
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
def render_photos3(args):
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
    popbox = v2.pop_boxes(spec["pops"], lang) if spec.get("pops") else {}
    chip, chip_t = None, 0.0
    big = small = None
    if ch:
        where, ci = ch["chip"]
        chip = v2.chip_box(chip_text(ch, lang))
        chip_t = 0.0 if where == "a" else starts[ci]
        code = ch["verdict"]
        big = v2.stamp_img(code, lang, 112 if code == "B" else 100)
        small = v2.stamp_img(code, lang, 40)
        t_v = starts[ch["vi"]] + VDELAY
        hold = 2.0 if code == "B" else 1.4
    tags = {pid: v2.credit_tag2(pid, lang) for pid, _, _, _ in shots}
    srct = v2.src_tag(lang)
    ring = ch.get("ring") if ch else None
    schema = ch.get("schema") if ch else None
    if ring:
        rimgs = {r: ring_img(r) for r in range(70, 92, 2)}
    if schema:
        sp_img = schema_panel(lang)
    pipe, tmp = b.ffmpeg_pipe(out)
    for fr in range(frames):
        t = fr / FPS
        acc = np.zeros((H, W, 3), np.float32); wsum = 0.0; cur = shots[0][0]; best = (-1, None)
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
            if a > best[0]:
                best = (a, (pid, im, mvk, p))
            if a >= 0.5:
                cur = pid
        frame = (acc / max(wsum, 1e-6)).astype(np.uint8)
        frame = overlay3(frame, t, dur, starts, caps, spec.get("pops") or {}, popbox, chip, chip_t, [srct, tags[cur]])
        if ring and best[1] is not None and best[1][0] == ring["photo"]:
            r0 = starts[ring["from"]] - 0.1; r1 = starts[ring["to"]] + dur[ring["to"]] + 0.3
            if r0 <= t <= r1:
                pid, im, mvk, p = best[1]
                x0, y0, x1, y1 = b.window_box(im, mvk, p)
                sx = (ring["xy"][0] * im.size[0] - x0) / (x1 - x0) * W
                sy = (ring["xy"][1] * im.size[1] - y0) / (y1 - y0) * H
                rr = int(round((80 + 10 * math.sin((t - r0) * 7)) / 2) * 2)
                al = min(1.0, (t - r0) / 0.25, (r1 - t) / 0.3)
                v2.blend_c(frame, rimgs[min(max(rr, 70), 90)], sx, sy, max(0.0, al))
        if schema:
            s0 = starts[schema["from"]] - 0.05; s1 = starts[schema["to"]] + dur[schema["to"]] + 0.2
            if s0 <= t <= s1:
                al = min(1.0, (t - s0) / 0.25, (s1 - t) / 0.25)
                b.blend(frame, sp_img, 40, 190, max(0.0, al))
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


def render_orig3(args):
    spec, lang = args
    out = spec_out(spec, lang)
    s0, e0 = d.WINDOWS[spec["win"]]
    frames = win_frames(spec["win"])
    sents = narr(lang, spec["key"], len(spec["pairs"]))
    dur, starts, _ = v2.timeline2(sents, 0.0, orig_lead3(sents, frames / FPS))
    end = starts[-1] + dur[-1]
    if end > frames / FPS - 0.12:
        raise RuntimeError(f"{spec['id']} {lang}: lektor {end:.2f}s dłuższy niż fragment {frames / FPS:.2f}s")
    frames = min(frames, int(math.ceil((end + ORIG_TAIL) * FPS)))   # klip kończy się tuż po lektorze: szybsze tempo, bez martwej ciszy
    if b.valid(out, frames):
        return str(out), frames
    caps = v2.caption_boxes(spec["pairs"], lang)
    ch = spec.get("ch")
    chip, chip_t = None, 0.0
    if ch and ch["chip"][0] == "a":
        chip = v2.chip_box(chip_text(ch, lang)); chip_t = starts[ch["chip"][1]]
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
        frame = overlay3(frame, fr / FPS, dur, starts, caps, {}, {}, chip, chip_t, [srct])
        pipe.stdin.write(frame.tobytes())
    dec.stdout.close(); dec.terminate()
    b.finish_pipe(pipe, tmp, out)
    return str(out), frames


def render_card3(args):
    spec, lang = args
    out = spec_out(spec, lang)
    frames = int(round(CARD_S * FPS))
    if b.valid(out, frames):
        return str(out), frames
    ch = spec["ch"]
    main = b.text_box("A tak to wygląda naprawdę" if lang == "pl" else "And what it really looks like", size=104, maxw=1700, path=b.FONT_B, bg=None, pad=(0, 0))
    sub = b.text_box(ch["name"][lang], size=46, maxw=1500, path=b.FONT_M, bg=None, fill=(210, 215, 225), pad=(0, 0))
    srct = v2.src_tag(lang)
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
        b.blend(f, srct, W - srct.shape[1] - 40, 36)
        pipe.stdin.write(f.tobytes())
    b.finish_pipe(pipe, tmp, out)
    return str(out), frames


def render_promise3(args):
    spec, lang = args
    out = spec_out(spec, lang)
    li = li_of(lang)
    sents = narr(lang, spec["key"], len(spec["pairs"]))
    dur, starts, frames = v2.timeline2(sents, spec["tail"])
    if b.valid(out, frames):
        return str(out), frames
    n = len(sents)
    bounds = [0.0] + [(starts[k] + dur[k] + starts[k + 1]) / 2 for k in range(n - 1)] + [frames / FPS]
    imgs = {pid: Image.open(PH / f"{pid}.jpg").convert("RGB") for pid in set(PROMISE_BG)}
    tags = {pid: v2.credit_tag2(pid, lang) for pid in imgs}
    srct = v2.src_tag(lang)
    stamp_idx = {idx: code for code, idx in d.HOOK4_STAMPS}
    texts = {}
    for k, p in enumerate(spec["pairs"]):
        if k in stamp_idx:
            continue
        top = k >= 9
        texts[k] = v2.shadow_text(d.disp(p[li]), 70 if top else 86, 1450 if top else 1400, (255, 255, 255))
    stamps = {idx: v2.stamp_img(code, lang, 62) for code, idx in d.HOOK4_STAMPS}
    caps = v2.caption_boxes(spec["pairs"], lang)
    pipe, tmp = b.ffmpeg_pipe(out)
    for fr in range(frames):
        t = fr / FPS
        k = max(i for i in range(n) if bounds[i] <= t + 1e-9) if t < bounds[-1] else n - 1
        pid = PROMISE_BG[k]
        prog = (t - bounds[k]) / max(bounds[k + 1] - bounds[k], 1e-6)
        m0, m1 = b.MOVES[pid]
        mvk = (m0, m1) if k % 2 == 0 else (m1, m0)
        frame = b.photo_frame(imgs[pid], mvk, prog)
        frame = (frame.astype(np.float32) * 0.42).astype(np.uint8)
        for row, (code, idx) in enumerate(d.HOOK4_STAMPS):
            if t >= starts[idx]:
                frame = v2.slam_frame(frame, stamps[idx], t - starts[idx], W / 2, 330 + row * 135)
        if k in texts:
            q = t - starts[k]
            s = 1.0 + 0.22 * max(0.0, 1 - q / 0.16) ** 2
            v2.blend_c(frame, v2.scaled(texts[k], s), W / 2, 205 if k >= 9 else H / 2 - 20)
        b.blend(frame, srct, W - srct.shape[1] - 40, 36)
        tg = tags[pid]
        b.blend(frame, tg, W - tg.shape[1] - 40, 36 + srct.shape[0] + 8)
        c = caps[k]
        if starts[k] - 0.05 <= t <= starts[k] + dur[k] + 0.25:
            b.blend(frame, c, (W - c.shape[1]) // 2, H - c.shape[0] - 56, min(1.0, (t - starts[k] + 0.05) / 0.12))
        pipe.stdin.write(frame.tobytes())
    b.finish_pipe(pipe, tmp, out)
    return str(out), frames


def render_mid3(args):
    spec, lang = args
    out = spec_out(spec, lang)
    li = li_of(lang)
    sents = narr(lang, spec["key"], len(spec["pairs"]))
    dur, starts, frames = v2.timeline2(sents, spec["tail"])
    if b.valid(out, frames):
        return str(out), frames
    base = v2.bg_gradient()
    srct = v2.src_tag(lang)
    texts = [v2.shadow_text(d.disp(p[li]), 66, 1400, (255, 255, 255)) for p in spec["pairs"]]
    caps = v2.caption_boxes(spec["pairs"], lang)
    nums = [b.text_box(str(i + 1), size=56, maxw=100, path=b.FONT_B, bg=None, fill=(10, 12, 18), pad=(0, 0)) for i in range(8)]
    names = {i: b.text_box(d.MID_SHORT[cid], size=32, maxw=300, path=b.FONT_M, bg=None, fill=(220, 225, 235), pad=(0, 0)) for i, cid in enumerate(d.ORDER[:4])}
    qm = b.text_box("?", size=64, maxw=100, path=b.FONT_B, bg=None, fill=(150, 158, 172), pad=(0, 0))
    xs = [240 + i * 205 for i in range(8)]
    Y = 430
    yy, xx = np.mgrid[0:H, 0:W]
    pipe, tmp = b.ffmpeg_pipe(out)
    for fr in range(frames):
        t = fr / FPS
        f = base.copy()
        for i in range(8):
            if i < 4:
                t0 = 0.25 + i * 0.2
                if t < t0:
                    continue
                s = 1.0 + 0.3 * max(0.0, 1 - (t - t0) / 0.18) ** 2
                col = d.VERDICT[d.CH_BY[d.ORDER[i]]["verdict"]]["rgb"]
                r = 62 * s
                m = (xx - xs[i]) ** 2 + (yy - Y) ** 2 <= r * r
                f[m] = col
                v2.blend_c(f, nums[i], xs[i], Y)
                v2.blend_c(f, names[i], xs[i], Y + 105)
            else:
                m = np.abs(np.hypot(xx - xs[i], yy - Y) - 60) <= 3
                f[m] = (110, 118, 134)
                v2.blend_c(f, qm, xs[i], Y)
        k = max([i for i in range(len(starts)) if starts[i] - 0.05 <= t] or [0])
        q = t - starts[k]
        s = 1.0 + 0.2 * max(0.0, 1 - q / 0.16) ** 2
        v2.blend_c(f, v2.scaled(texts[k], s), W / 2, 760)
        b.blend(f, srct, W - srct.shape[1] - 40, 36)
        pipe.stdin.write(f.tobytes())
    b.finish_pipe(pipe, tmp, out)
    return str(out), frames


def render_outro3(args):
    spec, lang = args
    out = spec_out(spec, lang)
    li = li_of(lang)
    sents = narr(lang, spec["key"], len(spec["pairs"]))
    dur, starts, frames = v2.timeline2(sents, spec["tail"])
    if b.valid(out, frames):
        return str(out), frames
    tally = d.tally()
    stamps = [(code, idx, v2.stamp_img(code, lang, 62)) for code, idx in d.OUTRO_TALLY]
    counts = {c: v2.shadow_text(f"{tally[c]}×", 110, 400, d.VERDICT[c]["rgb"]) for c, _ in d.OUTRO_TALLY}
    texts = [v2.shadow_text(d.disp(p[li]), 76 if k < 10 else 70, 1440, (255, 255, 255)) for k, p in enumerate(spec["pairs"])]
    ome = v2.shadow_text("Ometepe", 78, 500, d.VERDICT["B"]["rgb"])
    caps = v2.caption_boxes(spec["pairs"], lang)
    srct = v2.src_tag(lang)
    base = v2.bg_gradient()
    pipe, tmp = b.ffmpeg_pipe(out)
    for fr in range(frames):
        t = fr / FPS
        f = base.copy()
        k = max([i for i in range(len(starts)) if starts[i] - 0.05 <= t] or [0])
        if k < 10:
            for row, (code, idx, st) in enumerate(stamps):
                if t >= starts[idx]:
                    y = 190 + row * 150
                    v2.blend_c(f, counts[code], 440, y)
                    f = v2.slam_frame(f, st, t - starts[idx], 1060, y)
            if t >= starts[5]:
                v2.blend_c(f, ome, 1690, 190 + 3 * 150, b.smooth((t - starts[5]) / 0.2))
        if k not in (1, 2, 3, 4):
            q = t - starts[k]
            s = 1.0 + 0.2 * max(0.0, 1 - q / 0.16) ** 2
            y = 480 if k == 0 else (820 if k < 10 else H / 2 - 40)
            v2.blend_c(f, v2.scaled(texts[k], s), W / 2, y)
        b.blend(f, srct, W - srct.shape[1] - 40, 36)
        c = caps[k]
        if starts[k] - 0.05 <= t <= starts[k] + dur[k] + 0.25:
            b.blend(f, c, (W - c.shape[1]) // 2, H - c.shape[0] - 56, min(1.0, (t - starts[k] + 0.05) / 0.12))
        pipe.stdin.write(f.tobytes())
    b.finish_pipe(pipe, tmp, out)
    return str(out), frames


RENDER = {"photos": render_photos3, "orig": render_orig3, "card": render_card3, "promise": render_promise3,
          "mid": render_mid3, "outro": render_outro3}


def run_one(args):
    spec, lang = args
    return spec["id"], RENDER[spec["kind"]](args)


# ---------- komendy ----------
def cmd_plan(lang):
    t = 0.0
    for sp in plan(lang):
        if sp["kind"] == "card":
            dur = CARD_S
        elif sp["kind"] == "orig":
            dur = win_frames(sp["win"]) / FPS
            sents = narr(lang, sp["key"], len(sp["pairs"]))
            dd, st, _ = v2.timeline2(sents, 0, orig_lead3(sents, dur))
            print(f"   voice {st[0]:.2f}-{st[-1] + dd[-1]:.2f} / {dur:.2f}" + ("   !!! ZA DŁUGO" if st[-1] + dd[-1] > dur - 0.12 else ""))
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
    (WD3 / lang).mkdir(parents=True, exist_ok=True)
    specs = plan(lang)
    with Pool(2) as pool:
        for sid, r in pool.imap(run_one, [(s, lang) for s in specs]):
            print("ok", sid, r[1], flush=True)


def cmd_concat(lang):
    specs = plan(lang)
    lst = WD3 / lang / "concat.txt"
    lst.write_text("".join(f"file '{spec_out(s, lang)}'\n" for s in specs))
    out = WD3 / lang / "video_silent.mp4"
    tmp = str(out) + ".tmp.mp4"
    b.sh(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", "-f", "mp4", tmp])
    os.replace(tmp, out)
    print("concat ok", out)


def synth_card_fx3():
    v2.CARD2_S, v2.CARD2_HIT = CARD_S, CARD_HIT
    return v2.synth_card_fx2()


def synth_win_fx():
    """stempel „lepiej niż w vlogu”: uderzenie + wznosząca się fanfara."""
    base = v2.synth_stamp_fx()
    n = int(1.4 * SR)
    t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    for f0, off, amp in ((523.25, 0.0, 0.5), (659.25, 0.12, 0.45), (783.99, 0.24, 0.45), (1046.5, 0.36, 0.5)):
        tt = np.clip(t - off, 0, None) * (t >= off)
        x += amp * (np.sin(2 * np.pi * f0 * tt) + 0.3 * np.sin(2 * np.pi * 2 * f0 * tt)) * np.exp(-tt * 3.2) * (t >= off)
    x *= np.minimum(1, (1.4 - t) / 0.15)
    x = (x / (np.abs(x).max() + 1e-9) * 0.5).astype(np.float32)
    st = np.zeros((n, 2), np.float32)
    st[:, 0] = x; st[:, 1] = x
    st[:len(base)] += base
    return st


def orig_audio(wid):
    s, e = d.WINDOWS[wid]
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{s:.3f}", "-t", f"{win_frames(wid) / FPS:.3f}", "-i", os.environ["SRC"],
                        "-vn", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, dtype="<f4").reshape(-1, 2).copy()


def stamp_times(sp, st):
    """lista (czas_w_scenie, kod) uderzeń stempla w scenie."""
    k = sp["kind"]
    if k == "photos" and sp.get("ch"):
        return [(st[sp["ch"]["vi"]] + VDELAY, sp["ch"]["verdict"])]
    if k == "promise":
        return [(st[i], c) for c, i in d.HOOK4_STAMPS]
    if k == "outro":
        return [(st[i], c) for c, i in d.OUTRO_TALLY]
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
    cfx, sfx, wfx = synth_card_fx3(), v2.synth_stamp_fx(), synth_win_fx()
    segs = []
    for sp, dur, t0 in zip(specs, durs, starts_s):
        s = int(round(t0 * SR))
        k = sp["kind"]
        if k == "card":
            fx[s:s + len(cfx)] += cfx[:N - s]
            continue
        sents = narr(lang, sp["key"], len(sp["pairs"]))
        if k == "orig":
            dd, st, _ = v2.timeline2(sents, 0, orig_lead3(sents, dur))
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
        for ts, code in stamp_times(sp, st):
            a = s + int(ts * SR)
            e = wfx if code == "B" else sfx
            fx[a:a + len(e)] += e[:max(0, N - a)][:len(e)] if a < N else 0
    mus = b.read_f32(os.environ["MUSIC"])
    mus *= 10 ** ((-16 - meter.integrated_loudness(mus)) / 20)
    reps = int(math.ceil(N / len(mus)))
    music[:] = np.concatenate([mus] * reps)[:N]
    f_in, f_out = int(0.5 * SR), int(1.2 * SR)
    music[:f_in] *= np.linspace(0, 1, f_in)[:, None]; music[-f_out:] *= np.linspace(1, 0, f_out)[:, None]
    gv = 10 ** ((-16 - meter.integrated_loudness(voice[mask])) / 20)
    voice *= gv
    gm = 10 ** (((-16 - music_below) - meter.integrated_loudness(music[mask])) / 20)
    music *= gm
    fx *= 10 ** (-3 / 20)
    mix = voice + music + fx + orig
    sf = WD3 / lang
    np.save(sf / "stem_voice.npy", voice.astype(np.float16)); np.save(sf / "stem_music.npy", music.astype(np.float16))
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
    sf = WD3 / lang
    raw = sf / "mix_raw.wav"
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(raw), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True)
    j = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
    flt = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
           f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true:print_format=summary,alimiter=limit=0.75:level=disabled")
    mast = sf / "mix_master.wav"
    b.sh(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-af", flt, "-ar", str(SR), "-c:a", "pcm_s16le", str(mast)])
    out = sf / f"film1_v3_{lang}.mp4"
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
    def add(pid):
        if pid not in seen:
            seen.append(pid)
    for pid in ("machu2", "machu1"):
        add(pid)
    for pid in PROMISE_BG:
        add(pid)
    for cid in d.ORDER:
        ch = d.CH_BY[cid]
        for pid, _, _ in ch["shots"]:
            add(pid)
    return seen


def scene_starts(lang):
    t, out = 0.0, {}
    for sp in plan(lang):
        out[sp["id"]] = t
        t += b.nframes(spec_out(sp, lang)) / FPS
    return out, t


def fmt_t(x):
    x = int(x)
    return f"{x // 60}:{x % 60:02d}"


def cmd_docs():
    m = b.manifest()
    used = used_photos()
    L = ["# Źródła i licencje / Credits and licences (v3)", "", "## Film oryginalny / Original video", "",
         f"- „{d.SRC['title']}” — {d.SRC['author']} — {d.SRC['url']}",
         f"- Licencja / Licence: {d.SRC['license']} (YouTube: Creative Commons Attribution)",
         "- Użyte fragmenty / Excerpts used (s): " + ", ".join(f"{k} {a:.1f}–{e:.1f}" for k, (a, e) in d.WINDOWS.items()),
         "- Fragment „coast” to nienazwane ujęcie z wybrzeża z tego samego filmu. / “coast” is unnamed coastline footage from the same video.", "",
         "## Zdjęcia / Photos (Wikimedia Commons)", ""]
    for pid in used:
        x = m[pid]
        lu = b.LIC_URL.get(x["license"], "") or x.get("license_url", "")
        L.append(f"- **{x['title'].replace('File:', '')}** — {b.artist(pid, 'en')} — {x['license']}" + (f" ({lu})" if lu else "") + f" — {x['page']}")
    L += ["", "## Źródła faktów / Fact sources", ""]
    for ch in d.CH:
        L.append(f"- {ch['name']['en']}: " + ", ".join(ch["sources"]))
    L += ["", "## Zmiany / Changes",
          "- Zdjęcia: kadrowanie 16:9, ruch kamery, nakładki (stempel, pierścień, schemat); bez korekty kolorów. / Photos: 16:9 crop, camera move, overlays (stamp, ring, diagram); no colour grading.",
          "- Oryginał: fragmenty do 7 s, skalowanie do 1080p, dźwięk oryginału ściszony pod lektorem. / Original: excerpts up to 7 s, scaled to 1080p, original sound lowered under the voice-over.", "",
          "## Dźwięk / Sound",
          "- Muzyka / Music: „Transformations 3”, HoliznaCC0, CC0 1.0 — https://freemusicarchive.org/music/holiznacc0/transformations/transformations-3/",
          "- Lektor PL: Piper pl_PL-gosia-medium. Lektor EN: Kokoro-82M, af_heart (Apache-2.0). Mowa syntetyczna / synthetic speech.",
          "- Dźwięki planszy i stempla generowane w kodzie. / Card and stamp sounds generated in code.", ""]
    out = WD3 / "CREDITS_v3.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print("wrote", out)
    for lang in ("pl", "en"):
        try:
            st, total = scene_starts(lang)
        except Exception as e:
            print("no timings for", lang, e); continue
        chap = [(st["hook1"], "Machu Picchu, 1912" if lang == "en" else "Machu Picchu, 1912"), (st["promise"], "The promise: four verdicts" if lang == "en" else "Obietnica: cztery wyroki")]
        for cid in d.ORDER:
            if cid == "machu":
                chap.append((st["machu_pre"], "Machu Picchu: the loop closes" if lang == "en" else "Machu Picchu: pętla się zamyka"))
            else:
                chap.append((st[f"{cid}_orig"], f"{d.CH_BY[cid]['n']}. {d.CH_BY[cid]['name'][lang]} ({d.CH_BY[cid]['mech'][lang].title()})"))
        chap.append((st["outro"], "The count and your vote" if lang == "en" else "Podsumowanie i Twój głos"))
        lines = [f"{fmt_t(t)} {n}" for t, n in chap]
        head = {
            "en": ["Eight places from one travel vlog, and what the frame leaves out. Four verdicts: the frame chooses, reality is bigger, honest frame, better than the vlog.",
                   f"Original footage: \"{d.SRC['title']}\" by {d.SRC['author']} (CC BY) — {d.SRC['url']}"],
            "pl": ["Osiem miejsc z jednego vloga podróżniczego i to, czego kadr nie pokazuje. Cztery wyroki: kadr wybiera, rzeczywistość większa, uczciwy kadr, lepiej niż w vlogu.",
                   f"Materiał źródłowy: „{d.SRC['title']}” — {d.SRC['author']} (CC BY) — {d.SRC['url']}"]}[lang]
        cred = ["", "Photos (Wikimedia Commons): "] + [f"- {m[p]['title'].replace('File:', '')} — {b.artist(p, 'en')} — {m[p]['license']} — {m[p]['page']}" for p in used]
        cred += ["", "Music: Transformations 3 by HoliznaCC0 (CC0).", "Voice: synthetic (Piper / Kokoro)." if lang == "en" else "Lektor: mowa syntetyczna (Piper / Kokoro)."]
        txt = "\n".join(head + [""] + lines + cred)
        (WD3 / f"description_{lang}.txt").write_text(txt, encoding="utf-8")
        print("wrote description", lang, f"{total:.1f}s")


if __name__ == "__main__":
    c = sys.argv[1]
    WD3.mkdir(parents=True, exist_ok=True)
    if c == "plan": cmd_plan(sys.argv[2])
    elif c == "render": cmd_render(sys.argv[2])
    elif c == "concat": cmd_concat(sys.argv[2])
    elif c == "mix": cmd_mix(sys.argv[2])
    elif c == "master": cmd_master(sys.argv[2])
    elif c == "docs": cmd_docs()
    else: raise SystemExit(c)
