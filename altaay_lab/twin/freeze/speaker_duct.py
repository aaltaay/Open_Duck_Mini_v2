#!/usr/bin/env python3
"""speaker_duct.py: a printed duct from the speaker_interface plate to the head wall round the grille (V1 freeze, the
expression study's speaker fix). CAD check only for the part, calc only for the acoustics.

Run: python3 altaay_lab/twin/freeze/speaker_duct.py [--write]
--write writes print/speaker_interface.stl and speaker_duct.json.

Problem (expression study 4.3, CAD check only): the speaker fires through the 18.4 mm window of the speaker_interface
plate toward the right side wall, then crosses a 12.7 mm gap to the grille; that gap is open on every side to the head
interior, where the back wave of the cone also goes, so front and back waves partly cancel (about -8 dB, calc only).
Fix: a round duct, one piece with the interface plate (it prints straight up: the part's print 'up' in parts.csv is the
speaker axis), from the plate's front face to 1.0 mm short of the inner wall face, with a ring of the BOM 29 foam on its
end (one liner left on, so it seals and does not bond: the stand still comes out). The front wave then leaves only by
the grille; the head interior is the back box.
Sizes from the mesh (fasteners.json F352 to F355 give the axis and the 32 x 32 mm screw square):
  - grille: 127 holes of 2.0 mm on rings r 0 to 18 mm; head_freeze.py closes the r = 18 ring (36 holes), 91 stay,
    the outermost kept edge at r 16.1 mm;
  - duct bore DUCT_IN 16.5 mm (0.4 mm past the kept holes), outside DUCT_OUT 18.4 mm (the plate square is +/-18.5 mm):
    a 1.9 mm wall (4 lines of a 0.45 mm nozzle);
  - the two fitted interface screws (F353, F354; M2.5 DIN 912, head 4.5 mm) sit at r 22.6 mm: their heads start at
    r 20.4 mm, so the duct clears them by 2.0 mm and a hex key reaches them along the screw axis.
Checks: watertight; the duct inside the free air between the plate and the wall (no other part within 1.0 mm); the
foam gap at the wall; distance to the mic boards (D47) and to the ear servos and their sweep (D47, PR 25 ear mount);
tool access to F353 and F354; front chamber volume and the grille Helmholtz corner (calc only).
"""
import argparse
import json
import os

import numpy as np
import trimesh

from flib import (LAB, PRINT, HERE, scene, head_inst, inst_world, inst_by_key, to_man, from_man, cyl, speaker_frame,
                  hits_along, surface_cloud, base_mesh, placements, placement_box, r, dump)

DUCT_IN, DUCT_OUT = 16.5, 18.4
FOAM_GAP = 1.0              # BOM 29 VHB 4950 is 1.1 mm: about 0.1 mm squeeze, liner left on the wall side
FUSE = 0.3                  # the duct starts this far inside the plate so the union fuses
CLEAR_RULE = 1.0            # to every part that is not screwed to the interface
CLEAR_FIXED = 0.5           # to speaker_stand, the part the interface is screwed to (no relative motion; 2 x 0.2 mm print tolerance + 0.1)
HOLE_D, HOLES_KEPT, WALL = 2.0, 91, 3.0
C_AIR = 343.0e3             # mm/s
SRC = os.path.join(PRINT, "speaker_interface.stl")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    S = scene()
    c, ax, u, v, F = speaker_frame()
    si = inst_by_key(S, "speaker_interface")[0]
    Tsi = inst_world(S, si)
    base = base_mesh("print/speaker_interface.stl")
    SIw = base.copy()
    SIw.apply_transform(Tsi)
    H = S.world_mesh(head_inst(S))
    # plate front face and the wall along the axis, between the window and the plate edge
    tp = [t - 3 for t in hits_along(SIw, c + u * 12 - ax * 3, ax)]
    plate_front = max(tp)
    tw = [t - 3 for t in hits_along(H, c + u * 1.5 - ax * 3, ax) if t > 3]
    wall_in, wall_out = tw[0], tw[1]
    # the wall must be flat across the duct end (ray at every 15 deg on both radii)
    ends = []
    for ang in np.radians(np.arange(0, 360, 15)):
        for rad in (DUCT_IN, DUCT_OUT):
            o = c + (np.cos(ang) * u + np.sin(ang) * v) * rad
            t = [x - 3 for x in hits_along(H, o - ax * 3, ax) if x > 3]
            ends.append(t[0] if t else np.inf)
    wall_flat = float(np.ptp(ends))
    t0, t1 = plate_front - FUSE, wall_in - FOAM_GAP
    duct = cyl(c + ax * t0, c + ax * t1, DUCT_OUT, 96)
    bore = cyl(c + ax * (t0 - 1), c + ax * (t1 + 1), DUCT_IN, 96)
    D = to_man(duct) - to_man(bore)
    Ti = np.linalg.inv(Tsi)
    dl = from_man(D)
    dl.apply_transform(Ti)
    out = from_man(to_man(base) + to_man(dl))
    ow = out.copy()
    ow.apply_transform(Tsi)
    # clearance of the duct (the new material only) to every other head part and to the placed boxes
    duct_w = from_man(D)
    pts = surface_cloud(duct_w, 30000)
    keep = (pts - c) @ ax > plate_front + 0.2          # off the fused plate face
    pts = pts[keep]
    from scipy.spatial import cKDTree
    gaps = {}
    for i in S.inst:
        if i["link"] != "head_assembly" or i["key"] in ("speaker_interface",):
            continue
        m = S.world_mesh(i)
        if not len(m.faces):
            continue
        d = cKDTree(surface_cloud(m, 40000)).query(pts)[0]
        name = "%s[%d]" % (i["key"], i["idx"])
        if i["key"] == "head":       # the head wall itself: the foam gap at the duct end is by design
            far = (pts - c) @ ax < t1 - 0.3
            gaps[name + " (away from the duct end)"] = r(d[far].min(), 2)
            gaps[name + " (duct end, foam gap)"] = r(d[~far].min(), 2)
        else:
            gaps[name] = r(d.min(), 2)
    pl = placements()
    for k, p in pl.items():
        bx = placement_box(p)
        gaps["box " + k] = r(cKDTree(surface_cloud(bx, 8000)).query(pts)[0].min(), 2)
    worst = sorted(((k, g) for k, g in gaps.items() if "foam gap" not in k), key=lambda kv: kv[1])[:6]
    # mic boards and the ears (their sweep is in ear_mount.json: the holder and rod clear the shell over -90..90 deg)
    mic = {k: gaps.get("box " + k) for k in ("mic_l", "mic_r")}
    sg = {k: g for k, g in gaps.items() if k.startswith(("sg90", "right_antenna_holder", "left_antenna_holder", "antenna"))}
    # tool access to the fitted interface screws: a 2.0 mm hex key turned in a 4.5 mm circle along the screw axis
    tool = {}
    for fid in ("F353", "F354"):
        f = F[fid]
        p = np.array(f["seat_world"], float)
        ra = np.hypot((p - c) @ u, (p - c) @ v)
        tool[fid] = dict(screw_r_mm=r(ra), head_edge_r_mm=r(ra - 2.25), duct_clear_mm=r(ra - 2.25 - DUCT_OUT),
                         key_circle_clear_mm=r(ra - 2.25 - DUCT_OUT))
    # acoustics (calc only): front chamber and the grille as a Helmholtz neck
    Vf = np.pi * DUCT_IN ** 2 * (wall_in - plate_front)                 # mm3, the bore from the plate to the wall
    A = HOLES_KEPT * np.pi * (HOLE_D / 2) ** 2
    Leff = WALL + 1.7 * (HOLE_D / 2)                                     # each hole: wall plus 2 x 0.85 r end corrections
    fh = C_AIR / (2 * np.pi) * np.sqrt(A / (Vf * Leff))
    leak_before = dict(open_side_area_mm2=r(2 * np.pi * 18.5 * (wall_in - plate_front), 0),
                       note="the 12.7 mm gap is open all round (2 pi x 18.5 x 12.7 mm of side opening)")
    J = dict(script="altaay_lab/twin/freeze/speaker_duct.py", label="CAD check only (part); calc only (acoustics)",
             axis_world=np.round(ax, 4).tolist(), centre_world=np.round(c, 3).tolist(),
             plate_front_t_mm=r(plate_front), wall_t_mm=[r(wall_in), r(wall_out)], wall_flat_ptp_mm=r(wall_flat, 3),
             duct=dict(bore_mm=2 * DUCT_IN, outside_mm=2 * DUCT_OUT, wall_mm=r(DUCT_OUT - DUCT_IN), length_mm=r(t1 - t0),
                       foam_gap_mm=FOAM_GAP, volume_mm3=r(dl.volume, 1), mass_g_at_1_24=r(dl.volume * 1.24e-3, 2)),
             gaps_mm=gaps, worst_gaps_mm=dict(worst), mic_box_gaps_mm=mic, ear_parts_gaps_mm=sg, screw_access=tool,
             acoustics=dict(front_chamber_mm3=r(Vf, 0), grille_area_mm2=r(A, 1), neck_eff_mm=r(Leff, 2),
                            helmholtz_hz=r(fh, 0), before=leak_before,
                            note="calc only: with the duct the front wave leaves only by the 91 grille holes; the bench A/B "
                                 "sweep of the expression study (phone at 0.5 m) settles the gain"),
             file=dict(watertight=bool(out.is_watertight), volume_mm3=r(out.volume, 1), added_mm3=r(out.volume - base.volume, 1)))
    rule_ok = all(g >= (CLEAR_FIXED if k.startswith("speaker_stand") else CLEAR_RULE) for k, g in gaps.items() if "foam gap" not in k)
    J["clearance_rules_mm"] = dict(other_parts=CLEAR_RULE, speaker_stand=CLEAR_FIXED)
    ok = (out.is_watertight and rule_ok and wall_flat < 0.2
          and all(x["duct_clear_mm"] >= 1.0 for x in tool.values()) and min(v_ for v_ in mic.values() if v_ is not None) >= 10)
    J["pass"] = bool(ok)
    print(json.dumps({k: J[k] for k in ("plate_front_t_mm", "wall_t_mm", "wall_flat_ptp_mm", "duct", "worst_gaps_mm",
                                        "mic_box_gaps_mm", "ear_parts_gaps_mm", "screw_access", "acoustics", "file", "pass")}, indent=1))
    if a.write:
        out.export(SRC)
        dump(J, os.path.join(HERE, "speaker_duct.json"))
        print("wrote", SRC)


if __name__ == "__main__":
    main()
