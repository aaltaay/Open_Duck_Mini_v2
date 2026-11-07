#!/usr/bin/env python3
"""sit_urdf.py: the A1b sit (D59) in the robot description: robot.urdf, robot.xml and robot_motors.xml.

Run after sit_cad.py --write: python3 altaay_lab/twin/sit/sit_urdf.py [--write] (prints the change list without --write).

Changes, all from twin/sit/sit_cad.json (the CAD it describes) and sitlib.STOPS (the approved stop angles):
  joint ranges  knee upper 150 (both), ankle lower -95 (both), hip roll outward 8 (left lower -8, right upper +8),
                hip pitch back 75 (left lower -75, right upper +75), neck pitch upper +25, head pitch lower -25. The
                URDF range is the hard stop; the servo software limits are 3 deg inside (servo_limits.py).
  shin links    knee_and_ankle_assembly_2 and _4 load shin_left_sheet, shin_right_sheet and shin_spacer in place of the
                stock sheets and leg_spacer (same origins: the new parts keep the stock part frames).
  new parts     knee_bumper (shin links), ankle_pad (2 per foot), hip_pad (roll_to_pitch links), sit_seat and sit_bumper
                (trunk): a visual and a collision each, at the placements sit_cad.py computed.
Edits are made on the text, so the upstream formatting stays; the script checks that every edit landed exactly once.
"""
import argparse
import json
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sitlib as L  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
URDF = L.URDF
MJCF = [os.path.join(L.URDF_DIR, "robot.xml"), os.path.join(L.URDF_DIR, "robot_motors.xml")]
D = np.radians

# joint: (lower deg, upper deg) as the URDF has them per side (hip roll and hip pitch mirror on the right)
def ranges():
    st = {k: v["stop"] for k, v in L.STOPS.items()}
    return {
        "left_knee": (-90.0, st["knee_fold"]), "right_knee": (-90.0, st["knee_fold"]),
        "left_ankle": (st["ankle_sit"], 90.0), "right_ankle": (st["ankle_sit"], 90.0),
        "left_hip_roll": (st["hip_roll_out"], 25.0), "right_hip_roll": (-25.0, -st["hip_roll_out"]),
        "left_hip_pitch": (st["hip_pitch_back"], 30.0), "right_hip_pitch": (-30.0, -st["hip_pitch_back"]),
        "neck_pitch": (-20.0, st["neck_back"]), "head_pitch": (st["head_fwd"], 45.0),
    }


SHIN_SWAP = {"left_knee_to_ankle_left_sheet": "shin_left_sheet", "left_knee_to_ankle_right_sheet": "shin_right_sheet",
             "leg_spacer": "shin_spacer"}
SHIN_LINKS = ("knee_and_ankle_assembly_2", "knee_and_ankle_assembly_4")
TPU_RGBA = "0.95 0.75 0.2 1"


def rpy_of(R):
    """URDF rpy (fixed axes x, y, z) of a rotation matrix"""
    sy = -R[2, 0]
    p = np.arcsin(np.clip(sy, -1, 1))
    if abs(np.cos(p)) > 1e-9:
        r = np.arctan2(R[2, 1], R[2, 2])
        y = np.arctan2(R[1, 0], R[0, 0])
    else:
        r = np.arctan2(-R[1, 2], R[1, 1])
        y = 0.0
    return r, p, y


def quat_of(R):
    import trimesh.transformations as tf
    M = np.eye(4)
    M[:3, :3] = R
    q = tf.quaternion_from_matrix(M)
    return q / np.linalg.norm(q)          # w x y z (MuJoCo order)


def new_visuals(cad):
    """[(link, stem, 4x4 link frame in m)] of the new local-frame parts"""
    out = []
    for stem, rows in cad["placements"].items():
        for r in rows:
            T = np.array(r["T_link_mm"], float)
            T[:3, 3] /= 1000.0
            out.append((r["link"], stem, T))
    return out


def urdf_block(stem, T, collision=True):
    r, p, y = rpy_of(T[:3, :3])
    o = '<origin xyz="%.9g %.9g %.9g" rpy="%.9g %.9g %.9g" />' % (T[0, 3], T[1, 3], T[2, 3], r, p, y)
    s = ('        <visual>\n            %s\n            <geometry>\n                <mesh filename="package:///%s.stl"/>\n'
         '            </geometry>\n            <material name="%s_material">\n                <color rgba="%s"/>\n'
         '            </material>\n        </visual>\n' % (o, stem, stem, TPU_RGBA))
    if collision:
        s += ('        <collision>\n            %s\n            <geometry>\n                <mesh filename="package:///%s.stl"/>\n'
              '            </geometry>\n        </collision>\n' % (o, stem))
    return s


def edit_urdf(txt, cad):
    log = []
    R = ranges()
    for jn, (lo, hi) in R.items():
        pat = re.compile(r'(<joint name="%s" type="revolute">.*?<limit [^>]*?lower=")([^"]+)("[^>]*?upper=")([^"]+)(")' % jn, re.S)
        m = pat.findall(txt)
        if len(m) != 1:
            raise SystemExit("URDF: joint %s limit found %d times" % (jn, len(m)))
        txt = pat.sub(lambda mm: mm.group(1) + "%.17g" % D(lo) + mm.group(3) + "%.17g" % D(hi) + mm.group(5), txt)
        log.append("urdf %s limit %.1f to %.1f deg" % (jn, lo, hi))
    for ln in SHIN_LINKS:
        a = txt.index('<link name="%s">' % ln)
        b = txt.index("</link>", a)
        seg = txt[a:b]
        for old, new in SHIN_SWAP.items():
            n = seg.count("package:///%s.stl" % old)
            if n != 2:                       # one visual, one collision
                raise SystemExit("URDF %s: %s found %d times" % (ln, old, n))
            seg = seg.replace("package:///%s.stl" % old, "package:///%s.stl" % new)
            seg = seg.replace('name="%s_material"' % old, 'name="%s_material"' % new)
        txt = txt[:a] + seg + txt[b:]
        log.append("urdf %s: shin sheets and spacer swapped" % ln)
    for ln, stem, T in new_visuals(cad):
        a = txt.index('<link name="%s">' % ln)
        b = txt.rfind("\n", 0, txt.index("</link>", a)) + 1
        txt = txt[:b] + urdf_block(stem, T) + txt[b:]
        log.append("urdf %s: + %s" % (ln, stem))
    return txt, log


def body_segment(txt, body):
    """(start, end) of the body's own geoms: from its <body ... name="body" ...> tag to its first child <body or </body>"""
    m = re.search(r'<body\s+name="%s"[^>]*>' % re.escape(body), txt)
    if not m:
        m = re.search(r'<body\s*\n\s*name="%s"[^>]*>' % re.escape(body), txt)
    if not m:
        raise SystemExit("MJCF: body %s not found" % body)
    s = m.end()
    nxt = min(i for i in (txt.find("<body", s), txt.find("</body>", s)) if i >= 0)
    return s, nxt


def edit_mjcf(txt, cad, name):
    log = []
    R = ranges()
    for jn, (lo, hi) in R.items():
        pat = re.compile(r'(<joint\s+name="%s"[^>]*?range=")([^"]+)(")' % jn, re.S)
        if len(pat.findall(txt)) != 1:
            raise SystemExit("%s: joint %s range found %d times" % (name, jn, len(pat.findall(txt))))
        txt = pat.sub(lambda mm: mm.group(1) + "%.6f %.6f" % (D(lo), D(hi)) + mm.group(3), txt)
        log.append("%s %s range %.1f to %.1f deg" % (name, jn, lo, hi))
    # assets
    stems = sorted(set(SHIN_SWAP.values()) | {s for _, s, _ in new_visuals(cad)})
    a = txt.index("<asset>") + len("<asset>")
    txt = txt[:a] + "".join('\n    <mesh name="%s" file="%s.stl"/>' % (s, s) for s in stems) + txt[a:]
    for ln in SHIN_LINKS:
        s, e = body_segment(txt, ln)
        seg = txt[s:e]
        for old, new in SHIN_SWAP.items():
            n = len(re.findall(r'mesh="%s"' % old, seg))
            if n != 1:
                raise SystemExit("%s %s: geom %s found %d times" % (name, ln, old, n))
            seg = re.sub(r'mesh="%s"' % old, 'mesh="%s"' % new, seg)
        txt = txt[:s] + seg + txt[e:]
    for ln, stem, T in new_visuals(cad):
        s, e = body_segment(txt, ln)
        q = quat_of(T[:3, :3])
        g = ('\n<geom pos="%.6g %.6g %.6g" quat="%.6g %.6g %.6g %.6g" type="mesh" rgba="%s" mesh="%s"/>' %
             (T[0, 3], T[1, 3], T[2, 3], q[0], q[1], q[2], q[3], TPU_RGBA, stem))
        txt = txt[:e] + g + "\n" + txt[e:]
        log.append("%s %s: + %s" % (name, ln, stem))
    return txt, log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    cad = json.load(open(os.path.join(HERE, "sit_cad.json")))
    base_u = L.git_blob("mini_bdx/robots/open_duck_mini_v2/robot.urdf").decode()
    u, log = edit_urdf(base_u, cad)
    outs = {URDF: u}
    for p in MJCF:
        rel = os.path.relpath(p, L.REPO)
        t, lg = edit_mjcf(L.git_blob(rel).decode(), cad, os.path.basename(p))
        outs[p] = t
        log += lg
    for line in log:
        print(line)
    if a.write:
        for p, t in outs.items():
            open(p, "w").write(t)
        print("written:", ", ".join(os.path.relpath(p, L.REPO) for p in outs))


if __name__ == "__main__":
    main()
