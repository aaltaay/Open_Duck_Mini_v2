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
import argparse, hashlib, json, os, re, sys
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


# waypoints per wire family. The paddle cable: carried on the paddle and the carrier down to below the paddle, a free span
# (a service loop) down to its fixed clamp point where it drops into a groove in base_l, the groove to the bay.
PG = DP.PADDLE_GROOVE
CARRIER_VIAS = [(27.0, 20.0, 150.0), (27.0, 30.0, 126.0)]   # behind the paddle's yaw sweep (paddle back x 23, 10 deg about x 18)
FIXED_VIAS = [(44.0, 30.0, 16.0), (46.0, 30.0, DP.BASE["z1"] - 3.5), (105.0, 30.0, DP.BASE["z1"] - 3.5), (110.0, 30.0, DP.BASE["z1"] - 1.0),
              (111.0, 30.0, ZB + 6.0)]   # the groove-to-tray rise taken in two steps, so the bundle bend is wider than its slot circle
SPAN_EXTRA = 12.0          # the free span is this much longer than its longest chord over the travel
FAN_BACK, FAN_OUT = 6.0, 3.0     # each conductor leaves the bundle end along a straight stub: 6 mm back, 3 mm out from the axis
STATES = {"rest": (0.0, 0.0), "docked": (DA.PUSH_DOCKED, DA.YAW_DOCKED), "full_travel": (40.0, 0.0),
          "full_travel_yaw_plus": (40.0, np.radians(10.0)), "full_travel_yaw_minus": (40.0, -np.radians(10.0)),
          "rest_yaw_plus": (0.0, np.radians(10.0)), "rest_yaw_minus": (0.0, -np.radians(10.0))}
VIA = {
    "seat": [(-40.0, 10.0, 12.0), (-21.0, 14.0, 20.0), (-16.5, 14.0, 20.0), (27.0, 14.0, 20.0), (27.0, 14.0, DP.BASE["z1"] - 1.5),
             (60.0, 14.0, DP.BASE["z1"] - 1.8), (108.0, 14.0, DP.BASE["z1"] - 1.8), (108.2, 14.0, ZB + 3.0)],
}


def arc(A, B, L, n, k):
    """k points of a circular arc of length L from A to B, bulging toward n (made square to AB); None if L < the chord"""
    A, B = np.asarray(A, float), np.asarray(B, float); c = float(np.linalg.norm(B - A)); u = (B - A) / c
    n = np.asarray(n, float) - u * np.dot(n, u); n /= np.linalg.norm(n)
    if L < c - 1e-6:
        return None, None
    if L - c < 1e-6:
        return [A + (B - A) * t for t in np.linspace(0, 1, k)], float("inf")
    lo, hi = 1e-6, 2 * np.pi - 1e-6
    for _ in range(80):
        th = (lo + hi) / 2
        if th / (2 * np.sin(th / 2)) < L / c: lo = th
        else: hi = th
    R = L / th; mid = (A + B) / 2; ctr = mid - n * R * np.cos(th / 2)
    return [ctr + R * (np.cos(f) * n + np.sin(f) * u) for f in np.linspace(-th / 2, th / 2, k)], R


def chaikin(P, n=3):
    """round the corners of a routed trunk (corner cutting, the ends kept), so the conductors in their slots keep their
    spacing through a bend instead of crowding at a sharp corner"""
    P = [np.asarray(p, float) for p in P]
    for _ in range(n):
        Q = [P[0]]
        for a, b in zip(P[:-1], P[1:]):
            Q += [0.75 * a + 0.25 * b, 0.25 * a + 0.75 * b]
        Q.append(P[-1]); P = Q
    return P


def T_state(link, push, yaw):
    """the dock's own link transform (dock_assembly.link_transform), never a second copy of it"""
    return DA.link_transform(link, (push, yaw))


def pose_run(r, push, yaw):
    """a wire's points in a state: paddle and carrier points ride their link, the free span is rebuilt as an arc of its own
    rest length between its moved ends, fixed points stay. Returns (points, span radius or None, span ok)"""
    P = np.array(r["points"], float); tags = r["attach"]
    Q = []
    for p, t in zip(P, tags):
        if t.startswith("blend:"):       # a leg between the paddle and the carrier: it flexes, moving from the paddle's pose to the carrier's
            f = float(t[6:]); h = np.r_[p, 1.0]
            Q.append((1 - f) * (T_state("paddle", push, yaw) @ h)[:3] + f * (T_state("carrier", push, yaw) @ h)[:3])
        else:
            Q.append((T_state(t, push, yaw) @ np.r_[p, 1.0])[:3] if t in ("paddle", "carrier") else p.copy())
    idx = [i for i, t in enumerate(tags) if t == "span"]
    if not idx:
        return np.array(Q), None, True
    i0, i1 = idx[0], idx[-1]
    A, B = Q[i0 - 1], Q[i1 + 1]
    L = float(np.sum(np.linalg.norm(np.diff(P[i0 - 1:i1 + 2], axis=0), axis=1)))
    bul = P[(i0 + i1) // 2] - (P[i0 - 1] + P[i1 + 1]) / 2
    pts, R = arc(A, B, L, bul if np.linalg.norm(bul) > 1e-6 else np.array((-1.0, 0, 0)), i1 - i0 + 3)
    if pts is None:
        return np.array(Q), 0.0, False
    for k, i in enumerate(range(i0, i1 + 1)):
        Q[i] = pts[k + 1]
    return np.array(Q), R, True


TIGHT = {"seat"}


def family(w):
    if w["cable"] == "KC5":
        return "seat"
    return None


def obstacles(push=0.0, yaw=0.0):
    """the bodies a wire must clear in a paddle pose: the dock's components and fasteners as dock_assembly builds them for
    that pose (the strips rebuilt for the push), not a rest-state copy moved here"""
    comps = DA.components((push, yaw))
    M = [(c["id"], c["mesh"]) for c in comps if not c["id"].startswith(("adapter", "plug"))]
    return M + DA.fastener_meshes((push, yaw))


def grid(M):
    shape = np.ceil((HI - LO) / H).astype(int) + 1
    occ = np.zeros(shape, bool)
    for cid, m in M:
        b0 = np.maximum(np.floor((m.bounds[0] - LO) / H).astype(int) - 1, 0); b1 = np.minimum(np.ceil((m.bounds[1] - LO) / H).astype(int) + 2, shape)
        if np.any(b1 <= b0):
            continue
        ii = np.stack(np.meshgrid(*[np.arange(b0[k], b1[k]) for k in range(3)], indexing="ij"), -1).reshape(-1, 3)
        P = LO + ii * H
        if not m.is_watertight:            # contains() would read an open mesh as empty: refuse, never route through it
            raise SystemExit("obstacle %s is not watertight" % cid)
        inside = m.contains(P)
        sol = inside.copy()
        rest = np.nonzero(~inside)[0]
        for k0 in range(0, len(rest), 200000):     # every voxel near a surface is solid too (no size limit, no fallback)
            ch = rest[k0:k0 + 200000]
            _, dd, _ = trimesh.proximity.closest_point(m, P[ch])
            sol[ch] = dd < H * 0.6
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
        if not m.is_watertight:
            raise SystemExit("obstacle %s is not watertight: the inside test would pass it" % cid)
        ins = m.contains(Q)
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


def input_fingerprint(here=None):
    """sha256 over everything a route result depends on: the printed parts' STLs, the fastener schedule (kinds, sizes,
    links, poses), the netlist wires (ends, gauges, cables; not the cut lengths this script writes back), the terminals,
    the docked pose and the sources of dock_parts.py, dock_assembly.py and this file (their design parameters). C12
    recomputes it and fails on any mismatch, so a stale dock_cables3d.json can never pass."""
    here = here or HERE
    h = hashlib.sha256()
    for n in sorted(DP.PRINTED):
        h.update(n.encode()); h.update(open(os.path.join(here, "stl", n + ".stl"), "rb").read())
    for f in json.load(open(os.path.join(here, "dock_fasteners.json")))["fasteners"]:
        h.update(json.dumps([f.get(k) for k in ("id", "kind", "link", "pose_dock", "d", "length_mm", "head", "s", "h")], sort_keys=True).encode())
    nl = yaml.safe_load(open(os.path.join(here, "dock_netlist.yaml")))
    h.update(json.dumps([[w.get(k) for k in ("from", "to", "net", "gauge", "cable", "ends")] for w in nl["wires"]], sort_keys=True).encode())
    h.update(json.dumps({k: np.round(np.asarray(v, float), 3).tolist() for k, v in sorted(terminals().items())}).encode())
    for f in ("docked_pose.json", "dock_parts.py", "dock_assembly.py", "dock_routes.py"):
        h.update(f.encode()); h.update(open(os.path.join(here, f), "rb").read())
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--write-cuts", action="store_true"); a = ap.parse_args()
    NL = yaml.safe_load(open(os.path.join(HERE, "dock_netlist.yaml")))
    T = terminals()
    M = obstacles()
    FP = input_fingerprint()
    cache = os.environ.get("DOCK_ROUTE_CACHE")
    z = np.load(cache) if cache and os.path.exists(cache) else None
    if z is not None and "fp" in z.files and str(z["fp"]) == FP:     # the grid cache is reused only for the same inputs
        occ, dist = z["occ"], z["dist"]
    else:
        occ, dist = grid(M)
        if cache:
            np.savez_compressed(cache, occ=occ, dist=dist, fp=np.array(FP))
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
    BUNDLE = {"KP1": None, "KC5": [np.array(v, float) for v in VIA["seat"]]}
    trunk = {}
    for cid, vias in BUNDLE.items():
        ws = [w for w in NL["wires"] if w["cable"] == cid]
        ods = [OD[w["gauge"]] for w in ws]
        n = len(ws)
        rho = 0.0 if n == 1 else max(ods) / (2 * np.sin(np.pi / n)) + (0.4 if n > 2 else 0.15)   # room for the bends     # conductor centres on a circle, neighbours >= one OD apart
        rb = rho + max(ods) / 2
        own_ = [w_["from"] for w_ in ws] + [w_["to"] for w_ in ws]
        if vias is None:                 # the paddle cable: carrier part, free span (arc), fixed part
            Pc, fail = route_chain([np.array(v) for v in CARRIER_VIAS], (rb + 0.3, rb), [], own=own_)
            Pf, fail2 = route_chain([np.array(v) for v in FIXED_VIAS], (rb + 0.3, rb), [], own=own_)
            if Pc is None or Pf is None:
                bad.append("%s bundle: no route %s" % (cid, fail or fail2)); continue
            chord = max(float(np.linalg.norm(Pf[0] - (Pc[-1] + np.array((ps, 0, 0))))) for ps, _ in STATES.values())
            span, Rb = arc(Pc[-1], Pf[0], chord + SPAN_EXTRA, np.array((-1.0, 0, 0)), 24)
            Pc, Pf = chaikin(Pc), chaikin(Pf)
            P = Pc + span[1:-1] + Pf
            ttag = ["carrier"] * len(Pc) + ["span"] * (len(span) - 2) + ["fixed"] * len(Pf)
        else:
            P, fail = route_chain(vias, (rb + 0.3, rb), [], own=own_)
            # the seat pair runs in the spine channel and the base groove: kept on its grid path, no corner rounding
            ttag = ["fixed"] * (len(P) if P else 0)
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
        trunk[cid] = dict(P=P, slots=slots, rb=rb, rho=rho, tags=ttag)
        reserve(P, rb)
        for w_ in ws:                    # the straight fan-out stubs of every conductor, before any leg is routed
            S_ = slots[(w_["from"], w_["to"])]
            for e0, e1, c_ in ((S_[0], S_[1], P[0]), (S_[-1], S_[-2], P[-1])):
                d_ = (e1 - e0) / np.linalg.norm(e1 - e0); r_ = (e0 - c_) / max(np.linalg.norm(e0 - c_), 1e-9)
                reserve([e0, e0 - d_ * FAN_BACK + r_ * FAN_OUT], OD[w_["gauge"]] / 2)
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
        tags = None
        if w["cable"] == "KP2":
            P = [T[fa], T[fb]]; tags = ["paddle", "paddle"]
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
            pa_, pb_ = sa - da * FAN_BACK + ra * FAN_OUT, sb + db * FAN_BACK + rb_ * FAN_OUT   # the conductors fan out of the bundle end, each from its own slot
            leg_a = [Xa, pa_]
            leg_b = [pb_, Xb]
            sh = [T[x] for x in (fa, fb) if x in used] + [x_ for x_, k_ in ((Xa, fa), (Xb, fb)) if k_ in used]
            flex = (rad + 1.0, rad + 0.6)    # a pin-to-bundle leg flexes with the paddle yaw: routed with more room to its neighbours and the paddle
            La, fail_a = route_chain(leg_a, flex if fa == pad else needs, ends + [Xa, Xb], own=(fa, fb), shared=sh)    # only the wire's own lead exits are opened
            Lb, fail_b = route_chain(leg_b, flex if fb == pad else needs, ends + [Xa, Xb], own=(fa, fb), shared=sh)
            if La is not None and Lb is not None:
                La, Lb = La + [sa], [sb] + Lb                            # the last 6 mm straight into its slot
            if La is None or Lb is None:
                ok = False; bad.append("%s %s-%s: no leg route %s" % (w["cable"], fa, fb, fail_a or fail_b))
            else:
                P = [T[fa]] + La + [np.asarray(x) for x in body[1:-1]] + Lb + [T[fb]]
                tg = trunk[w["cable"]]["tags"]; tg = tg if near_a else tg[::-1]
                ea = "paddle" if fa.startswith("PADDLE") else "fixed"; eb = "paddle" if fb.startswith("PADDLE") else "fixed"
                tags = [ea] * (1 + len(La)) + tg[1:-1] + [eb] * (len(Lb) + 1)
                for lo, hi, end_, nxt in ((0, 1 + len(La), ea, tg[1]), (len(tags) - len(Lb) - 1, len(tags), eb, tg[-2])):
                    if end_ == "paddle" and nxt == "carrier":   # pin to bundle: blended by length from the pin (paddle) to the slot (carrier)
                        seg = [np.asarray(x, float) for x in P[lo:hi]] if lo == 0 else [np.asarray(x, float) for x in P[lo:hi]][::-1]
                        cum = np.r_[0, np.cumsum(np.linalg.norm(np.diff(np.array(seg), axis=0), axis=1))]; cum = cum / max(cum[-1], 1e-9)
                        bl = ["blend:%.3f" % c for c in cum]; bl[0] = "paddle"
                        tags[lo:hi] = bl if lo == 0 else bl[::-1]
                reserve(La, rad); reserve(Lb, rad)
        else:
            sh = [T[x] for x in (fa, fb) if x in used] + [x_ for x_, k_ in ((Xa, fa), (Xb, fb)) if k_ in used]
            P, fail = route_chain([Xa, Xb], needs, ends + [Xa, Xb], own=(fa, fb), shared=sh)
            if P is None:
                ok = False; bad.append("%s %s-%s: no route between %s" % (w["cable"], fa, fb, fail))
            else:
                P = [T[fa]] + P + [T[fb]]
                tags = ["fixed"] * len(P)
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
            slack = 40.0                     # 2 x 20 mm tails; the paddle travel is in the free span's own length
            holder = "holder lead" in (w.get("ends") or [])
            cut = int(np.ceil((L + slack) / 10.0) * 10) if not holder else 90
            if holder and L + 10 > 90:
                bad.append("%s %s-%s: the 90 mm holder lead is short (%.0f mm routed)" % (w["cable"], fa, fb, L))
            rec.update(attach=tags, points=np.round(np.array(P), 2).tolist(), length_mm=round(L, 1), cut_mm=cut, slack_mm=slack if not holder else round(90 - L, 1),
                       clearance_mm=None if exact is None else round(exact, 2), radius_mm=rad, lead_exit_mm=EXIT, hits=hits)
            if w["cable"] not in trunk and w["cable"] != "KP2":
                reserve(P, rad)
        else:
            rec.update(points=None)
        cables.setdefault(w["cable"], []).append(rec)
        print(w["cable"], fa, fb, rec.get("length_mm"), "clearance", rec.get("clearance_mm"), "radius", rad, flush=True)
    # 3. every state of the paddle (rest, docked, full travel, the swivel stops): bodies, wire to wire, bend radius of the free
    # span (3 x OD), stretch (the span's length covers its chord); the cut covers the longest state
    state_res = {}
    for sname, (push, yaw) in STATES.items():
        Ms = obstacles(push, yaw)        # every body rebuilt for the pose by dock_assembly
        Ts = {k: (T_state("paddle", push, yaw) @ np.r_[v, 1.0])[:3] if k.startswith("PADDLE.") else v for k, v in T.items()}
        posed, issues = {}, []
        for cid, rs in cables.items():
            for r in rs:
                if not r.get("points"):
                    continue
                Q, R, ok_ = pose_run(r, push, yaw)
                Lq = float(np.sum(np.linalg.norm(np.diff(Q, axis=0), axis=1)))
                rr = dict(r, points=Q.round(2).tolist())
                posed.setdefault(cid, []).append(rr)
                fa, fb = r["frm"], r["to"]; ends = [Ts[fa], Ts[fb]]
                smp = [x for p_, q_ in zip(Q[:-1], Q[1:]) for x in np.linspace(p_, q_, int(np.linalg.norm(q_ - p_) / 0.5) + 2)]
                Mw = [(c_, m_) for c_, m_ in Ms if c_ not in own_parts(fa) + own_parts(fb)]
                h = inside_any(Mw, smp, ends); ex = exact_clearance(Mw, smp, ends)
                if h or (ex is not None and ex < r["radius_mm"] - 0.15):
                    issues.append("%s %s: in a body %s, clearance %s" % (r["cable"], r["wire"], h[:2], ex))
                if not ok_:
                    issues.append("%s %s: stretched (the span is shorter than its chord)" % (r["cable"], r["wire"]))
                elif R is not None and R < 3 * r["od_mm"]:
                    issues.append("%s %s: span bend radius %.1f mm under 3 x OD" % (r["cable"], r["wire"], R))
                rr["length_mm"] = round(Lq, 1); rr["span_radius_mm"] = None if R is None or not np.isfinite(R) else round(R, 1)
        for x in pairwise(posed, Ts):
            issues.append("wires overlap: %s and %s, %.2f mm apart at %s (radii sum %.2f)" % x)
        state_res[sname] = dict(push_mm=round(push, 2), yaw_deg=round(float(np.degrees(yaw)), 2), check="PASS" if not issues else issues,
                                runs={r["wire"]: dict(points=r["points"], length_mm=r["length_mm"], span_radius_mm=r.get("span_radius_mm")) for rs in posed.values() for r in rs})
        bad += ["%s: %s" % (sname, x) for x in issues]
        print(sname, "PASS" if not issues else issues[:3], flush=True)
    for rs in cables.values():          # the cut covers the longest state; per-state geometry and checks on each run
        for r in rs:
            if not r.get("points"):
                continue
            Lmax = max(st["runs"][r["wire"]]["length_mm"] for st in state_res.values())
            r["length_max_mm"] = Lmax
            if r["cut_mm"] != 90:
                r["cut_mm"] = int(np.ceil((Lmax + 40.0) / 10.0) * 10)
            r["states"] = {k: dict(points=st["runs"][r["wire"]]["points"], length_mm=st["runs"][r["wire"]]["length_mm"],
                                   span_radius_mm=st["runs"][r["wire"]]["span_radius_mm"],
                                   check="PASS" if st["check"] == "PASS" or not any(r["wire"] in x for x in st["check"]) else "FAIL") for k, st in state_res.items()}
    keys = [(r["frm"], r["to"]) for rs in cables.values() for r in rs]
    if len(keys) != len(set(keys)):
        bad.append("a wire has two routes")
    if any(len(set(map(tuple, np.round(np.array(r["points"]), 0).tolist()))) < 2 for rs in cables.values() for r in rs if r["points"]):
        bad.append("a route has no length")
    out = dict(meta=dict(generated_by="altaay_lab/twin/dock/dock_routes.py", label="CAD check only", input_fingerprint=FP, frame="dock frame (dock_parts.py), mm, the dock state (paddle at rest, seat top up)",
                         grid_mm=H, lead_exit_mm=EXIT, rule="cut = the longest state's route + 2 x 20 mm tails (the paddle cable's free span carries the travel in its own length); holder leads 90 mm must reach with 10 mm to spare",
                         states={k: dict(push_mm=round(v[0], 2), yaw_deg=round(float(np.degrees(v[1])), 2), check=state_res.get(k, {}).get("check")) for k, v in STATES.items()},
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
