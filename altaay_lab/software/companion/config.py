"""Voice config. A credential field is refused. The key lives in the environment."""

from __future__ import annotations

import json
from pathlib import Path

# Names that are allowed to contain the letters of a secret, because they
# name an environment variable and do not hold the secret.
_ALLOWED = {"cloud_key_env"}
_BANNED = ("api_key", "apikey", "token", "secret", "password", "credential")

DEFAULTS = {
    "mode": "kid",
    "cloud": "off",
    "cloud_base_url": "",
    "cloud_model": "",
    "cloud_key_env": "ODM_CLOUD_API_KEY",
    "wake_model": "hey_jarvis",
    "wake_threshold": 0.5,
    "vosk_model_dir": "",
    "piper_model": "",
    "weather_city": "",
    "input_rate": 16000,
    "input_channels": 1,
    "i2s_shift": 16,
    "resident": False,
    "isolate": False,
}


def _reject_secrets(data):
    for key in data:
        if key in _ALLOWED:
            continue
        low = key.lower().replace("-", "_")
        if any(word in low for word in _BANNED) or low == "key":
            raise ValueError("config must not hold a credential")


def load_config(source=None, overrides=None):
    data = dict(DEFAULTS)
    if source is not None:
        if isinstance(source, (str, Path)):
            loaded = json.loads(Path(source).read_text(encoding="utf-8"))
        else:
            loaded = dict(source)
        _reject_secrets(loaded)
        data.update(loaded)
    if overrides:
        _reject_secrets(overrides)
        data.update(overrides)
    if data["mode"] not in ("kid", "adult"):
        raise ValueError("mode must be kid or adult")
    if data["cloud"] not in ("off", "mock", "live"):
        raise ValueError("cloud must be off, mock, or live")
    data["wake_threshold"] = float(data["wake_threshold"])
    data["input_rate"] = int(data["input_rate"])
    data["input_channels"] = int(data["input_channels"])
    data["i2s_shift"] = int(data["i2s_shift"])
    data["resident"] = bool(data.get("resident", False))
    data["isolate"] = bool(data.get("isolate", False))
    if data["resident"] and data["isolate"]:
        raise ValueError("resident and isolate cannot both be on")
    data["weather_city"] = " ".join(str(data.get("weather_city") or "").split())
    return data


def build_assistant(cfg, llm=None, weather=None):
    """Wire the assistant from a config dict. Heavy imports stay in the callers."""
    from .assistant import Assistant
    from .cloud_llm import LiveCloudLLM
    from .mock_llm import MockCloudLLM

    if llm is None:
        if cfg["cloud"] == "live":
            llm = LiveCloudLLM(cfg["cloud_base_url"], cfg["cloud_model"], cfg["cloud_key_env"])
        else:
            llm = MockCloudLLM()
    return Assistant(
        mode=cfg["mode"],
        cloud=cfg["cloud"],
        llm=llm,
        weather=weather,
        weather_city=cfg.get("weather_city") or "",
    )
