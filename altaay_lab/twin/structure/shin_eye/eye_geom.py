"""Shin drive eye shapes (CAD check only until eye_fea.py reads them).

The topology collar already grew the head side of the eye. The servo-facing face
stays put: that gap is about 2 mm. These shapes add a taper past the collar,
on the head side only, and a head recess that keeps the existing horn screws.
Nothing is copied over print/. A hole that has a screw stays open (D39). No
screw is added (D42).
"""
import os
import sys
import json
import numpy as np
import trimesh
import manifold3d as m3

HERE = os.path.dirname(os.path.abspath(__file__))
STRUCT = os.path.abspath(os.path.join(HERE, ".."))
LAB = os.path.abspath(os.path.join(STRUCT, "../.."))
REPO = os.path.abspath(os.path.join(LAB, ".."))
PRINT = os.path.join(REPO, "print")
OUT = os.path.join(HERE, "stl")
sys.path.insert(0, STRUCT)
sys.path.insert(0, os.path.join(STRUCT, "topology"))
import st_fea_run as FR  # noqa: E402
import margin_geom as MG  # noqa: E402

CLEAR_MM = 1.5
# DIN 912 M3 head, knurl up to 5.68 mm (fasteners.json source note). The recess
# is 5.8 mm so the head still lands on the original seat and the M3x6 still fits.
HEAD_D = 5.8
LINK = "knee_and_ankle_assembly_2"
PART = "shin_left_sheet"


def m3_of(mesh):
    v = np.asarray(mesh.vertices, np.float32)
    f = np.asarray(mesh.faces, np.uint32)
    return m3.Manifold(m3.Mesh(vert_properties=v, tri_verts=f))


def mesh_of(man):
    me = man.to_mesh()
    return trimesh.Trimesh(np.asarray(me.vert_properties)[:, :3].astype(float),
                           np.asarray(me.tri_verts).astype(int), process=False)


def apply_T(man, T):
    M = np.zeros((3, 4))
    M[:, :3] = np.asarray(T[:3, :3], float)
    M[:, 3] = np.asarray(T[:3, 3], float)
    return man.transform(M)


def cylinder(center, axis, radius, half):
    axis = np.asarray(axis, float)
    axis = axis / np.linalg.norm(axis)
    z = np.array([0.0, 0.0, 1.0])
    x = np.array([1.0, 0.0, 0.0]) if abs(np.dot(axis, z)) > 0.9 else np.cross(z, axis)
    x = x / np.linalg.norm(x)
    y = np.cross(axis, x)
    T = np.eye(4)
    T[:3, :3] = np.stack([x, y, axis], 1)
    T[:3, 3] = np.asarray(center, float) - axis * half
    return apply_T(m3.Manifold.cylinder(2 * half, radius, circular_segments=48), T)


def drive_screws(link, part):
    rows = MG.horn_groups(link, part, "horn(drive)")
    C = np.mean([np.array(x["seat_link"], float) for x in rows], 0)
    A = np.mean([np.array(x["axis_link"], float) for x in rows], 0)
    A = A / np.linalg.norm(A)
    return rows, C, A


def knee_servo_cloud():
    """Knee servo case in the shin link. The case lives on the parent link."""
    u = FR.urdf()
    jt = u.joint_map["left_knee"]
    origin = FR.joint_in_link(jt.parent, "left_knee")
    meshes = FR.servo_meshes(jt.parent, origin[:3, 3])
    pts = np.vstack([m.vertices for m in meshes])
    inv = np.linalg.inv(origin)
    return (inv @ np.c_[pts, np.ones(len(pts))].T).T[:, :3]


def other_clouds(link):
    clouds = [("knee servo", knee_servo_cloud())]
    ankle = FR.joint_in_link(link, "left_ankle")[:3, 3]
    clouds.append(("ankle servo", MG.servo_cloud(link, ankle)))
    for part in ("shin_right_sheet", "shin_spacer"):
        m, _ = MG.load_link(part, link)
        clouds.append((part, m.vertices))
    return clouds


def added_points(base, tool, pitch=0.8):
    both = mesh_of(tool)
    b0, b1 = both.bounds
    xs = np.arange(b0[0] + pitch / 2, b1[0], pitch)
    ys = np.arange(b0[1] + pitch / 2, b1[1], pitch)
    zs = np.arange(b0[2] + pitch / 2, b1[2], pitch)
    if not len(xs) or not len(ys) or not len(zs):
        return np.zeros((0, 3))
    X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij")
    pts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
    if len(pts) > 250000:
        pts = pts[:: max(1, len(pts) // 250000)]
    inside_tool = both.contains(pts)
    inside_base = base.contains(pts)
    return pts[inside_tool & ~inside_base]


def clearance(pts, clouds):
    rows = []
    ok = True
    for name, cloud in clouds:
        d = MG.min_dist(pts, cloud)
        rows.append(dict(against=name, min_mm=round(d, 2)))
        if d < CLEAR_MM:
            ok = False
    return ok, rows


def holes_open(mesh, screws, radius=1.2):
    """CAD check: the screw axis is not solid (D39, the hole stays open)."""
    out = []
    for x in screws:
        c = np.array(x["seat_link"], float)
        a = np.array(x["axis_link"], float)
        a = a / np.linalg.norm(a)
        ts = np.linspace(-1.0, float(x["near"]) + 1.0, 12)
        pts = c + ts[:, None] * a
        solid = int(mesh.contains(pts).sum())
        out.append(dict(id=x["id"], solid_samples=solid, n=len(pts)))
    return out


def taper_tool(stock, center, axis, bands):
    """Slides of the plate along -axis, each clipped to a radius. bands is (proud mm, radius mm)."""
    base = m3_of(stock)
    tool = None
    for proud, radius in bands:
        keep = cylinder(center, axis, radius, 30.0)
        # overlap the plate so the slide is one solid, same reason as the topology stack
        n = int(np.ceil(proud / 2.2))
        for k in range(1, n + 1):
            shift = np.eye(4)
            shift[:3, 3] = -axis * min(2.2 * k, proud)
            moved = apply_T(base, shift) ^ keep
            tool = moved if tool is None else tool + moved
    return tool


def counterbore_tool(screws, depth_from_seat=8.0):
    """Head recess on the head side of the original seat. The shank hole is untouched."""
    tool = None
    for x in screws:
        c = np.array(x["seat_link"], float)
        a = np.array(x["axis_link"], float)
        a = a / np.linalg.norm(a)
        mid = c - a * (depth_from_seat / 2.0)
        cyl = cylinder(mid, a, HEAD_D / 2.0, depth_from_seat / 2.0 + 0.4)
        tool = cyl if tool is None else tool + cyl
    return tool


def export_link(part, link, man_link, tag):
    T = FR.visual_T(link, part)
    out = mesh_of(man_link)
    inv = np.linalg.inv(T)
    out.apply_transform(inv)
    if np.linalg.det(inv[:3, :3]) < 0:
        out.invert()
    parts = out.split(only_watertight=False)
    out = max(parts, key=lambda p: abs(float(p.volume)))
    out = mesh_of(m3_of(out))
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, part + ".stl")
    out.export(path)
    return dict(part=part, tag=tag, bytes=os.path.getsize(path),
                faces=int(len(out.faces)),
                vol_mm3=round(float(mesh_of(man_link).volume), 1),
                watertight=bool(out.is_watertight),
                components=int(len(out.split(only_watertight=False))))


def build():
    stock, _ = MG.load_link(PART, LINK)
    screws, center, axis = drive_screws(LINK, PART)
    clouds = other_clouds(LINK)
    # The topology collar is 6.6 mm inside 32 mm. The taper steps that down
    # so the 6 mm cliff at 32 mm is not the section change.
    bands = ((6.6, 32.0), (4.4, 40.0), (2.2, 48.0))
    report = []
    tool = taper_tool(stock, center, axis, bands)
    add = added_points(stock, tool)
    ok, rows = clearance(add, clouds)
    merged = m3_of(stock) + tool
    mesh = mesh_of(merged)
    rec = export_link(PART, LINK, merged, "taper past the collar, head side")
    # export_link writes PART.stl. Keep a second name by copying after.
    taper_path = os.path.join(OUT, "shin_left_sheet_taper.stl")
    os.replace(os.path.join(OUT, PART + ".stl"), taper_path)
    rec.update(stl="twin/structure/shin_eye/stl/shin_left_sheet_taper.stl",
               ok_clearance=ok, clearance=rows, added_points=int(len(add)),
               holes=holes_open(mesh, screws), bands=[{"proud_mm": p, "radius_mm": r} for p, r in bands],
               screw_centre=np.round(center, 2).tolist(), axis=np.round(axis, 3).tolist())
    report.append(rec)
    print("taper", ok, rows, "dV", rec["vol_mm3"] - round(float(stock.volume), 1), flush=True)

    # The collar moves the peak off the eye onto the thin run of plate (about y -32 to -42).
    # A web on the head side of that run, full width, does not grow toward the knee servo.
    web = taper_tool(stock, center + np.array([0.0, -36.0, 0.0]), axis, ((6.6, 18.0),))
    both = merged + web
    wadd = added_points(mesh_of(merged), both)
    wok, wrows = clearance(wadd, clouds)
    wmesh = mesh_of(both)
    wrec = export_link(PART, LINK, both, "taper plus a web on the thin run of plate")
    web_path = os.path.join(OUT, "shin_left_sheet_web.stl")
    os.replace(os.path.join(OUT, PART + ".stl"), web_path)
    wrec.update(stl="twin/structure/shin_eye/stl/shin_left_sheet_web.stl",
                ok_clearance=wok, clearance=wrows, holes=holes_open(wmesh, screws))
    report.append(wrec)
    print("web", wok, wrows, flush=True)

    bore = counterbore_tool(screws)
    bored = merged - bore
    bmesh = mesh_of(bored)
    badd = added_points(stock, bored)
    bok, brows = clearance(badd, clouds)
    brec = export_link(PART, LINK, bored, "taper plus M3 head recess on the original seat")
    bore_path = os.path.join(OUT, "shin_left_sheet_taper_cbore.stl")
    os.replace(os.path.join(OUT, PART + ".stl"), bore_path)
    brec.update(stl="twin/structure/shin_eye/stl/shin_left_sheet_taper_cbore.stl",
                ok_clearance=bok, clearance=brows, holes=holes_open(bmesh, screws),
                head_d_mm=HEAD_D)
    report.append(brec)
    web_bored = both - bore
    wbmesh = mesh_of(web_bored)
    wbrec = export_link(PART, LINK, web_bored, "web plus the M3 head recess")
    wbpath = os.path.join(OUT, "shin_left_sheet_web_cbore.stl")
    os.replace(os.path.join(OUT, PART + ".stl"), wbpath)
    wbrec.update(stl="twin/structure/shin_eye/stl/shin_left_sheet_web_cbore.stl",
                 holes=holes_open(wbmesh, screws), head_d_mm=HEAD_D)
    report.append(wbrec)
    print("web cbore", wbrec["holes"], flush=True)
    print("cbore", bok, "holes", brec["holes"], flush=True)

    # gap from the stock servo-facing face to the knee case, at the screw radius
    servo = clouds[0][1]
    from scipy.spatial import cKDTree
    face = stock.vertices[np.linalg.norm(stock.vertices[:, :2] - center[:2], axis=1) < 12]
    face = face[face[:, 2] > -1.0]
    if len(face):
        d, _ = cKDTree(servo).query(face)
        i = int(np.argmin(d))
        report.append(dict(tag="servo-facing face", min_mm=round(float(d.min()), 2),
                           at=np.round(face[i], 2).tolist()))
        print("face gap", report[-1], flush=True)
    # The published collar, with the same head recess, so the M3x6 horn screws still land
    # on the original seat. The recess is at the eye. The thin-plate peak is not.
    topo = trimesh.load(os.path.join(STRUCT, "topology", "stl", PART + ".stl"), force="mesh")
    Tvis = FR.visual_T(LINK, PART)
    topo.apply_transform(Tvis)
    if np.linalg.det(Tvis[:3, :3]) < 0:
        topo.invert()
    coll = m3_of(topo) - counterbore_tool(screws)
    crec = export_link(PART, LINK, coll, "published collar plus the M3 head recess")
    cpath = os.path.join(OUT, "shin_left_sheet_collar_cbore.stl")
    os.replace(os.path.join(OUT, PART + ".stl"), cpath)
    crec.update(stl="twin/structure/shin_eye/stl/shin_left_sheet_collar_cbore.stl",
                holes=holes_open(mesh_of(coll), screws), head_d_mm=HEAD_D)
    report.append(crec)
    print("collar cbore holes", crec["holes"], flush=True)
    json.dump(report, open(os.path.join(HERE, "geom.json"), "w"), indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    build()
