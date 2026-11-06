"""mic_fasteners.py: write the 4 mic board screws (F356 to F359) into fasteners/fasteners.json and the two mic board
boxes (mic_l, mic_r) into audit/placements.json from twin/companion/mic_seats.json. CAD check only.

Run after mic_seat.py: python3 altaay_lab/twin/companion/mic_fasteners.py
The screw seat is the board top face: the boss top plus the PCB. The PCB thickness is not published; the stand-in is
PCB_T_SEAT (0.8 mm, the value the 1.8 mm overall height of adafruit.com/product/3421 points to, calc only), and the
screw length window is checked for 0.8 to 1.6 mm in mic_seats.json (engagement and tip gap).
"""
import copy
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(LAB, "twin", "complete3d"))
from common import scene   # noqa: E402

FJ = os.path.join(LAB, "fasteners", "fasteners.json")
PLACEMENTS = os.path.join(LAB, "audit", "placements.json")
SEATS = os.path.join(HERE, "mic_seats.json")
IDS = {"left": ("F356", "F357"), "right": ("F358", "F359")}
PCB_T_SEAT = 0.8


def main():
    J = json.load(open(SEATS))
    meta = J["meta"]
    L = meta["screw"]["L"]; rule = meta["screw"]["rule_engage"]
    depth = meta["pilot"]["depth"]; tip_rule = J["checks"].get("tip_gap_rule_mm", 0.25)
    F = json.load(open(FJ))
    S = scene(); Ti = np.linalg.inv(S.T0["head_assembly"])
    byid = {f["id"]: f for f in F["fasteners"]}
    for side, ids in IDS.items():
        s = J["seats"][side]
        for fid, h in zip(ids, s["screws"]):
            f = byid[fid]
            ax = np.array(h["axis_world"]); top = np.array(h["seat_world"])       # boss top, axis into the wall
            seat = top - ax * PCB_T_SEAT
            sl = (Ti @ np.r_[seat, 1.0])[:3]; al = Ti[:3, :3] @ ax; al = al / np.linalg.norm(al)
            x = np.cross([0, 0, 1.0], al) if abs(al[2]) < 0.9 else np.cross([1.0, 0, 0], al)
            x /= np.linalg.norm(x); y = np.cross(al, x)
            T = np.eye(4); T[:3, 0], T[:3, 1], T[:3, 2], T[:3, 3] = x, y, al, sl
            f.update(seat_world=np.round(seat, 3).tolist(), axis_world=np.round(ax, 4).tolist(),
                     seat_link=np.round(sl, 3).tolist(), axis_link=np.round(al, 4).tolist(), pose_link=np.round(T, 4).tolist(),
                     anchor="printed boss 5.0 mm, 3.5 mm high, pilot 1.65 x %.1f mm (twin/companion/mic_seat.py, D47)" % depth,
                     near=PCB_T_SEAT, far=round(PCB_T_SEAT + depth, 2), stop=round(PCB_T_SEAT + depth, 2),
                     e=round(L - PCB_T_SEAT, 2), e_min=round(min(s["screw_engagement_mm"].values()), 2),
                     lmin=round(PCB_T_SEAT + rule, 2), lmax=round(PCB_T_SEAT + depth - tip_rule, 2),
                     tip_gap=round(PCB_T_SEAT + depth - L, 2), len_status="OK",
                     seat_type="mic board top face (PCB 0.8 mm stand-in, not published; 0.8 to 1.6 checked: engagement %s mm, tip gap %s mm)" % (
                         " to ".join(str(v) for v in sorted(s["screw_engagement_mm"].values())),
                         " to ".join(str(v) for v in sorted(s["screw_tip_gap_mm"].values()))),
                     notes=["D47: mirror pair about the board centre line (D42); both board holes used (D39)",
                            "material past the pilot bottom %.2f mm (mic_seats.json, CAD check only)" % h["material_past_pilot_mm"],
                            "Board and holes from the 3421 board files (Adafruit-I2S-Microphone-Breakout-PCB), read 2026-11-05"])
    json.dump(F, open(FJ, "w"))
    P = json.load(open(PLACEMENTS))
    for side, pid in (("left", "mic_l"), ("right", "mic_r")):
        s = J["seats"][side]
        c = np.array(s["board_centre_world"]); n = np.array(s["inward_normal"])
        for p in P:
            if p["id"] == pid:
                p["center_mm"] = [round(float(v), 2) for v in c + n * 1.5]
                p["label"] = "I2S mic board %s (Adafruit 3421, BOM E8, D47)" % side
                p["seat_fix"] = "2026-11-05 ET, V1 track 11: on the bosses of twin/companion/mic_seat.py, 3.5 mm off the wall (CAD check only)"
    json.dump(P, open(PLACEMENTS, "w"), indent=1)
    print("fasteners F356 to F359 and placements mic_l, mic_r written")


if __name__ == "__main__":
    main()
