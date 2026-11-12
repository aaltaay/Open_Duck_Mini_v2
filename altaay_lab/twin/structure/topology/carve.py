"""Remove interior material that the structure-twin stress field does not load (FEA pass only).

Uses the existing solver (st_fea.Part, the same unit-load superposition as st_fea_run). An element may go
only when an upper bound on its von Mises stress, from the peak of each load component over the walking
and soft-fall histories, stays under a threshold, and the element is more than SKIN_MM inside the part.
The bound overstates the real stress, so the cut is smaller than a true topology optimum. The carved STL
is written under topology/stl_topo/ and is not copied over print/.
"""
import os, sys
import numpy as np
import trimesh
import manifold3d as m3

HERE = os.path.dirname(os.path.abspath(__file__))
STRUCT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, STRUCT)
import st_fea as FE
import st_fea_run as FR

OUT = os.path.join(HERE, "stl_topo")
SKIN_MM = 2.4
# 47.1 MPa / 2 is the walking allowable. Material under 8% of that carries no meaningful load.
VM_CAP = 0.08 * 47.1


def upper_vm(P, S):
    """Per-element upper bound on von Mises from component-wise peak loads (walking and soft falls)."""
    sig_u = FR.solve_units(P, S)
    peaks = np.zeros(sig_u.shape[0])
    for which in ("walk", "fall"):
        hist, names = FR.history(S, which)
        if which == "fall":
            sel = np.array([n.endswith("_tc0.0158_dr0.2") for n in names])
            hist = hist[sel]
        if len(hist):
            peaks = np.maximum(peaks, np.abs(hist).max(0))
    # |stress| <= sum_c peak_c * |unit stress_c|
    bound = np.zeros(sig_u.shape[1])
    for c in range(sig_u.shape[0]):
        s = sig_u[c]
        vm = np.sqrt(np.maximum(0, s[:, 0] ** 2 + s[:, 1] ** 2 + s[:, 2] ** 2
                                - s[:, 0] * s[:, 1] - s[:, 1] * s[:, 2] - s[:, 2] * s[:, 0]
                                + 3 * (s[:, 3] ** 2 + s[:, 4] ** 2 + s[:, 5] ** 2)))
        bound += peaks[c] * vm
    return bound


def carve_one(study, pitch):
    os.environ["ST_VOXEL_MM"] = str(pitch)
    P, S = FR.setup(study, 1)
    if len(P.members) != 1:
        raise SystemExit("carve_one is for a single part: " + study)
    bound = upper_vm(P, S)
    c = P.X[P.T].mean(1)
    # interior: far from the STL surface
    m = P.members[0]["mesh"]
    # distance via nearest surface sample
    pts, _ = trimesh.sample.sample_surface(m, 80000)
    from scipy.spatial import cKDTree
    dist = cKDTree(pts).query(c)[0]
    drop = (bound < VM_CAP) & (dist > SKIN_MM) & (P.zone != 4)
    print(study, "tets", len(P.T), "drop", int(drop.sum()), "bound p50", round(float(np.median(bound)), 2),
          "p95", round(float(np.percentile(bound, 95)), 2), flush=True)
    if drop.sum() < 20:
        return None
    centres = c[drop]
    # one cube per 2.4 mm cell that is mostly unloaded, so the pocket is a real void
    cell = 2.4
    key = np.floor(centres / cell).astype(np.int64)
    key = key[:, 0] + 1000003 * key[:, 1] + 1000003 * 1000003 * key[:, 2]
    _, idx = np.unique(key, return_index=True)
    centres = centres[idx]
    cubes = []
    for p in centres:
        cubes.append(m3.Manifold.cube([cell * 0.85] * 3).translate((p - cell * 0.425).tolist()))
    print(study, "void cubes", len(cubes), flush=True)
    tool = cubes[0]
    for b in cubes[1:]:
        tool = tool + b
    base = m3.Manifold(m3.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))
    carved = base - tool
    me = carved.to_mesh()
    out = trimesh.Trimesh(np.asarray(me.vert_properties)[:, :3], np.asarray(me.tri_verts), process=False)
    # back to STL frame
    T = P.members[0]["T"]
    inv = np.linalg.inv(T)
    out.apply_transform(inv)
    os.makedirs(OUT, exist_ok=True)
    name = P.members[0]["name"]
    path = os.path.join(OUT, name + ".stl")
    out.export(path)
    print(name, "vol", round(float(m.volume), 1), "->", round(float(carved.volume()), 1), "wrote", path, flush=True)
    return path


if __name__ == "__main__":
    study = sys.argv[1]
    pitch = float(sys.argv[2]) if len(sys.argv) > 2 else 1.2
    carve_one(study, pitch)
