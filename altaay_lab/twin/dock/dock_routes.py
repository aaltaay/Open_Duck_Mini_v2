#!/usr/bin/env python3
"""Route every wire of dock_netlist.yaml in 3D through the dock (CAD check only) and write dock_cables3d.json.

  python3 altaay_lab/twin/dock/dock_routes.py [--write-cuts]
  --write-cuts sets cut_mm in dock_netlist.yaml to the routed length plus the slack rule (rounded up to 10 mm).

Method (the same as the duck-side router, twin/dock/seats/route2.py, and its self-check):
1. Every body of the dock in the "dock" state (dock_assembly.py: printed and bought parts) and every fastener of
   dock_fasteners.json is an obstacle, voxelised on a 1.5 mm grid with a distance field.
2. One route per wire, between that wire's own two terminals (the pad, lug, test point, cup or hole the wire is
   soldered to), through the hand-set waypoints of its cable (the groove, the spine channel, the face hole), by a
   shortest clear path (Dijkstra, clearance = wire radius + 1 mm, then + 0.3 mm in the tight channels), string pulled.
3. Self-check: each wire's route may enter a body only within 3.5 mm of its own two terminals (the lead exits), and may
   touch only the two parts it is soldered to (its own jack, holder, board or pin); no
   route point anywhere else lies inside any body, and the centre line keeps at least the wire's radius (less 0.15 mm)
   from every body surface (both on the meshes, not the grid). Fails if a wire has no route, or two wires share one.
Cut rule: routed length + 2 x 20 mm service tails, + 20 mm for the paddle cable's 40 mm of travel (it is longest
with the paddle at rest, measured here); the holder's own 16 AWG leads must reach with 10 mm to spare.
"""
import argparse, json, os, re, sys
import numpy as np
import trimesh
import yaml
from scipy import ndimage
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dock_parts as DP  # noqa: E402
import dock_assembly as DA  # noqa: E402

H = 1.5
LO = np.array([-115.0, -150.0, 0.0]); HI = np.array([205.0, 150.0, 245.0])
OD = {"16 AWG": 3.0, "20 AWG": 1.8, "26 AWG": 1.3}      # [I] BNTECHGO listings (cables3d SRC od16, od20; 26 AWG from BOM 25)
EXIT = 3.5
ZB = DP.BAY["z0"] + DP.BAY["floor"]
ZT = ZB + DP.PERF["standoff"] + 1.6


def terminals():
    T = {}
    T["J1.TIP"] = (DP.BAY["x1"] - 15.0, DP.JACK["y"], DP.JACK["z"]); T["J1.SLV"] = (DP.BAY["x1"] - 15.0, DP.JACK["y"] + 2.6, DP.JACK["z"])
    T["FD.IN"] = (170.5, -86.4, ZB + DA.VHB + 8.6); T["FD.OUT"] = (119.5, -86.4, ZB + DA.VHB + 8.6)
    zs = ZB + DA.VHB + 1.6
    T["SWG.VIN"] = (152.5, -36.0, zs); T["SWG.VOUT"] = (167.8, -36.0, zs); T["SWG.GND"] = (152.5, -18.0, zs); T["SWG.CTRL"] = (167.8, -18.0, zs)
    zc = ZB + DA.VHB + 3.2
    T["CH.VSS"] = (124.0, -16.5, zc); T["CH.VDD"] = (136.0, -16.5, zc); T["CH.VBATP"] = (136.0, -31.0, zc); T["CH.STAT"] = (142.5, -22.0, ZB + DA.VHB + 1.6)
    for i, p in enumerate(("GND", "V9", "VSYS", "STAT", "CHGS", "SNS", "Q1C")):
        T[f"GATE.{p}"] = (121.6, 8.0 + 4.0 * i, ZT)
    s0 = DP.SW_HOLE_Z - DP.SW["hole_from_bottom"] - 3.5
    T["MS.C"] = (-63.4, -5.08, s0); T["MS.NO"] = (-63.4, 5.08, s0)
    for (z, y), n in zip(DP.PADDLE_PINS, DP.PIN_NAMES):
        key = {"SYS_R": "SYS_R", "SYS_L": "SYS_L", "GND_R": "GND_R", "GND_L": "GND_L", "SENSE": "SNS", "CHG": "CHG"}[n]
        T[f"PADDLE.{key}"] = (-DP.PIN_PROUD + DP.PIN["initial_height"] + 0.4, y, z)
    return {k: np.array(v, float) for k, v in T.items()}


LEAD = 4.0     # the straight lead-in from each terminal along its exit direction (past the 3.5 mm lead exit)


def lead_dir(k):
    """the direction a wire leaves its terminal: up from pads, test points and board holes; along the holder's axis; out of
    the jack lugs; down from the switch lugs; back out of the pin cups"""
    if k.startswith("FD."):
        return np.array((1.0, 0, 0)) if k.endswith("IN") else np.array((-1.0, 0, 0))
    if k.startswith("J1."):
        return np.array((-1.0, 0, 0))
    if k.startswith("MS."):
        return np.array((0, 0, -1.0))
    if k.startswith("PADDLE."):
        return np.array((1.0, 0, 0))
    return np.array((0, 0, 1.0))


# waypoints per wire family (through the groove, the spine channel and the face hole)
FACE = (DP.CABLE_HOLE["y"], DP.CABLE_HOLE["z"])
VIA = {
    "paddle": [(14.0, 14.0, None), (14.0, FACE[0], FACE[1]), (60.0, FACE[0], FACE[1]), (79.0, FACE[0], FACE[1]), (90.0, FACE[0] + 2, FACE[1]),
               (90.0, FACE[0] + 2, 40.0), (97.0, FACE[0], ZB + 4.0), (103.0, FACE[0], ZB + 4.0), (110.0, FACE[0], ZB + 4.0)],
    "seat": [(-40.0, 10.0, 12.0), (-21.0, 14.0, 20.0), (-16.5, 14.0, 20.0), (27.0, 14.0, 20.0), (27.0, 14.0, DP.BASE["z1"] - 1.5),
             (60.0, 14.0, DP.BASE["z1"] - 1.8), (108.0, 14.0, DP.BASE["z1"] - 1.8), (108.2, 14.0, ZB + 3.0)],
}
TIGHT = {"seat"}


def family(w):
    if w["cable"] == "KP1":
        return "paddle"
    if w["cable"] == "KC5":
        return "seat"
    return None


def obstacles():
    comps = DA.components("dock")
    M = [(c["id"], c["mesh"]) for c in comps if not c["id"].startswith(("adapter", "plug"))]
    fj = os.path.join(HERE, "dock_fasteners.json")
    if os.path.exists(fj):
        for f in json.load(open(fj))["fasteners"]:
            T = np.array(f["pose_dock"])
            if f["kind"] == "screw":
                m = trimesh.creation.cylinder(radius=f["d"] / 2, height=f["length_mm"], sections=10); m.apply_translation((0, 0, f["length_mm"] / 2))
                hd = trimesh.creation.cylinder(radius=f["head"]["dk"] / 2, height=f["head"]["k"], sections=10); hd.apply_translation((0, 0, -f["head"]["k"] / 2))
                m = trimesh.util.concatenate([m, hd])
            elif f["kind"] == "nut":
                m = trimesh.creation.cylinder(radius=f["s"] / 2 / np.cos(np.pi / 6), height=f["h"], sections=6); m.apply_translation((0, 0, f["h"] / 2))
            else:
                continue
            m.apply_transform(T)
            M.append((f["id"], m))
    return M


def grid(M):
    shape = np.ceil((HI - LO) / H).astype(int) + 1
    occ = np.zeros(shape, bool)
    for cid, m in M:
        b0 = np.maximum(np.floor((m.bounds[0] - LO) / H).astype(int) - 1, 0); b1 = np.minimum(np.ceil((m.bounds[1] - LO) / H).astype(int) + 2, shape)
        if np.any(b1 <= b0):
            continue
        ii = np.stack(np.meshgrid(*[np.arange(b0[k], b1[k]) for k in range(3)], indexing="ij"), -1).reshape(-1, 3)
        P = LO + ii * H
        inside = m.contains(P) if m.is_watertight else np.zeros(len(P), bool)
        try:
            d = np.abs(trimesh.proximity.signed_distance(m, P[~inside])) if (~inside).sum() and len(P) < 400000 else None
        except Exception:
            d = None
        sol = inside.copy()
        if d is not None:
            sol[~inside] = d < H * 0.6
        occ[tuple(ii[sol].T)] = True
    dist = ndimage.distance_transform_edt(~occ) * H
    return occ, dist


def idx(p):
    return tuple(np.clip(np.round((np.asarray(p) - LO) / H).astype(int), 0, None))


def pos(i):
    return LO + np.asarray(i) * H


def path(dist, a, b, need, open_pts, margin=24):
    A, B = np.array(idx(a)), np.array(idx(b))
    lo_i = np.maximum(np.minimum(A, B) - margin, 0); hi_i = np.minimum(np.maximum(A, B) + margin + 1, dist.shape)
    sub = dist[lo_i[0]:hi_i[0], lo_i[1]:hi_i[1], lo_i[2]:hi_i[2]]
    free = sub >= need
    for q in open_pts:                       # the lead exit: a 3.5 mm ball round the wire's own terminal
        qi = np.array(idx(q)) - lo_i; r = int(np.ceil(EXIT / H))
        for d in np.argwhere(np.ones((2 * r + 1,) * 3, bool)) - r:
            if np.linalg.norm(d) * H <= EXIT:
                j = qi + d
                if np.all(j >= 0) and np.all(j < free.shape):
                    free[tuple(j)] = True
    for q in (A - lo_i, B - lo_i):
        if np.all(q >= 0) and np.all(q < free.shape):
            free[tuple(q)] = True
    ids = -np.ones(sub.shape, np.int32); nz = np.argwhere(free).astype(np.int32); ids[tuple(nz.T)] = np.arange(len(nz), dtype=np.int32)
    rows, cols, w = [], [], []
    for dv in [(i, j, k) for i in (-1, 0, 1) for j in (-1, 0, 1) for k in (-1, 0, 1) if (i, j, k) > (0, 0, 0)]:
        q = nz + np.array(dv, np.int32); ok = np.all((q >= 0) & (q < sub.shape), 1); p0, q0 = nz[ok], q[ok]
        tgt = ids[tuple(q0.T)]; m = tgt >= 0
        cost = (np.linalg.norm(dv) * (1 + 0.3 / np.maximum(sub[tuple(q0[m].T)], 0.5))).astype(np.float32)
        rows.append(ids[tuple(p0[m].T)]); cols.append(tgt[m]); w.append(cost)
    rows, cols, w = map(np.concatenate, (rows, cols, w))
    G = csr_matrix((np.r_[w, w], (np.r_[rows, cols], np.r_[cols, rows])), shape=(len(nz), len(nz)))
    sa, sb = ids[tuple(A - lo_i)], ids[tuple(B - lo_i)]
    if sa < 0 or sb < 0:
        return None
    Dd, pred = dijkstra(G, indices=sa, return_predecessors=True)
    if not np.isfinite(Dd[sb]):
        return None
    pp = [sb]
    while pp[-1] != sa:
        pp.append(pred[pp[-1]])
    return [pos(nz[q] + lo_i) for q in pp[::-1]]


def pull(P, dist, need, ends):
    out = [P[0]]; i = 0
    while i < len(P) - 1:
        j = len(P) - 1
        while j > i + 1:
            seg = np.linspace(out[-1], P[j], int(np.linalg.norm(P[j] - out[-1]) / 0.5) + 2)
            if all(dist[idx(s)] >= need or min(np.linalg.norm(s - e) for e in ends) < EXIT for s in seg):
                break
            j -= 1
        out.append(P[j]); i = j
    return out


def inside_any(M, pts, skip_near, radius=0.0):
    """points (outside skip_near's 3.5 mm) inside any body, checked on the meshes"""
    bad = []
    pts = np.asarray(pts)
    keep = np.array([min(np.linalg.norm(p - q) for q in skip_near) > EXIT for p in pts])
    P = pts[keep]
    if not len(P):
        return bad
    for cid, m in M:
        sel = np.all((P >= m.bounds[0] - 0.5) & (P <= m.bounds[1] + 0.5), axis=1)
        if not sel.any():
            continue
        Q = P[sel]
        ins = m.contains(Q) if m.is_watertight else np.zeros(len(Q), bool)
        if ins.any():
            bad.append((cid, np.round(Q[ins][0], 1).tolist()))
    return bad


OWN = {"J1": ("jack",), "FD": ("fuse_holder",), "SWG": ("swg",), "CH": ("evm",), "GATE": ("perf",), "MS": ("switch",)}


def own_parts(pin):
    """the bodies a wire may touch because it ends on them: its own terminal's part (a pin: that spring pin)"""
    c, p = pin.split(".")
    if c == "PADDLE":
        n = {"SNS": "SENSE"}.get(p, p)
        return ("pin_" + n,)
    return OWN.get(c, ())


def exact_clearance(M, samples, ends):
    """least distance (mm) from the route's centre line to the surface of any body, outside the lead exits, on the meshes"""
    P = np.array([x for x in samples if min(np.linalg.norm(x - e) for e in ends) > EXIT])
    if not len(P):
        return None
    best = np.full(len(P), 99.0)
    for cid, m in M:
        near = np.all((P >= m.bounds[0] - 4) & (P <= m.bounds[1] + 4), axis=1)
        if not near.any():
            continue
        _, d, _ = trimesh.proximity.closest_point(m, P[near])
        best[near] = np.minimum(best[near], d)
    return float(best.min())


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--write-cuts", action="store_true"); a = ap.parse_args()
    NL = yaml.safe_load(open(os.path.join(HERE, "dock_netlist.yaml")))
    T = terminals()
    M = obstacles()
    cache = os.environ.get("DOCK_ROUTE_CACHE")
    if cache and os.path.exists(cache):
        z = np.load(cache); occ, dist = z["occ"], z["dist"]
    else:
        occ, dist = grid(M)
        if cache:
            np.savez_compressed(cache, occ=occ, dist=dist)
    print("grid", occ.shape, "solid", int(occ.sum()), flush=True)
    cables = {}
    bad = []
    for w in NL["wires"]:
        fa, fb = w["from"], w["to"]
        od = OD[w["gauge"]]; rad = od / 2
        ends = [T[fa], T[fb]]
        fam = family(w)
        vias = []
        if fam:
            pad_end = fa if fa.startswith("PADDLE") else fb
            for v in VIA[fam]:
                vias.append(np.array([v[0], v[1], v[2] if v[2] is not None else T[pad_end][2]], float))
            if fam == "seat" and fa.startswith("SWG"):
                vias = vias[::-1]
            if fam == "paddle" and fb.startswith("PADDLE"):
                vias = vias[::-1]
        Xa, Xb = T[fa] + lead_dir(fa) * (LEAD + rad), T[fb] + lead_dir(fb) * (LEAD + rad)   # past the exit by one radius
        chain = [Xa] + vias + [Xb]
        if w["cable"] == "KP2":
            chain = [T[fa], T[fb]]
        P = []
        ok = True
        for k in range(len(chain) - 1):
            a_, b_ = chain[k], chain[k + 1]
            opn = [p for p in (a_, b_) if any(np.allclose(p, e) for e in ends + [Xa, Xb])]
            seg = None
            for need in ((rad + 1.0, rad + 0.3, rad) if fam not in TIGHT else (rad + 0.3, rad)):
                seg = path(dist, a_, b_, need, opn)
                if seg is not None:
                    seg = pull(seg, dist, need, ends)
                    break
            if seg is None:
                ok = False; bad.append("%s %s-%s: no route between %s and %s" % (w["cable"], fa, fb, np.round(a_, 1).tolist(), np.round(b_, 1).tolist())); break
            seg[0] = a_; seg[-1] = b_
            P += seg if not P else seg[1:]
        if ok and w["cable"] != "KP2":
            P = [T[fa]] + P + [T[fb]]
        rec = dict(wire="%s-%s" % (fa, fb), frm=fa, to=fb, net=w["net"], gauge=w["gauge"], color=w["color"], od_mm=od, cable=w["cable"])
        if ok:
            P = [np.asarray(p, float) for p in P]
            L = float(np.sum(np.linalg.norm(np.diff(np.array(P), axis=0), axis=1)))
            samples = [x for p_, q_ in zip(P[:-1], P[1:]) for x in np.linspace(p_, q_, int(np.linalg.norm(q_ - p_) / 0.5) + 2)]
            Mw = [(cid, m) for cid, m in M if cid not in own_parts(fa) + own_parts(fb)]   # each part excluded only for its own wires
            hits = inside_any(Mw, samples, ends)
            exact = exact_clearance(Mw, samples, ends)
            if exact is not None and exact < rad - 0.15:
                hits = hits + [("clearance", round(exact, 2))]
            if hits:
                bad.append("%s %s-%s inside %s" % (w["cable"], fa, fb, hits[:3]))
            slack = 40.0 + (20.0 if w["cable"] == "KP1" else 0.0)
            holder = "holder lead" in (w.get("ends") or [])
            cut = int(np.ceil((L + slack) / 10.0) * 10) if not holder else 90
            if holder and L + 10 > 90:
                bad.append("%s %s-%s: the 90 mm holder lead is short (%.0f mm routed)" % (w["cable"], fa, fb, L))
            rec.update(points=np.round(np.array(P), 2).tolist(), length_mm=round(L, 1), cut_mm=cut, slack_mm=slack if not holder else round(90 - L, 1),
                       clearance_mm=None if exact is None else round(exact, 2), radius_mm=rad, lead_exit_mm=EXIT, hits=hits)
        else:
            rec.update(points=None)
        cables.setdefault(w["cable"], []).append(rec)
        print(w["cable"], fa, fb, rec.get("length_mm"), "clearance", rec.get("clearance_mm"), "radius", rad, flush=True)
    keys = [(r["frm"], r["to"]) for rs in cables.values() for r in rs]
    if len(keys) != len(set(keys)):
        bad.append("a wire has two routes")
    if any(len(set(map(tuple, np.round(np.array(r["points"]), 0).tolist()))) < 2 for rs in cables.values() for r in rs if r["points"]):
        bad.append("a route has no length")
    out = dict(meta=dict(generated_by="altaay_lab/twin/dock/dock_routes.py", label="CAD check only", frame="dock frame (dock_parts.py), mm, the dock state (paddle at rest, seat top up)",
                         grid_mm=H, lead_exit_mm=EXIT, rule="cut = route + 2 x 20 mm tails (+ 20 mm on KP1 for the 40 mm of paddle travel); holder leads 90 mm must reach with 10 mm to spare",
                         od_source="[I] BNTECHGO silicone wire listings (16 AWG 3.0 mm, 20 AWG 1.8 mm); 26 AWG 1.3 mm (BOM 25)"),
               cables=[dict(id=c, runs=r) for c, r in cables.items()], terminals={k: np.round(v, 2).tolist() for k, v in T.items()},
               self_check="PASS" if not bad else bad)
    json.dump(out, open(os.path.join(HERE, "dock_cables3d.json"), "w"), indent=1)
    print("SELF-CHECK", "PASS" if not bad else "FAIL", bad[:6])
    if a.write_cuts and not bad:
        txt = open(os.path.join(HERE, "dock_netlist.yaml")).read()
        for rs in cables.values():
            for r in rs:
                pat = re.compile(r"(\{cable: %s, from: %s, to: %s,[^\n]*?cut_mm: )(\d+)" % (re.escape(r["cable"]), re.escape(r["frm"]), re.escape(r["to"])))
                txt, n = pat.subn(lambda m: m.group(1) + str(r["cut_mm"]), txt)
                assert n == 1, r["wire"]
        open(os.path.join(HERE, "dock_netlist.yaml"), "w").write(txt)
        print("cut_mm written")
    if bad:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
