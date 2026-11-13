"""Docked charge at the reconciled MCP73213 board heat, and the nest beside that charge.

The older table (1.9 W and 3.2 W) stays in gate_p45b.json. This file does not overwrite it.
Watts are calc only, from circuitry/CHARGER_BOARD.md: (9.5 V - pack) x 1.00 A.
  7.2 V pack: 2.30 W.  6.0 V pack: 3.50 W.
That is the heat if the current stays at 1.00 A. The chip sheet regulates the die at 110 C,
so a real charge may fold the current back. The shell numbers below are the forced-current case.

Every shell temperature is sim pass only (the existing trunk model, torque off, 6 h).
The die rise on 62 C/W is calc only, and that 62 C/W is the sheet's JEDEC board, not the trunk.
The felt temperature is not a node in the model.

Run from the repo root:
  python3 altaay_lab/twin/thermal/gate_charge_watts.py
"""
import json
import os

import gate_p45b as G

# DS20002190C temperature specifications and the block diagram, as already read in CHARGER_BOARD.md.
THETA_JA = 62.0          # C/W, 4-layer JEDEC board, natural convection. Not the closed trunk.
T_REG = 110.0            # C, thermal-regulation comparator on the block diagram
T_SHUT = 150.0           # C typical, thermal shutdown, DC table. Hysteresis 10 C.
T_AMBIENT_MAX = 85.0     # C, industrial order code, -40 C to +85 C. This is ambient, not the junction.
# P45B version 1.2, charge window. Discharge is -40 C to 60 C. The sit is a charge.
T_CELL = (0.0, 60.0)
# STS3215 A/1 item 1-2. Item 7-11 turns torque off above 70 C.
T_SERVO = (-20.0, 60.0)
# THERMAL_TWIN.md [P1] to [P3] and [P6]. The wall node is the model's PLA, not a part touching the package.
PLA_HDT = (49.0, 57.0)   # C, 0.45 MPa band already cited
PLA_TG = (55.0, 60.0)
PETG_HDT_018 = 62.0      # C at 1.8 MPa, Bambu PETG HF
PETG_HDT_045 = 69.0      # C at 0.45 MPa
PETG_TG = 66.0
# Superior Felt Wool-Felt-Specs.pdf, properties that apply to all wool felt type I.
# The same sheet is the 99 percent recovery source in twin/contact/CONTACT_TWIN.md.
# -80 F to +200 F. This mat has no grade, so the range applies only if the mat is that felt.
FELT_F = (-80.0, 200.0)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "gate_charge_watts.json")
WATTS = (2.30, 3.50)


def _f_to_c(f):
    return (f - 32.0) / 1.8


def _die(p_w, room_c):
    rise = THETA_JA * p_w
    tj = room_c + rise
    return dict(theta_JA_C_per_W=THETA_JA, rise_C=round(rise, 2), junction_C=round(tj, 2),
                crosses_110C=tj > T_REG, crosses_150C=tj > T_SHUT,
                label="calc only, JEDEC board in room air, current forced at 1.00 A")


def _row_limits(row):
    cell = row["cell_end_C"]
    wall = row["trunk_wall_end_C"]
    knee = row["knee_reading_max_C"]
    air = row["trunk_air_end_C"]
    return dict(
        cell_crosses_0_to_60C=cell < T_CELL[0] or cell > T_CELL[1],
        knee_crosses_m20_to_60C=knee < T_SERVO[0] or knee > T_SERVO[1],
        wall_crosses_pla_hdt_49C=wall > PLA_HDT[0],
        wall_crosses_pla_tg_55C=wall > PLA_TG[0],
        wall_crosses_petg_hdt_62C=wall > PETG_HDT_018,
        trunk_air_crosses_industrial_ambient_85C=air > T_AMBIENT_MAX,
        # The felt is outside the shell. In this one-node model the outer wall is the
        # hottest surface the model gives the mat. The posed sit puts TPU on the felt,
        # and TPU is not a node, so this is a bound, not a felt temperature.
        wall_bound_crosses_wool_felt_93C=wall > _f_to_c(FELT_F[1]))


def main():
    # Arithmetic the table is built on. Fail here rather than publish a drifted watt.
    assert abs((9.5 - 7.2) * 1.00 - 2.30) < 1e-12
    assert abs((9.5 - 6.0) * 1.00 - 3.50) < 1e-12
    assert abs(2.30 * 62.0 - 142.6) < 1e-9
    assert abs(3.50 * 62.0 - 217.0) < 1e-9

    sit = []
    for w in WATTS:
        for corner in ("central", "high"):
            for Ta in (25.0, 32.0):
                row = G.run_sit(w, corner, Ta)
                row["limits"] = _row_limits(row)
                row["die_jedec"] = _die(w, Ta)
                sit.append(row)
                print("sit", w, corner, Ta, "cell", row["cell_end_C"], "air", row["trunk_air_end_C"],
                      "wall", row["trunk_wall_end_C"], "knee", row["knee_reading_max_C"],
                      "bec", row["bec_case_end_C"], "die", row["die_jedec"]["junction_C"], flush=True)

    # Same model as the published 3.2 W central 32 C row (cell 40.4 C, wall 36.84 C).
    check_32 = G.run_sit(3.2, "central", 32.0)
    # PR 49 life note, central, 3.50 W, 22 C and 32 C. Not a new corner of this table.
    life_22 = G.run_sit(3.50, "central", 22.0)
    life_32 = G.run_sit(3.50, "central", 32.0)
    print("check 3.2 central 32 cell", check_32["cell_end_C"], "wall", check_32["trunk_wall_end_C"])
    print("life 3.50 central 22 cell", life_22["cell_end_C"], "wall", life_22["trunk_wall_end_C"],
          "knee", life_22["knee_reading_max_C"], "bec", life_22["bec_case_end_C"])
    print("life 3.50 central 32 cell", life_32["cell_end_C"], "wall", life_32["trunk_wall_end_C"])
    if abs(check_32["cell_end_C"] - 40.4) > 0.05 or abs(check_32["trunk_wall_end_C"] - 36.84) > 0.05:
        raise SystemExit("the 3.2 W check does not match gate_p45b.json")

    die = []
    for w in WATTS:
        for Ta in (25.0, 32.0):
            d = _die(w, Ta)
            d["charger_W"] = w
            d["room_C"] = Ta
            # Power that holds the die at the cited limits on this theta, room air.
            d["watts_at_110C"] = round((T_REG - Ta) / THETA_JA, 3)
            d["watts_at_150C"] = round((T_SHUT - Ta) / THETA_JA, 3)
            die.append(d)

    doc = dict(
        label="sim pass only for shell temperatures, calc only for watts and for the JEDEC die",
        charger_W=list(WATTS),
        charger_note="calc only, 9.5 V in, 1.00 A forced, MCP73213, circuitry/CHARGER_BOARD.md",
        input_V=9.5,
        current_A=1.00,
        pack_V=dict(W_2_30=7.2, W_3_50=6.0),
        hours=6.0,
        state="docked sit, torque off, idle 21 mA per servo, charge 1.0 A",
        older_table="gate_p45b.json, 1.9 W and 3.2 W, left as written",
        life_note="PR 49 ran the central corner at 22 C and 32 C. This file adds the high corner and the 25 C room of the original table.",
        guesses=[
            "cell specific heat is the 18650 range already in twin_thermal.py, not on the P45B sheet",
            "half the can faces the bay air",
            "BEC efficiency 0.85 at idle, Castle publishes none",
            "the charger has no seat, so the PLA number is the trunk wall node, not the plastic touching the package",
            "in-trunk theta JA is not the 62 C/W JEDEC figure",
            "the nest felt has no grade, so a felt conductivity is not used",
        ],
        limits=dict(
            cells_charge_C=list(T_CELL),
            cells_source="Molicel INR21700-P45B version 1.2",
            servo_operating_C=list(T_SERVO),
            servo_source="STS3215 A/1 item 1-2",
            die_regulation_C=T_REG,
            die_shutdown_typical_C=T_SHUT,
            die_ambient_industrial_C=[-40, 85],
            die_source="MCP73213 DS20002190C, as read in circuitry/CHARGER_BOARD.md",
            pla_hdt_0p45_MPa_C=list(PLA_HDT),
            pla_tg_C=list(PLA_TG),
            petg_hdt_1p8_MPa_C=PETG_HDT_018,
            petg_hdt_0p45_MPa_C=PETG_HDT_045,
            petg_tg_C=PETG_TG,
            plastic_source="THERMAL_TWIN.md [P1] to [P3] and [P6]",
            wool_felt_type_I_F=list(FELT_F),
            wool_felt_type_I_C=[round(_f_to_c(FELT_F[0]), 2), round(_f_to_c(FELT_F[1]), 2)],
            felt_source="Superior Felt Wool-Felt-Specs.pdf, all wool felt type I. This mat's grade is not named.",
        ),
        verdict=dict(
            cells="no row crosses 0 C to 60 C",
            servo_reading="no row crosses -20 C to 60 C",
            pla_wall="no row crosses the 49 C heat-deflection edge",
            petg_wall="no row crosses 62 C",
            trunk_air_vs_85C="no row crosses the 85 C industrial ambient",
            die_jedec_forced_1A="every row crosses 110 C and 150 C",
            die_in_trunk="BLOCKER",
            felt_temperature="BLOCKER",
            plastic_touching_the_package="BLOCKER",
        ),
        sit=sit,
        die_jedec=die,
        regression=dict(
            published_3_2_central_32=dict(cell_C=40.4, wall_C=36.84, rerun_cell_C=check_32["cell_end_C"],
                                          rerun_wall_C=check_32["trunk_wall_end_C"]),
            life_note_3_50_central=dict(
                room_22=dict(cell_C=life_22["cell_end_C"], wall_C=life_22["trunk_wall_end_C"],
                             knee_C=life_22["knee_reading_max_C"], bec_C=life_22["bec_case_end_C"],
                             air_C=life_22["trunk_air_end_C"]),
                room_32=dict(cell_C=life_32["cell_end_C"], wall_C=life_32["trunk_wall_end_C"],
                             knee_C=life_32["knee_reading_max_C"], bec_C=life_32["bec_case_end_C"],
                             air_C=life_32["trunk_air_end_C"]))))
    for row in doc["sit"]:
        row["charger_W"] = "%.2f" % row["charger_W"]
    for row in doc["die_jedec"]:
        row["charger_W"] = "%.2f" % row["charger_W"]
    doc["charger_W"] = ["2.30", "3.50"]
    json.dump(doc, open(OUT, "w"), indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
