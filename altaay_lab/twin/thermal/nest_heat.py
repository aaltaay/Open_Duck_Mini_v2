#!/usr/bin/env python3
"""Docked and awake, with the BQ24133 loss in the trunk. Sim pass only for the shell.

Three P45B cells. The model stores two cans, so mass and can height are scaled
by 3/2, the same scale as BQ24133_HEAT.md. Servos idle at 12.0 V. The head
uses the corner's existing P5V, which is the awake electronics already in the
thermal twin. A 25 W Pi 5 is not that number.

  python3 altaay_lab/twin/thermal/nest_heat.py
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import twin_thermal as TT  # noqa: E402

# P45B version 1.2, via gate_p45b.py. Three cells through the two-can node.
TT.PARAMS["R_cell"] = 0.015
TT.PARAMS["m_cell_g"] = 70.0 * 1.5
TT.PARAMS["T_cell_max"] = 60.0
TT.PARAMS["cell_d_mm"] = 21.55
TT.PARAMS["cell_h_mm"] = 70.15 * 1.5
TT.PARAMS["T_cut"] = 200.0

V_BUS = 12.0
I_IDLE = 0.021
I_CHG = 1.006
ETA_CHG = 0.929          # chart read, BQ24133_HEAT.md Figure 10-4
ETA_I7C = 0.94           # cited low end, POWER.md section 12
ETA_5V = 0.94            # cited low end of the D30V30F5 band used in AWAKE_LOAD.md
NEST_V = 15.0
DIODE_VF = 0.50          # cited max at 5 A, MBRS540T3/D. Upper bound at a lower current.
V_PACK = 12.6
# Loss is Vbat * I * (1/eta - 1). Calc only. The 1.00 A row in the heat note is 0.963 W.
P_CHG = V_PACK * I_CHG * (1.0 / ETA_CHG - 1.0)
RTH_JA = 35.7            # cited, SLUSAF7D
TJ_REG = 120.0
TJ_SHUT = 150.0
CELL_MAX = 60.0          # cited, P45B charge window
SERVO_MAX = 60.0         # cited, STS3215 operating range, gate_p45b.py
PLA_HDT_LO = 49.0        # cited, THERMAL_TWIN.md PLA heat deflection low end


def idle_servo():
    p = I_IDLE * V_BUS
    z = np.zeros(14)
    return dict(P_cu25=z, P_board=z, P_fric=z.copy(), P_idle=np.full(14, p), i2=z)


def nest_amps(p5):
    """Current through one plus diode and one return diode. Calc only."""
    i_chg = V_PACK * I_CHG / ETA_CHG / NEST_V
    i_servo = (14 * I_IDLE * V_BUS) / ETA_I7C / NEST_V
    i_5 = p5 / ETA_5V / NEST_V
    return i_chg + i_servo + i_5


def trunk(c):
    p_servo = 14 * I_IDLE * V_BUS
    bec_loss = p_servo * (1.0 / ETA_I7C - 1.0)
    i = I_CHG
    i_nest = nest_amps(c["P5V"])
    # Two diodes conduct. 0.50 V is the 5 A maximum, so this is an upper bound at the lower current.
    p_diodes = 2.0 * i_nest * DIODE_VF
    return dict(cells=3 * i * i * TT.PARAMS["R_cell"], holder=i * i * c["R_holder"], bms=i * i * c["R_bms"],
                fuse=i * i * TT.PARAMS["R_fuse"], xt30=i * i * TT.PARAMS["R_xt30"], switch=0.0,
                wires=i * i * TT.PARAMS["R_wires"], bec=bec_loss, bec_leads=0.0, logic=0.15, charger=P_CHG,
                diodes=p_diodes)


def run(corner, Ta, hours=6.0):
    c = TT.CORNERS[corner]
    key = "stand"
    heats = {key: dict(servo=idle_servo(), trunk=trunk(c), head=c["P5V"])}
    r = TT.simulate(lambda t: key, heats, None, c, Ta, t_end=hours * 3600.0, dt=2.0, record=30.0)
    j = [TT.NAMES.index(n) for n in ("left_knee", "right_knee")]
    knee = float(r["Ts"][:, j].max())
    i_nest = nest_amps(c["P5V"])
    return dict(corner=corner, room_C=Ta, charger_W=round(P_CHG, 3),
                diode_W=round(2.0 * i_nest * DIODE_VF, 3), nest_A=round(i_nest, 3),
                cell_C=round(float(r["cells"][-1]), 2),
                trunk_air_C=round(float(r["trunk_air"][-1]), 2),
                trunk_wall_C=round(float(r["trunk_wall"][-1]), 2),
                knee_C=round(knee, 2),
                head_air_C=round(float(r["head_air"][-1]), 2))


def main():
    rows = []
    for corner in ("central", "high"):
        for room in (25.0, 32.0):
            rows.append(run(corner, room))
            print(rows[-1])
    hot = max(rows, key=lambda r: r["cell_C"])
    wall = max(rows, key=lambda r: r["trunk_wall_C"])
    air = max(rows, key=lambda r: r["trunk_air_C"])
    # Upper bound only. Figure 10-4 loss includes the inductor. RthJA is the package.
    die_hi = air["trunk_air_C"] + RTH_JA * P_CHG
    lines = []
    a = lines.append
    a("# Nest charge heat, docked and awake")
    a("")
    a("Sim pass only for the shell. The charger watts are calc only: %.3f W at %.3f A into %.1f V, efficiency %.3f."
      % (P_CHG, I_CHG, V_PACK, ETA_CHG))
    a("The 1.00 A chart row in BQ24133_HEAT.md is 0.963 W. This row uses the board's 1.006 A.")
    a("Servos idle at 12.0 V, torque off, rail on. Head heat is the corner P5V already in the thermal twin.")
    a("Two steering diodes carry that nest current. Their heat uses the cited 0.50 V maximum, which is specified at 5 A, so it is an upper bound here.")
    a("Three cells. Nothing here was measured on a board.")
    a("")
    a("| Corner | Room | Nest A | Diode W | Cells | Trunk air | Trunk wall | Knee reading | Head air |")
    a("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        a("| %s | %.0f C | %.3f | %.3f | %.2f C | %.2f C | %.2f C | %.2f C | %.2f C |" % (
            r["corner"], r["room_C"], r["nest_A"], r["diode_W"], r["cell_C"], r["trunk_air_C"],
            r["trunk_wall_C"], r["knee_C"], r["head_air_C"]))
    a("")
    a("Hottest cell %.2f C against the cited 0 C to 60 C charge window. %s" % (
        hot["cell_C"], "Inside." if hot["cell_C"] < CELL_MAX else "Crosses."))
    a("Hottest knee reading %.2f C against the cited -20 C to 60 C operating range. %s" % (
        max(r["knee_C"] for r in rows), "Inside." if max(r["knee_C"] for r in rows) < SERVO_MAX else "Crosses."))
    a("Hottest trunk wall %.2f C against the cited PLA heat-deflection low end of 49 C. %s" % (
        wall["trunk_wall_C"], "Inside." if wall["trunk_wall_C"] < PLA_HDT_LO else "Crosses."))
    a("Die upper bound at the hottest trunk air: %.1f C plus %.1f C/W times %.3f W = %.1f C. Thermal regulation is 120 C and shutdown is 150 C (cited)."
      % (air["trunk_air_C"], RTH_JA, P_CHG, die_hi))
    a("That bound puts every converter watt in the package, which the sheet does not. It is an upper bound, not a measured junction. %s" % (
        "The bound stays under 120 C." if die_hi < TJ_REG else "The bound crosses 120 C."))
    a("")
    a("Felt temperature is not a node. BLOCKER. In-trunk theta of the package is not the 35.7 C/W board. BLOCKER for a confirmed junction.")
    a("A 25 W Pi 5 is not in this head. The corner P5V is 3 W or 5 W. The 5 V, 5 A supply is pull request 111, not this charger.")
    text = "\n".join(lines) + "\n"
    if "\u2014" in text or "\u2013" in text:
        raise SystemExit("dash")
    open(os.path.join(HERE, "NEST_HEAT.md"), "w").write(text)
    json.dump(dict(rows=rows, p_chg_w=P_CHG, die_upper_C=round(die_hi, 2)),
              open(os.path.join(HERE, "nest_heat.json"), "w"), indent=1)
    print("wrote NEST_HEAT.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
