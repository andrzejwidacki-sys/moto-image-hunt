"""Wspólne narzędzia dla skryptów próbek TTS: wczytanie tekstów, zapis WAV, raport JSON."""
import contextlib, json, os, re, sys, time, traceback, wave
from pathlib import Path

import numpy as np

OUT = Path(os.environ.get("OUT", "tts-out"))
OUT.mkdir(parents=True, exist_ok=True)
TEXTS = json.loads((Path(__file__).parent / "texts.json").read_text(encoding="utf-8"))
ORDER = [(k, l) for k in ("t1", "t2", "t3") for l in ("hi", "es", "en", "pl")]
BUDGET_S = float(os.environ.get("BUDGET_MIN", "40")) * 60


def split_sentences(text):
    """Dzieli tekst na zdania (kropka, ?, !, danda) bez cięcia liczb typu 199.5."""
    parts = re.split(r"(?<=[.!?।])\s+", text.strip())
    return [p for p in parts if p]


def silence(sr, sec=0.25):
    return np.zeros(int(sr * sec), dtype=np.float32)


def safe(s):
    return re.sub(r"[^A-Za-z0-9._-]+", "-", str(s)).strip("-")


def write_wav(path, samples, sr):
    a = np.asarray(samples, dtype=np.float32).reshape(-1)
    a = np.clip(a, -1.0, 1.0)
    pcm = (a * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(int(sr))
        w.writeframes(pcm.tobytes())


def wav_seconds(path):
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / w.getframerate()


class Item:
    def __init__(self, meta):
        self.meta = meta

    def save(self, samples, sr):
        p = OUT / f"{self.meta['model']}_{self.meta['text']}_{self.meta['lang']}_{safe(self.meta['voice'])}.wav"
        write_wav(p, samples, sr)
        self.set_file(p)

    def set_file(self, p):
        self.meta["file"] = Path(p).name
        self.meta["audio_s"] = round(wav_seconds(p), 2)


class Report:
    def __init__(self, model):
        self.model = model
        self.t0 = time.time()
        self.data = {"model": model, "python": sys.version.split()[0], "cpus": os.cpu_count(),
                     "notes": {}, "items": []}

    def note(self, k, v):
        self.data["notes"][k] = v
        self.write()

    def over_budget(self):
        return time.time() - self.t0 > BUDGET_S

    @contextlib.contextmanager
    def item(self, text, lang, voice):
        meta = {"model": self.model, "text": text, "lang": lang, "voice": voice, "ok": False}
        it = Item(meta)
        t = time.time()
        try:
            yield it
            meta["ok"] = True
        except Exception as e:  # zapisujemy błąd i jedziemy dalej
            meta["error"] = f"{type(e).__name__}: {e}"[:400]
            traceback.print_exc()
        finally:
            meta["compute_s"] = round(time.time() - t, 2)
            if meta.get("audio_s"):
                meta["rtf"] = round(meta["compute_s"] / meta["audio_s"], 2)
            self.data["items"].append(meta)
            print("ITEM", json.dumps(meta, ensure_ascii=False), flush=True)
            self.write()

    def write(self):
        self.data["elapsed_s"] = round(time.time() - self.t0, 1)
        (OUT / "report.json").write_text(json.dumps(self.data, ensure_ascii=False, indent=1), encoding="utf-8")
