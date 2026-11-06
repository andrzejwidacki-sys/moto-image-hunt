# Próbki Gemini TTS przez REST. Klucz tylko ze zmiennej GEMINI_API_KEY (sekret repozytorium), nigdy do logów.
import base64, os, time
import requests
from common import *

KEY = os.environ["GEMINI_API_KEY"]
MODELS = [m.strip() for m in os.environ.get("GEMINI_MODELS", "gemini-3.1-flash-tts-preview,gemini-2.5-flash-preview-tts,gemini-3.8-flash-tts,gemini-3.8-flash-lite-tts").split(",") if m.strip()]
VOICES = [v.strip() for v in os.environ.get("GEMINI_VOICES", "Kore").split(",") if v.strip()]
rep = Report("gemini")
rep.note("models", MODELS)
rep.note("voices", VOICES)


def tts(model, voice, text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}},
        },
    }
    for attempt in range(2):
        r = requests.post(url, json=body, headers={"x-goog-api-key": KEY}, timeout=180)
        if r.status_code == 429 and attempt == 0:
            time.sleep(30)
            continue
        break
    if r.status_code != 200:
        # nie wypisujemy nagłówków; w treści błędu klucza nie ma
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
    part = r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]
    rate = 24000
    if "rate=" in part.get("mimeType", ""):
        rate = int(part["mimeType"].split("rate=")[1].split(";")[0])
    pcm = np.frombuffer(base64.b64decode(part["data"]), dtype="<i2").astype(np.float32) / 32768
    return pcm, rate


for model in MODELS:
    for voice in VOICES:
        for key, lang in ORDER:
            with rep.item(key, lang, f"{model}__{voice}") as it:
                pcm, rate = tts(model, voice, TEXTS[key][lang])
                it.save(pcm, rate)
            time.sleep(7)  # ostrożnie z RPM
