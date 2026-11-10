#!/usr/bin/env python3
"""sit_print.py: the print records of the A1b sit parts (D59): print/SLICE_SUMMARY.md and PRINT_CHECK.md.

  python3 altaay_lab/print/slice.py parts --out <S> --only <the D59 STLs> --jobs 2       (PrusaSlicer 2.7.2, D22 light)
  python3 altaay_lab/twin/sit/sit_print.py --slice <S> [--write]

Starts from both files at sitlib.BASE_REV (a re-run gives the same text) and:
  SLICE_SUMMARY.md  the per-part rows of every STL this job changed or added get the numbers of the run in <S>; the
                    quantities follow print/parts.csv (the thigh pair of knee_to_ankle sheets and leg_spacer are 2 now);
                    the totals table is the sum of the per-part rows (it was not recomputed after D38 to D50: the rows
                    added up to 1287.4 g against its 1293.8 g); a D59 paragraph says what was run.
  PRINT_CHECK.md    the 8 new STLs get a per-STL row measured here on the oriented STL of the run (overhang over 45 deg,
                    ray wall thickness p1 and median, insert bores 3.9 to 4.2 mm and their least wall, the servo pocket
                    against the STS3215 case at the zero pose) with the run's grams (light profile, flagged D59); the
                    quantities follow parts.csv; the totals add the new rows (light profile, so marked); a D59 note.
Grams and hours are slicer estimates, not printed results.
"""
import argparse
import csv
import json
import os
import re
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sitlib as L  # noqa: E402

SS = os.path.join(L.LAB, "print", "SLICE_SUMMARY.md")
PC = os.path.join(L.LAB, "PRINT_CHECK.md")
NEW = ["ankle_pad", "head_pad", "hip_pad", "knee_bumper", "neck_pad", "neck_stop", "roll_pad_left", "roll_pad_right", "shin_left_sheet",
       "shin_right_sheet", "shin_spacer", "sit_bumper", "sit_seat"]
CHANGED = ["foot_side", "foot_top", "head_pitch_to_yaw", "knee_to_ankle_left_sheet", "knee_to_ankle_right_sheet", "left_cache",
           "right_cache", "left_roll_to_pitch", "right_roll_to_pitch", "leg_spacer"]      # the neck sheets are stock again
PROFILE = {"light": "light (base)", "sparse": "light (sparse)"}


def parts_csv():
    return {r["stl"][:-4]: r for r in csv.DictReader(open(os.path.join(L.LAB, "print", "parts.csv")))}


def profile_text(r, res):
    if r["profile"] == "heavy":
        return "heavy (%s)" % r["overrides"]
    if r["profile"] == "rings":
        n = sum(v for v in (res.get("rings") or {}).values())
        kind = list((res.get("rings") or {"insert": 0}))[0]
        return "rings (base + %d %s rings)" % (n, kind)
    return PROFILE.get(r["overrides"] or "light", "light (%s)" % r["overrides"])


def ss_row(stem, r, res):
    q = int(r["qty"])
    return "| %s.stl | %d | %s | %s | %.2f | %.2f | %.2f | %.1f | %.2f | - | - |" % (
        stem, q, r["material"], profile_text(r, res), res["g"], res["s"] / 3600, res["g_support"], q * res["g"], q * res["s"] / 3600)


def update_slice_summary(txt, P, R, when):
    lines = txt.split("\n")
    rows, idx = {}, {}
    for i, l in enumerate(lines):
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        if l.startswith("| ") and len(c) == 11 and c[0].endswith(".stl") and c[1].isdigit():
            rows[c[0][:-4]] = c
            idx[c[0][:-4]] = i
    for stem in CHANGED:
        c = rows[stem]
        res, r = R[stem + ".stl"], P[stem]
        q = int(r["qty"])
        before = c[9:11]
        lines[idx[stem]] = "| %s.stl | %d | %s | %s | %.2f | %.2f | %.2f | %.1f | %.2f | %s | %s |" % (
            stem, q, c[2], c[3], res["g"], res["s"] / 3600, res["g_support"], q * res["g"], q * res["s"] / 3600, before[0], before[1])
    # new rows, in name order inside the table
    last = max(idx.values())
    table = [lines[i] for i in sorted(idx.values())]
    for stem in NEW:
        table.append(ss_row(stem, P[stem], R[stem + ".stl"]))
    table.sort(key=lambda l: l.split("|")[1].strip())
    first = min(idx.values())
    lines = lines[:first] + table + lines[last + 1:]
    # totals from the rows
    allrows = [[x.strip() for x in l.strip().strip("|").split("|")] for l in table]
    tot = {}
    for c in allrows:
        m = c[2]
        t = tot.setdefault(m, [0, 0.0, 0.0, 0.0])
        q = int(c[1])
        t[0] += q
        t[1] += q * float(c[4])
        t[2] += q * float(c[5])
        t[3] += q * float(c[6])
    out = []
    for l in lines:
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        if l.startswith("| ") and len(c) == 7 and c[0] in ("PLA", "TPU", "Total"):
            if c[0] == "Total":
                t = [sum(v[k] for v in tot.values()) for k in range(4)]
            else:
                t = tot[c[0]]
            l = "| %s | %d | %.1f | %.1f | %.1f | %s | %s |" % (c[0], t[0], t[1], t[2], t[3], c[5], c[6])
        out.append(l)
    txt = "\n".join(out)
    n_stl, n_parts = len(allrows), sum(int(c[1]) for c in allrows)
    txt = txt.replace("## Per part (robot set: 36 STLs, 52 parts)", "## Per part (robot set: %d STLs, %d parts)" % (n_stl, n_parts))
    tg = sum(v[1] for v in tot.values())
    th = sum(v[2] for v in tot.values())
    para = ("V1 sit job, %s (D59; twin/sit/SIT.md): the %d STLs it changed or added sliced with `slice.py parts --only` (D22 "
            "light profile; TPU parts on the sole profile, sit_seat and sit_bumper at 10 %% infill, config/ovr_sparse.ini), "
            "same box, and their rows replaced or added (the 'before' columns of the new parts are empty: they have no "
            "pre-D22 version). Quantities follow print/parts.csv: knee_to_ankle_left_sheet, knee_to_ankle_right_sheet and "
            "leg_spacer are the thigh parts only now (2 each); the shins print shin_left_sheet, shin_right_sheet and "
            "shin_spacer. The totals table below is now the sum of the per-part rows (%d STLs, %d parts, %.1f g, %.1f h); "
            "before this job its rows added up to 1287.4 g against its 1293.8 g, as the D38 to D50 rows were updated "
            "without it. The plate tables and the D22 comparison are not re-run." % (when, len(NEW) + len(CHANGED), n_stl, n_parts, tg, th))
    # the D22 section keeps its numbers of then; its set size is no claim about the set now (verify/c9_docs.py)
    txt = txt.replace("- Robot set (36 STLs, 52 parts): 1280.3 g", "- Robot set at D22 (36 STLs then; 52 parts): 1280.3 g")
    anchor = "## What changed with D22"
    txt = txt.replace(anchor, para + "\n\n" + anchor, 1)
    return txt, dict(stls=n_stl, parts=n_parts, grams=round(tg, 1), hours=round(th, 1),
                     by_material={k: dict(parts=v[0], grams=round(v[1], 1), hours=round(v[2], 1), support=round(v[3], 1)) for k, v in tot.items()})


# ---------------------------------------------------------------------------------------------------------------
# geometry columns of PRINT_CHECK for a new STL (its method section)
# ---------------------------------------------------------------------------------------------------------------
def overhang_area(m):
    n = m.face_normals
    a = m.area_faces
    zmin = m.bounds[0][2]
    on_bed = np.all(np.abs(m.vertices[m.faces][:, :, 2] - zmin) < 0.05, axis=1)
    return float(a[(n[:, 2] < -np.cos(np.radians(45))) & ~on_bed].sum())


def wall_p1_median(m, n=3000, seed=0):
    pts, fi = trimesh.sample.sample_surface(m, n, seed=seed)
    d = -m.face_normals[fi]
    o = pts + d * 1e-3
    loc, ri, _ = m.ray.intersects_location(o, d, multiple_hits=False)
    t = np.full(n, np.nan)
    t[ri] = np.linalg.norm(loc - o[ri], axis=1)
    t = t[np.isfinite(t) & (t > 0.05)]
    return float(np.percentile(t, 1)), float(np.median(t))


def insert_walls(m):
    out = []
    for f in L.hole_features(m):
        if f["kind"] != "circle" or not (3.9 <= f["d"] <= 4.2):
            continue
        p0, p1 = np.asarray(f["p0"], float), np.asarray(f["p1"], float)
        if np.linalg.norm(p1 - p0) < 3.0:
            continue
        ax = (p1 - p0) / np.linalg.norm(p1 - p0)
        u = np.cross(ax, [0, 0, 1.0]) if abs(ax[2]) < 0.9 else np.cross(ax, [1.0, 0, 0])
        u /= np.linalg.norm(u)
        v = np.cross(ax, u)
        best = np.inf
        for s in np.linspace(0.15, 0.85, 5):
            c = p0 + (p1 - p0) * s
            dirs = np.array([np.cos(t) * u + np.sin(t) * v for t in np.linspace(0, 2 * np.pi, 36, endpoint=False)])
            o = np.repeat(c[None], len(dirs), 0) + dirs * (f["d"] / 2 + 0.05)
            loc, ri, _ = m.ray.intersects_location(o, dirs, multiple_hits=False)
            if len(ri):
                best = min(best, float(np.min(np.linalg.norm(loc - o[ri], axis=1))))
        out.append(best)
    return out


def servo_pen(stem):
    """largest depth of the STS3215 case parts inside the part at the zero pose (shin sheets only): the depth of the
    intersection along the sheet normal (y)"""
    if not stem.startswith("shin_") or stem == "shin_spacer":
        return "none"
    S = L.scene(fresh=True)
    worst = 0.0
    for link in ("knee_and_ankle_assembly_2",):
        part = [i for i in S.inst if i["link"] == link and i["key"] == stem]
        case = [i for i in S.inst if i["link"] == link and i["key"] in ("servo_top", "servo_mid", "servo_bottom")]
        P = L.to_man(S.world_mesh(part[0]))
        for c in case:
            I = P ^ L.to_man(S.world_mesh(c))
            if I.volume() > 1e-4:
                b = L.from_man(I).bounds
                worst = max(worst, float(b[1][1] - b[0][1]))
    return "yes, max pen %.2f" % worst


def pc_row(stem, r, res, sdir):
    m = trimesh.load(os.path.join(sdir, "oriented", stem + ".stl"), force="mesh")
    fp = sorted(res["footprint"], reverse=True)
    fit = " ".join("%d:%s" % (b, "Y" if fp[0] <= b and fp[1] <= b else "N") for b in (180, 220, 256))
    p1, med = wall_p1_median(m)
    ins = insert_walls(trimesh.load(os.path.join(L.REPO, "print", stem + ".stl"), force="mesh"))
    q = int(r["qty"])
    up = r["up"] if not r["up"].startswith("vec:") else "turned (%s)" % r["up"][4:]
    mat = "%s %s" % (r["material"], "10%" if r["overrides"] == "sparse" else ("40%" if r["material"] == "TPU" else "15%"))
    if r["profile"] == "rings":
        mat += ", rings"
    elif r["profile"] == "heavy":
        mat += ", %s" % r["overrides"]
    flags = "D59 sit part, light profile numbers (the table's other rows are the 7:24 PM run)"
    if r["material"] == "TPU":
        flags += "; on VHB 4950 (BOM 29)"
    return "| %s.stl | %d | %s | %s up | %.1fx%.1f | %.1f | %s | %.0f | %.2f/%.2f | %d | %s | 0/0 | %s | %.2f | %.2f | %.2f | %.2f | %s |" % (
        stem, q, mat, up, fp[0], fp[1], res["height"], fit, overhang_area(m), p1, med, len(ins),
        ("%.2f" % min(ins)) if ins else "-", servo_pen(stem), res["g"], res["s"] / 3600, q * res["g"], q * res["s"] / 3600, flags)


def update_print_check(txt, P, R, sdir, when, ss_tot):
    lines = txt.split("\n")
    idx = {}
    for i, l in enumerate(lines):
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        if l.startswith("| ") and len(c) == 18 and c[0].endswith(".stl") and c[1].isdigit():
            idx[c[0][:-4]] = i
    for stem, i in idx.items():
        c = [x.strip() for x in lines[i].strip().strip("|").split("|")]
        q = int(P[stem]["qty"])
        if int(c[1]) != q:
            ge, he = float(c[13]), float(c[14])
            c[1], c[15], c[16] = str(q), "%.2f" % (q * ge), "%.2f" % (q * he)
            c[17] = (c[17] + "; " if c[17] else "") + "qty %s since D59 (thigh only)" % q
            lines[i] = "| " + " | ".join(c) + " |"
    table = [lines[i] for i in sorted(idx.values())] + [pc_row(s, P[s], R[s + ".stl"], sdir) for s in NEW]
    table.sort(key=lambda l: l.split("|")[1].strip())
    first, last = min(idx.values()), max(idx.values())
    lines = lines[:first] + table + lines[last + 1:]
    rows = [[x.strip() for x in l.strip().strip("|").split("|")] for l in table]
    tot = {}
    for c in rows:
        k = "TPU" if c[2].startswith("TPU") else "PLA"
        t = tot.setdefault(k, [0, 0.0, 0.0])
        t[0] += int(c[1])
        t[1] += float(c[15])
        t[2] += float(c[16])
    out = []
    for l in lines:
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        if l.startswith("| ") and len(c) == 6 and (c[0].startswith("PLA (") or c[0].startswith("TPU") or c[0] == "Total"):
            k = "Total" if c[0] == "Total" else ("TPU" if c[0].startswith("TPU") else "PLA")
            t = [sum(v[j] for v in tot.values()) for j in range(3)] if k == "Total" else tot[k]
            l = "| %s | %d | %.1f | %.1f | %s | %s |" % (c[0], t[0], t[1], t[2], c[4], c[5])
        out.append(l)
    txt = "\n".join(out)
    n_stl, n_parts = len(rows), sum(int(c[1]) for c in rows)
    txt = txt.replace("all 36 STLs fit (this line said 38 before; print/ has 36 robot STLs, 52 parts, as the table shows)",
                      "all %d STLs fit (this line said 38, then 36 before D59; print/ has %d robot STLs, %d parts, as the table shows)" % (n_stl, n_stl, n_parts))
    note = ("## Note %s: D59 alert sit parts\n\n"
            "The A1b sit (DECISIONS.md D59, twin/sit/SIT.md; CAD check only) changes 11 printed parts and adds 8 new ones. New rows here: "
            "%s, measured on the oriented STLs of a `slice.py parts --only` run (D22 light profile; their grams and hours are "
            "that run's, not the 7:24 PM run of the other rows; TPU pads and blocks go on VHB 4950). Quantities follow "
            "print/parts.csv: the knee_to_ankle sheets and leg_spacer are the thigh parts only (2 each); the shins print "
            "shin_left_sheet, shin_right_sheet (joggled 9 mm, with the clamp block) and shin_spacer. The changed STLs keep their "
            "rows here (geometry columns of the stock part; their light-profile grams are in print/SLICE_SUMMARY.md): the thigh "
            "sheets lose about 0.4 cm3 at the front edge; foot_top and foot_side get the heel notch, the ankle pad seat and the "
            "heel screw moved 20 mm toward the toe (old holes closed, D39); left_cache and right_cache are cut by about 12.6 cm3 "
            "for the fold; roll_to_pitch, both neck sheets and head_pitch_to_yaw get a stop lug. Every hole of a changed STL "
            "is checked to be there as before (twin/sit/sit_cad.py). Robot set now %d STLs, %d parts; in the light profile "
            "%.1f g and %.1f h (print/SLICE_SUMMARY.md).\n\n" % (when, ", ".join(NEW), n_stl, n_parts, ss_tot["grams"], ss_tot["hours"]))
    txt = txt.replace("# PRINT_CHECK\n\n", "# PRINT_CHECK\n\n" + note, 1)
    return txt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slice", required=True, help="the slice.py parts --out folder of the D59 STLs")
    ap.add_argument("--when", required=True, help="ET date and time of the slice run, for the notes (an empty one left a blank in both notes)")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    R = json.load(open(os.path.join(a.slice, "parts.json")))
    missing = [s for s in NEW + CHANGED if s + ".stl" not in R]
    if missing:
        raise SystemExit("the slice run has no %s" % missing)
    for s in NEW + CHANGED:                         # the run must be of the STLs in the tree now
        import hashlib
        h = hashlib.sha256(open(os.path.join(L.REPO, "print", s + ".stl"), "rb").read()).hexdigest()
        if R[s + ".stl"].get("sha256") != h:
            raise SystemExit("%s.stl changed since the slice run: slice it again" % s)
    P = parts_csv()
    ss, tot = update_slice_summary(L.git_blob("altaay_lab/print/SLICE_SUMMARY.md").decode(), P, R, a.when)
    pc = update_print_check(L.git_blob("altaay_lab/PRINT_CHECK.md").decode(), P, R, a.slice, a.when, tot)
    print(json.dumps(tot, indent=1))
    if a.write:
        open(SS, "w").write(ss)
        open(PC, "w").write(pc)
        print("written: print/SLICE_SUMMARY.md, PRINT_CHECK.md")


if __name__ == "__main__":
    main()
