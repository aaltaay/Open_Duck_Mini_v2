"""Knee heat rerun for the cost-down study.

Reuses twin/thermal/twin_thermal.py simulate() and twin/thermal/gate_p45b.py run_walk.
Does not edit those files, does not train a policy, and does not run the shared lab gym.

The walk reproduction is the existing P45B backlash session (sim pass only) through the
existing thermal model. Candidate watts are calc only: sheet Kt and R applied to the
published right-knee RMS torque, and only when the sheet stall at 7.2 V can make that torque.
"""
import json
import os
import sys

import numpy as np

LAB = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
THERM = os.path.join(LAB, "twin", "thermal")
sys.path.insert(0, THERM)
import gate_p45b as G  # noqa: E402
import twin_thermal as TT  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(LAB, "twin", "electromech", "out", "p45b_sheet", "session_bam_backlash_typical.csv")
# sim/ADDED_MASS_SIM.md table 4, backlash, our build, right knee. Sim pass only.
T_KNEE_RMS = 2.19
# Feetech sheets already opened in SERVO_UPGRADE_OPTIONS.md and KNEE_HEAT_STUDY.md.
# kgf to N uses 0.0980665, so 50 kg.cm is 4.903 Nm. The knee twin rounds that to 4.90.
KGF_CM = 0.0980665


def nm(kgcm):
    return kgcm * KGF_CM


def cross(t, y, thr):
    m = np.where(np.asarray(y) >= thr)[0]
    if not len(m):
        return None
    return round(float(t[m[0]]) / 60.0, 2)


def constant_knee(p_cu, ta, minutes, cut_c, p_board=0.0):
    """One right knee at a fixed copper wattage. Other servos idle. Central corner.
    The knee is outside the trunk, so trunk watts are left at 0. Friction is omitted,
    the same omission KNEE_HEAT_STUDY.md already states.

    Maxima come from the integrator (max_Ts, max_Tb, max_Tw), not from the stored
    samples. The 70 C time is t_cut when that is the configured cut. The 60 C time
    is taken from a record at the integration step, so a cut between samples cannot
    hide the crossing."""
    TT.PARAMS["T_cut"] = cut_c
    z = np.zeros(14)
    j = TT.NAMES.index("right_knee")
    pcu = z.copy()
    pcu[j] = p_cu
    pb = z.copy()
    pb[j] = p_board
    servo = dict(i2=z, P_cu25=pcu, P_board=pb, P_fric=z.copy(), P_idle=np.full(14, 0.021 * 7.2))
    trunk = {k: 0.0 for k in (
        "cells", "holder", "bms", "fuse", "xt30", "switch", "wires", "bec", "bec_leads", "logic")}
    heats = {"walk": dict(servo=servo, trunk=trunk, head=0.0)}
    dt = 0.5
    r = TT.simulate(lambda t: "walk", heats, None, TT.CORNERS["central"], ta,
                    t_end=minutes * 60.0, dt=dt, record=dt)
    t_cut = float(r["t_cut"][j])
    if cut_c <= 70.0 and np.isfinite(t_cut):
        minutes_70 = round(t_cut / 60.0, 2)
    else:
        minutes_70 = cross(r["t"], r["Ts"][:, j], 70.0)
    return dict(reading_max_C=round(float(r["max_Ts"][j]), 2),
                body_max_C=round(float(r["max_Tb"][j]), 2),
                winding_max_C=round(float(r["max_Tw"][j]), 2),
                minutes_to_60C=cross(r["t"], r["Ts"][:, j], 60.0),
                minutes_to_70C=minutes_70,
                cut_C=cut_c, room_C=ta, P_cu_W=round(p_cu, 3))


def at_torque(name, t_stall_72, kt, r_ohm, t_nm=T_KNEE_RMS):
    """Current and copper if this servo holds t_nm. None when stall is short of that torque."""
    if t_stall_72 + 1e-9 < t_nm:
        return None
    i = t_nm / kt
    return dict(servo=name, I_A=round(i, 3), R_ohm=r_ohm, P_cu_W=round(i * i * r_ohm, 3),
                note="calc only, RMS torque held, speed term left out")


def main():
    rows = []
    # Reproduction of the published log. gate_p45b leaves the torque cut at 200 C so the
    # clock can be read. That is the same choice as the published 3.3 minute run.
    TT.PARAMS["T_cut"] = 200.0
    for ta in (25.0, 32.0):
        w = G.run_walk(CSV, "central", ta, minutes=40.0)
        k = w["right_knee"]
        rows.append(dict(case="reproduce_p45b_backlash_log", label="sim pass only input, model calc",
                         room_C=ta, **k, cells_max_C=w["cells_max_C"]))
        print("log", ta, k, flush=True)

    # C001 cannot make 2.19 Nm. The log current is the trained actuator, not this sheet motor.
    # A stall hold is recorded so the sheet motor's own heat is not confused with the log.
    rows.append(constant_knee(2.5 * 2.5 * 2.5, 25.0, 20.0, 70.0) | dict(
        case="c001_sheet_stall_hold", label="calc only",
        note="2.5 A and 2.5 ohm, sheet stall, not a walk"))
    print("stall hold", rows[-1], flush=True)

    # STS3250 sheet A/0. Two resistances, because 1.2 ohm and 12 V / 4.2 A disagree.
    # Stall and no-load scaled linearly with voltage, the same estimate KNEE_TWIN.md uses.
    stall_12 = nm(50)
    kt_pub = nm(11)          # 11 kg.cm/A
    kt_stall = stall_12 / 4.2
    r_stall = 12.0 / 4.2
    stall_72 = stall_12 * (7.2 / 12.0)
    jobs = [
        ("sts3250_sheet_R_at_sim_torque", kt_pub, 1.2),
        ("sts3250_stall_line_R_at_sim_torque", kt_stall, r_stall),
    ]
    for name, kt, r in jobs:
        h = at_torque(name, stall_72, kt, r)
        print(name, "stall72", round(stall_72, 3), h, flush=True)
        for ta in (25.0, 32.0):
            rec = constant_knee(h["P_cu_W"], ta, 40.0, 70.0)
            rec.update(case=name, label="calc only", I_A=h["I_A"], R_ohm=r, stall_7v2_Nm=round(stall_72, 3))
            rows.append(rec)
            print(" ", ta, rec["minutes_to_60C"], rec["reading_max_C"], flush=True)

    # Knee-twin walking currents (sim pass only): 0.71 to 0.88 A, not the 2.19 Nm hold.
    for i_a, tag in ((0.71, "low"), (0.88, "high")):
        for r, rtag in ((1.2, "sheetR"), (r_stall, "stallR")):
            p = i_a * i_a * r
            rec = constant_knee(p, 32.0, 40.0, 70.0)
            rec.update(case="sts3250_knee_twin_current_%s_%s" % (tag, rtag),
                       label="sim current, calc copper", I_A=i_a, R_ohm=round(r, 3))
            rows.append(rec)
            print(rec["case"], rec["minutes_to_60C"], rec["reading_max_C"], flush=True)

    # Rated point, the cool reference already in KNEE_HEAT_STUDY.md.
    rec = constant_knee(0.65 * 0.65 * 2.5, 25.0, 40.0, 70.0)
    rec.update(case="c001_rated_0.65A", label="calc only")
    rows.append(rec)
    print("rated", rec["reading_max_C"], flush=True)

    out = dict(reuse=["twin/thermal/twin_thermal.py simulate", "twin/thermal/gate_p45b.py run_walk",
                      "twin/electromech/out/p45b_sheet/session_bam_backlash_typical.csv"],
               torque_Nm=T_KNEE_RMS, torque_source="sim/ADDED_MASS_SIM.md table 4, backlash, our build, right knee",
               rows=rows)
    dest = os.path.join(HERE, "knee_heat_results.json")
    json.dump(out, open(dest, "w"), indent=1)
    print("wrote", dest)


if __name__ == "__main__":
    main()
