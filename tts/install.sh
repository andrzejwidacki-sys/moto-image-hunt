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
    curl -sSL -o ck.zip https://myshell-public-repo-host.s3.amazonaws.com/openvoice/checkpoints_v2_0417.zip && unzip -q ck.zip ;;
  *) echo "nieznany model: $1"; exit 1 ;;
esac
