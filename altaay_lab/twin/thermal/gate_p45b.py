"""Thermal cases for the P45B pack, the STS3215 operating range, and the D61 charger in the trunk.

This does not re-run the walking policy. The sit-and-charge case is the thermal model with the
servos at idle (torque off, data sheet idle current) and the charger heat added in the trunk.
The walk case uses motor current from a closed-loop session CSV when one is named.

Every temperature here is sim pass only. The charger watts are the calc-only band from D61
(1.9 W at a 7.2 V pack, 3.2 W at a 6.0 V pack, MCP73213 linear charger). The cell numbers are
the opened P45B sheet (version 1.2). The servo limit is the opened STS3215 operating range,
-20 C to 60 C. The same sheet turns torque off above 70 C (item 7-11); that line is reported too.

Run from the repo root:
  python3 altaay_lab/twin/thermal/gate_p45b.py [session.csv ...]
With no CSV it uses the P45B backlash typical session. That file must have i_pack_rms and i_bec_rms.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import twin_thermal as TT  # noqa: E402

# P45B sheet, version 1.2. Specific heat is not on that sheet: the 18650 range already in the model stays,
# and it is a GUESS for this cell. The can area fraction is the same ASSUMPTION as the first thermal run.
TT.PARAMS["R_cell"] = 0.015
TT.PARAMS["m_cell_g"] = 70.0
TT.PARAMS["T_cell_max"] = 60.0
TT.PARAMS["cell_d_mm"] = 21.55
TT.PARAMS["cell_h_mm"] = 70.15
TT.PARAMS["T_cut"] = 200.0          # do not unload; report the time the reading crosses 60 C and 70 C
V_BUS = 7.2
I_IDLE = 0.021                      # STS3215 item 5-6
I_CHARGE = 1.0                      # MCP73213 on the EV board, D61
# BEC efficiency is not published. 0.85 is the lab assumption already used in this thermal model.
ETA_BEC = 0.85
OUT = os.path.join(HERE, "gate_p45b.json")
OLD_CSV = os.path.join(HERE, "..", "electromech", "out", "p45b_sheet", "session_bam_backlash_typical.csv")


def _cross(t, y, thr):
    m = np.where(np.asarray(y) >= thr)[0]
    if not len(m):
        return None
    return round(float(t[m[0]]) / 60.0, 2)


def _idle_servo():
    p = I_IDLE * V_BUS
    z = np.zeros(14)
    return dict(P_cu25=z, P_board=z, P_fric=z.copy(), P_idle=np.full(14, p), i2=z)


def _trunk_sit(charger_w, c):
    """trunk watts while docked, torque off, pack charging at 1.0 A"""
    p_servo = 14 * I_IDLE * V_BUS
    bec_loss = p_servo * (1.0 / ETA_BEC - 1.0)     # GUESS: the walking efficiency applied at idle
    i = I_CHARGE
    return dict(cells=2 * i * i * TT.PARAMS["R_cell"], holder=i * i * c["R_holder"], bms=i * i * c["R_bms"],
                fuse=i * i * TT.PARAMS["R_fuse"], xt30=i * i * TT.PARAMS["R_xt30"], switch=0.0, wires=i * i * TT.PARAMS["R_wires"],
                bec=bec_loss, bec_leads=0.0, logic=0.15, charger=charger_w)


def run_sit(charger_w, corner, Ta, hours=6.0):
    c = TT.CORNERS[corner]
    # "stand" is a stationary key in twin_thermal.simulate (walking air only for other keys). The duck is sitting still.
    key = "stand"
    heats = {key: dict(servo=_idle_servo(), trunk=_trunk_sit(charger_w, c), head=c["P5V"])}
    r = TT.simulate(lambda t: key, heats, None, c, Ta, t_end=hours * 3600.0, dt=2.0, record=30.0)
    t = r["t"]
    j = [TT.NAMES.index(n) for n in ("left_knee", "right_knee")]
    ts = r["Ts"][:, j].max(1)
    tb = r["Tb"][:, j].max(1)
    hs = TT.hot_spots(heats[key]["trunk"], float(r["trunk_air"][-1]), c, None)
    return dict(charger_W=charger_w, corner=corner, room_C=Ta, hours=hours,
                cell_end_C=round(float(r["cells"][-1]), 2), cell_max_C=round(float(r["cells"].max()), 2),
                trunk_air_end_C=round(float(r["trunk_air"][-1]), 2), trunk_wall_end_C=round(float(r["trunk_wall"][-1]), 2),
                trunk_wall_max_C=round(float(r["trunk_wall"].max()), 2),
                knee_reading_max_C=round(float(ts.max()), 2), knee_body_max_C=round(float(tb.max()), 2),
                head_air_end_C=round(float(r["head_air"][-1]), 2),
                bec_case_end_C=round(float(hs["bec_case"]), 2),
                minutes_to_servo_60C=_cross(t, ts, 60.0), minutes_to_servo_70C=_cross(t, ts, 70.0),
                minutes_to_cell_60C=_cross(t, r["cells"], 60.0),
                minutes_to_wall_49C=_cross(t, r["trunk_wall"], 49.0),
                minutes_to_wall_55C=_cross(t, r["trunk_wall"], 55.0))


def _csv_walk(path):
    lines = [ln for ln in open(path) if ln.strip() and not ln.startswith("#")]
    hdr = lines[0].strip().split(",")
    rows = [[float(x) if x else np.nan for x in ln.strip().split(",")] for ln in lines[1:]]
    A = np.array(rows, float)
    col = {h: i for i, h in enumerate(hdr)}
    im = np.array([A[:, col["im_rms_%d" % TT.SERVO_ID[n]]] for n in TT.NAMES]).T
    if "i_pack_rms" not in col or "i_bec_rms" not in col:
        raise SystemExit("session CSV %s has no RMS current columns; I^2R needs them" % path)
    return dict(t=A[:, col["t_s"]], im=im, i_pack=A[:, col["i_pack_rms"]], i_bec=A[:, col["i_bec_rms"]],
                i_pack_mean=A[:, col["i_pack"]], i_bec_mean=A[:, col["i_bec_out"]], v_bec=A[:, col["v_bec_out"]])


def run_walk(path, corner, Ta, minutes=40.0):
    """knee and cells from a session CSV. Copper uses the 2.5 ohm winding. The CSV current is whatever servo
    produced that file. Friction heat is not in the bins, so it is left out (the knee then runs slightly cool)."""
    S = _csv_walk(path)
    c = TT.CORNERS[corner]
    # the stored bins are 5 s. Map each sim time to a bin.
    tbin = S["t"]
    R_bam = 2.630               # the resistance the 2026-11-03 session used for Pcu (servo_sts3215.py BAM R_M)
    # board loss uses that same resistance minus the winding, so a new sheet session (R 2.96) is handled if
    # the file lives under p45b_sheet
    # a file whose name says sheet was integrated with the sheet stall resistance; the bam sessions use 2.630 ohm
    r_loop = 2.96 if "sheet" in os.path.basename(path) else R_bam

    def sched(t, tbin=tbin):
        return int(np.clip(np.searchsorted(tbin, t), 0, len(tbin) - 1))

    heats = {}
    for i in range(len(tbin)):
        i2 = np.nan_to_num(S["im"][i]) ** 2 * c["cf"] ** 2
        ip = float(S["i_pack"][i])          # RMS, for every I^2 R term
        ib = float(S["i_bec"][i])            # RMS, for the BEC lead I^2 R
        vb = float(S["v_bec"][i])
        # converter loss follows mean output power, not the square of the mean current
        bec_loss = max(vb * float(S["i_bec_mean"][i]), 0.0) * (1.0 / c["eta_bec"] - 1.0)
        trunk = dict(cells=2 * ip * ip * TT.PARAMS["R_cell"], holder=ip * ip * c["R_holder"], bms=ip * ip * c["R_bms"],
                     fuse=ip * ip * TT.PARAMS["R_fuse"], xt30=ip * ip * TT.PARAMS["R_xt30"],
                     switch=ip * ip * TT.sw_R_on(vb + 0.3, c), wires=ip * ip * TT.PARAMS["R_wires"],
                     bec=bec_loss, bec_leads=ib * ib * 0.004, logic=0.15)
        servo = dict(i2=i2, P_cu25=i2 * TT.PARAMS["R_w25"], P_board=i2 * max(r_loop - TT.PARAMS["R_w25"], 0.0),
                     P_fric=np.zeros(14), P_idle=np.full(14, I_IDLE * vb))
        heats[i] = dict(servo=servo, trunk=trunk, head=c["P5V"])
    t_end = min(float(tbin[-1]), minutes * 60.0)
    r = TT.simulate(sched, heats, None, c, Ta, t_end=t_end, dt=0.5, record=10.0)
    t = r["t"]
    out = dict(csv=os.path.basename(path), corner=corner, room_C=Ta, minutes=round(t_end / 60.0, 2),
               r_loop_ohm=r_loop, friction_heat="omitted, not in the session bins")
    for n in ("left_knee", "right_knee", "left_ankle", "right_ankle", "head_roll"):
        j = TT.NAMES.index(n)
        out[n] = dict(reading_max_C=round(float(r["max_Ts"][j]), 2), body_max_C=round(float(r["max_Tb"][j]), 2),
                      winding_max_C=round(float(r["max_Tw"][j]), 2),
                      minutes_to_60C=_cross(t, r["Ts"][:, j], 60.0), minutes_to_70C=_cross(t, r["Ts"][:, j], 70.0))
    out["cells_max_C"] = round(float(r["cells"].max()), 2)
    out["trunk_wall_max_C"] = round(float(r["trunk_wall"].max()), 2)
    out["trunk_air_max_C"] = round(float(r["trunk_air"].max()), 2)
    out["minutes_to_cell_60C"] = _cross(t, r["cells"], 60.0)
    out["minutes_to_wall_49C"] = _cross(t, r["trunk_wall"], 49.0)
    return out


def main():
    csvs = sys.argv[1:] or [OLD_CSV]
    sit = []
    for w in (1.9, 3.2):
        for corner in ("central", "high"):
            for Ta in (25.0, 32.0):
                row = run_sit(w, corner, Ta)
                sit.append(row)
                print("sit", w, corner, Ta, "cell", row["cell_end_C"], "wall", row["trunk_wall_end_C"],
                      "knee", row["knee_reading_max_C"], "bec", row["bec_case_end_C"], flush=True)
    walk = []
    for path in csvs:
        for corner in ("central", "high"):
            for Ta in (25.0, 32.0):
                row = run_walk(path, corner, Ta)
                walk.append(row)
                k = row["right_knee"]
                print("walk", os.path.basename(path), corner, Ta, "knee60", k["minutes_to_60C"],
                      "knee max", k["reading_max_C"], "body", k["body_max_C"], "cell", row["cells_max_C"],
                      "wall", row["trunk_wall_max_C"], flush=True)
    doc = dict(label="sim pass only", cell="Molicel INR21700-P45B version 1.2",
               servo_operating_C=[-20, 60], servo_torque_off_C=70,
               charger_W=[1.9, 3.2], charger_note="calc only, D61, MCP73213 linear",
               guesses=["cell specific heat is the 18650 range already in twin_thermal.py, not on the P45B sheet",
                        "half the can faces the bay air",
                        "BEC efficiency 0.85, Castle publishes none",
                        "charger has no seated part, so the PLA reported for it is the trunk wall node",
                        "walk friction heat is not in the session bins and is omitted"],
               pla_band_C=dict(HDT_0p45_MPa=[49, 57], Tg=[55, 60], vicat_overture_easy_pla=66.2,
                               source="the bands already cited in THERMAL_TWIN.md"),
               sit=sit, walk=walk)
    json.dump(doc, open(OUT, "w"), indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
