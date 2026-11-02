#!/usr/bin/env python3
"""Which printed parts are most at risk when find_soft_offsets.py drives all 14 joints to zero
at once (Runtime issue #32, UPSTREAM_ISSUES.md G6)?  Read only; prints a markdown table.

  python3 joint_risk.py

Per joint: URDF range, largest travel to zero (the joint can start anywhere in its range), mass
that swings (URDF masses of every link beyond the joint), and the printed parts that meet at the
joint (URDF visuals of the two links) with their wall thickness (p1 and median ray thickness from
altaay_lab/audit/meas_print.json, the PRINT_CHECK wall column). A servo can only push with its own
torque, so the part that breaks is the thin one at a joint that swings a big mass a long way,
or hits something on the way.
"""
import json, math, os
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
URDF = os.path.join(REPO, "mini_bdx", "robots", "open_duck_mini_v2", "robot.urdf")
MEAS = os.path.join(REPO, "altaay_lab", "audit", "meas_print.json")
NOT_PRINTED = ("wj-", "drive_palonier", "passive_palonier", "roll_bearing", "cell", "board", "bms",
               "usb_c_charger", "power_switch", "bno055", "raspberrypizerow", "holder", "sg90", "antenna.stl")


def main():
    r = ET.parse(URDF).getroot()
    meas = json.load(open(MEAS))
    mass, vis, kids = {}, {}, {}
    for l in r.findall("link"):
        n = l.get("name")
        m = l.find("inertial/mass")
        mass[n] = float(m.get("value")) if m is not None else 0.0
        vis[n] = [v.find("geometry/mesh").get("filename").split("/")[-1] for v in l.findall("visual")
                  if v.find("geometry/mesh") is not None]
    joints = []
    for j in r.findall("joint"):
        p, c = j.find("parent").get("link"), j.find("child").get("link")
        kids.setdefault(p, []).append(c)
        if j.get("type") == "revolute":
            lim = j.find("limit")
            joints.append((j.get("name"), p, c, float(lim.get("lower")), float(lim.get("upper"))))

    def subtree(n):
        return mass[n] + sum(subtree(k) for k in kids.get(n, []))

    def printed(link):
        out = []
        for f in vis[link]:
            if f.startswith(NOT_PRINTED) or f in NOT_PRINTED:
                continue
            key = f.replace("left_knee_to_ankle_", "knee_to_ankle_")
            if key in meas:
                w = meas[key]["wall_min_p1_p5_med"]
                out.append((key.replace(".stl", ""), round(w[1], 2), round(w[3], 2)))
        return out

    print("| Joint | Range deg | Max travel to zero deg | Mass that swings g | Printed parts at the joint (p1 / median wall mm) |")
    print("|---|---|---|---|---|")
    rows = []
    for name, p, c, lo, hi in joints:
        if name.startswith("right_"):
            continue
        parts = sorted(set(printed(p) + printed(c)), key=lambda t: t[2])
        rows.append((name, math.degrees(lo), math.degrees(hi), math.degrees(max(abs(lo), abs(hi))),
                     1000 * subtree(c), parts))
    for name, lo, hi, trav, ms, parts in sorted(rows, key=lambda t: -t[3] * t[4]):
        print("| %s | %.0f to %.0f | %.0f | %.0f | %s |" % (
            name, lo, hi, trav, ms, ", ".join("%s (%.2f / %.2f)" % t for t in parts) or "-"))


if __name__ == "__main__":
    main()
