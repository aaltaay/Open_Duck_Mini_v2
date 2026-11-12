"""Margin geometry for the structure twin (CAD check only until the FEA script reads the STLs).

Builds proposed STLs for the parts the 2026-11-03 FEA left under the walking margin of 2
or the soft-fall margin of 1.2. Nothing here is copied over print/. Holes that already
have a screw stay open (D39). No new screw is added, so the D42 pattern is unchanged.

The ear-wall bridge and the eye collar are sized to stay 1.5 mm clear of the servo cases
and of the thigh sheets through the hip pitch range. Hot PLA and the fall contact
stiffness are not inputs to this script.
"""
import os, sys, json
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
import st_fea_run as FR  # noqa: E402
import st_interfaces as SI  # noqa: E402

CLEAR_MM = 1.5


def m3_of(mesh):
    v = np.asarray(mesh.vertices, np.float32)
    f = np.asarray(mesh.faces, np.uint32)
    return m3.Manifold(m3.Mesh(vert_properties=v, tri_verts=f))


def mesh_of(man):
    me = man.to_mesh()
    return trimesh.Trimesh(np.asarray(me.vert_properties)[:, :3].astype(float), np.asarray(me.tri_verts).astype(int), process=False)


def apply_T(man, T):
    M = np.zeros((3, 4))
    M[:, :3] = np.asarray(T[:3, :3], float)
    M[:, 3] = np.asarray(T[:3, 3], float)
    return man.transform(M)


def box(lo, hi):
    lo = np.asarray(lo, float)
    hi = np.asarray(hi, float)
    size = np.maximum(hi - lo, 0.05)
    return m3.Manifold.cube(size.tolist()).translate(lo.tolist())


def load_link(part, link):
    T = FR.visual_T(link, part)
    m = trimesh.load(os.path.join(PRINT, part + ".stl"), force="mesh")
    m.apply_transform(T)
    if np.linalg.det(T[:3, :3]) < 0:
        m.invert()
    return m, T


def servo_cloud(link, near):
    meshes = FR.servo_meshes(link, near)
    if not meshes:
        return np.zeros((0, 3))
    return np.vstack([m.vertices for m in meshes])


def min_dist(pts, cloud):
    if not len(pts) or not len(cloud):
        return 1e9
    from scipy.spatial import cKDTree
    d, _ = cKDTree(cloud).query(pts, workers=1)
    return float(np.min(d))


def added_points(part_link, tool_link, n=4000):
    """points that the tool adds: on a grid inside the tool and outside the part"""
    both = mesh_of(tool_link)
    b0, b1 = both.bounds
    pitch = 0.8
    xs = np.arange(b0[0] + pitch / 2, b1[0], pitch)
    ys = np.arange(b0[1] + pitch / 2, b1[1], pitch)
    zs = np.arange(b0[2] + pitch / 2, b1[2], pitch)
    if not len(xs) or not len(ys) or not len(zs):
        return np.zeros((0, 3))
    X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij")
    pts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
    if len(pts) > n * 4:
        pts = pts[:: max(1, len(pts) // (n * 4))]
    inside_tool = both.contains(pts) if both.is_watertight else np.ones(len(pts), bool)
    inside_part = part_link.contains(pts)
    add = pts[inside_tool & ~inside_part]
    if len(add) > n:
        add = add[:: max(1, len(add) // n)]
    return add


def hip_pitch_sweep(parent_link, joint, child_parts, angles):
    """child part vertices in the parent link, over a list of joint angles (rad).

    URDF puts the joint origin on the child frame, and the axis is in that frame.
    The parent pose at angle q is origin @ rotation(q) about the child origin, not a
    rotation about the parent-frame point with the untransformed axis.
    """
    u = FR.urdf()
    jt = u.joint_map[joint]
    origin = FR.joint_in_link(parent_link, joint)
    axis = np.array(jt.axis, float)
    axis = axis / np.linalg.norm(axis)
    clouds = []
    for ang in angles:
        spin = trimesh.transformations.rotation_matrix(ang, axis, [0.0, 0.0, 0.0])
        T = origin @ spin
        for part, link in child_parts:
            m, _ = load_link(part, link)
            m.apply_transform(T)
            clouds.append(m.vertices)
    return np.vstack(clouds) if clouds else np.zeros((0, 3))


def horn_groups(link, part, kind):
    F = SI.fasteners()
    out = []
    for x in F:
        if x.get("link") == link and x.get("part") == part and x.get("anchor") == kind:
            out.append(x)
    return out


def eye_collar(mesh, screws, proud_mm=6.0, radius=32.0):
    """Thicken the head side of the horn eye by sliding the plate along the screw axis.
    The slide keeps the horn hole and the screw holes open, and it does not grow the outline,
    so it does not add a new free edge in the layer direction."""
    if len(screws) < 3:
        return None
    C = np.mean([np.array(x["seat_link"], float) for x in screws], 0)
    A = np.mean([np.array(x["axis_link"], float) for x in screws], 0)
    A = A / np.linalg.norm(A)
    z = np.array([0.0, 0.0, 1.0])
    x = np.array([1.0, 0.0, 0.0]) if abs(np.dot(A, z)) > 0.9 else np.cross(z, A)
    x = x / np.linalg.norm(x)
    y = np.cross(A, x)
    T = np.eye(4)
    T[:3, :3] = np.stack([x, y, A], 1)
    T[:3, 3] = C - A * 20.0
    cyl = apply_T(m3.Manifold.cylinder(40.0, radius, circular_segments=64), T)
    # The plate is about 3.3 mm thick. One slide longer than that leaves a gap, so the
    # pad is a stack of slides of 2.2 mm, each overlapping the last.
    base = m3_of(mesh)
    tool = None
    step = 2.2
    n = int(np.ceil(proud_mm / step))
    for k in range(1, n + 1):
        shift = np.eye(4)
        shift[:3, 3] = -A * step * k
        moved = apply_T(base, shift) ^ cyl
        tool = moved if tool is None else tool + moved
    return tool


def _clear(centre, clouds, extra=0.3):
    from scipy.spatial import cKDTree
    for cloud in clouds:
        if cloud is None or not len(cloud):
            continue
        if cKDTree(cloud).query(centre)[0] < CLEAR_MM + extra:
            return False
    return True


def roll_tool(mesh, clouds):
    """Fill only the air gap that follows a 4.5 to 6.5 mm ear wall, one small box per sample, and a short rib past each edge.
    A sample is kept only when its centre is CLEAR_MM away from every cloud (servo and the swept thigh)."""
    boxes = []
    ys = np.linspace(-18, 18, 37)
    zs = np.linspace(float(mesh.bounds[0, 2]) - 1, float(mesh.bounds[1, 2]) + 1, 43)
    x_start = float(mesh.bounds[0, 0]) - 5.0
    for y in ys:
        for z in zs:
            origin = np.array([x_start, y, z])
            loc, _, _ = mesh.ray.intersects_location(origin[None, :], np.array([[1.0, 0, 0]]))
            if len(loc) < 2:
                continue
            xs = np.sort(loc[:, 0])
            if len(xs) % 2:
                xs = xs[:-1]
            spans = list(zip(xs[0::2], xs[1::2]))
            for i, (a, b) in enumerate(spans):
                thick = b - a
                mid = 0.5 * (a + b)
                # only the ear wall beside the hip roll horns, not every 5 mm shell in the arm
                if not (4.3 <= thick <= 6.6 and 20.0 <= abs(mid) <= 40.0 and 6.0 <= z <= 38.0):
                    continue
                # Thicken the face farther from the hip roll axis by 3 mm, in x only.
                # A rib along y (the layer direction) failed in interlayer tension at its root.
                face = b if abs(b) >= abs(a) else a
                sign = 1.0 if face >= 0 else -1.0
                centre = np.array([face + sign * 1.3, y, z])
                # the sample is the box centre; the box reaches about 1.6 mm past it, so the centre
                # has to sit that far inside the 1.5 mm keep-out
                if not mesh.contains(centre[None, :])[0] and _clear(centre, clouds, extra=1.6):
                    # 0.25 mm overlap into the wall, then 2.6 mm outward. The overlap sign follows
                    # the face: on the negative-x wall, face - 0.25 sits in the air and leaves a gap.
                    lo = face - sign * 0.25
                    hi = face + sign * 2.6
                    if lo > hi:
                        lo, hi = hi, lo
                    boxes.append(box([lo, y - 0.55, z - 0.55], [hi, y + 0.55, z + 0.55]))
                # also grow the inboard face. The outboard side is 2 mm from the hip pitch servo,
                # and the soft-fall stress scaled with 1/thickness, so the extra section goes inward.
                inner = a if abs(a) <= abs(b) else b
                sign_i = -1.0 if inner > 0 else 1.0
                centre_i = np.array([inner + sign_i * 2.0, y, z])
                if not mesh.contains(centre_i[None, :])[0] and _clear(centre_i, clouds, extra=1.6):
                    lo = inner - sign_i * 0.25
                    hi = inner + sign_i * 4.0
                    if lo > hi:
                        lo, hi = hi, lo
                    boxes.append(box([lo, y - 0.55, z - 0.55], [hi, y + 0.55, z + 0.55]))
    if not boxes:
        return None
    tool = boxes[0]
    for b in boxes[1:]:
        tool = tool + b
    return tool


def check_clear(add_pts, clouds, label):
    rows = []
    ok = True
    for name, cloud in clouds:
        d = min_dist(add_pts, cloud)
        rows.append(dict(against=name, min_mm=round(d, 2)))
        if d < CLEAR_MM:
            ok = False
    return ok, rows


def export_part(part, link, tool_link, tag):
    mesh, T = load_link(part, link)
    base = m3_of(mesh)
    merged = base + tool_link
    out = mesh_of(merged)
    # back to the STL frame
    inv = np.linalg.inv(T)
    out.apply_transform(inv)
    if np.linalg.det(inv[:3, :3]) < 0:
        out.invert()
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, part + ".stl")
    out.export(path)
    return dict(part=part, link=link, tag=tag, stl=os.path.relpath(path, LAB),
                vol_before_mm3=round(float(mesh.volume), 1), vol_after_mm3=round(float(mesh_of(merged).volume), 1),
                faces=int(len(out.faces)), bytes=os.path.getsize(path))


def stack_along(mesh, direction, proud_mm, keep):
    """Connected thickness added by overlapping slides. keep is a manifold the slides are cut to."""
    direction = np.asarray(direction, float)
    direction = direction / np.linalg.norm(direction)
    base = m3_of(mesh)
    tool = None
    step = 2.0
    for k in range(1, int(np.ceil(proud_mm / step)) + 1):
        shift = np.eye(4)
        shift[:3, 3] = direction * step * k
        moved = apply_T(base, shift)
        if keep is not None:
            moved = moved ^ keep
        tool = moved if tool is None else tool + moved
    return tool


def main():
    os.makedirs(OUT, exist_ok=True)
    report = []
    # roll to pitch, both legs
    for part, link, joint, children in (
        ("left_roll_to_pitch", "left_roll_to_pitch_assembly", "left_hip_pitch",
         [("knee_to_ankle_left_sheet", "knee_and_ankle_assembly"), ("knee_to_ankle_right_sheet", "knee_and_ankle_assembly")]),
        ("right_roll_to_pitch", "right_roll_to_pitch_assembly", "right_hip_pitch",
         [("knee_to_ankle_left_sheet", "knee_and_ankle_assembly_3"), ("knee_to_ankle_right_sheet", "knee_and_ankle_assembly_3")]),
    ):
        mesh, T = load_link(part, link)
        near = FR.joint_in_link(link, joint)[:3, 3]
        servo = servo_cloud(link, near)
        u = FR.urdf()
        lim = u.joint_map[joint].limit
        angles = np.linspace(lim.lower, lim.upper, 7)
        swept = hip_pitch_sweep(link, joint, children, angles)
        tool = roll_tool(mesh, [servo, swept])
        if tool is None:
            report.append(dict(part=part, ok=False, why="no notch found"))
            continue
        add = added_points(mesh, tool)
        ok, rows = check_clear(add, [("hip pitch servo", servo), ("thigh sheets, full pitch range", swept)], part)
        rec = export_part(part, link, tool, "ear wall thickened in x, both faces, no rib along the layer direction")
        rec.update(ok_clearance=ok, clearance=rows, added_points=int(len(add)))
        report.append(rec)
        print(part, "clear", ok, rows, "dV", rec["vol_after_mm3"] - rec["vol_before_mm3"])
    # horn-eye collars on the drive plates
    eyes = [
        ("knee_to_ankle_left_sheet", "knee_and_ankle_assembly", "left_hip_pitch"),
        ("knee_to_ankle_right_sheet", "knee_and_ankle_assembly_3", "right_hip_pitch"),
        ("shin_left_sheet", "knee_and_ankle_assembly_2", "left_knee"),
        ("shin_right_sheet", "knee_and_ankle_assembly_4", "right_knee"),
    ]
    for part, link, joint in eyes:
        mesh, T = load_link(part, link)
        screws = horn_groups(link, part, "horn(drive)")
        tool = eye_collar(mesh, screws)
        if tool is None:
            report.append(dict(part=part, ok=False, why="no drive eye"))
            print(part, "no drive eye")
            continue
        add = added_points(mesh, tool)
        servo = servo_cloud(link, FR.joint_in_link(link, joint)[:3, 3])
        ok, rows = check_clear(add, [("servo case", servo)], part)
        rec = export_part(part, link, tool, "horn eye collar, head side, outside the screw heads")
        rec.update(ok_clearance=ok, clearance=rows, added_points=int(len(add)))
        report.append(rec)
        print(part, "clear", ok, rows, "dV", rec["vol_after_mm3"] - rec["vol_before_mm3"])
    # Neck sheets: soft falls are about 0.38. The sheet is 3.45 mm at the weak spot, and the
    # in-plane stress tracked 1/thickness on the ear wall, so the whole sheet grows 8 mm on its -z face.
    for part, link in (("neck_left_sheet", "neck_pitch_assembly"), ("neck_right_sheet", "neck_pitch_assembly")):
        mesh, T = load_link(part, link)
        servo = servo_cloud(link, FR.joint_in_link(link, "head_pitch")[:3, 3])
        best = None
        for direction in (np.array([0.0, 0.0, -1.0]), np.array([0.0, 0.0, 1.0])):
            tool = stack_along(mesh, direction, 8.0, None)
            add = added_points(mesh, tool)
            ok, rows = check_clear(add, [("head pitch servo", servo)], part)
            score = rows[0]["min_mm"] if rows else 0
            if best is None or score > best[0]:
                best = (score, ok, rows, tool, direction.tolist())
        score, ok, rows, tool, direction = best
        rec = export_part(part, link, tool, "neck sheet thickened 8 mm, direction %s" % direction)
        rec.update(ok_clearance=ok, clearance=rows, added_points=0, direction=direction)
        report.append(rec)
        print(part, "clear", ok, rows, "dir", direction, "dV", rec["vol_after_mm3"] - rec["vol_before_mm3"])
    # head_roll_mount: a 2.5 mm slab on the outer wall cleared the servo (3.3 mm) but the re-FEA
    # soft-fall worst went from 1.03 to 0.97, so the slab is not written.
    json.dump(report, open(os.path.join(HERE, "margin_geom.json"), "w"), indent=1)
    print("wrote", len(report), "rows")


if __name__ == "__main__":
    main()
