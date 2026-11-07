#!/usr/bin/env python3
"""servo_limits.py: the software joint limits of every servo, 3 deg inside every hard stop (D59), and their encoder
counts. Writes altaay_lab/software/servo_limits.json, which bench/set_angle_limits.py writes into the servo angle limit
registers and twin/sit/sit_model.py uses as the sim actuator ranges. calc only.

  python3 altaay_lab/twin/sit/servo_limits.py [--write]

Hard stop per joint end, the nearest of:
  - the URDF limit (robot.urdf, after sit_urdf.py: the designed sit stops are the URDF limits, sitlib.STOPS);
  - the first CAD contact found by sit_sweep.py (hard_stops: one joint moved from the zero pose, 0.5 deg steps,
    the first new overlap over the zero pose), read from sit_sweep.json.
Software limit = hard stop moved SOFT_MARGIN_DEG (3 deg) toward zero.
Encoder: raw = 2048 + (q + offset) x 4096 / 360 deg, the rustypot conversion the Runtime uses (bench/odm_bench/sts3215.py
POS_CENTER; KNEE_TWIN.md section 2: STS3250 4096 steps, centre 2048 [F5]). The margin to the 0/4095 wrap is reported at
the hard stops for a zero offset; set_angle_limits.py adds the measured offset per servo and refuses a range that wraps.
"""
import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sitlib as L  # noqa: E402

OUT = os.path.join(L.LAB, "software", "servo_limits.json")
JOINTS = {   # the Runtime HWI ids (bench/odm_bench/joints.py JOINTS)
    "left_hip_yaw": 20, "left_hip_roll": 21, "left_hip_pitch": 22, "left_knee": 23, "left_ankle": 24,
    "neck_pitch": 30, "head_pitch": 31, "head_yaw": 32, "head_roll": 33,
    "right_hip_yaw": 10, "right_hip_roll": 11, "right_hip_pitch": 12, "right_knee": 13, "right_ankle": 14}
STEPS_PER_DEG = 4096 / 360.0


def raw(deg, offset_rad=0.0):
    return int(round(2048 + (np.radians(deg) + offset_rad) * 4096 / (2 * np.pi)))


def build():
    r = ET.parse(L.URDF).getroot()
    urdf = {}
    for j in r.findall("joint"):
        l_ = j.find("limit")
        if l_ is not None and j.get("name") in JOINTS:
            urdf[j.get("name")] = (np.degrees(float(l_.get("lower"))), np.degrees(float(l_.get("upper"))))
    sw = json.load(open(os.path.join(HERE, "sit_sweep.json")))
    cad = sw.get("hard_stops", {})
    designed = {}
    for k, v in L.STOPS.items():
        designed.setdefault(v["joint"], {})[v["side"]] = (v["stop"], k)
        # the right side mirrors hip roll and hip pitch; knee, ankle and the head joints keep the sign
        rj = v["joint"].replace("left_", "right_")
        if rj != v["joint"]:
            mirror = any(s in rj for s in ("hip_roll", "hip_pitch"))
            side = {"lo": "hi", "hi": "lo"}[v["side"]] if mirror else v["side"]
            designed.setdefault(rj, {})[side] = (-v["stop"] if mirror else v["stop"], k)
    out = {}
    for jn, sid in JOINTS.items():
        lo_u, hi_u = urdf[jn]
        c = cad.get(jn, {})
        ends = {}
        for side, u in (("lo", lo_u), ("hi", hi_u)):
            cands = [(u, "URDF limit")]
            if jn in designed and side in designed[jn]:
                cands.append((designed[jn][side][0], "designed stop %s (D59)" % designed[jn][side][1]))
            cc = c.get(side)
            if cc is not None:
                cands.append((cc, "CAD contact (sit_sweep.py hard_stops)"))
            pick = max(cands, key=lambda x: x[0]) if side == "lo" else min(cands, key=lambda x: x[0])
            ends[side] = pick
        soft_lo = ends["lo"][0] + L.SOFT_MARGIN_DEG
        soft_hi = ends["hi"][0] - L.SOFT_MARGIN_DEG
        out[jn] = dict(id=sid, urdf_deg=[round(lo_u, 3), round(hi_u, 3)],
                       hard_lo_deg=round(ends["lo"][0], 2), hard_lo_source=ends["lo"][1],
                       hard_hi_deg=round(ends["hi"][0], 2), hard_hi_source=ends["hi"][1],
                       soft_lo_deg=round(soft_lo, 2), soft_hi_deg=round(soft_hi, 2),
                       raw_soft=[raw(soft_lo), raw(soft_hi)], raw_hard=[raw(ends["lo"][0]), raw(ends["hi"][0])],
                       wrap_margin_steps=min(raw(ends["lo"][0]), 4095 - raw(ends["hi"][0])))
    knee = out["left_knee"]
    J = dict(generated_by="altaay_lab/twin/sit/servo_limits.py", label="calc", rule="software limit = hard stop moved %.1f deg toward zero (D59)" % L.SOFT_MARGIN_DEG,
             encoder="raw = 2048 + (q + offset) x 4096 / 360 (rustypot; STS3215 and STS3250 4096 steps, KNEE_TWIN.md section 2)",
             registers="min angle limit 9 (u16), max angle limit 11 (u16), lock 55 [U] rustypot c8b8223 src/device/feetech_sts3215.rs, "
                       "pypot f6d305e sts3215_io.py; factory 0 and 4095 (bench/tests/fake_sts3215.py, the REGISTER_REFERENCE.md read)",
             knee_span=dict(deg=round(knee["hard_hi_deg"] - knee["hard_lo_deg"], 1), raw=knee["raw_hard"], wrap_margin_steps=knee["wrap_margin_steps"],
                            wrap_margin_deg=round(knee["wrap_margin_steps"] / STEPS_PER_DEG, 1),
                            note="the knee's -90 to +150 deg span maps to raw 1024 to 3755 at a zero offset: it does not cross the "
                                 "0/4095 wrap, so no offset register (31) is needed; a horn indexed more than the margin off zero would "
                                 "need one (set_angle_limits.py refuses a wrapping range)"),
             joints=out)
    return J


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    J = build()
    for jn, v in J["joints"].items():
        print("%-16s hard %7.2f (%s) .. %7.2f (%s)  soft %7.2f .. %7.2f  raw %s  wrap margin %d" % (
            jn, v["hard_lo_deg"], v["hard_lo_source"], v["hard_hi_deg"], v["hard_hi_source"], v["soft_lo_deg"], v["soft_hi_deg"],
            v["raw_soft"], v["wrap_margin_steps"]))
    if a.write:
        L.dump(J, OUT)
        print("wrote", os.path.relpath(OUT, L.REPO))
