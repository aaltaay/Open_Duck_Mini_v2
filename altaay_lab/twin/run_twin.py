#!/usr/bin/env python3
"""One digital twin. One command. CPU only.

  python3 -m altaay_lab.twin.run_twin
  python3 -m altaay_lab.twin.run_twin --short
  make twin

Every physical number is loaded from altaay_lab/twin/parts.yaml, which is
derived from the netlist, the limits file, and the order. The walk is the
run C policy in MuJoCo. The pack uses the existing power network and the
battery guard's pack floor. Heat uses the existing thermal twin, one step
per 0.1 s current bin. The nest sim is the existing one. Camera docking is
not in that sim, so the dock line is BLOCKER.

Nothing is bought. No paid GPU.
"""
import argparse
import math
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, ".."))
ROOT = os.path.abspath(os.path.join(LAB, ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from altaay_lab.twin import parts_truth as PT  # noqa: E402


def _no_dash(text):
    if "\u2014" in text or "\u2013" in text:
        raise SystemExit("report contains a dash that is not a hyphen")
    return text


def ts_fraction(rn, parts):
    """Same split as circuitry/check_bq24133.py: bias, parallel resistor, bead."""
    n = parts["ntc"]
    r1 = float(n["bias_ohm"])
    rpar = float(n["parallel_ohm"])
    if rn is None:
        rp = rpar
    else:
        rp = 1.0 / (1.0 / rpar + 1.0 / float(rn))
    return rp / (r1 + rp)


def bead_ohm(temp_c, parts):
    """10 kOhm at 25 C and the beta named on the netlist bead."""
    n = parts["ntc"]
    t = float(temp_c) + 273.15
    return float(n["r_25_ohm"]) * math.exp(float(n["beta"]) * (1.0 / t - 1.0 / 298.15))


def ntc_allows(temp_c, parts):
    frac = ts_fraction(bead_ohm(temp_c, parts), parts)
    cold = float(parts["ntc"]["stop_cold_frac"])
    hot = float(parts["ntc"]["stop_hot_frac"])
    return hot < frac < cold, frac


def bin_width(tbin):
    import numpy as np
    d = np.diff(np.asarray(tbin, float))
    d = d[np.isfinite(d) & (d > 1e-9)]
    if len(d) == 0:
        raise RuntimeError("current bins have no spacing")
    width = round(float(np.median(d)), 6)
    if float(np.max(np.abs(d - width))) > 1e-4:
        raise RuntimeError("current bins are not uniform")
    return width


def sched_every_bin(nbin, width):
    """One thermal step reads the next current bin. Same rule as runc_joint_current.py."""
    def sched(t, nbin=nbin, width=width):
        return int(math.floor(float(t) / width + 1e-9)) % nbin

    seen = [sched(i * width) for i in range(nbin)]
    if seen != list(range(nbin)):
        raise RuntimeError("thermal schedule skipped a current bin")
    return sched


def home_command():
    """Four legs and four turns. A fixed forward command drifts into a curve."""
    leg, turn = 6.0, 2.2
    cycle = 4.0 * (leg + turn)

    def command(t, data, infer):
        if t < 2.0:
            return [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        u = (t - 2.0) % cycle
        for _ in range(4):
            if u < leg:
                return [0.20, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
            u -= leg
            if u < turn:
                return [0.0, 0.0, 0.7, 0.0, 0.0, 0.0, 0.0]
            u -= turn
        return [0.20, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    return command


def walk(parts, seconds, scratch):
    import numpy as np
    os.environ["TWIN_EM_SCRATCH"] = scratch
    os.environ["ODM_SCRATCH"] = os.path.join(scratch, "models")
    os.environ["ODM_OUT"] = os.path.join(scratch, "cb_out")
    pg = os.environ.get("ODM_PLAYGROUND")
    if not pg:
        raise SystemExit("Set ODM_PLAYGROUND to an Open_Duck_Playground checkout at b9be205")
    os.environ["ODM_ONNX"] = os.path.join(LAB, "problems", "retrain_sts12", "sts12_runC_policy.onnx")
    sys.path.insert(0, os.path.join(LAB, "problems"))
    sys.path.insert(0, os.path.join(LAB, "twin", "electromech"))
    sys.path.insert(0, os.path.join(LAB, "twin", "thermal"))
    import sts12  # noqa: F401  registers the 3S pack and the 12 V sheet
    import em_twin as ET
    import knee_heat_chafe as KH
    import twin_thermal as TT

    c = dict(TT.CORNERS["central"])
    heat = TT.HeatWalk(c, 25.0, 0.1)
    stop_c = float(parts["rest"]["stop_c"])
    resume_c = float(parts["rest"]["resume_c"])
    eta = float(parts["regulator"]["eff_used"])
    knee = TT.NAMES.index("right_knee")
    trace = []

    def on_bin(info):
        im = np.asarray(info["im"], float)
        i2 = im * im
        vbar = float(np.mean(info["v"]))
        walking = info["phase"] == "walk"
        p_idle = 0.021 * max(vbar, 0.5)
        servo = dict(
            P_cu25=i2 * KH.R_W_12,
            P_board=i2 * KH.R_BOARD_12,
            P_fric=np.zeros(14),
            P_idle=np.full(14, p_idle),
        )
        i_pack = float(info["i_pack"])
        i2p = i_pack * i_pack
        p_out = float(info["v_bec"]) * float(info["i_bec"])
        trunk = dict(
            cells=3.0 * i2p * 0.015, holder=i2p * c["R_holder"], bms=i2p * c["R_bms"],
            fuse=i2p * TT.PARAMS["R_fuse"], xt30=i2p * TT.PARAMS["R_xt30"],
            switch=i2p * TT.sw_R_on(vbar, c), wires=i2p * TT.PARAMS["R_wires"],
            bec=max(p_out, 0.0) * (1.0 / eta - 1.0), bec_leads=0.0, logic=0.15,
        )
        Ts = heat.step(dict(servo=servo, trunk=trunk, head=c["P5V"]), walking)
        hot = float(np.max(Ts))
        trace.append((float(info["t"]), hot, float(Ts[knee]), float(heat.T_c), info["phase"], int(np.argmax(Ts))))
        if info["phase"] == "walk" and hot >= stop_c:
            return "rest"
        if info["phase"] in ("hold", "off", "stand") and hot <= resume_c:
            return "walk"
        return None

    extra = dict(
        BEC_V=float(parts["regulator"]["v_set"]),
        BEC_EFF=eta,
        BEC_HOLD=1 if parts["regulator"]["holds"] else 0,
    )
    r = ET.run(
        mass="ours", walk="backlash", cmd=(0.20, 0.0, 0.0), dur=float(seconds),
        supply="net", corner="typical", extra=extra,
        cell="p45b3", q0=0.0, servo_mode="sheet", guard="act",
        keep_full=False, bin_s=0.1, stop_on_fall=False, t_stats=0.0,
        label="one twin", progress=30.0,
        command_fn=home_command(), on_bin=on_bin, pack_floor=True,
    )
    r["_heat_trace"] = trace
    r["_heat"] = heat
    return r, np


def heat_of(result, np):
    """Temperatures stepped inside the walk, one 0.1 s bin at a time."""
    trace = result.get("_heat_trace") or []
    if len(trace) < 2:
        raise RuntimeError("the walk did not record a heat step")
    width = bin_width([row[0] for row in trace])
    if abs(width - 0.1) > 1e-3:
        raise RuntimeError("thermal step is %.4f s, not 0.1 s" % width)
    t = np.array([row[0] for row in trace], float)
    hot_c = np.array([row[1] for row in trace], float)
    knee = np.array([row[2] for row in trace], float)
    cell = np.array([row[3] for row in trace], float)
    phase = [row[4] for row in trace]
    which = np.array([row[5] for row in trace], int)
    import twin_thermal as TT
    hot_i = int(which[int(np.argmax(hot_c))])
    walk_n = sum(1 for p in phase if p == "walk")
    return dict(
        t=t, knee=knee, hot_c_series=hot_c, cell=cell, phase=phase,
        hot_name=TT.NAMES[hot_i], hot_c=float(np.max(hot_c)),
        knee_c=float(np.max(knee)), cell_c=float(np.max(cell)),
        walk_share=walk_n / max(len(phase), 1), width=width, nbin=len(trace),
    )


def distance_of(result, np):
    log = np.asarray(result.get("_log"), float) if result.get("_log") is not None else np.zeros((0, 2))
    if len(log) < 2:
        return 0.0, 0.0
    x, y = log[:, 1], log[:, 2]
    step = np.hypot(np.diff(x), np.diff(y))
    path = float(step.sum())
    net = float(np.hypot(x[-1] - x[0], y[-1] - y[0]))
    return path, net


def charge_of(parts, result, cell_c):
    q = float(result["q_end_mAh"])
    i_chg = float(parts["charger"]["i_charge_a"])
    hours = q / (i_chg * 1000.0) if i_chg > 0 else None
    allows, frac = ntc_allows(cell_c, parts)
    return dict(q_mAh=q, hours=hours, allows=allows, frac=frac, cell_c=cell_c)


def _public_error(exc):
    msg = " ".join(str(exc).split())
    msg = re.sub(r"/[^\s'\"]+", "[path]", msg)
    return msg[:240]


def dock_once():
    """One existing nest run. Perception in that file is a pose stand-in."""
    note = (
        "BLOCKER. The nest sim does not use a camera. It drives on the true pose plus noise. "
        "A seat in that sim is not a dock."
    )
    try:
        scratch = os.environ.get("NEST_SCRATCH") or os.path.join(tempfile.gettempdir(), "nestsim")
        sit_dir = os.path.join(scratch, "model", "sit")
        if not os.path.exists(os.path.join(sit_dir, "sit_model.json")):
            sys.path.insert(0, os.path.join(LAB, "twin", "sit"))
            import sit_model as SM
            SM.write(os.path.join(scratch, "model"), "sit")
        sim_dir = os.path.join(LAB, "twin", "dock", "nest", "sim")
        sys.path.insert(0, sim_dir)
        import current_budget as CB
        CB.ONNX = os.path.join(LAB, "problems", "retrain_sts12", "sts12_runC_policy.onnx")
        import nest_run as NR
        # Rail is 12 V. The turn-offset table has rows only at 6.0 and 7.2 V, so the
        # aim offset stays on the 7.2 V row instead of being extrapolated.
        run = NR.Run(dict(seed=0, volt=12.0, noise="mid", mu=0.8, pins=False))
        run.shift = NR.interp(NR.SHIFT, 7.2)
        run.coast = float(NR.interp(NR.COAST, 7.2))
        run.go()
        sits = run.out.get("sits") or []
        first = sits[0] if sits else {}
        seated = bool(first.get("nest", {}).get("ok")) if isinstance(first.get("nest"), dict) else False
        return dict(
            ran=True,
            camera="BLOCKER",
            note=note,
            seated_mechanical=seated,
            fell=bool(run.s.fallen),
            volt_v=12.0,
            policy="run C",
        )
    except Exception as exc:
        return dict(ran=False, camera="BLOCKER", note=note, error=_public_error(exc))


def limits_hit(parts, result, thermal, np):
    hits = []
    pack = result.get("pack") or {}
    i_max = pack.get("i_max")
    if i_max is not None and i_max > float(parts["fuse"]["i_fuse_a"]) + 1e-9:
        hits.append("pack current %.2f A crossed the %s A fuse" % (i_max, parts["fuse"]["i_fuse_a"]))
    if i_max is not None and i_max > float(parts["protection"]["i_work_a"]) + 1e-9:
        hits.append("pack current %.2f A crossed the %s A protection board" % (i_max, parts["protection"]["i_work_a"]))
    i_reg = None
    bp = result.get("_binsp") or {}
    if bp.get("i_bec_out_mean") is not None:
        i_reg = float(np.max(bp["i_bec_out_mean"]))
    if i_reg is not None and i_reg > float(parts["regulator"]["i_out_12v_at_10vin_a"]) + 1e-9:
        hits.append("regulator output %.2f A crossed the 16.5 A row at 10 V in" % i_reg)
    v_min = pack.get("v_term_min")
    floor = float(parts["pack"]["walk_stop_v"])
    if v_min is not None and v_min < floor - 1e-9:
        hits.append("pack fell to %.2f V, under the %.1f V walk cutoff" % (v_min, floor))
    if thermal["hot_c"] >= 60.0:
        hits.append("hottest reading %.1f C crossed the 60 C operating line" % thermal["hot_c"])
    if thermal["hot_c"] >= float(parts["rest"]["stop_c"]):
        hits.append("hottest reading reached the %s C rest" % parts["rest"]["stop_c"])
    return hits


def write_plot(path, result, thermal, parts, np):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    bp = result["_binsp"]
    t = np.asarray(bp["t_end"], float) / 60.0
    q = np.asarray(bp["q_mAh"], float)
    # Nameplate amp-hours from the parts file. The curve is the sim coulomb count.
    cap_mAh = float(parts["cells"]["capacity_ah"]) * 1000.0
    pct = (1.0 - q / cap_mAh) * 100.0
    i_pack = np.asarray(bp["i_pack_mean"], float)
    tt = np.asarray(thermal["t"], float) / 60.0
    knee = np.asarray(thermal["knee"], float)
    fig, ax = plt.subplots(3, 1, figsize=(7.2, 5.4), sharex=True)
    ax[0].plot(t, pct, color="#1f4e79", lw=1.2)
    ax[0].set_ylabel("battery %")
    ax[1].plot(tt, knee, color="#b85c38", lw=1.2)
    ax[1].axhline(float(parts["rest"]["stop_c"]), color="#b85c38", ls="--", lw=0.6)
    ax[1].set_ylabel("knee C")
    ax[2].plot(t, i_pack, color="#2f6f4e", lw=1.2)
    ax[2].set_ylabel("pack A")
    ax[2].set_xlabel("minutes")
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    if os.path.getsize(path) > 1_000_000:
        raise SystemExit("plot is over 1 MB")


def write_report(path, parts, result, thermal, charge, dock, hits, seconds):
    import numpy as np
    path_m, net_m = distance_of(result, np)
    gait = result.get("gait") or {}
    pack = result.get("pack") or {}
    q = float(result["q_end_mAh"])
    cap = float(parts["cells"]["capacity_ah"]) * 1000.0
    pct = (1.0 - q / cap) * 100.0
    stopped = result.get("stopped")
    fell = result.get("falls") or []
    walked = (not fell) and path_m > 0.5
    if fell:
        walked_line = "It fell at %.2f s (sim pass only)." % fell[0]
    elif stopped and str(stopped[0]).startswith("pack"):
        walked_line = "It walked until the pack cutoff at %.2f s (sim pass only)." % stopped[1]
    elif walked:
        walked_line = "It walked (sim pass only)."
    else:
        walked_line = "It did not hold a walk (sim pass only)."
    hot_limit = "60 C operating line on the servo page used by the thermal model, and the %s C rest in the limits file" % parts["rest"]["stop_c"]
    lines = []
    a = lines.append
    a("# One duck, one run")
    a("")
    a("Command: `make twin`")
    a("")
    a("Same command, short: `python3 -m altaay_lab.twin.run_twin --short`")
    a("")
    a("This is a simulation. Nothing here was measured on a servo, a cell, or a board.")
    a("")
    a(walked_line)
    a("The clock on this run is %.2f minutes (sim pass only). It stops at the 10 V pack cutoff or at 45 minutes, whichever comes first." % (float(result["dur_s"]) / 60.0))
    a("It covered %.2f m along the path, and ended %.2f m from the start (sim pass only)." % (path_m, net_m))
    a("The command is a room circuit: 6 s forward at 0.20 m/s, then a 2.2 s turn, four times around. An earlier run with the forward command held fixed logged 17.29 m of path and only 1.34 m from the start in 2 minutes, because the heading drifts and the path folds into a curve. That was not a room.")
    a("Mean speed along the path was %.3f m/s (sim pass only, path divided by time)." % (path_m / max(float(result["dur_s"]), 1e-6),))
    a("Battery at the end was %.1f percent of the %.2f Ah nameplate, %.0f mAh used (sim pass only for the coulomb count, cited for the nameplate)." % (pct, parts["cells"]["capacity_ah"], q))
    cutoff = result.get("stopped")
    if cutoff and str(cutoff[0]).startswith("pack"):
        a("The pack hit the %.1f V walk cutoff at %.1f s (sim pass only for the clock, cited for the cutoff)." % (float(parts["pack"]["walk_stop_v"]), float(cutoff[1])))
    else:
        a("The pack did not reach the %.1f V walk cutoff in this run (cited cutoff, sim pass only for the voltage)." % float(parts["pack"]["walk_stop_v"]))
    a("Pack voltage in the logged stats was %.2f V mean and %.2f V minimum (sim pass only)." % (
        float(pack.get("v_term_mean") or 0), float(pack.get("v_term_min") or 0)))
    a("Pack peak %.2f A is this 0.20 m/s room loop on the held 12.0 V rail (sim pass only). The 15.837 A in eval_table_bec12.md is a different case: the 0.40 m/s piece of a speed sequence, and that table still drops the regulator by 0.3 V instead of holding 12.0 V. The same table's 0.15 m/s typical peak is 8.956 A. Both peaks are sim pass only. Neither was measured on a pack." % float(pack.get("i_max") or 0))
    a("Hottest reading was the %s at %.1f C (sim pass only). The limit on that reading is the %s." % (thermal["hot_name"].replace("_", " "), thermal["hot_c"], hot_limit))
    a("The 55 C rest is inside the walk, not a replay. At 55 C the walk command goes to zero and the policy stands. It rested %d time%s. Walking was %.0f percent of the bins (sim pass only)." % (
        int(result.get("rests") or 0), "" if int(result.get("rests") or 0) == 1 else "s", 100.0 * thermal["walk_share"]))
    a("Turning the motor gains fully off tips this walk model over in a few seconds, and the knee joints only reach 90 deg, so the 147 deg sit from the sit study does not fit. The rest is therefore a powered stand. Holding the body up keeps the knee near 55 C, so it does not cool to 45 C and does not start walking again. That limit is sim pass only.")
    if dock.get("ran"):
        a("Dock: %s The mechanical sim used the run C policy and a 12 V rail. It %s (sim pass only). The aim offset table has no 12 V row, so that offset stayed at the 7.2 V measurement. Finding the nest by camera was not simulated." % (
            dock["note"], "sat" if dock.get("seated_mechanical") else "did not sit"))
    else:
        a("Dock: %s The mechanical sim did not finish in this run (%s)." % (dock["note"], dock.get("error") or "not run"))
    if charge["allows"]:
        a("Charge: the NTC gate is open at a cell temperature of %.1f C (calc only, bead beta and the BQ24133 divider). Time to put the used %.0f mAh back at %.3f A is %.2f hours (calc only)." % (
            charge["cell_c"], charge["q_mAh"], float(parts["charger"]["i_charge_a"]), charge["hours"] or 0))
    else:
        a("Charge: the NTC gate is shut at %.1f C (calc only). It does not charge." % charge["cell_c"])
    if hits:
        a("Limits this run touched: " + "; ".join(hits) + ".")
    else:
        a("No fuse, protection, regulator-row, walk-cutoff, or 60 C line was crossed in this run. The %s C rest did %s." % (
            parts["rest"]["stop_c"], "trip" if thermal["hot_c"] >= float(parts["rest"]["stop_c"]) else "not trip"))
    a("")
    a("## Numbers")
    a("")
    rows = [
        ("walked", "yes" if walked and not fell else "no", "sim pass only"),
        ("duration", "%.2f min" % (float(result["dur_s"]) / 60.0), "sim pass only"),
        ("path", "%.2f m" % path_m, "sim pass only"),
        ("net travel", "%.2f m" % net_m, "sim pass only"),
        ("rests", "%d" % int(result.get("rests") or 0), "sim pass only"),
        ("body speed", "%.3f m/s" % float(gait.get("vx") or 0), "sim pass only"),
        ("duck mass", "%.3f kg" % float(parts["mass"].get("robot_kg") or 0), parts["mass"].get("mass_label", "CAD mass model")),
        ("battery left", "%.1f percent" % pct, "sim pass only"),
        ("nameplate", "%.2f Ah" % float(parts["cells"]["capacity_ah"]), "cited"),
        ("pack mean", "%.2f V" % float(pack.get("v_term_mean") or 0), "sim pass only"),
        ("pack minimum", "%.2f V" % float(pack.get("v_term_min") or 0), "sim pass only"),
        ("pack mean current", "%.2f A" % float(pack.get("i_mean") or 0), "sim pass only"),
        ("pack peak current", "%.2f A" % float(pack.get("i_max") or 0), "sim pass only"),
        ("servo rail set point", "%.1f V" % float(parts["regulator"]["v_set"]), "cited"),
        ("regulator efficiency used", "%.2f" % float(parts["regulator"]["eff_used"]), "cited"),
        ("walk cutoff", "%.1f V" % float(parts["pack"]["walk_stop_v"]), "cited"),
        ("hottest part", thermal["hot_name"].replace("_", " "), "sim pass only"),
        ("hottest reading", "%.1f C" % thermal["hot_c"], "sim pass only"),
        ("rest stop", "%.0f C" % float(parts["rest"]["stop_c"]), "limits file"),
        ("rest resume", "%.0f C" % float(parts["rest"]["resume_c"]), "limits file"),
        ("cell temperature", "%.1f C" % thermal["cell_c"], "sim pass only"),
        ("dock", "BLOCKER", "BLOCKER"),
        ("charge current", "%.3f A" % float(parts["charger"]["i_charge_a"]), "cited"),
        ("time to replace what was used", "%.2f h" % (charge["hours"] or 0), "calc only"),
        ("NTC allows charge", "yes" if charge["allows"] else "no", "calc only"),
        ("fuse", "%.0f A" % float(parts["fuse"]["i_fuse_a"]), "cited"),
        ("thermal step", "%.1f s" % thermal["width"], "sim pass only"),
        ("scenario length asked", "%.2f min" % (float(seconds) / 60.0), "the command"),
    ]
    a("| What | Value | Label |")
    a("|---|---|---|")
    for name, val, label in rows:
        a("| %s | %s | %s |" % (name, val, label))
    a("")
    a("## What this twin does not model")
    a("")
    a("- A camera finding the nest. That is BLOCKER. The nest program uses the true pose plus noise.")
    a("- A pack-voltage sensor on the Pi. The 10 V stop is in the guard, and this sim passes the modeled pack voltage in. The Pi still has no sensor (BLOCKER).")
    a("- Winding resistance of the C018 as a measured number. The heat model still uses the assumed split from the older sheet.")
    a("- The i7C current below 10 V, the TRIM resistor, and the wide boost tolerance above 100 W (BLOCKER).")
    a("- Felt, dirt, and a measured well contact.")
    a("- The turn-offset table at 12 V. The dock uses the 7.2 V aim offset with a 12 V rail.")
    a("- Hardware. Every temperature, speed, and current above that says sim pass only is a model output.")
    a("")
    text = _no_dash("\n".join(lines) + "\n")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    p = argparse.ArgumentParser(description="Run the one digital twin")
    p.add_argument("--short", action="store_true", help="a few seconds, no dock sim")
    p.add_argument("--minutes", type=float, default=None)
    p.add_argument("--seconds", type=float, default=None)
    p.add_argument("--skip-dock", action="store_true")
    p.add_argument("--out", default=os.path.join(HERE, "out"))
    args = p.parse_args(argv)
    bad = PT.check()
    if bad:
        for row in bad:
            print("FAIL", row)
        return 1
    parts = PT.load()
    if args.short:
        seconds = 6.0
        skip_dock = True
    else:
        seconds = float(args.seconds) if args.seconds is not None else float(args.minutes if args.minutes is not None else 45.0) * 60.0
        skip_dock = bool(args.skip_dock)
    os.makedirs(args.out, exist_ok=True)
    scratch = tempfile.mkdtemp(prefix="duck_twin_")
    print("walk %.1f s" % seconds, flush=True)
    result, np = walk(parts, seconds, scratch)
    print("heat trace", result.get("rests"), "rests", flush=True)
    thermal = heat_of(result, np)
    print("charge", flush=True)
    charge = charge_of(parts, result, thermal["cell_c"])
    if skip_dock:
        dock = dict(
            ran=False, camera="BLOCKER",
            note="BLOCKER. The nest sim does not use a camera. It drives on the true pose plus noise. A seat in that sim is not a dock.",
            error="not run on this short command",
        )
    else:
        print("dock", flush=True)
        dock = dock_once()
    hits = limits_hit(parts, result, thermal, np)
    report = os.path.join(args.out, "REPORT.md")
    plot = os.path.join(args.out, "walk.png")
    write_report(report, parts, result, thermal, charge, dock, hits, seconds)
    write_plot(plot, result, thermal, parts, np)
    print("wrote %s" % os.path.relpath(report, ROOT))
    print("wrote %s" % os.path.relpath(plot, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
