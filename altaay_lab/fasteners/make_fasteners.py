#!/usr/bin/env python3
"""Every fastener instance of Open Duck Mini v2: found in the CAD, specified, checked, posed for the viewer.

  python3 altaay_lab/fasteners/make_fasteners.py --scratch <folder outside the repo>
  (or set ODM_FASTENER_SCRATCH). Writes altaay_lab/fasteners/fasteners.json and fasteners.csv.

What it does:
1. Builds the assembly like viewer/make_viewer_data.py (fastlib.Scene): robot.urdf at zero pose in mm, print/ STLs
   swapped in, head internals in the head.stl frame. Hole features are found on the STLs that get printed
   (audit/feat3d.py); head.stl and left/right_roll_to_pitch.stl in print/ differ from the URDF meshes the older
   audit (audit/sites.json) used.
2. Finds every screw joint with the same rules as audit/screws2.py (clearance hole, head seat, first anchor on the
   axis), keeping positions, plus the joints that rule cannot see: eye screws, camera, SG90 tabs and horn screws,
   STS3215 case screws (factory fitted), horn centre screws, the 58 M3 inserts.
3. Picks the shortest stock length that meets the cited engagement rule without bottoming (rays from the head seat
   along the screw find the first solid surface), and checks clearance holes and head recesses.
4. Counts per spec against BOM.md lines 16 and 17a to 17i.
The sweep over joint ranges is sweep_fasteners.py; the pictures are render_fasteners.py.
"""
import argparse
import csv
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fastlib  # noqa: E402
from fastlib import LINK_SUB, SERVO_TOP, SERVO_BOT, SERVO_MID, frame_from_axis  # noqa: E402

LAB = fastlib.LAB
REPO = fastlib.REPO

# ---------------------------------------------------------------------------------------------- sources
SRC = {
    "din912": "[I] https://westfieldfasteners.co.uk/Standards/ScrewBolt-SHCap-M.html (DIN 912 / ISO 4762 table 1: dk max M2 3.80, M2.5 4.50, M3 5.50; knurled heads up to 3.98, 4.68, 5.68; k max 2.00, 2.50, 3.00)",
    "insert_rule": "[I] https://tameson.com/pages/thread-engagement-chart (table 1: cast iron, brass 1.5 to 2.0 x screw diameter)",
    "pla_rule": "[I] https://westfieldfasteners.co.uk/Standards/ThreadForming-PhilPan30.html (\"Pilot holes should have a thread engagement of at least twice the screw diameter\"; table 2: ABS hole 0.80 x d, screw-in depth 2.00 x d; PLA is not listed, the ABS row is used)",
    "pa_rule": "[I] https://westfieldfasteners.co.uk/Standards/ThreadForming-PhilPan30.html (table 2: PA 6 GF 30 screw-in depth 1.90 x d, PA 6.6 GF 30 1.80 x d; the larger is used) with the case material PA+GF from the Feetech STS3215 datasheet item 6-3 [I] https://download.kamami.pl/p1198708-STS3215-C001-20230624.pdf",
    "alu_rule": "[I] https://www.nord-lock.com/insights/bolting-tips/2015/the-experts-thread-engagement-in-a-tapped-hole/ (about 2 x d in aluminium); horn plate thickness 2.4 mm (drive) and 2.2 mm (idle) from the URDF horn meshes [L]",
    "feetech_ds": "[I] https://download.kamami.pl/p1198708-STS3215-C001-20230624.pdf (Feetech STS3215 C001 spec 2023-06-23: item 6-13 rocker screw M3X6; drawing p.6: 8-PA2.0 self-tapping mounting holes, M3X6 machine screw at the output, PA3.0X5 self-tapping screw at the idle boss; p.8 packing photo)",
    "seeed": "[I] https://www.seeedstudio.com/STS3215-19kg-cm-7-4V-Serial-Servo-p-6338.html (part list: ST3215-C001 servo x1, servo horn x2, screw x18, JST wire x1)",
    "so101": "[I] https://huggingface.co/docs/lerobot/so101 (same STS3215 1/345: top horn secured with an M3x6 screw, no screw for the bottom horn, motor fastened with M2x6 screws, the smallest in the bag, printed parts to horns with M3x6)",
    "guide": "[U] docs/assembly_guide.md (b23317a): trunk_bottom to trunk_top 2 x M3x10; foot_bottom_tpu to foot_bottom_pla 2 x M3x6; servo case screws are the plastic screws that come with the motors; Loctite 243 on metal to metal motor screws",
    "d18": "[L] altaay_lab/DECISIONS.md D18 and print/check_hip_roll_screw.py (pan head modelled 4.0 x 1.6 mm, ISO 7045 M2 / ISO 7049 ST2.2)",
    "insert": "[L] altaay_lab/BOM.md line 16 (CNC Kitchen M3 x 5.7, D1 4.6, hole 4.0)",
    "sg90": "[I] https://www.rapidonline.com/rapid-pro-sg90-mini-servo-37-1330 (\"Supplied complete with control horns and mounting screws\"; sizes not published)",
    "iso7380": "[I] https://westfieldfasteners.co.uk/Standards/ScrewBolt-SHBtn-M.html (ISO 7380-1 table 1: M3 dk max 5.70, k max 1.65; M2.5 dk 4.5, k 1.5)",
}
MARGIN = 0.3            # mm the tip stays short of the first solid surface (lab choice for print tolerance) [L]
INSERT_L = 5.7          # [L] BOM line 16

# DIN 912 A2 lengths on BOM.md (length -> BOM line) and other standard lengths that would need a new BOM line
WASHER_SPEC = ("two M2.5 flat washers, ISO 7092 A4 HV200, 2.7 x 5.0 x 0.3 mm (BelMetric WFHV2.5X5SSA4, BOM 17l): "
               "a 0.6 mm stack under each eye screw head (D21 note)")
STOCK = {"M3": {5: "17e", 6: "17d", 8: "17a", 10: "17b", 12: "17c"},
         "M2.5": {6: "17f", 8: "17g", 10: "17i"}}
STD_EXTRA = {"M3": [4, 14, 16, 20], "M2.5": [4, 5, 12, 16]}
# self-tapping M2 pan head: servo bag (6 mm per the SO-101 guide, UNVERIFIED for this bag) and METALLIXITY kit (BOM 17h)
M2_KIT = [4, 5, 6, 8]
HEAD = {  # dk, k (mm) used to draw and to sweep
    "M3_din912": (5.5, 3.0), "M2.5_din912": (4.5, 2.5),
    "M2_pan_selftap": (4.0, 1.6),          # D18 model, real servo-bag head UNVERIFIED
    "M3_horn_centre": (5.6, 2.4),          # ISO 7045 M3 pan head as a stand-in, real head UNVERIFIED (photo shows a pan/button head)
    "PA3_idle": (6.0, 1.8),                # stand-in for the large washer head in the Feetech photo, UNVERIFIED
    "M2_case_factory": (4.0, 1.6),         # stand-in, sits in the 4.0 x 1.6 counterbore of the CAD case
    "SG90_screw": (4.0, 1.6),              # stand-in, UNVERIFIED
    "M3_iso7380": (5.7, 1.65), "M2.5_iso7380": (4.5, 1.5),   # button head, Westfield ISO 7380-1 table 1 [I]
}
KNURL = {"M3": 5.68, "M2.5": 4.68, "M2": 3.98}   # DIN 912 knurled head dk max (SRC din912)
COLORS = {  # colour by spec for the viewer and the pictures
    "M3x5": "#1f77b4", "M3x6": "#4f9fde", "M3x8": "#2ca02c", "M3x10": "#98df8a", "M3x12": "#006d2c",
    "M2.5x6": "#d62728", "M2.5x8": "#ff9896", "M2.5x10": "#8c1c13",
    "M2 servo bag": "#9467bd", "M2 kit": "#c5b0d5", "M3 horn centre": "#ff7f0e", "PA3 idle": "#000000",
    "M2 case (factory)": "#7f7f7f", "SG90 bag": "#e377c2", "M3 insert": "#d3a62c", "other": "#17becf",
    "M2.5x5": "#ff00ff", "M3x6 button": "#8c564b",
}


# ---------------------------------------------------------------------------------------------- rows (audit/screws2.py rules)
def anchor_type(m, d, L):
    if m == "drive_palonier" and abs(d - 2.5) < 0.2:
        return "horn(drive)"
    if m == "passive_palonier" and abs(d - 2.5) < 0.2:
        return "horn(passive)"
    if abs(d - 4.0) < 0.15 and L >= 5.0:
        return "M3 insert"
    if m.startswith("wj-") and d < 2.1:
        return "servo pilot"
    if abs(d - 2.0) < 0.1 and L >= 4.5 and not m.startswith("wj-"):
        return "plastic pilot 2.0"
    # added here (audit/screws2.py skips these): eye pilots 2.05 and 2.2 mm, 3.0 mm long
    if m in ("left_eye", "right_eye") and 1.9 <= d <= 2.3 and L >= 2.5:
        return "plastic pilot (eye)"
    return None


def centreline_point(w, p):
    """Point on the centre line of hole feature w closest to p."""
    a = (w["p1"] - w["p0"]) / np.linalg.norm(w["p1"] - w["p0"])
    return w["p0"] + a * np.dot(p - w["p0"], a)


def screw_rows(sites):
    rows = []
    for si, s in enumerate(sites):
        o, ax = np.array(s["o"], float), np.array(s["ax"], float)
        segs = [dict(t0=a, t1=b, m=m, k=k, d=d, i=i, w=w) for (a, b, m, k, d, i), w in zip(s["segs"], s["feat"])]
        for sg in segs:
            m = sg["m"]
            if m.startswith("wj-") or "palonier" in m:
                continue
            if not (2.4 <= sg["d"] <= 3.7):
                continue
            if anchor_type(m, sg["d"], sg["t1"] - sg["t0"]):
                continue
            heads = [h for h in segs if h["i"] == sg["i"] and 3.9 <= h["d"] <= 7.1
                     and (abs(h["t1"] - sg["t0"]) < 0.45 or abs(h["t0"] - sg["t1"]) < 0.45)
                     and not (abs(h["d"] - 4.0) < 0.15 and h["t1"] - h["t0"] >= 5.0)]
            rec = None
            if heads:
                h = heads[0]
                direction = 1 if abs(h["t1"] - sg["t0"]) < 0.45 else -1
                hf = h["t1"] if direction == 1 else h["t0"]
                seat = "recess d%s" % h["d"]
                rec = h
            else:
                seat, hf = "flat face", None
                for direction, face in ((1, sg["t0"]), (-1, sg["t1"])):
                    c = [x for x in segs if x["i"] != sg["i"] and anchor_type(x["m"], x["d"], x["t1"] - x["t0"])
                         and (x["t0"] - face) * direction > 0]
                    if c:
                        hf = face
                        break
                if hf is None:
                    continue
            cand = [x for x in segs if x["i"] != sg["i"] and anchor_type(x["m"], x["d"], x["t1"] - x["t0"])
                    and max((x["t0"] - hf) * direction, (x["t1"] - hf) * direction) > 0.3]
            r = dict(site=si, part=m, part_inst=sg["i"], clr=round(sg["d"], 2),
                     clr_len=round(sg["t1"] - sg["t0"], 2), seat=seat, seat_pt=o + ax * hf, axis=ax * direction,
                     recess=None if rec is None else dict(d=rec["d"], depth=round(rec["t1"] - rec["t0"], 2)),
                     segs=[(round((x["t0"] - hf) * direction, 2), round((x["t1"] - hf) * direction, 2), x["m"], x["d"], x["i"])
                           for x in segs])
            if not cand:
                r.update(anchor="NONE", into=None, into_inst=None, near=None, far=None, anchor_d=None)
            else:
                cand.sort(key=lambda x: min((x["t0"] - hf) * direction, (x["t1"] - hf) * direction))
                a = cand[0]
                near = min((a["t0"] - hf) * direction, (a["t1"] - hf) * direction)
                far = max((a["t0"] - hf) * direction, (a["t1"] - hf) * direction)
                # the screw sits on the anchor's own centre line (the site axis can be up to 0.35 mm off it)
                seat_a = centreline_point(a["w"], r["seat_pt"])
                clr_c = centreline_point(sg["w"], seat_a)
                r.update(anchor=anchor_type(a["m"], a["d"], a["t1"] - a["t0"]), into=a["m"], into_inst=a["i"],
                         near=round(near, 2), far=round(far, 2), anchor_d=a["d"], anchor_t0=round(a["t0"], 2),
                         seat_pt=seat_a, offset=round(float(np.linalg.norm(seat_a - clr_c)), 3))
            rows.append(r)
    return rows


# ---------------------------------------------------------------------------------------------- geometry helpers
def ring_dirs(axis, r, n=8):
    M = frame_from_axis([0, 0, 0], axis)
    x, y = M[:3, 0], M[:3, 1]
    return [np.zeros(3)] + [r * (np.cos(a) * x + np.sin(a) * y) for a in np.linspace(0, 2 * np.pi, n, endpoint=False)]


def stop_distance(S, seat, axis, r_ring):
    """First solid surface met by the screw core, from the seat along the axis (rays at the centre and on a ring)."""
    offs = ring_dirs(axis, r_ring)
    org = np.array([seat + o + axis * 0.05 for o in offs])
    d = np.tile(axis, (len(org), 1))
    t = S.first_hits(org, d, tmin=0.05)
    return float(t.min() + 0.05)


def servo_groups(S):
    """Group the 3 case parts and 2 horns of each STS3215 and name it by the joint its drive horn turns
    (same heuristic as viewer/make_viewer_data.py)."""
    inst = S.inst
    cent = {}
    for k, i in enumerate(inst):
        m = S.mesh(k)
        cent[k] = m.bounds.mean(0)
    by_link = defaultdict(list)
    for k, i in enumerate(inst):
        if i["name"] in (SERVO_TOP, SERVO_MID, SERVO_BOT, "drive_palonier", "passive_palonier"):
            by_link[i["link"]].append(k)
    groups = []
    for ln, ks in by_link.items():
        mids = [k for k in ks if inst[k]["name"] == SERVO_MID]
        free = set(ks) - set(mids)
        for km in mids:
            g = {"mid": km, SERVO_MID: km, "link": ln}
            for part in (SERVO_TOP, SERVO_BOT, "drive_palonier", "passive_palonier"):
                cand = [k for k in free if inst[k]["name"] == part]
                kb = min(cand, key=lambda k: np.linalg.norm(cent[k] - cent[km]))
                free.discard(kb)
                g[part] = kb
            hc = cent[g["drive_palonier"]]

            def axis_dist(j):
                d = hc - j["origin"]
                return np.linalg.norm(d - np.dot(d, j["axis"]) * j["axis"])
            cand = [j for j in S.joints if not j["name"].endswith("antenna") and ln in (j["parent"], j["child"])]
            j = min(cand, key=lambda j: (round(axis_dist(j), 1), np.linalg.norm(hc - j["origin"])))
            g.update(joint=j["name"], axis_err=round(float(axis_dist(j)), 2))
            groups.append(g)
    return groups


def link_pose(S, link, seat, axis):
    Tl = S.T0[link]
    Ti = np.linalg.inv(Tl)
    M = frame_from_axis(seat, axis)
    Ml = Ti @ M
    return Ml, (Ti @ np.r_[seat, 1])[:3], Ti[:3, :3] @ axis


# ---------------------------------------------------------------------------------------------- BOM
def bom_lines():
    path = os.path.join(LAB, "BOM.md")
    out = {}
    for ln in open(path, encoding="utf-8"):
        if not ln.startswith("|"):
            continue
        c = [x.strip() for x in ln.strip().strip("|").split("|")]
        if len(c) > 5 and re.match(r"^(1[67][a-z]?|18|19|1|14)$", c[0]):
            out[c[0]] = dict(item=c[1], spec=c[2], need=c[3], buy=c[4])
    return out


# ---------------------------------------------------------------------------------------------- length rules
def pick_length(kind, size, near, far, stop, flush_max=None):
    """Shortest stock length meeting the engagement rule without bottoming.
    kind: insert | horn | pla | eye | servo. Returns a dict with L, e, e_min, rule text, status."""
    lmax = stop - MARGIN
    if flush_max is not None:
        lmax = min(lmax, flush_max)
    if kind == "insert":
        d, e_min, rule = 3.0, 4.5, "brass insert: engage >= 1.5 x d = 4.5 mm of the 5.7 mm insert " + SRC["insert_rule"]
        cand = [(L, STOCK["M3"].get(L)) for L in sorted(set(STOCK["M3"]) | set(STD_EXTRA["M3"]))]
        eng = lambda L: min(L - near, INSERT_L)
        lmin = near + e_min
    elif kind == "horn":
        d, rule = 3.0, "metal horn, tapped M3, %.1f mm thread: engage the full horn thread, tip clear of the servo case; " \
                       "2 x d for aluminium cannot be met by design (" % (far - near) + SRC["alu_rule"] + "); " + SRC["so101"]
        e_min = far - near
        cand = [(L, STOCK["M3"].get(L)) for L in sorted(set(STOCK["M3"]) | set(STD_EXTRA["M3"]))]
        eng = lambda L: min(L, far) - near
        lmin = far
    elif kind in ("pla", "eye"):
        d, e_min = 2.5, 5.0
        rule = "M2.5 self-tapping a printed PLA pilot: screw-in depth >= 2 x d = 5.0 mm " + SRC["pla_rule"]
        cand = [(L, STOCK["M2.5"].get(L)) for L in sorted(set(STOCK["M2.5"]) | set(STD_EXTRA["M2.5"]))]
        eng = lambda L: min(L, far) - near
        lmin = near + e_min
    elif kind == "servo":
        d, e_min = 2.0, 3.8
        rule = "M2 self-tapping the STS3215 case (PA+GF): screw-in depth >= 1.9 x d = 3.8 mm " + SRC["pa_rule"]
        cand = [(L, "bag" if L == 6 else "17h") for L in M2_KIT]
        eng = lambda L: min(L, far) - near
        lmin = near + e_min
    elif kind == "pla_m2":
        d, e_min = 2.0, 4.0
        rule = "M2 self-tapping a printed PLA pilot: screw-in depth >= 2 x d = 4.0 mm " + SRC["pla_rule"]
        cand = [(L, "17h") for L in M2_KIT]
        eng = lambda L: min(L, far) - near
        lmin = near + e_min
    else:
        raise ValueError(kind)
    ok = [(L, ln) for L, ln in cand if L >= lmin - 1e-6 and L <= lmax + 1e-6]
    on_bom = [(L, ln) for L, ln in ok if ln]
    out = dict(rule=rule, e_min=round(e_min, 2), lmin=round(lmin, 2), lmax=round(lmax, 2))
    if on_bom:
        L, ln = on_bom[0]
        out.update(L=L, line=ln, status="OK")
    elif ok:
        L, ln = ok[0]
        out.update(L=L, line=None, status="NEW LENGTH")
    else:
        fits = [(L, ln) for L, ln in cand if L <= lmax + 1e-6 and ln]
        fits_any = [(L, ln) for L, ln in cand if L <= lmax + 1e-6]
        if fits:
            L, ln = fits[-1]
            out.update(L=L, line=ln, status="BELOW RULE")
        elif fits_any:
            L, ln = fits_any[-1]
            out.update(L=L, line=None, status="BELOW RULE, NEW LENGTH")
        else:
            L, ln = cand[0]
            out.update(L=L, line=ln, status="BOTTOMS")
    out["e"] = round(eng(out["L"]), 2)
    out["tip_gap"] = round(stop - out["L"], 2)
    return out


def clearance_status(clr, d, printed):
    m = clr - d
    if m < -1e-6:
        return "INTERFERENCE", round(m, 2)
    if printed and m < 0.15:
        return "TIGHT", round(m, 2)
    return "OK", round(m, 2)


# ---------------------------------------------------------------------------------------------- main
def build(scratch):
    t0 = time.time()
    S = fastlib.Scene(scratch)
    inst = S.inst
    sites, W = S.sites()
    n_hex = sum(1 for w in W if w["kind"] == "hex")
    print("scene: %d instances (%d URDF, assembly.json match %s), %d hole features (%d hex), %d sites, %.0f s" % (
        len(inst), S.n_urdf, S.assembly_match, len(W), n_hex, len(sites), time.time() - t0))
    raw = screw_rows(sites)
    groups = servo_groups(S)
    servo_of = {}
    for g in groups:
        for p in (SERVO_TOP, SERVO_MID, SERVO_BOT, "drive_palonier", "passive_palonier"):
            servo_of[g[p]] = g
    # one screw per anchor hole: rows that share a site and an anchor segment are one screw through a stack;
    # its head sits on the outermost part (largest near)
    best, dropped = {}, []
    for r in raw:
        if r["into_inst"] is None:
            best[("none", r["site"], r["part_inst"])] = r
            continue
        key = (r["site"], r["into_inst"], r["anchor_t0"], tuple(np.round(r["axis"], 2)))
        if key in best:
            keep, lose = (r, best[key]) if r["near"] > best[key]["near"] else (best[key], r)
            best[key] = keep
            dropped.append(dict(part=inst[lose["part_inst"]]["key"], under=inst[keep["part_inst"]]["key"], site=r["site"]))
        else:
            best[key] = r
    rows = list(best.values())
    rows.sort(key=lambda r: (r["site"], r["part_inst"]))
    print("screw rows %d raw, %d after merging stacked rows (%d merged: %s)" % (
        len(raw), len(rows), len(dropped), dict(Counter((d["part"], d["under"]) for d in dropped))))

    # horn holes the hole finder missed: a recess over the horn hole in the part screwed to the other holes
    horn_parts = defaultdict(set)
    for r in rows:
        if r["anchor"] in ("horn(drive)", "horn(passive)"):
            horn_parts[r["into_inst"]].add(r["part_inst"])
    have = {(r["site"], r["into_inst"]) for r in rows}
    added_horn = []
    for si, s in enumerate(sites):
        for (t0_, t1_, m, k, d, ii) in s["segs"]:
            if m not in ("drive_palonier", "passive_palonier") or abs(d - 2.5) > 0.2 or (si, ii) in have or ii not in horn_parts:
                continue
            o, ax = np.array(s["o"]), np.array(s["ax"])
            for pi in horn_parts[ii]:
                rec_segs = [x for x in s["segs"] if x[5] == pi and 4.9 <= x[4] <= 7.1]
                if not rec_segs:
                    continue
                rs = rec_segs[0]
                hw = [w for x, w in zip(s["segs"], s["feat"]) if x[5] == ii and x[2] == m and abs(x[4] - d) < 0.01][0]
                direction = 1 if rs[0] < t0_ else -1
                hf = rs[1] if direction == 1 else rs[0]          # recess floor = end of the recess toward the horn
                seat = centreline_point(hw, o + ax * hf)
                axis = ax * direction
                near = min((t0_ - hf) * direction, (t1_ - hf) * direction)
                far = max((t0_ - hf) * direction, (t1_ - hf) * direction)
                st = stop_distance(S, seat, axis, 0.4 * 2.5)
                if st < near:            # the path from the recess to the horn is blocked: no hole
                    continue
                r = dict(site=si, part=m, part_inst=pi, clr=None, clr_len=None, seat="recess d%s" % rs[4], seat_pt=seat,
                         axis=axis, recess=dict(d=rs[4], depth=round(rs[1] - rs[0], 2)),
                         segs=[(round((x[0] - hf) * direction, 2), round((x[1] - hf) * direction, 2), x[2], x[4], x[5]) for x in s["segs"]],
                         anchor="horn(drive)" if m == "drive_palonier" else "horn(passive)", into=m, into_inst=ii,
                         near=round(near, 2), far=round(far, 2), anchor_d=d, added="clearance hole not found by feat3d; "
                         "a recess sits over the horn hole and a ray from the recess floor reaches the horn (%.1f mm free)" % st)
                rows.append(r)
                added_horn.append(r)
                break
    print("horn screws added where the clearance hole was not detected: %d" % len(added_horn))

    F = []
    empty = []      # holes deliberately left empty, with the reason

    def add(rec):
        rec["id"] = "F%03d" % (len(F) + 1)
        F.append(rec)
        return rec

    # ------------------------------------------------------------------------------------------ 1. joints from the rows
    for r in rows:
        part = inst[r["part_inst"]]
        into = inst[r["into_inst"]] if r["into_inst"] is not None else None
        rec = dict(source="cad_row", site=r["site"], part=part["key"], part_inst=r["part_inst"], link=part["link"],
                   clr=r["clr"], clr_len=r["clr_len"], seat_type=r["seat"], recess=r["recess"], anchor=r["anchor"],
                   into=into["key"] if into else None, into_inst=r["into_inst"], near=r["near"], far=r["far"],
                   anchor_d=r["anchor_d"], seat_pt=np.array(r["seat_pt"], float), axis=np.array(r["axis"], float),
                   offset=r.get("offset"), notes=[r["added"]] if r.get("added") else [])
        if into is not None:
            if r["anchor"].startswith("horn"):
                g = servo_of.get(r["into_inst"])
                rec["servo"] = g["joint"] if g else None
            elif into["link"] != part["link"]:
                rec["notes"].append("LINK MISMATCH: part on %s, anchor on %s" % (part["link"], into["link"]))
            if into["name"].startswith("wj-"):
                g = servo_of.get(r["into_inst"])
                rec["servo"] = g["joint"] if g else None
        add(rec)

    # ------------------------------------------------------------------------------------------ 2. STS3215 case screws (factory)
    # top case STL frame: output axis at x=-25.5, z=0 along y; counterbored holes at x=-32.6, z=+-9.35 (floor y=3.4),
    # through holes at x=7.25, z=+-10 (top face y=5.0); bottom case pilots y -15.2 to -22.4 and -15.2 to -20.0 [L]
    CASE = [(-32.6, 9.35, 3.4, 18.6, 25.8, "output end, head in the 4.0 x 1.6 counterbore"),
            (-32.6, -9.35, 3.4, 18.6, 25.8, "output end, head in the 4.0 x 1.6 counterbore"),
            (7.25, 10.0, 5.0, 20.2, 25.0, "far end, head on the top face (no counterbore in the CAD)"),
            (7.25, -10.0, 5.0, 20.2, 25.0, "far end, head on the top face (no counterbore in the CAD)")]
    for g in sorted(groups, key=lambda g: g["joint"]):
        Tt = inst[g[SERVO_TOP]]["T"]
        for x, z, yseat, near, far, where in CASE:
            seat = (Tt @ np.r_[x, yseat, z, 1])[:3]
            axis = -(Tt[:3, :3] @ np.array([0, 1.0, 0]))
            add(dict(source="servo_case", part="servo top case", part_inst=g[SERVO_TOP], link=inst[g[SERVO_TOP]]["link"],
                     into="servo bottom case", into_inst=g[SERVO_BOT], anchor="servo case (factory)", servo=g["joint"],
                     near=near, far=far, seat_pt=seat, axis=axis, clr=2.0, clr_len=None, seat_type=where, recess=None,
                     notes=["comes with servo, fitted at the factory: do not remove; length and head not published"]))

    # ------------------------------------------------------------------------------------------ 3. horn centre and idle boss screws
    for g in sorted(groups, key=lambda g: g["joint"]):
        Td = inst[g["drive_palonier"]]["T"]
        seat = (Td @ np.r_[-25.5, 9.4, 0, 1])[:3]
        axis = -(Td[:3, :3] @ np.array([0, 1.0, 0]))
        out_link = sorted({inst[r["part_inst"]]["link"] for r in rows if r["into_inst"] == g["drive_palonier"]})
        add(dict(source="horn_centre", part="drive horn", part_inst=g["drive_palonier"], into="servo output shaft",
                 into_inst=g[SERVO_TOP], link=out_link[0] if out_link else inst[g["drive_palonier"]]["link"],
                 anchor="servo output shaft", servo=g["joint"], near=5.0, far=None, seat_pt=seat, axis=axis, clr=3.2,
                 clr_len=5.0, seat_type="flat face of the drive horn", recess=None,
                 notes=["comes with servo: M3x6 rocker screw per the Feetech datasheet; output shaft thread not modelled"]))
        Tp = inst[g["passive_palonier"]]["T"]
        seat_p = (Tp @ np.r_[-25.5, -28.2 + 0.0, 0, 1])[:3]       # boss end face (bottom case pilot entry at y=-28.2)
        Tb = inst[g[SERVO_BOT]]["T"]
        seat_p = (Tb @ np.r_[-25.5, -28.2, 0, 1])[:3]
        axis_p = Tb[:3, :3] @ np.array([0, 1.0, 0])
        n_idle = sum(1 for r in rows if r["into_inst"] == g["passive_palonier"])
        free = S.first_hits([seat_p - axis_p * 0.5], [-axis_p], tmin=0.05)[0]
        need = n_idle == 0
        add(dict(source="idle_boss", part="idle horn", part_inst=g["passive_palonier"], into="servo bottom case boss",
                 into_inst=g[SERVO_BOT], link=inst[g[SERVO_BOT]]["link"], anchor="servo idle boss pilot 2.67",
                 servo=g["joint"], near=0.0, far=5.4, seat_pt=seat_p, axis=axis_p, clr=6.1, clr_len=3.2,
                 seat_type="boss end face", recess=None, install=need,
                 notes=[("FIT: nothing is screwed to this idle horn and %.1f mm is free beyond it, so the PA3.0x5 screw from the bag "
                         "keeps it on the boss (Feetech drawing)" % free) if need else
                        ("NOT FITTED: the idle horn is held by %d M3 screws to its bracket (LeRobot SO-101 practice: no screw "
                         "on the idle horn); the PA3.0x5 screw stays in the bag" % n_idle)]))

    # ------------------------------------------------------------------------------------------ 4. head: camera, SG90 tabs
    Th = S.Th
    head_k = [k for k, i in enumerate(inst) if i["urdf"] == "head.stl"][0]
    cam = [w for w in W if w["i"] == head_k and 1.6 <= w["d"] <= 1.7 and 2.9 <= w["L"] <= 3.5]
    pcb = 1.0   # UNVERIFIED Camera Module 3 PCB thickness (not published, HARDWARE_AUDIT B9)
    for w in sorted(cam, key=lambda w: (round(w["p0"][1], 1), round(w["p0"][2], 1))):
        hx = np.linalg.inv(Th)
        a0, a1 = (hx @ np.r_[w["p0"], 1])[:3], (hx @ np.r_[w["p1"], 1])[:3]
        entry, bottom = (w["p0"], w["p1"]) if a0[0] < a1[0] else (w["p1"], w["p0"])   # PCB on the inner (smaller x) face
        axis = (bottom - entry) / np.linalg.norm(bottom - entry)
        seat = entry - axis * pcb
        add(dict(source="camera", part="camera PCB (not in CAD)", part_inst=None, into="head", into_inst=head_k,
                 link="head_assembly", anchor="plastic pilot 1.65 (camera)", near=pcb, far=pcb + w["L"], seat_pt=seat, axis=axis,
                 clr=2.2, clr_len=pcb, seat_type="camera PCB back face (PCB %.1f mm assumed, UNVERIFIED)" % pcb, recess=None,
                 notes=["Camera Module 3 holes 2.2 mm on 21 x 12.5 (HARDWARE_AUDIT B9); PCB thickness UNVERIFIED"]))
    sg = [k for k, i in enumerate(inst) if i["name"] == "sg90"]
    for k in sg:
        tabs = [w for w in W if w["i"] == k and abs(w["d"] - 2.0) < 0.1]
        for w in tabs:
            c = (w["p0"] + w["p1"]) / 2
            pil = min((x for x in W if x["i"] == head_k and 1.5 <= x["d"] <= 1.6 and 3.5 <= x["L"] <= 4.0),
                      key=lambda x: np.linalg.norm((x["p0"] + x["p1"]) / 2 - c))
            pc = (pil["p0"] + pil["p1"]) / 2
            ax_t = w["ax"] if np.dot(pc - c, w["ax"]) > 0 else -w["ax"]
            seat = c - ax_t * w["L"] / 2
            ang = float(np.degrees(np.arccos(min(1.0, abs(np.dot(ax_t, pil["ax"]))))))
            p_entry = min((pil["p0"], pil["p1"]), key=lambda p: np.dot(p - seat, ax_t))
            p_end = max((pil["p0"], pil["p1"]), key=lambda p: np.dot(p - seat, ax_t))
            add(dict(source="sg90_tab", part="SG90 tab", part_inst=k, into="head", into_inst=head_k, link="head_assembly",
                     pilot_pt=pc, pilot_ax=pil["ax"],
                     anchor="plastic pilot 1.55 (SG90 tab)", near=round(float(np.dot(p_entry - seat, ax_t)), 2),
                     far=round(float(np.dot(p_end - seat, ax_t)), 2), seat_pt=seat, axis=ax_t, clr=2.0, clr_len=w["L"],
                     seat_type="SG90 tab top face", recess=None, pilot_angle_deg=round(ang, 1),
                     notes=["SG90 bag screw (BOM 14), size not published; head pilot axis is %.1f deg off the SG90 tab axis in the CAD" % ang]))

    # speaker_interface to speaker_stand: 4 clearance holes 2.7 mm on a 32 x 32 mm square over the 4 side pilots
    # 2.12 mm of the stand (same square, same 20.7 deg tilted face; the pilots are drilled along y)
    k_si = [k for k, i in enumerate(inst) if i["key"] == "speaker_interface"][0]
    k_st = [k for k, i in enumerate(inst) if i["key"] == "speaker_stand"][0]
    for w in [w for w in W if w["i"] == k_si and 2.6 <= w["d"] <= 2.8]:
        c = (w["p0"] + w["p1"]) / 2
        pil = min((x for x in W if x["i"] == k_st and 2.05 <= x["d"] <= 2.2 and abs(x["ax"][1]) > 0.99),
                  key=lambda x: np.linalg.norm((x["p0"] + x["p1"]) / 2 - c))
        pc = (pil["p0"] + pil["p1"]) / 2
        ax_t = w["ax"] if np.dot(pc - c, w["ax"]) > 0 else -w["ax"]
        seat = c - ax_t * w["L"] / 2
        ang = float(np.degrees(np.arccos(min(1.0, abs(np.dot(ax_t, pil["ax"]))))))
        p_entry = min((pil["p0"], pil["p1"]), key=lambda p: np.dot(p - seat, ax_t))
        p_end = max((pil["p0"], pil["p1"]), key=lambda p: np.dot(p - seat, ax_t))
        off = np.linalg.norm((pc - seat) - np.dot(pc - seat, ax_t) * ax_t)
        add(dict(source="cad_row", part="speaker_interface", part_inst=k_si, into="speaker_stand", into_inst=k_st,
                 pilot_pt=pc, pilot_ax=pil["ax"],
                 link="head_assembly", anchor="plastic pilot 2.12 (speaker stand)", near=round(float(np.dot(p_entry - seat, ax_t)), 2),
                 far=round(float(np.dot(p_end - seat, ax_t)), 2), seat_pt=seat, axis=ax_t, clr=w["d"], clr_len=round(w["L"], 2),
                 seat_type="flat face", recess=None, pilot_angle_deg=round(ang, 1), anchor_d=pil["d"], offset=round(float(off), 2),
                 notes=["found here, not in audit/screws2.py or MOUNTING.md (B8 says no screw): pilot axis %.1f deg off the "
                        "clearance hole axis, pilot centre %.2f mm off it" % (ang, off)]))

    # ------------------------------------------------------------------------------------------ 5. inserts
    printed = {k for k, i in enumerate(inst) if i["printed"]}
    ins = [w for w in W if w["i"] in printed and 3.8 <= w["d"] <= 4.3 and 5.0 <= w["L"] <= 8.0]
    insert_recs = []
    for w in ins:
        c = (w["p0"] + w["p1"]) / 2
        # the screw that ends in this bore
        best_s, bd = None, 1e9
        for f in F:
            if f.get("anchor") != "M3 insert" or f["into_inst"] != w["i"]:
                continue
            p = f["seat_pt"] + f["axis"] * (f["near"] + f["far"]) / 2
            dd = np.linalg.norm(p - c)
            if dd < bd:
                best_s, bd = f, dd
        entry = min((w["p0"], w["p1"]), key=lambda p: np.dot(p - best_s["seat_pt"], best_s["axis"])) if best_s and bd < 2 else w["p0"]
        axis = best_s["axis"] if best_s and bd < 2 else w["ax"]
        insert_recs.append(dict(source="insert", part="M3 heat-set insert", into=inst[w["i"]]["key"], into_inst=w["i"],
                                link=inst[w["i"]]["link"], anchor="heat-set into a 4.0 mm bore", seat_pt=entry, axis=axis,
                                bore_d=w["d"], bore_len=round(w["L"], 2), screw=best_s["id"] if best_s and bd < 2 else None,
                                notes=[]))
    print("inserts: %d bores, %d with a screw" % (len(insert_recs), sum(1 for x in insert_recs if x["screw"])))

    # ------------------------------------------------------------------------------------------ 6. specs, lengths, checks
    for f in F:
        src, anc = f["source"], f["anchor"]
        f["notes"] = list(f.get("notes", []))
        part_printed = f.get("part_inst") is not None and inst[f["part_inst"]]["printed"]
        if src == "cad_row":
            if anc == "M3 insert":
                kind, size, head = "insert", "M3", "M3_din912"
            elif anc.startswith("horn"):
                kind, size, head = "horn", "M3", "M3_din912"
            elif anc == "servo pilot":
                kind, size, head = "servo", "M2", "M2_pan_selftap"
            elif anc == "plastic pilot 2.0":
                kind, size, head = "pla", "M2.5", "M2.5_din912"
            elif anc == "plastic pilot (eye)":
                kind, size, head = "eye", "M2.5", "M2.5_din912"
            elif anc == "plastic pilot 2.12 (speaker stand)":
                kind, size, head = "pla", "M2.5", "M2.5_din912"
            elif anc == "NONE":
                kind, size, head = "sg90_horn", "SG90", "SG90_screw"
            else:
                raise ValueError(anc)
            dk, k = HEAD[head]
            near, far = f["near"], f["far"]
            seat = f["seat_pt"]
            # head too big for its recess: it sits on the part face, the whole window shifts by the recess depth
            if f["recess"] and size in KNURL and f["recess"]["d"] < dk - 1e-6:
                shift = f["recess"]["depth"]
                f["notes"].append("head d %.1f does not fit the %.2f recess: it sits on the part face, %.1f mm higher" % (
                    dk, f["recess"]["d"], shift))
                seat = seat - f["axis"] * shift
                f["seat_pt"] = seat
                near, far = near + shift, far + shift
                f["near"], f["far"], f["head_proud_of_recess"] = round(near, 2), round(far, 2), True
            core = {"M3": 1.2, "M2.5": 0.9, "M2": 0.7, "SG90": 0.7}[size]
            if f.get("anchor_d"):
                core = min(core, 0.4 * f["anchor_d"])
            stop = stop_distance(S, seat, f["axis"], core)
            f["stop"] = round(stop, 2)
            f["size"], f["head_key"], f["head_dk"], f["head_k"] = size, head, dk, k
            if kind == "sg90_horn":
                # the 5.05 x 3.0 'recess' is the pocket that fits over the SG90 output spline: the screw comes from the
                # flat outer face, through the 2.0 mm plate, into the spline (ray cast: the SG90 sits on the pocket side)
                f["seat_pt"] = seat = seat + f["axis"] * f["clr_len"]
                f["axis"] = -f["axis"]
                f["seat_type"] = "flat outer face of the antenna holder (the 5.05 recess is the spline pocket)"
                f["recess"] = None
                stop = stop_distance(S, seat, f["axis"], 0.7)
                f["stop"] = round(stop, 2)
                f.update(anchor="SG90 output shaft (not modelled)", into="SG90 output shaft", near=round(stop, 2), far=None,
                         L=None, spec="SG90 bag horn screw", supply="SG90 bag (BOM 14)", line="14", status="UNVERIFIED",
                         color_key="SG90 bag")
                f["notes"].append("NONE anchor resolved: the hole is on the antenna joint axis (0.04 mm); the screw goes from "
                                  "the outer face through the holder into the SG90 output shaft, which sg90.stl does not model; "
                                  "first solid surface %.1f mm below the seat" % stop)
                f["notes"].append("size not published " + SRC["sg90"])
                continue
            flush = far if (kind == "eye" or f.get("pilot_angle_deg")) else None   # tilted pilots: rays miss the floor
            ch = pick_length(kind, size, near, far, stop, flush_max=flush)
            f.update(L=ch["L"], e=ch["e"], e_min=ch["e_min"], rule=ch["rule"], len_status=ch["status"], tip_gap=ch["tip_gap"],
                     lmin=ch["lmin"], lmax=ch["lmax"])
            if kind == "eye":
                # blind 3.0 mm pilot with a 1.5 mm front skin: the longest stock that does not bottom is M2.5x6 (1.0 mm of
                # thread). M2.5x8 reaches the pilot floor exactly; two 0.3 mm washers under the head (0.6 mm, the stocked
                # BOM 17l part, DECISIONS.md D21 note) leave 0.6 mm and 2.4 mm of thread.
                w = 0.6
                f.update(L=8, washer=dict(t=w, n=2, t_each=0.3, spec="%s" % WASHER_SPEC),
                         e=round(min(8 - w, far) - near, 2), tip_gap=round(stop - (8 - w), 2), len_status="BELOW RULE",
                         notes=f["notes"] + ["eye pilot is blind (3.0 mm deep, 1.5 mm front skin, ray cast): M2.5x8 alone "
                                             "reaches the floor (0.0 mm); with two 0.3 mm washers (0.6 mm): 2.4 mm of thread, 0.6 mm to the floor"])
                ch["L"], ch["line"] = 8, STOCK["M2.5"][8]
            if kind == "servo":
                f["spec"] = "M2x%d self-tapping pan head" % ch["L"]
                if ch["L"] == 6:
                    f.update(supply="servo bag (BOM 1): the M2x6 'smallest screws' " + SRC["so101"] + "; bag split UNVERIFIED (B2)",
                             line="1", color_key="M2 servo bag")
                else:
                    f.update(supply="METALLIXITY M2 kit (BOM 17h)", line="17h", color_key="M2 kit")
            else:
                f["spec"] = "%sx%d DIN 912 A2" % (size, ch["L"]) + (" + 2 x 0.3 mm washers" if f.get("washer") else "")
                f["line"] = ch["line"]
                f["supply"] = ("BOM %s" % ch["line"]) if ch["line"] else "NEW LENGTH (no BOM line)"
                f["color_key"] = "%sx%d" % (size, ch["L"])
            # clearance hole
            if f["clr"] is not None:
                st, mg = clearance_status(f["clr"], {"M3": 3.0, "M2.5": 2.5, "M2": 2.0}[size], part_printed)
                f["clearance"] = dict(hole=f["clr"], margin=mg, status=st)
            if f["recess"] and not f.get("head_proud_of_recess"):
                dkk = KNURL.get(size, dk) if head.endswith("din912") else dk
                m = f["recess"]["d"] - dkk
                f["recess_check"] = dict(recess=f["recess"]["d"], head=dkk, margin=round(m, 2),
                                         status="OK" if m >= 0.3 else ("TIGHT" if m >= 0 else "INTERFERENCE"),
                                         proud=round(k - f["recess"]["depth"], 2))
        elif src == "servo_case":
            f.update(size="M2", spec="PA2.0 self-tapping (factory)", L=None, draw_L=round(f["near"] + 3.8, 1),
                     head_key="M2_case_factory", head_dk=HEAD["M2_case_factory"][0], head_k=HEAD["M2_case_factory"][1],
                     supply="comes with servo (BOM 1), factory fitted", line="1", color_key="M2 case (factory)",
                     status="FACTORY", stop=None)
        elif src == "horn_centre":
            f.update(size="M3", spec="M3x6 machine screw (Feetech rocker screw)", L=6, head_key="M3_horn_centre",
                     head_dk=HEAD["M3_horn_centre"][0], head_k=HEAD["M3_horn_centre"][1],
                     supply="comes with servo (BOM 1) " + SRC["feetech_ds"], line="1", color_key="M3 horn centre", status="OK")
            f["notes"].append("Loctite 243: metal to metal " + SRC["guide"])
        elif src == "idle_boss":
            f.update(size="PA3.0", spec="PA3.0x5 self-tapping, washer head (Feetech idle screw)", L=5,
                     head_key="PA3_idle", head_dk=HEAD["PA3_idle"][0], head_k=HEAD["PA3_idle"][1],
                     supply="comes with servo (BOM 1) " + SRC["feetech_ds"], line="1", color_key="PA3 idle",
                     status="FIT" if f["install"] else "NOT FITTED")
        elif src == "camera":
            stop = stop_distance(S, f["seat_pt"], f["axis"], 0.6)
            ch = pick_length("pla_m2", "M2", f["near"], f["far"], stop)
            f.update(size="M2", stop=round(stop, 2), L=ch["L"], e=ch["e"], e_min=ch["e_min"], len_status=ch["status"],
                     tip_gap=ch["tip_gap"], rule=ch["rule"], lmin=ch["lmin"], lmax=ch["lmax"],
                     spec="M2x%d self-tapping pan head" % ch["L"], supply="METALLIXITY M2 kit (BOM 17h)", line="17h",
                     head_key="M2_pan_selftap", head_dk=HEAD["M2_pan_selftap"][0], head_k=HEAD["M2_pan_selftap"][1],
                     color_key="M2 kit")
        elif src == "sg90_tab":
            stop = stop_distance(S, f["seat_pt"], f["axis"], 0.6)
            f.update(size="SG90", stop=round(stop, 2), L=None, spec="SG90 bag mounting screw", supply="SG90 bag (BOM 14)",
                     line="14", head_key="SG90_screw", head_dk=HEAD["SG90_screw"][0], head_k=HEAD["SG90_screw"][1],
                     color_key="SG90 bag", status="UNVERIFIED")
    # D18: outer hip roll screw left out. Marked by sweep_fasteners.py from the measured hit; here: roll_motor_bottom rows
    for f in F:
        f["group"] = schedule_group(f, inst)
        f["viewer_sub"] = LINK_SUB.get(f["link"], "trunk")
    for x in insert_recs:
        x["group"] = schedule_group(x, inst)
        x["viewer_sub"] = LINK_SUB.get(x["link"], "trunk")
    print("records: %d fasteners + %d inserts, %.0f s" % (len(F), len(insert_recs), time.time() - t0))
    return dict(S=S, sites=sites, rows=rows, raw=raw, groups=groups, F=F, inserts=insert_recs, dropped=dropped,
                added_horn=added_horn, n_hex=n_hex, W=W)


ELEC = {"raspberrypizerow", "board", "bno055", "usb_c_charger", "camera PCB (not in CAD)"}
LEFT = {"left_roll_to_pitch_assembly", "knee_and_ankle_assembly", "knee_and_ankle_assembly_2", "foot_assembly"}
RIGHT = {"right_roll_to_pitch_assembly", "knee_and_ankle_assembly_3", "knee_and_ankle_assembly_4", "foot_assembly_2"}
NECK = {"neck_pitch_assembly", "head_pitch_to_yaw", "neck_yaw_assembly"}
HEADL = {"head_assembly", "left_antenna_holder", "right_antenna_holder"}


def schedule_group(f, inst):
    if f.get("part") in ELEC:
        return "electronics"
    ln = f["link"]
    if f.get("source") == "servo_case" or f.get("source") in ("horn_centre", "idle_boss"):
        # servo hardware goes with the servo's joint side
        j = f.get("servo", "")
        if j.startswith("left_") and j not in ("left_hip_yaw", "left_hip_roll"):
            return "left_leg"
        if j.startswith("right_") and j not in ("right_hip_yaw", "right_hip_roll"):
            return "right_leg"
        if j in ("neck_pitch", "head_pitch", "head_yaw"):
            return "neck"
        if j == "head_roll":
            return "head"
        return "trunk_hips"
    if ln in LEFT:
        return "left_leg"
    if ln in RIGHT:
        return "right_leg"
    if ln in NECK:
        return "neck"
    if ln in HEADL:
        return "head"
    return "trunk_hips"


# ---------------------------------------------------------------------------------------------- outputs
def site_of_features(sites):
    m = {}
    for si, s in enumerate(sites):
        for w in s["feat"]:
            m[(w["i"], tuple(np.round(w["p0"], 2)), tuple(np.round(w["p1"], 2)))] = si
    return m


def hole_ledger(R):
    """Every hole stack: which fastener uses it, or why it stays empty."""
    S, sites, F, ins = R["S"], R["sites"], R["F"], R["inserts"]
    inst = S.inst
    fmap = site_of_features(sites)
    used = defaultdict(list)
    for f in F:
        if f.get("site") is not None:
            used[f["site"]].append(f["id"])
    # special groups: find the site through the anchor feature nearest the screw axis
    for f in F:
        if f.get("site") is not None:
            continue
        p = f["seat_pt"] + f["axis"] * 2.0
        best, bd = None, 1e9
        want = {f.get("part_inst"), f.get("into_inst")} - {None}
        for si, s in enumerate(sites):
            o, ax = np.array(s["o"]), np.array(s["ax"])
            if abs(abs(np.dot(ax, f["axis"])) - 1) > 0.02 or not (want & {x[5] for x in s["segs"]}):
                continue
            v = p - o
            dd = np.linalg.norm(v - np.dot(v, ax) * ax)
            if dd < bd:
                best, bd = si, dd
        if best is not None and bd < 0.6:
            f["site"] = best
            used[best].append(f["id"])
    for f in F:   # pilots drilled off the clearance axis (20.7 deg): their own stack is used too
        if f.get("pilot_pt") is None:
            continue
        for si, s in enumerate(sites):
            o, ax = np.array(s["o"]), np.array(s["ax"])
            v = np.asarray(f["pilot_pt"]) - o
            if abs(abs(np.dot(ax, f["pilot_ax"])) - 1) < 0.02 and np.linalg.norm(v - np.dot(v, ax) * ax) < 0.6:
                used[si].append(f["id"])
                f["pilot_site"] = si
    for x in ins:
        p = np.asarray(x["seat_pt"]) + np.asarray(x["axis"]) * 1.0
        for si, s in enumerate(sites):
            o, ax = np.array(s["o"]), np.array(s["ax"])
            v = p - o
            if abs(abs(np.dot(ax, x["axis"])) - 1) < 0.02 and np.linalg.norm(v - np.dot(v, ax) * ax) < 0.6:
                used[si].append("insert")
                x["site"] = si
                break
    out = []
    for si, s in enumerate(sites):
        names = [(x[2], x[4], round(x[1] - x[0], 1), inst[x[5]]["key"]) for x in s["segs"]]
        if si in used:
            continue
        keys = {n[3] for n in names}
        ds = [n[1] for n in names]
        if any(k == "roll_bearing" for k in keys) or any(d > 30 for d in ds):
            why = "bearing seat (6804, BOM 18)"
        elif keys <= {"board", "raspberrypizerow", "bno055"} and max(ds) < 1.6:
            why = "PCB pad or via hole, not a fastener hole"
        elif keys <= {SERVO_TOP, SERVO_BOT} and all(abs(d - 1.67) < 0.05 or abs(d - 2.0) < 0.05 for d in ds):
            why = "STS3215 mounting pilot with nothing mounted on it (servo face is free here)"
        elif any(abs(d - 7.0) < 0.1 for d in ds) and ("drive_palonier" in keys or "passive_palonier" in keys):
            why = "screwdriver access hole over a horn centre"
        elif keys == {"sg90"}:
            why = "SG90 tab hole (screw recorded as an SG90 tab screw; the head pilot is 20.7 deg off this axis so it is a separate stack)"
        elif keys <= {"left_antenna_holder", "right_antenna_holder"} and all(abs(d - 1.8) < 0.1 for d in ds):
            why = "antenna rod holes (antenna.stl, no BOM line, no fastener)"
        elif keys == {"power_switch"}:
            why = "panel switch screw holes: the switch is held by the body_back cutout (MOUNTING.md)"
        elif keys == {"usb_c_charger"}:
            why = "charger 2nd hole: no pilot under it (MOUNTING.md)"
        elif keys == {"head"} and all(1.5 <= d <= 1.6 for d in ds):
            why = "SG90 tab pilot in head.stl (used by the SG90 tab screws, axis 20.7 deg off the SG90 tab)"
        elif keys == {"head"} and all(2.0 <= d <= 2.1 for d in ds) and max(n[2] for n in names) <= 2.3:
            why = "grille or vent hole: one of the 2.06 mm through holes in the head shell, not a fastener"
        elif keys == {"board"}:
            why = "board.stl copy in the head: print/head.stl (730c14b) has no pilots under it (the older URDF head mesh did); nothing is fitted here"
        elif "bulb" in keys and any(d > 20 for d in ds):
            why = "eye light path (bulb, head wall and eye glass seat), not a fastener"
        elif keys == {"head"} and any(7.0 < d < 8.0 for d in ds):
            why = "camera lens opening in the head front wall"
        elif keys == {"flash_light_module"}:
            why = "UNUSED: flash_light_module screw hole (2.79 clearance, 5.67 counterbore) with no pilot in head.stl or the reflector: the projector is not screwed in the CAD (B8)"
        elif keys == {"speaker_stand"} and all(2.0 <= d <= 2.15 for d in ds) and any(abs(n[2] - 5.0) < 0.1 for n in names):
            why = "UNUSED: speaker_stand top pilot 2.05 x 5.0 (2 in the stand, 12.75 mm apart); no part in the CAD or the BOM uses them"
        elif keys == {"speaker_interface"} and any(d > 15 for d in ds):
            why = "speaker opening in speaker_interface, not a fastener"
        elif keys == {"leg_spacer"} and all(abs(d - 6.0) < 0.1 for d in ds):
            why = "UNUSED: 6.0 x 4.8 mm hole across leg_spacer (2 per spacer), no part screws into it (cable or lightening hole)"
        elif keys <= {"head_bot_sheet"}:
            why = "UNUSED: head_bot_sheet through hole (cable pass-through), not a fastener"
        else:
            why = "UNUSED: no part in the CAD or the BOM screws into this hole"
        out.append(dict(site=si, why=why, holes=[dict(part=n[3], d=n[1], len=n[2]) for n in names],
                        at=np.round(np.array(s["o"]), 1).tolist(), axis=np.round(np.array(s["ax"]), 3).tolist()))
    return out


def bom_compare(F, ins):
    bl = bom_lines()
    need = Counter()
    for f in F:
        if f.get("status") in ("NOT FITTED",) or f.get("leave_out"):
            continue
        ln = f.get("line")
        if ln and ln not in ("1", "14"):
            need[(ln, f["spec"].split(" + ")[0])] += 1
        if f.get("washer"):
            need[("17l", "M2.5 washer 0.3 mm")] += f["washer"].get("n", 1)
    need[("16", "M3 heat-set insert")] = len(ins)
    rows = []
    by_line = defaultdict(int)
    for (ln, spec), n in need.items():
        by_line[ln] += n
    for ln in sorted(set(list(by_line) + [k for k in bl if k.startswith("17") or k == "16"])):
        b = bl.get(ln, {})
        bn = b.get("need")
        try:
            bn_i = int(re.match(r"\d+", bn).group(0)) if bn else None
        except Exception:
            bn_i = None
        specs = sorted({spec for (l2, spec) in need if l2 == ln})
        rows.append(dict(line=ln, item=b.get("item", "(new line)"), bom_need=bn_i, bom_buy=b.get("buy"), count=by_line.get(ln, 0),
                         specs=specs, match=(bn_i == by_line.get(ln, 0))))
    return rows


def ser(v):
    if isinstance(v, np.ndarray):
        return [round(float(x), 3) for x in v.ravel()] if v.ndim == 1 else [[round(float(x), 4) for x in r] for r in v]
    if isinstance(v, (np.floating,)):
        return None if not np.isfinite(v) else round(float(v), 3)
    if isinstance(v, float):
        return None if not np.isfinite(v) else round(v, 3)
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, dict):
        return {k: ser(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [ser(x) for x in v]
    return v


def records_for_json(R):
    S = R["S"]
    out = []
    for f in R["F"] + R["inserts"]:
        is_ins = f["source"] == "insert"
        Ml, sl, al = link_pose(S, f["link"], np.asarray(f["seat_pt"], float), np.asarray(f["axis"], float))
        if is_ins:
            geo = dict(d=4.6, L=INSERT_L, head=None)
            spec, color_key = "M3 heat-set insert CNC Kitchen M3 x 5.7", "M3 insert"
        else:
            Ld = f.get("L") or f.get("draw_L") or (f.get("near") or 0) + 4.0
            d = {"M3": 3.0, "M2.5": 2.5, "M2": 2.0, "PA3.0": 3.0, "SG90": 2.0}.get(f.get("size"), 2.0)
            geo = dict(d=d, L=round(float(Ld), 2), head=dict(type=f.get("head_key"), dk=f.get("head_dk"), k=f.get("head_k")))
            spec, color_key = f.get("spec"), f.get("color_key", "other")
        rec = dict(id=f.get("id") or "I%02d" % (len([x for x in out if x["kind"] == "insert"]) + 1),
                   kind="insert" if is_ins else "screw", source=f["source"], spec=spec, size=f.get("size", "M3"),
                   d=geo["d"], length_mm=f.get("L") if not is_ins else INSERT_L, draw_length_mm=geo["L"], head=geo["head"],
                   color_key=color_key, color=COLORS.get(color_key, COLORS["other"]),
                   link=f["link"], viewer_sub=f["viewer_sub"], group=f["group"],
                   seat_world=ser(np.asarray(f["seat_pt"], float)), axis_world=ser(np.asarray(f["axis"], float)),
                   seat_link=ser(sl), axis_link=ser(al), pose_link=ser(Ml),
                   part=f.get("part"), part_inst=f.get("part_inst"), into=f.get("into"), into_inst=f.get("into_inst"),
                   anchor=f.get("anchor"), servo=f.get("servo"), site=f.get("site"))
        for k in ("near", "far", "stop", "e", "e_min", "lmin", "lmax", "tip_gap", "len_status", "rule", "clearance",
                  "recess_check", "offset", "supply", "line", "status", "washer", "install", "pilot_angle_deg",
                  "seat_type", "clr", "head_proud_of_recess", "bore_d", "bore_len", "screw"):
            if k in f and f[k] is not None:
                rec[k] = ser(f[k])
        rec["notes"] = f.get("notes", [])
        out.append(rec)
    return out


def write_csv(path, recs):
    cols = ["id", "kind", "group", "link", "spec", "size", "length_mm", "head_dk", "head_k", "part", "into", "anchor",
            "near", "far", "stop", "e", "e_min", "len_status", "clearance", "recess", "supply", "line", "status",
            "sweep", "seat_world", "axis_world", "seat_link", "axis_link", "notes"]
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for r in recs:
            h = r.get("head") or {}
            cl = r.get("clearance") or {}
            rc = r.get("recess_check") or {}
            sw = r.get("sweep") or {}
            w.writerow([r["id"], r["kind"], r["group"], r["link"], r["spec"], r["size"], r.get("length_mm"), h.get("dk"), h.get("k"),
                        r.get("part"), r.get("into"), r.get("anchor"), r.get("near"), r.get("far"), r.get("stop"), r.get("e"),
                        r.get("e_min"), r.get("len_status"), "%s %s" % (cl.get("status", ""), cl.get("margin", "")) if cl else "",
                        "%s %s" % (rc.get("status", ""), rc.get("margin", "")) if rc else "", r.get("supply"), r.get("line"),
                        r.get("status"), sw.get("worst_text", ""), " ".join("%.2f" % x for x in r["seat_world"]),
                        " ".join("%.3f" % x for x in r["axis_world"]), " ".join("%.2f" % x for x in r["seat_link"]),
                        " ".join("%.3f" % x for x in r["axis_link"]), " | ".join(r.get("notes", []))])


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--scratch", default=os.environ.get("ODM_FASTENER_SCRATCH"), help="cache folder outside the repo")
    ap.add_argument("--out", default=HERE)
    a = ap.parse_args()
    if not a.scratch:
        sys.exit("give --scratch or ODM_FASTENER_SCRATCH (outside the repo)")
    scratch = os.path.abspath(a.scratch)
    if os.path.commonpath([scratch, REPO]) == REPO:
        sys.exit("scratch must be outside the repo")
    R = build(scratch)
    ledger = hole_ledger(R)
    recs = records_for_json(R)
    bom = bom_compare(R["F"], R["inserts"])
    S = R["S"]
    meta = dict(
        generated_by="altaay_lab/fasteners/make_fasteners.py", units="mm",
        frame="URDF world at zero joint angles (x forward, y left, z up); *_link fields are in the URDF link frame "
              "of `link` at zero pose; pose_link is a 4x4 (row-major) whose +z is the screw axis pointing into the "
              "joint and whose origin is the head seat (the underside of the head)",
        sources=SRC, margin_mm=MARGIN, stock=STOCK, head_models=HEAD, colors=COLORS,
        scene=dict(instances=len(S.inst), urdf_instances=S.n_urdf, assembly_json_match=S.assembly_match,
                   hole_features=len(R["W"]), hex_features=R["n_hex"], sites=len(R["sites"]),
                   print_vs_urdf="head.stl and left/right_roll_to_pitch.stl in print/ differ from the URDF meshes "
                                 "(up to 5.0 and 1.18 mm); holes here come from the print/ STLs"),
        merged_rows=R["dropped"], added_horn_screws=len(R["added_horn"]),
        servos=[dict(joint=g["joint"], link=g["link"]) for g in R["groups"]])
    out = dict(meta=meta, fasteners=recs, empty_holes=ledger, bom=bom)
    js = os.path.join(a.out, "fasteners.json")
    with open(js, "w") as fh:
        json.dump(out, fh, separators=(",", ":"))
    write_csv(os.path.join(a.out, "fasteners.csv"), recs)
    print("wrote %s (%.0f kB): %d records (%d screws, %d inserts), %d empty hole stacks" % (
        js, os.path.getsize(js) / 1e3, len(recs), sum(1 for r in recs if r["kind"] == "screw"),
        sum(1 for r in recs if r["kind"] == "insert"), len(ledger)))
    for b in bom:
        print("  BOM %-4s %-28s need %-5s counted %-4d %s %s" % (b["line"], b["item"][:28], b["bom_need"], b["count"],
                                                            "OK" if b["match"] else "MISMATCH", ", ".join(b["specs"])))
    print("empty holes by reason:", dict(Counter(x["why"].split(":")[0][:60] for x in ledger)))


if __name__ == "__main__":
    main()
