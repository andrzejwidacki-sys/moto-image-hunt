"""Test emocji: Chatterbox Multilingual z różnymi wartościami exaggeration / cfg_weight (EN, ES)."""
from common import *

rep = Report("cbemo")
import torch
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

model = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
rep.note("torch", torch.__version__)
SETS = [(0.5, 0.5), (0.8, 0.4), (1.1, 0.3)]
for key, lang in ORDER:
    if lang not in ("en", "es"):
        continue
    for ex, cfg in SETS:
        if rep.over_budget():
            break
        with rep.item(key, lang, f"ex{ex}-cfg{cfg}") as it:
            parts = []
            for sent in split_sentences(TEXTS[key][lang]):
                w = model.generate(sent, language_id=lang, exaggeration=ex, cfg_weight=cfg)
                parts += [w.squeeze().detach().cpu().numpy(), silence(model.sr)]
            it.save(np.concatenate(parts), model.sr)
