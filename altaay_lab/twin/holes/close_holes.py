"""Stage 3: close every hole that nothing uses, in the printed STLs (CAD check only).

Decision per hole (site x instance, data/sites_raw.json): kept when a fitted screw or insert uses it (seat, pass,
anchor, pilot, bore, or screwdriver access), or for light, sound, camera, vent or grille, bearing, antenna rod, a
cable or a tie; closed otherwise. An STL that serves several instances closes a hole only if every instance leaves
it unused. Plugs, in the STL frame (the print/ frame, so orientation and supports stay):
  - one cylinder per feature of the hole (its own axis and diameter; the mesh scan gives the true axis where the
    site axis is a few degrees off), radius + 0.15 mm so it overlaps the wall, ends extended 0.3 mm;
  - each open end is cut by a plane fitted to the part surface on a ring just outside the hole (or its
    counterbore), so the plug is flush; a blind end stops in the material;
  - the part is unioned with the plugs (manifold3d), so new material lies only in the old hole.
Checks: watertight, volume added against the analytic hole volume, flush residual (cap plane against the ring
surface), overlap of the added material with every other part at the zero pose, distance to kept holes, cables
and the drilled tie spots. Also the 4 seats under the lower back shell ears on body_middle_bottom_lip (F2 down).
Writes <OUT>/stl/*.stl and <OUT>/data/close_report.json (OUT: hlib.py).
"""
import json, os, sys, collections, glob
import numpy as np, trimesh, manifold3d
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hlib

OUT_STL = os.path.join(hlib.OUT, "stl")
os.makedirs(OUT_STL, exist_ok=True)
R_EXTRA, END_EXT, C_SEAT = 0.15, 0.3, 0.25
NEW_CUT = {"F076", "F178", "F183"}   # F076: one more pass (body_back 7 -> 6 with the ear seats); F178, F183: the left eye
RESTORE = {"F179", "F182"}           # keeps the other diagonal so both bulbs (one STL, mirrored) cut the same 2 STL holes
S = hlib.scene()
FJ = hlib.load_fj(); F = FJ["fasteners"]; FID = {f["id"]: f for f in F}
ins_of = {f["screw"]: f["id"] for f in F if f["kind"] == "insert"}
NEW_CUT |= {ins_of[s] for s in list(NEW_CUT) if s in ins_of}
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
        return "close", "no screw: " + ",".join("%s %s" % (u["id"], "(one more pass)" if u["id"] in NEW_CUT else "(%s)" % (u.get("status") or "")) for u in cut)
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


def build_plug(m, ray, segs):
    """segs: local features of one hole stack; returns (plug manifold, info)"""
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


cab = []
for c in C3["cables"]:
    P = np.array([p["p"] for p in c["points"]], float)
    if len(P) >= 2:
        n = [max(1, int(np.linalg.norm(b - a) / 0.5)) for a, b in zip(P[:-1], P[1:])]
        Q = np.vstack([a + (b - a) * np.linspace(0, 1, k, endpoint=False)[:, None] for a, b, k in zip(P[:-1], P[1:], n)] + [P[-1:]])
        cab.append((c["id"], Q, float(c.get("d_mm") or 2.0) / 2))
drill = [np.array(r["center_mm"], float) for r in C3["retention"] if r["kind"] == "drilled printed feature"]

report = dict(parts={}, holes=[], seats=None, conflicts=[])
MF_CACHE = {}
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
    plugs, infos = [], []
    for g in close:
        segs = [true_seg(src_rel, s) for s in g[0]["segs"]]
        U, info = build_plug(m, ray, segs)
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
    flush = [e["res_pos"] for i in infos for e in i["ends"] if e.get("res_pos") is not None]
    rec = [e["res_max"] for i in infos for e in i["ends"] if e.get("res_max") is not None]
    print("%-24s closed %2d kept %3d dV %7.1f (holes %7.1f) reread %s src %s bounds_same %s recess<=%s overlaps %s" % (
        name, len(close), len(keep), V1 - V0, rp["analytic_hole_mm3"], reread, src_edges, rp["bounds_same"],
        round(max(rec) + 0.02, 3) if rec else "-", [o for o in over if "other" in o][:3]), flush=True)
# per-instance variants of a shared STL whose instances leave different holes empty (D18: roll_motor_bottom)
for src in [s for s in srcs if s.endswith("roll_motor_bottom.stl")]:
    L = local_holes(src)
    m = trimesh.load(src, force="mesh"); m.merge_vertices(); ray = trimesh.ray.ray_triangle.RayMeshIntersector(m)
    for i in [i for i in inst if i["src"] == src]:
        tag = "L" if i["T"][1, 3] > 0 else "R"
        close = [g for g in L if any(h["inst"] == i["idx"] and h["decision"] == "close" for h in g)]
        M = to_mf(m); infos = []
        for g in close:
            U, info = build_plug(m, ray, [true_seg(os.path.relpath(src, hlib.REPO), s) for s in g[0]["segs"]])
            info.update(site=g[0]["site"], why=g[0]["why"]); infos.append(info); M = M + U
        new = from_mf(M, clean=True); out = os.path.join(OUT_STL, "roll_motor_bottom_%s.stl" % tag); new.export(out)
        rb = trimesh.load(out); eu, ec = np.unique(rb.edges_sorted, axis=0, return_counts=True)
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
hlib.jdump(report, "close_report.json")
print("conflicts", len(report["conflicts"]))
for c in report["conflicts"]:
    print("  ", c["stl"], [(h[0], h[1], h[2], h[3][:60]) for h in c["holes"]])
print("seats", json.dumps(report["seats"]))
