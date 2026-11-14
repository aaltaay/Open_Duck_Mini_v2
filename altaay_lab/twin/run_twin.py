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
    import sts12  # noqa: F401  registers the 3S pack and the 12 V sheet
    import em_twin as ET

    extra = dict(
        BEC_V=float(parts["regulator"]["v_set"]),
        BEC_EFF=float(parts["regulator"]["eff_used"]),
        BEC_HOLD=1 if parts["regulator"]["holds"] else 0,
    )
    cmd = (0.15, 0.0, 0.0)
    r = ET.run(
        mass="ours", walk="backlash", cmd=cmd, dur=float(seconds),
        supply="net", corner="typical", extra=extra,
        cell="p45b3", q0=0.0, servo_mode="sheet", guard="act",
        keep_full=False, bin_s=0.1, stop_on_fall=False, t_stats=0.0,
        label="one twin", progress=max(10.0, float(seconds) / 4.0),
    )
    return r, np


def heat(parts, result, np):
    sys.path.insert(0, os.path.join(LAB, "problems"))
    sys.path.insert(0, os.path.join(LAB, "twin", "thermal"))
    import knee_heat_chafe as KH
    import twin_thermal as TT

    bins = result["_bins"]
    bp = result["_binsp"]
    tbin = np.asarray(bp["t_end"], float)
    width = bin_width(tbin)
    if abs(width - 0.1) > 1e-3:
        raise RuntimeError("thermal step is %.4f s, not 0.1 s" % width)
    s = dict(
        t=tbin,
        im=np.asarray(bins["Im_rms"], float) / KH.I_SCALE,
        i_pack=np.asarray(bp["i_pack_mean"], float),
        i_pack_rms=np.asarray(bp["i_pack_rms"], float),
        v_bus=np.asarray(bp["v_bus_mean"], float),
        v_bec=np.asarray(bp["v_bec_out_mean"], float),
        i_bec_rms=np.asarray(bp["i_bec_out_rms"], float),
    )
    sts = dict(
        i_mean=float(np.nanmean(s["i_pack"])),
        i_rms=float(np.nanmean(s["i_pack_rms"])),
        bus_mean=float(np.nanmean(s["v_bus"])),
        bec_out_mean=float(np.nanmean(s["v_bec"])),
    )
    heats, c, t_used, _meta = KH.build_12v(s, sts, 1.0, 70.0, True)
    eta = float(parts["regulator"]["eff_used"])
    i_bec = np.asarray(bp["i_bec_out_mean"], float)
    for i in range(len(tbin)):
        p_out = float(s["v_bec"][i]) * float(i_bec[i])
        heats[i]["trunk"]["bec"] = p_out * (1.0 / eta - 1.0)
    # Torque-off rest uses the same cited efficiency, not the dropout assumption.
    p_idle = 14.0 * 0.021 * float(sts["bec_out_mean"])
    heats["off"]["trunk"]["bec"] = p_idle * (1.0 / eta - 1.0)
    nbin = len(tbin)
    sched = sched_every_bin(nbin, width)
    guard = dict(stop=float(parts["rest"]["stop_c"]), resume=float(parts["rest"]["resume_c"]), rest="off")
    sim = TT.simulate(sched, heats, None, c, 25.0, t_end=float(tbin[-1]), dt=width, guard=guard, record=width)
    names = list(TT.NAMES)
    jr = names.index("right_knee")
    hot = int(np.argmax(sim["max_Ts"]))
    return dict(
        t=np.asarray(sim["t"], float),
        ts=np.asarray(sim["Ts"], float),
        names=names,
        knee=jr,
        hot=hot,
        hot_name=names[hot],
        hot_c=float(sim["max_Ts"][hot]),
        knee_c=float(np.max(sim["Ts"][:, jr])),
        cell_c=float(np.max(sim["cells"])),
        walk_share=float(sim["walk_share"]),
        state=list(sim["state"]),
        width=width,
        nbin=nbin,
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
        stock = os.path.join(ROOT, "BEST_WALK_ONNX_2.onnx")
        CB.ONNX = stock
        import nest_run as NR
        run = NR.Run(dict(seed=0, volt=7.2, noise="mid", mu=0.8, pins=False))
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
            volt_v=7.2,
            policy="stock policy, the sim's own turn table",
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
    if i_max is not None and i_max > float(parts["regulator"]["i_out_12v_at_10vin_a"]) + 1e-9:
        hits.append("pack current %.2f A crossed the 16.5 A regulator row at 10 V in" % i_max)
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
    knee = np.asarray(thermal["ts"], float)[:, thermal["knee"]]
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
    walked = (not fell) and (gait.get("vx") or 0) > 0.02 and stopped != ("fall", fell[:1])
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
    a("The clock on this run is %.2f minutes (sim pass only)." % (float(result["dur_s"]) / 60.0))
    a("It covered %.2f m along the path, and ended %.2f m from the start (sim pass only)." % (path_m, net_m))
    a("Body speed was %.3f m/s at a 0.15 m/s command (sim pass only)." % float(gait.get("vx") or 0.0))
    a("Battery at the end was %.1f percent of the %.2f Ah nameplate, %.0f mAh used (sim pass only for the coulomb count, cited for the nameplate)." % (pct, parts["cells"]["capacity_ah"], q))
    a("Pack voltage at the end of the logged stats was %.2f V, minimum %.2f V (sim pass only). The walk cutoff is %.1f V (cited)." % (
        float(pack.get("v_term_mean") or 0), float(pack.get("v_term_min") or 0), float(parts["pack"]["walk_stop_v"])))
    a("Hottest reading was the %s at %.1f C (sim pass only). The limit on that reading is the %s." % (thermal["hot_name"].replace("_", " "), thermal["hot_c"], hot_limit))
    a("The heat model spent %.0f percent of the run walking. The remainder is the torque-off rest (sim pass only). That rest is not the code on the Pi." % (100.0 * thermal["walk_share"]))
    if dock.get("ran"):
        a("Dock: %s The mechanical sim at 7.2 V, stock policy, %s (sim pass only). That voltage is the sim's own table, not the 12 V rail." % (
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
        ("body speed", "%.3f m/s" % float(gait.get("vx") or 0), "sim pass only"),
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
    a("- The policy pausing inside MuJoCo at 55 C. The rest rule is applied when the heat model replays the current bins. The two are not one closed loop.")
    a("- A pack-voltage sensor on the Pi. The 10 V stop is in the guard, and this sim passes the modeled pack voltage in. The Pi still has no sensor (BLOCKER).")
    a("- Winding resistance of the C018 as a measured number. The heat model still uses the assumed split from the older sheet.")
    a("- The i7C current below 10 V, the TRIM resistor, and the wide boost tolerance above 100 W (BLOCKER).")
    a("- Felt, dirt, a measured well, and a whole-duck mass. Mass of the walking body is the existing added-mass model (GAP in the parts file).")
    a("- Joint angle limits from the parts file. They are not in the netlist, the limits file, or the order (GAP).")
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
        seconds = float(args.seconds) if args.seconds is not None else float(args.minutes or 2.0) * 60.0
        skip_dock = bool(args.skip_dock)
    os.makedirs(args.out, exist_ok=True)
    scratch = tempfile.mkdtemp(prefix="duck_twin_")
    print("walk %.1f s" % seconds, flush=True)
    result, np = walk(parts, seconds, scratch)
    print("heat", flush=True)
    thermal = heat(parts, result, np)
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
