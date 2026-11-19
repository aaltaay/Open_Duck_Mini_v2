#!/bin/bash
# Install the offline voice stack next to the walk venv.
# Does not edit the Runtime (D6) and does not put a key in a file.
# Models go to $ODM_VOICE_DIR (default $HOME/odm_voice), not into git.
set -euo pipefail

VOICE_DIR="${ODM_VOICE_DIR:-$HOME/odm_voice}"
VENV="${ODM_VOICE_VENV:-$HOME/.virtualenvs/open-duck-voice}"

python3 -m venv "$VENV"
"$VENV/bin/pip" install --upgrade pip
"$VENV/bin/pip" install 'openwakeword==0.4.0' 'vosk==0.3.45' 'piper-tts==1.8.0'

mkdir -p "$VOICE_DIR"
if [ ! -d "$VOICE_DIR/vosk-model-small-en-us-0.15" ]; then
  curl -fsSL -o "$VOICE_DIR/vosk-small.zip" https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
  unzip -q -o "$VOICE_DIR/vosk-small.zip" -d "$VOICE_DIR"
  rm -f "$VOICE_DIR/vosk-small.zip"
fi
if [ ! -f "$VOICE_DIR/en_US-lessac-low.onnx" ]; then
  curl -fsSL -o "$VOICE_DIR/en_US-lessac-low.onnx" \
    https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/low/en_US-lessac-low.onnx
  curl -fsSL -o "$VOICE_DIR/en_US-lessac-low.onnx.json" \
    https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/low/en_US-lessac-low.onnx.json
fi

python3 - "$VOICE_DIR/voice_config.json" "$VOICE_DIR" <<'PY'
import json, sys
path, voice = sys.argv[1], sys.argv[2]
cfg = {
    "mode": "kid",
    "cloud": "off",
    "cloud_base_url": "",
    "cloud_model": "",
    "cloud_key_env": "ODM_CLOUD_API_KEY",
    "wake_model": "hey_jarvis",
    "wake_threshold": 0.5,
    "vosk_model_dir": voice + "/vosk-model-small-en-us-0.15",
    "piper_model": voice + "/en_US-lessac-low.onnx",
    "weather_city": "",
    "input_rate": 48000,
    "input_channels": 2,
    "i2s_shift": 16,
    "resident": False,
    "isolate": True,
}
with open(path, "w", encoding="utf-8") as handle:
    json.dump(cfg, handle, indent=2)
    handle.write("\n")
print(path)
PY

echo "Voice venv: $VENV"
echo "Models: $VOICE_DIR"
echo "Cloud stays off until you export ODM_CLOUD_API_KEY yourself. Do not write the key into a file in the repo."
