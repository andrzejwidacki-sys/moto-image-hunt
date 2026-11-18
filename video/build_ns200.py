#!/usr/bin/env python3
"""Film o Bajaj Pulsar NS200 (EN), sceny ze zdjęć: ruch kamery, napisy, miks, mastering.
Zasady: skille narrated-photo-video / photo-video-camera-move / video-making / video-audio-checks.

Środowisko: NS_TTS = katalog z kokoro_ns{1..5}_en_af_heart.wav, NS_PHOTOS = katalog ze zdjęciami (patrz PHOTOS),
NS_MUSIC = plik mp3 (HoliznaCC0 "Drama", CC0), NS_OUT = katalog wyjściowy.
Polecenia: prep | plan | render | concat | mix | master   (kolejno; każde pomija gotowe pliki)
"""
import json, math, os, subprocess, sys, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "commentary"))
import build as b   # text_box, blend, smooth, ffmpeg_pipe, finish_pipe, valid, read_wav, split_by_silence, to48, window_box, read_f32

W, H, FPS, SR = b.W, b.H, b.FPS, b.SR
LEAD, GAP, TAIL, MIN_SCENE = 0.6, 0.5, 1.0, 7.0
OUT = Path(os.environ.get("NS_OUT", "ns200_out"))
PH = Path(os.environ.get("NS_PHOTOS", "photos"))
CANVAS = OUT / "canvas"
FILL = {"topique"}   # kadr 16:9 uciąłby motocykl: całe ujęcie na rozmytym tle (pionowe robią to same)
XF = 0.35
LANG = os.environ.get("NS_LANG", "en")
VOICE = {"en": "af_heart", "hi": "hf_alpha"}[LANG]
FR = b.FONT_M if LANG == "en" else "/usr/share/fonts/truetype/freefont/FreeSans.ttf"       # dewanagari: FreeSans
FB = b.FONT_B if LANG == "en" else "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
SZ = 0 if LANG == "en" else 6                                                                   # FreeSans wygląda mniejszy
CAPS_HI = {
    "s1": ["भारत की एक नेकेड स्पोर्ट बाइक।", "सिंगल-सिलेंडर, लिक्विड-कूल्ड इंजन, जिसकी क्षमता 199.5 सीसी है।"],
    "s2": ["प्रेस्ड स्टील का पेरिमीटर फ्रेम, 17 इंच के अलॉय व्हील और चार वाल्व।", "मौजूदा वर्ज़न में फ़्यूल इंजेक्शन है।",
           "इस बाइक में ABS है: फ़ोर्क पर लगा लेबल यही बताता है।"],
    "s3": ["अर्जेंटीना में यह राउज़र NS200 के नाम से बिकती है।", "इंजन कवर पर DTS-i का बैज है, और टैंक श्राउड पर बड़ा सा 200 लिखा है।"],
    "s4": ["हर बाइक स्टॉक नहीं रहती।", "इस बाइक का एग्ज़ॉस्ट बाद में लगाया हुआ लगता है।"],
    "s5": ["अक्टूबर 2026, मॉस्को।", "एक NS200, जिस पर टॉप केस और कूरियर बैग लगा है।",
           "फ़ोटोग्राफ़र का रूसी कैप्शन कहता है: “भारतीय जापानियों की जगह ले रहे हैं।”"],
}
POPS_HI = {"s1": {1: "199.5 cc"}, "s2": {0: "17 इंच अलॉय", 2: "ABS"}, "s3": {0: "राउज़र NS200", 1: "DTS-i · 200"}, "s5": {0: "मॉस्को · अक्टूबर 2026"}}

# plik, kadr (część zdjęcia, ułamki x0,y0,x1,y1) lub None, autor, licencja (tag w rogu), licencja pełna
PHOTOS = {
    "bishnoi": ("unsplash/01-WUa4ojEQwWg.jpg", None, "Abhivishrut Bishnoi", "free-use licence", "Unsplash License"),
    "banerjee": ("unsplash/02-gOu8VFGMXjs.jpg", None, "Arghya Banerjee", "free-use licence", "Unsplash License"),
    "monroy": ("unsplash/03-fUT4xh7TFv0.jpg", (0.0, 0.10, 1.0, 0.85), "Sebastian Monroy", "free-use licence", "Unsplash License"),
    "topique": ("unsplash/04--hh-RN9dkuk.jpg", (0.0, 0.50, 1.0, 0.95), "Topique SL", "free-use licence", "Unsplash License"),
    "escobar": ("unsplash/05-eVPo6RIBDpQ.jpg", None, "Juan Ignacio Escobar Tosi", "free-use licence", "Unsplash License"),
    "moscow": ("commons/05-Moscow__Bajaj_Pulsar_NS200_red__Oct_2026_01.jpg", None, "Retired electrician", "CC0", "CC0 1.0"),
}

# sceny: klucz TTS, napisy (po zdaniu), ujęcia [(zdjęcie, zdania, ruch)], wyskakujące liczby {zdanie: tekst}
SCENES = [
    dict(id="s1", key="ns1", n=2,
         caps=["A naked sport bike from India.", "A single-cylinder, liquid-cooled engine with a displacement of 199.5 cc."],
         shots=[("bishnoi", [0, 1], ((0.45, 0.52, 1.00), (0.60, 0.56, 1.14)))], pops={1: "199.5 cc"}, title=True),
    dict(id="s2", key="ns2", n=3,
         caps=["A pressed steel perimeter frame, 17-inch alloy wheels and four valves.", "The current version is fuel injected.",
               "This one carries ABS: the label on the fork says so."],
         shots=[("monroy", [0], ((0.50, 0.50, 1.00), (0.52, 0.58, 1.12))),
                ("banerjee", [1, 2], ((0.70, 0.60, 1.00), (0.74, 0.70, 1.50)))], pops={0: "17-inch alloy", 2: "ABS"}),
    dict(id="s3", key="ns3", n=2,
         caps=["In Argentina it is sold as the Rouser NS200.", "The engine cover carries a DTS-i badge, and the tank shroud a big 200."],
         shots=[("escobar", [0, 1], ((0.50, 0.45, 1.15), (0.55, 0.62, 1.50)))], pops={0: "Rouser NS200", 1: "DTS-i · 200"}),
    dict(id="s4", key="ns4", n=2,
         caps=["Not every one stays stock.", "The exhaust on this one looks aftermarket."],
         shots=[("topique", [0, 1], ((0.50, 0.50, 1.00), (0.50, 0.50, 1.10)))], pops={}),
    dict(id="s5", key="ns5", n=3,
         caps=["October 2026, Moscow.", "An NS200 with a top case and a courier bag.",
               "The photographer's Russian caption reads: “Indians are coming to replace the Japanese.”"],
         shots=[("moscow", [0, 1, 2], ((0.50, 0.36, 1.00), (0.55, 0.60, 1.00)))], pops={0: "Moscow · Oct 2026"}),
]
END_S = 8.0

# --------- zdjęcia: kadr, rozmyte tło dla pionowych, wyrównanie jasności ---------


def luma(im):
    a = np.asarray(im.resize((480, 270)), np.float32) / 255.0
    return float((0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]).mean())


def make_canvas(pid):
    f, crop, *_ = PHOTOS[pid]
    im = Image.open(PH / f).convert("RGB")
    if crop:
        w, h = im.size
        im = im.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))
    w, h = im.size
    if w >= h and pid not in FILL:   # poziome: używamy bezpośrednio (okno 16:9 w ruchu kamery)
        return im
    CW, CH = 2880, 1620          # pionowe: całe ujęcie na rozmytym, przyciemnionym tle
    bg = im.copy()
    s = max(CW / w, CH / h)
    bg = bg.resize((int(w * s) + 1, int(h * s) + 1), Image.BICUBIC)
    bg = bg.crop(((bg.width - CW) // 2, (bg.height - CH) // 2, (bg.width - CW) // 2 + CW, (bg.height - CH) // 2 + CH))
    bg = bg.filter(ImageFilter.GaussianBlur(48)).point(lambda v: int(v * 0.55))
    s2 = CH / h
    fg = im.resize((int(w * s2), CH), Image.LANCZOS)
    bg.paste(fg, ((CW - fg.width) // 2, 0))
    return bg


def cmd_prep():
    CANVAS.mkdir(parents=True, exist_ok=True)
    cs = {pid: make_canvas(pid) for pid in PHOTOS}
    ls = {pid: luma(c) for pid, c in cs.items()}
    med = float(np.median(list(ls.values())))
    rep = {}
    for pid, c in cs.items():
        g = min(1.35, max(0.78, (med / ls[pid]) ** 0.5))     # w połowie drogi do mediany
        a = np.asarray(c, np.float32) / 255.0
        a = np.clip(a * g, 0, 1) ** 0.98
        out = Image.fromarray((a * 255 + 0.5).astype(np.uint8))
        out.save(CANVAS / f"{pid}.png")
        rep[pid] = dict(size=out.size, luma_before=round(ls[pid], 3), gain=round(g, 3), luma_after=round(luma(out), 3))
    json.dump(dict(median_before=round(med, 3), photos=rep), open(OUT / "grade.json", "w"), indent=1)
    print(json.dumps(rep, indent=1))


# --------- głos i plan ---------
def narr(key, n):
    key = key if LANG == "en" else key.replace("ns", "nh")
    f = Path(os.environ["NS_TTS"]) / f"kokoro_{key}_{LANG}_{VOICE}.wav"
    x, sr = b.read_wav(f)
    return [b.to48(s, sr) for s in b.split_by_silence(x, sr, n)]


def timeline(sents, tail=TAIL, minlen=MIN_SCENE):
    dur = [len(s) / SR for s in sents]
    starts, t = [], LEAD
    for d in dur:
        starts.append(t); t += d + GAP
    total = max(starts[-1] + dur[-1] + tail, minlen)
    return dur, starts, math.ceil(total * FPS)


def plan():
    P = []
    for sc in SCENES:
        s = narr(sc["key"], sc["n"])
        dur, starts, frames = timeline(s)
        P.append(dict(sc=sc, sents=s, dur=dur, starts=starts, frames=frames))
    return P


def cmd_plan():
    t = 0.0
    for p in plan():
        print(p["sc"]["id"], "start", round(t, 2), "len", round(p["frames"] / FPS, 2), "voice", [round(d, 2) for d in p["dur"]])
        t += p["frames"] / FPS
    print("end card", END_S, "total", round(t + END_S, 2))


# --------- rysowanie ---------
def pop_box(text):
    return b.text_box(text, size=84 + SZ, maxw=1500, bg=(8, 10, 14, 205), pad=(40, 22), path=FB, radius=26)


def scaled(rgba, s):
    if abs(s - 1) < 1e-3:
        return rgba
    im = Image.fromarray(rgba, "RGBA")
    return np.asarray(im.resize((int(im.width * s), int(im.height * s)), Image.BICUBIC))


def tag_box(pid):
    _, _, author, tag, _ = PHOTOS[pid]
    if LANG == "hi":
        tag = "CC0" if tag == "CC0" else "मुफ़्त उपयोग लाइसेंस"
        return b.text_box(f"फ़ोटो: {author} · {tag}", size=26 + SZ, maxw=900, bg=(8, 10, 14, 150), pad=(16, 9), radius=10, path=FR)
    return b.text_box(f"Photo: {author} · {tag}", size=26, maxw=900, bg=(8, 10, 14, 150), pad=(16, 9), radius=10)


def render_scene(p):
    sc = p["sc"]
    out = OUT / f"{sc['id']}.mp4"
    frames = p["frames"]
    if b.valid(out, frames):
        return
    starts, dur = p["starts"], p["dur"]
    shots = [(pid, idx, mv, Image.open(CANVAS / f"{pid}.png").convert("RGB")) for pid, idx, mv in sc["shots"]]
    bounds = [0.0]
    for k in range(1, len(shots)):
        a, c = shots[k - 1][1][-1], shots[k][1][0]
        bounds.append((starts[a] + dur[a] + starts[c]) / 2)
    bounds.append(frames / FPS)
    texts = sc["caps"] if LANG == "en" else CAPS_HI[sc["id"]]
    assert len(texts) == len(dur), (sc["id"], len(texts), len(dur))
    caps = [b.text_box(c, size=42 + SZ, maxw=1560, path=FR) for c in texts]
    pops = {i: pop_box(t) for i, t in (sc["pops"] if LANG == "en" else POPS_HI.get(sc["id"], {})).items()}
    tags = {pid: tag_box(pid) for pid, *_ in shots}
    title = b.text_box("Bajaj Pulsar NS200", size=104, maxw=1700, bg=(8, 10, 14, 190), pad=(54, 26), path=b.FONT_B, radius=30) if sc.get("title") else None
    subt = "Naked sport bike from India" if LANG == "en" else "भारत की एक नेकेड स्पोर्ट बाइक"
    sub = b.text_box(subt, size=44 + SZ, maxw=1500, bg=(8, 10, 14, 150), pad=(30, 14), radius=16, path=FR) if title is not None else None
    pipe, tmp = b.ffmpeg_pipe(out)
    for fr in range(frames):
        t = fr / FPS
        acc = np.zeros((H, W, 3), np.float32); wsum = 0.0; best = (-1, None)
        for k, (pid, idx, mv, im) in enumerate(shots):
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
            acc += b.photo_frame(im, mv, (t - lo) / (hi - lo)).astype(np.float32) * a
            wsum += a
            if a > best[0]:
                best = (a, pid)
        f = (acc / max(wsum, 1e-6)).astype(np.uint8)
        f = np.ascontiguousarray(f)
        if fr < int(0.4 * FPS):                       # krótkie wejście z czerni
            f = (f.astype(np.float32) * (fr / (0.4 * FPS))).astype(np.uint8)
        if best[1]:
            tg = tags[best[1]]
            b.blend(f, tg, W - tg.shape[1] - 40, 36)
        if title is not None and t < 3.6:
            al = min(1.0, t / 0.3) * min(1.0, (3.6 - t) / 0.4)
            b.blend(f, title, (W - title.shape[1]) // 2, 120, al)
            b.blend(f, sub, (W - sub.shape[1]) // 2, 120 + title.shape[0] + 14, al)
        for si in range(len(dur)):
            s0, s1 = starts[si] - 0.05, starts[si] + dur[si] + 0.25
            if s0 <= t <= s1:
                c = caps[si]
                b.blend(f, c, (W - c.shape[1]) // 2, H - c.shape[0] - 56, min(1.0, (t - s0) / 0.12))
            if si in pops and starts[si] - 0.02 <= t <= starts[si] + dur[si] + 0.4 and not (title is not None and t < 3.6):
                q = t - starts[si]
                sc_ = 1.0 + 0.25 * max(0.0, 1 - q / 0.18) ** 2
                pb = scaled(pops[si], sc_)
                b.blend(f, pb, (W - pb.shape[1]) // 2, int(H * 0.30 - pb.shape[0] / 2))
        pipe.stdin.write(f.tobytes())
    b.finish_pipe(pipe, tmp, out)
    print("ok", sc["id"], frames, flush=True)


def end_frames():
    return int(END_S * FPS)


def render_end():
    out = OUT / "end.mp4"
    n = end_frames()
    if b.valid(out, n):
        return
    im = Image.new("RGB", (W, H), (12, 14, 20)); d = ImageDraw.Draw(im)
    FB_, FM = b.font(b.FONT_B, 70), b.font(FR, 38 + SZ)
    if LANG == "en":
        lines = [("Bajaj Pulsar NS200", FB_, (255, 255, 255)),
                 ("Photos: Abhivishrut Bishnoi · Arghya Banerjee · Sebastian Monroy", FM, (225, 228, 235)),
                 ("Juan Ignacio Escobar Tosi · Topique SL · Retired electrician (CC0)", FM, (225, 228, 235)),
                 ("Music: “Drama” by HoliznaCC0 (CC0 1.0)", FM, (225, 228, 235)),
                 ("Voice: synthetic (Kokoro). Specifications: Autocar India, Bajaj.", FM, (225, 228, 235)),
                 ("Licence details are in the description.", FM, (170, 176, 190))]
    else:
        lines = [("Bajaj Pulsar NS200", FB_, (255, 255, 255)),
                 ("फ़ोटो: Abhivishrut Bishnoi · Arghya Banerjee · Sebastian Monroy", FM, (225, 228, 235)),
                 ("Juan Ignacio Escobar Tosi · Topique SL · Retired electrician (CC0)", FM, (225, 228, 235)),
                 ("संगीत: “Drama”, HoliznaCC0 (CC0 1.0)", FM, (225, 228, 235)),
                 ("आवाज़: सिंथेटिक (Kokoro)। विनिर्देश: Autocar India, Bajaj।", FM, (225, 228, 235)),
                 ("लाइसेंस का ब्योरा विवरण में है।", FM, (170, 176, 190))]
    y = 250
    for t, f, c in lines:
        w = d.textlength(t, font=f); d.text(((W - w) / 2, y), t, font=f, fill=c); y += 110 if f is FB_ else 78
    base = np.asarray(im)
    pipe, tmp = b.ffmpeg_pipe(out)
    for fr in range(n):
        t = fr / FPS
        a = min(1.0, t / 0.5) * min(1.0, (END_S - t) / 0.8)
        pipe.stdin.write((base.astype(np.float32) * a).astype(np.uint8).tobytes())
    b.finish_pipe(pipe, tmp, out)
    print("ok end", n, flush=True)


def cmd_render():
    OUT.mkdir(parents=True, exist_ok=True)
    for p in plan():
        render_scene(p)
    render_end()


def cmd_concat():
    names = [f"{sc['id']}.mp4" for sc in SCENES] + ["end.mp4"]
    (OUT / "concat.txt").write_text("".join(f"file '{OUT.resolve() / n}'\n" for n in names))
    out = OUT / "video_silent.mp4"; tmp = str(out) + ".tmp.mp4"
    b.sh(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(OUT / "concat.txt"), "-c", "copy", "-f", "mp4", tmp])
    os.replace(tmp, out); print("concat ok", out)


# --------- dźwięk ---------
def cmd_mix():
    import pyloudnorm as pyln
    P = plan()
    durs = [p["frames"] / FPS for p in P] + [END_S]
    total = sum(durs); N = int(round(total * SR))
    voice = np.zeros((N, 2), np.float32); mask = np.zeros(N, bool)
    meter = pyln.Meter(SR)
    pos = 0.0
    for p, dur in zip(P, durs):
        for sn, st in zip(p["sents"], p["starts"]):
            a = int(round((pos + st) * SR))
            voice[a:a + len(sn), 0] += sn; voice[a:a + len(sn), 1] += sn; mask[a:a + len(sn)] = True
        pos += dur
    mus = b.read_f32(os.environ["NS_MUSIC"])
    mus *= 10 ** ((-16 - meter.integrated_loudness(mus)) / 20)
    music = np.zeros((N, 2), np.float32)
    seg = mus[:N] if len(mus) >= N else np.concatenate([mus, mus])[:N]
    music[:len(seg)] = seg
    f = int(1.2 * SR)
    music[-int(END_S * SR):] *= 2.0   # plansza końcowa: muzyka głośniej (bez lektora)
    music[:f] *= np.linspace(0, 1, f)[:, None]; music[-int(2 * SR):] *= np.linspace(1, 0, int(2 * SR))[:, None]
    voice *= 10 ** ((-16 - meter.integrated_loudness(voice[mask])) / 20)
    music *= 10 ** (((-16 - 15) - meter.integrated_loudness(music[mask])) / 20)
    mix = voice + music
    np.save(OUT / "stem_voice.npy", voice.astype(np.float16)); np.save(OUT / "stem_music.npy", music.astype(np.float16)); np.save(OUT / "mask.npy", mask)
    stats = dict(total_s=total, voice_on_speech_LUFS=float(meter.integrated_loudness(voice[mask])),
                 music_on_speech_LUFS=float(meter.integrated_loudness(music[mask])), peak_mix=float(np.abs(mix).max()))
    stats["voice_minus_music_dB"] = stats["voice_on_speech_LUFS"] - stats["music_on_speech_LUFS"]
    gaps = []
    idx = np.flatnonzero(mask)
    if len(idx):
        d = np.diff(idx); gaps = (d[d > int(0.05 * SR)] / SR).tolist()
    stats["longest_silence_between_speech_s"] = max(gaps) if gaps else 0.0
    json.dump(stats, open(OUT / "mix_stats.json", "w"), indent=1); print(json.dumps(stats, indent=1))
    pk = float(np.abs(mix).max())
    if pk > 0.9:
        mix = mix * (0.9 / pk)
    pcm = (np.clip(mix, -1, 1) * 32767).astype("<i2")
    with wave.open(str(OUT / "mix_raw.wav"), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())


def cmd_master():
    raw = OUT / "mix_raw.wav"
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(raw), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True)
    j = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
    flt = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
           f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true:print_format=summary,alimiter=limit=0.84:level=disabled")
    mast = OUT / "mix_master.wav"
    b.sh(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-af", flt, "-ar", str(SR), "-c:a", "pcm_s16le", str(mast)])
    out = OUT / f"ns200_{LANG}.mp4"; tmp = str(out) + ".tmp.mp4"
    b.sh(["ffmpeg", "-y", "-loglevel", "error", "-i", str(OUT / "video_silent.mp4"), "-i", str(mast), "-map", "0:v", "-map", "1:a",
          "-c:v", "copy", "-af", "alimiter=limit=1:level=disabled", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-f", "mp4", tmp]) if False else \
        b.sh(["ffmpeg", "-y", "-loglevel", "error", "-i", str(OUT / "video_silent.mp4"), "-i", str(mast), "-map", "0:v", "-map", "1:a",
              "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-f", "mp4", tmp])
    os.replace(tmp, out); print("final", out)


if __name__ == "__main__":
    {"prep": cmd_prep, "plan": cmd_plan, "render": cmd_render, "concat": cmd_concat, "mix": cmd_mix, "master": cmd_master}[sys.argv[1]]()
