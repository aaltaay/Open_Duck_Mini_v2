#!/usr/bin/env python3
"""Docked and awake sit with the in-duck BQ24133 loss in the trunk.

The duck is awake: the head keeps the 5 V load the thermal model already uses,
and the servo rail is open (circuitry/SERVO_RAIL.md), so servo current is 0.
The charger heat is the BQ24133 converter loss at 1.006 A (calc only), not the
old 1.9 W to 3.2 W MCP73213 band. That chip is not on this 3S pack.

Efficiency is the Figure 10-4 point at 1.00 A (cited chart read, 0.929). The
figure has no 1.006 A point. Loss is Vbat * 1.006 * (1/0.929 - 1), calc only.

Run from the repo root:
  python3 altaay_lab/twin/thermal/gate_docked_awake.py

Shell temperatures are sim pass only. The die figure is an upper bound.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import gate_bq24133 as G

# Calc only. Same 1.006 A as the netlist. Not a new set point.
I_CHG = 1.006
# Cited chart read, Figure 10-4, AVCC = 15 V, 3 cells, at 1.00 A.
ETA = 0.929
PACKS = (10.8, 12.6)
HOURS = 6.0


def main():
    G._three_cells()
    rows = []
    for vbat in PACKS:
        watts = G.loss_w(vbat, I_CHG, ETA)
        for corner in ("central", "high"):
            for room in (25.0, 32.0):
                row = G._sit(watts, 0.0, I_CHG, corner, room, hours=HOURS, i_idle_a=0.0)
                row["pack_V"] = vbat
                row["i_charge_A"] = I_CHG
                row["eta"] = ETA
                row["label"] = "sim pass only"
                row["servo_rail"] = "off"
                row["awake"] = "head 5 V load on, servos off"
                rows.append(row)
                print(
                    "pack %.1f W %.3f %s %g C  cells %.2f  wall %.2f  air %.2f  knee %.2f"
                    % (vbat, watts, corner, room, row["cell_end_C"], row["trunk_wall_end_C"],
                       row["trunk_air_end_C"], row["knee_reading_max_C"])
                )
    hottest = max(rows, key=lambda r: r["cell_end_C"])
    out = dict(
        label="sim pass only",
        current_A="1.006 calc only",
        eta_at_1A_chart=ETA,
        hours=HOURS,
        note="MCP73213 1.9 W to 3.2 W is not this sit. The installed charger is the BQ24133.",
        rows=rows,
        hottest_cells_C=hottest["cell_end_C"],
        hottest_wall_C=max(r["trunk_wall_end_C"] for r in rows),
        any_cell_over_60=any(r["cell_crosses_60C"] for r in rows),
        any_knee_over_60=any(r["knee_crosses_60C"] for r in rows),
        any_wall_over_49=any(r["wall_crosses_pla_49C"] for r in rows),
        die_upper_max_C=max(r["die_upper_trunk_air_C"] for r in rows),
    )
    path = os.path.join(HERE, "gate_docked_awake.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
        f.write("\n")
    print("wrote", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
