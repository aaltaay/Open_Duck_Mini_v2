#!/usr/bin/env python3
"""duck_pins.py: the duck side of the nest. Four spring pins under the body: two in the seat block (plus), two in the
belly bumper (minus). CAD check only (geometry), calc only (masses, forces).

Run: NEST_OCP=<folder with OCP> python3 duck_pins.py
Reads (never writes) the repo: robot.urdf, print/sit_seat.stl, print/sit_bumper.stl, print/body_middle_bottom.stl.
Writes stl/, step/ and duck_pins.json next to this file.

Parts (trunk frame = robot.urdf base frame at the zero pose, mm):
  sit_seat (changed, TPU 95A)        the D59 seat block with a pocket from its top face for the pin carrier and two
                                     plunger wells (3.6 mm) down to its floor face. Outer shape unchanged.
  sit_bumper (changed, TPU 95A)      the D59 belly bumper, the same way. Outer shape unchanged.
  pin_carrier_seat (new, PLA)        a rigid holder for the two probe sockets of the seat: two 7 mm columns joined by a
  pin_carrier_bumper (new, PLA)      3 mm web, under a 2.5 mm flange that lies on VHB against the body underside. It
                                     sits in the block's pocket, so the block holds it captive: no screw (D39: a
                                     printed seat holds the part; D42: no screw pattern to make uniform).
  body_middle_bottom (changed, PLA)  four 3.4 mm feedthroughs on the pin axes, one per pin: the socket's solder cup and
                                     its 22 AWG lead pass through (a named purpose, D39).
  pin_gauge (new, PLA, a tool)       two steps, 3.0 and 7.5 mm: the plunger tip is pressed level with the step that
                                     lies on the block's floor face while the socket is pressed into the carrier, so
                                     the tip height does not depend on the socket or probe length.
  spring_pin_ref                     a stand-in of the bought probe and socket for the assembly (dimensions est).
The pins stand along the floor normal of the torque-off sit (2.6 deg from trunk z, sim/calib.json), 20 mm apart, on the
lowest line of each block: 130.0 mm between the seat pair and the bumper pair along the floor.
"""
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nestcad_lib as N  # noqa: E402
from nestcad_lib import L  # noqa: E402

BIG = 400.0


def halfspace_below(P0, n, depth=BIG):
    """a big box filling the side of the plane (point P0, unit normal n) that n points AWAY from"""
    T = trimesh.geometry.align_vectors([0, 0, 1], n)
    T[:3, 3] = P0
    return L.box((-BIG, -BIG, -depth), (BIG, BIG, 0.0), T)


def underside_plane(body, T, which):
    """the body underside over the carrier flange: ray cast along the pin axis, plane fit. Returns point, unit normal
    (pointing down, out of the body), the fit residual and the inner-face height above the underside on each pin axis"""
    C = N.CARRIER
    u = T[:3, 2]
    pts = []
    for xl in np.linspace(-C["flange_x"] / 2, C["flange_x"] / 2, 5):
        for yl in np.linspace(-C["flange_y"] / 2, C["flange_y"] / 2, 9):
            o = (T @ np.array([xl, yl, -5.0, 1.0]))[:3]
            loc, _, _ = body.ray.intersects_location([o], [u])
            if len(loc):
                d = (loc - o) @ u
                pts.append(loc[np.argmin(d)])
    pts = np.array(pts)
    c = pts.mean(0)
    _, _, Vt = np.linalg.svd(pts - c)
    n = Vt[2]
    if n @ u > 0:
        n = -n
    res = float(np.abs((pts - c) @ n).max())
    walls = {}
    for yl in (N.PIN_Y, -N.PIN_Y):
        o = (T @ np.array([0.0, yl, -5.0, 1.0]))[:3]
        loc, _, _ = body.ray.intersects_location([o], [u])
        d = np.sort((loc - o) @ u)
        walls[yl] = (float(d[0]) - 5.0, float(d[1]) - 5.0)             # local u of the underside and of the inner face
    return c, n, res, walls


def build_block(S, body, which):
    B, C, P = N.BLOCK[which], N.CARRIER, N.PIN
    T = N.pin_frame(which)
    u = T[:3, 2]
    r_ = B["r"]
    inst = L.inst(S, B["stl"], B["stl"])
    old = S.world_mesh(inst)
    c, n, res, walls = underside_plane(body, T, which)
    top0 = c + N.VHB_T * n                                             # the carrier top plane: VHB below the underside
    u_top = float((top0 - T[:3, 3]) @ u)                               # about, on the pair centre line
    # ---- carrier, built in the pin frame (exact local coordinates), then placed
    Ti = np.linalg.inv(T)
    hi = u_top + 12.0
    below_top = L.xform(N.man(halfspace_below(top0, -n)), Ti)                        # under the carrier top plane
    above_flange_floor = L.xform(N.man(halfspace_below(top0 + C["flange_t"] * n, n)), Ti)
    cols = [N.mcyl(y, C["u_bot"], hi, C["col_d"], 48) for y in (N.PIN_Y, -N.PIN_Y)]
    web = N.mbox((-C["web_t"] / 2, -N.PIN_Y, C["u_bot"]), (C["web_t"] / 2, N.PIN_Y, hi))
    fl = N.mbox((-C["flange_x"] / 2, -C["flange_y"] / 2, C["u_bot"] + 1.0), (C["flange_x"] / 2, C["flange_y"] / 2, hi))
    body_c = (L.union(cols + [web]) + (fl ^ above_flange_floor)) ^ below_top
    bores = L.union([N.mcyl(y, C["u_bot"] - 2, hi, P["mount_hole"], 24) for y in (N.PIN_Y, -N.PIN_Y)])
    carrier = L.xform(body_c - bores, T)
    # ---- the block: pocket (the carrier grown by the fit, open to the top) and the plunger wells
    f = C["fit"]
    pk = [N.mcyl(y, C["u_bot"] - f, hi, C["col_d"] + 2 * f, 48) for y in (N.PIN_Y, -N.PIN_Y)]
    pk.append(N.mbox((-C["web_t"] / 2 - f, -N.PIN_Y, C["u_bot"] - f), (C["web_t"] / 2 + f, N.PIN_Y, hi)))
    pfl = N.mbox((-C["flange_x"] / 2 - f, -C["flange_y"] / 2 - f, C["u_bot"] + 1.0), (C["flange_x"] / 2 + f, C["flange_y"] / 2 + f, hi))
    pocket_l = L.union(pk) + (pfl ^ L.xform(N.man(halfspace_below(top0 + (C["flange_t"] + f) * n, n)), Ti))
    wells_l = L.union([N.mcyl(y, -r_ - 3.0, C["u_bot"], N.TPU_BORE, 24) for y in (N.PIN_Y, -N.PIN_Y)])
    pocket = L.xform(pocket_l + wells_l, T)
    new = N.man(old) - pocket
    # ---- the body feedthroughs: from below the underside to above the inner face, a 0.8 mm 45 deg mouth inside
    holes = []
    for y in (N.PIN_Y, -N.PIN_Y):
        u0, u1 = walls[y]
        holes.append(N.man(N.cyl_u(T, y, u0 - 1.0, u1 + 1.0, N.BODY_HOLE, 24)))
        cone = trimesh.creation.cone(radius=N.BODY_HOLE / 2 + 1.6, height=N.BODY_HOLE / 2 + 1.6, sections=24)
        cone.apply_transform(trimesh.transformations.rotation_matrix(np.pi, (1, 0, 0)))          # apex down
        cone.apply_translation((0.0, y, u1 + 0.8))            # at the inner face the mouth is hole + 2 x 0.8 across
        cone.apply_transform(T)
        holes.append(N.man(cone) ^ N.man(N.cyl_u(T, y, u1 - 0.8, u1 + 3.0, 12.0, 24)))
    holes = L.union(holes)
    # ---- the bought pin, plunger free (stand-in)
    tip_u = {y: -r_ - N.PROUD[which] for y in (N.PIN_Y, -N.PIN_Y)}
    pins = []
    for y in (N.PIN_Y, -N.PIN_Y):
        t = tip_u[y]
        head = trimesh.creation.icosphere(subdivisions=2, radius=P["tip_d"] / 2)
        head.apply_translation((0, y, t + P["tip_d"] / 2))
        head.apply_transform(T)
        plunger = N.cyl_u(T, y, t + P["tip_d"] / 2, t + P["exposed"] + 2.0, P["tube_d"], 16)
        socket = N.cyl_u(T, y, t + P["exposed"], t + P["exposed"] + P["socket_len"], P["socket_d"], 16)
        tail = N.cyl_u(T, y, t + P["exposed"] + P["socket_len"], t + P["exposed"] + P["socket_len"] + P["tail_len"], 1.2, 12)
        pins.append(dict(y=y, plunger=trimesh.util.concatenate([head, plunger]), socket=trimesh.util.concatenate([socket, tail]),
                         tip=(T @ np.array([0, y, t, 1.0]))[:3], face=(T @ np.array([0, y, -r_, 1.0]))[:3],
                         tail_end=(T @ np.array([0, y, t + P["exposed"] + P["socket_len"] + P["tail_len"], 1.0]))[:3]))
    # the carrier's part frame: flange face on the bed (z up out of the flange), origin on the pair centre line
    Tp = np.eye(4)
    zp = n / np.linalg.norm(n)
    yp = np.array([0.0, 1.0, 0.0])
    xp = np.cross(yp, zp)
    xp /= np.linalg.norm(xp)
    yp = np.cross(zp, xp)
    Tp[:3, 0], Tp[:3, 1], Tp[:3, 2] = xp, yp, zp
    o = T[:3, 3] + u * ((top0 - T[:3, 3]) @ n) / (u @ n)             # the pair centre line meets the top plane
    Tp[:3, 3] = o
    info = dict(pin_frame_T=np.round(T, 6).tolist(), underside_fit_residual_mm=N.r(res, 3), carrier_top_u_mm=N.r(u_top),
                carrier_height_mm=N.r(u_top - C["u_bot"]), tpu_under_carrier_mm=N.r(C["u_bot"] + r_),
                body_wall_u_mm={("L" if y > 0 else "R"): [N.r(a), N.r(b)] for y, (a, b) in walls.items()},
                body_wall_thickness_mm=N.r(walls[N.PIN_Y][1] - walls[N.PIN_Y][0]),
                tip_trunk_mm={("L" if p["y"] > 0 else "R"): np.round(p["tip"], 2).tolist() for p in pins},
                face_trunk_mm={("L" if p["y"] > 0 else "R"): np.round(p["face"], 2).tolist() for p in pins},
                tail_end_trunk_mm={("L" if p["y"] > 0 else "R"): np.round(p["tail_end"], 2).tolist() for p in pins},
                socket_mouth_below_carrier_mm=N.r(C["u_bot"] - (tip_u[N.PIN_Y] + P["exposed"])),
                socket_mouth_above_block_face_mm=N.r(tip_u[N.PIN_Y] + P["exposed"] + r_),
                press_ring_u_mm=N.r(tip_u[N.PIN_Y] + P["exposed"] + P["press_ring"]),
                pocket_open_area_mm2=N.r((C["flange_x"] + 2 * f) * (C["flange_y"] + 2 * f), 0))
    return dict(T=T, old=old, new=new, carrier=carrier, pocket=pocket, holes=holes, pins=pins, Tp=Tp, inst=inst, info=info, top0=top0, n=n)


def build():
    S = L.scene(fresh=True)
    bi = L.inst(S, N.TR, "body_middle_bottom")
    body = S.world_mesh(bi)
    out = {w: build_block(S, body, w) for w in ("seat", "bump")}
    body_new = N.man(body) - out["seat"]["holes"] - out["bump"]["holes"]
    return S, bi, body, body_new, out


def gauge():
    """the pin height gauge: a strip with two steps, 3.0 mm (seat) and 7.5 mm (bumper), and a 4 mm slot per pin"""
    g = N.man(L.box((0, 0, 0), (60, 14, 2.0)))
    g += N.man(L.box((0, 0, 0), (28, 14, 2.0 + N.PROUD["seat"])))
    g += N.man(L.box((32, 0, 0), (60, 14, 2.0 + N.PROUD["bump"])))
    for x0 in (4.0, 36.0):                       # each pad: two blind wells 20 mm apart do not fit a 14 mm strip, so one slot
        g -= N.man(L.box((x0, 5.0, 2.0), (x0 + 20.0, 9.0, 20.0)))
    return g


def main():
    S, bi, body, body_new, out = build()
    rec, parts = {}, {}
    placements = {}
    for w, stem, car in (("seat", "sit_seat", "pin_carrier_seat"), ("bump", "sit_bumper", "pin_carrier_bumper")):
        o = out[w]
        Tw = S.T0[o["inst"]["link"]] @ o["inst"]["T"]
        m = N.clean(L.xform(o["new"], np.linalg.inv(Tw)), stem)
        parts[stem] = m
        N.write_part(stem, m, rec, material="TPU 95A (BOM 28)")
        rec[stem]["volume_before_mm3"] = N.r(o["old"].volume, 1)
        placements[stem] = [dict(link=o["inst"]["link"], T_link_mm=np.round(o["inst"]["T"], 6).tolist(), note="unchanged (robot.urdf)")]
        mc = N.clean(L.xform(o["carrier"], np.linalg.inv(o["Tp"])), car)
        parts[car] = mc
        N.write_part(car, mc, rec, material="PLA (BOM 27 class), 100 % infill")
        placements[car] = [dict(link=N.TR, T_link_mm=np.round(np.linalg.inv(S.T0[N.TR]) @ o["Tp"], 6).tolist())]
        rec[car].update(o["info"])
    Tb = S.T0[N.TR] @ bi["T"]
    comps = sorted(body_new.decompose(), key=lambda c_: -c_.volume())
    mb = N.tm(L.xform(body_new, np.linalg.inv(Tb)))
    mb.merge_vertices()
    ok, _ = L.stl_roundtrip_ok(mb)
    b0 = S.mesh(bi)
    N.write_part("body_middle_bottom", mb, rec, step=False, material="PLA")
    rec["body_middle_bottom"].update(volume_before_mm3=N.r(b0.volume, 1), bodies=len(comps), bodies_before=int(b0.body_count),
                                     watertight_before=bool(b0.is_watertight),
                                     step_note="no STEP of the whole part: a faceted STEP of its 52,000 triangles is 59 MB (limit 5 MB); "
                                               "the change is in step/body_middle_bottom_feedthroughs.step (the four cut volumes, trunk frame)")
    placements["body_middle_bottom"] = [dict(link=N.TR, T_link_mm=np.round(bi["T"], 6).tolist(), note="unchanged (robot.urdf)")]
    cut = N.tm(out["seat"]["holes"] + out["bump"]["holes"])
    cut.merge_vertices()
    import step_export
    cut.export(os.path.join(N.STL_DIR, "body_middle_bottom_feedthroughs.stl"))
    s = step_export.mesh_to_step(cut, os.path.join(N.STEP_DIR, "body_middle_bottom_feedthroughs.step"), "body_middle_bottom_feedthroughs")
    rec["body_middle_bottom_feedthroughs"] = dict(stl="stl/body_middle_bottom_feedthroughs.stl", step="step/body_middle_bottom_feedthroughs.step",
                                                  what="the four cut volumes (3.4 mm holes with a 0.8 mm 45 deg mouth inside), trunk frame; not a part",
                                                  volume_mm3=N.r(cut.volume, 1), step_bytes=s["bytes"])
    g = N.clean(gauge(), "pin_gauge")
    N.write_part("pin_gauge", g, rec, material="PLA, a tool (not on the robot)")
    # the bought pin stand-in, one, in its own frame (tip at the origin, axis +z)
    P = N.PIN
    T0 = np.eye(4)
    ref = trimesh.util.concatenate([N.cyl_u(T0, 0, 0, P["exposed"], P["tube_d"], 16),
                                    N.cyl_u(T0, 0, P["exposed"], P["exposed"] + P["socket_len"], P["socket_d"], 16),
                                    N.cyl_u(T0, 0, P["exposed"] + P["socket_len"], P["exposed"] + P["socket_len"] + P["tail_len"], 1.2, 12)])
    ref = N.tm(L.union([N.man(x) for x in ref.split()]))
    N.write_part("spring_pin_ref", ref, rec, material="bought part stand-in (dimensions est, UNVERIFIED)")
    pins = {}
    for w in ("seat", "bump"):
        for p in out[w]["pins"]:
            pins["%s_%s" % (w, "L" if p["y"] > 0 else "R")] = dict(tip_free_trunk_mm=np.round(p["tip"], 3).tolist(),
                                                                   block_face_trunk_mm=np.round(p["face"], 3).tolist(),
                                                                   proud_mm=N.PROUD[w], pole="plus" if w == "seat" else "minus")
    a = out["seat"]["T"][:3, 2]
    sp = (np.array(pins["bump_L"]["block_face_trunk_mm"]) - np.array(pins["seat_L"]["block_face_trunk_mm"]))
    along = float(np.linalg.norm(sp - (sp @ a) * a))
    N.dump(dict(generated_by="duck_pins.py", label="CAD check only (geometry); calc only (forces, masses); pin dimensions marked est are UNVERIFIED",
                frame="trunk frame: robot.urdf base frame at the zero pose, mm", pin=N.PIN, proud_mm=N.PROUD,
                pin_axis_trunk=np.round(-a, 6).tolist(), sit_pitch_deg=N.r(N.SIT_PITCH, 3), pins=pins,
                pair_spacing_along_floor_mm=N.r(along), parts=rec, placements=placements), os.path.join(HERE, "duck_pins.json"))
    for k, v in rec.items():
        print("%-34s faces %6s  vol %10s  stl %8s  step %8s" % (k, v.get("faces"), v.get("volume_mm3"), v.get("bytes"), v.get("step_bytes")))
    print("pair spacing along the floor %.2f mm; seat info %s" % (along, out["seat"]["info"]))
    print("bumper info", out["bump"]["info"])


if __name__ == "__main__":
    main()
