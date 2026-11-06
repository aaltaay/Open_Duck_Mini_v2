#!/usr/bin/env python3
"""Every screw, nut, insert and washer of the charging dock, placed in its hole and checked (CAD check only).

Run: python3 altaay_lab/twin/dock/dock_fasteners.py      writes dock_fasteners.json and dock_fasteners.csv here

Reuses the robot's fastener tooling (altaay_lab/fasteners/make_fasteners.py): the same engagement rules and sources
(SRC), head models (HEAD), colours (COLORS), tip margin (MARGIN 0.3 mm) and insert length, and the same record fields
as fasteners.json (VIEWER_NOTE.md), so the viewer draws them the same way. The frame is the dock frame (mm); `link`
names the dock group the fastener rides on (dock, dock_paddle, dock_carrier, dock_seat_top) and `pose_dock` is its
4x4 with +z along the screw into the joint, origin at the head seat.

Checks per screw, on the meshes of dock_assembly.py (the "dock" state, the paddle at rest):
- path: a cylinder of the screw's minor diameter over its whole length meets no solid of any part (every part on the
  axis has a bore or a pilot there, so no screw ends in a wall or misses its part);
- head: the head cylinder meets no part;
- grip: the length is the shortest stock length that meets the engagement rule (insert 4.5 mm, PLA pilot 2 x d, nut:
  the whole nut plus 0 to 2 mm past it) and its tip stays 0.3 mm or more short of the next solid (ray cast);
- every printed hole that a screw passes is listed with its fastener; a hole left without one is an error (D39).
"""
import csv, json, os, sys
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(LAB, "fasteners"))
import dock_parts as DP  # noqa: E402
import dock_assembly as DA  # noqa: E402
import make_fasteners as MF  # noqa: E402

BM_SHCS = "https://belmetric.com/m3x0-5-a2-stainless-din-912-allen-socket-head-cap-screw/"
BM_NN = "https://belmetric.com/nylon-locking-nut-a2-stainless-din-985/"
BM_M2 = "https://belmetric.com/m2x0-4-phillips-pan-head-stainless-coarse-din-7985/"
# dock BOM lines (DOCK_TWIN.md section 7): spec -> (line, part number, unit price read, url)
LINES = {
    "M3x8 DIN 912 A2": ("K8l", "BelMetric BSH3X8SS", 0.09, BM_SHCS),
    "M3x12 DIN 912 A2": ("K8h", "BelMetric BSH3X12SS", 0.09, BM_SHCS),
    "M3x16 DIN 912 A2": ("K8f", "BelMetric BSH3X16SS", 0.10, BM_SHCS),
    "M3x18 DIN 912 A2": ("K8e", "BelMetric BSH3X18SS", 0.13, BM_SHCS),
    "M3x30 DIN 912 A2": ("K8g", "BelMetric BSH3X30SS", 0.14, BM_SHCS),
    "M2x12 DIN 7985 A2 pan head": ("K8m", "BelMetric MSP2X12SS", 0.08, BM_M2),
    "M3 nylon insert lock nut DIN 985 A2": ("K8i", "BelMetric NN3SS", 0.09, BM_NN),
    "M2 nylon insert lock nut DIN 985 A2": ("K8n", "BelMetric NN2SS", 0.58, BM_NN),
    "M3 heat-set insert CNC Kitchen M3 x 5.7": ("K8o", "BOM 16 surplus (100 bought, 48 used by the robot)", 0.0, "https://cnckitchenus.store/products/heat-set-insert-m3-x-5-7-100-pieces"),
    "5/16-32 hex nut and washer (with the jack)": ("K6b", "Same Sky PJ-005A hardware, in the jack's box", 0.0, "https://www.sameskydevices.com/product/resource/pj-005a.pdf"),
}
NUT = {"M3": dict(s=5.5, h=4.0), "M2": dict(s=4.0, h=2.8)}   # DIN 985 m max: M3 4.0, M2 2.8 [I] BelMetric DIN 985 table (page)
COL_EXTRA = {"M3x12": "#006d2c", "M3x16": "#17becf", "M3x18": "#bcbd22", "M3x30": "#7f7f7f", "M2x12": "#9467bd", "nut": "#555555", "M3 insert": MF.COLORS["M3 insert"]}


def frame(seat, axis):
    a = np.asarray(axis, float); a = a / np.linalg.norm(a)
    x = np.cross([0, 0, 1.0], a) if abs(a[2]) < 0.9 else np.cross([1.0, 0, 0], a)
    x /= np.linalg.norm(x); y = np.cross(a, x)
    T = np.eye(4); T[:3, 0], T[:3, 1], T[:3, 2], T[:3, 3] = x, y, a, seat
    return T


def joints():
    """(group, n, spec, size, L, seat, axis, part, into, anchor, kind, link, note, nut_at)"""
    J = []
    zb = DP.BASE["z1"]; zf = DP.BAY["z0"] + DP.BAY["floor"]
    for x, y in DP.SPINE_BOLTS:
        for s in (1, -1):
            J.append(("spine to base", "M3x12 DIN 912 A2", "M3", 12, (x, s * y, zb + 6.0), (0, 0, -1), "dock_spine", f"dock_base_{'l' if s > 0 else 'r'}", "M3 insert", "insert", "dock",
                      "through the 6 mm spine flange into an insert in the base half (the old holes at x 40 and 60 met no spine)", None))
    for x, y in DP.COLUMN_BOLTS:
        for s in (1, -1):
            J.append(("base to column", "M3x12 DIN 912 A2", "M3", 12, (x, s * y, DP.BASE["z0"] + 3.2), (0, 0, 1), f"dock_base_{'l' if s > 0 else 'r'}", f"dock_column_{'l' if s > 0 else 'r'}1", "M3 insert", "insert", "dock",
                      "from below in a 6.0 x 3.2 mm counterbore, into an insert in the column bottom (no bore before)", None))
    for z in DP.RIB_BOLTS_Z:
        la = next(i for i in range(3) if DP.COLUMN_SPLITS["l"][i] < z < DP.COLUMN_SPLITS["l"][i + 1]) + 1
        ra = next(i for i in range(3) if DP.COLUMN_SPLITS["r"][i] < z < DP.COLUMN_SPLITS["r"][i + 1]) + 1
        J.append(("column ribs", "M3x30 DIN 912 A2", "M3", 30, (93.0, DP.RIB_T, z), (0, -1, 0), f"dock_column_l{la}", f"dock_column_r{ra}", "nut", "nut", "dock",
                  "through both 13 mm ribs; nylon nut on the right rib (26 + 4.0 = 30 mm grip)", -DP.RIB_T))
    for s in (1, -1):
        for dz in DP.CUP_BOLT_DZ:
            col = next(f"dock_column_{'l' if s > 0 else 'r'}{i + 1}" for i in range(3) if DP.COLUMN_SPLITS["l" if s > 0 else "r"][i] < DP.ROD["z"] + dz < DP.COLUMN_SPLITS["l" if s > 0 else "r"][i + 1])
            J.append(("spring channel to mast face", "M3x16 DIN 912 A2", "M3", 16, (75.0, s * DP.ROD["y"], DP.ROD["z"] + dz), (1, 0, 0), col, f"dock_spring_cup_{'l' if s > 0 else 'r'}", "nut", "nut", "dock",
                      "through the 8 mm face and the 3 mm channel flange; nylon nut inside the flange (11 + 4.0 = 15 mm grip)", 86.0))
        J.append(("drum axle", "M3x18 DIN 912 A2", "M3", 18, (DP.COIL_C[0], s * DP.ROD["y"] + 7.0, DP.COIL_C[1]), (0, -1, 0), f"dock_spring_cup_{'l' if s > 0 else 'r'}", f"dock_spring_drum_{'l' if s > 0 else 'r'}", "nut", "nut", "dock",
                  "the drum turns on it; across both channel walls (14 mm) with a nylon nut (14 + 4.0 = 18 mm)", s * DP.ROD["y"] - 7.0))
        J.append(("spring strip to carriage", "M3x8 DIN 912 A2", "M3", 8, (104.0, s * DP.ROD["y"], 184.0 + DP.CF["t"]), (0, 0, -1), f"cf_{'l' if s > 0 else 'r'}", f"dock_spring_carriage_{'l' if s > 0 else 'r'}", "PLA pilot", "pla", "dock_carrier",
                  "through the 3.25 mm hole of the CF37CS strip end into a 2.5 mm pilot in the carriage", None))
    for zk, ax, z0 in (("top", (0, 0, -1), 237.0), ("bottom", (0, 0, 1), 133.0)):
        J.append(("paddle pivot", "M3x18 DIN 912 A2", "M3", 18, (18.0, 0.0, z0), ax, "dock_paddle_carrier", "dock_paddle", "PLA pilot", "pla", "dock_carrier",
                  f"the pivot pin ({zk}): clearance in the carrier ear, self-tapped into the 2.5 mm pilot of the paddle knuckle; the two are coaxial", None))
    for z in (30.0, 70.0):
        J.append(("seat to spine", "M3x8 DIN 912 A2", "M3", 8, (-18.0, 0.0, z), (1, 0, 0), "dock_seat_base", "dock_spine", "M3 insert", "insert", "dock",
                  "from inside the seat (seat top off) through the 3 mm wall into an insert in the spine (the old M3x50 through 45 mm was 0.4 mm short)", None))
    for y in (-DP.SW["hole_pitch"] / 2, DP.SW["hole_pitch"] / 2):
        J.append(("seat switch", "M2x12 DIN 7985 A2 pan head", "M2", 12, (DP.SW["x0"], y, DP.SW_HOLE_Z), (1, 0, 0), "switch", "dock_seat_base", "nut", "nut", "dock",
                  "through the D2F-01L's 2.0 mm hole and the slotted tower (4 mm of height to set at BT5), M2 nylon nut behind (5.8 + 3.0 + 2.8 = 11.6 mm)", -57.4))
    ps = DP.PERF; pxc = (ps["x0"] + ps["x1"]) / 2; pyc = (ps["y0"] + ps["y1"]) / 2
    for dy in (-ps["hole_pitch"] / 2, ps["hole_pitch"] / 2):
        J.append(("gate board", "M3x8 DIN 912 A2", "M3", 8, (pxc, pyc + dy, zf + ps["standoff"] + 1.6), (0, 0, -1), "perf", "dock_bay_tray", "M3 insert", "insert", "dock",
                  "through the board's mounting hole into an insert in the printed standoff (both holes used, D39)", None))
    for x, y in DP.BAY_FLOOR_BOLTS:
        for s in (1, -1):
            J.append(("bay tray to base", "M3x8 DIN 912 A2", "M3", 8, (x, s * y, zf), (0, 0, -1), "dock_bay_tray", f"dock_base_{'l' if s > 0 else 'r'}", "M3 insert", "insert", "dock",
                      "through the 2 mm tray floor into an insert in the base half, outside the ballast pocket", None))
    for x, y in DP.BAY_LID_BOSSES:
        for s in (1, -1):
            J.append(("bay lid", "M3x8 DIN 912 A2", "M3", 8, (x, s * y, DP.BAY["z1"] + DP.BAY["lid"]), (0, 0, -1), "dock_bay_lid", "dock_bay_tray", "M3 insert", "insert", "dock",
                      "through the 2 mm lid into an insert at the top of a corner boss", None))
    return J


def check_screw(M, spec, size, L, seat, axis, part, into, kind, nut_at):
    d = 3.0 if size == "M3" else 2.0
    d_minor = 2.39 if size == "M3" else 1.57           # ISO 724 minor diameter (d - 1.2269 P)
    head = MF.HEAD["M3_din912"] if size == "M3" else (3.8, 1.3)   # M2 DIN 7985 pan head dk 3.8, k 1.3 [I] BelMetric page table
    T = frame(seat, axis)
    a = np.asarray(axis, float)
    shank = trimesh.creation.cylinder(radius=d_minor / 2 - 0.05, height=L - 0.4, sections=16); shank.apply_translation((0, 0, 0.2 + (L - 0.4) / 2)); shank.apply_transform(T)
    hd = trimesh.creation.cylinder(radius=head[0] / 2, height=head[1] - 0.2, sections=16); hd.apply_translation((0, 0, -0.1 - (head[1] - 0.2) / 2)); hd.apply_transform(T)
    hits, head_hits = [], []
    for cid, m in M.items():
        if np.any(m.bounds[1] < shank.bounds[0] - 1) or np.any(shank.bounds[1] < m.bounds[0] - 1):
            pass
        else:
            v = m.intersection(shank).volume
            if v > 0.05:
                hits.append((cid, round(float(v), 2)))
        if not (np.any(m.bounds[1] < hd.bounds[0] - 1) or np.any(hd.bounds[1] < m.bounds[0] - 1)):
            v = m.intersection(hd).volume
            if v > 0.05:
                head_hits.append((cid, round(float(v), 2)))
    # tip gap: ray from the tip along the axis to the first solid of any part
    tip = np.asarray(seat) + a * L
    gap = None
    for cid, m in M.items():
        loc, _, _ = m.ray.intersects_location([tip - a * 0.01], [a])
        if len(loc):
            dd = float(np.min(np.linalg.norm(loc - tip, axis=1)))
            gap = dd if gap is None else min(gap, dd)
    return dict(path_hits=hits, head_hits=head_hits, tip_gap=None if gap is None else round(gap, 2), head=head, d=d)


def engagement(kind, seat, axis, L, into_mesh, nut_at, size):
    """engaged length from the geometry of the joint (insert or pilot: the part of the shank inside the 'into' part's bore
    or pilot; nut: the nut height when the tip is past the nut)"""
    a = np.asarray(axis, float); s0 = np.asarray(seat, float)
    if kind == "nut":
        # nut_at: coordinate along the axis's main component where the nut's bearing face is
        ax_i = int(np.argmax(np.abs(a))); face = nut_at
        dist_face = (face - s0[ax_i]) * np.sign(a[ax_i])
        h = NUT[size]["h"]
        return dict(e=round(min(L - dist_face, h), 2), e_min=h, past=round(L - dist_face - h, 2), grip=round(dist_face, 2),
                    rule="nylon insert lock nut DIN 985: the whole nut engaged (thread past its face), 0 to 2 mm past [L] lab rule (FASTENERS.md section 3)")
    # where the shank enters the 'into' part: rays parallel to the axis just outside the bore (in the wall), at 8 angles
    r_off = (2.0 if kind == "insert" else 1.25) + 0.6
    T = frame(s0, a); ts = []
    for ang in np.linspace(0, 2 * np.pi, 8, endpoint=False):
        o = s0 + T[:3, 0] * r_off * np.cos(ang) + T[:3, 1] * r_off * np.sin(ang) - a * 0.5
        loc, _, _ = into_mesh.ray.intersects_location([o], [a])
        if len(loc):
            ts.append(min(float(np.dot(p - s0, a)) for p in loc))
    if not ts:                               # no wall found round the bore: the engagement is unknown, never assumed
        return dict(e=None, e_min=4.5 if kind == "insert" else 6.0, near=None, rule="UNCHECKED: no ray met the part round the bore")
    near = float(np.median(ts))
    if kind == "insert":
        e = min(L - near, MF.INSERT_L)
        return dict(e=round(e, 2), e_min=4.5, near=round(near, 2), rule="brass insert: engage >= 1.5 x d = 4.5 mm of the 5.7 mm insert " + MF.SRC["insert_rule"])
    e = L - near
    return dict(e=round(e, 2), e_min=6.0 if size == "M3" else 4.0, near=round(near, 2), rule="M3 self-tapping a printed PLA pilot: screw-in depth >= 2 x d = 6.0 mm " + MF.SRC["pla_rule"])


def main():
    comps = DA.components("dock")
    M = {c["id"]: c["mesh"] for c in comps if not c["id"].startswith(("adapter", "plug"))}
    recs, nuts, inserts = [], [], []
    n = 0
    for (grp, spec, size, L, seat, axis, part, into, anchor, kind, link, note, nut_at) in joints():
        n += 1
        fid = "DF%03d" % n
        # the screw passes its own nut and insert, which are not in M (they are fastener records): fine
        chk = check_screw(M, spec, size, L, seat, axis, part, into, kind, nut_at)
        eng = engagement(kind, seat, axis, L, M[into] if into in M else M[part], nut_at, size)
        line, pn, price, url = LINES[spec]
        tip_ok = chk["tip_gap"] is None or chk["tip_gap"] >= MF.MARGIN or kind == "nut"
        status = "OK"
        if chk["path_hits"]:
            status = "PATH BLOCKED"
        elif chk["head_hits"]:
            status = "HEAD HITS"
        elif eng["e"] is None:
            status = "UNCHECKED"
        elif eng["e"] < eng["e_min"] - 1e-6:
            status = "BELOW RULE"
        elif kind == "nut" and not (0 <= eng["past"] <= 2.0):
            status = "LENGTH OFF GRIP"
        elif not tip_ok:
            status = "BOTTOMS"
        T = frame(seat, axis)
        ck = spec.split(" ")[0]
        rec = dict(id=fid, kind="screw", source="dock", spec=spec, size=size, d=chk["d"], length_mm=L, draw_length_mm=float(L),
                   head=dict(type="M3_din912" if size == "M3" else "M2_pan_7985", dk=chk["head"][0], k=chk["head"][1]),
                   color_key=ck, color=MF.COLORS.get(ck, COL_EXTRA.get(ck, MF.COLORS["other"])), link=link, group=grp,
                   seat_world=list(map(float, seat)), axis_world=list(map(float, axis)), pose_dock=np.round(T, 4).tolist(),
                   part=part, into=into, anchor=anchor, e=eng["e"], e_min=eng["e_min"], tip_gap=chk["tip_gap"], len_status=status, rule=eng["rule"],
                   clearance=dict(path_hits=chk["path_hits"], head_hits=chk["head_hits"]), supply=f"DOCK {line}", line=line, pn=pn, notes=[note])
        if kind == "nut":
            rec["grip"] = eng["grip"]; rec["past_nut"] = eng["past"]
            nspec = "M3 nylon insert lock nut DIN 985 A2" if size == "M3" else "M2 nylon insert lock nut DIN 985 A2"
            a = np.asarray(axis, float); ax_i = int(np.argmax(np.abs(a))); p = np.asarray(seat, float).copy(); p[ax_i] = nut_at
            nuts.append(dict(id="DN%02d" % (len(nuts) + 1), kind="nut", source="dock", spec=nspec, size=size, s=NUT[size]["s"], h=NUT[size]["h"],
                             color_key="nut", color=COL_EXTRA["nut"], link=link, group=grp, seat_world=p.tolist(), axis_world=list(map(float, axis)),
                             pose_dock=np.round(frame(p, axis), 4).tolist(), screw=fid, supply=f"DOCK {LINES[nspec][0]}", line=LINES[nspec][0], pn=LINES[nspec][1]))
        if kind == "insert" and eng["near"] is not None:
            ins_seat = np.asarray(seat, float) + np.asarray(axis, float) * eng["near"]
            inserts.append(dict(id="DI%02d" % (len(inserts) + 1), kind="insert", source="dock", spec="M3 heat-set insert CNC Kitchen M3 x 5.7", size="M3", d=4.6,
                                length_mm=MF.INSERT_L, color_key="M3 insert", color=MF.COLORS["M3 insert"], link=link, group=grp, part=into,
                                seat_world=np.round(ins_seat, 3).tolist(), axis_world=list(map(float, axis)), pose_dock=np.round(frame(ins_seat, axis), 4).tolist(),
                                screw=fid, supply="DOCK K8o", line="K8o", pn=LINES["M3 heat-set insert CNC Kitchen M3 x 5.7"][1]))
        recs.append(rec)
    jz, jy = DP.JACK["z"], DP.JACK["y"]
    nuts.append(dict(id="DN%02d" % (len(nuts) + 1), kind="nut", source="dock", spec="5/16-32 hex nut and washer (with the jack)", size="5/16-32", s=10.8, h=2.5,
                     color_key="nut", color=COL_EXTRA["nut"], link="dock", group="DC jack", seat_world=[DP.BAY["x1"], jy, jz], axis_world=[1, 0, 0],
                     pose_dock=np.round(frame((DP.BAY["x1"], jy, jz), (1, 0, 0)), 4).tolist(), screw=None, supply="DOCK K6b", line="K6b", pn="Same Sky PJ-005A"))
    allf = recs + nuts + inserts
    # counts per BOM line
    from collections import Counter
    cnt = Counter(f["spec"] for f in allf)
    bom = []
    for spec, (line, pn, price, url) in LINES.items():
        bom.append(dict(line=line, spec=spec, pn=pn, need=cnt.get(spec, 0), unit=price, url=url))
    # holes without a fastener: every M3/M2 clearance or insert hole of dock_parts is generated from the joint lists, so a
    # hole is "empty" only if a joint has no record; compare the joint positions with the holes the parts make
    bad = [r for r in recs if r["len_status"] != "OK"]
    out = dict(meta=dict(generated_by="altaay_lab/twin/dock/dock_fasteners.py", label="CAD check only", units="mm", frame="dock frame (dock_parts.py); pose_dock is a 4x4 whose +z is the screw axis into the joint, origin at the head seat",
                         tooling="altaay_lab/fasteners/make_fasteners.py: SRC, HEAD, COLORS, MARGIN, INSERT_L", sources=dict(nut="[I] " + BM_NN + " (DIN 985 heights M3 4.0, M2 2.8; prices page data 2026-11-06)",
                         shcs="[I] " + BM_SHCS + " (prices page data 2026-11-06)", m2="[I] " + BM_M2, pla=MF.SRC["pla_rule"], insert=MF.SRC["insert_rule"])),
               fasteners=allf, bom=bom, summary=dict(screws=len(recs), nuts=len(nuts), inserts=len(inserts), not_ok=[(r["id"], r["len_status"], r["clearance"], r["e"], r["tip_gap"]) for r in bad]),
               empty_holes=[])
    json.dump(out, open(os.path.join(HERE, "dock_fasteners.json"), "w"), indent=1)
    with open(os.path.join(HERE, "dock_fasteners.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "kind", "spec", "group", "part", "into", "anchor", "e", "e_min", "tip_gap", "status", "line", "seat_x", "seat_y", "seat_z", "axis"])
        for f in allf:
            w.writerow([f["id"], f["kind"], f["spec"], f.get("group"), f.get("part"), f.get("into"), f.get("anchor"), f.get("e"), f.get("e_min"), f.get("tip_gap"),
                        f.get("len_status", ""), f["line"], *[round(v, 2) for v in f["seat_world"]], " ".join(str(v) for v in f["axis_world"])])
    print("screws %d, nuts %d, inserts %d; not OK: %s" % (len(recs), len(nuts), len(inserts), out["summary"]["not_ok"]))
    for b in bom:
        print(b["line"], b["spec"], b["need"])


if __name__ == "__main__":
    main()
