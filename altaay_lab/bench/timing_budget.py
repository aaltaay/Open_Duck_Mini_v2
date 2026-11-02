#!/usr/bin/env python3
"""Bus timing budget of the 50 Hz walk loop, with and without the lab's extra reads.

Packet sizes (Feetech protocol as rustypot c8b8223 src/protocol/feetech.rs builds them):
  instruction FF FF ID LEN INST PARAMS CHK  = 6 + params bytes
  status      FF FF ID LEN ERR  DATA   CHK  = 6 + data bytes
  SYNC READ  of L bytes from n servos: request 8 + n, replies n x (6 + L)
  SYNC WRITE of L bytes to n servos:   8 + n x (1 + L), no reply
Wire time: 1 Mbaud 8N1 = 10 bits per byte = 10 us per byte (rustypot_position_hwi.py line 77).
Each read also waits for the USB round trip (CH343 full-speed through cdc-acm); that time is not
published: the table shows 0, 1 and 2 ms per read transaction (UNVERIFIED, measure on the Pi with
walk_with_guard.py / power_log.py, which report loop and read times). CPU time of the policy and
of Python on a Pi Zero 2 W is UNVERIFIED too.
The walking log (power_log.py --walk) reads on its own timer only in the idle part of each cycle
(odm_bench/vsampler.py): its read adds nothing to the control part; it needs an idle window of
its own read time plus a 2 ms margin, and the share of the walk it can sample is what is left.
The old log (--sampler cycle) read inside every cycle, before the Runtime's reads.

  python3 altaay_lab/bench/timing_budget.py              # analytic table (markdown)
  python3 altaay_lab/bench/timing_budget.py --measure --python <venv python> --scratch <dir>
        runs the real walk loop on the wire-timed simulated bus (x86, a lower bound for the Pi)
"""
import argparse
import os
import subprocess
import sys
import time

BYTE_US = 10.0
N = 14
SLOT_MS = 27.0       # power_log.py --sample-period-ms default
MARGIN_MS = 2.0      # power_log.py --sample-margin-ms default


def sync_read(n, length):
    return 8 + n, n * (6 + length)


def sync_write(n, length):
    return 8 + n * (1 + length)


def table(turnarounds=(0.0, 1.0, 2.0)):
    pos_req, pos_rep = sync_read(N, 2)
    vel_req, vel_rep = sync_read(N, 2)
    goal = sync_write(N, 2)
    runtime_bytes = pos_req + pos_rep + vel_req + vel_rep + goal
    rows = [("Runtime walk loop per cycle (rustypot): sync read 56 (position) + sync read 58 (velocity) + "
             "sync write 42 (goal), 14 servos", runtime_bytes, 2, "rustypot_position_hwi.py lines 119-165")]
    g7 = sum(sync_read(7, 2))
    g14 = sum(sync_read(N, 2))
    v14 = sum(sync_read(N, 1))
    blk = sum(sync_read(N, 9))
    vi = sum(sync_read(N, 1)) + sum(sync_read(N, 2))
    rows += [
        ("guard tick, staggered: sync read 62..63 (V, T) of 7 servos, every 0.25 s (12.5 cycles)", g7, 1,
         "odm_bench/sampler.py"),
        ("guard, all 14 at once: sync read 62..63", g14, 1, "start check"),
        ("voltage only, 14 servos: sync read 62 (check_voltage.py)", v14, 1, "check_voltage.py line 29"),
        ("old power log, inside every cycle: sync read 62..70 (V, T, status, I) of 14", blk, 1,
         "power_log.py --sampler cycle"),
        ("timer power log, idle part only: the same read, one per 27 ms slot when it fits", blk, 1,
         "power_log.py --walk (default)"),
        ("power log as two reads: 62 (V) and 69..70 (I)", vi, 2, "alternative"),
    ]
    out = ["| Transaction | Bytes | Wire ms | Reads | + USB 0 ms | + USB 1 ms | + USB 2 ms | Source |",
           "|---|---|---|---|---|---|---|---|"]
    for what, b, nreads, src in rows:
        wire = b * BYTE_US / 1000
        cols = [f"{wire + nreads * u:.2f}" for u in turnarounds]
        out.append(f"| {what} | {b} | {wire:.2f} | {nreads} | " + " | ".join(cols) + f" | {src} |")
    base = runtime_bytes * BYTE_US / 1000
    out.append("")
    out.append("Per 20 ms cycle (bus only, CPU not included):")
    for u in turnarounds:
        rt = base + 2 * u
        gw = rt + g7 * BYTE_US / 1000 + u
        ga = rt + (g7 * BYTE_US / 1000 + u) / 12.5
        pw = rt + blk * BYTE_US / 1000 + u
        tr = blk * BYTE_US / 1000 + u
        out.append(f"- USB {u:g} ms per read: Runtime {rt:.2f} ms; + guard tick in its cycle {gw:.2f} ms "
                   f"(average {ga:.2f} ms); + old power log every cycle {pw:.2f} ms; left for CPU: "
                   f"{20 - rt:.1f} / {20 - gw:.1f} / {20 - pw:.1f} ms. Timer log: control part stays "
                   f"{rt:.2f} ms; each timer read {tr:.2f} ms in the idle part, needs {tr + MARGIN_MS:.2f} ms "
                   f"free (read + {MARGIN_MS:g} ms margin), so it fits while Runtime CPU <= {20 - rt - tr - MARGIN_MS:.1f} ms; "
                   f"bus busy {100 * (rt + tr * 20 / SLOT_MS) / 20:.0f} % of the time at most (every slot read)")
    return "\n".join(out), dict(runtime=runtime_bytes, guard7=g7, guard14=g14, volt14=v14, block=blk, vi=vi)


def measure(py, scratch, seconds=12):
    """Real walk loop (Runtime RLWalk, rustypot, ONNX policy) on the wire-timed fake bus."""
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(here, "tests"))
    sys.dont_write_bytecode = True
    from fake_sts3215 import FakeBus, FakeServo  # noqa: E402
    import json
    import shutil
    os.makedirs(scratch, exist_ok=True)
    shim = os.path.join(scratch, "pty_shim.so")
    subprocess.run(["gcc", "-shared", "-fPIC", "-O2", "-o", shim, os.path.join(here, "tests", "pty_shim.c"), "-ldl"],
                   check=True)
    cfg = os.path.join(scratch, "duck_config.json")
    shutil.copy(os.path.join(os.path.dirname(here), "software", "duck_config.altaay.json"), cfg)
    onnx = os.path.join(os.path.dirname(os.path.dirname(here)), "BEST_WALK_ONNX_2.onnx")
    ids = [20, 21, 22, 23, 24, 30, 31, 32, 33, 10, 11, 12, 13, 14]
    runs = {"baseline (guard reads once)": ("walk_with_guard.py", ["--period", "1000000"]),
            "with the staggered guard": ("walk_with_guard.py", []),
            "with the old power log every cycle": ("power_log.py", ["--walk", "--no-guard", "--pack", "full",
                                                                    "--sampler", "cycle", "--seconds", str(seconds)]),
            "with the timer power log": ("power_log.py", ["--walk", "--no-guard", "--pack", "full",
                                                          "--seconds", str(seconds)])}
    res = {}
    for name, (script, extra) in runs.items():
        bus = FakeBus([FakeServo(i, reg85=0, volts=7.2) for i in ids], wire_time=True)
        bus.log_on = False
        out = os.path.join(scratch, "timing", "_".join(name.split()[:4]).replace("(", ""))
        env = dict(os.environ, LD_PRELOAD=shim, PYTHONPATH=os.path.join(here, "tests", "fake_hw"),
                   PYTHONDONTWRITEBYTECODE="1", PYGAME_HIDE_SUPPORT_PROMPT="1", ODM_FAKE_FEET="11",
                   ODM_FAKE_IMU="{}", ODM_BENCH_OUT=out)
        args = [py, os.path.join(here, script)] + extra + ["--onnx_model_path", onnx, "--duck_config_path", cfg,
                                                           "--serial_port", bus.path, "--no-commands"]
        if script == "walk_with_guard.py":
            args += ["--max-seconds", str(seconds), "--dry-run"]
        subprocess.run(args, env=env, capture_output=True, text=True, timeout=300)
        bus.stop()
        sub = "walk_guard" if script == "walk_with_guard.py" else "power_log"
        reps = sorted(os.listdir(os.path.join(out, sub)))
        rep = json.load(open(os.path.join(out, sub, [r for r in reps if r.endswith(".json")][-1])))
        loop = rep["data"].get("loop", {})
        rms = [i["measured"] for i in rep["items"] if i["item"] in ("11.read_ms", "9.read_ms")]
        res[name] = dict(loop=loop, read_ms=rms[0] if rms else None)
        smp = rep["data"].get("sampler")
        if smp:
            res[name]["sampler"] = {k: smp.get(k) for k in ("coverage", "read", "busy", "own", "room", "overruns",
                                                             "overrun_max_ms", "read_ms_mean", "read_ms_p99")}
        time.sleep(0.5)
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--measure", action="store_true")
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--scratch", default=os.environ.get("ODM_SCRATCH"))
    ap.add_argument("--seconds", type=float, default=12)
    a = ap.parse_args(argv)
    txt, _ = table()
    print(txt)
    if a.measure:
        if not a.scratch:
            ap.error("--measure needs --scratch or ODM_SCRATCH")
        print("\nMeasured on this machine, wire-timed simulated bus (no USB latency):")
        for k, v in measure(a.python, a.scratch, a.seconds).items():
            print(f"- {k}: {v}")


if __name__ == "__main__":
    sys.exit(main())
