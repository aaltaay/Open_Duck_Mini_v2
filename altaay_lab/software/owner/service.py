"""Long-running roles for systemd: walk, supervisor, voice, perception.

Each role answers the watchdog. A low-pack request file makes the process
exit 0 so systemd does not treat the stop as a crash.

The walk child is the existing guarded walk. Intentional guard exits do not
come back as failures. This file does not edit antennas.py. The ear PWM
overlay stays the environment variable the unit already sets.
"""

from __future__ import annotations

import os
import signal
import subprocess

from . import store, watchdog

ROLES = ("walk", "supervisor", "voice", "perception")
# Cited by walk_with_guard.py: these exits are a decision, not a crash.
INTENTIONAL_WALK_EXITS = frozenset({0, 4, 6, 7, 8, 9, 10, 11})
PING_S = 5


def shutdown_requested(state):
    return os.path.isfile(store.path(state, store.SHUTDOWN_REQUEST))


def heartbeat(state, role):
    store.write_json(store.path(state, "heartbeat-%s.json" % role), {
        "privacy": "The camera and the microphone stay on the duck. Frames and audio are not uploaded.",
        "role": role,
    }, 0o644)


def child_exit_code(code):
    if code in INTENTIONAL_WALK_EXITS:
        return 0
    return int(code)


def walk_argv(home):
    py = os.path.join(home, ".virtualenvs", "open-duck-mini-runtime", "bin", "python")
    script = os.path.join(home, "open_duck_mini_v2", "altaay_lab", "bench", "walk_with_guard.py")
    return [
        py,
        script,
        "--onnx_model_path", os.path.join(home, "BEST_WALK_ONNX_2.onnx"),
        "--duck_config_path", os.path.join(home, "duck_config.json"),
        "--knee-heat",
    ]


def install_stop(stop):
    def handle(signum, frame):
        del signum, frame
        stop.set()
    signal.signal(signal.SIGTERM, handle)
    signal.signal(signal.SIGINT, handle)


def serve(role, state, stop, interval=PING_S):
    if role not in ROLES:
        raise ValueError("unknown role")
    store.ensure(state)
    watchdog.notify("READY=1")
    while not stop.is_set():
        if shutdown_requested(state):
            watchdog.notify("STOPPING=1")
            return 0
        heartbeat(state, role)
        watchdog.notify("WATCHDOG=1")
        if stop.wait(interval):
            break
    return 0


def serve_walk(state, home, stop, popen=None, interval=PING_S):
    store.ensure(state)
    watchdog.notify("READY=1")
    argv = walk_argv(home)
    if not os.path.isfile(argv[0]) or not os.path.isfile(argv[1]):
        return 1
    cwd = os.path.join(home, "Open_Duck_Mini_Runtime", "scripts")
    if not os.path.isdir(cwd):
        return 1
    spawn = popen or subprocess.Popen
    child = spawn(argv, cwd=cwd)
    while not stop.is_set():
        if shutdown_requested(state):
            child.terminate()
            child.wait(timeout=15)
            return 0
        watchdog.notify("WATCHDOG=1")
        code = child.poll()
        if code is not None:
            return child_exit_code(code)
        if stop.wait(interval):
            break
    child.terminate()
    try:
        child.wait(timeout=15)
    except subprocess.TimeoutExpired:
        child.kill()
    return 0
