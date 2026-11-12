#!/usr/bin/env python3
"""sit_contacts.py: what touches the floor in the D59 alert sit (torque off), where, and with how much force.
sim pass only (MuJoCo, the repo's own sit model built by twin/sit/sit_model.py into a scratch folder; repo read only).
Also: (a) the same sit with a low dome under the seat block (the 'egg' / nest centre), heights 0 to 6 mm,
      (b) silhouettes of the sitting and standing duck for the sketches (convex hull per mesh geom),
      (c) clearances: belly underside, bumper, rear-most point (wall side), head height.

  PYTHONDONTWRITEBYTECODE=1 python3 sit_contacts.py <scratch>/model
Writes sit_contacts.json and duck_outline.json next to this file.
"""
import json
import os
import sys

import numpy as np

sys.dont_write_bytecode = True
REPO_SIT = os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")), "twin", "sit")  # altaay_lab/twin/sit, relative to this file
sys.path.insert(0, REPO_SIT)
import mujoco as m  # noqa: E402
import sit_sim as S  # noqa: E402
import sit_model as SM  # noqa: E402
from scipy.spatial import ConvexHull  # noqa: E402

OUT = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))


def model_with_dome(h_mm, r_mm=60.0, x_mm=-128.7, mu=0.8, under="seat"):
    """the sit model plus a rigid disc of height h on the floor (top at z = h).
    under='seat': centred where the seat block lands. Same collision edits as sit_sim.model()."""
    d = os.path.join(OUT, "sit")
    xml = open(os.path.join(d, "scene_flat_terrain.xml")).read()
    if h_mm > 0:
        g = ('<geom name="dome" type="cylinder" size="%.4f %.5f" pos="%.4f 0 %.5f" rgba="0.9 0.8 0.3 1" '
             'contype="1" conaffinity="1" friction="%.2f 0.02 0.002"/>' % (r_mm / 1000, h_mm / 2000, x_mm / 1000, h_mm / 2000, mu))
        assert "</worldbody>" in xml
        i = xml.rindex("</worldbody>")               # the last one: an earlier worldbody in the scene file is commented out
        xml = xml[:i] + g + xml[i:]
    md = m.MjModel.from_xml_string(xml, assets=SM.assets(d))
    for g in range(md.ngeom):
        nm = m.mj_id2name(md, m.mjtObj.mjOBJ_GEOM, g) or ""
        if nm in ("floor", "dome"):
            md.geom_contype[g], md.geom_conaffinity[g] = 1, 1
            md.geom_friction[g] = [mu, 0.02, 0.002]
            continue
        if md.geom_group[g] == 2 or nm in S.SOLES:
            md.geom_contype[g], md.geom_conaffinity[g] = 0, 1
            if nm not in S.SOLES:
                md.geom_friction[g] = [0.8, 0.02, 0.002]
    return md


def frame(md, dd):
    tr = m.mj_name2id(md, m.mjtObj.mjOBJ_BODY, "trunk_assembly")
    Rt = dd.xmat[tr].reshape(3, 3)
    head = np.arctan2(Rt[1, 0], Rt[0, 0])
    f = np.array([np.cos(head), np.sin(head)])
    l_ = np.array([-f[1], f[0]])
    return tr, dd.xpos[tr].copy(), f, l_, head


def contacts(md, dd):
    """per robot geom touching the world: normal force (N) and the force-weighted contact point (world, m)"""
    F, P = {}, {}
    for i in range(dd.ncon):
        c = dd.contact[i]
        w = np.zeros(6)
        m.mj_contactForce(md, dd, i, w)
        if w[0] <= 0:
            continue
        for g in (c.geom1, c.geom2):
            n = m.mj_id2name(md, m.mjtObj.mjOBJ_GEOM, g) or "geom%d" % g
            if n in ("floor", "dome"):
                continue
            F[n] = F.get(n, 0.0) + float(w[0])
            P[n] = P.get(n, np.zeros(3)) + float(w[0]) * c.pos
    return F, P


def geom_verts(md, dd, g):
    mid = md.geom_dataid[g]
    a, n = md.mesh_vertadr[mid], md.mesh_vertnum[mid]
    return md.mesh_vert[a:a + n] @ dd.geom_xmat[g].reshape(3, 3).T + dd.geom_xpos[g]


def outline(md, dd):
    """convex hull per visual mesh geom, in the heading frame (x forward, y left, z up; origin under the trunk origin, mm)"""
    tr, tp, f, l_, head = frame(md, dd)
    HEADB = {m.mj_name2id(md, m.mjtObj.mjOBJ_BODY, n) for n in ("head_assembly", "neck_yaw_assembly", "head_pitch_to_yaw", "neck_pitch_assembly")}
    FOOTB = {m.mj_name2id(md, m.mjtObj.mjOBJ_BODY, n) for n in S.FEET}
    out = []
    seen = set()
    for g in range(md.ngeom):
        if md.geom_type[g] != m.mjtGeom.mjGEOM_MESH:
            continue
        nm = m.mj_id2name(md, m.mjtObj.mjOBJ_GEOM, g) or "geom%d" % g
        key = (md.geom_dataid[g], md.geom_bodyid[g], tuple(np.round(md.geom_pos[g], 5)))
        if key in seen:
            continue
        seen.add(key)
        V = geom_verts(md, dd, g)
        X = np.c_[(V[:, :2] - tp[:2]) @ f, (V[:, :2] - tp[:2]) @ l_, V[:, 2]] * 1000
        b = md.geom_bodyid[g]
        bn = m.mj_id2name(md, m.mjtObj.mjOBJ_BODY, b)
        kind = ("sole" if nm in S.SOLES else "seat" if "sit_seat" in nm else "bumper" if "sit_bumper" in nm else
                "foot" if b in FOOTB else "head" if b in HEADB else "trunk" if b == tr else "leg")
        rec = dict(name=nm, body=bn, kind=kind, side="L" if X[:, 1].mean() > 15 else "R" if X[:, 1].mean() < -15 else "C")
        for tag, ax in (("side", (0, 2)), ("top", (0, 1)), ("front", (1, 2))):
            P = X[:, list(ax)]
            try:
                hh = ConvexHull(P)
                rec[tag] = np.round(P[hh.vertices], 1).tolist()
            except Exception:
                rec[tag] = []
        rec["depth_y"] = round(float(X[:, 1].mean()), 1)
        rec["depth_z"] = round(float(X[:, 2].mean()), 1)
        rec["depth_x"] = round(float(X[:, 0].mean()), 1)
        out.append(rec)
    return out


def geometry(md, dd):
    """heights and extents in the heading frame (mm)"""
    tr, tp, f, l_, head = frame(md, dd)
    allv, by = [], {}
    for g in range(md.ngeom):
        if md.geom_type[g] != m.mjtGeom.mjGEOM_MESH:
            continue
        nm = m.mj_id2name(md, m.mjtObj.mjOBJ_GEOM, g) or "geom%d" % g
        V = geom_verts(md, dd, g)
        X = np.c_[(V[:, :2] - tp[:2]) @ f, (V[:, :2] - tp[:2]) @ l_, V[:, 2]] * 1000
        allv.append(X)
        by[nm] = X
    A = np.vstack(allv)
    res = dict(trunk_z_mm=round(float(tp[2] * 1000), 1))
    res["extent_mm"] = dict(back=round(float(A[:, 0].min()), 1), front=round(float(A[:, 0].max()), 1),
                            right=round(float(A[:, 1].min()), 1), left=round(float(A[:, 1].max()), 1), top=round(float(A[:, 2].max()), 1))
    # rear-most point of the robot at a few height bands (what a wall or a back rest would meet first)
    res["rear_profile_mm"] = []
    for z0, z1 in ((0, 20), (20, 40), (40, 60), (60, 80), (80, 100), (100, 130), (130, 160), (160, 200), (200, 260), (260, 340)):
        s = A[(A[:, 2] >= z0) & (A[:, 2] < z1)]
        if len(s):
            i = s[:, 0].argmin()
            res["rear_profile_mm"].append(dict(z_band=[z0, z1], rear_x=round(float(s[i, 0]), 1), at_y=round(float(s[i, 1]), 1)))
    # which geom is rear-most
    rear = min(by.items(), key=lambda kv: kv[1][:, 0].min())
    res["rear_most_geom"] = dict(name=rear[0], x=round(float(rear[1][:, 0].min()), 1), z_at=round(float(rear[1][rear[1][:, 0].argmin(), 2]), 1))
    # underside clearance map on the centre band: lowest robot point per (x, y) cell
    cells = {}
    for x0 in range(-160, 80, 10):
        for y0 in (-50, -30, -10, 10, 30):
            s = A[(A[:, 0] >= x0) & (A[:, 0] < x0 + 10) & (A[:, 1] >= y0) & (A[:, 1] < y0 + 20)]
            if len(s):
                cells["%d,%d" % (x0, y0)] = round(float(s[:, 2].min()), 1)
    res["underside_lowest_z_mm_cells_x10_y20"] = cells
    band = {}
    for x0 in range(-160, 80, 10):
        s = A[(A[:, 0] >= x0) & (A[:, 0] < x0 + 10) & (abs(A[:, 1]) < 30)]
        if len(s):
            band[str(x0)] = round(float(s[:, 2].min()), 1)
    res["underside_lowest_z_mm_centre_band_absy30"] = band
    for key, pat in (("seat", "sit_seat"), ("bumper", "sit_bumper")):
        for nm, X in by.items():
            if pat in nm and "collision" in nm:
                i = X[:, 2].argmin()
                low = X[X[:, 2] < X[:, 2].min() + 1.0]
                res[key] = dict(lowest_z=round(float(X[i, 2]), 2), lowest_at_xy=[round(float(X[i, 0]), 1), round(float(X[i, 1]), 1)],
                                x_range=[round(float(X[:, 0].min()), 1), round(float(X[:, 0].max()), 1)],
                                y_range=[round(float(X[:, 1].min()), 1), round(float(X[:, 1].max()), 1)],
                                z_range=[round(float(X[:, 2].min()), 1), round(float(X[:, 2].max()), 1)],
                                within_1mm_of_lowest_x=[round(float(low[:, 0].min()), 1), round(float(low[:, 0].max()), 1)],
                                within_1mm_of_lowest_y=[round(float(low[:, 1].min()), 1), round(float(low[:, 1].max()), 1)])
    # head and camera height (head body origin)
    hb = m.mj_name2id(md, m.mjtObj.mjOBJ_BODY, "head_assembly")
    res["head_body_xyz_mm"] = [round(float(((dd.xpos[hb][:2] - tp[:2]) @ f) * 1000), 1), round(float(((dd.xpos[hb][:2] - tp[:2]) @ l_) * 1000), 1),
                               round(float(dd.xpos[hb][2] * 1000), 1)]
    com = dd.subtree_com[1]
    res["com_xyz_mm"] = [round(float(((com[:2] - tp[:2]) @ f) * 1000), 1), round(float(((com[:2] - tp[:2]) @ l_) * 1000), 1), round(float(com[2] * 1000), 1)]
    return res


def sit(md, mu_note="", want_outline=False):
    dd, c0 = S.stance_start(md)
    stand_geo = geometry(md, dd)
    stand_out = outline(md, dd) if want_outline else None
    stand_F, _ = contacts(md, dd)
    c = c0
    for (h, k, a, n, hd), T in S.DOWN:
        c = S.ramp(md, dd, c, S.targets(md, h, k, a, n, hd), T)
    c = S.ramp(md, dd, c, S.targets(md, *S.SIT), 1.5)
    for _ in range(int(0.5 / md.opt.timestep)):
        m.mj_step(md, dd)
    S.torque(md, False)
    for _ in range(int(10.0 / md.opt.timestep)):
        m.mj_step(md, dd)
    acc, accP, n = {}, {}, int(2.0 / md.opt.timestep)
    for _ in range(n):
        m.mj_step(md, dd)
        F, P = contacts(md, dd)
        for k, v in F.items():
            acc[k] = acc.get(k, 0.0) + v
            accP[k] = accP.get(k, np.zeros(3)) + P[k]
    tr, tp, f, l_, head = frame(md, dd)
    con = {}
    for k, v in acc.items():
        if v / n < 0.005:
            continue
        p = accP[k] / v
        con[k] = dict(N=round(v / n, 2), centre_of_pressure_trunk_frame_mm=[round(float(((p[:2] - tp[:2]) @ f) * 1000), 1),
                                                                             round(float(((p[:2] - tp[:2]) @ l_) * 1000), 1)],
                      z_mm=round(float(p[2] * 1000), 2))
    ts = S.trunk_state(md, dd)
    res = dict(contacts=con, sum_N=round(sum(v["N"] for v in con.values()), 2), weight_N=round(float(md.body_subtreemass[1] * 9.81), 2),
               trunk={k: round(v, 3) for k, v in ts.items()}, speed_m_s=round(float(np.linalg.norm(dd.qvel[:3])), 5),
               geometry=geometry(md, dd))
    S.torque(md, True)
    return res, (outline(md, dd) if want_outline else None), stand_geo, stand_out, stand_F


if __name__ == "__main__":
    R = dict(label="sim pass only", model="twin/sit/sit_model.py round-2 model (2.8078 kg), flat floor mu 0.8 unless said; torque off, 10 s settle, mean of 2 s")
    md0 = model_with_dome(0)
    base, out_sit, stand_geo, out_stand, stand_F = sit(md0, want_outline=True)
    R["flat_floor"] = base
    R["standing"] = dict(geometry=stand_geo, contacts_N={k: round(v, 2) for k, v in stand_F.items()})
    print("flat:", {k: v["N"] for k, v in base["contacts"].items()}, base["trunk"])
    R["dome_under_seat"] = []
    for h in (1, 2, 3, 4, 5, 6, 8):
        r, *_ = sit(model_with_dome(h))
        row = dict(dome_height_mm=h, dome_radius_mm=60, contacts={k: v["N"] for k, v in r["contacts"].items()},
                   cop={k: v["centre_of_pressure_trunk_frame_mm"] for k, v in r["contacts"].items()},
                   trunk=r["trunk"], bumper_lowest_z=r["geometry"].get("bumper", {}).get("lowest_z"), speed=r["speed_m_s"])
        R["dome_under_seat"].append(row)
        print("dome", h, row["contacts"], "pitch", r["trunk"].get("pitch"), "bumper z", row["bumper_lowest_z"], flush=True)
    # a wider disc that also reaches under the belly bumper (a low 'pebble' the trunk sits on, feet beside it)
    R["dome_under_seat_and_bumper"] = []
    for h in (3, 5, 8):
        mdw = model_with_dome(h, r_mm=75.0, x_mm=-18.7 - 45.0)
        r, *_ = sit(mdw)
        row = dict(height_mm=h, disc="r 75 mm centred 45 mm behind the trunk origin (covers seat and bumper, between the soles)",
                   contacts={k: v["N"] for k, v in r["contacts"].items()},
                   cop={k: v["centre_of_pressure_trunk_frame_mm"] for k, v in r["contacts"].items()}, trunk=r["trunk"], speed=r["speed_m_s"])
        R["dome_under_seat_and_bumper"].append(row)
        print("pebble", h, row["contacts"], r["trunk"], flush=True)
    json.dump(R, open(os.path.join(HERE, "sit_contacts.json"), "w"), indent=1)
    json.dump(dict(label="sim pass only; convex hull per mesh geom, heading frame, mm (x forward, y left, z up, origin on the floor under the trunk origin)",
                   sit=out_sit, stand=out_stand), open(os.path.join(HERE, "duck_outline.json"), "w"))
