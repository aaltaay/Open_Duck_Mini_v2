"""Wake, speech to text, the assistant, and speech out.

This is not the 50 Hz walk thread. The personality engine refuses that
thread on its own. Capture and playback stay half duplex: the amp SD pin
is the listen-or-speak switch already in the wiring (COMPANION.md).
"""

from __future__ import annotations

import time

from .audio_pcm import FRAME_SAMPLES, to_16k_mono

# Set point. The score can cross the line before the wake phrase has finished,
# so the recognizer also hears the second before that crossing. Not a measurement.
PREROLL_SAMPLES = 16000


class VoiceTurn:
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def as_dict(self):
        reply = self.reply or {}
        return {
            "woke": self.woke,
            "heard": self.heard,
            "said": reply.get("said", ""),
            "refused": bool(reply.get("refused")),
            "phases": tuple(self.phases),
            "stored": reply.get("stored"),
            "used_cloud": bool(reply.get("used_cloud")),
            "wake_score": self.wake_score,
            "wake_at": self.wake_at,
            "timings_s": dict(self.timings_s),
            "sample_rate": self.sample_rate,
            "audio_samples": len(self.audio),
        }


class VoicePipeline:
    def __init__(self, assistant, wake=None, stt=None, tts=None, *, threshold=0.5, factories=None, resident=True):
        self.assistant = assistant
        self.wake = wake
        self.stt = stt
        self.tts = tts
        self.threshold = float(threshold)
        self.factories = factories
        self.resident = bool(resident)
        if self.resident and (wake is None or stt is None or tts is None):
            raise ValueError("resident mode needs wake, stt, and tts")
        if not self.resident and not factories:
            raise ValueError("sequential mode needs factories")

    def run_pcm(self, samples, sample_rate, channels=1):
        """samples is mono or interleaved int16. Returns a VoiceTurn."""
        if self.resident:
            return self._run(samples, sample_rate, channels, self.wake, self.stt, self.tts, {})
        started = time.perf_counter()
        wake = self.factories["wake"]()
        load_wake = time.perf_counter() - started
        try:
            return self._run(samples, sample_rate, channels, wake, None, None, {"load_wake": load_wake})
        finally:
            _close(wake)

    def _run(self, samples, sample_rate, channels, wake, stt, tts, load):
        started = time.perf_counter()
        pcm = to_16k_mono(samples, sample_rate, channels)
        prepared = time.perf_counter()
        hit_at, score, name = self._scan(pcm, wake)
        woke_at = time.perf_counter()
        timings = {
            "prepare": prepared - started,
            "wake": woke_at - prepared,
        }
        timings.update(load)
        if hit_at is None:
            timings["total"] = time.perf_counter() - started + sum(load.values())
            return self._turn(False, "", {}, (), {}, [], 16000, score, name, -1, timings)
        utterance = pcm[max(0, hit_at - PREROLL_SAMPLES) :]
        if len(utterance) < FRAME_SAMPLES:
            timings["stt"] = 0.0
            timings["brain"] = 0.0
            timings["tts"] = 0.0
            timings["total"] = time.perf_counter() - started + sum(load.values())
            return self._turn(True, "", {"said": "", "refused": False}, (), {}, [], 16000, score, name, hit_at, timings)
        own_stt = stt is None
        if own_stt:
            # Drop the wake model before the recognizer loads. A second close is safe.
            _close(wake)
            began = time.perf_counter()
            stt = self.factories["stt"]()
            timings["load_stt"] = time.perf_counter() - began
        try:
            heard = stt.transcribe(utterance)
        finally:
            if own_stt:
                _close(stt)
        stt_at = time.perf_counter()
        reply = self.assistant.handle(heard or "")
        brain_at = time.perf_counter()
        own_tts = tts is None
        if own_tts:
            began = time.perf_counter()
            tts = self.factories["tts"]()
            timings["load_tts"] = time.perf_counter() - began
        try:
            audio, rate = tts.synthesize(reply["said"])
        finally:
            if own_tts:
                _close(tts)
        tts_at = time.perf_counter()
        timings["stt"] = stt_at - woke_at - timings.get("load_stt", 0.0)
        timings["brain"] = brain_at - stt_at
        timings["tts"] = tts_at - brain_at - timings.get("load_tts", 0.0)
        timings["total"] = tts_at - started + sum(load.values())
        return self._turn(True, heard, reply, reply["phases"], reply["bodies"], audio, rate, score, name, hit_at, timings)

    def _turn(self, woke, heard, reply, phases, bodies, audio, rate, score, name, hit_at, timings):
        return VoiceTurn(
            woke=woke,
            heard=heard,
            reply=reply,
            phases=phases,
            bodies=bodies,
            audio=audio,
            sample_rate=rate,
            wake_score=score,
            wake_name=name,
            wake_at=hit_at,
            timings_s=timings,
        )

    def _scan(self, pcm, wake):
        wake.reset()
        best = 0.0
        name = ""
        hit_at = None
        for start, frame in _frames(pcm):
            score, model_name = wake.feed(frame)
            if score > best:
                best = score
                name = model_name
            if hit_at is None and score >= self.threshold:
                hit_at = start + len(frame)
        return hit_at, best, name


def _close(engine):
    closer = getattr(engine, "close", None)
    if closer is not None:
        closer()


def _frames(samples):
    count = len(samples) // FRAME_SAMPLES
    for i in range(count):
        start = i * FRAME_SAMPLES
        yield start, samples[start : start + FRAME_SAMPLES]
