#!/usr/bin/env python3
"""Składa ścieżkę dźwiękową filmu NS200: lektor na osi czasu scen, opcjonalna muzyka z wyciszaniem pod głos,
normalizacja głośności i podłożenie pod wideo. Wymaga ffmpeg i ffprobe.

Przykład:
  python3 assemble_audio.py --video film_en.mp4 --out film_en_audio.mp4 \
      --clips n1.wav n2.wav n3.wav n4.wav n5.wav [--music tlo.mp3] [--lufs -14]
Struktura filmu: tytuł 5 s, pięć scen po 12 s, karta końcowa 8 s (razem 73 s).
"""
import argparse, json, subprocess, sys, tempfile
from pathlib import Path

SCENE_STARTS = [5, 17, 29, 41, 53]   # początki scen 1-5 w sekundach
SCENE_LEN = 12.0
LEAD = 0.6        # lektor zaczyna 0,6 s po wejściu sceny (po 0,4 s fade-in)
TAIL = 0.5        # i kończy najpóźniej 0,5 s przed końcem sceny
MAX_SPEEDUP = 1.15


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        sys.exit("BŁĄD ffmpeg:\n" + " ".join(map(str, cmd)) + "\n" + r.stderr[-1500:])
    return r


def dur(path):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)]).stdout)


def prep_clip(src, dst, speed):
    """Obcięcie ciszy z początku i końca, ewentualne przyspieszenie, normalizacja głośności jednego zdania."""
    af = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,"
          "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse")
    if speed > 1.001:
        af += f",atempo={speed:.4f}"
    af += ",loudnorm=I=-16:TP=-2:LRA=7"
    run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af", af, "-ac", "1", "-ar", "48000", str(dst)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--clips", nargs=5, required=True, help="5 plików lektora, po jednym na scenę")
    ap.add_argument("--music")
    ap.add_argument("--out", required=True)
    ap.add_argument("--lufs", type=float, default=-14.0)
    ap.add_argument("--music-db", type=float, default=-9.0, help="głośność muzyki względem lektora w przerwach (dB); pod głosem dodatkowo ją przyciszamy")
    a = ap.parse_args()

    vdur = dur(a.video)
    maxd = SCENE_LEN - LEAD - TAIL
    report = {"video_s": round(vdur, 2), "clips": [], "warnings": []}
    tmp = Path(tempfile.mkdtemp(prefix="asm_"))
    prepped = []
    for i, (c, start) in enumerate(zip(a.clips, SCENE_STARTS), 1):
        raw = tmp / f"raw{i}.wav"
        prep_clip(c, raw, 1.0)
        d0 = dur(raw)
        speed = 1.0
        if d0 > maxd:
            speed = min(d0 / maxd, MAX_SPEEDUP)
            prep_clip(c, raw, speed)
        d = dur(raw)
        ok = d <= maxd + 0.01
        if not ok:
            report["warnings"].append(f"Scena {i}: lektor {d:.1f} s nie mieści się w {maxd:.1f} s nawet po przyspieszeniu {speed:.2f}x. Skróć tekst.")
        report["clips"].append({"scene": i, "start_s": start + LEAD, "natural_s": round(d0, 2), "speedup": round(speed, 3), "final_s": round(d, 2), "fits": ok})
        prepped.append((raw, start + LEAD))

    music_path = None
    if a.music:   # muzykę wyrównujemy do tej samej głośności co lektora, potem odejmujemy --music-db
        music_path = tmp / "music.wav"
        run(["ffmpeg", "-v", "error", "-y", "-i", a.music, "-af", "loudnorm=I=-16:TP=-2:LRA=11", "-ar", "48000", "-ac", "2", str(music_path)])
    inputs, fc = [], []
    for k, (p, st) in enumerate(prepped):
        inputs += ["-i", str(p)]
        fc.append(f"[{k + 1}:a]adelay={int(st * 1000)}:all=1[v{k}]")  # wejście 0 to wideo
    # magistrala lektora wydłużona do końca filmu: sidechaincompress kończy się razem z najkrótszym wejściem
    fc.append("".join(f"[v{k}]" for k in range(5)) + f"amix=inputs=5:normalize=0:dropout_transition=0,apad=whole_dur={vdur}[voice]")
    n = 6  # indeks wejścia muzyki (0 = wideo, 1-5 = lektor)
    if a.music:
        inputs += ["-i", str(music_path)]
        fc.append(f"[{n}:a]aformat=sample_rates=48000:channel_layouts=stereo,aloop=loop=-1:size=2147483647,atrim=0:{vdur},asetpts=N/SR/TB,volume={a.music_db}dB,afade=t=in:d=2,afade=t=out:st={vdur - 3:.2f}:d=3[mus]")
        fc.append("[voice]asplit=2[vmix][vsc]")
        fc.append("[mus][vsc]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=500:makeup=1[duck]")
        fc.append("[vmix][duck]amix=inputs=2:normalize=0:duration=longest[mix]")
    else:
        fc.append("[voice]anull[mix]")
    fc.append(f"[mix]apad=whole_dur={vdur},atrim=0:{vdur},aformat=sample_rates=48000:channel_layouts=stereo[aout]")
    mixwav = tmp / "mix.wav"
    run(["ffmpeg", "-v", "error", "-y", "-i", a.video, *inputs, "-filter_complex", ";".join(fc), "-map", "[aout]", str(mixwav)])

    # normalizacja głośności w dwóch przebiegach (liniowa, bez pompowania)
    tgt = f"I={a.lufs}:TP=-1.5:LRA=11"
    p1 = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(mixwav), "-af", f"loudnorm={tgt}:print_format=json", "-f", "null", "-"])
    m = json.loads(p1.stderr[p1.stderr.rindex("{"):])
    ln = (f"loudnorm={tgt}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
          f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    run(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-i", str(mixwav), "-af", ln, "-map", "0:v:0", "-map", "1:a:0",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{vdur}", a.out])

    # pomiar końcowy
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", a.out, "-af", "ebur128=peak=true", "-f", "null", "-"])
    tail = r.stderr.split("Summary:")[-1]
    for line in tail.splitlines():
        line = line.strip()
        if line.startswith("I:"):
            report["integrated_lufs"] = float(line.split()[1])
        if line.startswith("Peak:"):
            report["true_peak_dbfs"] = float(line.split()[1])
    report["out_s"] = round(dur(a.out), 2)
    print(json.dumps(report, ensure_ascii=False, indent=1))
    if report["warnings"]:
        sys.exit(2)


if __name__ == "__main__":
    main()
