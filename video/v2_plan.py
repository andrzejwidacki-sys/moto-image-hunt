#!/usr/bin/env python3
"""Plan czasowy wersji 2 (hook, sceny, zwrot akcji, odpowiedź, payoff, karta końcowa) z nagrań lektora.
Cięcia ujęć wypadają w środku przerw między zdaniami lektora (cięcie „na oddech”), napisy są zsynchronizowane ze zdaniami.
Użycie: v2_plan.py --lang pl --clips iv0.wav ... iv6.wav --out plan_pl.json [--pause 1.0]"""
import argparse, json, math, sys, tempfile
from pathlib import Path
import numpy as np
from scipy.io import wavfile
sys.path.insert(0, str(Path(__file__).resolve().parent))
from assemble_audio import pad_pauses, prep_clip, dur

LEAD, HOOK_LEAD, TAIL = 0.6, 0.8, 1.3
BLACK, END_S, MIN_SHOT = 2.0, 9.0, 6.0
ceil_half = lambda x: math.ceil(x * 2) / 2


def sentences(wav, minrun=0.6):
    """Zwraca (czas trwania, [(t0,t1) zdań], [środki przerw]) z ciągłej ciszy cyfrowej między zdaniami."""
    sr, x = wavfile.read(str(wav))
    x = x.astype(np.float32) / (32768.0 if x.dtype == np.int16 else 1.0)
    if x.ndim > 1: x = x.mean(axis=1)
    z = np.abs(x) < 1e-4
    runs, i, n = [], 0, len(x)
    while i < n:
        if z[i]:
            j = i
            while j < n and z[j]: j += 1
            if j - i >= minrun * sr and i > 0 and j < n: runs.append((i / sr, j / sr))
            i = j
        else: i += 1
    d = n / sr
    cuts = [0.0] + [v for r in runs for v in r] + [d]
    sents = [(cuts[k], cuts[k + 1]) for k in range(0, len(cuts), 2)]
    return d, sents, [(a + b) / 2 for a, b in runs]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", required=True); ap.add_argument("--clips", nargs=7, required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--pause", type=float, default=1.0)
    ap.add_argument("--nsent", type=int, nargs=7, help="oczekiwana liczba zdań w klipach (kontrola)")
    a = ap.parse_args()
    tmp = Path(tempfile.mkdtemp(prefix="v2plan_"))
    info = []
    for k, c in enumerate(a.clips):
        pad, raw = tmp / f"pad{k}.wav", tmp / f"raw{k}.wav"
        pad_pauses(c, pad, a.pause); prep_clip(pad, raw, 1.0)
        d, sents, mids = sentences(raw)
        if a.nsent and len(sents) != a.nsent[k]:
            sys.exit(f"Klip iv{k}: wykryto {len(sents)} zdań, oczekiwano {a.nsent[k]}")
        info.append(dict(file=str(raw), dur=d, sents=sents, mids=mids))
    segs, t = [], 0.0
    # hook
    h = ceil_half(max(HOOK_LEAD + info[0]["dur"] + 1.2, 10.0))
    segs.append(dict(name="hook", kind="hook", start=t, dur=h, voice_start=t + HOOK_LEAD, clip=0)); t += h
    def scene(name, clip, black=0.0):
        nonlocal t
        i = info[clip]
        d = ceil_half(max(LEAD + i["dur"] + TAIL, 15.0))
        mids = [LEAD + m for m in i["mids"]]
        good = [m for m in mids if MIN_SHOT <= m <= d - MIN_SHOT]
        cut = min(good or mids or [d / 2], key=lambda m: abs(m - d / 2))
        s = dict(name=name, kind="scene", start=t + black, black=black, dur=d, voice_start=t + black + LEAD, clip=clip, cut=cut)
        segs.append(s); t += black + d
    for k in range(1, 5): scene(f"s{k}", k)
    black_start = t
    segs.append(dict(name="turn", kind="black", start=t, dur=BLACK)); t += BLACK
    scene("s5", 5)
    p = ceil_half(max(LEAD + info[6]["dur"] + 1.5, 10.0))
    segs.append(dict(name="payoff", kind="payoff", start=t, dur=p, voice_start=t + LEAD, clip=6)); t += p
    segs.append(dict(name="end", kind="end", start=t, dur=END_S)); t += END_S
    for s in segs:
        if "clip" in s:
            i = info[s["clip"]]
            s["sent_abs"] = [(s["voice_start"] + a0, s["voice_start"] + a1) for a0, a1 in i["sents"]]
            s["voice_file"] = i["file"]; s["voice_dur"] = i["dur"]
    plan = dict(lang=a.lang, total=t, segments=segs, mute=[black_start - 0.6, black_start + BLACK], black=[black_start, black_start + BLACK])
    json.dump(plan, open(a.out, "w"), ensure_ascii=False, indent=1)
    print(a.lang, "total", round(t, 1), [(s["name"], round(s["start"], 1), s["dur"]) for s in segs])


if __name__ == "__main__":
    main()
