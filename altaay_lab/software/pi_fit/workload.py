#!/usr/bin/env python3
"""Run the walk, the voice pipeline, the dock detector, and the autonomy loop.

This is the software stack, not the USB servo bus. Bus time is added later
from SOFTWARE.md and is calc only. Nothing here is a hardware pass.

Roles:
  stack    walk thread plus autonomy, and a voice request and one camera frame
  voice    one sequential voice turn, then exit
  camera   one detect() on the synthetic dock frame, then exit
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from altaay_lab.software.pi_fit.budget import PERIOD_S, slice_stats, work_stats  # noqa: E402


def _rss_mib():
    try:
        for line in open("/proc/self/status", encoding="utf-8", errors="replace"):
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) / 1024.0
            if line.startswith("VmHWM:"):
                pass
    except OSError:
        return None
    return None


def _hwm_mib():
    try:
        for line in open("/proc/self/status", encoding="utf-8", errors="replace"):
            if line.startswith("VmHWM:"):
                return int(line.split()[1]) / 1024.0
    except OSError:
        return None
    return None


def _cgroup_mib(cgroup_dir, name):
    if not cgroup_dir:
        return None
    path = Path(cgroup_dir) / name
    try:
        raw = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if raw == "max" or raw == "":
        return None
    return int(raw) / (1024.0 * 1024.0)


def _move_pid(pid, cgroup_dir):
    if not cgroup_dir:
        return
    path = Path(cgroup_dir) / "cgroup.procs"
    path.write_text("%s\n" % pid, encoding="utf-8")


def _policy(path, threads):
    import numpy as np
    import onnxruntime as ort

    options = ort.SessionOptions()
    options.intra_op_num_threads = int(threads)
    options.inter_op_num_threads = 1
    sess = ort.InferenceSession(str(path), sess_options=options, providers=["CPUExecutionProvider"])
    inp = sess.get_inputs()[0]
    width = None
    for dim in inp.shape:
        if isinstance(dim, int) and dim > 1:
            width = dim
    if width is None:
        width = 1
        for guess in (200, 120, 101, 80, 64, 48, 16):
            try:
                sess.run(None, {inp.name: [np.zeros(guess, dtype=np.float32)]})
                width = guess
                break
            except Exception:
                continue
    obs = np.zeros(width, dtype=np.float32)
    # One warmup so the first timed cycle is not the load.
    sess.run(None, {inp.name: [obs]})
    return sess, inp.name, obs


def _walk(sess, name, obs, seconds, rows, stop, cpu):
    if cpu is not None:
        try:
            os.sched_setaffinity(0, {int(cpu)})
        except OSError:
            pass
    end = time.perf_counter() + float(seconds)
    while time.perf_counter() < end and not stop.is_set():
        started = time.perf_counter()
        out = sess.run(None, {name: [obs]})
        action = out[0][0]
        # Keep the result live so a later change cannot treat the run as dead.
        obs[0] = float(action[0]) * 0.0
        work = time.perf_counter() - started
        remain = PERIOD_S - work
        if remain > 0.0:
            time.sleep(remain)
        rows.append((work, time.perf_counter() - started, started))


def _autonomy(stop, cpu):
    if cpu is not None:
        try:
            os.sched_setaffinity(0, {int(cpu)})
        except OSError:
            pass
    from altaay_lab.software.autonomy.plant import HomePlant
    from altaay_lab.software.autonomy.supervisor import Supervisor

    plant = HomePlant()
    sup = Supervisor(seed=1)
    dt = 0.1
    t = 0.0
    while not stop.is_set():
        began = time.perf_counter()
        sup.step(plant, t, dt, events=[])
        t += dt
        spare = dt - (time.perf_counter() - began)
        if spare > 0.0:
            time.sleep(spare)


def _voice_config(voice_dir, piper):
    from altaay_lab.software.companion.config import load_config

    voice = Path(voice_dir)
    return load_config(
        {
            "mode": "kid",
            "cloud": "off",
            "vosk_model_dir": str(voice / "vosk-model-small-en-us-0.15"),
            "piper_model": str(voice / piper),
            "wake_model": "hey_jarvis",
            "wake_threshold": 0.5,
            "resident": False,
            "isolate": False,
            "weather_city": "",
        }
    )


def _force_rest(cfg, audio):
    """Load speech to text, then speech out, one at a time, if wake did not fire."""
    from altaay_lab.software.companion.runtime import build_pipeline

    pipe = build_pipeline(cfg)
    timings = {}
    began = time.perf_counter()
    stt = pipe.factories["stt"]()
    timings["load_stt"] = time.perf_counter() - began
    try:
        heard = stt.transcribe(audio)
    finally:
        closer = getattr(stt, "close", None)
        if closer:
            closer()
    began = time.perf_counter()
    tts = pipe.factories["tts"]()
    timings["load_tts"] = time.perf_counter() - began
    try:
        spoken, rate = tts.synthesize("Timer set for 5 minutes.")
    finally:
        closer = getattr(tts, "close", None)
        if closer:
            closer()
    timings["spoken_samples"] = len(spoken)
    timings["rate"] = rate
    timings["heard"] = heard
    return timings


def run_voice(voice_dir, piper, wav_path):
    from altaay_lab.software.companion.audio_pcm import read_wav
    from altaay_lab.software.companion.runtime import build_pipeline

    audio = read_wav(wav_path)
    cfg = _voice_config(voice_dir, piper)
    pipe = build_pipeline(cfg)
    rss_before = _rss_mib()
    turn = pipe.run_pcm(audio, 16000, 1)
    forced = None
    if not turn.woke:
        forced = _force_rest(cfg, audio)
    return {
        "label": "measured in emulation",
        "woke": bool(turn.woke),
        "heard": turn.heard,
        "said": (turn.reply or {}).get("said", ""),
        "timings_s": turn.timings_s,
        "forced_stages": forced,
        "rss_before_mib": rss_before,
        "rss_after_mib": _rss_mib(),
        "hwm_mib": _hwm_mib(),
        "piper": piper,
    }


def run_camera():
    import numpy as np

    from altaay_lab.software.pi_fit.frame import dock_frame
    from altaay_lab.twin.dock.camera.camera_dock import detect

    image = dock_frame(np)
    started = time.perf_counter()
    found = detect(image)
    return {
        "label": "measured in emulation",
        "seconds": time.perf_counter() - started,
        "found": found is not None,
        "width": int(image.shape[1]),
        "height": int(image.shape[0]),
        "hwm_mib": _hwm_mib(),
    }


def _spawn(role, args, cgroup_dir):
    cmd = [
        sys.executable,
        "-m",
        "altaay_lab.software.pi_fit.workload",
        "--role",
        role,
        "--voice-dir",
        args.voice_dir,
        "--piper",
        args.piper,
        "--wav",
        args.wav,
    ]
    if role == "voice-staged":
        cmd.append("--wait-stdin")
    proc = subprocess.Popen(
        cmd, cwd=str(ROOT), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    if cgroup_dir:
        _move_pid(proc.pid, cgroup_dir)
    if role == "voice-staged":
        proc.stdin.write("\n")
        proc.stdin.flush()
    return proc


def _read_child(proc):
    out, err = proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(err.strip() or out.strip() or "child failed")
    return json.loads(out)


def run_stack(args):
    import numpy as np

    stop = threading.Event()
    rows = []
    sess, name, obs = _policy(args.policy, args.threads)
    walk_cpu = args.walk_cpu if args.spread else args.walk_cpu
    auto_cpu = args.auto_cpu if args.spread else args.walk_cpu
    walker = threading.Thread(target=_walk, args=(sess, name, obs, args.seconds, rows, stop, walk_cpu), daemon=True)
    auto = threading.Thread(target=_autonomy, args=(stop, auto_cpu), daemon=True)
    walker.start()
    # Let the policy settle before the other work starts.
    time.sleep(0.4)
    auto.start()
    samples = []
    stop_sample = threading.Event()

    def sample():
        while not stop_sample.is_set():
            samples.append(
                {
                    "t": round(time.perf_counter() - t0, 3),
                    "self_rss_mib": _rss_mib(),
                    "cgroup_mib": _cgroup_mib(args.mem_cgroup, "memory.current"),
                    "swap_mib": _cgroup_mib(args.mem_cgroup, "memory.swap.current"),
                }
            )
            time.sleep(0.2)

    t0 = time.perf_counter()
    sampler = threading.Thread(target=sample, daemon=True)
    sampler.start()
    voice_at = len(rows)
    camera_at = len(rows)
    voice = None
    camera = None
    try:
        if args.spread:
            voice_proc = _spawn("voice-staged", args, args.voice_cgroup)
            camera_proc = _spawn("camera", args, args.camera_cgroup)
            voice = _read_child(voice_proc)
            camera = _read_child(camera_proc)
        else:
            # Same core, same process. This is the stack as it is written today.
            def _cam_thread(box):
                box.append(run_camera())

            box = []
            cam = threading.Thread(target=_cam_thread, args=(box,))
            cam.start()
            voice = run_voice(args.voice_dir, args.piper, args.wav)
            cam.join()
            camera = box[0] if box else None
    finally:
        # Keep walking a little after the burst so the tail is in the log.
        time.sleep(0.4)
        stop.set()
        walker.join(timeout=2.0)
        auto.join(timeout=2.0)
        stop_sample.set()
        sampler.join(timeout=1.0)
    voice_end = len(rows)
    work = [item[0] for item in rows]
    period = [item[1] for item in rows]
    report = {
        "label": "measured in emulation",
        "role": "stack",
        "spread": bool(args.spread),
        "threads": int(args.threads),
        "piper": args.piper,
        "policy_input": int(obs.shape[0]),
        "policy_output": int(np.size(sess.run(None, {name: [obs]})[0])),
        "cycles": len(rows),
        "all": {"work": work_stats(work), "period_span_s": (max(period) - min(period)) if period else None},
        "during": slice_stats(work, period, voice_at, max(voice_at + 1, voice_end)),
        "voice": voice,
        "camera": camera,
        "self_hwm_mib": _hwm_mib(),
        "samples": samples,
        "camera_index": camera_at,
        "voice_index": voice_at,
    }
    # Drop the long per-cycle lists from the nested stats by keeping summaries only.
    # The chart uses samples plus the summary. Keep a short trace of work times
    # during the burst so the picture can show the deadline.
    report["during_work_s"] = [round(item, 6) for item in work[voice_at:voice_end]]
    report["during_period_s"] = [round(item, 6) for item in period[voice_at:voice_end]]
    return report


def run_walk(args):
    """Walk, autonomy, and one camera frame. No voice models.

    Used when the voice files are not in the tree. The label stays
    measured in emulation. It is not the full stack.
    """
    import numpy as np

    stop = threading.Event()
    rows = []
    sess, name, obs = _policy(args.policy, args.threads)
    walker = threading.Thread(
        target=_walk, args=(sess, name, obs, args.seconds, rows, stop, args.walk_cpu), daemon=True)
    auto = threading.Thread(target=_autonomy, args=(stop, args.auto_cpu), daemon=True)
    walker.start()
    time.sleep(0.2)
    auto.start()
    camera = run_camera()
    time.sleep(max(0.0, float(args.seconds) - 0.4))
    stop.set()
    walker.join(timeout=2.0)
    auto.join(timeout=2.0)
    work = [item[0] for item in rows]
    period = [item[1] for item in rows]
    return {
        "label": "measured in emulation",
        "role": "walk",
        "threads": int(args.threads),
        "policy_input": int(obs.shape[0]),
        "cycles": len(rows),
        "all": {"work": work_stats(work), "period": period_jitter_safe(period)},
        "work_s": [round(item, 6) for item in work],
        "period_s": [round(item, 6) for item in period],
        "camera": camera,
        "self_hwm_mib": _hwm_mib(),
        "voice": None,
    }


def period_jitter_safe(period):
    from altaay_lab.software.pi_fit.budget import period_jitter
    return period_jitter(period)


def stage_wake(voice_dir, wav_path):
    from altaay_lab.software.companion.audio_pcm import read_wav
    from altaay_lab.software.companion.pipeline import _frames
    from altaay_lab.software.companion.wake import OpenWakeWordEngine

    audio = read_wav(wav_path)
    before = _rss_mib()
    engine = OpenWakeWordEngine("hey_jarvis")
    engine.reset()
    best = 0.0
    hit = False
    for _start, frame in _frames(audio):
        score, _name = engine.feed(frame)
        if score > best:
            best = score
        if score >= 0.5:
            hit = True
    engine.close()
    return {
        "label": "measured in emulation",
        "stage": "wake",
        "woke": hit,
        "score": best,
        "rss_before_mib": before,
        "hwm_mib": _hwm_mib(),
    }


def stage_stt(voice_dir, wav_path):
    from altaay_lab.software.companion.audio_pcm import read_wav
    from altaay_lab.software.companion.stt import VoskSpeech

    audio = read_wav(wav_path)
    before = _rss_mib()
    engine = VoskSpeech(str(Path(voice_dir) / "vosk-model-small-en-us-0.15"))
    heard = engine.transcribe(audio)
    engine.close()
    return {
        "label": "measured in emulation",
        "stage": "stt",
        "heard": heard,
        "rss_before_mib": before,
        "hwm_mib": _hwm_mib(),
    }


def stage_tts(voice_dir, piper):
    from altaay_lab.software.companion.tts import PiperSpeech

    before = _rss_mib()
    engine = PiperSpeech(str(Path(voice_dir) / piper))
    audio, rate = engine.synthesize("Timer set for 5 minutes.")
    engine.close()
    return {
        "label": "measured in emulation",
        "stage": "tts",
        "samples": len(audio),
        "rate": rate,
        "rss_before_mib": before,
        "hwm_mib": _hwm_mib(),
    }


def run_voice_staged(voice_dir, piper, wav_path, wait_stdin):
    if wait_stdin:
        sys.stdin.readline()
    stages = []
    for role in ("stage-wake", "stage-stt", "stage-tts"):
        cmd = [
            sys.executable,
            "-m",
            "altaay_lab.software.pi_fit.workload",
            "--role",
            role,
            "--voice-dir",
            voice_dir,
            "--piper",
            piper,
            "--wav",
            wav_path,
        ]
        proc = subprocess.Popen(cmd, cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(err.strip() or out.strip() or role + " failed")
        stages.append(json.loads(out))
    return {
        "label": "measured in emulation",
        "staged": True,
        "woke": bool(stages[0].get("woke")),
        "heard": stages[1].get("heard", ""),
        "said": "Timer set for 5 minutes.",
        "stages": stages,
        "hwm_mib": _hwm_mib(),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Pi fit workload")
    parser.add_argument("--role", choices=("stack", "walk", "voice", "voice-staged", "stage-wake", "stage-stt", "stage-tts", "camera"), default="stack")
    parser.add_argument("--policy", default="")
    parser.add_argument("--voice-dir", default="")
    parser.add_argument("--piper", default="en_US-lessac-low.onnx")
    parser.add_argument("--wav", default="")
    parser.add_argument("--seconds", type=float, default=8.0)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--spread", action="store_true")
    parser.add_argument("--walk-cpu", type=int, default=0)
    parser.add_argument("--auto-cpu", type=int, default=0)
    parser.add_argument("--voice-cgroup", default="")
    parser.add_argument("--camera-cgroup", default="")
    parser.add_argument("--mem-cgroup", default="")
    parser.add_argument("--wait-stdin", action="store_true")
    parser.add_argument("--out", default="")
    args = parser.parse_args(argv)
    if args.role == "voice":
        report = run_voice(args.voice_dir, args.piper, args.wav)
    elif args.role == "voice-staged":
        report = run_voice_staged(args.voice_dir, args.piper, args.wav, args.wait_stdin)
    elif args.role == "stage-wake":
        report = stage_wake(args.voice_dir, args.wav)
    elif args.role == "stage-stt":
        report = stage_stt(args.voice_dir, args.wav)
    elif args.role == "stage-tts":
        report = stage_tts(args.voice_dir, args.piper)
    elif args.role == "camera":
        report = run_camera()
    else:
        if args.role == "walk":
            if not args.policy:
                raise SystemExit("walk needs --policy")
            report = run_walk(args)
        elif not args.policy or not args.wav or not args.voice_dir:
            raise SystemExit("stack needs --policy, --voice-dir, and --wav")
        else:
            report = run_stack(args)
    text = json.dumps(report)
    summary = {
        "label": "measured in emulation",
        "spread": report.get("spread"),
        "cycles": report.get("cycles"),
        "during_work": (report.get("during") or {}).get("work"),
        "during_period": (report.get("during") or {}).get("period"),
        "voice_hwm_mib": (report.get("voice") or {}).get("hwm_mib") if isinstance(report.get("voice"), dict) else None,
        "camera": report.get("camera"),
        "self_hwm_mib": report.get("self_hwm_mib"),
    }
    print("FITSUM " + json.dumps(summary), file=sys.stderr, flush=True)
    if args.out:
        try:
            Path(args.out).write_text(text + "\n", encoding="utf-8")
        except OSError as exc:
            print("FITWRITE " + str(exc), flush=True)
            raise
    print(text)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        raise SystemExit(0)
