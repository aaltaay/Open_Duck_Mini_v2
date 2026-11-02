"""Test harness: real Runtime code, real rustypot and pypot, simulated hardware.

Run (from the repo root, with a Python that has the Runtime's pinned packages, for example the
scratch venv built from Runtime setup.cfg; software/SOFTWARE.md section 7):
  ODM_RUNTIME_DIR=/home/user/upstream/Open_Duck_Mini_Runtime \
      <venv>/bin/python -m pytest altaay_lab/bench/tests -q
Bench scripts run as subprocesses with:
  LD_PRELOAD   tests/pty_shim.c, built here with gcc (rustypot's serialport sets DTR on open)
  PYTHONPATH   tests/fake_hw (Blinka board/digitalio/busio/pwmio stand-ins, byte-level BNO055)
The fake servo bus (tests/fake_sts3215.py) runs inside the pytest process on a pty.
Nothing is written into the Runtime checkout (no .pyc); logs go to pytest tmp folders.
"""
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.dont_write_bytecode = True
TESTS = Path(__file__).resolve().parent
BENCH = TESTS.parent
LAB = BENCH.parent
REPO = LAB.parent
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(BENCH))

RUNTIME = Path(os.environ.get("ODM_RUNTIME_DIR", "/home/user/upstream/Open_Duck_Mini_Runtime"))
ONNX = REPO / "BEST_WALK_ONNX_2.onnx"
DATA = TESTS / "data"
PY = os.environ.get("ODM_TEST_PYTHON", sys.executable)
IDS = [20, 21, 22, 23, 24, 30, 31, 32, 33, 10, 11, 12, 13, 14]


def _has(mod):
    r = subprocess.run([PY, "-c", f"import {mod}"], capture_output=True)
    return r.returncode == 0


HAS_RUSTYPOT = _has("rustypot")
HAS_PYPOT = _has("pypot.feetech")
HAS_ORT = _has("onnxruntime")
needs_libs = pytest.mark.skipif(not (HAS_RUSTYPOT and HAS_PYPOT), reason="rustypot 0.1.0 and pypot not installed")
needs_walk = pytest.mark.skipif(not (HAS_RUSTYPOT and HAS_PYPOT and HAS_ORT and ONNX.exists() and RUNTIME.exists()),
                                reason="walk needs rustypot, pypot, onnxruntime, the policy and the Runtime")
needs_runtime = pytest.mark.skipif(not RUNTIME.exists(), reason="Runtime checkout not found")


@pytest.fixture(scope="session")
def shim(tmp_path_factory):
    gcc = shutil.which("gcc")
    if not gcc:
        pytest.skip("gcc not available to build tests/pty_shim.c")
    out = tmp_path_factory.mktemp("shim") / "pty_shim.so"
    subprocess.run([gcc, "-shared", "-fPIC", "-O2", "-o", str(out), str(TESTS / "pty_shim.c"), "-ldl"], check=True)
    return str(out)


@pytest.fixture
def make_bus():
    from fake_sts3215 import FakeBus, FakeServo
    made = []

    def _make(ids=IDS, wire_time=False, **servo_kw):
        bus = FakeBus([FakeServo(i, **servo_kw) for i in ids], wire_time=wire_time)
        made.append(bus)
        return bus
    yield _make
    for b in made:
        b.stop()


@pytest.fixture
def duck_config(tmp_path):
    p = tmp_path / "duck_config.json"
    shutil.copy(LAB / "software" / "duck_config.altaay.json", p)
    return str(p)


@pytest.fixture
def run(shim, tmp_path):
    """Run a bench script; returns (CompletedProcess, out_dir)."""
    def _run(script, *args, env=None, timeout=180):
        e = dict(os.environ)
        e.update(LD_PRELOAD=shim, PYTHONPATH=str(TESTS / "fake_hw"), PYTHONDONTWRITEBYTECODE="1",
                 ODM_RUNTIME_DIR=str(RUNTIME), PYGAME_HIDE_SUPPORT_PROMPT="1", ODM_BENCH_OUT=str(tmp_path / "out"))
        e.setdefault("ODM_PYPOT_TIMEOUT", "0.5")       # shared test machine; pypot default is 0.05 s
        e.setdefault("ODM_FAKE_FEET", "11")
        e.setdefault("ODM_FAKE_IMU", "{}")
        if env:
            e.update(env)
        cmd = [PY, str(BENCH / script)] + [str(a) for a in args]
        t0 = time.time()
        r = subprocess.run(cmd, capture_output=True, text=True, env=e, timeout=timeout)
        r.seconds = time.time() - t0
        return r, tmp_path / "out"
    return _run


def last_report(out_dir, sub):
    import json
    files = sorted((Path(out_dir) / sub).glob("*.json"))
    assert files, f"no report in {out_dir}/{sub}"
    return json.load(open(files[-1]))


def item(rep, name):
    for i in rep["items"]:
        if i["item"] == name:
            return i
    raise KeyError(f"{name} not in {[i['item'] for i in rep['items']]}")
