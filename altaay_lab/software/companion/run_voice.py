#!/usr/bin/env python3
"""Run one wav through the voice pipeline and write the reply wav.

Example, after install_voice.sh, from the repo root:
  python3 altaay_lab/software/companion/run_voice.py --config "$HOME/odm_voice/voice_config.json" --wav request.wav --out reply.wav

This process is not the walk loop. Do not start it on the walk thread.
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

from altaay_lab.software.companion.audio_pcm import read_wav, write_wav  # noqa: E402
from altaay_lab.software.companion.config import load_config  # noqa: E402
from altaay_lab.software.companion.runtime import build_pipeline  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run one spoken clip through the companion.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--wav", required=True)
    parser.add_argument("--out", default="")
    args = parser.parse_args(argv)
    cfg = load_config(args.config)
    pipe = build_pipeline(cfg)
    samples = read_wav(args.wav)
    turn = pipe.run_pcm(samples, 16000, 1)
    if args.out and turn.audio:
        write_wav(args.out, turn.audio, turn.sample_rate)
    print(json.dumps(turn.as_dict(), sort_keys=True))
    return 0 if turn.woke else 2


if __name__ == "__main__":
    raise SystemExit(main())
