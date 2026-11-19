"""Wake word. openWakeWord, one model, on a thread that is not the walk.

The default phrase is the published hey_jarvis model (Apache-2.0).
The score threshold 0.5 is the project default (cited, the README).
A frame is 1280 samples, 80 ms at 16 kHz (cited, the README).
"""

from __future__ import annotations

from .audio_pcm import FRAME_SAMPLES


class WakeHit:
    def __init__(self, detected, name, score, at_sample):
        self.detected = bool(detected)
        self.name = name or ""
        self.score = float(score)
        self.at_sample = int(at_sample)


class ScriptedWake:
    """Test double. Fires once, at a fixed sample, with a fixed score."""

    def __init__(self, at_sample=16000, score=0.9, name="hey_jarvis"):
        self.at_sample = int(at_sample)
        self.score = float(score)
        self.name = name
        self.seen = 0
        self.reset_count = 0

    def reset(self):
        self.seen = 0
        self.reset_count += 1

    def feed(self, frame):
        start = self.seen
        self.seen += len(frame)
        if start < self.at_sample <= self.seen:
            return self.score, self.name
        return 0.0, self.name


class OpenWakeWordEngine:
    def __init__(self, model_name="hey_jarvis"):
        import warnings

        warnings.filterwarnings("ignore", message="Specified provider")
        from .onnx_slim import install

        install()
        import openwakeword
        from openwakeword.model import Model

        if model_name not in openwakeword.models:
            raise ValueError("unknown wake model")
        path = openwakeword.models[model_name]["model_path"]
        # One model, not the whole set. ONNX, CPU. VAD stays off (threshold 0).
        self.model = Model(wakeword_model_paths=[path], vad_threshold=0)
        self.model_name = model_name
        self._np = __import__("numpy")

    def close(self):
        self.model = None
        import gc

        gc.collect()

    def reset(self):
        self.model.reset()
        pre = self.model.preprocessor
        pre.raw_data_buffer.clear()
        pre.melspectrogram_buffer = self._np.ones((76, 32))
        pre.accumulated_samples = 0
        pre.feature_buffer = pre._get_embeddings(self._np.zeros(160000).astype(self._np.int16))

    def feed(self, frame):
        audio = self._np.asarray(frame, dtype=self._np.int16)
        if audio.shape != (FRAME_SAMPLES,):
            raise ValueError("wake frame must be 1280 samples")
        scores = self.model.predict(audio)
        if not scores:
            return 0.0, self.model_name
        name = max(scores, key=scores.get)
        return float(scores[name]), name
