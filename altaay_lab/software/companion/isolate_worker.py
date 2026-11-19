#!/usr/bin/env python3
"""One voice model, then exit.

The parent runs this once for wake, once for speech to text, and once for
speech out. The caller's config is the --config file. isolate is forced off
so this process does not start another child.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _cfg(path):
    from altaay_lab.software.companion.config import load_config

    cfg = load_config(path)
    cfg["isolate"] = False
    cfg["resident"] = False
    return cfg


def _wake(cfg, wav_path):
    from altaay_lab.software.companion.audio_pcm import read_wav
    from altaay_lab.software.companion.pipeline import _frames
    from altaay_lab.software.companion.wake import OpenWakeWordEngine

    # read_wav already returned 16 kHz mono. Do not convert again.
    audio = read_wav(wav_path)
    engine = OpenWakeWordEngine(cfg["wake_model"])
    engine.reset()
    best = 0.0
    woke = False
    try:
        for _start, frame in _frames(audio):
            score, _name = engine.feed(frame)
            if score > best:
                best = score
            if score >= float(cfg["wake_threshold"]):
                woke = True
    finally:
        engine.close()
    return {"woke": woke, "score": best}


def _stt(cfg, wav_path):
    from altaay_lab.software.companion.audio_pcm import read_wav
    from altaay_lab.software.companion.stt import VoskSpeech

    audio = read_wav(wav_path)
    engine = VoskSpeech(cfg["vosk_model_dir"])
    try:
        heard = engine.transcribe(audio)
    finally:
        engine.close()
    return {"heard": heard}


def _tts(cfg, text, reply_path):
    from altaay_lab.software.companion.audio_pcm import write_wav
    from altaay_lab.software.companion.tts import PiperSpeech

    engine = PiperSpeech(cfg["piper_model"])
    try:
        audio, rate = engine.synthesize(text)
    finally:
        engine.close()
    if reply_path:
        write_wav(reply_path, audio, rate)
    return {"sample_rate": int(rate), "samples": len(audio)}


def main(argv=None):
    parser = argparse.ArgumentParser(description="One voice model, then exit")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--stage", choices=("wake", "stt", "tts"), default="wake")
    parser.add_argument("--config", default="")
    parser.add_argument("--wav", default="")
    parser.add_argument("--reply", default="")
    parser.add_argument("--text-file", default="")
    args = parser.parse_args(argv)
    if args.self_check:
        print(json.dumps({"ok": True, "woke": False, "heard": "", "sample_rate": 16000}))
        return 0
    if not args.config:
        print("voice child needs --config", file=sys.stderr)
        return 2
    cfg = _cfg(args.config)
    if args.stage == "wake":
        report = _wake(cfg, args.wav)
    elif args.stage == "stt":
        report = _stt(cfg, args.wav)
    else:
        text = Path(args.text_file).read_text(encoding="utf-8") if args.text_file else ""
        report = _tts(cfg, text, args.reply)
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
