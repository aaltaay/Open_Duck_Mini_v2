"""3S sit with the BQ24133 loss, and the 2S MCP73213 fallback.

The planned charge current is 1.00 A. problems/NEST3.md uses 1.00 A for the
15.0 V drop budget. The chip's fast-charge range is 0.6 A to 2.5 A (cited).
2.5 A is the datasheet maximum, not the current that note plans.

Efficiency is read off Figure 10-4 of SLUSAF7D (15 V in, 3 cells). The figure
does not print the battery voltage, so the same efficiency is used at 10.8 V
and at 12.6 V. Loss is Vbat * I * (1/efficiency - 1), calc only.

The thermal model hardcodes two cans. Mass and can height are scaled by 3/2
so the cell node is three P45B cans. That scale is undone only by not running
the old 2S table from this file.

Run from the repo root:
  python3 altaay_lab/twin/thermal/gate_bq24133.py
"""
import json
import os

import numpy as np

import gate_p45b as G
import twin_thermal as TT

# SLUSAF7D, revised September 2020. https://www.ti.com/lit/ds/symlink/bq24133.pdf
THETA_JA = 35.7          # C/W, RθJA, 24-pin VQFN. The sheet points at SPRA953. Not the closed trunk.
T_REG = 120.0            # C, thermal regulation
T_SHUT = 150.0           # C, thermal shutdown. Restart when the junction falls below 130 C.
T_ABS = 155.0            # C, absolute maximum junction
T_AMB = 85.0             # C, recommended free-air maximum
# Figure 10-4, chart read, black trace, AVCC = 15 V, 3 cells.
ETA_15V_3CELL = {1.00: 0.929, 2.50: 0.926}
# Figure 10-4, chart read, red trace, AVCC = 12 V, 2 cells. No 9.5 V trace is printed.
ETA_12V_2CELL_1A = 0.916
I_PLAN = 1.00
I_MAX = 2.50
V_IN = 15.0
# 3.6 V/cell is the 7.2 V point of the 2S table, times 3/2. 12.6 V is 3 x 4.2, CELL tied to VREF.
PACKS = (10.8, 12.6)
N_CELLS = 3
R_CELL = 0.015
M_CELL = 70.0
H_CELL = 70.15
# Walk study dropout when the BEC setpoint is 16 V and the pack is below it (problems/FIT3.md).
V_DROP = 0.3
I_IDLE = 0.021

# MCP73213, DS20002190C, as already used in CHARGE_WATTS.md on the other branch.
MCP_THETA = 62.0
MCP_REG = 110.0
MCP_SHUT = 150.0
MCP_VIN = 9.5
MCP_PACKS = (6.0, 7.2)
AH = 4.5
TIMER_H = (5.4, 6.6)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "gate_bq24133.json")


def loss_w(vbat, i_chg, eta):
    return vbat * i_chg * (1.0 / eta - 1.0)


def die_c(room_c, p_w, theta=THETA_JA):
    return room_c + theta * p_w


def _three_cells():
    # simulate() multiplies mass and can height by 2. Scaling each by 3/2 makes three cans.
    TT.PARAMS["m_cell_g"] = M_CELL * N_CELLS / 2.0
    TT.PARAMS["cell_h_mm"] = H_CELL * N_CELLS / 2.0
    TT.PARAMS["R_cell"] = R_CELL
    TT.PARAMS["T_cut"] = 200.0


def _sit(charger_w, v_servo, i_chg, corner, Ta, hours=6.0):
    c = TT.CORNERS[corner]
    p_idle = I_IDLE * v_servo
    i_idle = 14 * I_IDLE
    # The 16 V setpoint is above the pack, so the BEC is in dropout, not at 85 percent.
    bec = i_idle * V_DROP
    z = np.zeros(14)
    servo = dict(P_cu25=z, P_board=z, P_fric=z.copy(), P_idle=np.full(14, p_idle), i2=z)
    trunk = dict(
        cells=N_CELLS * i_chg * i_chg * R_CELL,
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
    r = TT.simulate(lambda t: key, heats, None, c, Ta, t_end=hours * 3600.0, dt=2.0, record=30.0)
    air = float(r["trunk_air"][-1])
    wall = float(r["trunk_wall"][-1])
    cells = float(r["cells"][-1])
    j = [TT.NAMES.index(n) for n in ("left_knee", "right_knee")]
    knee = float(r["Ts"][:, j].max())
    hs = TT.hot_spots(trunk, air, c, None)
    return dict(
        charger_W=round(charger_w, 3),
        corner=corner,
        room_C=Ta,
        cell_end_C=round(cells, 2),
        trunk_air_end_C=round(air, 2),
        trunk_wall_end_C=round(wall, 2),
        knee_reading_max_C=round(knee, 2),
        bec_case_end_C=round(float(hs["bec_case"]), 2),
        die_on_cited_board_C=round(die_c(Ta, charger_w), 2),
        die_if_35p7_in_trunk_air_C=round(die_c(air, charger_w), 2),
        cell_crosses_60C=cells > 60.0,
        knee_crosses_60C=knee > 60.0,
        wall_crosses_pla_49C=wall > 49.0,
        wall_crosses_petg_62C=wall > 62.0,
        air_crosses_85C=air > T_AMB,
        die_board_crosses_120C=die_c(Ta, charger_w) > T_REG,
        die_board_crosses_150C=die_c(Ta, charger_w) > T_SHUT,
        die_trunk_crosses_120C=die_c(air, charger_w) > T_REG,
        die_trunk_crosses_150C=die_c(air, charger_w) > T_SHUT,
    )


def mcp_fallback():
    rows = []
    for vpack in MCP_PACKS:
        dv = MCP_VIN - vpack
        p = dv * 1.00
        for Ta in (25.0, 32.0):
            tj = Ta + MCP_THETA * p
            rows.append(dict(
                pack_V=vpack, room_C=Ta, power_W=round(p, 2),
                junction_C=round(tj, 1),
                crosses_110C=tj > MCP_REG, crosses_150C=tj > MCP_SHUT,
            ))
    # Current that holds the cited limits on 62 C/W at a 32 C room, worst drop (6.0 V pack).
    dv = MCP_VIN - 6.0
    out = dict(
        label="calc only",
        theta_C_per_W=MCP_THETA,
        forced_1A=rows,
        i_for_110C_at_32C_6V_A=round((MCP_REG - 32.0) / MCP_THETA / dv, 3),
        i_for_150C_at_32C_6V_A=round((MCP_SHUT - 32.0) / MCP_THETA / dv, 3),
        hours_at_150C_current=round(AH / ((MCP_SHUT - 32.0) / MCP_THETA / dv), 2),
        timer_h=list(TIMER_H),
        theta_needed_for_3p50W_under_150C_at_32C=round((MCP_SHUT - 32.0) / 3.50, 2),
        theta_cited_C_per_W=MCP_THETA,
    )
    # 2-cell BQ24133, CELL floating, 8.4 V. Nearest curve is 12 V in, not the 9.5 V nest.
    eta = ETA_12V_2CELL_1A
    p_bq = loss_w(8.4, 1.00, eta)
    p_low = loss_w(8.4, 1.00, 0.85)
    out["bq24133_2cell"] = dict(
        cell_pin="floating, 8.4 V, cited",
        eta_chart=eta,
        eta_note="Figure 10-4 red trace at 1.00 A, AVCC 12 V, 2 cells. No 9.5 V trace.",
        loss_at_8p4V_W=round(p_bq, 3),
        junction_32C=round(die_c(32.0, p_bq), 1),
        loss_if_85pct_W=round(p_low, 3),
        junction_32C_if_85pct=round(die_c(32.0, p_low), 1),
    )
    return out


def main():
    # The 2S model still matches its published row before the 3-cell scale.
    chk = G.run_sit(3.2, "central", 32.0)
    if abs(chk["cell_end_C"] - 40.4) > 0.05 or abs(chk["trunk_wall_end_C"] - 36.84) > 0.05:
        raise SystemExit("2S check does not match gate_p45b.json")
    print("2S check cell", chk["cell_end_C"], "wall", chk["trunk_wall_end_C"])

    _three_cells()
    cases = []
    for i_chg, packs in ((I_PLAN, PACKS), (I_MAX, (12.6,))):
        eta = ETA_15V_3CELL[i_chg]
        for vbat in packs:
            p = loss_w(vbat, i_chg, eta)
            for corner in ("central", "high"):
                for Ta in (25.0, 32.0):
                    row = _sit(p, vbat, i_chg, corner, Ta)
                    row.update(i_chg_A=i_chg, vbat_V=vbat, eta=eta, planned=(i_chg == I_PLAN))
                    cases.append(row)
                    print(i_chg, vbat, corner, Ta, "loss", round(p, 3),
                          "cell", row["cell_end_C"], "wall", row["trunk_wall_end_C"],
                          "air", row["trunk_air_end_C"], "knee", row["knee_reading_max_C"],
                          "die", row["die_on_cited_board_C"], "die_trunk", row["die_if_35p7_in_trunk_air_C"],
                          flush=True)

    doc = dict(
        label="sim pass only for the shell, calc only for the loss and the die",
        datasheet="BQ24133 SLUSAF7D, September 2020",
        figure="Figure 10-4, chart read",
        theta_JA_C_per_W=THETA_JA,
        regulation_C=T_REG,
        shutdown_C=T_SHUT,
        planned_current_A=I_PLAN,
        planned_current_note="1.00 A is the current problems/NEST3.md uses for the 15.0 V drop. 2.50 A is the datasheet maximum.",
        vin_V=V_IN,
        eta_15V_3cell=ETA_15V_3CELL,
        eta_note="The 3-cell trace does not print the battery voltage. The same efficiency is used at 10.8 V and 12.6 V.",
        cells=N_CELLS,
        cell_scale="mass and can height times 3/2, because the model hardcodes two cans",
        bec="0.3 V dropout times the idle current. The 16 V setpoint is above the pack.",
        servo_volts="the pack voltage of that row. A nest-fed bus near 14.7 V is above the 14 V page range and is not the row.",
        nest="cad/nest_v2 stays. The mat is not redrawn.",
        sit=cases,
        mcp73213_2s_fallback=mcp_fallback(),
        check_2s_3p2W_central_32=dict(cell_C=chk["cell_end_C"], wall_C=chk["trunk_wall_end_C"]),
    )
    json.dump(doc, open(OUT, "w"), indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
