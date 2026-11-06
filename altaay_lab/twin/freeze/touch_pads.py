#!/usr/bin/env python3
"""touch_pads.py: touch pads and the two MPR121 boards (V1 freeze, D51; expression study 4.1). CAD check only for the
places, calc only for the capacitance.

Run: python3 altaay_lab/twin/freeze/touch_pads.py [--write]
--write writes touch_pads.json here and the board boxes tch_h and tch_b into audit/placements.json (the viewer and
cables3d read them).

Parts (sources):
  - Adafruit 1982 MPR121 STEMMA QT, $7.95, in stock [R] adafruit.com/product/1982 (read 2026-11-06 ET): I2C 0x5A, set to
    0x5B with ADDR to 3Vo [R] the Adafruit MPR121 guide, pinouts page; board 33.02 x 19.05 mm, 2 holes on one long edge
    [R] Adafruit-MPR121-PCB 'Adafruit MPR121 Breakout.brd' (the STEMMA QT revision keeps the outline, expression study:
    33.0 x 19.3 mm from the fab print); mass not published (BLOCKER, about 3 g, calc only).
  - Copper foil tape with conductive adhesive, Adafruit 1127, 25 mm x 15 m, 0.07 mm, $19.95, 22 in stock [R]
    adafruit.com/product/1127.
  - Pad rules [R] NXP AN3863 rev 4 (as read in the expression study): pad about the size of the touching hand or finger
    (3.3), spacing 2 to 3 x the cover thickness between pads (3.5), a ground ring round each pad on a battery robot whose
    ground floats (3.6), no air gap between the foil and the cover (3.7).
Places (the expression study's sites, checked again here on the V1 meshes):
  PH1 head top: inner roof of print/head.stl, centred x 10, y 0;  PH2 back of the head: inner back slope, x -45, y 0;
  PB1 back behind the neck: inner roof of body_middle_top, x -95, y 0.
  Cheeks were asked about: a symmetric patch on both side walls forward of the mic seats is searched here; see
  "cheeks" in the output for the result.
Each pad is 30 x 30 mm of foil, with a 3 mm guard ring of the same foil 3 mm outside it (42 x 42 mm in all), stuck on
the inner face. Checks per pad: every ray of a 1 mm grid over the 42 x 42 mm footprint meets the shell from inside (no
hole under the foil), the wall under it, the turn of the surface (the foil must lie down), 3 mm or more from every
other part, placed box and routed cable, and 9.6 mm or more between the guard rings of two pads.
Boards: TCHH (0x5A) on VHB 4950 on the inner roof of the head, TCHB (0x5B) on VHB under the trunk_top plate beside
the BNO055 (it taps the D2 wires at the BNO055 header, D19). A board seat is searched on the same surfaces: the
33.0 x 19.1 mm board plus 4.6 mm of parts and 1.1 mm of tape, 2 mm or more from every part and box, 8 mm or more from
any pad guard ring (the board's ground plane would load the pad), nearest to its pads.
"""
import argparse
import json
import os

import numpy as np
from scipy.spatial import cKDTree

from flib import (HERE, PLACEMENTS, scene, head_inst, inst_by_key, hits_along, surface_cloud, placements, placement_box,
                  r, dump, CABLES3D)

GAP, RING = 3.0, 3.0
EDGE = 2 * (GAP + RING)                           # the guard ring adds 12 mm to each side length of a pad
EPS0 = 8.854e-3                                   # pF/mm
ER = (2.9, 4.2)                                   # PLA, 1 to 100 MHz (Picha and Papezova 2023, via the expression study)
BOARD = (33.02, 19.05, 4.6 + 1.1)
CLR_PART, CLR_BOARD, PAD_TO_BOARD, PAD_TO_PAD = 3.0, 2.0, 8.0, 9.6
OWN_LEAD_TO_BOARD = 0.5     # past its exit, a board's own lead may be dressed against the board, not through it
SITES = {
    "PH1": dict(label="head top", link="head_assembly", shell="head", c=(10.0, 0.0), size=(30.0, 30.0), z0=200.0, d=(0, 0, 1)),
    "PH2": dict(label="back of the head", link="head_assembly", shell="head", c=(-74.0, 0.0), size=(20.0, 30.0), z0=200.0, d=(0, 0, 1)),
    "PB1": dict(label="back behind the neck", link="trunk_assembly", shell="body_middle_top", c=(-95.0, 0.0), size=(17.0, 34.0), z0=80.0, d=(0, 0, 1)),
}
BOARDS = {
    "tch_h": dict(id="TCHH", label="MPR121 touch board, head (Adafruit 1982, I2C 0x5A, BOM E9, D51)", link="head_assembly",
                  surfaces=[("head", 200.0, (0, 0, 1), ((0, np.arange(-75, 95, 2.5)), (1, np.arange(-40, 40.1, 2.5))))],
                  pads=("PH1", "PH2")),
    "tch_b": dict(id="TCHB", label="MPR121 touch board, body (Adafruit 1982, I2C 0x5B, ADDR to 3Vo, BOM E9, D51)",
                  link="trunk_assembly", pads=("PB1",), near=(-87.1, 0.0, 43.3),
                  # under the neck opening the neck swings (neck_pitch -20 to 65 deg): no board there
                  keep_out=((-80.0, -30.0, 50.0), (28.0, 30.0, 120.0)),
                  surfaces=[(sk, z0, (0, 0, dz), ((0, np.arange(-108, 12, 2.0)), (1, np.arange(-48, 48.1, 2.0))))
                            for sk, z0, dz in (("trunk_top", 30.0, 1), ("trunk_top", 100.0, -1), ("body_middle_top", 80.0, 1))]
                           + [("body_middle_top", 0.0, (0, sy, 0), ((0, np.arange(-108, 20, 2.0)), (2, np.arange(56, 100, 2.0))))
                              for sy in (1, -1)]
                           + [("body_middle_bottom", 0.0, (0, sy, 0), ((0, np.arange(-108, 30, 2.0)), (2, np.arange(-20, 50, 2.0))))
                              for sy in (1, -1)]),
}


def shell_mesh(S, key):
    if key == "head":
        return S.world_mesh(head_inst(S))
    return S.world_mesh(inst_by_key(S, key)[0])


def others(S, link, shell_key, extra_skip=()):
    out = {}
    for i in S.inst:
        if i["link"] != link or i["key"] in (shell_key,) + tuple(extra_skip):
            continue
        if link == "head_assembly" and i["key"] == "board":
            continue                                       # B7: the second board.stl copy is not a part
        m = S.world_mesh(i)
        if len(m.faces):
            out["%s[%d]" % (i["key"], i["idx"])] = cKDTree(surface_cloud(m, 30000))
    for k, p in placements().items():
        if k.startswith("tch_"):
            continue
        out["box " + k] = cKDTree(surface_cloud(placement_box(p), 6000))
    return out


def cable_trees(link):
    C = json.load(open(CABLES3D))
    out = {}
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "cables3d"))
    import c3d_lib as L
    s = L.Scene()
    for c in C["cables"]:
        P = []
        for run in c["runs"]:
            for p in run["points"]:
                if p["link"] == link:
                    P.append((s.T0[p["link"]] @ np.r_[p["p"], 1.0])[:3])
        if len(P) >= 2:
            P = np.array(P)
            dense = np.vstack([a + (b - a) * t for a, b in zip(P[:-1], P[1:]) for t in np.linspace(0, 1, 12)])
            out[c["id"]] = (cKDTree(dense), c.get("d_mm") or 2.0, dense)
    return out


OWN = {"PH1": ("D17",), "PH2": ("D18",), "PB1": ("D20",), "tch_h": ("D16", "D17", "D18"), "tch_b": ("D19", "D20", "D21", "D22")}
def cable_gaps(ctr, item, P, rule=3.0, own_free=False):
    """gap from points P (the item) to every routed cable. A lead that ends on this item is checked too, except its
    termination: from each route end inward, the stretch until the lead first stands `rule` mm off the item (the
    solder joint and the lead exit over the pad or the board); the rest of its route keeps the rule. own_free: leave
    the item's own leads out altogether (a seat search, where they would follow the seat)"""
    out = {}
    tP = cKDTree(P)
    for k, (t, dd, dense) in ctr.items():
        if k in OWN.get(item, ()):
            if own_free:
                continue
            d = tP.query(dense)[0] - dd / 2
            far = np.nonzero(d >= rule)[0]
            if not len(far):
                continue
            a, b = far[0], far[-1]
            mid = dense[a:b + 1]
            out[k] = float(tP.query(mid)[0].min() - dd / 2)
            continue
        out[k] = float(t.query(P)[0].min() - dd / 2)
    return out


def patch(shell, cx, cy, z0, d, size, step=1.0):
    """first hits from inside over a size[0] x size[1] footprint (x, y) centred at (cx, cy): points, thickness, misses"""
    d = np.array(d, float)
    P, T, miss = [], [], 0
    hx, hy = size[0] / 2, size[1] / 2
    for x in np.arange(cx - hx, cx + hx + 1e-6, step):
        for y in np.arange(cy - hy, cy + hy + 1e-6, step):
            t = hits_along(shell, [x, y, z0], d)
            t = [v for v in t if v > 0]
            if len(t) < 2:
                miss += 1
                continue
            p0 = np.array([x, y, z0]) + d * t[0]
            _, _, tri = shell.ray.intersects_location([[x, y, z0]], [d])
            loc, _, tri = shell.ray.intersects_location([[x, y, z0]], [d])
            k = int(np.argmin(np.linalg.norm(loc - p0, axis=1)))
            nn = shell.face_normals[tri[k]]
            nn = nn if nn @ d > 0 else -nn                          # outward through the wall
            tn = [v for v in hits_along(shell, p0 - nn * 0.01, nn) if v > 0.02]
            P.append(p0)
            T.append(tn[0] if tn else t[1] - t[0])
    return np.array(P), np.array(T), miss


def surface_turn(P):
    """largest angle between local plane normals over the patch (fitted on 10 x 10 mm cells)"""
    from numpy.linalg import svd
    ns = []
    for cx in np.unique(np.round(P[:, 0] / 10)):
        for cy in np.unique(np.round(P[:, 1] / 10)):
            Q = P[(np.round(P[:, 0] / 10) == cx) & (np.round(P[:, 1] / 10) == cy)]
            if len(Q) >= 12:
                n = svd(Q - Q.mean(0))[2][2]
                ns.append(n * np.sign(n[2] if abs(n[2]) > 0.1 else 1))
    ns = np.array(ns)
    if len(ns) < 2:
        return 0.0
    return float(np.degrees(np.arccos(np.clip(np.min(ns @ ns.T), -1, 1))))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    S = scene()
    trees = {lk: others(S, lk, sk) for lk, sk in (("head_assembly", "head"), ("trunk_assembly", "body_middle_top"))}
    ctrees = {lk: cable_trees(lk) for lk in ("head_assembly", "trunk_assembly")}
    J = dict(script="altaay_lab/twin/freeze/touch_pads.py", label="CAD check only (places); calc only (capacitance)",
             guard_gap_mm=GAP, guard_ring_mm=RING, guard_adds_mm=EDGE, pads={}, boards={})
    pads = {}
    for pid, s in SITES.items():
        sh = shell_mesh(S, s["shell"])
        P, T, miss = patch(sh, *s["c"], s["z0"], s["d"], (s["size"][0] + EDGE, s["size"][1] + EDGE))
        Pin, Tin, _ = patch(sh, *s["c"], s["z0"], s["d"], s["size"])
        gaps = {k: float(t.query(P)[0].min()) for k, t in trees[s["link"]].items()}
        cg = cable_gaps(ctrees[s["link"]], pid, P)
        A = len(Pin) * 1.0                                   # projected 1 mm cells
        dmed = float(np.median(Tin))
        eff = 1.0 if s["shell"] == "head" else 0.66          # 2-wall shell, 15 % infill: about 66 % (expression study)
        cap = [EPS0 * er * A / dmed * eff for er in ER]
        fing = [EPS0 * er * 200.0 / dmed * eff for er in ER]
        turn = surface_turn(P)
        worst = sorted(gaps.items(), key=lambda kv: kv[1])[:3]
        cworst = sorted(cg.items(), key=lambda kv: kv[1])[:3]
        ok = miss == 0 and worst[0][1] >= CLR_PART and (not cworst or cworst[0][1] >= CLR_PART) and turn <= 45.0
        pads[pid] = P
        J["pads"][pid] = dict(label=s["label"], link=s["link"], on=s["shell"], pad_mm=list(s["size"]),
                              footprint_with_guard_mm=[s["size"][0] + EDGE, s["size"][1] + EDGE], centre_world=np.round(P.mean(0), 2).tolist(),
                              misses_in_footprint=miss, wall_mm=[r(Tin.min()), r(dmed), r(Tin.max())],
                              surface_turn_deg=r(turn, 1), pad_area_mm2=r(A, 0),
                              palm_pF=[r(x, 2) for x in cap], two_fingertips_pF=[r(x, 2) for x in fing],
                              part_gaps_mm={k: r(v, 1) for k, v in worst}, cable_gaps_mm={k: r(v, 1) for k, v in cworst},
                              ok=bool(ok))
        print(pid, json.dumps(J["pads"][pid]))
    # spacing between the guard rings of pads on the same link
    sp = {}
    for p1 in pads:
        for p2 in pads:
            if p1 < p2 and SITES[p1]["link"] == SITES[p2]["link"]:
                sp["%s-%s" % (p1, p2)] = r(cKDTree(pads[p1]).query(pads[p2])[0].min(), 1)
    J["guard_ring_spacing_mm"] = sp
    # cheeks: a symmetric pair on the side walls, forward of the mic seats
    H = shell_mesh(S, "head")
    best = None
    rows = 0
    reasons = {"a hole or a wall outside 1.6 to 4.5 mm under the footprint": 0, "within 3 mm of a part, box or cable": 0}
    FOOT2 = (30.0 + EDGE) / 2                        # a 30 x 30 mm cheek pad with its guard
    for x in np.arange(40.0, 92.0, 4.0):
        for z in np.arange(188.0, 214.0, 4.0):
            res = []
            for sgn in (1, -1):
                Q, Tq, m = [], [], 0
                for dx in np.arange(-FOOT2, FOOT2 + 1e-6, 1.5):
                    for dz in np.arange(-FOOT2, FOOT2 + 1e-6, 1.5):
                        t = [v for v in hits_along(H, [x + dx, 0.0, z + dz], [0, sgn, 0]) if v > 0]
                        if len(t) < 2 or not (1.6 <= t[1] - t[0] <= 4.5):
                            m += 1
                            continue
                        Q.append([x + dx, sgn * t[0], z + dz])
                if m:
                    res.append(None)
                    reasons["a hole or a wall outside 1.6 to 4.5 mm under the footprint"] += 1
                    break
                Q = np.array(Q)
                g = min(float(t.query(Q)[0].min()) for t in trees["head_assembly"].values())
                cgm = min(cable_gaps(ctrees["head_assembly"], "cheek", Q).values(), default=99)
                res.append(min(g, cgm))
            rows += 1
            if len(res) == 2 and None not in res and min(res) < CLR_PART:
                reasons["within 3 mm of a part, box or cable"] += 1
            if len(res) == 2 and None not in res and min(res) >= CLR_PART and (best is None or min(res) > best[2]):
                best = (x, z, min(res))
    J["cheeks"] = (dict(found=True, x=best[0], z=best[1], clearance_mm=r(best[2], 1)) if best else
                   dict(found=False, rejected=reasons, searched="x 40 to 88, z 188 to 212, both side walls at the same place, 30 x 30 mm pad "
                        "with its guard ring (42 x 42 mm), %d places" % rows,
                        why="on every place at least one side has a footprint ray that goes through an opening or "
                            "meets a wall outside 1.6 to 4.5 mm (counts in rejected); the side walls there carry the speaker "
                            "grille and its duct (right), the side lamp opening (left), the eye and lamp bosses"))
    print("cheeks", J["cheeks"])
    # board seats
    newbox = {}
    for key, b in BOARDS.items():
        cand = []
        for (shn, o_, d_, grid) in b["surfaces"]:
            sh_ = shell_mesh(S, shn)
            d_ = np.array(d_, float)
            ax_ = int(np.argmax(np.abs(d_)))
            (ia, va), (ib, vb) = grid
            for p_ in va:
                for q_ in vb:
                    o = np.zeros(3)
                    o[ax_], o[ia], o[ib] = o_, p_, q_
                    t = [v for v in hits_along(sh_, o, d_) if v > 0]
                    if t:
                        cand.append((o + d_ * t[0], o, sh_, d_, shn, ia, ib))
        if b.get("keep_out"):
            lo_k, hi_k = np.array(b["keep_out"][0]), np.array(b["keep_out"][1])
            cand = [c_ for c_ in cand if not np.all((c_[0] >= lo_k) & (c_[0] <= hi_k))]
        best_b = None
        why = {}
        for (c, o, sh, db, shn, ia, ib), rot in [(c_, ro) for c_ in cand for ro in (0, 1)]:
            bx, by = (BOARD[0], BOARD[1]) if rot == 0 else (BOARD[1], BOARD[0])
            ua, ub = np.eye(3)[ia], np.eye(3)[ib]
            # the shell under the footprint: 5 x 3 hits and a plane fit (the 1.1 mm tape takes up 0.6 mm), tilt up to 25 deg
            Q = []
            for dx in np.linspace(-bx / 2, bx / 2, 5):
                for dy in np.linspace(-by / 2, by / 2, 3):
                    oo = o + ua * dx + ub * dy
                    tt = [v for v in hits_along(sh, oo, db) if v > 0]
                    if not tt:
                        break
                    Q.append(oo + db * tt[0])
            if len(Q) < 15:
                why["off the shell"] = why.get("off the shell", 0) + 1
                continue
            Q = np.array(Q)
            n = np.linalg.svd(Q - Q.mean(0))[2][2]
            res = (Q - Q.mean(0)) @ n
            n = -n if n @ db > 0 else n                                # into the cavity
            tilt = float(np.degrees(np.arccos(min(1.0, abs(n @ db)))))
            if np.ptp(res) > 0.6 or tilt > 25.0:
                why["not flat"] = why.get("not flat", 0) + 1
                continue
            c = c + n * ((Q.mean(0) - c) @ n)
            ea = ua if rot == 0 else ub
            ea = ea - (ea @ n) * n
            ea /= np.linalg.norm(ea)
            eb = np.cross(n, ea)
            g = np.array([c + ea * u_ + eb * v_ + n * w_ for u_ in np.linspace(-bx / 2, bx / 2, 7)
                          for v_ in np.linspace(-by / 2, by / 2, 5) for w_ in np.linspace(0.3, BOARD[2], 4)])
            shell_g = [x for x in trees[b["link"]].items()]
            gp = min(float(t.query(g)[0].min()) for k, t in shell_g if not k.startswith(("box tch", shn + "[")))
            gc = min(cable_gaps(ctrees[b["link"]], key, g, rule=CLR_BOARD, own_free=True).values(), default=99)
            gpad = min(float(cKDTree(P).query(g)[0].min()) for pid, P in pads.items() if SITES[pid]["link"] == b["link"])
            if gp < CLR_BOARD or gc < CLR_BOARD or gpad < PAD_TO_BOARD:
                k_ = "part" if gp < CLR_BOARD else ("cable" if gc < CLR_BOARD else "pad")
                why[k_] = why.get(k_, 0) + 1
                continue
            lead = sum(float(np.linalg.norm(pads[p].mean(0) - c)) for p in b["pads"])
            if "near" in b:
                lead += float(np.linalg.norm(np.array(b["near"]) - c))
            if best_b is None or lead < best_b[0]:
                best_b = (lead, c, gp, gc, gpad, rot, (bx, by), n, tilt, shn, db, ia, ib)
                best_g = g
        if best_b is None:
            J["boards"][key] = dict(found=False, rejected=why)
            print(key, "no seat", why)
            continue
        lead, c, gp, gc, gpad, rot, (bx, by), n, tilt, shn, db, ia, ib = best_b
        gcs = cable_gaps(ctrees[b["link"]], key, best_g, rule=CLR_BOARD)
        gc_own = min(gcs.values(), default=99)
        own_g = {k: r(v, 1) for k, v in gcs.items() if k in OWN[key]}
        J["boards"][key] = dict(id=b["id"], centre_top_face_world=np.round(c, 2).tolist(), box_xyz_mm=[bx, by, BOARD[2]],
                                long_side_along="xyz"[ia] if rot == 0 else "xyz"[ib], face_normal=np.round(n, 3).tolist(), tilt_deg=r(tilt, 1),
                                part_gap_mm=r(gp, 1), cable_gap_mm=r(gc, 1), own_lead_gaps_mm=own_g, own_lead_rule_mm=OWN_LEAD_TO_BOARD,
                                own_leads_ok=bool(min(own_g.values(), default=99) >= OWN_LEAD_TO_BOARD), pad_gap_mm=r(gpad, 1), lead_sum_mm=r(lead, 0),
                                on=shn, mount="VHB 4950 (BOM 29) on the board's back; its parts face %s" % np.round(n, 2).tolist())
        ea = (np.eye(3)[ia] if rot == 0 else np.eye(3)[ib])
        ea = ea - (ea @ n) * n
        ea /= np.linalg.norm(ea)
        eb = np.cross(n, ea)
        cc = c + n * BOARD[2] / 2
        corners = np.array([cc + ea * sa * bx / 2 + eb * sb * by / 2 + n * sn * BOARD[2] / 2
                            for sa in (-1, 1) for sb in (-1, 1) for sn in (-1, 1)])
        ext = np.ptp(corners, axis=0)
        J["boards"][key]["aabb_xyz_mm"] = np.round(ext, 2).tolist()
        newbox[key] = dict(id=key, label=b["label"], dims_xyz_mm=np.round(ext, 2).tolist(), box_with_margin_mm=np.round(ext + 2, 2).tolist(),
                           center_mm=np.round(cc, 2).tolist(), frame="urdf_world_mm",
                           n_positions=None, dist_to_anchor_mm=None, dist_to_imu_mm=None,
                           flat_face_support="VHB 4950 on %s, face normal %s" % (shn, np.round(n, 2).tolist()),
                           score=None, seat_fix="altaay_lab/twin/freeze/touch_pads.py (D51)")
        print(key, J["boards"][key])
    J["pass"] = bool(all(p["ok"] for p in J["pads"].values()) and all(v >= PAD_TO_PAD for v in sp.values())
                     and all(v.get("found", True) and v.get("own_leads_ok", True) for v in J["boards"].values()))
    print("pass", J["pass"])
    if a.write:
        dump(J, os.path.join(HERE, "touch_pads.json"))
        P_ = [p for p in json.load(open(PLACEMENTS)) if not p["id"].startswith("tch_")]
        P_ += list(newbox.values())
        with open(PLACEMENTS, "w") as fh:
            json.dump(P_, fh, indent=1)
            fh.write("\n")
        print("wrote touch_pads.json and the board boxes in audit/placements.json")


if __name__ == "__main__":
    main()
