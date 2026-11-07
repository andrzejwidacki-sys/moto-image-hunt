from common import *

rep = Report("chatterbox")
import torch
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

t = time.time()
model = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
rep.note("load_s", round(time.time() - t, 1))
rep.note("torch", torch.__version__)
rep.note("supported_languages", ChatterboxMultilingualTTS.get_supported_languages())
rep.note("voice_cloning", "nie testowane: brak próbki głosu (celowo, repo jest publiczne)")
for key, lang in ORDER:
    if rep.over_budget():
        rep.note("stopped", "budżet czasu")
        break
    with rep.item(key, lang, "default") as it:
        parts = []
        for sent in split_sentences(TEXTS[key][lang]):
            w = model.generate(sent, language_id=lang)
            parts += [w.squeeze().detach().cpu().numpy(), silence(model.sr)]
        it.save(np.concatenate(parts), model.sr)
