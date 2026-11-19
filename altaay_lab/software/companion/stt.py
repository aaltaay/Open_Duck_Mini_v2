"""Speech to text. Vosk small English, the model named for a Pi.

The model directory is downloaded by install_voice.sh. It is not in git.
"""

from __future__ import annotations

import json


class ScriptedSpeech:
    def __init__(self, text):
        self.text = text
        self.calls = 0

    def transcribe(self, samples):
        self.calls += 1
        if len(samples) == 0:
            return ""
        return self.text


class VoskSpeech:
    def __init__(self, model_dir):
        from vosk import KaldiRecognizer, Model

        self.model = Model(str(model_dir))
        self._recognizer = KaldiRecognizer
        self.rate = 16000

    def close(self):
        self.model = None
        import gc

        gc.collect()

    def transcribe(self, samples):
        rec = self._recognizer(self.model, self.rate)
        raw = samples.tobytes() if hasattr(samples, "tobytes") else bytes(samples)
        step = 4000
        for i in range(0, len(raw), step):
            rec.AcceptWaveform(raw[i : i + step])
        final = json.loads(rec.FinalResult())
        return " ".join(str(final.get("text") or "").split())
