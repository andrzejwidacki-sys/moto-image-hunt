import subprocess, sys, urllib.request, wave
from pathlib import Path
from common import *

# Głosy do porównania. Licencje: patrz MODEL_CARD zapisane w tts-out/modelcards/
VOICES = {
    "pl": ["pl_PL-gosia-medium", "pl_PL-darkman-medium"],
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
            import io
            import numpy as np
            parts, sr = [], None
            for sent in split_sentences(TEXTS[key][lang]):
                buf = io.BytesIO()
                with wave.open(buf, "wb") as wf:
                    voice.synthesize_wav(sent, wf)
                buf.seek(0)
                with wave.open(buf, "rb") as rf:
                    sr = rf.getframerate()
                    parts.append(np.frombuffer(rf.readframes(rf.getnframes()), dtype=np.int16))
                parts.append(np.zeros(sr // 2, dtype=np.int16))  # cyfrowa cisza między zdaniami
            data = np.concatenate(parts[:-1])
            with wave.open(str(p), "wb") as wf:
                wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(data.tobytes())
            it.set_file(p)
