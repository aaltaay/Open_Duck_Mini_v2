#!/usr/bin/env python3
"""One digital twin. One command. CPU only.

  python3 -m altaay_lab.twin.run_twin
  python3 -m altaay_lab.twin.run_twin --short
  make twin

Every physical number is loaded from altaay_lab/twin/parts.yaml, which is
derived from the netlist, the limits file, and the order. The walk is the
run C policy in MuJoCo. The pack uses the existing power network and the
battery guard's pack floor. Heat uses the existing thermal twin, one step
per 0.1 s current bin, with the C018 sheet's 1.0 ohm terminal resistance.
The nest sim is the existing one. Camera docking is
not in that sim, so the dock line is BLOCKER.

Nothing is bought. No paid GPU.
"""
import argparse
import json
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


# ST-3215-C018 specification A/0 (2023-07-20), items 5-10 and 5-6. Cited.
# The PDF is the download on https://www.feetechrc.com/525603.html
R_TERM_OHM = 1.0
I_IDLE_STOPPED_A = 0.030
KNEE_SOFT_HI_DEG = 147.0


def sit_path():
    """Sit-study pose, clamped to the register soft stops.

    Knee high stop in this command is 147 deg. The CAD bumper is 150 deg
    (software/servo_limits.json). The walk ankle joint is still -90 deg.
    The sit note's foot clearance is already met at -75 deg when the knee
    is at 150 deg, so -90 deg is enough and the ankle range is left alone.
    """
    with open(os.path.join(LAB, "twin", "sit", "sit_pose.json"), encoding="utf-8") as f:
        raw = json.load(f)["joints_deg"]
    with open(os.path.join(LAB, "software", "servo_limits.json"), encoding="utf-8") as f:
        limits = json.load(f)["joints"]
    final = {}
    for name, deg in raw.items():
        deg = float(deg)
        lim = limits.get(name) or {}
        if lim.get("soft_lo_deg") is not None:
            deg = max(deg, float(lim["soft_lo_deg"]))
        if lim.get("soft_hi_deg") is not None:
            deg = min(deg, float(lim["soft_hi_deg"]))
        final[name] = deg
    for name in ("left_ankle", "right_ankle"):
        if name in final:
            final[name] = max(final[name], -90.0)
    # One ramp. A stop at a half fold tips this walk model when the gains drop.
    # The full 147 deg fold stays up with the gains off.
    return [(3.5, final)]


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
        # Item 5-10 is the motor terminal resistance. Copper heat is I^2 times that
        # value. The old 3.753 ohm split is the stall-line resistance times the C001
        # winding share. It is not on the C018 sheet. See HEAT_AUDIT.md.
        p_idle = I_IDLE_STOPPED_A * max(vbar, 0.5)
        servo = dict(
            P_cu25=i2 * R_TERM_OHM,
            P_board=np.zeros(14),
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


def _boot():
    import em_twin as ET
    import knee_heat_chafe as KH
    import twin_thermal as TT
    return ET, KH, TT


def measure_rest(parts, scratch):
    """Zero-command stance, a 20 deg crouch, then the 147 deg sit with torque off."""
    import numpy as np
    ET, _, TT = _boot()
    knee = TT.NAMES.index("right_knee")
    rows = []

    def on_bin(info):
        rows.append(dict(
            t=float(info["t"]), phase=info["phase"],
            im=float(info["im"][knee]), q=float(info["q_deg"][knee]),
            imv=np.asarray(info["im"], float).copy(),
        ))
        if info["t"] >= 1.2 and info["phase"] == "walk":
            return "rest"
        return None

    extra = dict(
        BEC_V=float(parts["regulator"]["v_set"]),
        BEC_EFF=float(parts["regulator"]["eff_used"]),
        BEC_HOLD=1 if parts["regulator"]["holds"] else 0,
    )
    r = ET.run(
        mass="ours", walk="backlash", cmd=(0.0, 0.0, 0.0), dur=11.0,
        supply="net", corner="typical", extra=extra,
        cell="p45b3", q0=0.0, servo_mode="sheet", guard=None,
        keep_full=False, bin_s=0.1, stop_on_fall=False, t_stats=0.0,
        label="sit rest", progress=0.0,
        command_fn=lambda t, data, m: [0.0] * 7, on_bin=on_bin,
        sit_path_deg=sit_path(), knee_hi_deg=KNEE_SOFT_HI_DEG,
    )
    crouch_pose = {}
    for name, deg in sit_path()[-1][1].items():
        if "knee" in name:
            crouch_pose[name] = 20.0 if deg > 0 else -20.0
        elif "ankle" in name:
            crouch_pose[name] = -15.0 if deg < 0 else 15.0
        else:
            crouch_pose[name] = 0.0
    crow = []

    def on_crouch(info):
        crow.append(dict(
            t=float(info["t"]), phase=info["phase"],
            im=float(info["im"][knee]), q=float(info["q_deg"][knee]),
            imv=np.asarray(info["im"], float).copy(),
        ))
        if info["t"] >= 0.4 and info["phase"] == "walk":
            return "rest"
        return None

    rc = ET.run(
        mass="ours", walk="backlash", cmd=(0.0, 0.0, 0.0), dur=3.5,
        supply="net", corner="typical", extra=extra,
        cell="p45b3", q0=0.0, servo_mode="sheet", guard=None,
        keep_full=False, bin_s=0.1, stop_on_fall=False, t_stats=0.0,
        label="crouch", progress=0.0,
        command_fn=lambda t, data, m: [0.0] * 7, on_bin=on_crouch,
        sit_path_deg=[(6.0, crouch_pose)], knee_hi_deg=KNEE_SOFT_HI_DEG,
    )

    def window(src, t0, t1):
        sel = [row for row in src if t0 <= row["t"] < t1]
        if not sel:
            return dict(i=None, q=None, im=None)
        im = np.array([row["im"] for row in sel], float)
        q = np.array([row["q"] for row in sel], float)
        imv = np.mean([row["imv"] for row in sel], axis=0)
        return dict(i=float(np.sqrt(np.mean(im * im))), q=float(q[-1]), im=imv)

    off_rows = [row for row in rows if row["phase"] == "off"]
    return dict(
        falls=list(r.get("falls") or []),
        phase_end=r.get("phase_end"),
        stance=window(rows, 0.4, 1.2),
        crouch=window(crow, 2.4, 3.5),
        crouch_falls=list(rc.get("falls") or []),
        folded=window(rows, 5.8, 6.6),
        off=window(rows, 8.0, 11.0),
        knee_max=float(max(row["q"] for row in rows)) if rows else 0.0,
        off_n=len(off_rows),
    )


def _replay(np, TT, c, walk_im, rest_im, r_ohm, r_board, area, knee_scale, stop, resume):
    dt = 0.1
    minutes = 45.0
    n = int(round(minutes * 60.0 / dt))
    hw = TT.HeatWalk(dict(c), 25.0, dt)
    hw.A = np.array(hw.A, float).copy()
    for name in ("left_knee", "right_knee"):
        hw.A[TT.NAMES.index(name)] *= area
    jk = [TT.NAMES.index(name) for name in ("left_knee", "right_knee")]
    seq = np.asarray(walk_im, float).copy()
    seq[:, jk] *= knee_scale
    rest = np.zeros(14) if rest_im is None else np.asarray(rest_im, float).copy()
    rest[jk] *= knee_scale
    state = "walk"
    walk_n = 0
    knee = TT.NAMES.index("right_knee")
    peak = -1e9
    idle = I_IDLE_STOPPED_A * 12.0
    trunk = dict(cells=0.0, holder=0.0, bms=0.0, fuse=0.0, xt30=0.0, switch=0.0, wires=0.0, bec=0.2, bec_leads=0.0, logic=0.15)
    for s in range(n):
        walking = state == "walk"
        im = seq[s % len(seq)] if walking else rest
        i2 = im * im
        servo = dict(
            P_cu25=i2 * r_ohm, P_board=i2 * r_board,
            P_fric=np.zeros(14), P_idle=np.full(14, idle),
        )
        Ts = hw.step(dict(servo=servo, trunk=trunk, head=c["P5V"]), walking)
        peak = max(peak, float(Ts[knee]))
        if walking:
            walk_n += 1
        hot = float(np.max(Ts))
        if state == "walk" and hot >= stop:
            state = "rest"
        elif state == "rest" and hot <= resume:
            state = "walk"
    return walk_n / max(n, 1), peak


def cool_min(np, TT, c, rest_im, r_ohm, r_board, start=55.0, goal=45.0):
    dt = 0.1
    hw = TT.HeatWalk(dict(c), 25.0, dt)
    hw.Tw[:] = start
    hw.Tb[:] = start
    hw.Ts[:] = start
    im = np.zeros(14) if rest_im is None else np.asarray(rest_im, float)
    idle = I_IDLE_STOPPED_A * 12.0
    trunk = dict(cells=0.0, holder=0.0, bms=0.0, fuse=0.0, xt30=0.0, switch=0.0, wires=0.0, bec=0.05, bec_leads=0.0, logic=0.15)
    knee = TT.NAMES.index("right_knee")
    n = int(round(30.0 * 60.0 / dt))
    for s in range(n):
        i2 = im * im
        servo = dict(
            P_cu25=i2 * r_ohm, P_board=i2 * r_board,
            P_fric=np.zeros(14), P_idle=np.full(14, idle),
        )
        Ts = hw.step(dict(servo=servo, trunk=trunk, head=c["P5V"]), False)
        if float(Ts[knee]) <= goal:
            return (s + 1) * dt / 60.0
    return None


def rank_fixes(result, rest, np):
    """45 min replays of this walk's current. Sim pass only."""
    import knee_heat_chafe as KH
    import twin_thermal as TT
    c = dict(TT.CORNERS["central"])
    im = np.asarray(result["_bins"]["Im_rms"], float)
    phases = list(result.get("phases") or [])
    n = min(len(im), len(phases))
    walked = [im[i] for i in range(n) if phases[i] == "walk"]
    if len(walked) < 2:
        walked = list(im[:max(n, 1)])
    walk_im = np.asarray(walked, float)
    zero = np.zeros(14)
    stance = rest["stance"]["im"] if rest["stance"]["im"] is not None else zero
    crouch = rest["crouch"]["im"] if rest["crouch"]["im"] is not None else stance
    off = rest["off"]["im"] if rest["off"]["im"] is not None else zero
    r_old = float(KH.R_W_12 + KH.R_BOARD_12)
    stop = 55.0
    resume = 45.0
    specs = [
        ("cited 1.0 ohm, powered stand", R_TERM_OHM, 0.0, 1.0, 1.0, stance, 0.0, "this run"),
        ("cited 1.0 ohm, torque-off sit", R_TERM_OHM, 0.0, 1.0, 1.0, off, 0.0, "sit check"),
        ("old stall-line 4.444 ohm, torque-off sit", r_old, 0.0, 1.0, 1.0, off, 0.0, "comparison"),
        ("old stall-line 4.444 ohm, powered stand", r_old, 0.0, 1.0, 1.0, stance, 0.0, "the 3 percent run"),
        ("knee current times 0.70", R_TERM_OHM, 0.0, 1.0, 0.70, off, 0.0, "retrain"),
        ("20 deg knee crouch, torque on", R_TERM_OHM, 0.0, 1.0, 1.0, crouch, 0.0, "stance"),
        ("knee area times 1.3", R_TERM_OHM, 0.0, 1.3, 1.0, off, 0.0, "heatsink"),
        ("knee area times 1.8", R_TERM_OHM, 0.0, 1.8, 1.0, off, 0.0, "heatsink"),
        ("STS3250 knees, cited 1.2 ohm", 1.2, 0.0, 1.0, 1.0, off, 39.0, "servo swap"),
        ("gear ratio times 1.5", R_TERM_OHM, 0.0, 1.0, 1.0 / 1.5, off, 0.0, "not a catalog part"),
    ]
    rows = []
    for name, r_ohm, r_board, area, scale, rest_im, mass_g, kind in specs:
        share, peak = _replay(np, TT, c, walk_im, rest_im, r_ohm, r_board, area, scale, stop, resume)
        rows.append(dict(name=name, share=share, minutes=share * 45.0, peak=peak, mass_g=mass_g, kind=kind))
    cool_off = cool_min(np, TT, c, off, R_TERM_OHM, 0.0)
    cool_stand = cool_min(np, TT, c, stance, R_TERM_OHM, 0.0)
    return dict(rows=rows, cool_off=cool_off, cool_stand=cool_stand, r_old=r_old)


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


def write_report(path, parts, result, thermal, charge, dock, hits, seconds, rest, rank):
    import numpy as np
    path_m, net_m = distance_of(result, np)
    gait = result.get("gait") or {}
    pack = result.get("pack") or {}
    q = float(result["q_end_mAh"])
    cap = float(parts["cells"]["capacity_ah"]) * 1000.0
    pct = (1.0 - q / cap) * 100.0
    stopped = result.get("stopped")
    fell = result.get("falls") or []
    log = np.asarray(result.get("_log"), float) if result.get("_log") is not None else np.zeros((0, 2))
    recovered = False
    if fell and len(log) > 2 and log.shape[1] > 10:
        after = log[log[:, 0] > float(fell[0]) + 1.0]
        recovered = len(after) > 0 and bool((after[:, 10] < 0.5).any())
    walked = path_m > 0.5 and (not fell or recovered)
    if fell and recovered:
        walked_line = "It tipped at %.2f s and was up again (sim pass only)." % fell[0]
    elif fell:
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
    spikes = int(pack.get("n_solver_spike") or 0)
    spike_txt = "No solver step left the 8 V to 13.2 V window."
    if spikes:
        spike_txt = "Solver steps outside that window: %d. Their raw extreme was %.2f A and %.2f V, and those steps are not the walk current." % (
            spikes, float(pack.get("i_max_raw") or 0), float(pack.get("v_min_raw") or 0))
    a("Pack peak %.2f A is this 0.20 m/s room loop on the held 12.0 V rail, counting steps whose pack voltage stayed between 8 V and 13.2 V (sim pass only). The 15.837 A in eval_table_bec12.md is a different case: the 0.40 m/s piece of a speed sequence, and that table still drops the regulator by 0.3 V instead of holding 12.0 V. The same table's 0.15 m/s typical peak is 8.956 A. Both peaks are sim pass only. Neither was measured on a pack. %s" % (
        float(pack.get("i_max") or 0), spike_txt))
    a("Hottest reading was the %s at %.1f C (sim pass only). The limit on that reading is the %s." % (thermal["hot_name"].replace("_", " "), thermal["hot_c"], hot_limit))
    a("The 55 C rest is inside the walk. At 55 C the command goes to zero and the policy stands. Folding to the sit from a walk tips this model, so the session does not fold. It rested %d time%s. Upright walking is the figure in the table (sim pass only)." % (
        int(result.get("rests") or 0), "" if int(result.get("rests") or 0) == 1 else "s"))
    if rest.get("falls"):
        sit_line = "The 147 deg sit tipped at %.2f s in the rest check (sim pass only)." % rest["falls"][0]
    else:
        sit_line = (
            "The rest check reached a right knee of %.0f deg, then torque off. "
            "Stance current was %.2f A, the 20 deg crouch was %.2f A, and torque off was %.3f A (sim pass only)."
            % (
                rest.get("knee_max") or 0,
                rest["stance"]["i"] or 0,
                rest["crouch"]["i"] or 0,
                rest["off"]["i"] or 0,
            )
        )
    cool_off = rank.get("cool_off")
    cool_stand = rank.get("cool_stand")
    off_txt = "did not reach 45 C in 30 min" if cool_off is None else "reached 45 C in %.2f min" % cool_off
    stand_txt = "did not reach 45 C in 30 min" if cool_stand is None else "reached 45 C in %.2f min" % cool_stand
    a(sit_line + " From a 55 C start, torque off %s. The powered stand %s. Both clocks are sim pass only, on the cited 1.0 ohm." % (off_txt, stand_txt))
    a("Knee high stop used here is 147 deg, the register soft stop. The CAD bumper is 150 deg (software/servo_limits.json, CAD check only). The walk model was compiled at 90 deg, and this run raises that stop before the sit.")
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
        ("walking minutes", "%.2f min" % (float(result.get("upright_walk_s") or 0.0) / 60.0), "sim pass only"),
        ("terminal resistance", "%.1f ohm" % R_TERM_OHM, "cited"),
        ("knee high stop", "%.0f deg" % KNEE_SOFT_HI_DEG, "CAD check only"),
        ("sit knee reached", "%.0f deg" % (rest.get("knee_max") or 0), "sim pass only"),
        ("torque-off cool from 55 C", off_txt, "sim pass only"),
        ("powered-stand cool from 55 C", stand_txt, "sim pass only"),
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
    a("- A bench measurement of the C018 terminal resistance. The heat uses the 1.0 ohm printed in specification A/0 item 5-10. The stall line 12 V / 2.7 A is 4.444 ohm on the same sheet, and the old 3.753 ohm figure was that stall line times the C001 winding share. The audit is altaay_lab/twin/thermal/HEAT_AUDIT.md.")
    a("- The i7C current below 10 V, the TRIM resistor, and the wide boost tolerance above 100 W (BLOCKER).")
    a("- Felt, dirt, and a measured well contact.")
    a("- The turn-offset table at 12 V. The dock uses the 7.2 V aim offset with a 12 V rail.")
    a("- Hardware. Every temperature, speed, and current above that says sim pass only is a model output.")
    a("")
    a("The duck mass is the whole robot. The trunk body alone is %.3f kg. The stock Open Duck Mini model is %.3f kg. MuJoCo loads %.3f kg, and the parts rollup is %.3f kg. The rollup includes three P45B cells at the cited 70 g, the i7C at the cited 75 g, the 3S protection board, the BQ24133 board, and three limb breakers. The protection-board grams are the cited size times 1.2 g/cm3 (calc only). The BQ24133 assembled grams and the breaker package grams are not on a datasheet." % (
        float(parts["mass"].get("trunk_kg") or 0), float(parts["mass"].get("stock_kg") or 0),
        float(parts["mass"].get("robot_kg") or 0), float(parts["mass"].get("rollup_kg") or 0)))
    a("")
    a("## What was compared")
    a("")
    a("Each row replays this run's walking current for 45 min. The rest is the measured stance current, the measured crouch current, or torque off. Sim pass only. Mass is the change from the C018 knees. No new part is on the bill.")
    a("")
    a("| Option | Walking minutes | Knee peak C | Added mass g | Kind |")
    a("|---|---|---|---|---|")
    chosen = None
    for row in rank["rows"]:
        a("| %s | %.1f | %.1f | %.0f | %s |" % (row["name"], row["minutes"], row["peak"], row["mass_g"], row["kind"]))
        if row["kind"] == "this run":
            chosen = row
    a("")
    session_min = float(result.get("upright_walk_s") or 0.0) / 60.0
    if chosen and chosen["minutes"] >= 20.0 and chosen["peak"] < 60.0 and session_min >= 20.0 and thermal["knee_c"] < 60.0:
        a("Chosen: the cited 1.0 ohm terminal resistance, and a stand with the command at zero when the reading reaches 55 C. This session's upright walking is %.1f min with the knee at %.1f C, and it adds no mass. The 45 min replay of the walking current, resting at the measured stance current, walks %.1f min with the knee at %.1f C. A separate check folds to 147 deg from a settled stand and turns the gains off. Folding from a walk tips this model, so that fold is not the session rest. The heatsink rows assume extra case area. The servo swap and the gear row are studies. No decision entry. A lower knee current would need a retrain, and this session did not run one." % (
            session_min, thermal["knee_c"], chosen["minutes"], chosen["peak"]))
    else:
        a("No option is a clear hardware win on this session. The table is a study. A gait with lower knee torque needs a retrain on a GPU. The published RTX 4090 note is 1.5 to 3 hours, and the RunPod 4090 rates already cited in problems/TRAIN_STS12.md are $0.34 to $0.89 an hour, so that retrain is about $0.51 to $2.67. It was not run.")
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
    print("rest", flush=True)
    rest = measure_rest(parts, scratch)
    rank = rank_fixes(result, rest, np)
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
    write_report(report, parts, result, thermal, charge, dock, hits, seconds, rest, rank)
    write_plot(plot, result, thermal, parts, np)
    print("wrote %s" % os.path.relpath(report, ROOT))
    print("wrote %s" % os.path.relpath(plot, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
