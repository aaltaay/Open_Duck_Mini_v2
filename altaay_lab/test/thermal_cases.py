"""Shared thermal cases for the test playbook.

Uses twin/thermal/twin_thermal.py and the P45B setup in gate_p45b.py.
Does not edit those models. simulate() still assumes two cans, so a three-cell
run scales mass and can height by 3/2, the same method as gate_bq24133.py.

Every temperature this module returns is sim pass only. Currents taken from
problems/sts12.json are sim pass only. The 0.30 V dropout and the 0.85 BEC
efficiency are the lab assumptions (Castle publishes neither).
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, ".."))
THERM = os.path.join(LAB, "twin", "thermal")
if THERM not in sys.path:
    sys.path.insert(0, THERM)

import twin_thermal as TT  # noqa: E402
import gate_p45b as G  # noqa: E402

# Cited sheet and sim inputs. Stall torque 19.5 kg.cm is the opened STS3215
# C001 line used by the electromechanical twin. 0.0980665 N.m per kg.cm.
STALL_NM_7V4 = 19.5 * 0.0980665
I_STALL_7V4 = 2.5  # twin_thermal.PARAMS I_stall, the C001 line the model uses
KT_7V4 = STALL_NM_7V4 / I_STALL_7V4  # calc only
R_LOOP_7V4 = 2.96  # gate_p45b sheet session loop, ohm
R_W_7V4 = 2.5  # twin_thermal winding share of that loop, ohm
V_SET_12 = 12.0
V_DROP = 0.3  # lab assumption, unpublished
V_REG_MIN = V_SET_12 + V_DROP  # input needed before a 12.0 V setpoint can hold
N_CELLS = 3
R_CELL = 0.015
M_CELL = 70.0
H_CELL = 70.15
I_IDLE_C001 = 0.021  # STS3215 C001 sheet idle. Not the C018 no-load current.
I_NL_C018 = 0.180  # C018 no-load current at 12 V, cited. Running, not torque-off.
ETA5 = float(np.mean(TT.PARAMS["eta_reg5"]))


def apply_two_cell():
    """P45B can, two of them, matching gate_p45b (simulate multiplies by 2)."""
    TT.PARAMS["R_cell"] = R_CELL
    TT.PARAMS["m_cell_g"] = M_CELL
    TT.PARAMS["cell_h_mm"] = H_CELL
    TT.PARAMS["cell_d_mm"] = 21.55
    TT.PARAMS["T_cell_max"] = 60.0
    TT.PARAMS["T_cut"] = 200.0
    TT.PARAMS["cell_area_frac"] = 0.5


def apply_three_cell():
    """Three P45B cans via the 3/2 scale gate_bq24133 already uses."""
    TT.PARAMS["R_cell"] = R_CELL
    TT.PARAMS["m_cell_g"] = M_CELL * N_CELLS / 2.0
    TT.PARAMS["cell_h_mm"] = H_CELL * N_CELLS / 2.0
    TT.PARAMS["cell_d_mm"] = 21.55
    TT.PARAMS["T_cell_max"] = 60.0
    TT.PARAMS["T_cut"] = 200.0
    TT.PARAMS["cell_area_frac"] = 0.5


def load_sts12():
    import json
    path = os.path.join(LAB, "problems", "sts12.json")
    doc = json.load(open(path))
    return doc


def pack_corner(doc, name):
    p = doc["corners"][name]["pack"]
    return dict(
        i_mean=float(p["i_mean"]),
        i_rms=float(p["i_rms"]),
        i_max=float(p["i_max"]),
        v_term_mean=float(p["v_term_mean"]),
        v_term_min=float(p["v_term_min"]),
        bus_mean=float(p["bus_mean"]),
        bus_min=float(p["bus_min"]),
        bec_out_mean=float(p["bec_out_mean"]),
        bec_out_min=float(p["bec_out_min"]),
        bec_in_min=float(p["bec_in_min"]),
    )


def bec_split(i_pack, v_bus, p5):
    """BEC output current after the 5 V branch is taken off the pack current.

    Calc only. The 5 V current is P5 / (eta * Vbus). eta is the mean of the
    Pololu D30V30F5 band already in the thermal model (0.94 to 0.97).
    """
    i5 = p5 / (ETA5 * v_bus)
    i_bec = max(i_pack - i5, 0.0)
    return dict(i5_A=i5, i_bec_A=i_bec, p5_W=p5, eta5=ETA5)


def dropout_loss_w(i_bec):
    return i_bec * V_DROP


def regulate_loss_w(i_bec, eta, v_set=V_SET_12):
    p_out = v_set * i_bec
    return p_out * (1.0 / eta - 1.0), p_out


def _cross(t, y, thr):
    m = np.where(np.asarray(y) >= thr)[0]
    if not len(m):
        return None
    return round(float(t[m[0]]) / 60.0, 2)


def _end_summary(r, heats, key, c):
    t = r["t"]
    j = [TT.NAMES.index(n) for n in ("left_knee", "right_knee")]
    ts = r["Ts"][:, j].max(1)
    tb = r["Tb"][:, j].max(1)
    tw = r["Tw"][:, j].max(1)
    trunk = heats[key]["trunk"] if isinstance(key, str) else heats[0]["trunk"]
    # hot_spots wants one loss dict. Callers that vary the loss pass the mean
    # through heats[key] already.
    hs = TT.hot_spots(trunk, float(r["trunk_air"][-1]), c, None)
    jr = TT.NAMES.index("right_knee")
    return dict(
        cell_end_C=round(float(r["cells"][-1]), 2),
        cell_max_C=round(float(r["cells"].max()), 2),
        trunk_air_end_C=round(float(r["trunk_air"][-1]), 2),
        trunk_wall_end_C=round(float(r["trunk_wall"][-1]), 2),
        trunk_wall_max_C=round(float(r["trunk_wall"].max()), 2),
        knee_reading_max_C=round(float(ts.max()), 2),
        knee_body_max_C=round(float(tb.max()), 2),
        knee_winding_max_C=round(float(tw.max()), 2),
        right_knee_reading_max_C=round(float(r["max_Ts"][jr]), 2),
        bec_case_end_C=round(float(hs["bec_case"]), 2),
        minutes_to_reading_60C=_cross(t, ts, 60.0),
        minutes_to_reading_70C=_cross(t, ts, 70.0),
        minutes_to_cell_60C=_cross(t, r["cells"], 60.0),
        minutes_to_wall_49C=_cross(t, r["trunk_wall"], 49.0),
        head_air_end_C=round(float(r["head_air"][-1]), 2),
    )


def sit(charger_w, v_servo, i_per_servo, i_chg, corner, room_c, hours=6.0, n_cells=3):
    """Docked sit. v_servo 0 and i_per_servo 0 is the cut rail."""
    if n_cells == 3:
        apply_three_cell()
    else:
        apply_two_cell()
    c = TT.CORNERS[corner]
    z = np.zeros(14)
    p_idle = i_per_servo * v_servo
    i_srv = 14.0 * i_per_servo
    bec = i_srv * V_DROP
    servo = dict(P_cu25=z, P_board=z, P_fric=z.copy(), P_idle=np.full(14, p_idle), i2=z)
    trunk = dict(
        cells=n_cells * i_chg * i_chg * R_CELL,
        holder=i_chg * i_chg * c["R_holder"],
        bms=i_chg * i_chg * c["R_bms"],
        fuse=i_chg * i_chg * TT.PARAMS["R_fuse"],
        xt30=i_chg * i_chg * TT.PARAMS["R_xt30"],
        switch=0.0,
        wires=i_chg * i_chg * TT.PARAMS["R_wires"],
        bec=bec,
        bec_leads=0.0,
        logic=0.15,
        charger=charger_w,
    )
    key = "stand"
    heats = {key: dict(servo=servo, trunk=trunk, head=c["P5V"])}
    r = TT.simulate(lambda t: key, heats, None, c, room_c, t_end=hours * 3600.0, dt=2.0, record=120.0)
    out = _end_summary(r, heats, key, c)
    out.update(
        label="sim pass only",
        corner=corner,
        room_C=room_c,
        hours=hours,
        charger_W=charger_w,
        v_servo=v_servo,
        i_per_servo_A=i_per_servo,
        bec_loss_W=round(bec, 4),
        n_cells=n_cells,
    )
    return out


def _csv_arrays(path):
    lines = [ln for ln in open(path) if ln.strip() and not ln.startswith("#")]
    hdr = lines[0].strip().split(",")
    rows = [[float(x) if x else np.nan for x in ln.strip().split(",")] for ln in lines[1:]]
    a = np.array(rows, float)
    col = {h: i for i, h in enumerate(hdr)}
    im = np.array([a[:, col["im_rms_%d" % TT.SERVO_ID[n]]] for n in TT.NAMES]).T
    return dict(
        t=a[:, col["t_s"]],
        im=im,
        i_pack=a[:, col["i_pack"]],
        i_bec=a[:, col["i_bec_out"]],
        v_bec=a[:, col["v_bec_out"]],
    )


def session_regulating_loss(path, eta=0.85):
    """Mean BEC loss if that session's output power is buck-regulated at eta.

    The p45b_sheet CSV is the 7.2 V bus session (pack near 8.2 V). This is the
    loss model behind the old 109 C case. It is not the 12 V walk.
    """
    s = _csv_arrays(path)
    p_out = np.maximum(s["v_bec"] * s["i_bec"], 0.0)
    loss = p_out * (1.0 / eta - 1.0)
    return dict(
        label="calc only from sim pass only session currents",
        csv=os.path.basename(path),
        eta=eta,
        v_bec_mean=round(float(np.nanmean(s["v_bec"])), 3),
        i_bec_mean_A=round(float(np.nanmean(s["i_bec"])), 3),
        p_out_mean_W=round(float(np.nanmean(p_out)), 2),
        loss_mean_W=round(float(np.nanmean(loss)), 2),
        i_pack_mean_A=round(float(np.nanmean(s["i_pack"])), 3),
    )


def walk_scaled(path, corner, room_c, sts_pack, mode, minutes=40.0):
    """Continuous walk on the sheet-session current shape.

    Motor current is scaled by Kt_7.4 / Kt_12 so the same torque maps onto the
    C018 stall line (calc only). Pack current is scaled so its mean matches the
    STS12 corner (calc only). This is not a new closed-loop trace and not run C.

    mode "dropout": loss = I_bec * 0.30 V. This is the 12.0 V setpoint on the
    STS12 walk, because that walk's BEC input stays under 12.3 V.
    mode "regulate": loss = Pout * (1/eta - 1) at 12.0 V. The STS12 walk does
    not enter this regime. It is a bound only.
    """
    apply_three_cell()
    c = TT.CORNERS[corner]
    s = _csv_arrays(path)
    kt12 = 1.0896  # problems/sts12.json sheet.kt_Nm_per_A
    i_scale = KT_7V4 / kt12
    r_w = 4.444 * (R_W_7V4 / R_LOOP_7V4)
    r_board = 4.444 - r_w
    scale_pack = sts_pack["i_mean"] / float(np.nanmean(s["i_pack"]))
    split0 = bec_split(sts_pack["i_mean"], sts_pack["bus_mean"], c["P5V"])
    tbin = s["t"]

    def sched(t, tbin=tbin):
        return int(np.clip(np.searchsorted(tbin, t % (tbin[-1] + 5.0)), 0, len(tbin) - 1))

    heats = {}
    losses = []
    for i in range(len(tbin)):
        im = np.nan_to_num(s["im"][i]) * i_scale * c["cf"]
        i2 = im ** 2
        ip = float(s["i_pack"][i]) * scale_pack
        sp = bec_split(ip, sts_pack["bus_mean"], c["P5V"])
        ib = sp["i_bec_A"]
        if mode == "dropout":
            bec = dropout_loss_w(ib)
            v_srv = sts_pack["bec_out_mean"]
        elif mode == "regulate":
            bec, _p = regulate_loss_w(ib, c["eta_bec"])
            v_srv = V_SET_12
        else:
            raise ValueError(mode)
        losses.append(bec)
        trunk = dict(
            cells=N_CELLS * ip * ip * R_CELL,
            holder=ip * ip * c["R_holder"],
            bms=ip * ip * c["R_bms"],
            fuse=ip * ip * TT.PARAMS["R_fuse"],
            xt30=ip * ip * TT.PARAMS["R_xt30"],
            switch=ip * ip * TT.sw_R_on(sts_pack["bus_mean"], c),
            wires=ip * ip * TT.PARAMS["R_wires"],
            bec=bec,
            bec_leads=ib * ib * 0.004,
            logic=0.15,
        )
        # Idle is not added. The session current already includes the motor
        # current. C018's 180 mA no-load is a running figure, not a second term.
        servo = dict(
            i2=i2,
            P_cu25=i2 * r_w,
            P_board=i2 * r_board,
            P_fric=np.zeros(14),
            P_idle=np.zeros(14),
        )
        heats[i] = dict(servo=servo, trunk=trunk, head=c["P5V"], v_srv=v_srv)
    t_end = min(float(tbin[-1]), minutes * 60.0)
    r = TT.simulate(sched, heats, None, c, room_c, t_end=t_end, dt=0.5, record=10.0)
    # Case temperature from the mean BEC loss and the air at the end.
    mean_trunk = dict(heats[0]["trunk"])
    mean_trunk["bec"] = float(np.mean(losses))
    heats_mean = {0: dict(trunk=mean_trunk)}
    summary = _end_summary(r, heats_mean, 0, c)
    summary.update(
        label="sim pass only",
        mode=mode,
        corner=corner,
        room_C=room_c,
        minutes=round(t_end / 60.0, 2),
        i_scale=round(i_scale, 4),
        kt_7v4_Nm_per_A=round(KT_7V4, 4),
        kt_12_Nm_per_A=kt12,
        r_w_ohm=round(r_w, 3),
        r_board_ohm=round(r_board, 3),
        pack_scale=round(scale_pack, 4),
        i_bec_mean_A=round(split0["i_bec_A"], 3),
        bec_loss_mean_W=round(float(np.mean(losses)), 3),
        friction_heat="omitted, not in the session bins",
        current_shape="2S sheet session, scaled. Not run C. Not a 12 V closed-loop trace.",
        n_cells=3,
    )
    return summary
