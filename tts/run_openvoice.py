# OpenVoice V2 = MeloTTS (głos bazowy) + konwerter barwy. Bez próbki głosu testujemy tylko głos bazowy
# oraz "dymny" test konwertera (barwa z innego głosu bazowego).
import glob, os
from common import *

rep = Report("openvoice")
rep.note("unsupported", ["pl", "hi"])
from melo.api import TTS

MELO = {"en": "EN", "es": "ES"}
models = {}
for key, lang in ORDER:
    if lang not in MELO or rep.over_budget():
        continue
    with rep.item(key, lang, "melo-base") as it:
        if lang not in models:
            models[lang] = TTS(language=MELO[lang], device="cpu")
        m = models[lang]
        spk = list(m.hps.data.spk2id.items())[0]
        p = OUT / f"openvoice_{key}_{lang}_melo-base.wav"
        m.tts_to_file(TEXTS[key][lang], spk[1], str(p))
        it.set_file(p)
        rep.note(f"melo_speaker_{lang}", spk[0])

# test konwertera (best effort)
try:
    import torch
    from openvoice import se_extractor
    from openvoice.api import ToneColorConverter
    ck = "checkpoints_v2"
    tcc = ToneColorConverter(f"{ck}/converter/config.json", device="cpu")
    tcc.load_ckpt(f"{ck}/converter/checkpoint.pth")
    src = OUT / "openvoice_s1_es_melo-base.wav"
    ref = OUT / "openvoice_s1_en_melo-base.wav"
    with rep.item("s1", "es", "tone-convert-smoke") as it:
        tgt_se, _ = se_extractor.get_se(str(ref), tcc, vad=False)
        src_se = torch.load(f"{ck}/base_speakers/ses/es.pth", map_location="cpu")
        p = OUT / "openvoice_s1_es_tone-convert-smoke.wav"
        tcc.convert(audio_src_path=str(src), src_se=src_se, tgt_se=tgt_se, output_path=str(p))
        it.set_file(p)
except Exception as e:
    rep.note("converter_failed", f"{type(e).__name__}: {str(e)[:300]}")
