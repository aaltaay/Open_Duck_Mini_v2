#!/usr/bin/env python3
"""Child process for one sequential voice turn. Exits when the turn is done."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv=None):
    parser = argparse.ArgumentParser(description="One voice turn, then exit")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--voice-dir", default="")
    parser.add_argument("--piper", default="en_US-lessac-low.onnx")
    parser.add_argument("--wav", default="")
    parser.add_argument("--reply", default="")
    parser.add_argument("--rate", type=int, default=16000)
    parser.add_argument("--channels", type=int, default=1)
    args = parser.parse_args(argv)
    if args.self_check:
        print(json.dumps({"ok": True, "woke": False, "heard": "", "said": "", "timings_s": {}, "phases": []}))
        return 0
    from altaay_lab.software.companion.audio_pcm import read_wav, write_wav
    from altaay_lab.software.companion.config import load_config
    from altaay_lab.software.companion.runtime import build_pipeline

    voice = Path(args.voice_dir)
    cfg = load_config(
        {
            "mode": "kid",
            "cloud": "off",
            "vosk_model_dir": str(voice / "vosk-model-small-en-us-0.15"),
            "piper_model": str(voice / args.piper),
            "wake_model": "hey_jarvis",
            "wake_threshold": 0.5,
            "resident": False,
            "isolate": False,
            "weather_city": "",
        }
    )
    audio = read_wav(args.wav)
    pipe = build_pipeline(cfg)
    turn = pipe.run_pcm(audio, args.rate, args.channels)
    if args.reply and turn.audio:
        write_wav(args.reply, turn.audio, turn.sample_rate)
    report = turn.as_dict()
    report["sample_rate"] = turn.sample_rate
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
