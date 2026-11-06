import numpy as np
from common import *

# lang_code Kokoro: a=en-US, e=es, h=hi. Polskiego Kokoro nie obsługuje.
PLAN = {"en": ("a", ["af_heart", "am_michael"]), "es": ("e", ["ef_dora", "em_alex"]), "hi": ("h", ["hf_alpha", "hm_omega"])}
rep = Report("kokoro")
rep.note("unsupported", ["pl"])
from kokoro import KPipeline

pipes = {}
for key, lang in ORDER:
    if lang not in PLAN:
        continue
    code, voices = PLAN[lang]
    for v in voices:
        if rep.over_budget():
            break
        with rep.item(key, lang, v) as it:
            if code not in pipes:
                pipes[code] = KPipeline(lang_code=code)
            chunks = [np.asarray(a) for _, _, a in pipes[code](TEXTS[key][lang], voice=v) if a is not None]
            it.save(np.concatenate(chunks), 24000)
