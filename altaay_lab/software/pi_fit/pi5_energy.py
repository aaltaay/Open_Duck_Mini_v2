#!/usr/bin/env python3
"""Hours-awake impact of a higher computer draw. Calc only, sim pass only.

The Zero soak uses 1.75 W (0.350 A times 5 V). This run keeps every other
set point and replaces that term with 5.0 W, the high end of the cited
whitepaper minimum band. The walk current gains the same watt delta, because
the published 5.144 A did not include a Pi 5.

It does not overwrite the Zero soak files.
"""

from __future__ import annotations

import json
import os

from altaay_lab.software.autonomy.plant import PI_W
from altaay_lab.software.autonomy.soak import run
from altaay_lab.software.pi_fit.pi5_board import MIN_W_HIGH


def main():
    base, _day, _sup = run(days=3.0, seed=1)
    extra = MIN_W_HIGH - PI_W
    newer, _day2, _sup2 = run(days=3.0, seed=1, pi_w=MIN_W_HIGH, walk_extra_w=extra)
    report = {
        "label": "sim pass only, computer watts are the cited minimum band",
        "zero_computer_w": PI_W,
        "pi5_computer_w": MIN_W_HIGH,
        "pi5_computer_w_label": "cited, whitepaper RP-010139-WP table 1 high end of 4 W to 5 W. A measured idle watt is BLOCKER.",
        "walk_extra_w": extra,
        "walk_extra_label": "calc only, added on top of the 5.144 A sim mean",
        "zero_hours_awake": base["hours_awake"],
        "pi5_hours_awake": newer["hours_awake"],
        "hours_delta": newer["hours_awake"] - base["hours_awake"],
        "zero_min_pack_v": base["min_pack_v"],
        "pi5_min_pack_v": newer["min_pack_v"],
        "zero_dock_attempts": base.get("dock_attempts"),
        "pi5_dock_attempts": newer.get("dock_attempts"),
    }
    dest = os.path.join(os.path.dirname(__file__), "pi5_energy.json")
    with open(dest, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=1)
        handle.write("\n")
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
