"""Test emocji: Qwen3-TTS CustomVoice 1.7B z instrukcją stylu (parametr instruct)."""
import torch
from common import *

rep = Report("qwen3emo")
from qwen_tts import Qwen3TTSModel

MID = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
model = Qwen3TTSModel.from_pretrained(MID, device_map="cpu", dtype=torch.float32)
rep.note("model_id", MID)
speakers = model.get_supported_speakers()
rep.note("supported_speakers", speakers)
NAMES = {"en": "English", "es": "Spanish"}
STYLES = {
    "neutral": None,
    "excited": "Speak with energy and excitement, like an enthusiastic motorcycle presenter introducing a bike. Lively, upbeat pace.",
    "docu": "Warm, confident documentary narrator. Expressive intonation, slight smile in the voice, natural pauses between sentences.",
}
SPK = [s for s in ("aiden", "ryan") if s in (speakers or [])] or (speakers or [])[:1]
for key, lang in ORDER:
    if lang not in NAMES or rep.over_budget():
        continue
    for sp in SPK[:1]:
        for style, inst in STYLES.items():
            with rep.item(key, lang, f"{sp}-{style}") as it:
                parts = []
                for sent in split_sentences(TEXTS[key][lang]):
                    kw = {"instruct": inst} if inst else {}
                    wavs, sr = model.generate_custom_voice(text=sent, language=NAMES[lang], speaker=sp, **kw)
                    parts += [np.asarray(wavs[0]), silence(sr)]
                it.save(np.concatenate(parts), sr)
