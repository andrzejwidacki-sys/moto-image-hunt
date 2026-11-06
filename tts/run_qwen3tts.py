import torch
from common import *

rep = Report("qwen3tts")
rep.note("unsupported", ["pl", "hi"])
from qwen_tts import Qwen3TTSModel

model = None
for mid in ("Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice", "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"):
    try:
        model = Qwen3TTSModel.from_pretrained(mid, device_map="cpu", dtype=torch.float32)
        rep.note("model_id", mid)
        break
    except Exception as e:
        rep.note(f"load_failed_{mid}", f"{type(e).__name__}: {str(e)[:300]}")
if model is None:
    raise SystemExit("żaden model Qwen3-TTS się nie załadował")
langs, speakers = model.get_supported_languages(), model.get_supported_speakers()
rep.note("supported_languages", langs)
rep.note("supported_speakers", speakers)
NAMES = {"en": "English", "es": "Spanish"}
for key, lang in ORDER:
    if lang not in NAMES or rep.over_budget():
        continue
    for sp in (speakers or [])[:2]:
        with rep.item(key, lang, sp) as it:
            wavs, sr = model.generate_custom_voice(text=TEXTS[key][lang], language=NAMES[lang], speaker=sp)
            it.save(wavs[0], sr)
