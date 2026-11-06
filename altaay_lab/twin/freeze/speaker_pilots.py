#!/usr/bin/env python3
"""speaker_pilots.py: measure the 4 speaker_stand side pilots on their own axis (HARDWARE_AUDIT B8, FASTENERS finding 19).
CAD check only.

Run: python3 altaay_lab/twin/freeze/speaker_pilots.py [--write-fasteners]
--write-fasteners puts the measured axis, the pilot extent and the engagement into fasteners.json and fasteners.csv
(rows F352 to F355) and writes speaker_pilots.json.

Why: the record said the stand pilots are "drilled 20.7 deg off the hole axis". That number came from the feat3d fit
(audit/feat3d.py), which reads every bore along a mesh axis: the speaker axis is 20.7 deg off the head y axis
(acos 0.935), so a pilot along the speaker axis is read 20.7 deg off. The ear pilots had the same artefact
(PR 25, twin/companion/ear_mount.py). Here each pilot is measured on print/speaker_stand.stl along the screw axis:
  1. centre and diameter from 36 radial rays at 0.4 mm steps along the axis (the centre drift gives any tilt);
  2. PCA of the pilot wall vertices within 1.3 mm of the axis gives its own axis;
  3. rays parallel to the axis at 1.2, 1.6 and 2.0 mm off it give where the interface plate and the stand material
     start and end along the screw.
Engagement = screw tip (seat + length) - start of the stand material.
"""
import argparse
import csv
import io
import json
import os

import numpy as np

from flib import LAB, HERE, scene, inst_by_key, frame_from_axis, hits_along, r, dump, FASTENERS

IDS = ("F352", "F353", "F354", "F355")
FIT_ANGLE = 20.7


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--write-fasteners", action="store_true")
    a = ap.parse_args()
    S = scene()
    st = S.world_mesh(inst_by_key(S, "speaker_stand")[0])
    si = S.world_mesh(inst_by_key(S, "speaker_interface")[0])
    D = json.load(open(FASTENERS))
    F = {f["id"]: f for f in D["fasteners"]}
    out = {}
    for fid in IDS:
        f = F[fid]
        ax = np.array(f["axis_world"], float)
        ax, u, v = frame_from_axis(ax)
        p = np.array(f["seat_world"], float)
        fitted = not str(f.get("status") or "").startswith(("LEAVE OUT", "NOT FITTED"))
        cen, dia = [], []
        for t in np.arange(0.2, 14.0, 0.4):
            o = p + ax * t
            q = []
            for ang in np.linspace(0, 2 * np.pi, 36, endpoint=False):
                d = np.cos(ang) * u + np.sin(ang) * v
                h = hits_along(st, o, d)
                h = [x for x in h if x > 0]
                if h and h[0] < 2.0:
                    q.append(o + d * h[0])
            if len(q) >= 33:
                q = np.array(q)
                cen.append((t, q.mean(0)))
                dia.append(2 * np.linalg.norm(q - q.mean(0), axis=1).mean())
        rec = dict(fitted=fitted)
        if len(cen) >= 3:
            C = np.array([x[1] for x in cen])
            axc = np.linalg.svd(C - C.mean(0))[2][0]
            rec.update(pilot_d_mm=r(np.median(dia), 2), pilot_found_t_mm=[r(cen[0][0], 1), r(cen[-1][0], 1)],
                       centre_line_vs_screw_deg=r(np.degrees(np.arccos(min(1.0, abs(axc @ ax)))), 2),
                       centre_off_mm=r(np.max(np.linalg.norm(np.cross(C - p, ax), axis=1)), 3))
        V = st.vertices
        dv = V - p
        t_ = dv @ ax
        rad = np.linalg.norm(dv - np.outer(t_, ax), axis=1)
        sel = V[(rad < 1.3) & (t_ > 1.5) & (t_ < 6.5)]
        if len(sel) >= 6:
            a_ = np.linalg.svd(sel - sel.mean(0))[2][0]
            rec["pilot_axis_measured_deg"] = r(np.degrees(np.arccos(min(1.0, abs(a_ @ ax)))), 2)
            rec["pilot_axis_vs_mesh_y_deg"] = r(np.degrees(np.arccos(min(1.0, abs(a_[1])))), 1)
        ext = {}
        for name, m in (("interface", si), ("stand", st)):
            spans = []
            for rr in (1.2, 1.6, 2.0):
                h = [x - 3 for x in hits_along(m, p - ax * 3 + u * rr, ax)]
                spans.append(h[:2])
            ext[name] = spans
        st0 = min(s[0] for s in ext["stand"] if s)
        st1 = max(s[1] for s in ext["stand"] if len(s) > 1)
        rec.update(interface_mm=[r(ext["interface"][1][0]), r(ext["interface"][1][1])] if len(ext["interface"][1]) > 1 else None,
                   stand_material_mm=[r(st0), r(st1)], screw=f["spec"], screw_length_mm=f["length_mm"])
        rec["pilot_through"] = not [x for x in hits_along(st, p + ax * (st0 + 0.5), ax) if x > 0]
        rec["engaged_mm"] = r(f["length_mm"] - st0, 2)
        rec["tip_to_exit_mm"] = r(st1 - f["length_mm"], 2)
        out[fid] = rec
    fit = [out[k] for k in IDS if out[k]["fitted"]]
    ang = max(x["pilot_axis_measured_deg"] for x in fit)
    J = dict(script="altaay_lab/twin/freeze/speaker_pilots.py", label="CAD check only", fit_angle_feat3d_deg=FIT_ANGLE,
             pilots=out, verdict=("coaxial: the 2 fitted pilots are %.2f deg off the screw axis on the mesh; the 20.7 deg was "
                                  "the feat3d fit reading them along the mesh y axis (the same artefact as the ear pilots, PR 25)" % ang)
             if ang < 2.0 else "tilted %.1f deg on the mesh" % ang)
    print(json.dumps(J, indent=1))
    if a.write_fasteners:
        note_old = [n for n in F["F353"]["notes"] if "deg off the clearance hole axis" in n]
        for fid in IDS:
            rec, f = out[fid], F[fid]
            f["pilot_axis_measured_deg"] = rec.get("pilot_axis_measured_deg")
            f["pilot_measured"] = dict(d_mm=rec.get("pilot_d_mm"), stand_material_mm=rec["stand_material_mm"],
                                       through=rec["pilot_through"], engaged_mm=rec["engaged_mm"],
                                       by="altaay_lab/twin/freeze/speaker_pilots.py (CAD check only)")
            new = ("pilot on the screw axis: measured on the mesh %.2f deg off (the feat3d fit reads it along the head y axis, "
                   "%.1f deg off); the 2.05 mm pilot runs through %.1f mm of stand wall (t %.2f to %.2f mm from the seat), so an "
                   "M2.5x5 engages %.1f mm" % (rec["pilot_axis_measured_deg"], FIT_ANGLE, rec["stand_material_mm"][1] - rec["stand_material_mm"][0],
                                               rec["stand_material_mm"][0], rec["stand_material_mm"][1], rec["engaged_mm"]))
            f["notes"] = [n for n in f["notes"] if "deg off the clearance hole axis" not in n] + [new]
        with open(FASTENERS, "w") as fh:
            json.dump(D, fh)
        fc = os.path.join(LAB, "fasteners", "fasteners.csv")
        rows = list(csv.reader(open(fc, newline="")))
        hdr = rows[0]
        ni = hdr.index("notes") if "notes" in hdr else None
        if ni is not None:
            for row in rows[1:]:
                if row and row[0] in IDS:
                    row[ni] = "; ".join(F[row[0]]["notes"])
            buf = io.StringIO()
            csv.writer(buf, lineterminator="\r\n").writerows(rows)
            open(fc, "w", newline="").write(buf.getvalue())
        dump(J, os.path.join(HERE, "speaker_pilots.json"))
        print("fasteners.json and .csv: %s updated (old note: %s)" % (", ".join(IDS), note_old))


if __name__ == "__main__":
    main()
