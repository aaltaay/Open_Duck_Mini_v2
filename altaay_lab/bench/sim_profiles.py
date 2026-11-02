#!/usr/bin/env python3
"""Make servo voltage sag profiles from the lab power path sim (sim pass only).

The battery guard tests need per-servo Present Voltage traces, not only the summary
numbers in sim/POWER_PATH_SIM.md. This script reuses the lab ngspice model as it is
(build() from sim/power_path_sim.py, star topology = D15 wiring) on the MuJoCo walk
trace from sim/current_budget.py, and keeps every servo voltage over time.

Two outputs, both small CSV files (well under 1 MB):
  sim_star_<case>.csv      6 s windows at 50 Hz: one row per sample, one column per servo ID.
  sim_star_discharge.csv   the same 6 s walk window run at falling cell voltages
                           (4.0 V down to 3.20 V per cell), joined end to end. The time
                           axis between steps is artificial (6 s per step); the guard
                           logic counts samples, so this only shortens the test.

Usage (traces from sim/current_budget.py with ODM_SAVE_TRACES=1, in a scratch folder):
  ODM_SAVE_TRACES=1 ODM_OUT=$SCRATCH/simtraces MUJOCO_GL=disable \
      python3 altaay_lab/sim/current_budget.py walk_backlash
  python3 altaay_lab/bench/sim_profiles.py --traces $SCRATCH/simtraces \
      --out altaay_lab/bench/tests/data
Needs ngspice on PATH and numpy. Read-only for everything outside --out.
"""
import argparse
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
SIM_SCRIPT = os.path.join(LAB, "sim", "power_path_sim.py")

# Same window and corners as sim/power_path_sim.py __main__ (walk, backlash model, 10 to 16 s).
WINDOW = (10.0, 16.0)
TYPICAL = dict(R_contact=0.005, kit_awg=24, R_cell=0.015, R_holder=0.010, R_adapter=0.005)
CASES = {
    "full_typical": (4.2, TYPICAL),
    "nominal_typical": (3.7, TYPICAL),
    "nominal_highside": (3.7, {}),
    "low_typical": (3.3, TYPICAL),
}
DISCHARGE_CELL_V = [4.0, 3.9, 3.8, 3.7, 3.6, 3.55, 3.5, 3.45, 3.4, 3.35, 3.3, 3.25, 3.2]
RATE_HZ = 50.0

# Servo ID for each joint name: Runtime HWI map (rustypot_position_hwi.py lines 14 to 31 at 376de65).
JOINT_ID = {
    "left_hip_yaw": 20, "left_hip_roll": 21, "left_hip_pitch": 22, "left_knee": 23, "left_ankle": 24,
    "neck_pitch": 30, "head_pitch": 31, "head_yaw": 32, "head_roll": 33,
    "right_hip_yaw": 10, "right_hip_roll": 11, "right_hip_pitch": 12, "right_knee": 13, "right_ankle": 14,
}


def load_sim_module(traces_dir):
    os.environ["ODM_TRACES"] = traces_dir
    os.environ.setdefault("ODM_OUT", tempfile.mkdtemp(prefix="odm_power_sim_"))
    spec = importlib.util.spec_from_file_location("lab_power_path_sim", SIM_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True
    spec.loader.exec_module(mod)
    return mod


def run_traces(mod, npz, vcell, over):
    """Same steps as power_path_sim.run_case, but returns the voltage traces."""
    pw, dt = mod.servo_power(npz, *WINDOW)
    over = dict(over); over["topology"] = "star"
    cir, probes, nodes, _ = mod.build(pw, dt, vcell, mod.P["I_q"], over)
    with tempfile.TemporaryDirectory() as td:
        f = os.path.join(td, "c.cir"); outf = os.path.join(td, "o.txt")
        with open(f, "w") as fh:
            fh.write(cir.replace("{OUTFILE}", outf))
        r = subprocess.run(["ngspice", "-b", f], capture_output=True, text=True, timeout=1800)
        if not os.path.exists(outf):
            raise RuntimeError(r.stdout[-2000:] + r.stderr[-2000:])
        A = np.loadtxt(outf)
    tt = A[:, 0]; cols = A[:, 1::2]
    res = {pr: cols[:, i] for i, pr in enumerate(probes)}
    grid = np.arange(0.0, tt[-1] - tt[0], 1.0 / RATE_HZ)
    out = {}
    for name, (a, b) in nodes.items():
        out[JOINT_ID[name]] = np.interp(grid + tt[0], tt, res[f"v({a},{b})"])
    bus = np.interp(grid + tt[0], tt, res["v(bus,busn)"])
    return grid, out, bus


def write_csv(path, t, traces, extra=None, header_note=""):
    ids = sorted(traces)
    cols = ["t_s"] + (list(extra.keys()) if extra else []) + [f"v_{i}" for i in ids]
    with open(path, "w") as fh:
        fh.write(f"# {header_note}\n")
        fh.write(",".join(cols) + "\n")
        for k in range(len(t)):
            row = [f"{t[k]:.3f}"]
            if extra:
                row += [f"{extra[c][k]:.3f}" if isinstance(extra[c][k], float) else str(extra[c][k]) for c in extra]
            row += [f"{traces[i][k]:.3f}" for i in ids]
            fh.write(",".join(row) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--traces", required=True, help="folder with trace_walk_backlash.npz (scratch)")
    ap.add_argument("--out", default=os.path.join(HERE, "tests", "data"))
    ap.add_argument("--skip-discharge", action="store_true")
    a = ap.parse_args(argv)
    npz = os.path.join(a.traces, "trace_walk_backlash.npz")
    if not os.path.exists(npz):
        sys.exit(f"missing {npz}: run sim/current_budget.py with ODM_SAVE_TRACES=1 first")
    mod = load_sim_module(a.traces)
    os.makedirs(a.out, exist_ok=True)
    summary = {}
    for case, (vc, over) in CASES.items():
        t0 = time.time()
        t, tr, bus = run_traces(mod, npz, vc, over)
        note = (f"sim pass only. sim/power_path_sim.py build(), topology star (D15), walk backlash "
                f"{WINDOW[0]}-{WINDOW[1]} s, cell OCV {vc} V, corner {'typical' if over else 'high-side'}; "
                f"servo terminal voltage in V at {RATE_HZ:g} Hz")
        write_csv(os.path.join(a.out, f"sim_star_{case}.csv"), t, tr, {"bus_v": bus}, note)
        ank = np.minimum(tr[24], tr[14])
        summary[case] = dict(cell_ocv=vc, worst_min=round(float(min(v.min() for v in tr.values())), 3),
                             ankle_min=round(float(ank.min()), 3),
                             left_ankle_frac_below_6=round(float((tr[24] < 6.0).mean()), 3),
                             right_ankle_frac_below_6=round(float((tr[14] < 6.0).mean()), 3),
                             median_of_servos_mean=round(float(np.median(np.vstack(list(tr.values())), axis=0).mean()), 3),
                             bus_mean=round(float(bus.mean()), 3), seconds=round(time.time() - t0, 1))
        print(case, json.dumps(summary[case]))
    if not a.skip_discharge:
        T, TR, CELL = [], {i: [] for i in JOINT_ID.values()}, []
        offset = 0.0
        for vc in DISCHARGE_CELL_V:
            over = TYPICAL
            t, tr, _ = run_traces(mod, npz, vc, over)
            T.append(t + offset); offset = T[-1][-1] + 1.0 / RATE_HZ
            for i in TR: TR[i].append(tr[i])
            CELL.append(np.full(len(t), vc))
            med = float(np.median(np.vstack(list(tr.values())), axis=0).mean())
            print(f"discharge step cell {vc:.2f} V: median-of-servos mean {med:.3f} V")
        T = np.concatenate(T); TR = {i: np.concatenate(v) for i, v in TR.items()}
        cell = np.concatenate(CELL)
        write_csv(os.path.join(a.out, "sim_star_discharge.csv"), T, TR, {"cell_ocv_v": cell},
                  "sim pass only. Same model, typical corner, star topology; 6 s walk window per cell OCV step "
                  f"{DISCHARGE_CELL_V}; time between steps is artificial")
    with open(os.path.join(a.out, "sim_profiles_summary.json"), "w") as fh:
        json.dump(dict(source="altaay_lab/bench/sim_profiles.py on sim/power_path_sim.py build()", sim_pass_only=True,
                       window_s=WINDOW, rate_hz=RATE_HZ, cases=summary), fh, indent=1)


if __name__ == "__main__":
    main()
