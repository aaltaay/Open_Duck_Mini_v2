"""ear_mount.py: how the two ear SG90s (the antenna servos, GPIO12 and 13) are held in the head. CAD check only.

Run: python3 altaay_lab/twin/companion/ear_mount.py --out <folder outside the repo> [--glb <viewer duck.glb or duck.glb.txt>]
        [--write-fasteners]
Writes altaay_lab/twin/companion/ear_mount.json and, in --out, per ear: a section through the tab holes, a section
across the plate and two 3D close-ups from inside the head. With --write-fasteners the SG90 tab screw rows (F348 to
F351) of fasteners/fasteners.json and fasteners.csv get the measured pilot axis (pilot_axis_measured_deg) and the
corrected note, the same text fasteners/make_fasteners.py now writes.

Pose: the SG90 instances of audit/assembly.json (URDF zero pose), moved into the head.stl frame with the head
instance transform. With --glb the viewer's own pose is read from the GLB (node head_assembly-sg90-1 and -2 against
head_assembly-head-1) and compared; the head mesh is then also checked in its decimated viewer form.

Checks per ear and per head STL (print/head.stl, the printable copy; twin/companion/stl/head.stl, the twin copy with
the mic seats; the viewer mesh when --glb is given):
  1. tab contact: rays from 0.3 mm below the tab top face along the servo axis on a 0.25 mm grid over both tabs
     (hole areas left out); a ray that meets plastic within 0.15 mm of the tab face is contact.
  2. plate thickness above the tabs: the same rays, entry to exit.
  3. pilots: 24 radial rays at 7 depths from each tab hole axis give the pilot centre and diameter; PCA of the pilot
     wall vertices gives its axis against the tab axis.
  4. what stops the servo turning: the servo surface is sampled (120000 points); points within 0.15 mm of the head
     are contact, summed per face group (body end faces above the tabs bear on the pocket ends).
  5. gaps from the body to the plastic: rays from each body face along its normal at 4 heights.
  6. ear travel: the antenna holder and rod of each side over the URDF limits (-90 to 90 deg, 5 deg steps): least
     distance to the head shell, to the mic board envelopes (mic_seats.json) and to the camera box.
"""
import argparse
import base64
import io
import json
import os
import sys

import numpy as np
import trimesh
import yourdfpy
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(LAB)
URDF_DIR = os.path.join(REPO, "mini_bdx", "robots", "open_duck_mini_v2")
HEADS = {"print/head.stl": os.path.join(REPO, "print", "head.stl"),
         "twin/companion/stl/head.stl": os.path.join(HERE, "stl", "head.stl")}
TAB_TOP, TAB_BOT, HOLE_X, HOLE_R = 19.2, 16.7, 13.75, 1.0     # sg90.stl, mm, servo frame (z = output shaft)
BODY_X, BODY_Y, BODY_TOP = 11.5, 6.5, 23.42
SHAFT = np.array([5.675, 0.0])                                 # output shaft axis in the servo frame (boss centre)
SIDES = ("left", "right")                                      # sg90 instance 0 is left (+y), 1 is right


def r(x, n=2):
    return None if x is None or (isinstance(x, float) and not np.isfinite(x)) else round(float(x), n)


def load_pose():
    a = json.load(open(os.path.join(LAB, "audit", "assembly.json")))
    T = {}
    for i in a["inst"]:
        T.setdefault(i["mesh"], []).append(np.array(i["T"]))
    Th = T["head.stl"][0]
    return Th, [np.linalg.inv(Th) @ t for t in T["sg90.stl"]]


def load_glb(path):
    data = open(path, "rb").read()
    if path.endswith(".txt"):
        data = base64.b64decode(data)
    sc = trimesh.load(io.BytesIO(data), file_type="glb", force="scene")
    Th, gh = sc.graph["head_assembly-head-1"]
    out = []
    for n in ("head_assembly-sg90-1", "head_assembly-sg90-2"):
        T, _ = sc.graph[n]
        out.append(np.linalg.inv(np.array(Th)) @ np.array(T))
    return sc.geometry[gh].copy(), out


def sg90():
    m = trimesh.load(os.path.join(URDF_DIR, "sg90.stl"), force="mesh")
    m.apply_scale(1000.0)
    return m


def hits(mesh, M, p, d):
    o = trimesh.transform_points([p], M)[0]
    dw = M[:3, :3] @ np.asarray(d, float)
    loc, _, _ = mesh.ray.intersects_location([o], [dw], multiple_hits=True)
    return np.sort(np.linalg.norm(loc - o, axis=1)) if len(loc) else np.array([])


def check_ear(mesh, M, s0, pts, nrm, dA):
    out = {}
    g = 0.25
    tabs = []
    for sx in (1, -1):
        area = contact = 0.0
        gaps, thick = [], []
        for x in np.arange(BODY_X + g / 2, 16.3, g):
            for y in np.arange(-BODY_Y + g / 2, BODY_Y, g):
                if (x - HOLE_X) ** 2 + y ** 2 < HOLE_R ** 2:
                    continue
                h = hits(mesh, M, [sx * x, y, TAB_TOP - 0.3], [0, 0, 1])
                gap = h[0] - 0.3 if len(h) else np.inf
                area += g * g
                gaps.append(gap)
                if abs(gap) < 0.15:
                    contact += g * g
                    if len(h) > 1:
                        thick.append(h[1] - h[0])
        gaps = np.array(gaps)
        # pilot: centre and diameter from radial rays, axis from the wall vertices
        cs, ds = [], []
        for dz in (0.3, 1.0, 1.5, 2.0, 3.0, 3.5, 4.0):
            q = []
            for ang in np.linspace(0, 2 * np.pi, 24, endpoint=False):
                h = hits(mesh, M, [sx * HOLE_X, 0, TAB_TOP + dz], [np.cos(ang), np.sin(ang), 0])
                rr = h[0] if len(h) else np.nan
                q.append([sx * HOLE_X + rr * np.cos(ang), rr * np.sin(ang)])
            q = np.array(q)
            c = np.nanmean(q, 0)
            cs.append(np.linalg.norm(c - [sx * HOLE_X, 0]))
            ds.append(2 * np.nanmean(np.linalg.norm(q - c, axis=1)))
        hc = hits(mesh, M, [sx * HOLE_X, 0, TAB_TOP - 0.3], [0, 0, 1])
        v = trimesh.transform_points(mesh.vertices, np.linalg.inv(M))
        sel = v[(np.hypot(v[:, 0] - sx * HOLE_X, v[:, 1]) < 0.9) & (v[:, 2] > TAB_TOP - 0.2) & (v[:, 2] < TAB_TOP + 8)]
        ax_deg = None
        if len(sel) >= 6:
            a = np.linalg.svd(sel - sel.mean(0), full_matrices=False)[2][0]
            ax_deg = float(np.degrees(np.arccos(min(1.0, abs(a[2])))))
        tabs.append(dict(tab="+x" if sx > 0 else "-x", tab_area_mm2=r(area, 1), contact_mm2=r(contact, 1),
                         gap_max_mm=r(gaps[np.isfinite(gaps)].max()) if np.isfinite(gaps).any() else None,
                         plate_mm=r(np.median(thick)) if thick else None,
                         pilot_d_mm=r(np.median(ds)), pilot_centre_off_mm=r(max(cs), 3),
                         pilot_depth_mm=r(hc[0] - 0.3) if len(hc) else None,
                         pilot_axis_vs_tab_axis_deg=r(ax_deg, 1)))
    out["tabs"] = tabs
    # contact over the whole servo surface, per face group
    w = trimesh.transform_points(pts, M)
    _, dist, _ = trimesh.proximity.ProximityQuery(mesh).on_surface(w)
    near = dist < 0.15
    above = pts[:, 2] > TAB_TOP
    groups = {
        "tab top faces": (nrm[:, 2] > 0.9) & (np.abs(pts[:, 2] - TAB_TOP) < 0.05),
        "body end faces above the tabs (x = +-11.5)": (np.abs(nrm[:, 0]) > 0.9) & above & (np.abs(pts[:, 0]) < BODY_X + 0.1),
        "body side faces above the tabs (y = +-6.5)": (np.abs(nrm[:, 1]) > 0.9) & above,
        "gear top and shaft boss": pts[:, 2] > BODY_TOP + 0.01,
        "body below the tabs": pts[:, 2] < TAB_BOT - 0.01,
    }
    out["contact_mm2"] = {k: dict(contact=r((near & m).sum() * dA, 1), of=r(m.sum() * dA, 1)) for k, m in groups.items()}
    out["contact_total_mm2"] = r(near.sum() * dA, 1)
    if mesh.is_watertight:
        out["servo_depth_in_plastic_max_mm"] = r(trimesh.proximity.ProximityQuery(mesh).signed_distance(w[::20]).max())
    # gaps from the body faces along their normals
    gaps = {}
    for z in (10.0, 21.0, 23.0):
        row = {}
        for lab, d, p in (("+x", [1, 0, 0], [BODY_X - 0.1, 0, z]), ("-x", [-1, 0, 0], [-BODY_X + 0.1, 0, z]),
                          ("+y", [0, 1, 0], [0, BODY_Y - 0.1, z]), ("-y", [0, -1, 0], [0, -BODY_Y + 0.1, z])):
            h = hits(mesh, M, p, d)
            row[lab] = r(h[0] - 0.1) if len(h) else None
        gaps["z=%g" % z] = row
    out["body_gap_mm"] = gaps
    return out


def ear_sweep(head_world, mics, cam_box):
    """Antenna holder and rod of each side over the URDF limits: least distance to the head shell and the mic boards."""
    u = yourdfpy.URDF.load(os.path.join(URDF_DIR, "robot.urdf"), load_meshes=False, build_scene_graph=True)
    pq = trimesh.proximity.ProximityQuery(head_world)
    cache = {}
    res = {}
    for side in SIDES:
        j = side + "_antenna"
        lim = next(x.limit for x in u.robot.joints if x.name == j)
        worst = dict(shell=(np.inf, None), mic=(np.inf, None), camera=(np.inf, None))
        for a in np.radians(np.arange(np.degrees(lim.lower), np.degrees(lim.upper) + 0.1, 5.0)):
            u.update_cfg({j: a})
            Tl = np.array(u.get_transform(side + "_antenna_holder"))
            Tl[:3, 3] *= 1000.0
            P = []
            for v in u.link_map[side + "_antenna_holder"].visuals:
                fn = os.path.basename(v.geometry.mesh.filename)
                if fn not in cache:
                    m = trimesh.load(os.path.join(URDF_DIR, fn), force="mesh")
                    m.apply_scale(1000.0)
                    cache[fn] = m.sample(8000, seed=3)
                O = np.array(v.origin if v.origin is not None else np.eye(4))
                O[:3, 3] *= 1000.0
                P.append(trimesh.transform_points(cache[fn], Tl @ O))
            P = np.vstack(P)
            _, d, _ = pq.on_surface(P)
            if d.min() < worst["shell"][0]:
                worst["shell"] = (float(d.min()), float(np.degrees(a)))
            for mc in mics:
                dm = box_dist(P, *mc).min()
                if dm < worst["mic"][0]:
                    worst["mic"] = (float(dm), float(np.degrees(a)))
            dc = box_dist(P, *cam_box).min()
            if dc < worst["camera"][0]:
                worst["camera"] = (float(dc), float(np.degrees(a)))
        res[side] = dict(travel_deg=[r(np.degrees(lim.lower), 0), r(np.degrees(lim.upper), 0)],
                         **{"min_to_%s_mm" % k: r(v[0]) for k, v in worst.items()},
                         **{"at_%s_deg" % k: r(v[1], 0) for k, v in worst.items()})
    return res


def box_dist(P, c, R, dims):
    q = (P - c) @ R
    e = np.maximum(np.abs(q) - np.asarray(dims) / 2.0, 0)
    return np.linalg.norm(e, axis=1)


def mic_boxes():
    """Mic board envelopes (audit/placements.json mic_l and mic_r, URDF world, axis-aligned boxes)."""
    P = json.load(open(os.path.join(LAB, "audit", "placements.json")))
    return [(np.array(p["center_mm"], float), np.eye(3), np.array(p["dims_xyz_mm"], float)) for p in P if p["id"] in ("mic_l", "mic_r")]


def camera_box():
    """Camera Module 3 box as the viewer draws it (twin/complete3d/camera_seat.json, URDF world, axis-aligned)."""
    J = json.load(open(os.path.join(LAB, "twin", "complete3d", "camera_seat.json")))["viewer_box_today"]
    return np.array(J["center_world"], float), np.eye(3), np.array(J["extents"], float)


# ---------------------------------------------------------------------------------------------- pictures
def section(ax, mesh, M, origin, normal, idx, color, fill=None, lw=0.8):
    Mi = np.linalg.inv(M)
    loc = mesh.copy()
    loc.apply_transform(Mi)
    s = loc.section(plane_origin=origin, plane_normal=normal)
    if s is None:
        return
    for p in s.discrete:
        ax.plot(p[:, idx[0]], p[:, idx[1]], color=color, lw=lw)
    if fill:
        try:
            pl, to3 = s.to_2D()
            for poly in pl.polygons_full:
                xy = np.array(poly.exterior.coords)
                P = trimesh.transform_points(np.column_stack([xy, np.zeros(len(xy))]), to3)
                ax.fill(P[:, idx[0]], P[:, idx[1]], color=fill, lw=0, alpha=0.55)
                for h in poly.interiors:
                    xy = np.array(h.coords)
                    P = trimesh.transform_points(np.column_stack([xy, np.zeros(len(xy))]), to3)
                    ax.fill(P[:, idx[0]], P[:, idx[1]], color="white", lw=0)
        except Exception:
            pass


def screw_mesh(sx):
    """SG90 bag screw as drawn by the viewer (d 2.0, head 4.0 x 1.6, 7.2 mm): head under the tab, shank up."""
    sh = trimesh.creation.cylinder(radius=1.0, height=7.2, sections=24)
    sh.apply_translation([sx * HOLE_X, 0, TAB_BOT + 3.6])
    hd = trimesh.creation.cylinder(radius=2.0, height=1.6, sections=24)
    hd.apply_translation([sx * HOLE_X, 0, TAB_BOT - 0.8])
    return trimesh.util.concatenate([sh, hd])


def pictures(out, head_mesh, poses, s0, res, label):
    for k, side in enumerate(SIDES):
        M = poses[k]
        fig, axs = plt.subplots(1, 2, figsize=(13, 5.6), dpi=110)
        ax = axs[0]
        section(ax, head_mesh, np.eye(4) @ M, [0, 0, 0], [0, 1, 0], (0, 2), "#222222", fill="#c9b79c")
        loc = s0.copy()
        section(ax, loc, np.eye(4), [0, 0, 0], [0, 1, 0], (0, 2), "#d62728", fill="#f4a3a3")
        for sx in (1, -1):
            section(ax, screw_mesh(sx), np.eye(4), [0, 0, 0], [0, 1, 0], (0, 2), "#7f7f7f", fill="#bdbdbd", lw=0.6)
        t = res[k]["tabs"]
        ax.annotate("tab on %.2f mm of plate, contact %.1f + %.1f mm2" % (t[0]["plate_mm"] or 0, t[0]["contact_mm2"], t[1]["contact_mm2"]),
                    (HOLE_X + 2, TAB_TOP), (2, 42), fontsize=7, arrowprops=dict(arrowstyle="-", lw=0.5))
        ax.annotate("pilot D%.2f, %.1f mm to the drill tip, axis %.1f deg and %.3f mm off the tab hole" % (
                    t[1]["pilot_d_mm"], t[1]["pilot_depth_mm"] or 0, t[1]["pilot_axis_vs_tab_axis_deg"] or 0, t[1]["pilot_centre_off_mm"]),
                    (-HOLE_X, TAB_TOP + 3), (-44, 47), fontsize=7, arrowprops=dict(arrowstyle="-", lw=0.5))
        ax.annotate("screw (SG90 bag, size not published)", (-HOLE_X, TAB_BOT - 1), (-40, -6), fontsize=7,
                    arrowprops=dict(arrowstyle="-", lw=0.5))
        ax.annotate("output shaft, out of the head", (SHAFT[0], 31), (8, 52), fontsize=7, arrowprops=dict(arrowstyle="-", lw=0.5))
        ax.set_xlim(-45, 45); ax.set_ylim(-8, 56); ax.set_aspect("equal"); ax.grid(alpha=0.2)
        ax.set_xlabel("servo x, mm (along the tabs)"); ax.set_ylabel("servo z, mm (output shaft axis)")
        ax.set_title("%s ear, cut through both tab holes (servo y = 0)" % side, fontsize=9)
        ax = axs[1]
        section(ax, head_mesh, M, [0, 0, 21.0], [0, 0, 1], (0, 1), "#222222", fill="#c9b79c")
        section(ax, s0, np.eye(4), [0, 0, 21.0], [0, 0, 1], (0, 1), "#d62728", fill="#f4a3a3")
        g = res[k]["body_gap_mm"]["z=21"]
        ce = res[k]["contact_mm2"]["body end faces above the tabs (x = +-11.5)"]["contact"]
        wy = 1 if g["+y"] is not None else -1          # the side with the wall; the other side is open
        ax.annotate("body ends on the pocket ends: gap %s / %s mm, %.1f mm2 contact (what stops it turning)" % (g["+x"], g["-x"], ce),
                    (BODY_X, -wy * 2), (-42, -wy * 28), fontsize=7, arrowprops=dict(arrowstyle="-", lw=0.5))
        ax.annotate("%sy side: %s mm to the wall; %sy side open" % ("+" if wy > 0 else "-", g["%sy" % ("+" if wy > 0 else "-")],
                                                                  "-" if wy > 0 else "+"),
                    (0, wy * BODY_Y), (-14, wy * 27), fontsize=7, arrowprops=dict(arrowstyle="-", lw=0.5))
        for sx in (1, -1):
            ax.add_patch(plt.Circle((sx * HOLE_X, 0), 0.75, fill=False, color="#1f77b4", lw=0.8))
        ax.annotate("pilots (blue)", (HOLE_X, 0.8), (18, 12), fontsize=7, arrowprops=dict(arrowstyle="-", lw=0.5))
        ax.set_xlim(-45, 45); ax.set_ylim(-32, 32); ax.set_aspect("equal"); ax.grid(alpha=0.2)
        ax.set_xlabel("servo x, mm"); ax.set_ylabel("servo y, mm")
        ax.set_title("%s ear, cut across the plate at servo z = 21 (2 mm above the tabs)" % side, fontsize=9)
        fig.suptitle("%s, %s: shell (tan), SG90 (red), tab screws as drawn (grey). CAD check only." % (label, side), fontsize=9)
        fig.tight_layout()
        fig.savefig(os.path.join(out, "ear_%s_section.png" % side))
        plt.close(fig)
        # 3D close-up from inside the head: the shell is cut to a box around the servo (cut faces capped)
        Mi = np.linalg.inv(M)
        hl = head_mesh.copy()
        hl.apply_transform(Mi)
        for o, nn in (([-30, 0, 0], [1, 0, 0]), ([30, 0, 0], [-1, 0, 0]), ([0, -22, 0], [0, 1, 0]), ([0, 24, 0], [0, -1, 0]),
                      ([0, 0, 12], [0, 0, 1]), ([0, 0, 34], [0, 0, -1])):
            hl = hl.slice_plane(o, nn, cap=True)
        parts = [(hl, np.array([0.86, 0.78, 0.64])), (s0, np.array([0.86, 0.22, 0.22]))]
        for sx in (1, -1):
            parts.append((screw_mesh(sx), np.array([0.62, 0.64, 0.68])))
        subs = []
        for m, colr in parts:
            v, f = trimesh.remesh.subdivide_to_size(m.vertices, m.faces, max_edge=2.5)
            t = v[f]
            subs.append((t, np.tile(colr, (len(t), 1))))
        tri = np.vstack([p[0] for p in subs])
        base = np.vstack([p[1] for p in subs])
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
        for elev, azim, tag in ((-28, -62, "from_below"), (-12, 22, "from_the_side")):
            fig = plt.figure(figsize=(7.5, 6.5), dpi=110)
            ax = fig.add_subplot(111, projection="3d")
            el, az = np.radians(elev), np.radians(azim)
            view = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])
            nf = n * np.sign(n @ view)[:, None]
            light = view + np.array([0.0, 0.0, -0.6]) + np.array([0.4, -0.3, 0.0])
            light /= np.linalg.norm(light)
            shade = 0.38 + 0.62 * np.clip(nf @ light, 0, 1)
            col = np.clip(base * shade[:, None], 0, 1)
            ax.add_collection3d(Poly3DCollection(tri, facecolors=col, edgecolors="none"))
            ax.set_xlim(-30, 30); ax.set_ylim(-26, 26); ax.set_zlim(-2, 38)
            ax.set_box_aspect((60, 52, 40))
            ax.view_init(elev=elev, azim=azim)
            ax.set_xlabel("servo x, mm"); ax.set_ylabel("servo y, mm"); ax.set_zlabel("servo z (shaft), mm")
            ax.set_title("%s ear seen from inside the head (%s); the shell is cut to a box around the servo.\n"
                         "%s in the viewer pose: shell tan, SG90 red, the 2 tab screws grey (drawn as the viewer draws them).\n"
                         "CAD check only." % (side, tag.replace("_", " "), label), fontsize=8)
            fig.tight_layout()
            fig.savefig(os.path.join(out, "ear_%s_3d_%s.png" % (side, tag)))
            plt.close(fig)


TAB_SCREWS = ("F348", "F349", "F350", "F351")
OLD_NOTE = "SG90 bag screw (BOM 14), size not published; head pilot axis is 20.7 deg off the SG90 tab axis in the CAD"


def write_fasteners(ang_m, ang_fit=20.7):
    """Measured pilot axis and the corrected note into the 4 SG90 tab screw rows (same text as make_fasteners.py)."""
    note = ("SG90 bag screw (BOM 14), size not published; the head pilot is coaxial with the SG90 tab hole "
            "(measured on the mesh: axis %.1f deg off; the feat3d fit reads it along the head y axis, %.1f deg off)" % (ang_m, ang_fit))
    fj = os.path.join(LAB, "fasteners", "fasteners.json")
    F = json.load(open(fj))
    n = 0
    for rec in F["fasteners"]:
        if rec["id"] in TAB_SCREWS and rec.get("source") == "sg90_tab":
            rec["pilot_axis_measured_deg"] = round(float(ang_m), 1)
            rec["notes"] = [note if x == OLD_NOTE or x.startswith("SG90 bag screw (BOM 14), size not published; the head pilot is coaxial")
                            else x for x in rec["notes"]]
            n += 1
    json.dump(F, open(fj, "w"))
    fc = os.path.join(LAB, "fasteners", "fasteners.csv")
    txt = open(fc, newline="").read()
    lines = txt.split("\n")
    for k, ln in enumerate(lines):
        if ln.split(",", 1)[0] in TAB_SCREWS:
            lines[k] = ln.replace('"%s"' % OLD_NOTE, '"%s"' % note)
    open(fc, "w", newline="").write("\n".join(lines))
    return n, note


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True, help="picture folder, outside the repo")
    ap.add_argument("--glb", default=None, help="viewer duck.glb or duck.glb.txt (to check the viewer pose and mesh)")
    ap.add_argument("--write-fasteners", action="store_true", help="write the measured pilot axis into fasteners.json and .csv")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    Th, poses = load_pose()
    s0 = sg90()
    pts, fi = trimesh.sample.sample_surface(s0, 120000, seed=1)
    nrm, dA = s0.face_normals[fi], s0.area / 120000
    meshes = {k: trimesh.load(p, force="mesh") for k, p in HEADS.items()}
    J = dict(script="altaay_lab/twin/companion/ear_mount.py", method=__doc__.split("Checks per ear")[1].strip(),
             frame="head.stl frame (print/ frame); servo frame: sg90.stl x1000 (x along the tabs, z the output shaft)",
             pose="audit/assembly.json sg90 instances", heads={})
    if a.glb:
        vm, vposes = load_glb(a.glb)
        J["viewer_pose_vs_assembly_max_mm"] = r(max(np.abs(vp - p).max() for vp, p in zip(vposes, poses)), 4)
        meshes["viewer GLB head (decimated)"] = vm
        poses_draw = vposes
    else:
        poses_draw = poses
    for k, m in meshes.items():
        J["heads"][k] = dict(faces=int(len(m.faces)), watertight=bool(m.is_watertight),
                             ears={side: check_ear(m, poses_draw[n], s0, pts, nrm, dA) for n, side in enumerate(SIDES)})
        print(k, json.dumps(J["heads"][k]["ears"]["left"]["tabs"]))
    hw = meshes["print/head.stl"].copy()
    hw.apply_transform(Th)
    try:
        J["ear_travel"] = ear_sweep(hw, mic_boxes(), camera_box())
    except (KeyError, StopIteration, FileNotFoundError) as e:
        J["ear_travel"] = "BLOCKER: %s" % e
    print("ear travel", J["ear_travel"])
    pictures(a.out, meshes["print/head.stl"], poses_draw, s0,
             [J["heads"]["print/head.stl"]["ears"][s] for s in SIDES], "print/head.stl")
    if a.write_fasteners:
        ang = max(t["pilot_axis_vs_tab_axis_deg"] for s in SIDES for t in J["heads"]["print/head.stl"]["ears"][s]["tabs"])
        n, note = write_fasteners(ang)
        print("fasteners.json: %d SG90 tab screw rows updated: %s" % (n, note))
    with open(os.path.join(HERE, "ear_mount.json"), "w") as fh:
        json.dump(J, fh, indent=1)
        fh.write("\n")


if __name__ == "__main__":
    main()
