"""V1 track 9: grow the battery bay in body_back for a 2S1P Molicel P45B 21700 pack (CAD check only).
Pack: two 21700 cells side by side in y, axes along z, spot-welded nickel strip and heat shrink: 22.2 x 43.7 x 71.0 mm
(x, y, z; P45B 21.40 +/- 0.15 x 70.00 +/- 0.15 mm [Molicel INR21700P45B-01], P50B 21.55 x 70.15 max, plus 0.3 mm shrink
per side and 0.3 mm strip). Bay as built: x -139.6 to -119.0 (lid face), y +/-20.7, z -7.5 to 76.0 (trunk frame, rays).
New cavity: the two cell outlines (cylinders r 11.35 mm on axes x -133.1, y -9.35 and +12.2) joined, rear face x -144.45, front
box to the lid face x -119.0 (rearward, into the 14.4 mm back wall; the pack front stays 0.5 mm behind the lid's central pad at x -121.5), y -20.7 to +23.55 (all the widening on the +y side: the
charger screw F123's pilot ends 1.0 mm from the -y wall), z -4.5 to 67.5 (the pack height only, clear of the lid screws
F017, F018, F027, F028 at the corners); 0.25 mm clearance per side in y and 0.5 mm in x. The lid stays as it is. Writes <OUT>/body_back.stl (print frame) and <OUT>/bay_edit.json."""
import os, sys, json
import numpy as np, trimesh, manifold3d
REPO = os.environ.get("ODM_REPO", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
OUT = os.environ.get("BAY_OUT", os.path.join(os.path.expanduser("~"), "v1_out", "battery", "bay", "out"))   # outside the repo
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, os.path.join(REPO, "altaay_lab", "fasteners"))
from fastlib import Scene
S = Scene(os.path.join(OUT, "scene"))
K = {i["key"]: k for k, i in enumerate(S.inst)}
bb = S.inst[K["body_back"]]; T = bb["T"]; Ti = np.linalg.inv(T)
src = trimesh.load(bb["src"], force="mesh")
NEW = dict(x=(-144.7, -119.0), y=(-20.7, 23.55), z=(-4.5, 67.5))
PACK = dict(x=(-144.2, -122.0), y=(-20.45, 23.25), z=(-4.0, 67.0))     # the pack itself, seated on the bay floor + 3.5 mm foam
def boxmesh(B):
    lo = np.array([B["x"][0], B["y"][0], B["z"][0]]); hi = np.array([B["x"][1], B["y"][1], B["z"][1]])
    return trimesh.creation.box(extents=hi - lo, transform=trimesh.transformations.translation_matrix((lo + hi) / 2))
def man(m):
    return manifold3d.Manifold(manifold3d.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))
def tm(M):
    g = M.to_mesh(); return trimesh.Trimesh(g.vert_properties[:, :3], g.tri_verts, process=True)
XC, YC, RP, RC = -133.1, (-9.35, 12.2), 11.1, 11.35   # cell axes (z), pack radius (cell + sleeve), cut radius
def stadium(r, x_front, y_front, zr):
    """two cylinders (the cells) joined by a box between them, plus a box from the cell axes to x_front over y_front"""
    h = zr[1] - zr[0]; zc = (zr[0] + zr[1]) / 2
    parts = [man(trimesh.creation.cylinder(radius=r, height=h, sections=96, transform=trimesh.transformations.translation_matrix((XC, y, zc)))) for y in YC]
    parts.append(man(boxmesh(dict(x=(XC - r, XC), y=YC, z=zr))))
    parts.append(man(boxmesh(dict(x=(XC, x_front), y=y_front, z=zr))))
    M = parts[0]
    for q in parts[1:]:
        M = M + q
    return M
def prism():
    """the cut: 45 deg chamfers tangent to the two cell outlines (cut radius RC) up to a flat ceiling at x = XC - RC, so the
    part prints (front face down, up = -x) with no support on the chamfers"""
    from shapely.geometry import Polygon
    xr = XC - RC
    yR = (xr - XC) + YC[1] + RC * 2 ** 0.5          # right chamfer y = x - XC + yB + RC sqrt2, at the ceiling
    xR = NEW["y"][1] - YC[1] - RC * 2 ** 0.5 + XC     # and at the +y wall
    yL = -(xr - XC) + YC[0] - RC * 2 ** 0.5
    xL = -(NEW["y"][0] - YC[0] + RC * 2 ** 0.5) + XC
    poly = Polygon([(NEW["x"][1], NEW["y"][0]), (xL, NEW["y"][0]), (xr, yL), (xr, yR), (xR, NEW["y"][1]), (NEW["x"][1], NEW["y"][1])])
    P = trimesh.creation.extrude_polygon(poly, NEW["z"][1] - NEW["z"][0])
    P.apply_translation((0, 0, NEW["z"][0]))
    rep_poly.extend([list(map(lambda v: round(v, 2), c)) for c in poly.exterior.coords])
    return man(P)
rep_poly = []
CUT = prism()
PK = stadium(RP, XC + RP, (YC[0] - RP, YC[1] + RP), PACK["z"])
cut = tm(CUT); cut.apply_transform(Ti)                                    # into the print frame
A = man(src); B = man(cut)
new = tm(A - B)
rep = dict(cut_polygon_xy_mm=rep_poly, src=bb["src"], watertight_before=bool(src.is_watertight), watertight_after=bool(new.is_watertight),
           volume_before_mm3=round(float(src.volume), 1), volume_after_mm3=round(float(new.volume), 1))
rep["removed_mm3"] = round(rep["volume_before_mm3"] - rep["volume_after_mm3"], 1)
# overlap of the pack box with every part of the scene except the edited body_back (zero pose)
pk = PK; ov = {}
for k, i in enumerate(S.inst):
    if k == K["body_back"] or i["key"] in ("holder", "cell", "battery"):
        continue
    m = S.mesh(k)
    if not (m.bounds[0] < np.array([PACK[a][1] for a in "xyz"]) + 1).all() or not (m.bounds[1] > np.array([PACK[a][0] for a in "xyz"]) - 1).all():
        continue
    try:
        v = (pk ^ man(m)).volume()
    except Exception as e:  # noqa: BLE001
        v = None
    if v is None or v > 1e-3:
        ov[i["key"] + f"#{k}"] = None if v is None else round(v, 2)
nb = new.copy(); nb.apply_transform(T)
v = (pk ^ man(nb)).volume(); ov["body_back (edited)"] = round(v, 2)
rep["pack_overlap_mm3"] = ov
# wall left: rays from the new cavity faces outward through body_back (trunk frame)
rmi = trimesh.ray.ray_triangle.RayMeshIntersector(nb); walls = {}
for lab, o, dvec in (("back -x", (-144.35, 1.4, 30), (-1, 0, 0)), ("rear +y chamfer", (-141.0, 20.25, 30), (-0.707, 0.707, 0)), ("rear -y chamfer", (-141.0, -17.35, 30), (-0.707, -0.707, 0)), ("left +y", (-130, 23.45, 30), (0, 1, 0)), ("right -y", (-130, -20.6, 30), (0, -1, 0)),
                     ("right -y low", (-130, -20.6, 5), (0, -1, 0)), ("left +y high", (-130, 23.45, 65), (0, 1, 0))):
    loc, ir, it = rmi.intersects_location([o], [dvec], multiple_hits=True)
    d = sorted(np.linalg.norm(loc - np.array(o), axis=1).round(2).tolist())
    walls[lab] = d[:4]
rep["wall_rays_mm"] = walls
# every fastener's screw segment against the cut (pilot radius about 1.0 to 1.25 mm): keep 1.5 mm of material
F = json.load(open(os.path.join(REPO, "altaay_lab", "fasteners", "fasteners.json")))["fasteners"]
lo = np.array([NEW[a][0] for a in "xyz"]); hi = np.array([NEW[a][1] for a in "xyz"]); near = {}
for f in F:
    sw = np.array(f["seat_world"], float); ax = np.array(f["axis_world"], float); L = float(f.get("length_mm") or 10)
    dmin = min(float(np.linalg.norm(np.maximum(0, np.maximum(lo - (sw + ax * L * t * sg), (sw + ax * L * t * sg) - hi)))) for t in np.linspace(0, 1, 41) for sg in (1, -1))
    if dmin < 6:
        near[f["id"]] = dict(spec=f.get("spec"), part=f.get("part"), into=f.get("into"), axis_dist_mm=round(dmin, 2))
rep["fasteners_within_6mm"] = near
new.export(os.path.join(OUT, "body_back.stl"))
json.dump(rep, open(os.path.join(OUT, "bay_edit.json"), "w"), indent=1)
print(json.dumps(rep, indent=1))
