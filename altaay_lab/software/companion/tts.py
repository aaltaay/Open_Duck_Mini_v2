"""Speech out. Piper, low voice, on the CPU.

The voice file is downloaded by install_voice.sh. It is not in git.
Playback on the duck is a later aplay to the I2S amp. This class only
writes samples.
"""

from __future__ import annotations

import array


class ScriptedSpeechOut:
    def __init__(self, rate=16000):
        self.rate = rate
        self.texts = []

    def synthesize(self, text):
        self.texts.append(text)
        # A short tone so a test can hear that speech was produced.
        # 200 ms. Not a voice.
        count = self.rate // 5
        tone = array.array("h", bytes(count * 2))
        for i in range(count):
            tone[i] = 8000 if (i // 20) % 2 == 0 else -8000
        return tone, self.rate


class PiperSpeech:
    def __init__(self, model_path):
        from .onnx_slim import install

        install()
        from piper import PiperVoice

        self.voice = PiperVoice.load(str(model_path))

    def close(self):
        self.voice = None
        import gc

        gc.collect()

    def synthesize(self, text):
        import numpy as np

        parts = []
        rate = 16000
        for chunk in self.voice.synthesize(text):
            rate = int(chunk.sample_rate)
            parts.append(chunk.audio_int16_array)
        if not parts:
            return array.array("h"), rate
        joined = np.concatenate(parts).astype(np.int16)
        return array.array("h", joined.tobytes()), rate
