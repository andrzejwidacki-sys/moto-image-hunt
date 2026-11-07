import subprocess, sys, urllib.request, wave
from pathlib import Path
from common import *

# Głosy do porównania. Licencje: patrz MODEL_CARD zapisane w tts-out/modelcards/
VOICES = {
    "hi": ["hi_IN-pratham-medium", "hi_IN-priyamvada-medium", "hi_IN-rohan-medium"],
    "es": ["es_MX-claude-high", "es_ES-mls_9972-low", "es_ES-davefx-medium", "es_ES-sharvard-medium"],
    "en": ["en_US-ryan-high", "en_GB-alan-medium"],
}
rep = Report("piper")
vdir = Path("voices")
vdir.mkdir(exist_ok=True)
(OUT / "modelcards").mkdir(exist_ok=True)
from piper import PiperVoice

loaded = {}
for lang, names in VOICES.items():
    for name in names:
        fam, rest = name.split("_", 1)
        code, vname, quality = name.split("-", 2)
        base = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/{code.split('_')[0]}/{code}/{vname}/{quality}"
        try:
            subprocess.run([sys.executable, "-m", "piper.download_voices", "--download-dir", str(vdir), name],
                           check=True, capture_output=True, text=True)
            loaded[(lang, name)] = PiperVoice.load(vdir / f"{name}.onnx")
        except Exception as e:
            rep.note(f"voice_failed_{name}", f"{type(e).__name__}: {str(e)[:300]}")
            continue
        try:
            with urllib.request.urlopen(base + "/MODEL_CARD", timeout=30) as r:
                (OUT / "modelcards" / f"{name}.md").write_bytes(r.read())
        except Exception as e:
            rep.note(f"modelcard_failed_{name}", str(e)[:200])

for key, lang in ORDER:
    for (l, name), voice in loaded.items():
        if l != lang:
            continue
        with rep.item(key, lang, name) as it:
            p = OUT / f"piper_{key}_{lang}_{safe(name)}.wav"
            with wave.open(str(p), "wb") as wf:
                voice.synthesize_wav(TEXTS[key][lang], wf)
            it.set_file(p)
