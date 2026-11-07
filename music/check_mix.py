"""Sprawdza zrozumiałość lektora w gotowym miksie: Whisper z czasami słów, WER na scenę względem tekstu narracji.
Porównuje miks (lektor + muzyka) z samym lektorem. Użycie: python check_mix.py <katalog z <lang>_mix.mp3 i <lang>_voice.mp3> <wyjście> [model]"""
import json, sys, os, subprocess
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tts"))
from check_whisper import words, wer
from faster_whisper import WhisperModel

IN, OUT = sys.argv[1], sys.argv[2]
SIZE = sys.argv[3] if len(sys.argv) > 3 else "medium"
os.makedirs(OUT, exist_ok=True)
TEXTS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tts", "texts.json"), encoding="utf-8"))
STARTS = [5, 17, 29, 41, 53]
model = WhisperModel(SIZE, device="cpu", compute_type="int8")
res = []
for lang in ("en", "es", "hi"):
    for kind in ("mix", "voice"):
        f = f"{IN}/{lang}_{kind}.mp3"
        if not os.path.exists(f):
            continue
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"], capture_output=True, check=True).stdout
        audio = np.frombuffer(raw, dtype=np.float32)   # dekodowanie przez ffmpeg, bez av (niezgodność wersji)
        segs, _ = model.transcribe(audio, language=lang, word_timestamps=True, vad_filter=False, beam_size=5)
        ws = [w for s in segs for w in s.words]
        per = []
        for k, st in enumerate(STARTS, 1):
            sel = [w.word for w in ws if st <= (w.start + w.end) / 2 < st + 12]
            hyp = "".join(sel) if False else " ".join(x.strip() for x in sel)
            ref = TEXTS[f"n{k}"][lang]
            e = wer(words(ref, lang), words(hyp, lang))
            per.append({"scene": k, "wer": round(e, 3), "hyp": hyp, "ref": ref})
        outside = [w.word for w in ws if not any(st <= (w.start + w.end) / 2 < st + 12 for st in STARTS)]
        res.append({"lang": lang, "kind": kind, "scenes": per, "words_outside_scenes": " ".join(x.strip() for x in outside)})
        print(lang, kind, [p["wer"] for p in per], flush=True)
json.dump(res, open(f"{OUT}/mixcheck.json", "w"), ensure_ascii=False, indent=1)
