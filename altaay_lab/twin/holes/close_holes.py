"""Stage 3: close every hole that nothing uses, in the printed STLs (CAD check only).

Decision per hole (site x instance, data/sites_raw.json): kept when a fitted screw or insert uses it (seat, pass,
anchor, pilot, bore, or screwdriver access), or for light, sound, camera, vent or grille, bearing, antenna rod, a
cable or a tie; closed otherwise. An STL that serves several instances closes a hole only if every instance leaves
it unused. Plugs, in the STL frame (the print/ frame, so orientation and supports stay):
  - one cylinder per feature of the hole (its own axis and diameter; the mesh scan gives the true axis where the
    site axis is a few degrees off), radius + 0.15 mm so it overlaps the wall, ends extended 0.3 mm;
  - each open end is capped to the part surface itself (D42 follow-up): rays from outside find the surface on
    5 rings just outside the hole (or its counterbore), a quadratic height field (slanted or curved surface) is
    fitted to the hits, the plug runs out past it and is cut by it 0.02 mm under the surface, so it is flush and
    never proud; where the ring is not one smooth surface (an edge or a step), the cap is square to the axis at the
    hole end; a blind end stops in the material;
  - the part is unioned with the plugs (manifold3d), so new material lies only in the old hole.
Checks: watertight, volume added against the analytic hole volume, flush residual (cap plane against the ring
surface), overlap of the added material with every other part at the zero pose, distance to kept holes, cables
and the drilled tie spots. Also the 4 seats under the lower back shell ears on body_middle_bottom_lip (F2 down).
Flush check of every open plug end: rays from outside on the hole disk against the fitted ring surface (dimple
deeper than 0.05 mm or anything proud fails). HOLES_MEASURE=<repo root> measures the STLs there (print/ and
twin/screws/stl/) with the same hole set instead of building (the D39 plugs: HOLES_STAGE=D39 HOLES_MEASURE=...).
Writes <OUT>/stl/*.stl and <OUT>/data/close_report.json (OUT: hlib.py).
"""
import json, os, sys, collections, glob
import numpy as np, trimesh, manifold3d
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hlib

OUT_STL = os.path.join(hlib.OUT, "stl")
os.makedirs(OUT_STL, exist_ok=True)
R_EXTRA, END_EXT, C_SEAT = 0.15, 0.3, 0.25
STAGE = os.environ.get("HOLES_STAGE", "D42")
MEASURE = os.environ.get("HOLES_MEASURE")
NEW_CUT = {"F076", "F178", "F183"}   # F076: one more pass (body_back 7 -> 6 with the ear seats); F178, F183: the left eye
RESTORE = {"F179", "F182"}           # keeps the other diagonal so both bulbs (one STL, mirrored) cut the same 2 STL holes
D42_CUT = {"F069", "F088"} if STAGE == "D42" else set()                    # D42: uniform patterns (DECISIONS.md D42)
D42_BACK = {"F071", "F027", "F084", "F090"} if STAGE == "D42" else set()   # body_front 4 corners, lid 4, head_bot_sheet mirrored corners
NEW_CUT |= D42_CUT
RESTORE |= D42_BACK
S = hlib.scene()
FJ = hlib.load_fj(); F = FJ["fasteners"]; FID = {f["id"]: f for f in F}
ins_of = {f["screw"]: f["id"] for f in F if f["kind"] == "insert"}
NEW_CUT |= {ins_of[s] for s in list(NEW_CUT) if s in ins_of}
RESTORE |= {ins_of[s] for s in list(RESTORE) if s in ins_of}    # an insert comes back with its screw
D42_CUT |= {ins_of[s] for s in list(D42_CUT) if s in ins_of}
rows = json.load(open(os.path.join(hlib.DATA, "sites_raw.json")))
extra = {x["stl"]: x for x in json.load(open(os.path.join(hlib.DATA, "extra_holes.json")))}
C3 = json.load(open(os.path.join(hlib.LAB, "cables3d", "cables3d.json")))
inst = S.inst

KEEP_EMPTY = [("grille or vent", "vent or grille (heat twin)"), ("eye light path", "light (eye)"),
              ("camera lens", "camera lens"), ("speaker opening", "sound (speaker)"), ("antenna rod", "antenna rod"),
              ("bearing seat", "bearing"), ("UNUSED: no part in the CAD or the BOM screws into this hole", None)]


def decide(r):
    fit = [u for u in r["users"] if (u["fitted"] or u["id"] in RESTORE) and u["id"] not in NEW_CUT]
    if fit:
        how = sorted({u["how"] for u in fit})
        return "keep", ("screwdriver access to %s" % ",".join(u["id"] for u in fit) if how == ["screwdriver access"]
                        else "fitted %s (%s)" % (",".join(sorted({u["id"] for u in fit})), "/".join(how)))
    why = r["empty_why"] or ""
    if r["dmax"] > 20.0 and not why:
        return "keep", "opening %.1f mm, not a fastener hole (servo, horn or cable clearance)" % r["dmax"]
    for key, reason in KEEP_EMPTY:
        if why.startswith(key) or key in why[:40]:
            if reason:
                return "keep", reason
            if r["part"] in ("flash_light_module", "flash_reflector_interface"):
                return "keep", "light (projector light channel, parts.csv)"
    if r["cables"]:
        return "keep", "cable " + ",".join(r["cables"])
    cut = [u for u in r["users"] if (not u["fitted"] and u["id"] not in RESTORE) or u["id"] in NEW_CUT]
    if cut:
        return "close", "no screw: " + ",".join("%s %s" % (u["id"], "(D42 uniform pattern)" if u["id"] in D42_CUT else "(one more pass)" if u["id"] in NEW_CUT else "(%s)" % (u.get("status") or "")) for u in cut)
    if why:
        return "close", "unused: " + why[:110]
    return "close", "unused (no list)"


# ---------------------------------------------------------------- local holes per STL
def to_local(T, p):
    return (np.linalg.inv(T) @ np.r_[p, 1])[:3]


def ax_local(T, a):
    v = np.linalg.inv(T)[:3, :3] @ np.asarray(a, float)
    return v / np.linalg.norm(v)


by_src = collections.defaultdict(list)
for r in rows:
    if not r["printed"]:
        continue
    I = inst[r["inst"]]
    T = I["T"]
    o, a = np.array(r["o"]), np.array(r["ax"])
    segs = []
    for s in r["segs"]:
        p0 = to_local(T, o + a * s["t0"]); p1 = to_local(T, o + a * s["t1"])
        segs.append(dict(d=s["d"], kind=s["kind"], p0=p0, p1=p1))
    dec, why = decide(r)
    by_src[I["src"]].append(dict(site=r["site"], inst=r["inst"], part=r["part"], segs=segs, decision=dec, why=why,
                                 users=[u["id"] for u in r["users"]], centre_world=r["centre"], ax_world=r["ax"], dmax=r["dmax"]))


def same_hole(h1, h2):
    c1 = np.mean([np.r_[s["p0"], s["p1"]].reshape(2, 3).mean(0) for s in h1["segs"]], axis=0)
    c2 = np.mean([np.r_[s["p0"], s["p1"]].reshape(2, 3).mean(0) for s in h2["segs"]], axis=0)
    return np.linalg.norm(c1 - c2) < 1.0


def local_holes(src):
    L = []
    for h in by_src[src]:
        for g in L:
            if same_hole(g[0], h):
                g.append(h); break
        else:
            L.append([h])
    return L


# ---------------------------------------------------------------- plug geometry
def true_seg(src_rel, s):
    """the scan's feature for this segment when its axis is the true one (smaller, rounder ring)"""
    x = extra.get(src_rel)
    if not x:
        return s
    c = (s["p0"] + s["p1"]) / 2
    best = s
    for f in x["holes"]:
        p0, p1 = np.array(f["p0"]), np.array(f["p1"])
        if np.linalg.norm((p0 + p1) / 2 - c) < 2.0 and f["d"] < best["d"] - 0.04 and abs(f["d"] - s["d"]) < 0.3 * s["d"]:
            best = dict(d=f["d"], kind=f["kind"], p0=p0, p1=p1, from_scan=True)
    return best


def ring_plane(m, ray, c_end, a_out, R, depth=1.0):
    """plane of the part surface on a ring just outside radius R at an open end (a_out points out of the part)"""
    t = np.array([0, 0, 1.0]) if abs(a_out[2]) < 0.9 else np.array([1.0, 0, 0])
    u = np.cross(a_out, t); u /= np.linalg.norm(u); v = np.cross(a_out, u)
    P = []
    for rho in (R + 0.35, R + 0.7, R + 1.1):
        for th in np.linspace(0, 2 * np.pi, 24, endpoint=False):
            P.append(c_end - a_out * depth + rho * (np.cos(th) * u + np.sin(th) * v))
    P = np.array(P)
    inside = m.contains(P)
    P = P[inside]
    if len(P) < 8:
        return None
    loc, ir, _ = ray.intersects_location(P, np.tile(a_out, (len(P), 1)), multiple_hits=False)
    if len(loc) < 8:
        return None
    dist = np.linalg.norm(loc - P[ir], axis=1)
    hit = loc[dist <= depth + 1.5]
    if len(hit) < 8:
        return None
    cen = hit.mean(0)
    _, _, vt = np.linalg.svd(hit - cen)
    n = vt[2] if vt[2] @ a_out > 0 else -vt[2]
    if n @ a_out < 0.7:     # irregular ring: plane normal to the axis
        n = a_out
    res = (hit - cen) @ n
    # never proud: the cap plane goes through the lowest ring point, so new material stays under the old surface
    if res.max() - res.min() > 0.25:      # ring not flat (edge, step or curved patch): square plane at the hole end
        return None
    c = cen + n * (float(res.min()) - 0.02)
    return dict(c=c, n=n, res_max=float(res.max() - res.min()), res_pos=0.0, n_pts=int(len(hit)))


def cyl(p0, p1, r):
    a = p1 - p0; L = np.linalg.norm(a)
    c = trimesh.creation.cylinder(radius=r, height=L, sections=48)
    T = trimesh.geometry.align_vectors([0, 0, 1], a / L)
    T[:3, 3] = (p0 + p1) / 2
    c.apply_transform(T)
    return c


def halfspace_box(c, n, size=80.0):
    b = trimesh.creation.box(extents=[size, size, size])
    T = trimesh.geometry.align_vectors([0, 0, 1], n)
    T[:3, 3] = c - n * size / 2
    b.apply_transform(T)
    return b


def to_mf(m):
    return manifold3d.Manifold(manifold3d.Mesh(vert_properties=np.asarray(m.vertices, np.float32),
                                               tri_verts=np.asarray(m.faces, np.uint32)))


def from_mf(M, clean=False):
    mm = M.to_mesh()
    V, Fc = np.asarray(mm.vert_properties, float)[:, :3], np.asarray(mm.tri_verts)
    if clean:
        V, _ = separate_pinches(V, Fc)
    t = trimesh.Trimesh(vertices=V, faces=Fc, process=False)
    if clean:
        t.update_faces(t.nondegenerate_faces(height=1e-7)); t.remove_unreferenced_vertices()
    return t


CAP_IN, RING_DR, RING_TOL, FLUSH_TOL = 0.02, (0.35, 0.6, 0.9, 1.2, 1.5), 0.10, 0.05


def frame(a):
    t = np.array([0, 0, 1.0]) if abs(a[2]) < 0.9 else np.array([1.0, 0, 0])
    u = np.cross(a, t); u /= np.linalg.norm(u)
    return u, np.cross(a, u)


def surface_t(ray, c, a_out, u, v, UV, H):
    """height along a_out (from c) where a ray from c + a_out H down -a_out first enters the part; nan if none"""
    O = c + a_out * H + UV[:, :1] * u + UV[:, 1:2] * v
    loc, ir, it = ray.intersects_location(O, np.tile(-a_out, (len(O), 1)), multiple_hits=True)
    t = np.full(len(O), np.nan)
    if len(loc):
        enter = ray.mesh.face_normals[it] @ a_out > 0.05
        h = (loc - c) @ a_out
        for k in np.where(enter & (h < H - 0.05))[0]:
            if not (h[k] <= t[ir[k]]):
                t[ir[k]] = h[k]
    return t


def poly(UV, deg):
    x, y = UV[:, 0], UV[:, 1]
    cols = [np.ones_like(x), x, y] + ([x * x, x * y, y * y] if deg >= 2 else []) + ([x ** 3, x * x * y, x * y * y, y ** 3] if deg >= 3 else [])
    return np.stack(cols, axis=1)


def fit_h(fit, UV):
    """height of the fitted surface along a_out at points UV of the end's (u, v) frame"""
    if fit["kind"].startswith("two planes"):
        h1, h2 = poly(UV, 1) @ fit["p1"], poly(UV, 1) @ fit["p2"]
        return np.minimum(h1, h2) if fit["op"] == "min" else np.maximum(h1, h2)
    if fit["kind"] != "radial":
        return poly(UV, fit["deg"]) @ fit["coef"]
    # radial: on each ray from the hole centre, the part surface just outside the hole in that direction
    return np.interp(np.mod(np.arctan2(UV[:, 1], UV[:, 0]), 2 * np.pi), fit["th"], fit["h_in"], period=2 * np.pi)


def two_planes(UV, t, tol=0.03, it=300):
    """the ring on two faces (an edge, a step or a chamfer): two planes by RANSAC, joined as min (convex edge:
    the part is under both) or max (step up or corner: under either), whichever fits the ring; residual over the
    best 95% of the points (a fillet line may sit between the faces)"""
    rng = np.random.default_rng(7); A = poly(UV, 1)
    def ransac(idx):
        best = None
        for _ in range(it):
            s3 = rng.choice(idx, 3, replace=False)
            try:
                p = np.linalg.solve(A[s3], t[s3])
            except np.linalg.LinAlgError:
                continue
            inl = idx[np.abs(A[idx] @ p - t[idx]) < tol]
            if best is None or len(inl) > len(best):
                best = inl
        return None if best is None or len(best) < 6 else np.linalg.lstsq(A[best], t[best], rcond=None)[0], best
    idx = np.arange(len(t))
    p1, in1 = ransac(idx)
    if p1 is None:
        return None
    rest = np.setdiff1d(idx, in1)
    if len(rest) < 6:
        return None
    p2, in2 = ransac(rest)
    if p2 is None:
        return None
    out = None
    for op in ("min", "max"):
        h = np.minimum(A @ p1, A @ p2) if op == "min" else np.maximum(A @ p1, A @ p2)
        r = np.sort(np.abs(h - t))[int(0.95 * len(t)) - 1]
        if out is None or r < out["res"]:
            out = dict(kind="two planes (%s)" % op, op=op, p1=p1, p2=p2, res=float(r), n=len(t))
    return out


def surface_fit(m, ray, c, a_out, R):
    """the part surface round an open hole end, from 5 rings of rays just outside R (first entry hits): a
    polynomial height field (plane, quadratic or cubic, the lowest degree within RING_TOL), or, where the ring is
    not one smooth surface (the hole at an edge, a step or a chamfer), two faces joined as the part has them
    (two_planes). Returns (fit, note) or (None, reason)."""
    u, v = frame(a_out)
    th = np.linspace(0, 2 * np.pi, 36, endpoint=False)
    UV = np.array([((R + dr) * np.cos(t), (R + dr) * np.sin(t)) for dr in RING_DR for t in th])
    seen, cands = 0, []
    for H in (12.0, 6.0, 3.0, 1.5):
        t = surface_t(ray, c, a_out, u, v, UV, H)
        ok = np.isfinite(t); seen = max(seen, int(ok.sum()))
        if ok.sum() < 0.5 * len(t):
            continue
        for deg in ((1, 2, 3) if ok.sum() >= 0.95 * len(t) else (1,)):
            A = poly(UV[ok], deg); coef = np.linalg.lstsq(A, t[ok], rcond=None)[0]
            res = float(np.abs(t[ok] - A @ coef).max())
            cands.append(dict(u=u, v=v, coef=coef, deg=deg, res=res, n=int(ok.sum()), H=H, kind=["", "plane", "quadratic", "cubic"][deg]))
            if res <= RING_TOL:
                break
        if any(c_["res"] <= RING_TOL for c_ in cands):
            break
        tp = two_planes(UV[ok], t[ok])
        if tp:
            tp.update(u=u, v=v, H=H, deg=9)
            cands.append(tp)
            if tp["res"] <= RING_TOL:
                break
    if not cands:
        return None, ("no surface round the end (it lies inside the part)" if seen == 0 else "ring mostly off the part (%d of %d rays)" % (seen, len(UV)))
    good = [c_ for c_ in cands if c_["res"] <= RING_TOL]
    if not good:
        t = surface_t(ray, c, a_out, u, v, UV[:2 * len(th)], 6.0)
        h_in = np.fmin(t[:len(th)], t[len(th):])
        k = np.where(np.isfinite(h_in))[0]
        if len(k) < 0.5 * len(th):
            return None, "ring not one smooth surface nor two faces (best residual %.2f mm)" % min(c_["res"] for c_ in cands)
        good = [dict(u=u, v=v, kind="radial", th=th, h_in=np.interp(th, th[k], h_in[k], period=2 * np.pi), res=min(c_["res"] for c_ in cands), n=len(k), H=6.0, deg=99)]
    best = min(good, key=lambda c_: (c_["deg"], c_["res"]))
    g = np.array([(r * np.cos(t), r * np.sin(t)) for r in np.linspace(0, R + R_EXTRA + 0.5, 6) for t in th])
    h = fit_h(best, g)
    best.update(lo=float(h.min()), hi=float(h.max()))
    return best, ("%s, ring residual %.3f mm" % (best["kind"], best["res"]) if best["kind"] != "radial" else
                  "radial (the surface just outside the hole in each direction; ring not one smooth surface nor two faces, residual %.2f mm)" % best["res"])


def heightfield(c, a_out, fit, Rc, depth, n_r=8, n_th=48):
    """solid under the fitted surface (minus CAP_IN) over a disk of radius Rc, down to -depth along a_out"""
    u, v = fit["u"], fit["v"]
    th = np.linspace(0, 2 * np.pi, n_th, endpoint=False)
    rs = np.linspace(0, Rc, n_r + 1)[1:]
    UV = np.vstack([[0.0, 0.0]] + [np.c_[r * np.cos(th), r * np.sin(th)] for r in rs])
    h = fit_h(fit, UV) - CAP_IN
    P = c + UV[:, :1] * u + UV[:, 1:2] * v
    top = P + h[:, None] * a_out; bot = P - depth * a_out
    V = np.vstack([top, bot]); nv = len(UV); F = []
    ring = lambda k, j: 1 + k * n_th + (j % n_th)
    for j in range(n_th):
        F.append([0, ring(0, j), ring(0, j + 1)])
        F.append([nv, nv + ring(0, j + 1), nv + ring(0, j)])
        for k in range(n_r - 1):
            a0, a1, b0, b1 = ring(k, j), ring(k, j + 1), ring(k + 1, j), ring(k + 1, j + 1)
            F += [[a0, b0, b1], [a0, b1, a1], [nv + a0, nv + b1, nv + b0], [nv + a0, nv + a1, nv + b1]]
        o0, o1 = ring(n_r - 1, j), ring(n_r - 1, j + 1)
        F += [[o0, nv + o0, nv + o1], [o0, nv + o1, o1]]
    hf = trimesh.Trimesh(V, np.array(F), process=False)
    if hf.volume < 0:
        hf.invert()
    return to_mf(hf)


def stack_ends(m, segs):
    """the two ends of a hole stack along its axis: centre, outward axis, radius of the widest feature there,
    open or blind, and which segment ends touch it"""
    a = segs[0]["p1"] - segs[0]["p0"]; a = a / np.linalg.norm(a)
    ts = [((s["p0"] - segs[0]["p0"]) @ a, (s["p1"] - segs[0]["p0"]) @ a) for s in segs]
    tmin = min(min(x) for x in ts); tmax = max(max(x) for x in ts)
    out = []
    for tend, sign in ((tmin, -1.0), (tmax, 1.0)):
        a_out = a * sign
        touch = []
        for k, (t0, t1) in enumerate(ts):
            te = min(t0, t1) if sign < 0 else max(t0, t1)
            if abs(te - tend) < 0.6:
                touch.append((k, 0 if (t0 < t1) == (sign < 0) else 1))
        R = max(segs[k]["d"] for k, _ in touch) / 2
        c_axis = segs[0]["p0"] + a * tend
        out.append(dict(c=c_axis, a_out=a_out, R=R, open=not bool(m.contains([c_axis + a_out * 0.3])[0]), touch=touch))
    return out, tmax - tmin


def flush_of(mesh_new, ray_new, e):
    """dimple (under the part surface round the hole) and proud (over it) of a capped end: the ring surface is fitted
    again on the checked mesh (rings from R + 0.35 mm, outside the plug), then rays on the hole disk"""
    fit, note = surface_fit(mesh_new, ray_new, e["c"], e["a_out"], e["R"])
    if fit is None:
        return dict(ok=None, note=note)
    th = np.linspace(0, 2 * np.pi, 12, endpoint=False) + 0.137      # off the plug's mesh edges (rays on an edge can miss)
    UV = np.vstack([[0.013, 0.007]] + [np.c_[r * np.cos(th), r * np.sin(th)] for r in (0.35 * e["R"], 0.7 * e["R"], 0.9 * e["R"])])
    if fit["kind"] == "radial":
        UV = UV[1:]
    t = surface_t(ray_new, e["c"], e["a_out"], fit["u"], fit["v"], UV, fit["H"])
    dev = t - fit_h(fit, UV)
    dev = np.where(np.isfinite(dev), dev, -99.0)          # no surface over the disk: an open hole
    return dict(dimple_mm=round(float(max(0.0, -dev.min())), 3), proud_mm=round(float(max(0.0, dev.max())), 3), ref=note,
                ok=bool(-dev.min() <= FLUSH_TOL and dev.max() <= 1e-3))


def build_plug(m, ray, segs):
    """segs: local features of one hole stack; returns (plug manifold, info)"""
    ends, L = stack_ends(m, segs)
    info = dict(ends=[], segs=[])
    ext = [[END_EXT, END_EXT] for _ in segs]
    clips = []
    for e in ends:
        rec = dict(open=e["open"], R=round(e["R"], 2))
        if e["open"]:
            fit, res = surface_fit(m, ray, e["c"], e["a_out"], e["R"])
            if fit is not None:
                for k, w in e["touch"]:
                    ext[k][w] = max(END_EXT, fit["hi"] + 0.5)
                clips.append(heightfield(e["c"], e["a_out"], fit, max(s["d"] for s in segs) / 2 + R_EXTRA + 0.5, L + 20.0))
                rec.update(cap="fitted to the part surface: " + res, n_pts=fit["n"], surface_rise_mm=[round(fit["lo"], 3), round(fit["hi"], 3)])
                e["fit"] = fit
            else:
                clips.append(to_mf(halfspace_box(e["c"] - e["a_out"] * CAP_IN, e["a_out"], 400.0)))
                rec.update(cap="square to the axis at the hole end: " + res)
        info["ends"].append(rec)
    pieces = []
    for k, s in enumerate(segs):
        sa = s["p1"] - s["p0"]; Ls = np.linalg.norm(sa); sa /= Ls
        pieces.append(cyl(s["p0"] - sa * ext[k][0], s["p1"] + sa * ext[k][1], s["d"] / 2 + R_EXTRA))
        info["segs"].append(dict(d=round(s["d"], 2), L=round(Ls, 2), scan_axis=bool(s.get("from_scan"))))
    U = to_mf(pieces[0])
    for p in pieces[1:]:
        U = U + to_mf(p)
    for C in clips:
        U = U ^ C
    info["_ends"] = ends
    return U, info


def build_plug_d39(m, ray, segs):
    """the D39 plug (track 2e): cap plane fitted to a ring just inside the part, or square at the hole end; kept as the
    fallback where the surface-fitted cap does not pass the flush check"""
    a = segs[0]["p1"] - segs[0]["p0"]; a /= np.linalg.norm(a)
    pieces, info = [], dict(ends=[], segs=[])
    for s in segs:
        sa = s["p1"] - s["p0"]; L = np.linalg.norm(sa); sa /= L
        pieces.append(cyl(s["p0"] - sa * END_EXT, s["p1"] + sa * END_EXT, s["d"] / 2 + R_EXTRA))
        info["segs"].append(dict(d=round(s["d"], 2), L=round(L, 2), scan_axis=bool(s.get("from_scan"))))
    U = to_mf(pieces[0])
    for p in pieces[1:]:
        U = U + to_mf(p)
    # open ends along the stack axis
    ts = [((s["p0"] - segs[0]["p0"]) @ a, (s["p1"] - segs[0]["p0"]) @ a, s) for s in segs]
    tmin = min(min(x[0], x[1]) for x in ts); tmax = max(max(x[0], x[1]) for x in ts)
    for tend, sign in ((tmin, -1.0), (tmax, 1.0)):
        a_out = a * sign
        # segment at that end and its radius
        s_end = min(ts, key=lambda x: abs((min(x[0], x[1]) if sign < 0 else max(x[0], x[1])) - tend))
        # widest feature touching that end (counterbore)
        R = max(x[2]["d"] for x in ts if abs(min(x[0], x[1]) - tend) < 0.6 or abs(max(x[0], x[1]) - tend) < 0.6) / 2
        sa = s_end[2]["p1"] - s_end[2]["p0"]; sa /= np.linalg.norm(sa)
        c_axis = segs[0]["p0"] + a * tend
        probe = c_axis + a_out * 0.3
        is_open = not bool(m.contains([probe])[0])
        e = dict(open=is_open, R=round(R, 2))
        if is_open:
            pl = ring_plane(m, ray, c_axis, a_out if abs(sa @ a) > 0.999 else (sa if sa @ a_out > 0 else -sa), R)
            if pl is None:
                pl = dict(c=c_axis - a_out * 0.02, n=a_out, res_max=None, res_pos=None, n_pts=0)
                e["cap"] = "square to the axis at the hole end (ring not flat)"
            e.update(res_max=pl["res_max"], res_pos=pl["res_pos"], n_pts=pl["n_pts"], plane_shift=round(float((pl["c"] - c_axis) @ pl["n"]), 3))
            U = U ^ to_mf(halfspace_box(pl["c"], pl["n"], 400.0))   # keep the plug behind the cap plane
        info["ends"].append(e)
    return U, info


def score(fl):
    """worst flush of a plug's open ends: (fails, dimple + 10 x proud)"""
    fl = [f for f in fl if f and f.get("ok") is not None]
    return (sum(1 for f in fl if not f["ok"]), max([f["dimple_mm"] + 10 * f["proud_mm"] for f in fl], default=0.0))


def choose_plug(m, ray, M_src, segs, overlap=None):
    """the surface-fitted plug, or the D39 plug where that one is flusher (each tried on the part, flush check);
    a plug whose new material overlaps another part at the zero pose (overlap: callback, mm3) is taken last"""
    best = None
    for how, fn in (("surface-fitted cap", build_plug), ("D39 cap (plane or square)", build_plug_d39)):
        U, info = fn(m, ray, segs)
        t = from_mf(M_src + U); rt = trimesh.ray.ray_triangle.RayMeshIntersector(t)
        ends, _ = stack_ends(m, segs)
        fl = [flush_of(t, rt, e) if e["open"] else None for e in ends]
        ov = overlap(U - M_src) if overlap else 0.0
        sc = (ov > 1e-3,) + score(fl)
        info["tried"] = info.get("tried", []) + [dict(how=how, overlap_mm3=round(ov, 4), fails=sc[1], worst=round(sc[2], 3))]
        if best is None or sc < best[0]:
            best = (sc, U, info, how)
        if sc[:2] == (False, 0):
            break
    sc, U, info, how = best
    info["cap_method"] = how
    info.setdefault("_ends", stack_ends(m, segs)[0])
    return U, info


def measure_ends(m, segs, mesh_new, ray_new):
    """flush check of an existing plug (HOLES_MEASURE): hole ends from the hole STL, ring and disk on the plugged one"""
    ends, _ = stack_ends(m, segs)
    return [dict(open=e["open"], R=round(e["R"], 2), flush=flush_of(mesh_new, ray_new, e) if e["open"] else None) for e in ends]


# ---------------------------------------------------------------- ear seats (F2 down, body_back on body_middle_bottom_lip)
def ear_seats(lip_local, T_bmb, back_world, xs=-115.0, x_lo=-116.0, x_hi=-114.0):
    """fill the gap between each lower back shell ear and the lip horseshoe round it, under the ear, down to C_SEAT"""
    from shapely.geometry import Polygon, box as sbox
    from shapely.ops import unary_union
    lipw = lip_local.copy(); lipw.apply_transform(T_bmb)
    def sec(m, x):
        s = m.section(plane_origin=[x, 0, 0], plane_normal=[1, 0, 0])
        if s is None:
            return Polygon()
        R = np.eye(4); R[:3, :3] = np.array([[0, 1.0, 0], [0, 0, 1.0], [1.0, 0, 0]]); R[:3, 3] = [0, 0, -x]
        pl, _ = s.to_planar(to_2D=R, check=False)
        return unary_union([g.buffer(0) for g in pl.polygons_full])
    out, rep = [], []
    B = unary_union([sec(back_world, x) for x in (x_lo + 0.1, xs, x_hi - 0.1)])
    Lp = unary_union([sec(lipw, x) for x in (x_lo + 0.1, xs, x_hi - 0.1)])
    for y0 in (-45.0, 45.0):
        for z0 in (42.6, 2.85):
            win = sbox(y0 - 7, z0 - 7, y0 + 7, z0)          # lower half of the ear window
            lp = Lp.intersection(sbox(y0 - 7, z0 - 7, y0 + 7, z0 + 7))
            if lp.is_empty or lp.area < 2:
                rep.append(dict(ear=[y0, z0], seat="no lip here")); continue
            hull = lp.convex_hull
            fill = hull.intersection(win).difference(B.buffer(C_SEAT)).difference(Lp)
            fill = unary_union([g for g in getattr(fill, "geoms", [fill]) if g.area > 0.3])
            if fill.is_empty:
                rep.append(dict(ear=[y0, z0], seat="no gap to fill")); continue
            seat2d = fill.union(lp.intersection(win)).buffer(0)
            for g in getattr(fill, "geoms", [fill]):
                mm = trimesh.creation.extrude_polygon(g.buffer(0.05), x_hi - x_lo)
                T = np.eye(4); T[:3, 0] = [0, 1.0, 0]; T[:3, 1] = [0, 0, 1.0]; T[:3, 2] = [1.0, 0, 0]; T[:3, 3] = [x_lo, 0, 0]
                mm.apply_transform(T); out.append(mm)
            # capacities (calc only): bearing on the ear's lower outline, shear at the seat root (x = -114 plane)
            under = B.intersection(sbox(y0 - 7, z0 - 7, y0 + 7, z0)).buffer(C_SEAT + 0.05).intersection(seat2d.buffer(0.05))
            yb = under.bounds if not under.is_empty else (0, 0, 0, 0)
            bear_w = yb[2] - yb[0]
            root = seat2d.area
            gap0 = lp.intersection(win).distance(B.intersection(win)) if not lp.intersection(win).is_empty else None
            rep.append(dict(ear=[y0, z0], gap_before_mm=round(gap0, 2) if gap0 is not None else None, fill_mm2=round(fill.area, 1),
                            seat_root_mm2=round(root, 1), bearing_width_mm=round(bear_w, 1), depth_mm=round(x_hi - x_lo, 1),
                            bearing_N=round(bear_w * (x_hi - x_lo) * 47.1, 0), root_shear_N=round(root * 12.7, 0),
                            capacity_N=round(min(bear_w * (x_hi - x_lo) * 47.1, root * 12.7), 0)))
    return out, rep


def separate_pinches(V, Fc, eps=0.001):
    """manifold output can hold 2 vertices at one point (two sheets touching); an STL merges them by position.
    Move every extra copy 1 micron into its own sheet so the file stays watertight when read back."""
    key = np.round(V, 6)
    _, inv, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True)
    dup = np.where(cnt[inv] > 1)[0]
    if len(dup) == 0:
        return V, 0
    tm = trimesh.Trimesh(V, Fc, process=False)
    vn = tm.vertex_normals
    seen = set(); V = V.copy(); n = 0
    for i in dup:
        k = inv[i]
        if k in seen:
            V[i] -= vn[i] * eps; n += 1
        else:
            seen.add(k)
    return V, n


# ---------------------------------------------------------------- main
def other_parts_near(bounds_w, skip):
    out = []
    for i in inst:
        if i["idx"] in skip:
            continue
        b = S.mesh(i["idx"]).bounds
        if np.all(b[0] <= bounds_w[1] + 1.0) and np.all(b[1] >= bounds_w[0] - 1.0):
            out.append(i["idx"])
    return out


MF_CACHE = {}


def plug_overlap(A, src):
    """mm3 of new plug material (manifold, STL frame) inside any other part, every instance of the STL, zero pose"""
    a = from_mf(A)
    if a.volume < 1e-6:
        return 0.0
    tot = 0.0
    for i in inst:
        if i["src"] != src:
            continue
        aw = a.copy(); aw.apply_transform(i["T"])
        if i["mirror"]:
            aw.invert()
        Maw = to_mf(aw)
        for k in other_parts_near(aw.bounds, {i["idx"]}):
            if k not in MF_CACHE:
                om = S.mesh(k)
                try:
                    mk = to_mf(om); MF_CACHE[k] = mk if abs(mk.volume() - om.volume) < 1e-3 * abs(om.volume) + 1e-3 else None
                except Exception:
                    MF_CACHE[k] = None
            if MF_CACHE[k] is not None:
                tot += (Maw ^ MF_CACHE[k]).volume()
    return float(tot)


cab = []
for c in C3["cables"]:
    P = np.array([p["p"] for p in c["points"]], float)
    if len(P) >= 2:
        n = [max(1, int(np.linalg.norm(b - a) / 0.5)) for a, b in zip(P[:-1], P[1:])]
        Q = np.vstack([a + (b - a) * np.linspace(0, 1, k, endpoint=False)[:, None] for a, b, k in zip(P[:-1], P[1:], n)] + [P[-1:]])
        cab.append((c["id"], Q, float(c.get("d_mm") or 2.0) / 2))
drill = [np.array(r["center_mm"], float) for r in C3["retention"] if r["kind"] == "drilled printed feature"]

report = dict(parts={}, holes=[], seats=None, conflicts=[])
srcs = sorted(by_src)
twin_map = {"body_front": "body_front_groove", "body_middle_top": "body_middle_top_lip", "body_middle_bottom": "body_middle_bottom_lip"}
jobs = [(src, src, None) for src in srcs]
for k, v in twin_map.items():
    jobs.append((os.path.join(hlib.REPO, "print", k + ".stl"), os.path.join(hlib.LAB, "twin", "screws", "stl", v + ".stl"), v))

for src, mesh_path, twin_name in jobs:
    name = twin_name or os.path.splitext(os.path.basename(src))[0]
    src_rel = os.path.relpath(src, hlib.REPO)
    L = local_holes(src)
    close, keep = [], []
    for g in L:
        decs = {h["decision"] for h in g}
        if decs == {"close"}:
            close.append(g)
        else:
            keep.append(g)
            if "close" in decs:
                report["conflicts"].append(dict(stl=name, holes=[(h["site"], h["inst"], h["decision"], h["why"]) for h in g]))
    for g in L:
        for h in g:
            report["holes"].append(dict(stl=name, site=h["site"], inst=h["inst"], part=h["part"], decision="close" if g in close else "keep",
                                        why=h["why"] if g in close or h["decision"] == "keep" else "kept: another instance uses it (%s)" % "; ".join(x["why"] for x in g if x["decision"] == "keep"),
                                        d=[round(s["d"], 2) for s in h["segs"]], centre_world=h["centre_world"], users=h["users"]))
    seats = None
    if not close and name != "body_middle_bottom_lip":
        continue
    m = trimesh.load(mesh_path, force="mesh"); m.merge_vertices()
    V0 = float(m.volume)
    if not m.is_watertight or abs(to_mf(m).volume() - V0) > 1e-3 * V0:
        print("SOURCE NOT MANIFOLD", name, m.is_watertight)
    ray = trimesh.ray.ray_triangle.RayMeshIntersector(m)
    if MEASURE:
        mp = os.path.join(MEASURE, os.path.relpath(mesh_path, hlib.REPO))
        mn = trimesh.load(mp, force="mesh"); rn = trimesh.ray.ray_triangle.RayMeshIntersector(mn)
        infos = [dict(site=g[0]["site"], why=g[0]["why"], ends=measure_ends(m, [true_seg(src_rel, s) for s in g[0]["segs"]], mn, rn)) for g in close]
        report["parts"][name] = dict(stl=name, measured=os.path.relpath(mp, MEASURE), n_closed=len(close), plugs=infos)
        bad = [(i["site"], e["flush"]) for i in infos for e in i["ends"] if e["open"] and not e["flush"].get("ok")]
        print("%-24s measured %2d plugs, off: %s" % (name, len(close), bad), flush=True)
        continue
    plugs, infos = [], []
    M_src = to_mf(m)
    for g in close:
        segs = [true_seg(src_rel, s) for s in g[0]["segs"]]
        U, info = choose_plug(m, ray, M_src, segs, overlap=(lambda A, src=src: plug_overlap(A, src)) if not twin_name else None)
        info.update(site=g[0]["site"], why=g[0]["why"], analytic_mm3=round(sum(np.pi * (s["d"] / 2) ** 2 * np.linalg.norm(s["p1"] - s["p0"]) for s in segs), 1))
        plugs.append(U); infos.append(info)
    M = to_mf(m)
    if name == "body_middle_bottom_lip":
        Tb = [i["T"] for i in inst if i["key"] == "body_middle_bottom"][0]
        back = S.mesh([i["idx"] for i in inst if i["key"] == "body_back"][0])
        boxes, srep = ear_seats(m, Tb, back)
        Ti = np.linalg.inv(Tb)
        for b in boxes:
            b.apply_transform(Ti); M = M + to_mf(b)
        seats = srep
        report["seats"] = srep
    Pall = None
    for U in plugs:
        Pall = U if Pall is None else Pall + U
    if Pall is not None:
        M = M + Pall
    new = from_mf(M, clean=True)
    V1 = float(new.volume)
    out = os.path.join(OUT_STL, name + ".stl")
    new.export(out)
    rb = trimesh.load(out); eu, ec = np.unique(rb.edges_sorted, axis=0, return_counts=True)
    ray_new = trimesh.ray.ray_triangle.RayMeshIntersector(rb)
    for info in infos:
        for rec, e in zip(info["ends"], info.pop("_ends")):
            if e["open"]:
                rec["flush"] = flush_of(rb, ray_new, e)
    reread = dict(watertight=bool(rb.is_watertight), open_edges=int((ec == 1).sum()), nonmanifold_edges=int((ec > 2).sum()))
    es, esc = np.unique(m.edges_sorted, axis=0, return_counts=True)
    src_edges = dict(open_edges=int((esc == 1).sum()), nonmanifold_edges=int((esc > 2).sum()))
    added = from_mf(M - to_mf(m)) if (Pall is not None or seats) else None
    # zero-pose overlap and clearances, every instance of this STL
    over = []
    for i in inst:
        if i["src"] != src or added is None or twin_name and i["key"] not in twin_map:
            continue
        aw = added.copy(); aw.apply_transform(i["T"])
        if i["mirror"]:
            aw.invert()
        Pq = np.vstack([aw.vertices, trimesh.sample.sample_surface(aw, 3000, seed=3)[0]]) if aw.area > 0 else aw.vertices
        Maw = to_mf(aw)
        for k in other_parts_near(aw.bounds, {i["idx"]}):
            om = S.mesh(k)
            if k not in MF_CACHE:
                try:
                    mk = to_mf(om); MF_CACHE[k] = mk if abs(mk.volume() - om.volume) < 1e-3 * abs(om.volume) + 1e-3 else None
                except Exception:
                    MF_CACHE[k] = None
            mk = MF_CACHE[k]
            if mk is not None:
                vol = (Maw ^ mk).volume()
                if vol > 1e-3:
                    over.append(dict(inst=i["idx"], other=inst[k]["key"], overlap_mm3=round(float(vol), 4)))
            else:
                b = om.bounds; sel = np.all((Pq > b[0] - 0.1) & (Pq < b[1] + 0.1), axis=1)
                if sel.any() and om.contains(Pq[sel]).any():
                    over.append(dict(inst=i["idx"], other=inst[k]["key"], points_inside=int(om.contains(Pq[sel]).sum()), test="contains (not manifold)"))
        bb0, bb1 = aw.bounds[0] - 10, aw.bounds[1] + 10
        cmin = None
        for _, Q, rr in cab:
            q = Q[np.all((Q > bb0) & (Q < bb1), axis=1)]
            if len(q):
                dd = float(np.min(np.linalg.norm(q[:, None, :] - Pq[None, ::5, :], axis=2))) - rr
                cmin = dd if cmin is None else min(cmin, dd)
        dmin = min((float(np.min(np.linalg.norm(Pq - d, axis=1))) for d in drill), default=None)
        over.append(dict(inst=i["idx"], cable_clear_mm=None if cmin is None else round(cmin, 2), drilled_tie_spot_mm=None if dmin is None else round(dmin, 1)))
    # distance from each plug to the kept holes of this STL
    kd = []
    for info, g in zip(infos, close):
        c = np.mean([(s["p0"] + s["p1"]) / 2 for s in g[0]["segs"]], axis=0); rp = max(s["d"] for s in g[0]["segs"]) / 2 + R_EXTRA
        best = 1e9
        for kg in keep:
            for s in kg[0]["segs"]:
                sa = s["p1"] - s["p0"]; Ls = np.linalg.norm(sa); sa /= Ls
                v = c - s["p0"]; t = np.clip(v @ sa, 0, Ls)
                best = min(best, float(np.linalg.norm(v - t * sa)) - rp - s["d"] / 2)
        info["kept_hole_gap_mm"] = round(best, 2) if best < 1e8 else None
    rp = dict(stl=name, src=os.path.relpath(mesh_path, hlib.REPO), out=out, bytes=os.path.getsize(out),
              watertight=reread["watertight"], reread=reread, source_edges=src_edges, volume_mm3=[round(V0, 1), round(V1, 1)], added_mm3=round(V1 - V0, 1),
              analytic_hole_mm3=round(sum(i["analytic_mm3"] for i in infos), 1), n_closed=len(close), n_kept=len(keep),
              bounds_same=bool(np.allclose(new.bounds, m.bounds, atol=0.02)), plugs=infos, zero_pose=over, seats=seats)
    report["parts"][name] = rp
    fl = [e["flush"] for i in infos for e in i["ends"] if e.get("flush") and e["flush"].get("ok") is not None]
    sq = sum(1 for i in infos for e in i["ends"] if e["open"] and e["flush"].get("ok") is None)
    print("%-24s closed %2d kept %3d dV %7.1f (holes %7.1f) reread %s src %s bounds_same %s dimple<=%s proud<=%s off %d square %d overlaps %s" % (
        name, len(close), len(keep), V1 - V0, rp["analytic_hole_mm3"], reread, src_edges, rp["bounds_same"],
        max([f["dimple_mm"] for f in fl], default="-"), max([f["proud_mm"] for f in fl], default="-"), sum(1 for f in fl if not f["ok"]), sq,
        [o for o in over if "other" in o][:3]), flush=True)
# per-instance variants of a shared STL whose instances leave different holes empty (D18: roll_motor_bottom)
for src in [s for s in srcs if s.endswith("roll_motor_bottom.stl")]:
    L = local_holes(src)
    m = trimesh.load(src, force="mesh"); m.merge_vertices(); ray = trimesh.ray.ray_triangle.RayMeshIntersector(m)
    for i in [i for i in inst if i["src"] == src]:
        tag = "L" if i["T"][1, 3] > 0 else "R"
        close = [g for g in L if any(h["inst"] == i["idx"] and h["decision"] == "close" for h in g)]
        M = to_mf(m); infos = []
        if MEASURE:
            mp = os.path.join(os.environ.get("HOLES_MEASURE_OPT", os.path.join(MEASURE, "print")), "roll_motor_bottom_%s.stl" % tag)   # optional STLs, not in the repo
            if os.path.exists(mp):
                mn = trimesh.load(mp, force="mesh"); rn = trimesh.ray.ray_triangle.RayMeshIntersector(mn)
                infos = [dict(site=g[0]["site"], why=g[0]["why"], ends=measure_ends(m, [true_seg(os.path.relpath(src, hlib.REPO), s) for s in g[0]["segs"]], mn, rn)) for g in close]
            report["parts"]["roll_motor_bottom_" + tag] = dict(stl="roll_motor_bottom_" + tag, measured=mp if os.path.exists(mp) else "not in the repo", plugs=infos)
            continue
        for g in close:
            U, info = choose_plug(m, ray, to_mf(m), [true_seg(os.path.relpath(src, hlib.REPO), s) for s in g[0]["segs"]])
            info.update(site=g[0]["site"], why=g[0]["why"]); infos.append(info); M = M + U
        new = from_mf(M, clean=True); out = os.path.join(OUT_STL, "roll_motor_bottom_%s.stl" % tag); new.export(out)
        rb = trimesh.load(out); eu, ec = np.unique(rb.edges_sorted, axis=0, return_counts=True)
        rn = trimesh.ray.ray_triangle.RayMeshIntersector(rb)
        for info in infos:
            for rec, e in zip(info["ends"], info.pop("_ends")):
                rec["flush"] = flush_of(rb, rn, e) if e["open"] else None
        aw = from_mf(M - to_mf(m)); aw.apply_transform(i["T"]); Maw = to_mf(aw); ov = []
        for k in other_parts_near(aw.bounds, {i["idx"]}):
            try:
                mk = to_mf(S.mesh(k)); vol = (Maw ^ mk).volume()
                if vol > 1e-3: ov.append((inst[k]["key"], round(vol, 4)))
            except Exception as ex:
                ov.append((inst[k]["key"], "not checked: %s" % ex))
        report["parts"]["roll_motor_bottom_" + tag] = dict(stl="roll_motor_bottom_" + tag, inst=i["idx"], out=out, bytes=os.path.getsize(out),
            watertight=bool(rb.is_watertight), nonmanifold_edges=int((ec > 2).sum()), volume_mm3=[round(m.volume, 1), round(new.volume, 1)],
            added_mm3=round(new.volume - m.volume, 1), n_closed=len(close), plugs=infos, zero_pose=ov, bounds_same=bool(np.allclose(new.bounds, m.bounds, atol=0.02)))
        print("roll_motor_bottom_%s inst %d closed %d dV %.1f watertight %s overlaps %s" % (tag, i["idx"], len(close), new.volume - m.volume, rb.is_watertight, ov))
hlib.jdump(report, "measure_%s.json" % STAGE if MEASURE else "close_report.json")
print("conflicts", len(report["conflicts"]))
for c in report["conflicts"]:
    print("  ", c["stl"], [(h[0], h[1], h[2], h[3][:60]) for h in c["holes"]])
print("seats", json.dumps(report["seats"]))
