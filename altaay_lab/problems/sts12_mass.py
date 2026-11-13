#!/usr/bin/env python3
"""60 s sheet walks of the 12 V STS3215 on 3S, with the third cell's mass in the trunk.

The holder stays out, as twin/battery/BAY.md already has it. The added mass is one
P45B, 70 g, at the rear cell seat from bay3.py. No retrain. Sim pass only.
"""
import json
import os
import shutil
import sys
import xml.etree.ElementTree as ETXML

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(LAB, "twin", "electromech"))
sys.path.insert(0, os.path.join(LAB, "sim"))
os.environ.setdefault("TWIN_EM_SCRATCH", os.path.join(__import__("tempfile").gettempdir(), "twin_em"))

import em_twin as ET  # noqa: E402
import servo_sts3215 as SV  # noqa: E402
import sts12  # noqa: E402  sets the 12 V sheet constants and the 3S cell

# Rear cell axis from bay3.py, trunk frame, metres. z is the bay mid height.
CELL_M = np.array([-0.15251, 0.001425, 0.0315])
CELL_KG = 0.070  # cited maximum, Molicel P45B, BAY.md


def shift_inertia(I, m, c, dm, p):
    """I is the inertia about c. Returns mass, com, and inertia about the new com."""
    m2 = m + dm
    c2 = (m * c + dm * p) / m2
    def about(mass, point):
        r = point - c2
        return mass * ((r @ r) * np.eye(3) - np.outer(r, r))
    return m2, c2, I + about(m, c) + about(dm, p)


def heavier_model():
    ET.model_folder("ours")
    src = os.path.join(ET.AM.SCR, "models", "ours")
    dst = os.path.join(ET.AM.SCR, "models", "ours_cell3")
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    for name in ("open_duck_mini_v2.xml", "open_duck_mini_v2_backlash.xml"):
        path = os.path.join(dst, name)
        tree = ETXML.parse(path)
        for body in tree.getroot().iter("body"):
            if body.get("name") != "trunk_assembly":
                continue
            inert = body.find("inertial")
            m = float(inert.get("mass"))
            c = np.array([float(x) for x in inert.get("pos").split()])
            f = [float(x) for x in inert.get("fullinertia").split()]
            I = np.array([
                [f[0], f[3], f[4]],
                [f[3], f[1], f[5]],
                [f[4], f[5], f[2]],
            ])
            m2, c2, I2 = shift_inertia(I, m, c, CELL_KG, CELL_M)
            inert.set("mass", f"{m2:.9g}")
            inert.set("pos", " ".join(f"{x:.9g}" for x in c2))
            inert.set("fullinertia", " ".join(f"{x:.9g}" for x in (
                I2[0, 0], I2[1, 1], I2[2, 2], I2[0, 1], I2[0, 2], I2[1, 2])))
            moved = dict(mass_before_kg=round(m, 4), mass_after_kg=round(m2, 4),
                         com_before_m=[round(float(x), 5) for x in c],
                         com_after_m=[round(float(x), 5) for x in c2])
        tree.write(path)
    return dst, moved


def knees_of(r):
    names = list(r["names"])
    bins = r.get("_bins") or {}
    vmin = bins.get("V_min")
    t_end = (r.get("_binsp") or {}).get("t_end")
    if vmin is None or t_end is None or len(t_end) == 0:
        return {}
    fall = r["falls"][0] if r["falls"] else 1e9
    use = np.asarray(t_end) <= fall + 0.05
    if not np.any(use):
        use = np.ones(len(t_end), bool)
    out = {}
    for n in ("left_knee", "right_knee"):
        i = names.index(n)
        out[n] = round(float(vmin[use, i].min()), 3)
    bp = r["_binsp"]
    out["i_pack_peak_A"] = round(float(np.asarray(bp["i_pack_max"])[use].max()), 3)
    return out


def walk(corner, cmd, dur):
    r = ET.run(
        mass="ours", walk="backlash", cmd=(cmd, 0.0, 0.0), dur=dur,
        supply="net", corner=corner, extra=dict(BEC_V=16.0),
        cell="p45b3", q0=0.0, servo_mode="sheet", guard=None,
        keep_full=False, stop_on_fall=True, t_stats=0.0, label="sts12m",
    )
    g = r["gait"]
    return dict(
        label="sim pass only",
        corner=corner,
        cmd_m_s=cmd,
        dur_s=r["dur_s"],
        fall_s=r["falls"] or "none",
        vx_m_s=None if g.get("vx") is None else round(g["vx"], 4),
        track_lin=None if g.get("track_lin") is None else round(g["track_lin"], 3),
        knees=knees_of(r),
        pack=r.get("pack"),
    )


def main():
    dst, moved = heavier_model()
    ET.model_folder = lambda mass: dst
    rows = []
    for corner in ("typical", "high-side"):
        rows.append(walk(corner, 0.15, 60.0))
        print(rows[-1]["corner"], rows[-1]["cmd_m_s"], rows[-1]["fall_s"], rows[-1]["vx_m_s"], flush=True)
    reached = rows[0]["vx_m_s"]
    for corner in ("typical", "high-side"):
        rows.append(walk(corner, reached, 60.0))
        print("reached", rows[-1]["corner"], rows[-1]["fall_s"], rows[-1]["vx_m_s"], flush=True)
    # same torque scale, the trained no-load speed, so the 0.09 m/s can be compared
    sts12.SV.ServoBank.__init__ = sts12._INIT
    fast = walk("typical", 0.15, 20.0)
    print("bam speed", fast["fall_s"], fast["vx_m_s"], flush=True)
    doc = dict(
        label="sim pass only",
        added_mass_kg=CELL_KG,
        cell_seat_m=[round(float(x), 5) for x in CELL_M],
        trunk=moved,
        holder_kg=0.0,
        holder_note="The 25 g holder is already out of this pack (twin/battery/BAY.md). It is not added back.",
        no_load_rad_s=dict(sheet_12V=round(sts12.W0_12, 3), bam=round(sts12.W0_BAM, 3),
                           ratio=round(sts12.W0_12 / sts12.W0_BAM, 3)),
        walks=rows,
        bam_speed_typical_20s=fast,
    )
    path = os.path.join(HERE, "sts12_mass.json")
    json.dump(doc, open(path, "w"), indent=1)
    print("wrote", path)


if __name__ == "__main__":
    main()
