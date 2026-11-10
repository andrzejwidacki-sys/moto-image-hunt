"""Transkrypcja Whisperem GOTOWEGO dźwięku filmu (lektor + muzyka + ambient) i WER na scenę względem tekstu narracji.
Użycie: python check_final.py <katalog z <lang>_final.mp3 i plan_<lang>.json> <wyjście> [model]"""
import json, re, sys, os, subprocess
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tts"))
from check_whisper import words, wer
from faster_whisper import WhisperModel
IN, OUT = sys.argv[1], sys.argv[2]; SIZE = sys.argv[3] if len(sys.argv) > 3 else "medium"
os.makedirs(OUT, exist_ok=True)
TEXTS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tts", "texts.json"), encoding="utf-8"))
KEY = {"hook": "iv0", "s1": "ix1", "s2": "ix2", "s3": "ix3", "s4": "ix4", "s5": "ix5", "payoff": "iv6"}
model = WhisperModel(SIZE, device="cpu", compute_type="int8"); res = []
for lang in ("en", "es", "hi", "pl"):
    f = f"{IN}/{lang}_final.mp3"
    if not os.path.exists(f): continue
    plan = json.load(open(f"{IN}/plan_{lang}.json"))
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"], capture_output=True, check=True).stdout
    audio = np.frombuffer(raw, dtype=np.float32)
    segs, _ = model.transcribe(audio, language=lang, word_timestamps=True, vad_filter=False, beam_size=5)
    ws = [w for s in segs for w in s.words]; per = []
    for s in plan["segments"]:
        if s["name"] not in KEY: continue
        a, b = s["voice_start"] - 0.5, s["voice_start"] + s["voice_dur"] + 0.5
        hyp = " ".join(w.word.strip() for w in ws if a <= (w.start + w.end) / 2 < b)
        ref = re.sub(r"\[([^\]]+)\]\(/[^)]*/\)", r"\1", TEXTS[KEY[s["name"]]][lang])
        per.append({"scene": s["name"], "wer": round(wer(words(ref, lang), words(hyp, lang)), 3), "hyp": hyp, "ref": ref})
    res.append({"lang": lang, "scenes": per}); print(lang, [(p["scene"], p["wer"]) for p in per], flush=True)
    json.dump(res, open(f"{OUT}/finalcheck.json", "w"), ensure_ascii=False, indent=1)
