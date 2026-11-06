#!/usr/bin/env python3
"""head_freeze.py: the head for the V1 freeze (2026-11-06 ET). CAD check only.

Run: python3 altaay_lab/twin/freeze/head_freeze.py [--write]
--write writes print/head.stl (the file the viewer, cables3d, the fasteners and the slicer read) and head_freeze.json.

What it does, in order:
1. Mic seats into print/head.stl. Until now the D47 seats (2 bosses, a port tube and a 1.2 mm sound port per side)
   were only in twin/companion/stl/head.stl, which twin/companion/mic_seat.py builds from print/head.stl. The two meshes
   are compared with exact booleans (manifold3d): every bit of added or removed material must sit inside the two mic
   seat zones (mic_seats.json board centre +/- 14 mm), and nothing may change inside the two ear servo zones (the SG90
   poses of audit/assembly.json, +/- 30 mm): the ear mount checked by twin/companion/ear_mount.py stays exactly as it is.
2. The speaker duct (speaker_duct.py, D51 to D58 freeze set) leaves the outer ring of the grille outside the duct, so
   those holes are closed: 36 holes of 2.0 mm on the r = 18 mm ring round the speaker axis (the grille has rings at
   r 0, 3, 6, 9, 12, 15 and 18 mm; 127 holes). A plug is a 2.1 mm cylinder through the 3.0 mm wall, 0.03 mm short of
   each face, so it is flush within the 0.05 mm of the D42 cap rule. The 91 holes inside the duct stay (286 mm2).
Frames: print/ frame for the file (unchanged orientation and supports), URDF world for the checks.
"""
import argparse
import json
import os
import shutil

import numpy as np
import trimesh

from flib import (LAB, PRINT, HERE, scene, head_inst, inst_world, to_man, from_man, cyl, speaker_frame, hits_along, r, dump, base_mesh, BASE_REV)

SEATED = os.path.join(LAB, "twin", "companion", "stl", "head.stl")
OUT = os.path.join(PRINT, "head.stl")
PLUG_RING_R = 18.0          # the ring of grille holes left outside the duct (speaker_duct.py DUCT_IN 16.5 mm)
HOLE_D, PLUG_D = 2.0, 2.1
FACE_GAP = 0.03             # each plug end stops this far inside the wall face: flush within 0.05 mm (D42)
SEAT_ZONE, EAR_PAD = 14.0, 3.0   # seat zone: board centre +/- 14 mm; ear envelope: the SG90 bounds + 3 mm (plate, pocket, pilots)
NOISE_MM3 = 0.01            # boolean noise floor: the companion STL was written with float32 vertices (a 0.2 mm cube)


def base_head():
    """print/head.stl as it was before the freeze: the mesh mic_seat.py started from"""
    return base_mesh("print/head.stl")


def grille_holes(H, c, ax, u, v):
    """hole centres of the speaker grille in the wall middle plane (world), with their ring radius"""
    t_in = hits_along(H, c + u * 1.5 - ax * 3, ax)      # between the centre hole and the r = 3 ring
    t_in = [t - 3 for t in t_in if t > 3]
    wall0, wall1 = t_in[0], t_in[1]
    sec = H.section(plane_origin=c + ax * (wall0 + wall1) / 2, plane_normal=ax)
    out = []
    for e in sec.discrete:
        q = np.asarray(e) - c
        d = max(np.ptp(q @ u), np.ptp(q @ v))
        if abs(d - HOLE_D) < 0.25 and np.hypot((q @ u).mean(), (q @ v).mean()) < 25.0:
            a, b = (q @ u).mean(), (q @ v).mean()
            out.append(dict(u=a, v=b, r=float(np.hypot(a, b)), d=float(max(np.ptp(q @ u), np.ptp(q @ v)))))
    return out, wall0, wall1


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    S = scene()
    hi = head_inst(S)
    Th = inst_world(S, hi)
    base = base_head()
    seated = trimesh.load(SEATED, force="mesh")
    J = dict(script="altaay_lab/twin/freeze/head_freeze.py", label="CAD check only", frame="checks in the URDF world, zero pose; file in the print/ frame")
    # 1. mic seats: where do the two meshes differ? Exact volumes of the differences inside the zones (manifold3d)
    Mb, Ms = to_man(base), to_man(seated)
    Ti = np.linalg.inv(Th)
    seats = json.load(open(os.path.join(LAB, "twin", "companion", "mic_seats.json")))["seats"]

    def local_box(center, half):
        b = trimesh.creation.box(extents=[2 * half] * 3)
        b.apply_translation(center)
        b.apply_transform(Ti)
        return to_man(b)
    zone = None
    for s_ in ("left", "right"):
        z = local_box(np.array(seats[s_]["board_centre_world"]), SEAT_ZONE)
        zone = z if zone is None else zone + z
    ears = []
    for i in S.inst:
        if i.get("urdf") == "sg90.stl":
            m = S.world_mesh(i)
            lo, hi_ = m.bounds[0] - EAR_PAD, m.bounds[1] + EAR_PAD
            b = trimesh.creation.box(extents=hi_ - lo)
            b.apply_translation((lo + hi_) / 2)
            b.apply_transform(Ti)
            ears.append(to_man(b))
    res = {}
    for name, D in (("added", Ms - Mb), ("removed", Mb - Ms)):
        tot = D.volume()
        inz = (D ^ zone).volume()
        ear = sum((D ^ e).volume() for e in ears)
        res[name] = dict(volume_mm3=r(tot, 3), in_seat_zones_mm3=r(inz, 3), outside_seat_zones_mm3=r(tot - inz, 4),
                         in_ear_envelopes_mm3=r(ear, 4))
    ok = all(v["outside_seat_zones_mm3"] <= NOISE_MM3 and v["in_ear_envelopes_mm3"] <= NOISE_MM3 for v in res.values())
    J["mic_seats"] = dict(source="twin/companion/stl/head.stl (twin/companion/mic_seat.py on print/head.stl of %s)" % BASE_REV,
                          seat_zone_half_mm=SEAT_ZONE, noise_floor_mm3=NOISE_MM3, ear_envelope_pad_mm=EAR_PAD, ear_envelopes=len(ears), **res, ok=ok)
    print("mic seats:", json.dumps(res), "ok", ok)
    # 2. grille plugs
    Hw = seated.copy()
    Hw.apply_transform(Th)
    c, ax, u, v, _ = speaker_frame()
    holes, w0, w1 = grille_holes(Hw, c, ax, u, v)
    plug = [h for h in holes if abs(h["r"] - PLUG_RING_R) < 0.5]
    keep = [h for h in holes if abs(h["r"] - PLUG_RING_R) >= 0.5]
    M = Ms
    for h in plug:
        p = c + u * h["u"] + v * h["v"]
        cy = cyl(p + ax * (w0 + FACE_GAP), p + ax * (w1 - FACE_GAP), PLUG_D / 2, 32)
        cy.apply_transform(Ti)
        M = M + to_man(cy)
    out = from_man(M)
    ow = out.copy()
    ow.apply_transform(Th)
    # flush and closed: a ray along the axis through each plug centre hits the plug faces within 0.05 mm of the wall faces
    flush, open_after = [], 0
    for h in plug:
        p = c + u * h["u"] + v * h["v"]
        t = [x - 3 for x in hits_along(ow, p - ax * 3, ax) if x > 3]
        if len(t) < 2:
            open_after += 1
            continue
        flush.append(max(abs(t[0] - w0), abs(t[1] - w1)))
    kept_open = 0
    for h in keep:
        p = c + u * h["u"] + v * h["v"]
        t = [x - 3 for x in hits_along(ow, p - ax * 3, ax) if 3 < x < 3 + w1 + 1]
        kept_open += not t
    J["grille"] = dict(holes=len(holes), hole_d_mm=r(np.median([h["d"] for h in holes]), 2),
                       rings_mm=sorted({round(h["r"]) for h in holes}), wall_mm=[r(w0), r(w1)],
                       plugged=len(plug), plugged_ring_r_mm=PLUG_RING_R, kept=len(keep),
                       kept_open_after=kept_open, plugged_still_open=open_after,
                       plug_flush_worst_mm=r(max(flush) if flush else None, 3), flush_rule_mm=0.05,
                       open_area_before_mm2=r(len(holes) * np.pi * (HOLE_D / 2) ** 2, 1),
                       open_area_after_mm2=r(len(keep) * np.pi * (HOLE_D / 2) ** 2, 1),
                       kept_max_edge_r_mm=r(max(h["r"] for h in keep) + HOLE_D / 2, 2))
    print("grille: %d holes, plug %d (ring %.0f mm), keep %d; kept open %d, plugs still open %d, flush worst %s mm" % (
        len(holes), len(plug), PLUG_RING_R, len(keep), kept_open, open_after, J["grille"]["plug_flush_worst_mm"]))
    J["file"] = dict(watertight=bool(out.is_watertight), volume_mm3=r(out.volume, 1),
                     volume_vs_print_before_mm3=r(out.volume - base.volume, 1), faces=int(len(out.faces)))
    J["pass"] = bool(J["mic_seats"]["ok"] and out.is_watertight and open_after == 0 and kept_open == len(keep)
                     and flush and max(flush) <= 0.05)
    print("watertight %s, +%.1f mm3 against print/head.stl before; pass %s" % (out.is_watertight, out.volume - base.volume, J["pass"]))
    if a.write:
        out.export(OUT)
        J["file"]["bytes"] = os.path.getsize(OUT)
        dump(J, os.path.join(HERE, "head_freeze.json"))
        print("wrote", OUT, J["file"]["bytes"], "bytes")


if __name__ == "__main__":
    main()
