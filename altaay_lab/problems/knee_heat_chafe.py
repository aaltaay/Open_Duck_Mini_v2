#!/usr/bin/env python3
"""Knee heat and the 1 ohm chafe, on the existing thermal twin. CPU only.

Does not edit the twin, the netlist, part_limits, FMEA.md, or D61.
PR 83 and PR 84 were open when this was written, so those files are not in this tree.

  python3 altaay_lab/problems/knee_heat_chafe.py

Temperatures are sim pass only. Currents and fuse times are calc only, except
currents copied from a session log or an eval table, which stay sim pass only.
Cited numbers are marked in the JSON.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, ".."))
THERM = os.path.join(LAB, "twin", "thermal")
sys.path.insert(0, THERM)

import twin_thermal as TT  # noqa: E402
import gate_p45b as G  # noqa: E402

OUT = os.path.join(HERE, "knee_heat_chafe_results.json")
CSV = os.path.join(LAB, "twin", "electromech", "out", "p45b_sheet", "session_bam_backlash_typical.csv")

# C001 sheet A/1, opened in THERMAL_TWIN.md. Stall 19.5 kg.cm at 2.5 A, 7.4 V.
KT_7V4 = 19.5 * 0.0980665 / 2.5
# C018 page, problems/sts12.json. Stall line 12 V / 2.7 A = 4.444 ohm.
KT_12 = 1.0896
R_LOOP_12 = 4.444
R_LOOP_7 = 2.96
R_W_SHARE = 2.5 / R_LOOP_7  # C001 winding share of the stall line. Not printed for the C018.
R_W_12 = R_LOOP_12 * R_W_SHARE
R_BOARD_12 = R_LOOP_12 - R_W_12
I_SCALE = KT_7V4 / KT_12
V_DROP = 0.3
N_CELLS = 3
R_CELL = 0.015

# Run C at BEC 12.0 V, eval_table_bec12.md (PR 84). Sim pass only.
RUN_C = {
    "0.15_typical_peak_A": 8.956,
    "0.15_typical_100ms_A": 6.337,
    "0.40_typical_peak_A": 15.599,
    "0.40_typical_100ms_A": 13.081,
    "seq_typical_peak_A": 15.837,
    "seq_typical_100ms_A": 13.064,
}
# Older STS12 0.15 m/s walk, problems/sts12.json. Not run C.
STS12_PACK = dict(i_mean=5.068, i_rms=5.42, i_max=9.527, bus_mean=11.894, bec_out_mean=11.576)
# Old 7.4 V budget on the 16 AWG after the switch, wiring notes. Sim pass only.
OLD_PACK_100MS_A = 7.04
# Servo-feed 100 ms peaks, WIRES.md, the 7.4 V budget. Sim pass only.
FEED_PEAK_A = {
    "SP1_left_hip": 1.64,
    "SP4_left_ankle": 1.98,
    "SP2_right_hip": 2.21,
    "SP5_right_ankle": 2.11,
    "SP3_neck": 1.52,
}

# Littelfuse ATOF 0287, the family of 0287015.PXCN.
# https://www.littelfuse.com/assetdocs/littelfuse_datasheet_287_atof_r2.7.pdf
# Windows for a 3 A to 40 A fuse. Times in seconds. None means the sheet gives no max.
ATOF_3_TO_40 = [
    (1.10, 360000.0, None),
    (1.35, 0.750, 600.0),
    (1.60, 0.250, 50.0),
    (2.00, 0.150, 5.0),
    (3.50, 0.080, 0.500),
    (6.00, None, 0.100),
]


def apply_three_cell(t_cut):
    TT.PARAMS["R_cell"] = R_CELL
    TT.PARAMS["m_cell_g"] = 70.0 * N_CELLS / 2.0
    TT.PARAMS["cell_h_mm"] = 70.15 * N_CELLS / 2.0
    TT.PARAMS["cell_d_mm"] = 21.55
    TT.PARAMS["T_cell_max"] = 60.0
    TT.PARAMS["T_cut"] = t_cut
    TT.PARAMS["cell_area_frac"] = 0.5


def load_csv(path):
    lines = [ln for ln in open(path) if ln.strip() and not ln.startswith("#")]
    hdr = lines[0].strip().split(",")
    rows = [[float(x) if x else np.nan for x in ln.strip().split(",")] for ln in lines[1:]]
    a = np.array(rows, float)
    col = {h: i for i, h in enumerate(hdr)}
    im = np.array([a[:, col["im_rms_%d" % TT.SERVO_ID[n]]] for n in TT.NAMES]).T
    isup = np.array([a[:, col["isup_%d" % TT.SERVO_ID[n]]] for n in TT.NAMES]).T
    return dict(
        t=a[:, col["t_s"]],
        im=im,
        isup=isup,
        i_pack=a[:, col["i_pack"]],
        i_pack_rms=a[:, col["i_pack_rms"]],
        i_bec=a[:, col["i_bec_out"]],
        i_bec_rms=a[:, col["i_bec_rms"]],
        v_bec=a[:, col["v_bec_out"]],
    )


def groups_of(names):
    left = [i for i, n in enumerate(names) if n.startswith("left_")]
    right = [i for i, n in enumerate(names) if n.startswith("right_")]
    neck = [i for i, n in enumerate(names) if n.startswith("neck_") or n.startswith("head_")]
    return {"left_leg": left, "right_leg": right, "neck_and_head": neck}


def chafe_calc():
    """1 ohm nick from 12.6 V to ground. Same path as the playbook fault script."""
    r_path = 3 * 0.015 + 0.025 + 0.006 + 0.002 + 0.013 + 0.0088
    v = 12.6
    rows = []
    for r_nick in (1.0, 0.1, 0.05, 0.01):
        i = v / (r_path + r_nick)
        rows.append(dict(
            r_nick_ohm=r_nick,
            i_A=round(i, 2),
            p_nick_W=round(i * i * r_nick, 1),
            over_15A=bool(i > 15.0),
        ))
    # A nick on the servo bus sees the bus, not the open-circuit pack.
    # 11.0 V is the low end of the run C 0.15 m/s bus. Calc only.
    i_bus = 11.0 / (1.0 + 0.05)
    return dict(
        label="calc only",
        v_oc_V=v,
        r_path_ohm=round(r_path, 4),
        r_path_note="3 x 15 mOhm cells, BMS 25 mOhm max, fuse 6 mOhm, XT30 2 mOhm, switch 13 mOhm, wires 8.8 mOhm",
        rows=rows,
        bus_11V_1ohm_with_50mOhm_A=round(i_bus, 2),
        bus_note="calc only. A knee-lead nick after the BEC is not the 12.6 V pack node.",
    )


def atof_window(i_a, rating_a):
    """Where i sits on the ATOF 3-40 A table. No interpolation."""
    pct = i_a / rating_a
    below = None
    above = None
    for p, tmin, tmax in ATOF_3_TO_40:
        if pct + 1e-9 >= p:
            below = dict(percent=p, t_min_s=tmin, t_max_s=tmax)
        elif above is None:
            above = dict(percent=p, t_min_s=tmin, t_max_s=tmax)
    must_hold_100h = pct <= 1.10
    must_open = pct >= 1.35
    return dict(
        i_A=round(i_a, 3),
        rating_A=rating_a,
        percent_of_rating=round(100.0 * pct, 1),
        at_or_under_110pct_holds_100h=must_hold_100h,
        at_or_over_135pct_must_open=must_open,
        row_at_or_below=below,
        next_higher_row=above,
    )


def branch_currents(s):
    g = groups_of(TT.NAMES)
    scale = RUN_C["0.40_typical_100ms_A"] / OLD_PACK_100MS_A
    out = {}
    for name, idx in g.items():
        total = np.nansum(s["isup"][:, idx], axis=1)
        out[name] = dict(
            label="sim pass only, 5 s bins of the old backlash session",
            bin_mean_A=round(float(np.nanmean(total)), 3),
            bin_max_A=round(float(np.nanmax(total)), 3),
        )
    feeds = {}
    for name, peak in FEED_PEAK_A.items():
        feeds[name] = dict(
            old_100ms_peak_A=peak,
            label="sim pass only, 7.4 V budget in WIRES.md",
            scaled_to_runC_040_100ms_A=round(peak * scale, 3),
            scale_note="calc only. Peak times 13.081 / 7.04. The share may not survive the new gait.",
        )
    legs = {
        "left_SP1_plus_SP4": FEED_PEAK_A["SP1_left_hip"] + FEED_PEAK_A["SP4_left_ankle"],
        "right_SP2_plus_SP5": FEED_PEAK_A["SP2_right_hip"] + FEED_PEAK_A["SP5_right_ankle"],
        "neck_SP3": FEED_PEAK_A["SP3_neck"],
    }
    leg_scaled = {k: round(v * scale, 3) for k, v in legs.items()}
    return dict(
        session_bins=out,
        feed_peaks=feeds,
        sum_of_feed_peaks_A=legs,
        sum_of_feed_peaks_scaled_A=leg_scaled,
        scale_100ms=round(scale, 4),
        scale_note=(
            "calc only. 13.081 A run C 100 ms peak (sim pass only) divided by the "
            "7.04 A 100 ms pack figure on the old 16 AWG (sim pass only). "
            "Summing two feed peaks overstates a simultaneous current."
        ),
    )


def eFuse_check(i_chafe, i_branch):
    """TPS259827ONRGE, RILIM 182 ohm, the tabulated 8.13 A point.

    Cited, SLVSFE7, https://www.ti.com/lit/ds/symlink/tps25982.pdf
    ILIM at 182 ohm: 7.77 to 8.54 A at 25 C, 7.23 to 9.07 A from -40 C to 125 C.
    Fast trip is 210 percent of ILIM, typical only.
    ITIMER discharge 1.4 to 2.8 uA, delta V 0.7 to 1.3 V.
    t_ms = C_nF * dV / I_uA. That is calc only from those cited currents and volts.
    """
    ilim = dict(typ_25C=8.13, min_25C=7.77, max_25C=8.54, min_temp=7.23, max_temp=9.07)
    # Shortest blanking uses the fastest discharge. Longest uses the slowest.
    # 600 nF: shortest about 150 ms, so a 100 ms branch pulse can pass,
    # longest about 557 ms.
    c_nf = 600.0
    t_short = c_nf * 0.7 / 2.8
    t_long = c_nf * 1.3 / 1.4
    chafe_above_max = i_chafe > ilim["max_temp"]
    branch_under_min = i_branch < ilim["min_temp"]
    return dict(
        part="TPS259827ONRGE",
        mode="circuit breaker, no overvoltage lockout",
        r_ilim_ohm=182,
        ilim_A=ilim,
        i_chafe_A=round(i_chafe, 2),
        chafe_above_hottest_ILIM=chafe_above_max,
        i_branch_compare_A=round(i_branch, 3),
        branch_under_coldest_ILIM=branch_under_min,
        fast_trip_typical_A=round(2.10 * ilim["max_temp"], 2),
        fast_trip_note="210 percent of ILIM is typical. The chafe is under that, so it uses the blanking timer.",
        itimer_nF=c_nf,
        blanking_short_ms=round(t_short, 1),
        blanking_long_ms=round(t_long, 1),
        blanking_note=(
            "calc only. t_ms = C_nF * dV / I_uA from the cited ITIMER current and delta V. "
            "The startup cap limit equation did not extract cleanly from the PDF text. "
            "Whether 220 nF is under that limit is BLOCKER."
        ),
        ron_typ_mohm=2.7,
        drop_at_8A_mV=round(2.7 * 8.0, 1),
    )


def _cross(t, y, thr):
    m = np.where(np.asarray(y) >= thr)[0]
    if not len(m):
        return None
    return round(float(t[m[0]]) / 60.0, 2)


def summarize(r, heats, c, name):
    t = r["t"]
    jr = TT.NAMES.index("right_knee")
    bodies = {n: round(float(r["max_Tb"][j]), 2) for j, n in enumerate(TT.NAMES)}
    readings = {n: round(float(r["max_Ts"][j]), 2) for j, n in enumerate(TT.NAMES)}
    windings = {n: round(float(r["max_Tw"][j]), 2) for j, n in enumerate(TT.NAMES)}
    hot_name = max(bodies, key=bodies.get)
    # Mean trunk for the BEC case. Walk bins only.
    trunk_keys = [k for k in heats if k != "off"]
    bec = float(np.mean([heats[k]["trunk"]["bec"] for k in trunk_keys]))
    trunk = dict(heats[trunk_keys[0]]["trunk"])
    trunk["bec"] = bec
    hs = TT.hot_spots(trunk, float(r["trunk_air"][-1]), c, None)
    return dict(
        name=name,
        label="sim pass only",
        minutes=round(float(t[-1]) / 60.0, 2),
        walk_share=round(float(r["walk_share"]), 3),
        right_knee_reading_max_C=readings["right_knee"],
        right_knee_body_max_C=bodies["right_knee"],
        right_knee_winding_max_C=windings["right_knee"],
        minutes_to_right_reading_60C=_cross(t, r["Ts"][:, jr], 60.0),
        minutes_to_right_reading_70C=_cross(t, r["Ts"][:, jr], 70.0),
        minutes_to_right_body_49C=_cross(t, r["Tb"][:, jr], 49.0),
        hottest_body_servo=hot_name,
        hottest_body_C=bodies[hot_name],
        cell_max_C=round(float(r["cells"].max()), 2),
        wall_max_C=round(float(r["trunk_wall"].max()), 2),
        trunk_air_end_C=round(float(r["trunk_air"][-1]), 2),
        bec_case_end_C=round(float(hs["bec_case"]), 2),
        bec_loss_mean_W=round(bec, 3),
        bodies_C=bodies,
        readings_C=readings,
    )


def build_12v(s, sts, torque_scale, t_cut):
    apply_three_cell(t_cut)
    c = dict(TT.CORNERS["central"])
    scale_mean = sts["i_mean"] / float(np.nanmean(s["i_pack"]))
    scale_rms = sts["i_rms"] / float(np.nanmean(s["i_pack_rms"]))
    tbin = s["t"]
    heats = {}
    for i in range(len(tbin)):
        im = np.nan_to_num(s["im"][i]) * I_SCALE * torque_scale * c["cf"]
        i2 = im ** 2
        i_mean = float(s["i_pack"][i]) * scale_mean * torque_scale
        i_rms = float(s["i_pack_rms"][i]) * scale_rms * torque_scale
        i2p = i_rms * i_rms
        # 5 V branch: P5 / (eta * Vbus). eta is the mean of the Pololu 0.94 to 0.97 band.
        eta5 = float(np.mean(TT.PARAMS["eta_reg5"]))
        i5 = c["P5V"] / (eta5 * sts["bus_mean"])
        ib = max(i_mean - i5, 0.0)
        ib_rms = float(s["i_bec_rms"][i]) * scale_rms * torque_scale
        bec = ib * V_DROP
        trunk = dict(
            cells=N_CELLS * i2p * R_CELL,
            holder=i2p * c["R_holder"],
            bms=i2p * c["R_bms"],
            fuse=i2p * TT.PARAMS["R_fuse"],
            xt30=i2p * TT.PARAMS["R_xt30"],
            switch=i2p * TT.sw_R_on(sts["bus_mean"], c),
            wires=i2p * TT.PARAMS["R_wires"],
            bec=bec,
            bec_leads=ib_rms * ib_rms * 0.004,
            logic=0.15,
        )
        heats[i] = dict(
            servo=dict(i2=i2, P_cu25=i2 * R_W_12, P_board=i2 * R_BOARD_12, P_fric=np.zeros(14), P_idle=np.zeros(14)),
            trunk=trunk,
            head=c["P5V"],
        )
    z = np.zeros(14)
    # Torque-off current of the C018 is not on the page that was opened. 21 mA is the C001 idle.
    p_idle = 0.021 * sts["bec_out_mean"]
    i_off = 14 * 0.021
    heats["off"] = dict(
        servo=dict(i2=z, P_cu25=z, P_board=z, P_fric=z, P_idle=np.full(14, p_idle)),
        trunk=dict(
            cells=N_CELLS * i_off * i_off * R_CELL,
            holder=0.0, bms=0.0, fuse=0.0, xt30=0.0, switch=0.0, wires=0.0,
            bec=i_off * V_DROP, bec_leads=0.0, logic=0.15,
        ),
        head=c["P5V"],
    )
    meta = dict(
        i_scale=round(I_SCALE, 4),
        torque_scale=torque_scale,
        r_w_ohm=round(R_W_12, 3),
        r_board_ohm=round(R_BOARD_12, 3),
        pack_scale_mean=round(scale_mean, 4),
        pack_scale_rms=round(scale_rms, 4),
        right_knee_I_rms_first_bin_A=round(float(np.nan_to_num(s["im"][0, TT.NAMES.index("right_knee")]) * I_SCALE * torque_scale), 3),
        current_shape="Old backlash session, Kt-scaled. Not run C. Not a new closed-loop trace.",
        idle_on_rest="0.021 A, C001 sheet. C018 torque-off current is BLOCKER.",
        five_volt_split="P5V / (mean eta 0.94 to 0.97 times bus). Calc only.",
    )
    return heats, c, tbin, meta


def run_thermal(s):
    heats, c, tbin, meta = build_12v(s, STS12_PACK, 1.0, 200.0)
    n = len(tbin)

    def bin_at(t, tbin=tbin, n=n):
        return int(np.clip(np.searchsorted(tbin, t % (float(tbin[-1]) + 5.0)), 0, n - 1))

    def pattern_sched(pattern):
        per = sum(d for _, d in pattern)

        def f(t, per=per, pattern=pattern):
            x = t % per
            acc = 0.0
            for st, d in pattern:
                if x < acc + d:
                    if st == "off":
                        return "off"
                    return bin_at(t)
                acc += d
            return "off"

        return f

    jobs = []

    def add(name, sched, t_end, guard, a_scale, extra_c, torque, t_cut):
        jobs.append(dict(name=name, sched=sched, t_end=t_end, guard=guard, a_scale=a_scale,
                         extra_c=extra_c, torque=torque, t_cut=t_cut))

    add("v12_continuous_cut_off_25C", bin_at, 40 * 60.0, None, None, {}, 1.0, 200.0)
    add("v12_continuous_cut_70_25C", bin_at, 40 * 60.0, None, None, {}, 1.0, 70.0)
    add("v12_continuous_cut_70_32C", bin_at, 40 * 60.0, None, None, {}, 1.0, 70.0)
    home = [("walk", 90.0), ("off", 360.0)]
    add("home_90s_walk_6min_sit_25C", pattern_sched(home), 90 * 60.0, None, None, {}, 1.0, 70.0)
    add("home_90s_walk_6min_sit_32C", pattern_sched(home), 90 * 60.0, None, None, {}, 1.0, 70.0)
    add("guard_55_45_25C", bin_at, 90 * 60.0, dict(stop=55.0, resume=45.0, rest="off"), None, {}, 1.0, 70.0)
    add("guard_55_45_32C", bin_at, 90 * 60.0, dict(stop=55.0, resume=45.0, rest="off"), None, {}, 1.0, 70.0)
    add("guard_50_42_25C", bin_at, 90 * 60.0, dict(stop=50.0, resume=42.0, rest="off"), None, {}, 1.0, 70.0)
    knees = np.array([1.3 if "knee" in n else 1.0 for n in TT.NAMES])
    knees_big = np.array([1.8 if "knee" in n else 1.0 for n in TT.NAMES])
    add("sink_30pct_continuous_25C", bin_at, 40 * 60.0, None, knees, {}, 1.0, 70.0)
    add("spreader_80pct_continuous_25C", bin_at, 40 * 60.0, None, knees_big, {}, 1.0, 70.0)
    add("vents_continuous_25C", bin_at, 40 * 60.0, None, None, dict(G_vent=0.3), 1.0, 70.0)
    add("torque_0.70_continuous_25C", bin_at, 40 * 60.0, None, None, {}, 0.70, 70.0)
    add("torque_0.55_continuous_25C", bin_at, 40 * 60.0, None, None, {}, 0.55, 70.0)
    add("combo_guard55_and_sink30_25C", bin_at, 90 * 60.0, dict(stop=55.0, resume=45.0, rest="off"), knees, {}, 1.0, 70.0)
    add("combo_guard55_and_sink30_32C", bin_at, 90 * 60.0, dict(stop=55.0, resume=45.0, rest="off"), knees, {}, 1.0, 70.0)
    add("combo_home_and_sink30_25C", pattern_sched(home), 90 * 60.0, None, knees, {}, 1.0, 70.0)

    # Cache heats by (torque, t_cut). The cut is a PARAMS value, not part of the heat dict.
    cache = {}
    rows = []
    rooms = {
        "v12_continuous_cut_70_32C": 32.0,
        "home_90s_walk_6min_sit_32C": 32.0,
        "guard_55_45_32C": 32.0,
        "combo_guard55_and_sink30_32C": 32.0,
    }
    for job in jobs:
        key = (job["torque"], job["t_cut"])
        if key not in cache:
            cache[key] = build_12v(s, STS12_PACK, job["torque"], job["t_cut"])
        heats, c0, tbin, meta = cache[key]
        c = dict(c0)
        c.update(job["extra_c"])
        fan = 3.0 if job["extra_c"].get("G_vent") else 1.0
        Ta = rooms.get(job["name"], 25.0)
        r = TT.simulate(
            job["sched"], heats, None, c, Ta,
            t_end=job["t_end"], dt=0.5, guard=job["guard"],
            A_scale=job["a_scale"], trunk_fan=fan, record=10.0,
        )
        row = summarize(r, heats, c, job["name"])
        row["room_C"] = Ta
        row["t_cut_C"] = job["t_cut"]
        row["torque_scale"] = job["torque"]
        row["meta"] = meta
        rows.append(row)
        print(
            job["name"],
            "read", row["right_knee_reading_max_C"],
            "body", row["right_knee_body_max_C"],
            "t60", row["minutes_to_right_reading_60C"],
            "cell", row["cell_max_C"],
            "wall", row["wall_max_C"],
            "walk", row["walk_share"],
            flush=True,
        )
    return rows


def session_stats(s):
    jr = TT.NAMES.index("right_knee")
    # First 4 minutes is bins whose t_s is at most 240.
    m = s["t"] <= 240.0
    return dict(
        label="sim pass only",
        file="altaay_lab/twin/electromech/out/p45b_sheet/session_bam_backlash_typical.csv",
        minutes=round(float(s["t"][-1]) / 60.0, 2),
        right_knee_rms_first_4min_A=round(float(np.sqrt(np.nanmean(s["im"][m, jr] ** 2))), 3),
        right_knee_rms_all_A=round(float(np.sqrt(np.nanmean(s["im"][:, jr] ** 2))), 3),
        pack_mean_A=round(float(np.nanmean(s["i_pack"])), 3),
        pack_rms_mean_of_bins_A=round(float(np.nanmean(s["i_pack_rms"])), 3),
        pack_bin_max_A=round(float(np.nanmax(s["i_pack"])), 3),
    )


def main():
    s = load_csv(CSV)
    stats = session_stats(s)
    print("session", stats, flush=True)
    print("reproduce published walk", flush=True)
    TT.PARAMS["T_cut"] = 200.0
    published = G.run_walk(CSV, "central", 25.0, minutes=40.0)
    # Drop nothing large. The published function already returns a small dict.
    published["label"] = "sim pass only"
    TT.PARAMS["T_cut"] = 70.0
    published_cut = G.run_walk(CSV, "central", 25.0, minutes=40.0)
    published_cut["label"] = "sim pass only"
    published_cut["t_cut_C"] = 70.0
    print(
        "published with the 70 C cut",
        "knee60", published_cut["right_knee"]["minutes_to_60C"],
        "body", published_cut["right_knee"]["body_max_C"],
        "reading", published_cut["right_knee"]["reading_max_C"],
        flush=True,
    )
    print(
        "published knee60", published["right_knee"]["minutes_to_60C"],
        "body", published["right_knee"]["body_max_C"],
        "reading", published["right_knee"]["reading_max_C"],
        flush=True,
    )
    chafe = chafe_calc()
    branches = branch_currents(s)
    i_chafe = chafe["rows"][0]["i_A"]
    # Compare the eFuse with the hotter scaled sum-of-peaks, the conservative branch.
    i_branch = max(branches["sum_of_feed_peaks_scaled_A"].values())
    fuse_rows = {}
    for rating in (15.0, 10.0, 7.5, 5.0):
        fuse_rows[str(rating)] = dict(
            chafe=atof_window(i_chafe, rating),
            pack_peak_15_6=atof_window(RUN_C["0.40_typical_peak_A"], rating),
            pack_100ms_13_1=atof_window(RUN_C["0.40_typical_100ms_A"], rating),
            branch_scaled_max=atof_window(i_branch, rating),
        )
    efuse = eFuse_check(i_chafe, i_branch)
    print("thermal cases", flush=True)
    thermal = run_thermal(s)
    doc = dict(
        label="sim pass only or calc only, per row",
        session=stats,
        published_gate_p45b=published,
        published_with_70C_cut=published_cut,
        i_scale=round(I_SCALE, 4),
        kt_7v4=round(KT_7V4, 4),
        kt_12=KT_12,
        r_w_12_ohm=round(R_W_12, 3),
        chafe=chafe,
        branches=branches,
        atof=fuse_rows,
        efuse=efuse,
        run_c_pack_A=RUN_C,
        thermal=thermal,
        assumptions=[
            "C018 winding resistance is the C001 winding share times the C018 stall line. The C018 page does not print a winding resistance.",
            "0.30 V dropout is the lab assumption. Castle does not publish it.",
            "C018 torque-off current is not on the opened page. Rests use the C001 21 mA idle.",
            "Friction heat is omitted, which makes the knee slightly cool.",
            "The 12 V current shape is the old session scaled by Kt. It is not run C.",
            "Aluminum area factors of 1.3 and 1.8 are assumptions. The twin has no separate spreader node.",
            "Trunk vent 0.3 W/K and 3x inner convection are the assumptions already in the twin's mitigation table.",
        ],
    )
    json.dump(doc, open(OUT, "w"), indent=1)
    print("wrote", os.path.relpath(OUT, os.path.join(LAB, "..")))


if __name__ == "__main__":
    main()
