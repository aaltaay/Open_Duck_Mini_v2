"""PCM helpers for the voice pipeline.

The mics are 48 kHz, 2 channel, S32_LE (cited, twin/companion/COMPANION.md
section 2). openWakeWord frames are 80 ms of 16 kHz 16-bit audio, which is
1280 samples (cited, the project README). Vosk uses that same 16 kHz rate.
48000 / 16000 = 3, so a block of three mic samples becomes one engine sample.
That ratio is calc only from the two cited rates.

The 24-bit mic sample sits in a 32-bit slot. Which bits are the audio on this
duck has not been captured: BLOCKER. The shift below is the usual I2S packing
(top of the 32-bit word) and it is a set point until a bench capture.
"""

from __future__ import annotations

import array
import wave

FRAME_SAMPLES = 1280
ENGINE_RATE = 16000
MIC_RATE = 48000
# Set point until a capture on this duck. Not a measured alignment.
I2S_SHIFT = 16


def downsample_48k(samples):
    """Average each three samples. Input is mono int16 at 48 kHz."""
    count = len(samples) // 3
    out = array.array("h", bytes(count * 2))
    for i in range(count):
        j = i * 3
        out[i] = (int(samples[j]) + int(samples[j + 1]) + int(samples[j + 2])) // 3
    return out


def _as_int16(samples):
    if isinstance(samples, array.array) and samples.typecode == "h":
        return array.array("h", samples)
    data = array.array("h")
    data.extend(int(value) for value in samples)
    return data


def to_16k_mono(samples, sample_rate, channels=1):
    """Mono int16 at 16 kHz. channels is 1 or 2, interleaved."""
    if channels not in (1, 2):
        raise ValueError("channels must be 1 or 2")
    if sample_rate not in (ENGINE_RATE, MIC_RATE):
        raise ValueError("sample rate must be 16000 or 48000")
    data = _as_int16(samples)
    if channels == 2:
        pairs = len(data) // 2
        mono = array.array("h", bytes(pairs * 2))
        for i in range(pairs):
            mono[i] = (int(data[2 * i]) + int(data[2 * i + 1])) // 2
        data = mono
    if sample_rate == MIC_RATE:
        data = downsample_48k(data)
    return data


def s32_frames_to_s16(raw, channels, shift=I2S_SHIFT):
    """Little-endian S32_LE bytes to interleaved int16."""
    if shift < 0 or shift > 16:
        raise ValueError("shift must be 0 to 16")
    words = array.array("i")
    words.frombytes(raw)
    if words.itemsize != 4:
        raise ValueError("int must be 4 bytes")
    if sys_big():
        words.byteswap()
    out = array.array("h", bytes((len(words)) * 2))
    for i, word in enumerate(words):
        out[i] = max(-32768, min(32767, word >> shift))
    return to_16k_mono(out, MIC_RATE, channels)


def sys_big():
    import sys

    return sys.byteorder != "little"


def read_wav(path):
    """Read a PCM wav as mono int16 at 16 kHz. Stereo is averaged."""
    with wave.open(str(path), "rb") as handle:
        channels = handle.getnchannels()
        width = handle.getsampwidth()
        rate = handle.getframerate()
        raw = handle.readframes(handle.getnframes())
    if width == 2:
        samples = array.array("h")
        samples.frombytes(raw)
        if sys_big():
            samples.byteswap()
        return to_16k_mono(samples, rate, channels)
    if width == 4:
        if rate != MIC_RATE:
            raise ValueError("32-bit wav must be 48000 Hz")
        return s32_frames_to_s16(raw, channels)
    raise ValueError("wav must be 16-bit or 32-bit PCM")


def write_wav(path, samples, sample_rate):
    if isinstance(samples, array.array) and samples.typecode == "h":
        data = array.array("h", samples)
    elif hasattr(samples, "tobytes") and not isinstance(samples, (bytes, bytearray)):
        data = array.array("h")
        data.frombytes(samples.tobytes())
    else:
        data = array.array("h")
        data.extend(int(value) for value in samples)
    if sys_big():
        data.byteswap()
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(int(sample_rate))
        handle.writeframes(data.tobytes())


def frames(samples, size=FRAME_SAMPLES):
    """Yield full frames. The tail shorter than one frame is dropped."""
    count = len(samples) // size
    for i in range(count):
        start = i * size
        yield start, samples[start : start + size]
