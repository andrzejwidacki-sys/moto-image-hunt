#!/usr/bin/env python3
"""Liczy długości scen 1-5 tak, żeby lektor z przerwami między zdaniami się zmieścił.
dlugosc = LEAD + długość lektora (z przerwami) + 1,0 s zapasu na końcu, zaokrąglona w górę do 0,5 s, minimum 12 s.
Użycie: python3 plan_scene_durs.py --pause 1.0 --clips c1..c5.wav   -> wypisuje 5 liczb oddzielonych spacją"""
import argparse, math, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import assemble_audio as A

ap = argparse.ArgumentParser()
ap.add_argument("--clips", nargs=5, required=True)
ap.add_argument("--pause", type=float, default=1.0)
ap.add_argument("--min", type=float, default=12.0)
a = ap.parse_args()
tmp = Path(tempfile.mkdtemp(prefix="plan_"))
out = []
for i, c in enumerate(a.clips, 1):
    pad, raw = tmp / f"p{i}.wav", tmp / f"r{i}.wav"
    A.pad_pauses(c, pad, a.pause)
    A.prep_clip(pad, raw, 1.0)
    d = A.dur(raw)
    out.append(max(a.min, math.ceil((A.LEAD + d + 1.0) * 2) / 2))
print(" ".join(f"{x:g}" for x in out))
