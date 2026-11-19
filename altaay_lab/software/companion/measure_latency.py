#!/usr/bin/env python3
"""Measure wake, speech to text, the assistant, and speech out on this machine.

The audio is synthesized with Piper, then recognized. That is a real wav of
synthetic speech, measured here. It is not a measurement on the Pi.
A separate human clip is used when a wav path is passed.

Usage, from the repo root, with the voice venv:
  ODM_VOICE_DIR=$HOME/odm_voice python3 altaay_lab/software/companion/measure_latency.py --out altaay_lab/software/companion/latency_x86.json
"""

from __future__ import annotations

import argparse
import json
import os
import resource
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from altaay_lab.software.companion.audio_pcm import write_wav  # noqa: E402
from altaay_lab.software.companion.config import load_config  # noqa: E402
from altaay_lab.software.companion.runtime import build_pipeline  # noqa: E402
from altaay_lab.software.companion.weather import WeatherClient, WeatherOffline  # noqa: E402


def _machine():
    mhz = "unknown"
    name = "unknown"
    try:
        for line in open("/proc/cpuinfo", encoding="utf-8", errors="replace"):
            if line.lower().startswith("cpu mhz") and mhz == "unknown":
                mhz = line.split(":", 1)[1].strip()
            elif line.lower().startswith("model name") and name == "unknown":
                name = line.split(":", 1)[1].strip()
    except OSError:
        pass
    return "x86_64, %s cores, reported %s MHz, %s" % (os.cpu_count(), mhz, name)


def _rss_mb():
    # Linux ru_maxrss is kilobytes. This is the peak of this process.
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def _synth(voice, text):
    parts = []
    rate = 16000
    started = time.perf_counter()
    for chunk in voice.synthesize(text):
        rate = int(chunk.sample_rate)
        parts.append(chunk.audio_int16_array)
    import numpy as np

    audio = np.concatenate(parts).astype(np.int16) if parts else np.zeros(0, dtype=np.int16)
    return audio, rate, time.perf_counter() - started


def _turn_row(turn):
    row = turn.as_dict()
    row["label"] = "measured on this x86 VM, not the Pi"
    return row


def _rss_now():
    for line in open("/proc/self/status", encoding="utf-8", errors="replace"):
        if line.startswith("VmRSS:"):
            return int(line.split()[1]) / 1024.0
    return None


def _rows(pipe, audio, repeats):
    rows = []
    for _ in range(repeats):
        pipe.assistant.timers.clear()
        pipe.assistant.timer_jobs.clear()
        rows.append(_turn_row(pipe.run_pcm(audio, 16000, 1)))
    totals = [row["timings_s"]["total"] for row in rows if "total" in row["timings_s"]]
    return rows, (statistics.median(totals) if totals else None)
    row = turn.as_dict()
    row["label"] = "measured on this x86 VM, not the Pi"
    return row


def main(argv=None):
    parser = argparse.ArgumentParser(description="Measure the voice pipeline on this machine.")
    parser.add_argument("--voice-dir", default=os.environ.get("ODM_VOICE_DIR", ""))
    parser.add_argument("--out", required=True)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--human-wav", default="")
    args = parser.parse_args(argv)
    voice_dir = Path(args.voice_dir)
    cfg = load_config(
        {
            "mode": "kid",
            "cloud": "off",
            "vosk_model_dir": str(voice_dir / "vosk-model-small-en-us-0.15"),
            "piper_model": str(voice_dir / "en_US-lessac-low.onnx"),
            "wake_model": "hey_jarvis",
            "wake_threshold": 0.5,
            "weather_city": "",
        }
    )
    phrase = "Hey Jarvis. Set a timer for five minutes."
    from altaay_lab.software.companion.tts import PiperSpeech

    speaker = PiperSpeech(cfg["piper_model"])
    audio, rate, synth_s = _synth(speaker.voice, phrase)
    speaker.close()
    if rate != 16000:
        raise SystemExit("the low voice was expected at 16000 Hz")

    sequential = build_pipeline(cfg)
    seq_rows, seq_median = _rows(sequential, audio, max(1, args.repeats))
    seq_rss = _rss_now()

    resident_cfg = dict(cfg)
    resident_cfg["resident"] = True
    loaded = time.perf_counter()
    resident = build_pipeline(resident_cfg)
    load_s = time.perf_counter() - loaded
    res_rows, res_median = _rows(resident, audio, args.repeats)
    res_rss = _rss_now()
    weather = {"label": "measured on this x86 VM, not the Pi", "city": "Chicago"}
    started = time.perf_counter()
    try:
        weather["said"] = WeatherClient().report("Chicago")
        weather["ok"] = bool(weather["said"])
    except WeatherOffline:
        weather["ok"] = False
        weather["said"] = ""
    weather["seconds"] = time.perf_counter() - started

    human = None
    if args.human_wav:
        from altaay_lab.software.companion.audio_pcm import read_wav

        human_audio = read_wav(args.human_wav)
        started = time.perf_counter()
        heard = resident.stt.transcribe(human_audio)
        human = {
            "label": "measured on this x86 VM, not the Pi",
            "heard": heard,
            "seconds": time.perf_counter() - started,
            "samples": len(human_audio),
        }

    report = {
        "label": "measured on this x86 VM, not the Pi",
        "machine": _machine(),
        "phrase": phrase,
        "audio_seconds": len(audio) / 16000.0,
        "synth_seconds": synth_s,
        "sequential": {
            "note": "Pi default. One model at a time. ONNX arenas off. Measured on this x86 VM, not the Pi.",
            "repeats": seq_rows,
            "median_total_s": seq_median,
            "rss_mb_after": seq_rss,
        },
        "resident": {
            "note": "All three models stay loaded. Faster. Heavier. Measured on this x86 VM, not the Pi.",
            "model_load_seconds": load_s,
            "repeats": res_rows,
            "median_total_s": res_median,
            "rss_mb_after": res_rss,
        },
        "rss_mb_peak": _rss_mb(),
        "weather": weather,
        "human": human,
        "engines": {
            "wake": "openWakeWord 0.4.0 hey_jarvis",
            "stt": "vosk 0.3.45 vosk-model-small-en-us-0.15",
            "tts": "piper-tts 1.8.0 en_US-lessac-low",
        },
    }
    # The machine line is read from this process. It is not a Pi number.
    out = Path(args.out)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    kept = voice_dir / "request_timer.wav"
    write_wav(kept, audio, 16000)
    print(json.dumps({"sequential_median_s": seq_median, "resident_median_s": res_median, "heard": res_rows[-1]["heard"] if res_rows else "", "said": res_rows[-1]["said"] if res_rows else "", "weather_ok": weather["ok"], "rss_mb_peak": report["rss_mb_peak"], "seq_rss_mb": seq_rss, "res_rss_mb": res_rss}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
