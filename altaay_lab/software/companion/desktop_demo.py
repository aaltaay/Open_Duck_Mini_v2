#!/usr/bin/env python3
"""Desktop drawing of one spoken request and the personality poses.

The picture is not MuJoCo and not the robot. Every frame says DESKTOP DEMO.
The head angles are the personality engine's targets for the phases the
pipeline returned. Ears and eyes are drawn from those same targets.

Usage, from the repo root, with the voice packages installed:
  ODM_VOICE_DIR=$HOME/odm_voice python3 altaay_lab/software/companion/desktop_demo.py --out altaay_lab/software/companion/out/voice_desktop_demo.mp4
"""

from __future__ import annotations

import argparse
import array
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from altaay_lab.software.companion.audio_pcm import write_wav  # noqa: E402
from altaay_lab.software.companion.config import load_config  # noqa: E402
from altaay_lab.software.companion.runtime import build_pipeline  # noqa: E402
from altaay_lab.software.personality.engine import Personality  # noqa: E402

FPS = 20
W, H = 1280, 720


def _font(size):
    from PIL import ImageFont

    env = os.environ.get("ODM_FONT", "")
    if env and os.path.isfile(env):
        return ImageFont.truetype(env, size)
    try:
        path = subprocess.check_output(["fc-match", "-f", "%{file}", "DejaVu Sans"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        path = ""
    if path and os.path.isfile(path):
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _clip(samples, src_rate):
    data = array.array("h")
    if hasattr(samples, "tobytes") and not isinstance(samples, array.array):
        data.frombytes(samples.tobytes())
    else:
        data.extend(int(value) for value in samples)
    if src_rate == 16000:
        return data
    count = int(len(data) * 16000 / src_rate)
    out = array.array("h", bytes(count * 2))
    last = max(1, len(data) - 1)
    for i in range(count):
        out[i] = data[min(last, int(i * src_rate / 16000))]
    return out


def _draw(fonts, cmd, lines):
    from PIL import Image, ImageDraw

    big, small = fonts
    img = Image.new("RGB", (W, H), (24, 32, 48))
    pen = ImageDraw.Draw(img)
    pen.rectangle((0, 0, W, 92), fill=(242, 230, 200))
    pen.text((32, 12), "DESKTOP DEMO", font=big, fill=(20, 20, 20))
    pen.text((32, 54), "Not the robot. Head angles are personality targets.", font=small, fill=(40, 40, 40))
    yaw = float(cmd["head_yaw"])
    pitch = float(cmd["head_pitch"])
    roll = float(cmd["head_roll"])
    neck = float(cmd["neck_pitch"])
    hx = 640 + int(-yaw * 260)
    hy = 300 + int(pitch * 160) + int(-neck * 30)
    pen.ellipse((500, 410, 780, 650), fill=(245, 197, 24), outline=(90, 60, 10), width=4)
    pen.polygon([(600, 450), (680, 450), (hx + 28, hy + 50), (hx - 28, hy + 50)], fill=(245, 197, 24))
    pen.ellipse((hx - 92, hy - 84, hx + 92, hy + 84), fill=(255, 214, 64), outline=(90, 60, 10), width=4)
    pen.polygon([(hx + 64, hy - 8), (hx + 132, hy + 10), (hx + 64, hy + 30)], fill=(214, 112, 28))
    bright = max(0.0, min(1.0, float(cmd["eye_brightness"])))
    eye = int(30 + 225 * bright)
    for side in (-1, 1):
        ex = hx + side * 34 + int(roll * 36) * side
        ey = hy - 18 + int(roll * 10) * side
        pen.ellipse((ex - 18, ey - 20, ex + 18, ey + 20), fill=(eye, eye, eye), outline=(40, 40, 40), width=2)
        if cmd.get("blink") != "off":
            pen.ellipse((ex - 6, ey - 4, ex + 6, ey + 10), fill=(30, 30, 30))
    for side, key in ((-1, "antenna_left"), (1, "antenna_right")):
        lift = max(-1.0, min(1.0, float(cmd[key])))
        base_x = hx + side * 80
        base_y = hy - 60
        tip_y = base_y - int(78 * (0.35 + 0.65 * ((lift + 1) / 2)))
        pen.polygon(
            [(base_x, base_y), (base_x + side * 18, base_y + 16), (base_x + side * 10, tip_y)],
            fill=(255, 214, 64),
            outline=(90, 60, 10),
        )
    pen.rectangle((0, 600, W, H), fill=(16, 20, 32))
    y = 612
    for line in lines:
        pen.text((32, y), line[:90], font=small, fill=(240, 236, 220))
        y += 26
    return img


def _hold(person, phase, seconds):
    person.show_assistant(phase)
    person._phase_until = person.t + seconds + 0.2
    steps = max(1, int(round(seconds * FPS)))
    frames = []
    for i in range(steps):
        if i == 0:
            cmd = person.step(0.0)
        else:
            cmd = person.step(1.0 / FPS)
        frames.append(cmd)
    return frames


def _segment(track, count, clip):
    need = int(round(count / FPS * 16000))
    piece = array.array("h", bytes(need * 2))
    n = min(need, len(clip))
    if n:
        piece[:n] = array.array("h", clip[:n])
    track.extend(piece)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Desktop demo of one spoken timer request.")
    parser.add_argument("--voice-dir", default=os.environ.get("ODM_VOICE_DIR", ""))
    parser.add_argument("--out", required=True)
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
            "resident": True,
        }
    )
    pipe = build_pipeline(cfg)
    phrase = "Hey Jarvis. Set a timer for five minutes."
    parts = []
    rate = 16000
    for chunk in pipe.tts.voice.synthesize(phrase):
        rate = int(chunk.sample_rate)
        parts.append(chunk.audio_int16_array)
    import numpy as np

    request = np.concatenate(parts).astype(np.int16)
    turn = pipe.run_pcm(request, rate, 1)
    if not turn.woke or "timer" not in (turn.heard or ""):
        raise SystemExit("the spoken timer was not heard: %r" % (turn.heard,))
    request_16 = _clip(request, rate)
    reply_16 = _clip(turn.audio, turn.sample_rate)
    person = Personality(mode="kid", seed=1)
    idle = []
    for _ in range(int(0.6 * FPS)):
        idle.append(person.step(1.0 / FPS))
    listen_s = max(1.2, len(request_16) / 16000.0 + 0.1)
    speak_s = max(1.2, len(reply_16) / 16000.0 + 0.15)
    sequence = [("listening", listen_s)]
    if "thinking" in turn.phases:
        sequence.append(("thinking", 0.8))
    sequence.append(("speaking", speak_s))
    sequence.append(("done", 1.0))
    held = [idle]
    for phase, seconds in sequence:
        held.append(_hold(person, phase, seconds))
    fonts = (_font(36), _font(22))
    heard = "Heard: %s" % (turn.heard or "")
    said = "Said: %s" % turn.reply["said"]
    score = "Wake score %.2f, kid mode, desktop demo" % turn.wake_score
    images = []
    labels_for = []
    images.extend(idle)
    labels_for.extend(["waiting"] * len(idle))
    for (phase, _seconds), cmds in zip(sequence, held[1:]):
        images.extend(cmds)
        labels_for.extend([phase] * len(cmds))
    frames = []
    for cmd, phase in zip(images, labels_for):
        frames.append(_draw(fonts, cmd.as_dict(), [score, "Phase: " + phase, heard, said]))
    track = array.array("h")
    _segment(track, len(idle), array.array("h"))
    _segment(track, len(held[1]), request_16)
    index = 2
    if "thinking" in turn.phases:
        _segment(track, len(held[index]), array.array("h"))
        index += 1
    _segment(track, len(held[index]), reply_16)
    index += 1
    _segment(track, len(held[index]), array.array("h"))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as folder:
        folder = Path(folder)
        for i, frame in enumerate(frames):
            frame.save(folder / ("f%04d.png" % i))
        wav = folder / "demo.wav"
        write_wav(wav, track, 16000)
        subprocess.check_call(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-framerate",
                str(FPS),
                "-i",
                str(folder / "f%04d.png"),
                "-i",
                str(wav),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-crf",
                "30",
                "-c:a",
                "aac",
                "-b:a",
                "64k",
                "-shortest",
                "-movflags",
                "+faststart",
                str(out),
            ]
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
