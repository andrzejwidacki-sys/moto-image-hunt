#!/usr/bin/env python3
"""Ścieżka dźwiękowa wersji 2 wg planu z v2_plan.py: lektor, muzyka z wyciszaniem pod głos, ambient na scenach,
całkowita cisza w czarnym kadrze (zwrot akcji), normalizacja do −14 LUFS, podłożenie pod wideo."""
import argparse, json, os, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from assemble_audio import run, dur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True); ap.add_argument("--plan", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--music"); ap.add_argument("--music-db", type=float, default=-12.0)
    ap.add_argument("--amb", help="JSON: {nazwa_sceny: {file, db}}; ambient na całą scenę, pętla, fade 1 s")
    ap.add_argument("--amb-lufs", type=float, default=-34.0, help="głośność ambientu (LUFS po normalizacji, przed miksem; lektor ma −16)")
    ap.add_argument("--lufs", type=float, default=-14.0); ap.add_argument("--stems")
    a = ap.parse_args()
    plan = json.load(open(a.plan)); vdur = dur(a.video)
    tmp = Path(a.out).parent / (Path(a.out).stem + "_tmp"); tmp.mkdir(exist_ok=True, parents=True)
    voices = [(s["voice_file"], s["voice_start"]) for s in plan["segments"] if "voice_file" in s]
    inputs, fc = [], []
    for k, (p, st) in enumerate(voices):
        inputs += ["-i", p]; fc.append(f"[{k + 1}:a]adelay={int(st * 1000)}:all=1[v{k}]")
    n = len(voices)
    fc.append("".join(f"[v{k}]" for k in range(n)) + f"amix=inputs={n}:normalize=0:dropout_transition=0,apad=whole_dur={vdur}[voice]")
    idx = n + 1
    mus_labels = []
    # muzyka
    mpath = tmp / "music.wav"
    run(["ffmpeg", "-v", "error", "-y", "-i", a.music, "-af", "loudnorm=I=-16:TP=-2:LRA=11", "-ar", "48000", "-ac", "2", str(mpath)])
    inputs += ["-i", str(mpath)]
    fc.append(f"[{idx}:a]aformat=sample_rates=48000:channel_layouts=stereo,aloop=loop=-1:size=2147483647,atrim=0:{vdur},asetpts=N/SR/TB,volume={a.music_db}dB,afade=t=in:d=2,afade=t=out:st={vdur - 3:.2f}:d=3[mus0]")
    mus_labels.append("[mus0]"); idx += 1
    # ambient
    amb_rep = {}
    if a.amb:
        amb = json.load(open(a.amb))
        for s in plan["segments"]:
            if s["kind"] == "scene" and s["name"] in amb:
                cfg = amb[s["name"]]; ap_ = tmp / f"amb_{s['name']}.wav"
                run(["ffmpeg", "-v", "error", "-y", "-i", cfg["file"], "-af", f"loudnorm=I={a.amb_lufs}:TP=-6:LRA=20", "-ar", "48000", "-ac", "2", str(ap_)])
                inputs += ["-i", str(ap_)]
                st, d = s["start"] - 0.5, s["dur"] + 1.0     # ambient wchodzi 0,5 s przed sceną i kończy 0,5 s po
                st = max(st, 0)
                fc.append(f"[{idx}:a]aformat=sample_rates=48000:channel_layouts=stereo,aloop=loop=-1:size=2147483647,atrim=0:{d},asetpts=N/SR/TB,"
                          f"afade=t=in:d=1.2,afade=t=out:st={d - 1.2:.2f}:d=1.2,volume={cfg.get('db', 0)}dB,adelay={int(st * 1000)}:all=1,apad=whole_dur={vdur}[amb{idx}]")
                mus_labels.append(f"[amb{idx}]"); amb_rep[s["name"]] = Path(cfg["file"]).name; idx += 1
    nb = len(mus_labels)
    fc.append("".join(mus_labels) + f"amix=inputs={nb}:normalize=0:duration=longest,atrim=0:{vdur}[bus]")
    # cisza w czarnym kadrze: wyciszenie szyny muzyka+ambient z narastaniem 0,4 s
    m0, m1 = plan["mute"]; r = 0.4
    expr = f"if(lt(t,{m0 - r}),1,if(lt(t,{m0}),({m0}-t)/{r},if(lt(t,{m1}),0,if(lt(t,{m1 + r}),(t-{m1})/{r},1))))"
    fc.append(f"[bus]volume='{expr}':eval=frame[busm]")
    fc.append("[voice]asplit=2[vmix][vsc]")
    fc.append("[busm][vsc]sidechaincompress=threshold=0.05:ratio=3:attack=20:release=500:makeup=1[duck]")
    fc_pre = list(fc)
    fc.append("[vmix][duck]amix=inputs=2:normalize=0:duration=longest[mix]")
    fc.append(f"[mix]apad=whole_dur={vdur},atrim=0:{vdur},aformat=sample_rates=48000:channel_layouts=stereo[aout]")
    mixwav = tmp / "mix.wav"
    run(["ffmpeg", "-v", "error", "-y", "-i", a.video, *inputs, "-filter_complex", ";".join(fc), "-map", "[aout]", str(mixwav)])
    report = {"video_s": round(vdur, 2), "ambient": amb_rep}
    if a.stems:
        sd = Path(a.stems); sd.mkdir(exist_ok=True, parents=True)
        run(["ffmpeg", "-v", "error", "-y", "-i", a.video, *inputs, "-filter_complex", ";".join(fc_pre), "-map", "[vmix]", str(sd / "voice.wav"), "-map", "[duck]", str(sd / "music.wav")])
        rows = []
        def lufs(f, t0, t1):
            r_ = run(["ffmpeg", "-hide_banner", "-nostats", "-ss", f"{t0}", "-to", f"{t1}", "-i", str(sd / f), "-af", "ebur128", "-f", "null", "-"])
            for line in r_.stderr.split("Summary:")[-1].splitlines():
                if line.strip().startswith("I:"): return float(line.split()[1])
        for s in plan["segments"]:
            if "voice_file" in s:
                t0, t1 = s["voice_start"], s["voice_start"] + s["voice_dur"]
                v, mu = lufs("voice.wav", t0, t1), lufs("music.wav", t0, t1)
                rows.append({"seg": s["name"], "voice_minus_music_db": round(v - mu, 1)})
        report["speech_vs_music"] = rows
        t0, t1 = plan["black"]
        r_ = run(["ffmpeg", "-hide_banner", "-nostats", "-ss", f"{t0 + 0.3}", "-to", f"{t1 - 0.1}", "-i", str(mixwav), "-af", "volumedetect", "-f", "null", "-"])
        report["black_max_volume"] = [l.split("max_volume:")[1].strip() for l in r_.stderr.splitlines() if "max_volume" in l]
    tgt = f"I={a.lufs}:TP=-1.5:LRA=11"
    p1 = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(mixwav), "-af", f"loudnorm={tgt}:print_format=json", "-f", "null", "-"])
    m = json.loads(p1.stderr[p1.stderr.rindex("{"):])
    part = a.out + ".part.mp4"
    ln = (f"loudnorm={tgt}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,alimiter=limit=0.8:level=disabled")
    run(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-i", str(mixwav), "-af", ln, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{vdur}", part])
    r_ = run(["ffmpeg", "-hide_banner", "-nostats", "-i", part, "-af", "ebur128=peak=true", "-f", "null", "-"])
    for line in r_.stderr.split("Summary:")[-1].splitlines():
        line = line.strip()
        if line.startswith("I:"): report["integrated_lufs"] = float(line.split()[1])
        if line.startswith("Peak:"): report["true_peak_dbfs"] = float(line.split()[1])
    report["out_s"] = round(dur(part), 2)
    os.replace(part, a.out)   # final pojawia się dopiero po pełnym sukcesie
    print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
