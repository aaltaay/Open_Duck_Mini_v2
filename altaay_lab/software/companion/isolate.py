"""One voice model per child process.

Sequential mode already loads one model at a time. The child exiting is what
hands the RAM back to the OS. An in-process close does not. LATENCY.md
recorded that a deleted wake model stayed resident. The fit run in
software/pi_fit/FIT.md measured this same one-process-per-model split.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from .audio_pcm import read_wav, to_16k_mono, write_wav
from .config import build_assistant


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

    def run_pcm(self, samples, sample_rate, channels=1):
        """Wake, then speech to text, then speech out. Each model is its own process."""
        folder = Path(tempfile.mkdtemp(prefix="odm-voice-"))
        try:
            pcm = to_16k_mono(samples, int(sample_rate), int(channels))
            wav_path = folder / "turn.wav"
            # One conversion. The child reads 16 kHz mono and must not convert again.
            write_wav(wav_path, pcm, 16000)
            cfg_path = folder / "voice_config.json"
            handed = dict(self.cfg)
            handed["isolate"] = False
            handed["resident"] = False
            cfg_path.write_text(json.dumps(handed), encoding="utf-8")
            wake = self._stage("wake", cfg_path, wav_path)
            if not wake.get("woke"):
                return ChildTurn(
                    {"woke": False, "heard": "", "said": "", "phases": [], "timings_s": {}},
                    [],
                    16000,
                )
            heard = self._stage("stt", cfg_path, wav_path).get("heard") or ""
            reply = build_assistant(self.cfg).handle(heard)
            text_path = folder / "say.txt"
            text_path.write_text(reply.get("said") or "", encoding="utf-8")
            reply_path = folder / "reply.wav"
            spoken = self._stage("tts", cfg_path, wav_path, text_path=text_path, reply_path=reply_path)
            audio = read_wav(reply_path) if reply_path.is_file() else []
            report = {
                "woke": True,
                "heard": heard,
                "said": reply.get("said") or "",
                "phases": list(reply.get("phases") or ()),
                "timings_s": {},
                "sample_rate": int(spoken.get("sample_rate") or 16000),
            }
            return ChildTurn(report, audio, report["sample_rate"])
        finally:
            for name in folder.glob("*"):
                try:
                    name.unlink()
                except OSError:
                    pass
            try:
                folder.rmdir()
            except OSError:
                pass

    def _stage(self, stage, cfg_path, wav_path, text_path=None, reply_path=None):
        cmd = self.command + [
            "--stage",
            stage,
            "--config",
            str(cfg_path),
            "--wav",
            str(wav_path),
        ]
        if text_path is not None:
            cmd.extend(["--text-file", str(text_path)])
        if reply_path is not None:
            cmd.extend(["--reply", str(reply_path)])
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(err.strip() or out.strip() or "voice child failed")
        return json.loads(out)
