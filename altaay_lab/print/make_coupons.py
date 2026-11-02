#!/usr/bin/env python3
"""Cut test coupons from the REAL upstream Open Duck Mini v2 print STLs (nothing is redrawn).

  python3 make_coupons.py OUT_DIR

OUT_DIR must be outside the repo (lab rule: no CAD exports in git). For each coupon the script
cuts the upstream STL with a box (manifold3d boolean), turns it to the same print orientation as
the full part, re-measures the feature it is meant to test, and writes:
  OUT_DIR/<coupon>.stl      ready to slice, resting on Z=0
  OUT_DIR/manifest.json     source STL + sha256, cut box, orientation, profile, rings, measured checks,
                            and the physical pass/fail test
The insert coupons C2a, C2b and C3 also get a light copy (C2aL, C2bL, C3L: same cut, the light profile of their part
with a solid ring round the bore, DECISIONS.md D22). The copies print next to them in session S1: that is the D22 gate.
Then slice them with:  python3 slice.py coupons --out SLICE_DIR --coupons OUT_DIR

Coordinates below are the upstream print STL frame (mm). Feature positions come from
altaay_lab/audit/sites.json (zero-pose frame) moved into each STL frame, and are re-measured
here from the STL itself. Needs: trimesh, numpy, shapely, manifold3d.
"""
import hashlib, json, os, sys

import numpy as np
import trimesh
from shapely.geometry import Polygon

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
PRINT_DIR = os.path.join(REPO, "print")
UP = {"+x": (1, 0, 0), "-x": (-1, 0, 0), "+y": (0, 1, 0), "-y": (0, -1, 0),
      "+z": (0, 0, 1), "-z": (0, 0, -1)}

COUPONS = [
    dict(id="C1", file="C1_trunk_bottom_bearing_seat.stl", source="trunk_bottom.stl", up="+z",
         box=[[-25, 14.0, -95], [40, 60, -70]], material="PLA", overrides="insert+fit",
         what="One 6804 bearing seat of trunk_bottom (32.19 mm, 5.8 mm deep) on its 26.19 mm lip, "
              "with the real ring wall round it. Same orientation and profile as trunk_bottom.",
         blockers="PRINT_CHECK flag 7",
         test=["Calipers: seat bore 32.10 to 32.25 mm (CAD 32.19) at 2 angles 90 degrees apart.",
               "A 6804ZZ (20x32x7) goes in by thumb pressure (no hammer, no heat) and sits flat on the lip.",
               "Push the bearing sideways at the top edge: no rocking you can feel or see.",
               "The bearing comes back out with finger pressure (it is a slip fit by design, 0.19 mm).",
               "FAIL if it needs force or does not seat: see PRINT_PLAN.md 'Hole size' before trunk_bottom and head."]),
    dict(id="C2a", file="C2a_foot_top_insert_boss_and_switch_slot.stl", source="foot_top.stl", up="-y",
         box=[[12.0, 78.0, -260], [50, 100.6, -200]], material="PLA", overrides="insert",
         what="foot_top insert boss with the 1.5 mm wall (M3 bore 4.0 x 5.8 plus its 2.0 pilot) and one "
              "Omron SS-10 slot (6.4 x 19.8). Top 21.45 mm of the part in its print orientation. Printed with 4 walls "
              "(insert), the D22 fallback for foot_top, next to its light copy C2aL.",
         blockers="B16, B11 (switch seat), test order TO12 and TO14",
         test=["Install one CNC Kitchen M3x5.7 insert with the Pinecil insert tip: it goes in straight and ends flush (straight edge, no lip over 0.1 mm).",
               "The 1.5 mm side wall shows no crack, split or bulge over 0.2 mm (straight edge along the outside).",
               "An M3x10 screw threads in fully by hand. Tighten with the short arm of a 2.5 mm hex key: the insert does not spin.",
               "Hang 5 kg from the screw for 10 s (or pull 5 kg on a luggage scale): the insert does not move.",
               "Omron SS-10 presses into the slot by thumb, stays in when the coupon is shaken upside down, and the lever still clicks freely."]),
    dict(id="C2b", file="C2b_foot_top_insert_boss.stl", source="foot_top.stl", up="-y",
         box=[[-60, 78.0, -260], [-36.2, 90.0, -200]], material="PLA", overrides="insert",
         what="The second foot_top insert boss (also 1.5 mm wall), for a second insert sample. Cut 10.85 mm "
              "deep: the bore (5.8 mm) plus 5 mm of its 2.0 mm pilot, which here opens at the bed face. Printed with "
              "4 walls (insert), next to its light copy C2bL.",
         blockers="B16",
         test=["Same insert checks as C2a on the second boss. Both must pass."]),
    dict(id="C3", file="C3_foot_bottom_pla_blind_insert_bore.stl", source="foot_bottom_pla.stl", up="-z",
         box=[[4.2, 70, -260], [22.2, 110, -240]], material="PLA", overrides="insert",
         what="The shallowest insert bore: foot_bottom_pla, blind, 4.0 mm x 5.8 mm cylinder plus a drill "
              "point cone, for a 5.7 mm insert. No pilot below it, so molten plastic has little room. Printed with "
              "4 walls (insert), the D22 fallback for foot_bottom_pla, next to its light copy C3L.",
         blockers="B15, PRINT_CHECK flag 5, test order TO12",
         test=["Install one M3x5.7 insert to flush. It reaches flush without pushing harder than on C2a.",
               "Depth gauge or calipers: insert top is flush to 0.1 mm proud at most.",
               "Look at the far side (bed face): no bulge or crack over the bore (floor is about 1.1 mm at the cone tip).",
               "An M3x8 screw threads in by hand over the full insert length (5.7 mm) without hitting plastic.",
               "Hang 5 kg from the screw for 10 s: the insert does not move."]),
    dict(id="C4", file="C4_head_yaw_to_roll_servo_pocket.stl", source="head_yaw_to_roll.stl", up="+z",
         box=[[45.5, -16, 100], [62, 16, 160]], material="PLA", overrides="neck+fit",
         what="The one servo pocket that is undersize across the servo in CAD: head_yaw_to_roll, floor "
              "ledge to top arm 34.90 mm for a 35.00 mm STS3215 body (0.10 mm interference). Full "
              "height arm, same orientation, supports and profile (neck+fit) as the full part, so it also "
              "tests the stronger neck setting (UPSTREAM_ISSUES G5). It also holds 4 of the 24 neck chain "
              "5.5 mm M3 head recesses (drive horn screws) and 4 of the 4.0 mm M2 pan head recesses (servo "
              "case screws), so it carries the recess fit test (DECISIONS.md D20).",
         blockers="PRINT_CHECK flag 6, D20 (recess fit), B21 and B2 (M2 heads)",
         test=["Calipers: gap between the floor ledge and the underside of the top arm, at the ledge (CAD 34.90 mm).",
               "Slide a real STS3215 (test order TO1) case end-first between ledge and arm: it goes in with firm thumb pressure, no tools, and does not rattle. PASS.",
               "If it will not go in by hand: up to 0.2 mm short, sand the underside of the arm lightly (expected, flag 6) and note it.",
               "FAIL if more than 0.2 mm short, or the support scar on the arm underside is rougher than light sanding fixes: see PRINT_PLAN.md before the head parts.",
               "Recess fit (D20): put a DIN 912 M3x5 head (BOM 17e) into each of the 4 recesses of 5.5 mm. Expected as printed: it does not drop in (heads are 5.50 to 5.68 mm). Open one recess to 6.0 mm with the 6.0 mm bit (BOM T11) turned by hand, and stop as soon as the bit starts to cut the recess floor: the head must then drop in and sit flat. FAIL: tell Ahmed before the neck parts are drilled.",
               "Recess fit: a servo-bag M2 screw head (TO1) and a kit M2x5 head (BOM 17h, 3.7 mm per its listing) go into each of the 4 recesses of 4.0 mm and sit flat. If one does not, open that recess to 4.5 mm and note it (fasteners/FASTENERS.md finding 12)."]),
    dict(id="T1", file="T1_left_eye_whole.stl", source="left_eye.stl", up="+x", box=None,
         material="PLA", overrides="wall3",
         what="Whole left_eye (B14: its 4 screw pilots are 2.2 mm, the right eye has 2.05 mm). The pilots are "
              "blind, 3.0 mm deep behind a 1.3 mm front skin (D21). Printed in the eye profile (3 walls, wall3: D22 "
              "keeps the eyes heavy); it is the robot's left eye.",
         blockers="B14, D21, BOM E4 (eye glass disc), test order TO11",
         test=["Depth rod of the calipers in each pilot: about 3.0 mm, blind (CAD 3.0 mm, 1.3 mm front skin on this eye).",
               "In the robot the screw passes a 0.5 mm washer, the bulb (2.0 mm) and the head wall (3.0 mm) before the eye (D21). So clamp 5.5 mm under each M2.5x8 head (11 of the 0.5 mm washers from BOM 17l, or the bulb plus 3.5 mm of scrap with a 2.7 mm hole): it then engages 2.5 mm, as in the robot. Never drive a bare M2.5x8 to the pilot floor: it would push through the skin.",
               "Drive the M2.5x8 DIN 912 into each of the 4 pilots with a 2.0 mm hex key: it cuts its own thread and needs clear torque to turn.",
               "Snug each screw firmly with the short arm of the key: no stripping, the screw does not spin free.",
               "Pull the eye by hand with 4 screws in: nothing moves.",
               "The eye glass disc (29.6 x 1.85 mm seat) drops into its seat and stays in when tipped.",
               "FAIL if any pilot strips: B14 stays open (use an M2.5 thread-forming screw or ask Ahmed about a 2.05 mm pilot)."]),
    dict(id="T2", file="T2_foot_bottom_tpu_whole.stl", source="foot_bottom_tpu.stl", up="-z", box=None,
         material="TPU", overrides="",
         what="Whole foot_bottom_tpu in Overture TPU 95A at 40% infill (B26). If it passes it is the left leg sole.",
         blockers="B26, test order TO13",
         test=["No missing layers, no blobs over 0.5 mm, lies flat (no corner lifted over 0.5 mm on a flat table).",
               "Calipers: length 101.9 and width 40.7 mm within 0.3 mm.",
               "An M3 screw passes both 3.4 mm holes and its head sinks fully into the 6.5 mm counterbores.",
               "Screw it to foot_bottom_pla (or C3 for one hole): it pulls flat, no gap over 0.3 mm at the edges.",
               "Grip (record only, upstream gives no number): on the lab floor, with 1 kg on it, tilt until it slides and note the angle next to a PLA part on the same surface."]),
]


# D22 gate (DECISIONS.md, print/MASS_STUDY.md): a light copy of each insert coupon. Same cut and orientation, printed in
# the light profile of its part: 2 walls, 15 %, and a 2.0 mm solid ring round the insert bore (slice.py finds the bore in
# the coupon and adds the ring as a modifier, as it does in the part). It prints next to the 4-wall coupon in session S1.
LIGHT_OF = ("C2a", "C2b", "C3")


def light_copy(c):
    d = dict(c)
    d.update(id=c["id"] + "L", file=c["file"].replace(c["id"] + "_", c["id"] + "L_", 1), overrides="", rings="insert",
             light_of=c["id"], blockers="D22 gate; " + c["blockers"],
             what="Light copy of %s (D22 gate): the same cut, printed in the light profile of %s (2 walls, 15 %%, a 2.0 mm "
                  "solid ring round the insert bore, config/mod_ring.ini), next to %s with its 4 walls." % (c["id"], c["source"][:-4], c["id"]),
             test=["Every %s test below, on this coupon, side by side with %s:" % (c["id"], c["id"])] + c["test"] +
                  ["D22 gate: if %sL fails a test that %s passes, the 10 insert ring parts (body_middle_bottom, body_middle_top, "
                   "foot_top x2, foot_bottom_pla x2, leg_spacer x4) print with 4 walls (insert) and no rings (parts.csv heavy "
                   "column; PRINT_PLAN.md step 1)." % (c["id"], c["id"])])
    return d


COUPONS = [x for c in COUPONS for x in ([c, light_copy(c)] if c["id"] in LIGHT_OF else [c])]


def rot_up(up):
    u = np.array(UP[up], float)
    z = np.array([0, 0, 1.0])
    if np.allclose(u, z):
        return np.eye(4)
    if np.allclose(u, -z):
        return trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0])
    return trimesh.transformations.rotation_matrix(np.arccos(np.dot(u, z)), np.cross(u, z))


def section_circles(m, origin, normal):
    """Circular holes cut by a plane: list of (centre xyz, diameter)."""
    s = m.section(plane_origin=origin, plane_normal=normal)
    out = []
    if s is None:
        return out
    p2, T = s.to_2D() if hasattr(s, "to_2D") else s.to_planar()
    for poly in p2.polygons_full:
        for ring in poly.interiors:
            c = np.array(ring.coords)[:-1]
            pg = Polygon(c)
            circ = 4 * np.pi * pg.area / pg.length ** 2
            if circ > 0.95 and len(c) > 8:
                cen = np.array(pg.centroid.coords[0])
                d = 2 * np.linalg.norm(c - cen, axis=1).mean()
                out.append(((T @ np.r_[cen, 0, 1])[:3], float(d)))
    return out


def section_rects(m, origin, normal):
    """Rectangular holes cut by a plane: list of (short side, long side)."""
    s = m.section(plane_origin=origin, plane_normal=normal)
    out = []
    if s is None:
        return out
    p2, T = s.to_2D() if hasattr(s, "to_2D") else s.to_planar()
    for poly in p2.polygons_full:
        for ring in poly.interiors:
            pg = Polygon(ring.coords)
            rr = pg.minimum_rotated_rectangle
            if pg.area / rr.area > 0.97:
                xs, ys = rr.exterior.coords.xy
                e = sorted([np.hypot(xs[1] - xs[0], ys[1] - ys[0]), np.hypot(xs[2] - xs[1], ys[2] - ys[1])])
                out.append((round(e[0], 2), round(e[1], 2)))
    return out


def hits(m, o, d):
    loc, _, _ = m.ray.intersects_location([o], [d], multiple_hits=True)
    return sorted(float(np.dot(p - o, d)) for p in loc) if len(loc) else []


def min_radial_wall(m, p0, axis, depth, r_bore=2.0):
    """Thinnest plastic between a bore and the next surface, rays out from the bore axis."""
    a = np.array(axis, float)
    u = np.cross(a, [1, 0, 0]) if abs(a[0]) < 0.9 else np.cross(a, [0, 1, 0])
    u /= np.linalg.norm(u)
    v = np.cross(a, u)
    best = 1e9
    for t in np.linspace(0.3, depth - 0.3, 10):
        c = np.array(p0) + a * t
        for ang in np.linspace(0, 2 * np.pi, 180, endpoint=False):
            d = np.cos(ang) * u + np.sin(ang) * v
            h = [x for x in hits(m, c, d) if x > r_bore - 0.5]
            if len(h) >= 2:
                best = min(best, h[1] - h[0])
    return round(best, 2)


def check(cid, m):
    """Re-measure the feature each coupon is for, in the upstream STL frame."""
    r = {}
    if cid == "C1":
        seat = [d for c, d in section_circles(m, [0, 35, -82.5], [0, 0, 1]) if 31 < d < 33]
        lip = [d for c, d in section_circles(m, [0, 35, -87.0], [0, 0, 1]) if 25 < d < 27]
        zs = [z for z in np.arange(-88.7, -78.0, 0.1)
              if any(31 < d < 33 for c, d in section_circles(m, [0, 35, z], [0, 0, 1]))]
        r = dict(seat_d=round(seat[0], 2) if seat else None, lip_d=round(lip[0], 2) if lip else None,
                 seat_z=[round(min(zs), 1), round(max(zs), 1)] if zs else None,
                 seat_depth=round(max(zs) - min(zs) + 0.1, 1) if zs else None)
        r["ok"] = bool(seat and abs(seat[0] - 32.19) < 0.05 and lip and abs(lip[0] - 26.19) < 0.05
                       and zs and abs(r["seat_depth"] - 5.8) < 0.25)
    elif cid in ("C2a", "C2b"):
        x = 29.7 if cid == "C2a" else -43.2
        bore = [d for c, d in section_circles(m, [x, 82.0, -241.63], [0, 1, 0]) if 3.8 < d < 4.2]
        pilot = [d for c, d in section_circles(m, [x, 88.0, -241.63], [0, 1, 0]) if 1.8 < d < 2.2]
        wall = min_radial_wall(m, [x, 79.15, -241.63], [0, 1, 0], 5.8)
        r = dict(bore_d=round(bore[0], 2) if bore else None, pilot_d=round(pilot[0], 2) if pilot else None,
                 min_wall=wall)
        r["ok"] = bool(bore and pilot and 1.45 <= wall <= 1.65)
        if cid == "C2a":
            sl = [e for e in section_rects(m, [18.24, 90.0, -241.3], [0, 0, 1]) if e[0] > 5]
            r["switch_slot"] = sl[0] if sl else None
            r["ok"] = r["ok"] and bool(sl and abs(sl[0][0] - 6.4) < 0.05 and abs(sl[0][1] - 19.8) < 0.1)
    elif cid == "C3":
        bore = [d for c, d in section_circles(m, [13.2, 90.0, -251.0], [0, 0, 1]) if 3.8 < d < 4.2]
        h = hits(m, np.array([13.2, 90.0, -253.62 - 1.0]), np.array([0, 0, 1.0]))
        cyl = [z for z in np.arange(-253.5, -245.7, 0.05)
               if any(3.9 < d < 4.1 for c, d in section_circles(m, [13.2, 90.0, z], [0, 0, 1]))]
        # the ray starts 1 mm outside the open end, runs up the bore axis: first hit is the cone tip
        r = dict(bore_d=round(bore[0], 2) if bore else None,
                 cylinder_depth=round(max(cyl) - (-253.62), 2) if cyl else None,
                 depth_to_cone_tip=round(h[0] - 1.0, 2) if len(h) > 0 else None,
                 floor_at_tip=round(h[1] - h[0], 2) if len(h) > 1 else None)
        r["ok"] = bool(bore and r["cylinder_depth"] and abs(r["cylinder_depth"] - 5.8) < 0.15
                       and r["floor_at_tip"] and r["floor_at_tip"] > 0.5)
    elif cid == "C4":
        # (49.4, 5.0) is on the floor ledge where the across-servo fit is -0.10 mm
        up = hits(m, np.array([49.4, 5.0, 128.4]), np.array([0, 0, 1.0]))
        dn = hits(m, np.array([49.4, 5.0, 128.4]), np.array([0, 0, -1.0]))
        r = dict(ceiling_z=round(128.4 + up[0], 2) if up else None, ledge_z=round(128.4 - dn[0], 2) if dn else None)
        r["gap"] = round(up[0] + dn[0], 2) if up and dn else None
        # D20 recess fit: the 4 drive horn screw recesses (5.5 mm, axis x, seat at x 59.2) and the 4 servo case screw
        # recesses (4.0 mm, axis z: 2 open on the bed face, seat at z 109.96; 2 open on the top face, seat at z 147.16)
        rec55 = [d for c, d in section_circles(m, [58.2, 0, 129.06], [1, 0, 0]) if 5.3 < d < 5.7]
        rec40 = ([d for c, d in section_circles(m, [52.75, 0, 108.96], [0, 0, 1]) if 3.8 < d < 4.2]
                 + [d for c, d in section_circles(m, [49.0, 0, 148.16], [0, 0, 1]) if 3.8 < d < 4.2])
        r["recess_5_5"] = sorted(round(d, 2) for d in rec55)
        r["recess_4_0"] = sorted(round(d, 2) for d in rec40)
        r["ok"] = bool(r["gap"] and abs(r["gap"] - 34.90) < 0.05 and len(rec55) == 4 and len(rec40) == 4)
    elif cid == "T1":
        cs = [(c, d) for c, d in section_circles(m, [121.5, 40, 139.4], [1, 0, 0]) if 2.0 < d < 2.4]
        p = [round(d, 2) for c, d in cs]
        # D21: the pilots are blind. Ray from 1 mm outside the bed face up each pilot axis: the first hit is the
        # pilot floor, the second the front face.
        x0 = m.bounds[0][0] - 1.0
        depth, skin = [], []
        for c, d in cs:
            h = hits(m, np.array([x0, c[1], c[2]]), np.array([1.0, 0, 0]))
            if len(h) >= 2:
                depth.append(round(h[0] - 1.0, 2))
                skin.append(round(h[1] - h[0], 2))
        r = dict(pilots=p, pilot_depth=depth, front_skin=skin,
                 ok=len(p) == 4 and all(abs(d - 2.2) < 0.05 for d in p)
                 and len(depth) == 4 and all(abs(x - 3.0) < 0.1 for x in depth))
    elif cid == "T2":
        e = sorted(np.round(m.extents, 1).tolist())
        r = dict(extents=e, ok=abs(e[2] - 101.9) < 0.2 and abs(e[1] - 40.7) < 0.2 and abs(e[0] - 8.0) < 0.1)
    return r


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    out = os.path.abspath(sys.argv[1])
    if out == REPO or out.startswith(REPO + os.sep):
        sys.exit("OUT_DIR must be outside the repo (no CAD exports in git)")
    os.makedirs(out, exist_ok=True)
    man = {"upstream_print_dir": PRINT_DIR, "coupons": []}
    all_ok = True
    for c in COUPONS:
        src = os.path.join(PRINT_DIR, c["source"])
        part = trimesh.load(src)
        if c["box"]:
            lo, hi = np.array(c["box"][0], float), np.array(c["box"][1], float)
            box = trimesh.creation.box(extents=hi - lo)
            box.apply_translation((lo + hi) / 2)
            cut = trimesh.boolean.intersection([part, box], engine="manifold")
        else:
            cut = part.copy()
        meas = check(c.get("light_of") or c["id"], cut)
        all_ok &= meas["ok"]
        m = cut.copy()
        m.apply_transform(rot_up(c["up"]))
        m.apply_translation(-m.bounds[0])
        m.export(os.path.join(out, c["file"]))
        rec = {k: c[k] for k in ("id", "file", "source", "up", "box", "material", "overrides", "what", "blockers", "test")}
        rec.update(rings=c.get("rings", ""), light_of=c.get("light_of", ""))
        rec.update(source_sha256=hashlib.sha256(open(src, "rb").read()).hexdigest(),
                   watertight=bool(m.is_watertight), bodies=len(m.split(only_watertight=False)),
                   volume_cm3=round(m.volume / 1000, 2), footprint_mm=[round(float(x), 1) for x in m.extents[:2]],
                   height_mm=round(float(m.extents[2]), 1), measured=meas)
        man["coupons"].append(rec)
        print("%-4s %-46s %5.2f cm3  %s x %s x %s mm  bodies %d  check %s %s" % (
            c["id"], c["file"], rec["volume_cm3"], rec["footprint_mm"][0], rec["footprint_mm"][1],
            rec["height_mm"], rec["bodies"], "OK" if meas["ok"] else "FAILED",
            {k: v for k, v in meas.items() if k != "ok"}))
    json.dump(man, open(os.path.join(out, "manifest.json"), "w"), indent=1)
    if not all_ok:
        sys.exit("a coupon check failed: the cut does not hold the feature it should")


if __name__ == "__main__":
    main()
