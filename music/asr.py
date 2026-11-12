"""Transkrypcja Whisperem z czasami (segmenty i słowa). Użycie: python asr.py <audio> <wyjście> <język> [model]"""
import json, sys, os, subprocess
import numpy as np
from faster_whisper import WhisperModel
A, OUT, LANG = sys.argv[1], sys.argv[2], sys.argv[3]; SIZE = sys.argv[4] if len(sys.argv) > 4 else "medium"
os.makedirs(OUT, exist_ok=True)
m = WhisperModel(SIZE, device="cpu", compute_type="int8")
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", A, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"], capture_output=True, check=True).stdout
audio = np.frombuffer(raw, dtype=np.float32)
segs, info = m.transcribe(audio, language=LANG, word_timestamps=True, vad_filter=True, beam_size=5)
res = []
for s in segs:
    res.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip(), "words": [[round(w.start, 2), round(w.end, 2), w.word] for w in s.words]})
    print(round(s.start, 1), s.text.strip()[:90], flush=True)
json.dump({"duration": info.duration, "segments": res}, open(f"{OUT}/transcript.json", "w"), ensure_ascii=False)
with open(f"{OUT}/transcript.txt", "w") as f:
    for s in res:
        t = int(s["start"]); f.write(f"[{t//60:02d}:{t%60:02d}] {s['text']}\n")
