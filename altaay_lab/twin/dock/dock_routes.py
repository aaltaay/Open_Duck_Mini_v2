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
3. Harnesses (the paddle cable KP1, the seat switch pair KC5) are routed as one bundle with the bundle's envelope (the
   conductor centres on a circle, neighbours at least one OD apart), the conductors laid in it at fixed slots by a
   parallel-transport frame; every other wire is routed after them and keeps clear of the wires already placed.
4. Self-check: each wire's route may enter a body only within 3.5 mm of its own two terminals (the lead exits), and may
   touch only the two parts it is soldered to (its own jack, holder, board or pin); no
   route point anywhere else lies inside any body, and the centre line keeps at least the wire's radius (less 0.15 mm)
   from every body surface (both on the meshes, not the grid). Fails if a wire has no route, or two wires share one; and wire to wire, no two centre lines come closer than the sum of their radii outside
   the terminal zones they share (the 3.5 mm lead exits, and 6 mm round a pad or pin both wires end on).
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
               (90.0, FACE[0] + 2, 40.0), (97.0, FACE[0] + 4, ZB + 10.0), (103.0, FACE[0] + 4, ZB + 10.0), (110.0, FACE[0] + 4, ZB + 10.0)],
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


def path(dist, a, b, need, open_pts, margin=24, wires=None, block=None, shared=()):
    A, B = np.array(idx(a)), np.array(idx(b))
    lo_i = np.maximum(np.minimum(A, B) - margin, 0); hi_i = np.minimum(np.maximum(A, B) + margin + 1, dist.shape)
    sub = dist[lo_i[0]:hi_i[0], lo_i[1]:hi_i[1], lo_i[2]:hi_i[2]]
    free = sub >= need
    if block is not None:                    # other wires' terminals and lead exits: no wire passes over a pad it does not end on
        free &= ~block[lo_i[0]:hi_i[0], lo_i[1]:hi_i[1], lo_i[2]:hi_i[2]]
    for q in open_pts:                       # the lead exit: a 3.5 mm ball round the wire's own terminal
        qi = np.array(idx(q)) - lo_i; r = int(np.ceil(EXIT / H))
        for d in np.argwhere(np.ones((2 * r + 1,) * 3, bool)) - r:
            if np.linalg.norm(d) * H <= EXIT:
                j = qi + d
                if np.all(j >= 0) and np.all(j < free.shape) and (wires is None or not wires[tuple(j + lo_i)] or any(np.allclose(q, z) for z in shared)):
                    free[tuple(j)] = True         # the lead exit opens bodies, never a wire already placed
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
            if all(dist[idx(s)] >= need or min((np.linalg.norm(s - e) for e in ends), default=99.0) < EXIT for s in seg):
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


def pairwise(cables, T, zone=None):
    """every pair of routed wires: least distance between their centre lines against the sum of their radii; points within
    the 3.5 mm lead exit of a terminal, or within 6 mm of a terminal both wires end on (a shared pad, a doubled pin, a
    splice point), are not compared"""
    R = [r for rs in cables.values() for r in rs if r.get("points")]
    smp = []
    for r in R:
        P = np.array(r["points"])
        S = np.concatenate([np.linspace(p, q, int(np.linalg.norm(q - p) / 0.4) + 2) for p, q in zip(P[:-1], P[1:])])
        smp.append(S)
    out = []
    from scipy.spatial import cKDTree
    trees = [cKDTree(S) for S in smp]
    for i in range(len(R)):
        for j in range(i + 1, len(R)):
            a, b = R[i], R[j]
            need = (a["od_mm"] + b["od_mm"]) / 2
            d, k = trees[j].query(smp[i], distance_upper_bound=need)
            close = np.where(np.isfinite(d) & (d < need - 0.05))[0]
            if not len(close):
                continue
            ta = [np.array(T[a["frm"]]), np.array(T[a["to"]])]; tb = [np.array(T[b["frm"]]), np.array(T[b["to"]])]
            shared = [x for x in ta if any(np.allclose(x, y) for y in tb)] + [y for y in tb if any(np.linalg.norm(y - x) < 7.0 for x in ta)]
            for c in close:
                p = smp[i][c]; q = smp[j][k[c]]
                if min(np.linalg.norm(p - e) for e in ta) <= EXIT or min(np.linalg.norm(q - e) for e in tb) <= EXIT:
                    continue
                if any(np.linalg.norm(p - z) < 6.0 + 3.0 for z in shared):
                    continue
                out.append((a["wire"], b["wire"], float(d[c]), np.round(p, 1).tolist(), need))
                break
    return out


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
    occ_w = np.zeros_like(occ)          # voxels taken by wires already placed (each later wire keeps clear of them)
    used = set()                         # terminals that already carry a wire (a second wire on a pad shares its lead exit)
    tball = {}
    for k, p in T.items():               # every terminal and its lead-in, a 3 mm ball each
        m = np.zeros_like(occ); X = p + lead_dir(k) * (LEAD + 1.0)
        for q in (p, X, (p + X) / 2):
            c = np.array(idx(q)); rr = 2
            for d in np.argwhere(np.ones((5, 5, 5), bool)) - rr:
                if np.linalg.norm(d) * H <= 3.0 and np.all(c + d >= 0) and np.all(c + d < m.shape):
                    m[tuple(c + d)] = True
        tball[k] = m
    allb = np.zeros_like(occ)
    for m in tball.values():
        allb |= m

    def term_block(own):
        b = allb.copy()
        for k in own:
            b &= ~tball[k]
        return b

    def reserve(P, rad):
        nonlocal dist
        for p_, q_ in zip(P[:-1], P[1:]):
            for x in np.linspace(p_, q_, int(np.linalg.norm(q_ - p_) / 0.5) + 2):
                c = np.array(idx(x)); rr = int(np.ceil(rad / H))
                for d in np.argwhere(np.ones((2 * rr + 1,) * 3, bool)) - rr:
                    if np.linalg.norm(d) * H <= rad + H:   # one voxel more: the grid is 1.5 mm
                        q = c + d
                        if np.all(q >= 0) and np.all(q < occ_w.shape):
                            occ_w[tuple(q)] = True
        dist = ndimage.distance_transform_edt(~(occ | occ_w)) * H

    def route_chain(chain, need_list, opn_pts, own=(), shared=()):
        P = []
        for k in range(len(chain) - 1):
            a_, b_ = chain[k], chain[k + 1]
            opn = [p for p in (a_, b_) if any(np.allclose(p, e) for e in opn_pts)]
            seg = None
            for need in need_list:
                seg = path(dist, a_, b_, need, opn, wires=occ_w, block=term_block(own), shared=shared)
                if seg is not None:
                    seg = pull(seg, dist, need, opn_pts)
                    break
            if seg is None:
                return None, (a_, b_)
            seg[0] = a_; seg[-1] = b_
            P += seg if not P else seg[1:]
        return [np.asarray(p, float) for p in P], None

    # 1. harness trunks as bundles: one path with the bundle's envelope, the conductors laid in it at fixed offsets
    BUNDLE = {"KP1": [np.array((19.0, FACE[0], 150.0)), np.array((19.0, FACE[0], FACE[1]))] + [np.array([v[0], v[1], v[2]], float) for v in VIA["paddle"][2:]],
              "KC5": [np.array(v, float) for v in VIA["seat"]]}
    trunk = {}
    for cid, vias in BUNDLE.items():
        ws = [w for w in NL["wires"] if w["cable"] == cid]
        ods = [OD[w["gauge"]] for w in ws]
        n = len(ws)
        rho = 0.0 if n == 1 else max(ods) / (2 * np.sin(np.pi / n)) + (0.4 if n > 2 else 0.15)   # room for the bends     # conductor centres on a circle, neighbours >= one OD apart
        rb = rho + max(ods) / 2
        P, fail = route_chain(vias, (rb + 0.3, rb), [], own=[w_["from"] for w_ in ws] + [w_["to"] for w_ in ws])
        if P is None:
            bad.append("%s bundle: no route between %s" % (cid, fail)); continue
        # parallel-transport frame along the trunk, so each conductor keeps its slot through the bends
        t = [(P[k + 1] - P[k]) / max(np.linalg.norm(P[k + 1] - P[k]), 1e-9) for k in range(len(P) - 1)]
        u = np.cross(t[0], [0, 0, 1.0]) if abs(t[0][2]) < 0.9 else np.cross(t[0], [1.0, 0, 0]); u /= np.linalg.norm(u)
        frames = []
        for k in range(len(P)):
            tk = t[min(k, len(t) - 1)] if k == 0 or k == len(P) - 1 else (t[k - 1] + t[k]) / max(np.linalg.norm(t[k - 1] + t[k]), 1e-9)
            u = u - tk * np.dot(u, tk); u /= np.linalg.norm(u); v = np.cross(tk, u)
            frames.append((u, v))
        slots = {}
        for k, w in enumerate(ws):
            ang = 2 * np.pi * k / n
            slots[(w["from"], w["to"])] = [P[m] + rho * (np.cos(ang) * frames[m][0] + np.sin(ang) * frames[m][1]) for m in range(len(P))]
        trunk[cid] = dict(P=P, slots=slots, rb=rb, rho=rho)
        reserve(P, rb)
        for w_ in ws:                    # the straight fan-out stubs of every conductor, before any leg is routed
            S_ = slots[(w_["from"], w_["to"])]
            for e0, e1, c_ in ((S_[0], S_[1], P[0]), (S_[-1], S_[-2], P[-1])):
                d_ = (e1 - e0) / np.linalg.norm(e1 - e0); r_ = (e0 - c_) / max(np.linalg.norm(e0 - c_), 1e-9)
                reserve([e0, e0 - d_ * 6.0 + r_ * 4.0], OD[w_["gauge"]] / 2)
        print(cid, "bundle", round(2 * rb, 2), "mm, %d conductors, trunk %.0f mm" % (n, float(np.sum(np.linalg.norm(np.diff(np.array(P), axis=0), axis=1)))), flush=True)
    # 2. every wire: its own legs from its terminals to its slot in the bundle, or its whole route; placed wires are kept clear
    order = sorted(NL["wires"], key=lambda w: (w["cable"] not in BUNDLE, w["cable"] == "KP2"))
    for w in order:
        fa, fb = w["from"], w["to"]
        od = OD[w["gauge"]]; rad = od / 2
        ends = [T[fa], T[fb]]
        Xa, Xb = T[fa] + lead_dir(fa) * (LEAD + rad), T[fb] + lead_dir(fb) * (LEAD + rad)   # past the exit by one radius
        needs = (rad + 1.0, rad + 0.6)
        ok = True
        if w["cable"] == "KP2":
            P = [T[fa], T[fb]]
        elif w["cable"] in trunk:
            S = trunk[w["cable"]]["slots"][(fa, fb)]
            near_a = np.linalg.norm(S[0] - Xa) < np.linalg.norm(S[-1] - Xa)
            sa, sb = (S[0], S[-1]) if near_a else (S[-1], S[0])
            body = S if near_a else S[::-1]
            pre = []
            pad = fa if fa.startswith("PADDLE") else (fb if fb.startswith("PADDLE") else None)
            da = body[1] - body[0]; da = da / np.linalg.norm(da); db = body[-1] - body[-2]; db = db / np.linalg.norm(db)
            tr = trunk[w["cable"]]["P"]; c0, c1 = (tr[0], tr[-1]) if near_a else (tr[-1], tr[0])
            ra = (sa - c0) / max(np.linalg.norm(sa - c0), 1e-9); rb_ = (sb - c1) / max(np.linalg.norm(sb - c1), 1e-9)
            pa_, pb_ = sa - da * 6.0 + ra * 4.0, sb + db * 6.0 + rb_ * 4.0   # the conductors fan out of the bundle end, each from its own slot
            leg_a = [Xa, pa_]
            leg_b = [pb_, Xb]
            sh = [T[x] for x in (fa, fb) if x in used] + [x_ for x_, k_ in ((Xa, fa), (Xb, fb)) if k_ in used]
            La, fail_a = route_chain(leg_a, needs, ends + [Xa, Xb], own=(fa, fb), shared=sh)    # only the wire's own lead exits are opened
            Lb, fail_b = route_chain(leg_b, needs, ends + [Xa, Xb], own=(fa, fb), shared=sh)
            if La is not None and Lb is not None:
                La, Lb = La + [sa], [sb] + Lb                            # the last 6 mm straight into its slot
            if La is None or Lb is None:
                ok = False; bad.append("%s %s-%s: no leg route %s" % (w["cable"], fa, fb, fail_a or fail_b))
            else:
                P = [T[fa]] + La + [np.asarray(x) for x in body[1:-1]] + Lb + [T[fb]]
                reserve(La, rad); reserve(Lb, rad)
        else:
            sh = [T[x] for x in (fa, fb) if x in used] + [x_ for x_, k_ in ((Xa, fa), (Xb, fb)) if k_ in used]
            P, fail = route_chain([Xa, Xb], needs, ends + [Xa, Xb], own=(fa, fb), shared=sh)
            if P is None:
                ok = False; bad.append("%s %s-%s: no route between %s" % (w["cable"], fa, fb, fail))
            else:
                P = [T[fa]] + P + [T[fb]]
        used.update((fa, fb))
        rec = dict(wire="%s-%s" % (fa, fb), frm=fa, to=fb, net=w["net"], gauge=w["gauge"], color=w["color"], od_mm=od, cable=w["cable"],
                   bundle=dict(od_mm=round(2 * trunk[w["cable"]]["rb"], 2), slot_radius_mm=round(trunk[w["cable"]]["rho"], 2)) if w["cable"] in trunk else None)
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
            if w["cable"] not in trunk and w["cable"] != "KP2":
                reserve(P, rad)
        else:
            rec.update(points=None)
        cables.setdefault(w["cable"], []).append(rec)
        print(w["cable"], fa, fb, rec.get("length_mm"), "clearance", rec.get("clearance_mm"), "radius", rad, flush=True)
    # 3. wire to wire: no two conductor centre lines closer than the sum of their radii, outside the terminal zones they share
    pw = pairwise(cables, T)
    for x in pw:
        bad.append("wires overlap: %s and %s, %.2f mm apart at %s (radii sum %.2f)" % x)
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
