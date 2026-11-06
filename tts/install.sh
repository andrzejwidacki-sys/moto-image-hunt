#!/usr/bin/env bash
set -euxo pipefail
CPU=https://download.pytorch.org/whl/cpu
case "$1" in
  piper)
    pip install piper-tts ;;
  kokoro)
    sudo apt-get update -qq && sudo apt-get install -y -qq espeak-ng
    pip install torch --index-url $CPU
    pip install kokoro ;;
  chatterbox)
    pip install torch==2.6.0 torchaudio==2.6.0 --index-url $CPU
    pip install "git+https://github.com/resemble-ai/chatterbox.git" || pip install chatterbox-tts
    pip freeze | grep -i -E "chatterbox|torch|transformers" ;;
  qwen3tts)
    sudo apt-get update -qq && sudo apt-get install -y -qq sox libsox-dev
    pip install torch torchaudio --index-url $CPU
    pip install qwen-tts ;;
  openvoice)
    sudo apt-get update -qq && sudo apt-get install -y -qq libsndfile1 ffmpeg
    pip install torch torchaudio --index-url $CPU
    pip install av
    pip install "git+https://github.com/myshell-ai/MeloTTS.git"
    pip install --no-deps "git+https://github.com/myshell-ai/OpenVoice.git"
    pip install faster-whisper pydub librosa wavmark inflect unidecode
    python -m unidic download
    # checkpointy konwertera: najpierw HF (repo myshell-ai/OpenVoiceV2), awaryjnie S3; brak nie blokuje testu głosu bazowego
    timeout 300 python -c "from huggingface_hub import snapshot_download; snapshot_download('myshell-ai/OpenVoiceV2', local_dir='checkpoints_v2', allow_patterns=['converter/*','base_speakers/ses/es.pth','base_speakers/ses/en-*.pth'])" || \
      { curl -fsSL --max-time 120 -o ck.zip https://myshell-public-repo-host.s3.amazonaws.com/openvoice/checkpoints_v2_0417.zip && unzip -q ck.zip; } || echo "BRAK checkpointow konwertera" ;;
  *) echo "nieznany model: $1"; exit 1 ;;
esac
