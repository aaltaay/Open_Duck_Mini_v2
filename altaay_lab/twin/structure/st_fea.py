"""Structure twin: linear FEA of a printed part or a bonded group of printed parts, as printed (FEA pass only).

Model
- Geometry: the upstream print STLs (print/<part>.stl, mm) placed in their URDF link frame; a group of parts that
  touch (the two sheets and the leg_spacer of a leg segment) is joined by a boolean union (manifold3d), so the
  screwed joints between them are bonded (ASSUMPTION: no slip or gap at the M3 insert joints).
- Mesh: TetGen (pip tetgen 0.8.4) linear tetrahedra, quality ratio 1.6, minimum dihedral 15 deg, maximum volume
  set per run (mesh convergence check at 3 sizes).
- Zones per element, in the print frame of the part the element belongs to (z = the parts.csv "up" axis, layers
  horizontal): perimeters (walls) = within n beads of a side face (2 walls 0.86 mm, 3 walls 1.27 mm, 4 walls
  1.67 mm, 5 walls 2.09 mm; print/config/ovr_insert.ini: 0.45 + (n - 1) x 0.41 mm); top skin 5 layers (1.0 mm)
  under an up-facing face; bottom skin 4 layers (0.8 mm) over a down-facing face (pla_print.ini); solid rings of
  mod_ring.ini (insert bore + 4.0 mm diameter, 0.6 mm past each end); the rest is gyroid infill (15 %, neck 40 %).
- Materials: solid zones isotropic, E 2641 MPa (Overture PLA TDS v5.1, 100 % infill specimens, search result text),
  nu 0.35 (ASSUMPTION, range 0.30 to 0.40); infill E = E_s rho^2.12 (Gibson and Ashby power law, gyroid exponent
  2.12 from Doyle et al. 2025), nu 0.30.
- Loads: 6D loads (N, N mm at a reference point) spread on the surface nodes of screw hole walls and the face annuli
  under the heads with RBE3 weights (statically equal, adds no stiffness).
- Supports: nodes within 0.3 mm of the servo case surfaces (bonded to a rigid servo case, ASSUMPTION: the PA+GF
  case is much stiffer than the printed part) and the case screw hole walls are fixed.
- Failure index per element in its part's print frame: solid zones max(von Mises / X, sqrt((max(s_zz, 0) / Z)^2 +
  (tau_z / S)^2)); infill zones von Mises / (0.3 rho^1.5 X) (Gibson and Ashby plastic collapse).
"""
import os, json, time
import numpy as np
import trimesh, tetgen
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, "../.."))
REPO = os.path.abspath(os.path.join(LAB, ".."))
PRINT = os.environ.get("ST_PRINT", os.path.join(REPO, "print"))

def stl_path(name):
    """STL for a study member or a support mesh. ST_PRINT wins when the file is there; otherwise the print set."""
    p = os.path.join(PRINT, name + ".stl")
    if os.path.exists(p):
        return p
    return os.path.join(REPO, "print", name + ".stl")

E_SOLID = 2641.0
NU_SOLID = 0.35
GYROID_N = 2.12
WALL_MM = {2: 0.86, 3: 1.27, 4: 1.67, 5: 2.09, 6: 2.50}   # 0.45 + (n - 1) x 0.41 mm
TOP_MM, BOT_MM = 1.0, 0.8
# 6-tet split of a cube. Every cube uses the same diagonal, so neighboring cubes share faces.
_CUBE_TETS = np.array([[0, 1, 3, 7], [0, 3, 2, 7], [0, 2, 6, 7], [0, 6, 4, 7], [0, 4, 5, 7], [0, 5, 1, 7]], np.int32)
_CUBE_OFF = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0], [0, 0, 1], [1, 0, 1], [0, 1, 1], [1, 1, 1]], np.int32)


def voxel_tets(mesh, pitch, holes=()):
    """Linear tets from a regular grid of the solid (FEA pass only).

    TetGen's recoversubfaces step fails on the current print STLs (edges shorter than 0.05 mm).
    This keeps the same element, the same assembler and the same solver. A voxel is solid when its
    centre is inside the STL. holes is a list of (centre, unit axis, radius, half length) cylinders
    that stay open (screw holes and horn hubs). Pitch is in mm.
    """
    b0 = np.asarray(mesh.bounds[0], float) - pitch
    b1 = np.asarray(mesh.bounds[1], float) + pitch
    xs = np.arange(b0[0], b1[0] + pitch * 0.5, pitch)
    ys = np.arange(b0[1], b1[1] + pitch * 0.5, pitch)
    zs = np.arange(b0[2], b1[2] + pitch * 0.5, pitch)
    xc, yc, zc = xs[:-1] + pitch / 2, ys[:-1] + pitch / 2, zs[:-1] + pitch / 2
    IX, IY, IZ = np.meshgrid(np.arange(len(xc)), np.arange(len(yc)), np.arange(len(zc)), indexing="ij")
    pts = np.stack([xc[IX].ravel(), yc[IY].ravel(), zc[IZ].ravel()], 1)
    inside = np.asarray(mesh.contains(pts), bool)
    for c, a, r, h in holes:
        d = pts - np.asarray(c, float)
        ax = d @ np.asarray(a, float)
        rad = np.linalg.norm(d - np.outer(ax, a), axis=1)
        inside &= ~((rad < r) & (np.abs(ax) < h))
    ijk = np.stack([IX.ravel()[inside], IY.ravel()[inside], IZ.ravel()[inside]], 1)
    if not len(ijk):
        raise RuntimeError("voxel mesh is empty")
    corners = ijk[:, None, :] + _CUBE_OFF[None, :, :]
    flat = corners.reshape(-1, 3)
    nx, ny = len(xs), len(ys)
    key = flat[:, 0] + nx * (flat[:, 1] + ny * flat[:, 2])
    uniq, inv = np.unique(key, return_inverse=True)
    kz = uniq // (nx * ny)
    rem = uniq % (nx * ny)
    ky = rem // nx
    kx = rem % nx
    X = np.stack([xs[kx], ys[ky], zs[kz]], 1)
    T = inv.reshape(-1, 8)[:, _CUBE_TETS].reshape(-1, 4).astype(np.int32)
    a = X[T[:, 1]] - X[T[:, 0]]
    b = X[T[:, 2]] - X[T[:, 0]]
    d = X[T[:, 3]] - X[T[:, 0]]
    signed = np.einsum("ij,ij->i", np.cross(a, b), d)
    neg = signed < 0
    if neg.any():
        T = T.copy()
        T[neg, 1], T[neg, 2] = T[neg, 2], T[neg, 1].copy()
    return X, T

def up_rotation(up):
    """rotation R taking STL coordinates to the print frame where 'up' is +z"""
    if isinstance(up, str) and up.startswith("vec:"):
        u = np.array([float(x) for x in up[4:].split()])
    else:
        ax = {"x": 0, "y": 1, "z": 2}[up[-1]]; u = np.zeros(3); u[ax] = -1.0 if up[0] == "-" else 1.0
    u = u / np.linalg.norm(u)
    a = np.array([1.0, 0, 0]) if abs(u[0]) < 0.9 else np.array([0, 1.0, 0])
    x = np.cross(a, u); x /= np.linalg.norm(x); y = np.cross(u, x)
    return np.vstack([x, y, u])

def parts_csv():
    import csv
    return {r["stl"][:-4]: r for r in csv.DictReader(open(os.path.join(LAB, "print/parts.csv")))}

def profile_of(part):
    r = parts_csv()[part]; ov = r["overrides"]; walls = 2; infill = 0.15
    if "insert" in ov: walls = 4
    if "wall3" in ov: walls = 3
    if "neck" in ov: walls = 5; infill = 0.40
    return dict(walls=walls, infill=infill, rings=r["rings"], up=r["up"], profile=r["profile"], overrides=ov)

class Part:
    # mesh levels for the convergence check (TetGen radius-edge ratio, minimum dihedral angle, maximum volume mm3)
    LEVELS = {1: dict(minratio=2.0, mindihedral=10, maxvol=5.0), 2: dict(minratio=1.6, mindihedral=15, maxvol=1.0),
              3: dict(minratio=1.4, mindihedral=18, maxvol=0.3)}

    def __init__(self, members, level=1, rings=(), grow=None, tie_mm=0.45, k_tie=2.0e4, prof_over=None, simplify=None, voxel_mm=None, holes=()):
        """members: list of (part_name, T_link 4x4 STL mm -> link mm); rings: list of (centre_link, axis_link, r, half_len).
        Each member is meshed on its own; members that touch are tied by stiff springs between surface nodes closer than
        tie_mm (bonded screwed joint, ASSUMPTION; k_tie N/mm per node pair, about 15 x the local element stiffness E h).
        voxel_mm: build the tets on a grid of that pitch instead of TetGen (see voxel_tets). holes: cylinders kept open."""
        self.members = []; L = Part.LEVELS[level]; self.level = level; self.voxel_mm = voxel_mm
        Xs, Ts, mem = [], [], []; off = 0; t = time.time()
        for k, (name, T) in enumerate(members):
            m = trimesh.load(stl_path(name), force="mesh")
            if simplify and name in simplify:            # collapse STL edges shorter than simplify[name] mm (manifold3d), so that
                import manifold3d as m3                   # TetGen does not refine a cascade of tiny tets at needle triangles
                me = m3.Manifold(m3.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32))).simplify(simplify[name]).to_mesh()
                m = trimesh.Trimesh(np.asarray(me.vert_properties)[:, :3].astype(float), np.asarray(me.tri_verts).astype(int), process=True)
            m.apply_transform(T)
            if np.linalg.det(T[:3, :3]) < 0: m.invert()
            prof = profile_of(name)
            if prof_over and name in prof_over: prof = dict(prof, **prof_over[name])     # proposal studies: other walls or infill
            Rp = up_rotation(prof["up"]); R_lp = Rp @ T[:3, :3].T
            self.members.append(dict(name=name, T=T, prof=prof, R=R_lp, mesh=m))
            if voxel_mm:
                n_, e_ = voxel_tets(m, float(voxel_mm), holes)
            else:
                tg = tetgen.TetGen(np.asarray(m.vertices, float), np.asarray(m.faces, int))
                n_, e_ = tg.tetrahedralize(order=1, mindihedral=L["mindihedral"], minratio=L["minratio"], maxvolume=L["maxvol"], fixedvolume=True, quiet=True)[:2]
            Xs.append(np.asarray(n_, float)); Ts.append(np.asarray(e_, int) + off); mem.append(np.full(len(e_), k)); off += len(n_)
        self.X = np.vstack(Xs); self.T = np.vstack(Ts); self.mem = np.concatenate(mem); self.mesh_s = time.time() - t
        self.node_mem = np.concatenate([np.full(len(x), k) for k, x in enumerate(Xs)])
        self.name = "+".join(x["name"] for x in self.members)
        self.rings = rings; self.tie_mm = tie_mm; self.k_tie = k_tie
        self.zones()

    def ties(self):
        """node pairs of different members closer than tie_mm (surface nodes only)"""
        sn = np.nonzero(self.surface_nodes())[0]; pairs = []
        for a in range(len(self.members)):
            A = sn[self.node_mem[sn] == a]
            for b in range(a + 1, len(self.members)):
                Bn = sn[self.node_mem[sn] == b]
                if not len(A) or not len(Bn): continue
                d, j = cKDTree(self.X[Bn]).query(self.X[A], distance_upper_bound=self.tie_mm)
                ok = np.isfinite(d); pairs.append(np.stack([A[ok], Bn[j[ok]]], axis=1))
        return np.vstack(pairs) if pairs else np.zeros((0, 2), int)

    def zones(self):
        X, T = self.X, self.T; c = X[T].mean(1); ne = len(T)
        dist = np.full(ne, 1e9); nzp = np.zeros(ne)
        for k, M in enumerate(self.members):
            sel = self.mem == k; m = M["mesh"]; n = int(min(2e6, max(5e4, m.area / 0.06 ** 2)))
            pts, fi = trimesh.sample.sample_surface(m, n)
            d, idx = cKDTree(pts).query(c[sel], distance_upper_bound=8.0)
            far = ~np.isfinite(d); idx = np.minimum(idx, len(pts) - 1)
            nrm = m.face_normals[fi[idx]]
            if far.any():
                pc, fc = trimesh.sample.sample_surface(m, 20000); d2, i2 = cKDTree(pc).query(c[sel][far]); d[far] = d2; nrm[far] = m.face_normals[fc[i2]]
            dist[sel] = d; nzp[sel] = (nrm @ M["R"].T)[:, 2]
        zone = np.full(ne, 3, int)                                            # 0 wall, 1 top skin, 2 bottom skin, 3 infill, 4 ring
        walls = np.array([WALL_MM[M["prof"]["walls"]] for M in self.members])[self.mem]
        side = np.abs(nzp) < 0.7
        zone[side & (dist < walls)] = 0
        zone[(nzp >= 0.7) & (dist < TOP_MM)] = 1
        zone[(nzp <= -0.7) & (dist < BOT_MM)] = 2
        for (cc, aa, r, h) in self.rings:
            dd = c - cc; ax = dd @ aa; rad = np.linalg.norm(dd - np.outer(ax, aa), axis=1)
            zone[(rad < r) & (np.abs(ax) < h) & (zone == 3)] = 4
        self.zone = zone; self.dist = dist
        self.infill = np.array([M["prof"]["infill"] for M in self.members])[self.mem]
        V = self.vol(); self.zone_vol = {k: float(V[zone == k].sum()) for k in range(5)}
        self.member_vol = {M["name"]: float(V[self.mem == k].sum()) for k, M in enumerate(self.members)}

    def vol(self):
        X, T = self.X, self.T
        a = X[T[:, 1]] - X[T[:, 0]]; b = X[T[:, 2]] - X[T[:, 0]]; d = X[T[:, 3]] - X[T[:, 0]]
        return np.abs(np.einsum("ij,ij->i", np.cross(a, b), d)) / 6.0

    def material(self):
        n = len(self.T); C = np.zeros((n, 6, 6))
        def iso(E, nu):
            lam = E * nu / ((1 + nu) * (1 - 2 * nu)); mu = E / (2 * (1 + nu)); M = np.zeros((6, 6))
            M[:3, :3] = lam; M[[0, 1, 2], [0, 1, 2]] += 2 * mu; M[[3, 4, 5], [3, 4, 5]] = mu; return M
        Cs = iso(E_SOLID, NU_SOLID); C[:] = Cs
        inf = self.zone == 3
        for rho in np.unique(self.infill[inf]):
            C[inf & (self.infill == rho)] = iso(E_SOLID * rho ** GYROID_N, 0.30)
        self.C = C; return C

    def assemble(self):
        X, T = self.X, self.T; n = len(X)
        M = np.concatenate([np.ones((len(T), 4, 1)), X[T]], axis=2)
        G = np.linalg.inv(M)[:, 1:, :]
        B = np.zeros((len(T), 6, 12))
        for i in range(4):
            gx, gy, gz = G[:, 0, i], G[:, 1, i], G[:, 2, i]
            B[:, 0, 3 * i] = gx; B[:, 1, 3 * i + 1] = gy; B[:, 2, 3 * i + 2] = gz
            B[:, 3, 3 * i + 1] = gz; B[:, 3, 3 * i + 2] = gy
            B[:, 4, 3 * i] = gz; B[:, 4, 3 * i + 2] = gx
            B[:, 5, 3 * i] = gy; B[:, 5, 3 * i + 1] = gx
        self.B = B; self.V = self.vol()
        Ke = np.einsum("eji,ejk,ekl->eil", B, self.C, B) * self.V[:, None, None]
        dof = (3 * T[:, :, None] + np.arange(3)[None, None, :]).reshape(len(T), 12)
        rows = np.repeat(dof, 12, axis=1).ravel(); cols = np.tile(dof, (1, 12)).ravel()
        K = sp.csr_matrix((Ke.ravel(), (rows, cols)), shape=(3 * n, 3 * n))
        P_ = self.ties(); self.n_ties = len(P_)
        if len(P_):
            r, cc, v = [], [], []
            for k in range(3):
                i, j = 3 * P_[:, 0] + k, 3 * P_[:, 1] + k
                r += [i, j, i, j]; cc += [i, j, j, i]; v += [np.full(len(i), self.k_tie)] * 2 + [np.full(len(i), -self.k_tie)] * 2
            K = K + sp.csr_matrix((np.concatenate(v), (np.concatenate(r), np.concatenate(cc))), shape=(3 * n, 3 * n))
        self.K = K

    def surface_nodes(self):
        if not hasattr(self, "_surf_nodes"):
            T = self.T; faces = np.vstack([T[:, [0, 1, 2]], T[:, [0, 1, 3]], T[:, [0, 2, 3]], T[:, [1, 2, 3]]])
            fs = np.sort(faces, axis=1); u, cnt = np.unique(fs, axis=0, return_counts=True)
            m = np.zeros(len(self.X), bool); m[np.unique(u[cnt == 1])] = True; self._surf_nodes = m
        return self._surf_nodes

    def nodes_near_hole(self, c, a, r_hole, half_len, face_r=None):
        """surface nodes on a hole wall (radius r_hole +- 0.35 mm, within half_len of c along a) and, with face_r,
        on the face annuli round the axis at the hole ends (link frame)"""
        X = self.X; d = X - c; ax = d @ a; rad = np.linalg.norm(d - np.outer(ax, a), axis=1); sn = self.surface_nodes()
        sel = sn & (np.abs(rad - r_hole) < 0.35) & (np.abs(ax) <= half_len + 0.05)
        if face_r: sel |= sn & (rad < face_r) & (rad > r_hole - 0.2) & (np.abs(ax) <= half_len + 0.6)
        return np.nonzero(sel)[0]

    def rbe3(self, nodes, F, M, ref):
        P = self.X[nodes]; c = P.mean(0); r = P - c; n = len(nodes)
        Mc = M + np.cross(ref - c, F)
        J = np.einsum("ij,ij->", r, r) * np.eye(3) - r.T @ r
        a = np.linalg.solve(J, Mc)
        return F[None, :] / n + np.cross(a[None, :], r)

    def solve(self, loads, fixed_nodes, tol=1e-8):
        n = len(self.X); f = np.zeros(3 * n)
        for nodes, F, M, ref in loads:
            fn = self.rbe3(nodes, np.asarray(F, float), np.asarray(M, float), np.asarray(ref, float))
            for k in range(3): np.add.at(f, 3 * nodes + k, fn[:, k])
        fixed = np.zeros(3 * n, bool)
        for k in range(3): fixed[3 * fixed_nodes + k] = True
        free = ~fixed
        if not hasattr(self, "_ml") or self._free_key != fixed_nodes.tobytes():
            import pyamg
            self._Kff = self.K[free][:, free].tocsr()
            self._ml = pyamg.smoothed_aggregation_solver(self._Kff, B=self._rigid_modes(free), max_coarse=500)
            self._free_key = fixed_nodes.tobytes()
        t = time.time(); res = []
        uf = self._ml.solve(f[free], tol=tol, accel="cg", maxiter=500, residuals=res)
        self.solver = f"pyamg 5.4.1 smoothed aggregation + CG, {len(res)} iterations, relative residual {res[-1] / max(res[0], 1e-30):.1e}"
        u = np.zeros(3 * n); u[free] = uf; self.solve_s = time.time() - t
        self.u = u.reshape(n, 3); self.f = f
        return self.u

    def _rigid_modes(self, free):
        X = self.X; n = len(X); B = np.zeros((3 * n, 6))
        B[0::3, 0] = 1; B[1::3, 1] = 1; B[2::3, 2] = 1
        B[1::3, 3] = -X[:, 2]; B[2::3, 3] = X[:, 1]; B[0::3, 4] = X[:, 2]; B[2::3, 4] = -X[:, 0]
        B[0::3, 5] = -X[:, 1]; B[1::3, 5] = X[:, 0]
        return B[free]

    def stress_print(self):
        """element stress (Voigt xx yy zz yz xz xy, MPa) in each element's member print frame"""
        ue = self.u[self.T].reshape(len(self.T), 12)
        s = np.einsum("eij,ej->ei", self.C, np.einsum("eij,ej->ei", self.B, ue))
        S = np.zeros((len(s), 3, 3))
        S[:, 0, 0], S[:, 1, 1], S[:, 2, 2] = s[:, 0], s[:, 1], s[:, 2]
        S[:, 1, 2] = S[:, 2, 1] = s[:, 3]; S[:, 0, 2] = S[:, 2, 0] = s[:, 4]; S[:, 0, 1] = S[:, 1, 0] = s[:, 5]
        out = np.zeros_like(s)
        for k, M in enumerate(self.members):
            sel = self.mem == k; R = M["R"]
            Sp = np.einsum("ij,ejk,lk->eil", R, S[sel], R)
            out[sel] = np.stack([Sp[:, 0, 0], Sp[:, 1, 1], Sp[:, 2, 2], Sp[:, 1, 2], Sp[:, 0, 2], Sp[:, 0, 1]], axis=1)
        return out

def averaging_matrix(P, radius=1.0, k=32):
    """sparse (ne x ne) volume-weighted average of the element stress over the elements of the same member and the same
    zone class (solid or infill) whose centroids lie within 'radius' mm (among the k nearest). Linear tetrahedra give a
    constant stress per element; where the 0.86 to 2.1 mm wall bands and the 56 x softer infill cut through elements,
    single elements carry stress spikes of either sign. The average over 1 mm (about two 0.45 mm beads and five 0.2 mm
    layers, the scale of the printed structure) is used for the failure index; the raw element peak is reported too."""
    c = P.X[P.T].mean(1); V = P.vol(); solid = P.zone != 3; ne = len(c)
    d, j = cKDTree(c).query(c, k=k)
    ok = (d <= radius) & (P.mem[j] == P.mem[:, None]) & (solid[j] == solid[:, None])
    ok[:, 0] = True                                                # the element itself
    w = np.where(ok, V[j], 0.0); w = w / w.sum(1, keepdims=True)
    rows = np.repeat(np.arange(ne), k)
    return sp.csr_matrix((w.ravel(), (rows, j.ravel())), shape=(ne, ne))

def failure_index(sig, solid, rho, X_xy=47.1, Z=22.0, S=22.0):
    sxx, syy, szz, syz, sxz, sxy = [sig[..., i] for i in range(6)]
    vm = np.sqrt(0.5 * ((sxx - syy) ** 2 + (syy - szz) ** 2 + (szz - sxx) ** 2) + 3 * (syz ** 2 + sxz ** 2 + sxy ** 2))
    tz = np.hypot(syz, sxz); fi_vm = vm / X_xy; fi_z = np.sqrt((np.clip(szz, 0, None) / Z) ** 2 + (tz / S) ** 2)
    fi_inf = vm / (0.3 * rho ** 1.5 * X_xy)
    return np.where(solid, np.maximum(fi_vm, fi_z), fi_inf), vm, szz, tz, fi_vm, fi_z
