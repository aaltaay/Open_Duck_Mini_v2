"""One voice turn in a child process.

Sequential mode already loads one model at a time. The child exiting is what
hands the RAM back to the OS. An in-process close does not. LATENCY.md
recorded that a deleted wake model stayed resident.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from .audio_pcm import read_wav, write_wav


def worker_path():
    return str(Path(__file__).with_name("isolate_worker.py"))


class ChildTurn:
    """Same fields run_voice.py reads off an in-process turn."""

    def __init__(self, report, audio, sample_rate):
        self.woke = bool(report.get("woke"))
        self.heard = report.get("heard") or ""
        self.reply = {"said": report.get("said") or ""}
        self.audio = audio
        self.sample_rate = int(sample_rate or 16000)
        self.timings_s = dict(report.get("timings_s") or {})
        self.phases = tuple(report.get("phases") or ())

    def as_dict(self):
        return {
            "woke": self.woke,
            "heard": self.heard,
            "said": self.reply.get("said", ""),
            "phases": self.phases,
            "timings_s": dict(self.timings_s),
            "sample_rate": self.sample_rate,
            "audio_samples": len(self.audio),
        }


class IsolatedPipeline:
    def __init__(self, cfg, command=None):
        self.cfg = cfg
        self.command = list(command) if command is not None else [sys.executable, worker_path()]

    def start(self, samples, sample_rate, channels=1):
        folder = Path(tempfile.mkdtemp(prefix="odm-voice-"))
        wav_path = folder / "turn.wav"
        reply_path = folder / "reply.wav"
        write_wav(wav_path, samples, int(sample_rate))
        cmd = self.command + [
            "--voice-dir",
            str(Path(self.cfg["vosk_model_dir"]).parent),
            "--piper",
            Path(self.cfg["piper_model"]).name,
            "--wav",
            str(wav_path),
            "--reply",
            str(reply_path),
            "--rate",
            str(int(sample_rate)),
            "--channels",
            str(int(channels)),
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        proc._odm_dir = folder  # noqa: SLF001 - cleaned in finish
        proc._odm_reply = reply_path  # noqa: SLF001
        return proc

    def finish(self, proc):
        out, err = proc.communicate()
        folder = getattr(proc, "_odm_dir", None)
        reply_path = getattr(proc, "_odm_reply", None)
        try:
            if proc.returncode != 0:
                raise RuntimeError(err.strip() or "voice child failed")
            report = json.loads(out)
            audio = []
            rate = int(report.get("sample_rate") or 16000)
            if reply_path is not None and Path(reply_path).is_file():
                audio = read_wav(reply_path)
            return ChildTurn(report, audio, rate)
        finally:
            if folder is not None:
                for name in Path(folder).glob("*"):
                    try:
                        name.unlink()
                    except OSError:
                        pass
                try:
                    Path(folder).rmdir()
                except OSError:
                    pass

    def run_pcm(self, samples, sample_rate, channels=1):
        return self.finish(self.start(samples, sample_rate, channels))
