"""Shared code for altaay_lab/cables3d: robot scene (URDF posing in mm), 1 mm occupancy grid with a distance field,
clear-path router and a small numpy rasterizer for the PNGs (this machine has no OpenGL).

Frames: URDF world at the zero pose, x forward, y left, z up, mm. Link frames are yourdfpy link transforms (x1000).
Inputs (read-only): mini_bdx/robots/open_duck_mini_v2/robot.urdf and meshes (Open_Duck_Mini b23317a), print/*.stl.
"""
import os
import json
import numpy as np
import trimesh
import yourdfpy
from scipy import ndimage
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra


# ---------------------------------------------------------------- scene
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # altaay_lab/cables3d -> repo
URDF_DIR = os.path.join(REPO, "mini_bdx", "robots", "open_duck_mini_v2")
PRINT_DIR = os.path.join(REPO, "print")
LAB = os.path.join(REPO, "altaay_lab")

HEAD_INTERNALS = ["left_eye", "right_eye", "bulb", "bulb", "flash_light_module",
                  "flash_reflector_interface", "speaker_stand", "speaker_interface"]
CASE = {"wj-wk00-0122topcabinetcase_95.stl": "servo_top", "wj-wk00-0123middlecase_56.stl": "servo_mid",
        "wj-wk00-0124bottomcase_45.stl": "servo_bottom"}


def mm(T):
    T = np.array(T, float).copy()
    T[:3, 3] *= 1000.0
    return T


class Scene:
    def __init__(self, use_print=True):
        self.u = yourdfpy.URDF.load(os.path.join(URDF_DIR, "robot.urdf"), load_meshes=False, build_scene_graph=True)
        self.joints = {}
        for j in self.u.robot.joints:
            if j.type == "revolute":
                self.joints[j.name] = dict(parent=j.parent, child=j.child, lo=float(j.limit.lower), hi=float(j.limit.upper),
                                           axis=np.asarray(j.axis, float))
        self.zero = {n: 0.0 for n in self.u.actuated_joint_names}
        self.u.update_cfg(self.zero)
        self.T0 = {ln: mm(self.u.get_transform(ln)) for ln in self.u.link_map}
        self.print_files = {os.path.splitext(f)[0] for f in os.listdir(PRINT_DIR) if f.endswith(".stl")}
        self._mesh = {}
        self.inst = []   # dict(link, key, file, T_link (mm), printed)
        for ln, link in self.u.link_map.items():
            for v in link.visuals:
                fn = os.path.basename(v.geometry.mesh.filename)
                Tv = mm(v.origin if v.origin is not None else np.eye(4))
                stem = os.path.splitext(fn)[0]
                key, path, scale = stem, os.path.join(URDF_DIR, fn), 1000.0
                if use_print:
                    for s in (stem, stem.replace("left_", "", 1), stem.replace("right_", "", 1)):
                        if s in self.print_files:
                            key, path, scale = s, os.path.join(PRINT_DIR, s + ".stl"), 1.0
                            break
                if fn in CASE:
                    key = CASE[fn]
                self.inst.append(dict(link=ln, key=key, urdf=fn, path=path, scale=scale, T=Tv,
                                      printed=path.startswith(PRINT_DIR)))
        # head internals: modelled in the head.stl frame
        th = [i for i in self.inst if i["key"] == "head"][0]
        seen = {}
        for stem in HEAD_INTERNALS:
            seen[stem] = seen.get(stem, 0) + 1
            M = np.diag([1.0, -1.0, 1.0, 1.0]) if seen[stem] == 2 else np.eye(4)
            self.inst.append(dict(link=th["link"], key=stem, urdf=None, path=os.path.join(PRINT_DIR, stem + ".stl"),
                                  scale=1.0, T=th["T"] @ M, printed=True, mirrored=seen[stem] == 2))
        for k, i in enumerate(self.inst):
            i["idx"] = k

    def mesh(self, i):
        """local mesh (mm) of instance i, cached by path"""
        p = i["path"]
        if p not in self._mesh:
            m = trimesh.load(p, force="mesh")
            if i["scale"] != 1.0:
                m.apply_scale(i["scale"])
            self._mesh[p] = m
        return self._mesh[p]

    def world_mesh(self, i, Tl=None):
        Tl = self.T0 if Tl is None else Tl
        m = self.mesh(i).copy()
        T = Tl[i["link"]] @ i["T"]
        if i.get("mirrored"):
            m.invert()      # keep normals outward after the mirror
        m.apply_transform(T)
        return m

    def link_T(self, cfg):
        c = dict(self.zero)
        c.update(cfg)
        self.u.update_cfg(c)
        out = {ln: mm(self.u.get_transform(ln)) for ln in self.u.link_map}
        self.u.update_cfg(self.zero)
        return out

    def joint_world(self, name, Tl=None):
        """joint origin and axis in world at the given link transforms (default zero pose)"""
        Tl = self.T0 if Tl is None else Tl
        j = self.joints[name]
        Tc = Tl[j["child"]]
        return Tc[:3, 3].copy(), Tc[:3, :3] @ j["axis"]

    def servos(self):
        """one dict per servo: joint, link, case transform (case STL frame -> link frame), ports"""
        out = []
        cases = [i for i in self.inst if i["key"] == "servo_bottom"]
        horns = [i for i in self.inst if i["urdf"] == "drive_palonier.stl"]
        for c in cases:
            Tw = self.T0[c["link"]] @ c["T"]
            # case frame: horn axis along local y at x = -25.5, z = 0 (measured on the case meshes)
            hc = (Tw @ np.array([-25.5, 7.0, 0.0, 1.0]))[:3]
            ax = Tw[:3, :3] @ np.array([0, 1.0, 0])
            best = None
            for jn, j in self.joints.items():
                if "antenna" in jn or c["link"] not in (j["parent"], j["child"]):
                    continue
                p, a = self.joint_world(jn)
                d = hc - p
                off = np.linalg.norm(d - np.dot(d, a) * a)
                par = abs(np.dot(a, ax))
                score = (round(off, 1), np.linalg.norm(d))
                if par > 0.99 and (best is None or score < best[0]):
                    best = (score, jn)
            out.append(dict(joint=best[1] if best else None, link=c["link"], T_case_link=c["T"], idx=c["idx"]))
        return out


# ---------------------------------------------------------------- grid
PITCH = 1.0
SERVO_INNER = ((-35.0, 9.0), (-24.0, 4.8), (-11.8, 11.8))   # case-frame box filled solid (inside the cups)
TRUNK_SHELL = {"body_front", "body_back", "body_middle_bottom", "body_middle_top", "trunk_top", "trunk_bottom",
               "battery_pack_lid"}
HEAD_SHELL = {"head", "head_bot_sheet"}


def box_mesh(center, dims, R=None):
    b = trimesh.creation.box(extents=dims)
    T = np.eye(4)
    if R is not None:
        T[:3, :3] = R
    T[:3, 3] = center
    b.apply_transform(T)
    return b


class Grid:
    def __init__(self, lo, shape, links):
        self.lo = np.asarray(lo, float)
        self.shape = tuple(int(x) for x in shape)
        self.links = list(links)
        self.label = np.zeros(self.shape, np.uint8)
        self.edt = None

    def idx(self, P):
        return np.floor((np.atleast_2d(P) - self.lo) / PITCH).astype(np.int64)

    def centre(self, I):
        return self.lo + (np.asarray(I) + 0.5) * PITCH

    def inside(self, I):
        I = np.atleast_2d(I)
        return np.all((I >= 0) & (I < np.array(self.shape)), axis=1)

    def mark_points(self, pts, lab):
        I = self.idx(pts)
        ok = self.inside(I)
        I = I[ok]
        self.label[I[:, 0], I[:, 1], I[:, 2]] = lab

    def mark_mesh(self, m, lab, fill=True):
        """surface voxels (subdivision vertices) plus every voxel whose centre is inside the watertight mesh"""
        if np.any(m.bounds[1] < self.lo) or np.any(m.bounds[0] > self.lo + np.array(self.shape) * PITCH):
            return
        self.mark_points(m.voxelized(pitch=PITCH).points, lab)
        if fill and m.is_watertight:
            lo = np.floor((m.bounds[0] - self.lo) / PITCH).astype(int)
            hi = np.ceil((m.bounds[1] - self.lo) / PITCH).astype(int)
            lo, hi = np.maximum(lo, 0), np.minimum(hi, np.array(self.shape))
            gx, gy, gz = [self.lo[a] + (np.arange(lo[a], hi[a]) + 0.5) * PITCH for a in range(3)]
            for k0 in range(0, len(gx), 20):        # chunks along x to bound memory
                X, Y, Z = np.meshgrid(gx[k0:k0 + 20], gy, gz, indexing="ij")
                P = np.c_[X.ravel(), Y.ravel(), Z.ravel()]
                inside = m.contains(P)
                if inside.any():
                    self.mark_points(P[inside], lab)

    def finish(self):
        """distance field of the free voxels (mm)"""
        self.edt = ndimage.distance_transform_edt(self.label == 0, sampling=PITCH).astype(np.float32)

    def overlay(self, boxes, clear=()):
        """copy with cleared world boxes ((lo xyz), (hi xyz)), extra solid boxes (link, centre, dims, R, key) and a
        fresh distance field"""
        g = Grid(self.lo, self.shape, self.links)
        g.label = self.label.copy()
        for lo_, hi_ in clear:
            a = np.maximum(np.floor((np.asarray(lo_) - self.lo) / PITCH).astype(int), 0)
            b = np.minimum(np.ceil((np.asarray(hi_) - self.lo) / PITCH).astype(int), np.array(self.shape))
            g.label[a[0]:b[0], a[1]:b[1], a[2]:b[2]] = 0
        for ln, c, d, R, key in boxes:
            g.mark_mesh(box_mesh(c, d, R), 1 + self.links.index(ln), fill=True)
        g.finish()
        for k in ("trunk_in", "head_in", "trunk_hull", "head_hull"):
            if hasattr(self, k):
                setattr(g, k, getattr(self, k))
        return g

    def sample(self, P, field=None):
        """trilinear sample of edt (or a given field) at world points"""
        F = self.edt if field is None else field
        q = (np.atleast_2d(P) - self.lo) / PITCH - 0.5
        return ndimage.map_coordinates(F, q.T, order=1, mode="nearest")


def build(scene, extra_boxes=(), cache=None):
    """zero-pose grid of every scene instance (plus extra boxes). Cached as .npz when cache is given."""
    keys = ("trunk_in", "head_in", "trunk_hull", "head_hull")
    if cache and os.path.exists(cache):
        z = np.load(cache, allow_pickle=True)
        g = Grid(z["lo"], z["label"].shape, [str(x) for x in z["links"]])
        g.label = z["label"]
        g.edt = z["edt"]
        for k in keys:
            if k in z:
                setattr(g, k, z[k])
        return g
    W = [scene.world_mesh(i) for i in scene.inst]
    lo = np.floor(np.min([m.bounds[0] for m in W], 0) - 12) - 0.5   # voxel centres on integer mm, as trimesh's
    hi = np.max([m.bounds[1] for m in W], 0) + 12
    shape = np.ceil((hi - lo) / PITCH).astype(int)
    links = sorted(scene.T0)
    g = Grid(lo, shape, links)
    for i, m in zip(scene.inst, W):
        lab = 1 + links.index(i["link"])
        g.mark_mesh(m, lab, fill=True)
        if i["key"] == "servo_bottom":       # the case meshes are cups: fill the servo body
            T = scene.T0[i["link"]] @ i["T"]
            (x0, x1), (y0, y1), (z0, z1) = SERVO_INNER
            c = np.array([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2, 1.0])
            g.mark_mesh(box_mesh((T @ c)[:3], (x1 - x0, y1 - y0, z1 - z0), T[:3, :3]), lab, fill=True)
    for ln, c, d, R, key in extra_boxes:
        g.mark_mesh(box_mesh(c, d, R), 1 + links.index(ln), fill=True)
    g.finish()
    # interiors: (a) enclosed by the shell voxels on all 6 axis rays, (b) inside the convex hull of the shells
    from scipy.spatial import Delaunay
    for name, keys_ in (("trunk", TRUNK_SHELL), ("head", HEAD_SHELL)):
        shells = [m for i, m in zip(scene.inst, W) if i["key"] in keys_]
        sh = np.zeros(g.shape, bool)
        for m in shells:
            I = g.idx(m.voxelized(pitch=PITCH).points)
            I = I[g.inside(I)]
            sh[I[:, 0], I[:, 1], I[:, 2]] = True
        enc = np.ones(g.shape, bool)
        for ax in range(3):
            c = np.cumsum(sh, axis=ax, dtype=np.int32)
            tot = np.take(c, [-1], axis=ax)
            enc &= (c > 0) & ((tot - c) > 0)
        setattr(g, name + "_in", enc)
        hull = trimesh.util.concatenate(shells).convex_hull
        tri = Delaunay(hull.vertices)
        b0 = np.maximum(np.floor((hull.bounds[0] - g.lo) / PITCH).astype(int), 0)
        b1 = np.minimum(np.ceil((hull.bounds[1] - g.lo) / PITCH).astype(int), np.array(g.shape))
        hm = np.zeros(g.shape, bool)
        gx, gy, gz = [g.lo[a] + (np.arange(b0[a], b1[a]) + 0.5) * PITCH for a in range(3)]
        for k0 in range(0, len(gx), 25):
            X, Y, Z = np.meshgrid(gx[k0:k0 + 25], gy, gz, indexing="ij")
            P = np.c_[X.ravel(), Y.ravel(), Z.ravel()]
            hm[b0[0] + k0:b0[0] + k0 + X.shape[0], b0[1]:b1[1], b0[2]:b1[2]] = (tri.find_simplex(P) >= 0).reshape(X.shape)
        setattr(g, name + "_hull", hm)
    if cache:
        np.savez_compressed(cache, lo=g.lo, label=g.label, edt=g.edt, links=np.array(links),
                            **{k: getattr(g, k) for k in keys})
    return g


# ---------------------------------------------------------------- router
OFFS = np.array([(i, j, k) for i in (-1, 0, 1) for j in (-1, 0, 1) for k in (-1, 0, 1)
                 if (i, j, k) > (0, 0, 0)])          # 13 forward offsets (undirected graph)


def seg_clear(g, a, b, clr, mask_fn=None, step=0.5):
    """True if every sample on a-b has edt >= clr (and passes mask_fn)"""
    a, b = np.asarray(a, float), np.asarray(b, float)
    n = max(2, int(np.linalg.norm(b - a) / step) + 1)
    P = a + (b - a) * np.linspace(0, 1, n)[:, None]
    if g.sample(P).min() < clr:
        return False
    if mask_fn is not None and not mask_fn(P).all():
        return False
    return True


def route(g, S, E, clr, margin=30.0, wall=(3.0, 12.0, 0.6), grow=(30.0, 60.0, 100.0, 150.0),
          free_radius=4.0, near_labels=(), near_mm=16.0, hulls=()):
    """Shortest clear path S -> E (world mm). Domain: free voxels with edt >= clr that are inside one of `hulls`
    (full-grid bool masks) or within near_mm of a solid whose label is in near_labels.
    wall = (preferred gap above clearance, distance where the penalty saturates, weight). Returns a polyline or None."""
    S, E = np.asarray(S, float), np.asarray(E, float)
    for m in (margin,) + tuple(x for x in grow if x > margin):
        lo = np.maximum(np.floor((np.minimum(S, E) - m - g.lo)).astype(int), 0)
        hi = np.minimum(np.ceil((np.maximum(S, E) + m - g.lo)).astype(int), np.array(g.shape))
        sub = tuple(slice(lo[a], hi[a]) for a in range(3))
        D = g.edt[sub]
        shp = D.shape
        dom = np.zeros(shp, bool)
        for h in hulls:
            dom |= h[sub]
        if len(near_labels):
            own = np.isin(g.label[sub], np.asarray(near_labels))
            if own.any():
                dom |= ndimage.distance_transform_edt(~own) <= near_mm
        ok = (D >= clr) & dom
        iS = np.floor(S - g.lo).astype(int) - lo
        iE = np.floor(E - g.lo).astype(int) - lo
        if not ((0 <= iS).all() and (iS < shp).all() and (0 <= iE).all() and (iE < shp).all()):
            continue
        r = int(np.ceil(free_radius))
        snapped = []
        for c in (iS, iE):          # the ends may sit inside the clearance zone; a solid end voxel snaps to free
            sl = tuple(slice(max(0, c[a] - r), min(shp[a], c[a] + r + 1)) for a in range(3))
            ok[sl] |= D[sl] > 0.0
            if not ok[tuple(c)]:
                cand = np.argwhere(ok[sl]) + np.array([s_.start for s_ in sl])
                if not len(cand):
                    return None
                c = cand[np.argmin(np.linalg.norm(cand - c, axis=1))]
            snapped.append(np.array(c))
        iS, iE = snapped
        nid = -np.ones(shp, np.int64)
        nid[ok] = np.arange(int(ok.sum()))
        gap, sat, w = wall
        pen = 1.0 + w * np.clip((D - clr - gap) / max(sat - gap, 1e-6), 0, 1)
        rows, cols, wts = [], [], []
        for o in OFFS:
            a_sl = tuple(slice(max(0, -o[k]), shp[k] - max(0, o[k])) for k in range(3))
            b_sl = tuple(slice(max(0, o[k]), shp[k] - max(0, -o[k])) for k in range(3))
            both = ok[a_sl] & ok[b_sl]
            if not both.any():
                continue
            rows.append(nid[a_sl][both])
            cols.append(nid[b_sl][both])
            wts.append(float(np.linalg.norm(o)) * 0.5 * (pen[a_sl][both] + pen[b_sl][both]))
        if not rows:
            continue
        n = int(ok.sum())
        Gm = csr_matrix((np.concatenate(wts), (np.concatenate(rows), np.concatenate(cols))), shape=(n, n))
        s_id, e_id = nid[tuple(iS)], nid[tuple(iE)]
        dist, pred = dijkstra(Gm, directed=False, indices=s_id, return_predecessors=True)
        if not np.isfinite(dist[e_id]):
            continue
        path = [e_id]
        while path[-1] != s_id:
            path.append(pred[path[-1]])
        inv = np.argwhere(ok)
        P = g.lo + lo + inv[path[::-1]] + 0.5
        P = np.vstack([S, P[1:-1], E]) if len(P) > 2 else np.vstack([S, E])
        dom_fn = lambda Q: _dom_lookup(g, Q, hulls, near_labels, near_mm)
        return pull(g, P, clr, dom_fn if (hulls or len(near_labels)) else None)
    return None


def _dom_lookup(g, Q, hulls, near_labels, near_mm):
    I = np.clip(g.idx(Q), 0, np.array(g.shape) - 1)
    ok = np.zeros(len(Q), bool)
    for h in hulls:
        ok |= h[I[:, 0], I[:, 1], I[:, 2]]
    if len(near_labels) and not ok.all():
        r = int(np.ceil(near_mm))
        for k in np.nonzero(~ok)[0]:
            c = I[k]
            sl = tuple(slice(max(0, c[a] - r), min(g.shape[a], c[a] + r + 1)) for a in range(3))
            sub = np.isin(g.label[sl], np.asarray(near_labels))
            if sub.any():
                J = np.argwhere(sub) + np.array([s_.start for s_ in sl])
                ok[k] = np.min(np.linalg.norm(J - c, axis=1)) <= near_mm
    return ok


def pull(g, P, clr, allowed=None):
    """string pulling: from each kept point jump to the farthest point with a clear straight segment"""
    out = [P[0]]
    i = 0
    n = len(P)
    while i < n - 1:
        j = n - 1
        while j > i + 1:
            # ends may sit inside the clearance zone: relax the check near them
            a, b = P[i], P[j]
            if seg_clear_relaxed(g, a, b, clr, allowed, P[0], P[-1]):
                break
            j -= 1
        out.append(P[j])
        i = j
    return np.array(out)


def seg_clear_relaxed(g, a, b, clr, allowed, S, E, relax=4.0, step=0.5):
    n = max(2, int(np.linalg.norm(b - a) / step) + 1)
    Q = a + (b - a) * np.linspace(0, 1, n)[:, None]
    d = g.sample(Q)
    near = (np.linalg.norm(Q - S, axis=1) < relax) | (np.linalg.norm(Q - E, axis=1) < relax)
    if (d[~near] < clr).any() or (d[near] <= 0.05).any():
        return False
    if allowed is not None and not allowed(Q[~near]).all():
        return False
    return True


# ---------------------------------------------------------------- raster
def look_at(eye, target, up):
    eye, target, up = (np.asarray(v, float) for v in (eye, target, up))
    f = target - eye
    f /= np.linalg.norm(f)
    r = np.cross(f, up)
    r /= np.linalg.norm(r)
    u = np.cross(r, f)
    return r, u, f


class Canvas:
    def __init__(self, w, h, eye, target, up=(0, 0, 1), ortho_half=None, fov_deg=30.0, bg=(255, 255, 255)):
        self.w, self.h = w, h
        self.eye = np.asarray(eye, float)
        self.r, self.u, self.f = look_at(eye, target, up)
        self.ortho_half = ortho_half
        self.fov = np.radians(fov_deg)
        self.depth = np.full(h * w, np.inf)
        self.rgb = np.zeros((h * w, 3), float)
        self.rgb[:] = bg
        self.ids = np.full(h * w, -1, np.int64)

    def project(self, P):
        d = np.atleast_2d(np.asarray(P, float)) - self.eye
        x, y, z = d @ self.r, d @ self.u, d @ self.f
        if self.ortho_half is not None:
            s = (self.w / 2) / self.ortho_half
            return np.c_[self.w / 2 + x * s, self.h / 2 - y * s, z]
        s = (self.h / 2) / np.tan(self.fov / 2)
        zz = np.maximum(z, 1e-6)
        return np.c_[self.w / 2 + x / zz * s, self.h / 2 - y / zz * s, z]

    def _fill(self, T, fc, ident, K):
        """T (m,3,3) screen triangles whose bbox fits in K x K pixels"""
        x0 = np.floor(T[:, :, 0].min(1)).astype(np.int64)
        y0 = np.floor(T[:, :, 1].min(1)).astype(np.int64)
        ox, oy = np.meshgrid(np.arange(K + 1), np.arange(K + 1), indexing="ij")
        ox, oy = ox.ravel(), oy.ravel()
        chunk = max(1, 3_000_000 // len(ox))
        for a in range(0, len(T), chunk):
            t = T[a:a + chunk]
            px = x0[a:a + chunk, None] + ox[None, :] + 0.5
            py = y0[a:a + chunk, None] + oy[None, :] + 0.5
            ax_, ay_ = t[:, 0, 0:1], t[:, 0, 1:2]
            bx_, by_ = t[:, 1, 0:1], t[:, 1, 1:2]
            cx_, cy_ = t[:, 2, 0:1], t[:, 2, 1:2]
            den = (by_ - cy_) * (ax_ - cx_) + (cx_ - bx_) * (ay_ - cy_)
            den = np.where(np.abs(den) < 1e-12, 1e-12, den)
            w0 = ((by_ - cy_) * (px - cx_) + (cx_ - bx_) * (py - cy_)) / den
            w1 = ((cy_ - ay_) * (px - cx_) + (ax_ - cx_) * (py - cy_)) / den
            w2 = 1 - w0 - w1
            inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
            inside &= (px >= 0) & (px < self.w) & (py >= 0) & (py < self.h)
            ti, oi = np.nonzero(inside)
            if not len(ti):
                continue
            z = w0[ti, oi] * t[ti, 0, 2] + w1[ti, oi] * t[ti, 1, 2] + w2[ti, oi] * t[ti, 2, 2]
            pix = py[ti, oi].astype(np.int64) * self.w + px[ti, oi].astype(np.int64)
            order = np.lexsort((z, pix))
            pix, z, ti = pix[order], z[order], ti[order]
            first = np.r_[True, pix[1:] != pix[:-1]]
            pix, z, ti = pix[first], z[first], ti[first]
            better = z < self.depth[pix]
            pix, z, ti = pix[better], z[better], ti[better]
            self.depth[pix] = z
            self.rgb[pix] = fc[a + ti]
            self.ids[pix] = ident if np.isscalar(ident) else ident[a + ti]

    def draw(self, V, F, color, light=(0.35, 0.45, 0.82), ambient=0.55, ident=0, shade=True, **_):
        V = np.asarray(V, float)
        F = np.asarray(F, np.int64)
        if len(F) == 0:
            return
        col = np.asarray(color, float)
        n = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        L = np.asarray(light, float)
        L /= np.linalg.norm(L)
        sgn = np.sign(n @ -self.f)
        sgn[sgn == 0] = 1
        lam = np.clip((n * sgn[:, None]) @ L, 0, 1)
        k = ambient + (1 - ambient) * lam if shade else np.ones(len(F))
        fc = (col if col.ndim == 2 else np.tile(col, (len(F), 1))) * k[:, None]
        S = self.project(V)
        T = S[F]
        keep = (T[:, :, 2] > 1e-3).all(1)
        T, fc = T[keep], fc[keep]
        ids = ident if np.isscalar(ident) else np.asarray(ident)[keep]
        if not len(T):
            return
        x0, x1 = T[:, :, 0].min(1), T[:, :, 0].max(1)
        y0, y1 = T[:, :, 1].min(1), T[:, :, 1].max(1)
        vis = (x1 >= 0) & (y1 >= 0) & (x0 < self.w) & (y0 < self.h)
        T, fc, x0, x1, y0, y1 = T[vis], fc[vis], x0[vis], x1[vis], y0[vis], y1[vis]
        if not np.isscalar(ids):
            ids = ids[vis]
        # clip huge bboxes to the screen for bucketing
        size = np.maximum(np.minimum(x1, self.w) - np.maximum(x0, 0), np.minimum(y1, self.h) - np.maximum(y0, 0))
        size = np.maximum(size, np.maximum(x1 - x0, y1 - y0) * 0 + 0)
        ext = np.maximum(x1 - x0, y1 - y0)
        edges = [4, 8, 16, 32, 64, 128]
        lo = 0
        for e in edges:
            sel = (ext > lo) & (ext <= e) if lo else (ext <= e)
            if sel.any():
                self._fill(T[sel], fc[sel], ids if np.isscalar(ids) else ids[sel], e + 1)
            lo = e
        big = np.nonzero(ext > edges[-1])[0]
        for b in big:   # rare: fill each over its clipped bbox
            t = T[b]
            bx0 = int(max(0, np.floor(t[:, 0].min())))
            by0 = int(max(0, np.floor(t[:, 1].min())))
            bx1 = int(min(self.w - 1, np.ceil(t[:, 0].max())))
            by1 = int(min(self.h - 1, np.ceil(t[:, 1].max())))
            if bx1 < bx0 or by1 < by0:
                continue
            gx, gy = np.meshgrid(np.arange(bx0, bx1 + 1) + 0.5, np.arange(by0, by1 + 1) + 0.5, indexing="ij")
            gx, gy = gx.ravel(), gy.ravel()
            (ax_, ay_, az), (bx_, by_, bz), (cx_, cy_, cz) = t
            den = (by_ - cy_) * (ax_ - cx_) + (cx_ - bx_) * (ay_ - cy_)
            if abs(den) < 1e-12:
                continue
            w0 = ((by_ - cy_) * (gx - cx_) + (cx_ - bx_) * (gy - cy_)) / den
            w1 = ((cy_ - ay_) * (gx - cx_) + (ax_ - cx_) * (gy - cy_)) / den
            w2 = 1 - w0 - w1
            ins = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
            z = w0 * az + w1 * bz + w2 * cz
            pix = gy.astype(np.int64) * self.w + gx.astype(np.int64)
            ok = ins & (z < self.depth[pix])
            self.depth[pix[ok]] = z[ok]
            self.rgb[pix[ok]] = fc[b]
            self.ids[pix[ok]] = ids if np.isscalar(ids) else ids[b]

    def outline(self, color=(40, 40, 40), depth_jump=4.0, id_lines=True, strength=0.65):
        D = self.depth.reshape(self.h, self.w)
        I = self.ids.reshape(self.h, self.w)
        Df = np.where(np.isinf(D), 1e9, D)
        e = np.zeros((self.h, self.w), bool)
        jy = np.abs(Df[1:, :] - Df[:-1, :]) > depth_jump
        jx = np.abs(Df[:, 1:] - Df[:, :-1]) > depth_jump
        if id_lines:
            jy |= I[1:, :] != I[:-1, :]
            jx |= I[:, 1:] != I[:, :-1]
        e[1:, :] |= jy
        e[:, 1:] |= jx
        rgb = self.rgb.reshape(self.h, self.w, 3)
        rgb[e] = rgb[e] * (1 - strength) + np.array(color) * strength
        self.rgb = rgb.reshape(-1, 3)

    def image(self):
        from PIL import Image
        return Image.fromarray(np.clip(self.rgb.reshape(self.h, self.w, 3), 0, 255).astype(np.uint8))


# ---------------------------------------------------------------- tubes
def tube(P, r, k=8):
    """triangle mesh of a tube of radius r along polyline P (parallel transport frames)"""
    P = np.asarray(P, float)
    keep = [0]
    for i in range(1, len(P)):
        if np.linalg.norm(P[i] - P[keep[-1]]) > 1e-6:
            keep.append(i)
    P = P[keep]
    if len(P) < 2:
        return np.zeros((0, 3)), np.zeros((0, 3), int)
    t = np.gradient(P, axis=0)
    t /= np.linalg.norm(t, axis=1, keepdims=True)
    a = np.array([0, 0, 1.0]) if abs(t[0][2]) < 0.9 else np.array([1.0, 0, 0])
    n = np.cross(t[0], a)
    n /= np.linalg.norm(n)
    frames = []
    for i in range(len(P)):
        if i:
            n = n - np.dot(n, t[i]) * t[i]
            nl = np.linalg.norm(n)
            n = n / nl if nl > 1e-9 else np.cross(t[i], a) / np.linalg.norm(np.cross(t[i], a))
        frames.append((n, np.cross(t[i], n)))
    ang = np.linspace(0, 2 * np.pi, k, endpoint=False)
    V = np.array([P[i] + r * (np.cos(q) * frames[i][0] + np.sin(q) * frames[i][1]) for i in range(len(P)) for q in ang])
    F = []
    for i in range(len(P) - 1):
        for j in range(k):
            a0, a1 = i * k + j, i * k + (j + 1) % k
            b0, b1 = a0 + k, a1 + k
            F += [[a0, a1, b1], [a0, b1, b0]]
    return V, np.array(F, int)


def bundle_tubes(P, colors, d_bundle):
    """one thin tube per conductor around the centreline (or one tube for a single conductor)"""
    n = len(colors)
    if n <= 1:
        V, F = tube(P, d_bundle / 2.0)
        return [(V, F, colors[0] if colors else (150, 150, 150))]
    rc = d_bundle / 2.0 / (1.0 + 1.0 / np.sin(np.pi / n)) if n > 1 else d_bundle / 2
    off = d_bundle / 2.0 - rc
    P = np.asarray(P, float)
    t = np.gradient(P, axis=0)
    t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
    a = np.array([0, 0, 1.0]) if abs(t[0][2]) < 0.9 else np.array([1.0, 0, 0])
    nrm = np.cross(t[0], a)
    nrm /= np.linalg.norm(nrm)
    N = []
    for i in range(len(P)):
        if i:
            nrm = nrm - np.dot(nrm, t[i]) * t[i]
            nrm /= max(np.linalg.norm(nrm), 1e-9)
        N.append(nrm.copy())
    N = np.array(N)
    B = np.cross(t, N)
    out = []
    for c, col in enumerate(colors):
        q = 2 * np.pi * c / n
        Q = P + off * (np.cos(q) * N + np.sin(q) * B)
        V, F = tube(Q, rc * 1.05, k=6)
        out.append((V, F, col))
    return out
