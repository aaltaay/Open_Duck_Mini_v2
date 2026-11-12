#!/usr/bin/env python3
"""nest_assembly.py: the duck in its torque-off sit on the nest, against a wall. CAD check only (placement); the sit
pose is the repo's record altaay_lab/twin/sit/sit_pose.json (sim pass only).

Run: python3 nest_assembly.py        (after duck_pins.py and nest_parts.py)
Writes nest_assembly.glb (every node, nest frame, mm scaled to m, z up turned to glTF y up), nest_assembly.json (every
node: name, group, source file, 4x4 placement in the nest frame, colour) and nest_assembly_new_parts.stl (the nest and
the new or changed duck parts only, in the assembled pose, mm).

Placement: the sit pose's trunk is turned to face the room (the duck's forward is the nest's -x) and moved so the middle
of the two seat pins stands on the sun centre. Soles on the ring cloth (2.10 mm above the floor).
The repo parts the nest changes are swapped for the new files: sit_seat, sit_bumper, body_middle_bottom. The plungers
are drawn pressed in as far as the mat pushes them in this pose.
"""
import json
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nestcad_lib as N  # noqa: E402
from nestcad_lib import L  # noqa: E402

SKIP = {"usb_c_charger", "power_switch", "bms", "bno055", "board", "cell", "holder", "raspberrypizerow"}     # as sit_pose.py
TPU_KEYS = ("knee_bumper", "ankle_pad", "hip_pad", "roll_pad_left", "roll_pad_right", "foot_bottom_tpu", "neck_pad", "head_pad")
CHANGED = ("sit_seat", "sit_bumper", "body_middle_bottom")
Z_SOLE = 2 * N.FELT_T + N.CLOTH_T          # the soles rest on the ring cloth
Z_SUN = 2 * N.FELT_T + N.FOIL_T + N.CLOTH_T


def duck_pins_json():
    return json.load(open(os.path.join(HERE, "duck_pins.json")))


def nest_parts_json():
    return json.load(open(os.path.join(HERE, "nest_parts.json")))


def sit_pose():
    return json.load(open(os.path.join(N.LAB, "twin", "sit", "sit_pose.json")))


def trunk_in_nest(P, DP, yaw_deg=180.0, off=(0.0, 0.0)):
    """4x4 of the trunk frame in the nest frame: the recorded sit pose, turned by yaw about z (180 = facing the room),
    the seat pin pair's middle over the sun centre + off, the sim floor (z 0) lifted to the sole height on the mat"""
    Tt = np.array(P["trunk_T_mm"])
    c, s = np.cos(np.radians(yaw_deg)), np.sin(np.radians(yaw_deg))
    Rz = np.array([[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1.0]])
    T = Rz @ Tt
    mid = (np.array(DP["pins"]["seat_L"]["block_face_trunk_mm"]) + np.array(DP["pins"]["seat_R"]["block_face_trunk_mm"])) / 2
    w = (T @ np.append(mid, 1.0))[:3]
    T[0, 3] += off[0] - w[0]
    T[1, 3] += off[1] - w[1]
    T[2, 3] += Z_SOLE
    return T


def mat_top(x, y):
    """height of the mat's top surface at a point (nest frame): cloth where there is cloth"""
    r_ = np.hypot(x, y)
    if r_ <= N.SUN_R:
        return Z_SUN
    if N.RING_R0 <= r_ <= N.RING_R1 and x <= N.WALL_X - N.RING_BACK:
        return Z_SOLE
    if r_ <= N.TOP_R:
        return 2 * N.FELT_T
    return N.FELT_T if r_ <= N.BASE_R else 0.0


def load_part(name):
    return trimesh.load(os.path.join(N.STL_DIR, name + ".stl"), force="mesh")


def pin_meshes(Tn, DP, which, side):
    """plunger and socket of one pin in the nest frame, the plunger pressed in by the mat; returns meshes and numbers"""
    P = N.PIN
    T = Tn @ N.pin_frame(which)
    y = N.PIN_Y if side == "L" else -N.PIN_Y
    r_ = N.BLOCK[which]["r"]
    face = (T @ np.array([0, y, -r_, 1.0]))[:3]
    tip_free = (T @ np.array([0, y, -r_ - N.PROUD[which], 1.0]))[:3]
    zt = mat_top(face[0], face[1])
    u = T[:3, 2]
    comp = max(0.0, (zt - tip_free[2]) / u[2])                    # along the pin axis
    comp_draw = min(comp, N.PROUD[which])                          # past flush the TPU would be squashed: not drawn
    t0 = -r_ - N.PROUD[which] + comp_draw
    head = trimesh.creation.icosphere(subdivisions=2, radius=P["tip_d"] / 2)
    head.apply_translation((0, y, t0 + P["tip_d"] / 2))
    head.apply_transform(T)
    mouth = -r_ - N.PROUD[which] + P["exposed"]
    plunger = trimesh.util.concatenate([head, N.cyl_u(T, y, t0 + P["tip_d"] / 2, mouth + 2.0, P["tube_d"], 16)])
    socket = trimesh.util.concatenate([N.cyl_u(T, y, mouth, mouth + P["socket_len"], P["socket_d"], 16),
                                       N.cyl_u(T, y, mouth + P["socket_len"], mouth + P["socket_len"] + P["tail_len"], 1.2, 12)])
    return plunger, socket, dict(face_xy=np.round(face[:2], 2).tolist(), face_z=N.r(face[2]), mat_top_z=N.r(zt), gap_mm=N.r(face[2] - zt),
                                 compression_mm=N.r(comp), force_n=N.r(N.pin_force(comp)), zone="sun" if zt == Z_SUN else "ring" if zt == Z_SOLE else "felt")


# The leads inside the trunk (trunk frame, mm). Names are proposals for wiring/netlist.yaml.
#   NP1, NP2  seat pins (plus), 22 AWG, from each solder cup to the splice JNP on the belly floor
#   NP3       JNP to DK6.VIN (the dock supply ideal diode of D50, twin/dock/dock_routes.json terminal), 20 AWG
#   NM1, NM2  bumper pins (minus), 22 AWG, up the gap in front of trunk_bottom to the splice JNM (where JGD was)
#   NM3       JNM to BMS.P-: the old cable DC2's second leg, kept as routed (twin/dock/dock_routes.json run DC2), 20 AWG
# The duck-side charger board (it moves from the dock into the duck) has no seat yet: its input would tap JNP (BLOCKER).
JNP, JNM = (-101.0, 10.0, -6.0), (24.0, -4.0, 31.0)
DK6_VIN = (-104.0, -4.5, 43.0)
DC2_LEG = [(-16.0, -25.0, 33.0), (-115.0, -30.0, 38.0), (-124.0, -31.0, 35.0), (-126.0, -31.0, 33.0), (-126.3, -31.5, 33.0)]


def routes(DP):
    """{name: dict(points, d, gauge, note)} in the trunk frame"""
    ts = DP["parts"]["pin_carrier_seat"]["tail_end_trunk_mm"]
    tb = DP["parts"]["pin_carrier_bumper"]["tail_end_trunk_mm"]
    R = {}
    R["NP1"] = dict(points=[ts["L"], (-108.3, 10.0, -12.0), (-104.0, 10.0, -8.0), JNP], d=1.7, gauge="22 AWG silicone", pole="plus")
    R["NP2"] = dict(points=[ts["R"], (-108.3, -10.0, -12.0), (-105.0, 0.0, -10.5), (-102.5, 7.0, -7.5), JNP], d=1.7, gauge="22 AWG silicone", pole="plus")
    R["NP3"] = dict(points=[JNP, (-100.0, 10.0, 0.0), (-100.0, 10.0, 39.0), (-103.0, 1.0, 40.5), (-104.0, -5.0, 41.0), DK6_VIN], d=2.0, gauge="20 AWG", pole="plus")
    R["NM1"] = dict(points=[tb["L"], (21.7, 10.0, -20.0), (22.0, 10.0, 20.0), (23.0, 3.0, 28.0), JNM], d=1.7, gauge="22 AWG silicone", pole="minus")
    R["NM2"] = dict(points=[tb["R"], (21.7, -10.0, -20.0), (22.0, -10.0, 22.0), JNM], d=1.7, gauge="22 AWG silicone", pole="minus")
    R["NM3"] = dict(points=[JNM] + DC2_LEG, d=2.0, gauge="20 AWG", pole="minus", note="the old DC2 leg, as routed in twin/dock/dock_routes.json")
    for v in R.values():
        P = np.array(v["points"], float)
        v["points"] = P
        v["length_mm"] = N.r(np.linalg.norm(np.diff(P, axis=0), axis=1).sum(), 1)
    return R


def tube(pts, d):
    ms = []
    for a, b in zip(pts[:-1], pts[1:]):
        if np.linalg.norm(b - a) > 1e-6:
            ms.append(L.cyl(a, b, d / 2.0, 10))
    for p in pts[1:-1]:
        s = trimesh.creation.icosphere(subdivisions=1, radius=d / 2.0)
        s.apply_translation(p)
        ms.append(s)
    return trimesh.util.concatenate(ms)


def scene(yaw_deg=180.0, off=(0.0, 0.0), duck=True, room=True, standins=True, cover=True):
    """[dict(name, group, mesh (nest frame, mm), rgba, source, T (4x4 or None))], and the numbers of this placement"""
    DP, NP = duck_pins_json(), nest_parts_json()
    out, info = [], {}
    # ---- the nest
    colour = dict(nest_felt_base="felt2", nest_felt_top="felt", nest_sun="sun", nest_sun_foil="foil", nest_ring="ring", nest_feed="foil",
                  nest_box_tray="box", nest_box_lid="box", nest_rim_cover="rim", nest_bolster_left="felt2", nest_bolster_right="felt2")
    for k in NP["parts"]:
        if k == "nest_rim_cover" and not cover:
            continue
        out.append(dict(name=k, group="nest", mesh=load_part(k), rgba=N.COL[colour[k]], source="stl/%s.stl" % k, T=np.eye(4)))
    if standins:
        for k, v in NP["standins"].items():
            s, c = np.array(v["size"]), np.array(v["c"])
            out.append(dict(name="standin_" + k, group="nest_standin", mesh=L.box(c - s / 2, c + s / 2), rgba=N.COL["board" if "board" in k else "metal"],
                            source="stand-in box: " + v["note"], T=np.eye(4)))
    if room:
        wall = L.box((N.WALL_X, -420, 0), (N.WALL_X + 12, 420, 520))
        floor = L.box((-480, -420, -6), (N.WALL_X + 12, 420, 0))
        out.append(dict(name="wall", group="room", mesh=wall, rgba=N.COL["wall"], source="reference", T=np.eye(4)))
        out.append(dict(name="floor", group="room", mesh=floor, rgba=N.COL["floor"], source="reference", T=np.eye(4)))
    if not duck:
        return out, info
    # ---- the duck
    P = sit_pose()
    S = L.scene(fresh=True)
    Tl = S.link_T({k: np.radians(v) for k, v in P["joints_deg"].items()})
    Tn = trunk_in_nest(P, DP, yaw_deg, off)
    info["trunk_T_nest_mm"] = np.round(Tn, 5).tolist()
    for i in S.inst:
        if i["key"] in SKIP:
            continue
        Tw = Tn @ Tl[i["link"]] @ i["T"]
        if i["key"] in CHANGED:
            m = load_part(i["key"])
            src, grp = "stl/%s.stl (changed)" % i["key"], "duck_changed"
        else:
            m = S.mesh(i).copy()
            if i.get("mirrored"):
                m.invert()
            src, grp = os.path.relpath(i["path"], N.REPO), "duck"
        m.apply_transform(Tw)
        ln = i["link"]
        if i["key"] in ("sit_seat", "sit_bumper") or i["key"] in TPU_KEYS:
            col = N.COL["tpu"]
        elif "foot" in ln:
            col = N.COL["foot"]
        elif ln.startswith(("knee", "hip", "left_roll", "right_roll")):
            col = N.COL["leg"]
        else:
            col = N.COL["duck"]
        out.append(dict(name="%s#%d" % (i["key"], i["idx"]), group=grp, mesh=m, rgba=col, source=src, T=Tw, key=i["key"], link=ln))
    allv = np.vstack([o["mesh"].vertices for o in out if o["group"].startswith("duck")])
    k = int(np.argmax(allv[:, 0]))
    info["tail_to_wall_mm"] = N.r(N.WALL_X - allv[k, 0], 1)
    info["tail_z_mm"] = N.r(allv[k, 2], 1)
    info["duck_extent_nest_mm"] = np.round([allv.min(0), allv.max(0)], 1).tolist()
    info["pins"] = {}
    for which, car in (("seat", "pin_carrier_seat"), ("bump", "pin_carrier_bumper")):
        Tc = Tn @ np.array(DP["placements"][car][0]["T_link_mm"])
        m = load_part(car)
        m.apply_transform(Tc)
        out.append(dict(name=car, group="duck_new", mesh=m, rgba=N.COL["carrier"], source="stl/%s.stl (new)" % car, T=Tc))
        for side in ("L", "R"):
            pl, so, nf = pin_meshes(Tn, DP, which, side)
            nm = "%s_%s" % (which, side)
            info["pins"][nm] = nf
            out.append(dict(name="pin_plunger_" + nm, group="duck_new", mesh=pl, rgba=N.COL["pin"], source="bought: probe (stand-in)", T=None))
            out.append(dict(name="pin_socket_" + nm, group="duck_new", mesh=so, rgba=N.COL["socket"], source="bought: socket (stand-in)", T=None))
    for nm, v in routes(DP).items():
        w = tube(v["points"], v["d"])
        w.apply_transform(Tn)
        out.append(dict(name="lead_" + nm, group="duck_new", mesh=w, rgba=N.COL["wire_p" if v["pole"] == "plus" else "wire_m"],
                        source="%s lead, %s" % (v["gauge"], v.get("note", "new route")), T=None))
    return out, info


def write_glb(items, path, max_faces=None):
    sc = trimesh.Scene()
    for it in items:
        m = it["mesh"].copy()
        if max_faces and len(m.faces) > max_faces and it["group"] == "duck":
            try:
                m = m.simplify_quadric_decimation(face_count=max_faces)
            except Exception:
                pass
        m.apply_scale(0.001)
        m = trimesh.Trimesh(m.vertices, m.faces, process=True)                      # shared vertices, no per-face colours
        m.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
            baseColorFactor=[float(c) for c in it["rgba"]], metallicFactor=0.0, roughnessFactor=0.9, name=it["name"]))
        sc.add_geometry(m, node_name=it["name"], geom_name=it["name"])
    R = trimesh.transformations.rotation_matrix(-np.pi / 2, (1, 0, 0))          # z up to glTF y up
    sc.apply_transform(R)
    sc.export(path)
    return os.path.getsize(path)


def main():
    items, info = scene()
    nodes = [dict(name=it["name"], group=it["group"], source=it["source"], rgba=list(it["rgba"]), faces=int(len(it["mesh"].faces)),
                  T_nest_mm=None if it["T"] is None else np.round(it["T"], 5).tolist()) for it in items]
    for mf in (None, 8000, 4000, 2000, 1000, 500):
        size = write_glb(items, os.path.join(HERE, "nest_assembly.glb"), mf)
        if size < 4.8e6:
            break
    if size > 5e6:
        raise SystemExit("nest_assembly.glb is over 5 MB")
    own = trimesh.util.concatenate([it["mesh"] for it in items if it["group"] in ("nest", "duck_new", "duck_changed")])
    own.export(os.path.join(HERE, "nest_assembly_new_parts.stl"))
    own_bytes = os.path.getsize(os.path.join(HERE, "nest_assembly_new_parts.stl"))
    if own_bytes > 5e6:
        raise SystemExit("nest_assembly_new_parts.stl is over 5 MB")
    N.dump(dict(generated_by="nest_assembly.py", label="CAD check only (placement); sim pass only (the sit pose, twin/sit/sit_pose.json)",
                frame="nest frame, mm (the GLB is in m, y up)", glb="nest_assembly.glb", glb_bytes=size,
                new_parts_stl="nest_assembly_new_parts.stl", new_parts_stl_bytes=own_bytes,
                new_parts_stl_note="one STL, nest frame, mm: every nest part and every new or changed duck part in the assembled pose (no repo duck meshes)",
                glb_note="repo duck meshes decimated to at most %s faces each to keep the file under 5 MB; the nest and the new duck parts are exact" % mf if mf else "all meshes exact",
                **info, nodes=nodes), os.path.join(HERE, "nest_assembly.json"))
    print("nodes", len(nodes), "glb bytes", size, "decimate", mf)
    print(json.dumps(info["pins"], indent=0))


if __name__ == "__main__":
    main()
