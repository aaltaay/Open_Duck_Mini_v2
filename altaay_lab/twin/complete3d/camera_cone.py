"""camera_cone.py: the Camera Module 3 field on the measured head seat. CAD check only and calc only.

Extends twin/complete3d/camera_seat.json. It does not move the seat, the screws, or the cable.

Run: python3 altaay_lab/twin/complete3d/camera_cone.py
Writes altaay_lab/twin/complete3d/camera_cone.json and altaay_lab/twin/camera/figs/*.png

The lens numbers are the Camera Module 3 product brief (June 2024, RP-008151-DS-1), standard column
(the bill line E6 is the standard module, not the wide one):
  https://datasheets.raspberrypi.com/camera/camera-module-3-product-brief.pdf
Page 3: Sony IMX708, 7.4 mm sensor diagonal, 1.4 um pixels, 4608 x 2592, module 25 x 24 x 11.5 mm.
Page 4 drawing: 66 deg across the 25 mm board edge, 41 deg across the 23.862 mm edge, lens diameter 5.75 mm.
Page 5: standard lens, focal length 4.74 mm, diagonal 75 deg, horizontal 66 deg, vertical 41 deg,
focus 10 cm to infinity, F1.8, infrared cut filter fitted.

On the installed head the 25 mm edge (the brief's horizontal, 66 deg) stands vertical. The 23.862 mm
edge (the brief's vertical, 41 deg) runs left to right. That is the seat in camera_seat.json: the
21 mm hole pitch, which is the 25 mm edge minus the 2 mm margins, lies along world z.
"""
import json
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import HEAD_LINK, LAB, scene, write_json  # noqa: E402

FIG = os.path.join(LAB, "twin", "camera", "figs")
SEAT = os.path.join(HERE, "camera_seat.json")
SIT = os.path.join(LAB, "twin", "sit", "sit_pose.json")
OUT = os.path.join(HERE, "camera_cone.json")

# brief, standard module, pages 3 to 5 (cited in the module docstring)
HFOV_DEG, VFOV_DEG, DFOV_DEG = 66.0, 41.0, 75.0
FOCAL_MM = 4.74
SENSOR_DIAG_MM = 7.4
PIX_UM = 1.4
PIX_HV = (4608, 2592)          # brief "horizontal/vertical", along the 66 deg and 41 deg axes
FOCUS_MM = (100.0, np.inf)     # 10 cm to infinity
LENS_D_MM = 5.75
BOARD_WH_MM = (25.0, 23.862)   # page 4, width (66 deg) by height (41 deg)
OVERALL_D_MM = 11.5            # page 3
PCB_CALLOUT_MM = 1.12          # page 4 side view, the thin board callout
HX = np.radians(HFOV_DEG / 2.0)   # along camera X: brief horizontal, installed up-down
HY = np.radians(VFOV_DEG / 2.0)   # along camera Y: brief vertical, installed left-right
# active area from the pixel count and the pixel size (calc only). The brief states the 7.4 mm diagonal.
ACTIVE_MM = (PIX_HV[0] * PIX_UM * 1e-3, PIX_HV[1] * PIX_UM * 1e-3)

# head pitch samples. Signs are checked at run time against the optical axis.
# soft and hard stops: software/servo_limits.json head_pitch. Runtime gamepad: cables3d/route_cables.py RUNTIME.
PITCHES_DEG = {
    "command_0": 0.0,             # sim/run_stock_walk.py schedule writes head_pitch 0 for the whole walk
    "soft_down": -22.0,           # servo_limits.json soft_lo
    "hard_down": -25.0,           # CAD contact, servo_limits.json hard_lo (the head forward stop)
    "runtime_up": float(np.degrees(0.3)),   # Runtime gamepad upper end, +0.3 rad
    "soft_up": 36.0,              # servo_limits.json soft_hi
}
# the Runtime lower end is -0.78 rad (-44.7 deg). The printed stop is -25 deg, so the head cannot go there.
RUNTIME_LO_DEG = float(np.degrees(-0.78))

# nest, twin/dock/nest/cad/NEST_CAD.md (CAD check only). Sun centre is the origin of that note.
SUN_R_MM = 50.0
RING_IN_MM, RING_OUT_MM = 82.0, 235.0
RING_CUT_DX_MM = 190.0 - 56.0     # the ring is cut 56 mm from the wall; the wall is 190 mm past the sun
RANGES_M = (0.30, 0.50, 0.75, 1.00, 1.50, 2.00)
SIDE_M = 0.25                     # the old dock start box was +/- 0.25 m (twin/dock/DOCK_TWIN.md). Not a nest start.
SKIP_HIT_MM = 8.0                 # ignore the lens hole and the 2.5 mm wall the pupil sits in
# parts that can hide the floor. Servo cases and the Pi stay out: they are inside a shell.
OCC_KEYS = {
    "head", "head_bot_sheet", "body_front", "body_back", "body_middle_top", "body_middle_bottom",
    "trunk_top", "trunk_bottom", "foot_top", "foot_side", "foot_bottom_tpu", "foot_bottom_pla",
    "shin_left_sheet", "shin_right_sheet", "knee_to_ankle_left_sheet", "knee_to_ankle_right_sheet",
    "left_roll_to_pitch", "right_roll_to_pitch", "neck_left_sheet", "neck_right_sheet",
    "head_pitch_to_yaw", "head_yaw_to_roll", "neck_pitch_assembly",
}


def active_diag():
    return float(np.hypot(*ACTIVE_MM))


def pinhole_fov_deg():
    """full-array pinhole from the brief focal length and the pixel grid. Not the number the cone uses."""
    return tuple(float(np.degrees(2 * np.arctan((a / 2) / FOCAL_MM))) for a in (*ACTIVE_MM, active_diag()))


def rect_diag_deg():
    """corner-to-corner of the 66 by 41 rectangle, calc only. The brief states 75 deg."""
    return float(np.degrees(2 * np.arctan(np.hypot(np.tan(HX), np.tan(HY)))))


def load_seat():
    seat = json.load(open(SEAT))
    R = np.array(seat["frame"]["T_cam_world"], float)[:3, :3]
    origin = np.array(seat["lens"]["opening_centre_world"], float)
    return seat, origin, R


def map_point(p0, link, Tl, Tt, T0):
    ph = np.ones(4)
    ph[:3] = p0
    return (Tt @ Tl[link] @ np.linalg.inv(T0[link]) @ ph)[:3]


def map_R(R0, link, Tl, Tt, T0):
    M = Tt @ Tl[link] @ np.linalg.inv(T0[link])
    return M[:3, :3] @ R0


def sole_min_z(S):
    z = []
    for i in S.inst:
        if i["key"] == "foot_bottom_tpu":
            z.append(S.world_mesh(i).vertices[:, 2].min())
    return float(min(z))


def toe_x(S, Tl, Tt):
    xs = []
    for i in S.inst:
        if i["key"] in ("foot_bottom_tpu", "foot_top", "foot_side"):
            m = S.world_mesh(i).copy()
            m.apply_transform(Tt @ Tl[i["link"]] @ np.linalg.inv(S.T0[i["link"]]))
            xs.append(m.vertices[:, 0].max())
    return float(max(xs))


def occ_mesh(S, Tl, Tt):
    parts = []
    for i in S.inst:
        if i["key"] not in OCC_KEYS:
            continue
        m = S.world_mesh(i).copy()
        m.apply_transform(Tt @ Tl[i["link"]] @ np.linalg.inv(S.T0[i["link"]]))
        parts.append(m)
    return trimesh.util.concatenate(parts)


def in_fov(d_world, R):
    """rectangular field. Camera X is the 66 deg axis, camera Y the 41 deg axis, camera Z forward."""
    d = R.T @ np.asarray(d_world, float)
    if d[2] <= 1e-9:
        return False, None, None
    tx = float(np.arctan2(d[0], d[2]))
    ty = float(np.arctan2(d[1], d[2]))
    return abs(tx) <= HX + 1e-8 and abs(ty) <= HY + 1e-8, tx, ty


def ray_dir(R, sx, sy):
    d = np.array([np.tan(sx * HX), np.tan(sy * HY), 1.0])
    d /= np.linalg.norm(d)
    return R @ d


def first_hits(mesh, origins, dirs, skip=SKIP_HIT_MM):
    origins = np.atleast_2d(np.asarray(origins, float))
    dirs = np.atleast_2d(np.asarray(dirs, float))
    if len(dirs) == 1 and len(origins) > 1:
        dirs = np.repeat(dirs, len(origins), 0)
    loc, ri, _ = mesh.ray.intersects_location(origins, dirs, multiple_hits=True)
    out = np.full(len(origins), np.inf)
    if len(ri):
        t = np.einsum("ij,ij->i", loc - origins[ri], dirs[ri])
        for r, tt in zip(ri, t):
            if skip < tt < out[r]:
                out[r] = tt
    return out


def floor_hit(origin, direction):
    if direction[2] >= -1e-9:
        return np.inf
    return float((0.0 - origin[2]) / direction[2])


def look(origin, R):
    fwd = R[:, 2]
    elev = float(np.degrees(np.arctan2(fwd[2], np.hypot(fwd[0], fwd[1]))))
    return dict(pupil_mm=[round(float(x), 2) for x in origin],
                forward=[round(float(x), 4) for x in fwd],
                elev_deg=round(elev, 2),
                height_mm=round(float(origin[2]), 2))


def centreline_floor(origin, R, mesh):
    """closest visible floor point on the forward vertical plane through the pupil (y held)."""
    best = None
    for s in np.linspace(0.15, 1.0, 18):
        d = ray_dir(R, s, 0.0)          # +camera X is down when the board is installed as measured
        if d[2] >= -1e-6:
            continue
        tf = floor_hit(origin, d)
        if not np.isfinite(tf):
            continue
        th = first_hits(mesh, origin, d)[0]
        p = origin + d * tf
        vis = th > tf - 1.0
        row = dict(x_mm=round(float(p[0]), 1), ahead_of_pupil_mm=round(float(p[0] - origin[0]), 1),
                   visible=bool(vis), blocked_mm=None if not np.isfinite(th) else round(float(th), 1))
        if not vis:
            if best is None:
                best = row
            continue
        if best is None or not best["visible"] or p[0] < best["x_mm"]:
            best = row
    return best


def foot_band(origin, R, mesh, toe, y_half=90.0):
    """floor cells from 40 mm behind the toe to 250 mm ahead, and whether the field sees them."""
    xs = np.arange(toe - 40.0, toe + 250.1, 10.0)
    ys = np.arange(-y_half, y_half + 0.1, 10.0)
    pts = np.array([(x, y, 0.0) for x in xs for y in ys])
    d = pts - origin
    dist = np.linalg.norm(d, axis=1)
    d = d / dist[:, None]
    inside = np.array([in_fov(di, R)[0] for di in d])
    hit = first_hits(mesh, np.repeat(origin[None], len(pts), 0), d)
    visible = inside & (hit > dist - 1.0)
    ahead = pts[:, 0] >= toe - 5.0
    return dict(cells=int(len(pts)), in_field=int(inside.sum()), visible=int(visible.sum()),
                visible_ahead_of_toe=int((visible & ahead).sum()),
                ahead_of_toe=int(ahead.sum()),
                nearest_visible_x_mm=None if not visible.any() else round(float(pts[visible, 0].min()), 1),
                toe_x_mm=round(float(toe), 1))


def nest_points(sun, toward_wall):
    """sun disc and ring samples. toward_wall is the unit direction from the sun toward the wall (the cut side)."""
    out = []
    out.append(("sun_centre", sun.copy(), "sun"))
    for k in range(12):
        a = 2 * np.pi * k / 12
        out.append(("sun_rim", sun + np.array([np.cos(a), np.sin(a), 0.0]) * SUN_R_MM, "sun"))
    for r, name in ((RING_IN_MM, "ring_in"), (RING_OUT_MM, "ring_out")):
        for k in range(16):
            a = 2 * np.pi * k / 16
            p = sun + np.array([np.cos(a), np.sin(a), 0.0]) * r
            dx = float(np.dot(p - sun, toward_wall))
            if dx > RING_CUT_DX_MM:
                continue
            out.append((name, p, "ring"))
    return out


def see_points(origin, R, mesh, points):
    rows = []
    if not points:
        return rows
    P = np.array([p for _, p, _ in points])
    d = P - origin
    dist = np.linalg.norm(d, axis=1)
    du = d / dist[:, None]
    hit = first_hits(mesh, np.repeat(origin[None], len(P), 0), du)
    for (name, p, kind), di, dist_i, th in zip(points, du, dist, hit):
        ok, tx, ty = in_fov(di, R)
        rows.append(dict(name=name, kind=kind, in_field=bool(ok),
                         occluded=bool(np.isfinite(th) and th < dist_i - 1.0),
                         slant_mm=round(float(dist_i), 1),
                         in_focus=bool(dist_i >= FOCUS_MM[0]),
                         tx_deg=None if tx is None else round(float(np.degrees(tx)), 2),
                         ty_deg=None if ty is None else round(float(np.degrees(ty)), 2)))
    return rows


def summarise(rows, kind):
    sub = [r for r in rows if r["kind"] == kind]
    seen = [r for r in sub if r["in_field"] and not r["occluded"] and r["in_focus"]]
    return dict(samples=len(sub), in_field=sum(r["in_field"] for r in sub),
                seen=len(seen),
                seen_frac=round(len(seen) / len(sub), 3) if sub else None)


def pixel_pair(origin, R, sun):
    """pixels across the 100 mm disc on a rectilinear sensor.

    The rectangular field is a pinhole: image position is c[axis] / c[2], and the
    half-width of the sensor is tan of the half angle. Lateral is the 2592 axis
    (41 deg, left-right). Near-to-far is the 4608 axis (66 deg, up-down).
    """
    left = sun + np.array([0.0, SUN_R_MM, 0.0])
    right = sun + np.array([0.0, -SUN_R_MM, 0.0])
    near = sun + np.array([-SUN_R_MM, 0.0, 0.0])   # toward the duck when the duck looks along +x and the sun is ahead
    far = sun + np.array([SUN_R_MM, 0.0, 0.0])

    def span(a, b, axis, n_pix, half):
        def u(p):
            c = R.T @ (np.asarray(p, float) - origin)
            if c[2] <= 1e-9:
                return None
            return c[axis] / c[2]
        ua, ub = u(a), u(b)
        if ua is None or ub is None:
            return None
        return abs(ua - ub) * (n_pix / (2.0 * np.tan(half)))

    px_lat = span(left, right, 1, PIX_HV[1], HY)
    px_dep = span(near, far, 0, PIX_HV[0], HX)
    slant = float(np.linalg.norm(sun - origin))
    # a disc of this diameter in a plane facing the camera, at the sun's camera-z (calc only, an upper bound)
    cz = float((R.T @ (sun - origin))[2])
    face_lat = (2 * SUN_R_MM / cz) * (PIX_HV[1] / (2.0 * np.tan(HY))) if cz > 1e-9 else None
    face_dep = (2 * SUN_R_MM / cz) * (PIX_HV[0] / (2.0 * np.tan(HX))) if cz > 1e-9 else None
    def rnd(v):
        return None if v is None else round(float(v), 1)

    return dict(slant_mm=round(slant, 1),
                lateral_px_still=rnd(px_lat),
                depth_px_still=rnd(px_dep),
                face_on_lateral_px=rnd(face_lat),
                face_on_depth_px=rnd(face_dep),
                lateral_px_1080_scale=rnd(None if px_lat is None else px_lat * 1080 / PIX_HV[1]),
                depth_px_1080_scale=rnd(None if px_dep is None else px_dep * 1920 / PIX_HV[0]),
                projection="rectilinear, c[axis]/c[2] times pixels over 2 tan(half angle)")


def approach(origin, R, mesh, toe, ranges, side_mm=0.0):
    """sun on the floor, horizontal range from the pupil, duck looking generally toward +x."""
    rows = []
    for rm in ranges:
        sun = np.array([origin[0] + rm * 1000.0, origin[1] + side_mm, 0.0])
        toward_wall = np.array([1.0, 0.0, 0.0])    # the duck walks toward the wall, which is past the sun
        pts = nest_points(sun, toward_wall)
        seen = see_points(origin, R, mesh, pts)
        # the near half of the ring is the half toward the duck (smaller x)
        near_ring = []
        for (name, p, kind), rec in zip(pts, seen):
            if kind == "ring" and p[0] <= sun[0]:
                near_ring.append(rec)
        rows.append(dict(
            range_m=rm,
            side_mm=side_mm,
            sun_x_mm=round(float(sun[0]), 1),
            toe_to_sun_mm=round(float(sun[0] - toe), 1),
            sun=summarise(seen, "sun"),
            ring=summarise(seen, "ring"),
            ring_near=summarise(near_ring, "ring"),
            pixels=pixel_pair(origin, R, sun),
            sun_centre=next(r for r in seen if r["name"] == "sun_centre"),
        ))
    return rows


def sit_target(S, Tl, Tt, origin, R, mesh):
    """the recorded sit, with the sun under the seat contact (the landing window is 45 mm, NEST_CAD)."""
    seat = None
    for i in S.inst:
        if i["key"] == "sit_seat":
            m = S.world_mesh(i).copy()
            m.apply_transform(Tt @ Tl[i["link"]] @ np.linalg.inv(S.T0[i["link"]]))
            low = m.vertices[m.vertices[:, 2] < 3.0]
            seat = low.mean(0) if len(low) else m.vertices.mean(0)
            break
    sun0 = np.array([seat[0], seat[1], 0.0])
    # facing the room: the sit head looks toward the duck's +x at this pose (checked by the forward vector).
    # the wall is behind the camera, opposite the forward horizontal heading.
    fwd = R[:, 2].copy()
    fwd[2] = 0.0
    fwd /= np.linalg.norm(fwd)
    toward_wall = -fwd
    out = []
    for name, off in (("under_seat", np.zeros(3)), ("window_45", toward_wall * 45.0), ("window_ahead", -toward_wall * 45.0)):
        sun = sun0 + off
        sun[2] = 0.0
        pts = nest_points(sun, toward_wall)
        seen = see_points(origin, R, mesh, pts)
        out.append(dict(place=name, sun_mm=[round(float(x), 1) for x in sun],
                        sun=summarise(seen, "sun"), ring=summarise(seen, "ring"),
                        pixels=pixel_pair(origin, R, sun),
                        sun_centre=next(r for r in seen if r["name"] == "sun_centre")))
    return dict(seat_contact_mm=[round(float(x), 1) for x in sun0], places=out)


def verts_of(S, Tl, Tt, keys):
    vs = []
    for i in S.inst:
        if i["key"] in keys:
            m = S.world_mesh(i).copy()
            m.apply_transform(Tt @ Tl[i["link"]] @ np.linalg.inv(S.T0[i["link"]]))
            v = m.vertices
            if len(v) > 800:
                v = v[:: max(1, len(v) // 800)]
            vs.append(v)
    return np.vstack(vs) if vs else np.zeros((0, 3))


def save_figs(pack):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    os.makedirs(FIG, exist_ok=True)
    paths = []

    def finish(fig, name):
        p = os.path.join(FIG, name)
        fig.savefig(p, dpi=110)
        plt.close(fig)
        paths.append(p)

    # side view: stand at command 0 and at the forward stop, lower and upper edges, floor, sun marks
    fig, ax = plt.subplots(figsize=(8.4, 4.2))
    stand = pack["poses"]["stand_command_0"]
    down = pack["poses"]["stand_hard_down"]
    body = pack["silhouettes"]["stand"]
    for pose, color, label in ((stand, "#1b4f72", "head pitch 0, lower and upper edge"),
                               (down, "#b9770e", "head pitch -25, lower and upper edge")):
        o = np.array(pose["look"]["pupil_mm"])
        R = np.array(pose["R"])
        for sx, lw in ((1, 1.6), (-1, 1.0)):
            d = ray_dir(R, sx, 0.0)
            t = floor_hit(o, d)
            if not np.isfinite(t) or t > 2200:
                t = 1600.0
            q = o + d * min(t, 2200.0)
            ax.plot([o[0], q[0]], [o[2], max(q[2], -5)], color=color, lw=lw, label=label if sx == 1 else None)
        ax.scatter([o[0]], [o[2]], c=color, s=22, zorder=5)
    ax.axhline(0, color="#1e8449", lw=1.2, label="floor")
    ax.plot([body["toe"], body["toe"]], [0, 40], color="#922b21", lw=1.4, label="forward toe")
    o0 = stand["look"]["pupil_mm"][0]
    for rm, mk in ((0.3, "o"), (0.5, "o"), (1.0, "s"), (2.0, "D")):
        ax.scatter([o0 + rm * 1000], [2], marker=mk, c="#b7950b", s=36, zorder=4)
    ax.annotate("0.3 m", (o0 + 300, 8), fontsize=7, color="#7d6608")
    ax.annotate("0.5", (o0 + 500, 8), fontsize=7, color="#7d6608")
    ax.annotate("1 m", (o0 + 1000, 8), fontsize=7, color="#7d6608")
    ax.annotate("2 m", (o0 + 2000, 8), fontsize=7, color="#7d6608")
    ax.set_xlim(-40, 2300)
    ax.set_ylim(-30, 520)
    ax.set_xlabel("x, mm, forward. URDF zero, soles on z = 0. CAD check only.")
    ax.set_ylabel("z, mm")
    ax.set_title("Side view. The wide 66 deg axis is up and down. Gold marks are the sun centre.")
    ax.legend(fontsize=7, loc="upper right")
    fig.tight_layout()
    finish(fig, "side_cone.png")

    # top view at pitch 0
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    o = np.array(stand["look"]["pupil_mm"])
    R = np.array(stand["R"])
    for sy, lw in ((1, 1.3), (-1, 1.3), (0, 0.8)):
        d = ray_dir(R, 0.0, sy)
        q = o + d * 2200
        ax.plot([o[0], q[0]], [o[1], q[1]], color="#1b4f72", lw=lw)
    ax.scatter([o[0]], [o[1]], c="#1b4f72", s=18, label="lens")
    for rm in RANGES_M:
        sun = np.array([o[0] + rm * 1000.0, o[1]])
        # at pitch 0 the disc centre is below the 66 deg field until 0.64 m (the side view)
        below = rm < 0.64
        col = "#aab7b8" if below else "#b7950b"
        ax.add_patch(plt.Circle(sun, SUN_R_MM, fill=False, ec=col, lw=1.2))
        ax.add_patch(plt.Circle(sun, RING_OUT_MM, fill=False, ec=col, lw=0.6, ls="--"))
        ax.add_patch(plt.Circle(sun, RING_IN_MM, fill=False, ec=col, lw=0.6, ls="--"))
    ax.plot([body["toe"], body["toe"]], [-200, 200], color="#922b21", lw=1, label="toe line")
    ax.set_xlim(-50, 2300)
    ax.set_ylim(-400, 400)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x, mm, forward")
    ax.set_ylabel("y, mm, left")
    ax.set_title("Top view, pitch 0. 41 deg is left to right. Grey is below the up-down field. CAD check only.", fontsize=9)
    ax.legend(fontsize=7, loc="upper right")
    fig.tight_layout()
    finish(fig, "top_cone.png")

    # floor visibility grids
    for key, title, fname in (
        ("stand_command_0", "Standing, head pitch 0. Floor the field can see.", "floor_stand.png"),
        ("stand_hard_down", "Standing, head at the -25 deg stop. Floor the field can see.", "floor_down.png"),
        ("sit", "Recorded sit (sim pose). Floor the field can see.", "floor_sit.png"),
    ):
        g = pack["grids"][key]
        fig, ax = plt.subplots(figsize=(7.4, 3.5))
        show = np.array(g["show"], float)   # 0 outside, 1 in field but blocked, 2 visible
        from matplotlib.colors import ListedColormap
        cmap = ListedColormap(["#2c1654", "#b9770e", "#f7dc6f"])
        ax.imshow(show, origin="lower", cmap=cmap, vmin=0, vmax=2,
                  extent=[g["x0"], g["x1"], g["y0"], g["y1"]], aspect="auto", interpolation="nearest")
        ax.plot([g["toe"], g["toe"]], [g["y0"], g["y1"]], color="#f5b7b1", lw=1.2, label="forward toe")
        ax.scatter([], [], c="#2c1654", s=40, label="outside the field")
        ax.scatter([], [], c="#b9770e", s=40, label="in the field, body in the way")
        ax.scatter([], [], c="#f7dc6f", s=40, label="on the floor, in the field")
        ax.set_xlabel("x, mm, forward")
        ax.set_ylabel("y, mm, left")
        ax.set_title(title + " CAD check only.")
        ax.legend(fontsize=7, loc="upper right")
        fig.tight_layout()
        finish(fig, fname)

    # pixels vs range
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    rr = [r["range_m"] for r in pack["approach_centre"]]
    ax.plot(rr, [r["pixels"]["lateral_px_still"] for r in pack["approach_centre"]], "o-", color="#1b4f72",
            label="across the disc, 2592 px axis (still)")
    ax.plot(rr, [r["pixels"]["depth_px_still"] for r in pack["approach_centre"]], "s-", color="#b9770e",
            label="near edge to far edge, 4608 px axis (still)")
    ax.plot(rr, [r["pixels"]["lateral_px_1080_scale"] for r in pack["approach_centre"]], "o--", color="#5dade2",
            label="across the disc if 1080p keeps the full field")
    ax.axvline(0.64, color="#922b21", lw=1, ls=":")
    ax.text(0.66, 1450, "level head:\ndisc enters\nthe field", fontsize=7, color="#922b21")
    ax.set_xlabel("horizontal range, lens to sun centre, m")
    ax.set_ylabel("pixels the disc would cover")
    ax.set_title("100 mm disc, head pitch 0. Left of the dotted line it is below the field. Calc only.")
    ax.legend(fontsize=7, loc="upper right")
    ax.set_ylim(0, 1850)
    fig.tight_layout()
    finish(fig, "pixels_range.png")
    return paths


def floor_grid(origin, R, mesh, toe):
    xs = np.arange(toe - 80.0, origin[0] + 2100.0, 20.0)
    ys = np.arange(-350.0, 350.1, 20.0)
    show = np.zeros((len(ys), len(xs)))
    origins = np.repeat(origin[None], len(xs) * len(ys), 0)
    pts = np.array([(x, y, 0.0) for y in ys for x in xs])
    d = pts - origin
    dist = np.linalg.norm(d, axis=1)
    du = d / dist[:, None]
    inside = np.array([in_fov(di, R)[0] for di in du])
    hit = first_hits(mesh, origins, du)
    vis = inside & (hit > dist - 1.0)
    blocked = inside & ~vis
    show.ravel()[blocked] = 1
    show.ravel()[vis] = 2
    return dict(show=show.tolist(), x0=float(xs[0]), x1=float(xs[-1]), y0=float(ys[0]), y1=float(ys[-1]),
                toe=float(toe), visible_cells=int(vis.sum()), blocked_cells=int(blocked.sum()))


def envelope(verts):
    if not len(verts):
        return dict(x=[], z=[])
    x = verts[:, 0]
    z = verts[:, 2]
    bins = np.linspace(x.min(), x.max(), 60)
    xs, lo, hi = [], [], []
    for a, b in zip(bins[:-1], bins[1:]):
        m = (x >= a) & (x < b)
        if m.sum() < 3:
            continue
        xs.append(0.5 * (a + b))
        lo.append(np.percentile(z[m], 2))
        hi.append(np.percentile(z[m], 98))
    return dict(x=xs + xs[::-1], z=hi + lo[::-1], toe=float(verts[:, 0].max()))


def main():
    S = scene()
    seat, origin0, R0 = load_seat()
    zsole = sole_min_z(S)
    # URDF zero, translated so the sole rests on z = 0. Neck and legs stay at 0.
    Tt0 = np.eye(4)
    Tt0[2, 3] = -zsole
    zero = {n: 0.0 for n in S.u.actuated_joint_names}
    Tl0 = S.link_T({})
    link = seat["frame"]["link"]
    assert link == HEAD_LINK

    def cam_at(joints_deg, Tt):
        Tl = S.link_T({k: np.radians(v) for k, v in joints_deg.items()}) if joints_deg else Tl0
        o = map_point(origin0, link, Tl, Tt, S.T0)
        R = map_R(R0, link, Tl, Tt, S.T0)
        # keep a right-handed copy for the json (lists)
        return Tl, o, R

    # confirm the axis map: camera X should point down (world -z) at pitch 0
    _, o, R = cam_at({}, Tt0)
    axis_note = dict(
        cam_X_world=[round(float(x), 4) for x in R[:, 0]],
        cam_Y_world=[round(float(x), 4) for x in R[:, 1]],
        cam_Z_world=[round(float(x), 4) for x in R[:, 2]],
        brief_66_on="camera X, the 25 mm board edge",
        brief_41_on="camera Y, the 23.862 mm board edge",
    )

    poses = {}
    grids = {}
    sil = {}
    # standing pitches
    stand_mesh = None
    stand_tl = None
    for name, deg in PITCHES_DEG.items():
        Tl, o, Rm = cam_at({"head_pitch": deg}, Tt0)
        if stand_mesh is None:
            stand_mesh = occ_mesh(S, Tl, Tt0)
            stand_tl = Tl
            sil["stand"] = envelope(verts_of(S, Tl, Tt0, {"head", "body_front", "body_middle_top", "foot_top", "foot_side"}))
            sil["stand"]["toe"] = toe_x(S, Tl, Tt0)
        elif abs(deg) > 0:  # head moved: rebuild, the legs did not
            stand_mesh_p = occ_mesh(S, Tl, Tt0)
        toe = sil["stand"]["toe"]
        mesh = stand_mesh if abs(deg) < 1e-9 else stand_mesh_p
        key = "stand_" + name
        poses[key] = dict(
            joints_deg={"head_pitch": round(deg, 2)},
            look=look(o, Rm),
            R=Rm.tolist(),
            floor=centreline_floor(o, Rm, mesh),
            feet=foot_band(o, Rm, mesh, toe),
            toe_x_mm=round(toe, 1),
        )
        if name in ("command_0", "hard_down"):
            grids[key] = floor_grid(o, Rm, mesh, toe)

    # sit: recorded pose. Joints and trunk are sim pass only. The rays on that pose are CAD check only.
    sitp = json.load(open(SIT))
    Tt_s = np.array(sitp["trunk_T_mm"], float)
    Tl_s, o_s, R_s = cam_at(sitp["joints_deg"], Tt_s)
    mesh_s = occ_mesh(S, Tl_s, Tt_s)
    toe_s = toe_x(S, Tl_s, Tt_s)
    poses["sit"] = dict(
        label_pose="sim pass only (sit_pose.json)",
        joints_deg={k: sitp["joints_deg"][k] for k in ("neck_pitch", "head_pitch", "head_yaw", "head_roll")},
        trunk_pitch_deg=sitp["trunk_pitch_deg"],
        look=look(o_s, R_s),
        R=R_s.tolist(),
        floor=centreline_floor(o_s, R_s, mesh_s),
        feet=foot_band(o_s, R_s, mesh_s, toe_s),
        toe_x_mm=round(toe_s, 1),
        nest=sit_target(S, Tl_s, Tt_s, o_s, R_s, mesh_s),
    )
    grids["sit"] = floor_grid(o_s, R_s, mesh_s, toe_s)

    # approach from the level head and from the forward stop
    appr = {}
    for key in ("stand_command_0", "stand_hard_down"):
        Tl, o, Rm = cam_at({"head_pitch": poses[key]["joints_deg"]["head_pitch"]}, Tt0)
        mesh = stand_mesh if key.endswith("command_0") else occ_mesh(S, Tl, Tt0)
        toe = poses[key]["toe_x_mm"]
        appr[key] = approach(o, Rm, mesh, toe, RANGES_M, 0.0)
        appr[key + "_side"] = approach(o, Rm, mesh, toe, (0.30, 0.50, 1.0, 2.0), SIDE_M * 1000.0)

    ph, pv, pd = pinhole_fov_deg()
    # hole vs the brief cone, from the seat's measured opening and the PCB-to-wall gap
    opening_r = seat["lens"]["opening_d_mm"] / 2.0
    gap = seat["lens"]["pcb_front_to_wall_mm"]   # PCB front to the inner wall
    # a pupil on the PCB front face clears the inner rim out to this half angle
    hole_half_deg = float(np.degrees(np.arctan(opening_r / gap))) if gap else None
    # page 3 overall depth includes the board. The lens front is that depth minus the 1.12 mm board callout,
    # ahead of the PCB front face. The outer wall is the seat's inner gap plus the wall thickness.
    lens_ahead_of_pcb_front = OVERALL_D_MM - PCB_CALLOUT_MM
    proud = lens_ahead_of_pcb_front - (gap + seat["lens"]["wall_t_mm"])

    out = dict(
        meta=dict(
            script="altaay_lab/twin/complete3d/camera_cone.py",
            seat="altaay_lab/twin/complete3d/camera_seat.json",
            brief="https://datasheets.raspberrypi.com/camera/camera-module-3-product-brief.pdf",
            brief_id="RP-008151-DS-1, June 2024",
            module="Raspberry Pi Camera Module 3 standard, BOM E6, Adafruit 5657",
            labels="FOV and sensor: cited from the brief. Pose: CAD check only, except the sit joints which are sim pass only. "
                   "Pixels and the pinhole check: calc only. A real frame was not taken.",
        ),
        brief=dict(
            sensor="Sony IMX708",
            sensor_diagonal_mm=SENSOR_DIAG_MM,
            pixel_um=PIX_UM,
            pixels_hv=list(PIX_HV),
            active_mm=[round(ACTIVE_MM[0], 4), round(ACTIVE_MM[1], 4)],
            active_diagonal_mm=round(active_diag(), 3),
            focal_mm=FOCAL_MM,
            hfov_deg=HFOV_DEG,
            vfov_deg=VFOV_DEG,
            dfov_deg=DFOV_DEG,
            f_number=1.8,
            focus_cm=[10, "infinity"],
            ir_cut=True,
            board_mm=[25.0, 23.862, 11.5],
            lens_diameter_mm=LENS_D_MM,
            pcb_side_view_mm=PCB_CALLOUT_MM,
            pinhole_hvd_deg=[round(ph, 2), round(pv, 2), round(pd, 2)],
            rectangle_diagonal_deg=round(rect_diag_deg(), 2),
        ),
        install=dict(
            axis=axis_note,
            opening_d_mm=seat["lens"]["opening_d_mm"],
            wall_t_mm=seat["lens"]["wall_t_mm"],
            pcb_front_to_inner_wall_mm=gap,
            hole_half_angle_from_pcb_front_deg=round(hole_half_deg, 1),
            lens_proud_of_outer_wall_mm=round(float(proud), 2),
            zero_sole_z_mm=round(zsole, 2),
            note="66 deg is up-down on this head. 41 deg is left-right. The pupil used for the rays is the measured lens opening centre. "
                 "The brief does not mark the entrance pupil (BLOCKER for that point, a few millimetres).",
        ),
        pitches_deg={k: round(v, 2) for k, v in PITCHES_DEG.items()},
        runtime_command_lo_deg=round(RUNTIME_LO_DEG, 2),
        runtime_lo_unreachable="the gamepad asks for -44.7 deg. The printed forward stop is -25 deg.",
        poses={k: {kk: vv for kk, vv in p.items() if kk != "R"} for k, p in poses.items()},
        approach=appr,
        grids={k: {kk: vv for kk, vv in g.items() if kk != "show"} for k, g in grids.items()},
    )
    # figures need R and the grids' show arrays; keep them out of the json by passing a side pack
    pack = dict(poses=poses, grids=grids, silhouettes=sil, approach_centre=appr["stand_command_0"])
    paths = save_figs(pack)
    out["figures"] = [os.path.relpath(p, os.path.join(LAB, "..")) for p in paths]
    write_json(out, OUT)
    # a short print for the report
    print("sole z", round(zsole, 2), "axis", axis_note["cam_X_world"], axis_note["cam_Z_world"])
    print("pinhole", out["brief"]["pinhole_hvd_deg"], "rect diag", out["brief"]["rectangle_diagonal_deg"], "proud", proud, "hole half", hole_half_deg)
    for k, p in poses.items():
        print(k, "elev", p["look"]["elev_deg"], "h", p["look"]["height_mm"], "floor", p["floor"], "feet vis", p["feet"]["visible_ahead_of_toe"], "/", p["feet"]["ahead_of_toe"], "near x", p["feet"]["nearest_visible_x_mm"])
    if "nest" in poses["sit"]:
        for pl in poses["sit"]["nest"]["places"]:
            print("sit", pl["place"], pl["sun"], pl["ring"], "centre", pl["sun_centre"])
    for row in appr["stand_command_0"]:
        print("appr0", row["range_m"], "sun", row["sun"], "ring", row["ring"], "near", row["ring_near"], "px", row["pixels"]["lateral_px_still"], row["pixels"]["depth_px_still"], "toe", row["toe_to_sun_mm"], "ctr", row["sun_centre"]["in_field"], row["sun_centre"]["occluded"])
    for row in appr["stand_hard_down"]:
        print("appr-25", row["range_m"], "sun", row["sun"]["seen_frac"], "ring", row["ring"]["seen_frac"], "near", row["ring_near"]["seen_frac"], "ctr", row["sun_centre"])
    for row in appr["stand_command_0_side"]:
        print("side0", row["range_m"], "sun", row["sun"]["seen_frac"], "ring", row["ring"]["seen_frac"], "ctr", row["sun_centre"]["in_field"], row["sun_centre"]["ty_deg"])
    for row in appr["stand_hard_down_side"]:
        print("side-25", row["range_m"], "sun", row["sun"]["seen_frac"], "ring", row["ring"]["seen_frac"], "ctr", row["sun_centre"]["in_field"])
    for pth in paths:
        print("fig", os.path.basename(pth), os.path.getsize(pth))


if __name__ == "__main__":
    main()
