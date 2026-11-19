"""Build the real engines from a config. Imports the speech libraries here, not in tests."""

from __future__ import annotations

from .config import build_assistant
from .pipeline import VoicePipeline
from .stt import VoskSpeech
from .tts import PiperSpeech
from .wake import OpenWakeWordEngine
from .weather import WeatherClient


def build_pipeline(cfg, weather=None):
    if cfg.get("isolate"):
        from .isolate import IsolatedPipeline

        if not cfg.get("vosk_model_dir") or not cfg.get("piper_model"):
            raise ValueError("vosk_model_dir and piper_model are required")
        return IsolatedPipeline(cfg)
    if not cfg.get("vosk_model_dir") or not cfg.get("piper_model"):
        raise ValueError("vosk_model_dir and piper_model are required")
    if weather is None:
        weather = WeatherClient()
    assistant = build_assistant(cfg, weather=weather)
    threshold = float(cfg["wake_threshold"])
    if cfg.get("resident"):
        wake = OpenWakeWordEngine(cfg["wake_model"])
        stt = VoskSpeech(cfg["vosk_model_dir"])
        tts = PiperSpeech(cfg["piper_model"])
        return VoicePipeline(assistant, wake, stt, tts, threshold=threshold, resident=True)

    def wake_factory():
        return OpenWakeWordEngine(cfg["wake_model"])

    def stt_factory():
        return VoskSpeech(cfg["vosk_model_dir"])

    def tts_factory():
        return PiperSpeech(cfg["piper_model"])

    return VoicePipeline(
        assistant,
        factories={"wake": wake_factory, "stt": stt_factory, "tts": tts_factory},
        threshold=threshold,
        resident=False,
    )
