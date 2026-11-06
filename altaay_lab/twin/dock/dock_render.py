#!/usr/bin/env python3
"""Section and 3D close-ups of the dock (CAD check only): the paddle and pins, the seat and its springs and switch, the
electronics bay, the cable routes, the whole dock and the docked duck. Pictures go to --out (outside the repo).

Run: python3 altaay_lab/twin/dock/dock_render.py --out <folder>
3D views shade each facet by its normal (matplotlib); sections are mesh cuts in the dock frame.
"""
import argparse, json, os, sys
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dock_assembly as DA  # noqa: E402
import dock_parts as DP  # noqa: E402

COL = {"printed": (0.86, 0.80, 0.68), "bought": (0.35, 0.45, 0.60), "board_part": (0.15, 0.15, 0.15), "paper": (0.95, 0.95, 0.95),
       "pin": (0.95, 0.75, 0.15), "evm": (0.10, 0.45, 0.20), "perf": (0.70, 0.55, 0.20), "swg": (0.15, 0.35, 0.15), "steel": (0.55, 0.57, 0.60),
       "screw": (0.30, 0.30, 0.32), "insert": (0.80, 0.65, 0.20), "nut": (0.45, 0.45, 0.48), "duck": (0.80, 0.82, 0.86)}
WIRE = {"red": (0.85, 0.1, 0.1), "black": (0.1, 0.1, 0.1), "white": (0.6, 0.6, 0.9), "yellow": (0.9, 0.8, 0.1), "green": (0.1, 0.6, 0.2), "blue": (0.1, 0.3, 0.9)}


def color_of(c):
    i = c["id"]
    if i.startswith("pin_"): return COL["pin"]
    if i in ("evm",): return COL["evm"]
    if i == "perf": return COL["perf"]
    if i == "swg": return COL["swg"]
    if i.startswith(("rod_", "ballast_", "cf_", "seat_spring")): return COL["steel"]
    return COL.get(c["kind"], (0.6, 0.6, 0.6))


def fasteners():
    p = os.path.join(HERE, "dock_fasteners.json")
    if not os.path.exists(p):
        return []
    out = []
    for f in json.load(open(p))["fasteners"]:
        T = np.array(f["pose_dock"])
        if f["kind"] == "screw":
            m = trimesh.creation.cylinder(radius=f["d"] / 2, height=f["draw_length_mm"], sections=12); m.apply_translation((0, 0, f["draw_length_mm"] / 2))
            h = trimesh.creation.cylinder(radius=f["head"]["dk"] / 2, height=f["head"]["k"], sections=14); h.apply_translation((0, 0, -f["head"]["k"] / 2))
            m = trimesh.util.concatenate([m, h]); c = COL["screw"]
        elif f["kind"] == "insert":
            m = trimesh.creation.cylinder(radius=2.3, height=5.7, sections=12); m.apply_translation((0, 0, 2.85)); c = COL["insert"]
        else:
            m = trimesh.creation.cylinder(radius=f.get("s", 5.5) / 2 / np.cos(np.pi / 6), height=f["h"], sections=6); m.apply_translation((0, 0, f["h"] / 2)); c = COL["nut"]
        m.apply_transform(T)
        out.append((m, c, f))
    return out


def wires():
    p = os.path.join(HERE, "dock_cables3d.json")
    if not os.path.exists(p):
        return []
    J = json.load(open(p))
    return [(np.array(r["points"]), WIRE.get(r.get("color", "black"), (0.2, 0.2, 0.2)), r.get("od_mm", 1.8)) for c in J["cables"] for r in c["runs"] if r.get("points")]


def boxcut(m, lo, hi):
    try:
        b = trimesh.creation.box(extents=np.subtract(hi, lo)); b.apply_translation(np.add(lo, hi) / 2)
        r = m.intersection(b)
        return r if len(r.faces) else None
    except Exception:
        return m.slice_plane(lo, (1, 0, 0)) if False else None


def draw3d(ax, items, lo, hi, elev=22, azim=-60, wire=None, light=(0.4, -0.5, 0.8), alpha=1.0):
    L = np.array(light) / np.linalg.norm(light)
    tris, cols = [], []
    for m, c in items:
        mm = boxcut(m, lo, hi) if lo is not None else m
        if mm is None or len(mm.faces) == 0:
            continue
        sh = 0.45 + 0.55 * np.clip(np.abs(mm.face_normals @ L), 0, 1)
        tris.append(mm.vertices[mm.faces]); cols.append(np.clip(np.array(c)[None, :] * sh[:, None], 0, 1))
    if tris:
        pc = Poly3DCollection(np.concatenate(tris), facecolors=np.concatenate(cols), edgecolors="none", linewidths=0, alpha=alpha)
        ax.add_collection3d(pc)
    for P, c, od in (wire or []):
        if lo is not None:
            keep = np.all((P >= np.array(lo) - 1) & (P <= np.array(hi) + 1), axis=1)
            if not keep.any():
                continue
        ax.plot(P[:, 0], P[:, 1], P[:, 2], color=c, lw=max(0.8, od * 0.9), solid_capstyle="round")
    if lo is not None:
        ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1]); ax.set_zlim(lo[2], hi[2])
        ax.set_box_aspect(np.subtract(hi, lo))
    ax.view_init(elev=elev, azim=azim)
    ax.set_xlabel("x (mm)"); ax.set_ylabel("y (mm)"); ax.set_zlabel("z (mm)")
    ax.tick_params(labelsize=6)


def section(ax, items, o, n, idx, lim, title, fast=None):
    for m, c in items:
        s = m.section(plane_origin=o, plane_normal=n)
        if s is None:
            continue
        for e in s.discrete:
            e = np.asarray(e)
            ax.fill(e[:, idx[0]], e[:, idx[1]], color=c, alpha=0.55, lw=0)
            ax.plot(e[:, idx[0]], e[:, idx[1]], color=np.array(c) * 0.5, lw=0.7)
    ax.set_xlim(*lim[0]); ax.set_ylim(*lim[1]); ax.set_aspect("equal"); ax.grid(alpha=0.25)
    ax.set_xlabel("xyz"[idx[0]] + " (dock frame, mm)"); ax.set_ylabel("xyz"[idx[1]] + " (mm)"); ax.set_title(title, fontsize=8)


def duck_meshes(glb):
    """the duck in the docked pose, from the viewer's duck.glb (make_viewer_data.py) and its manifest: each node moved by
    T_dock(link) x T_zero(link)^-1, as the Docked scene of the viewer"""
    if not glb or not os.path.exists(glb):
        return []
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "viewer"))
    import dock_scene, yourdfpy
    g, n = dock_scene.read_glb(glb)
    man = json.load(open(os.path.join(os.path.dirname(glb), "manifest.json")))
    REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
    u = yourdfpy.URDF.load(os.path.join(REPO, "mini_bdx/robots/open_duck_mini_v2/robot.urdf"), load_meshes=False, build_scene_graph=True)
    u.update_cfg(np.zeros(len(u.actuated_joint_names)))
    TD = DA.docked_duck_links(); out = []
    for nd in n:
        rec = man["nodes"].get(nd["name"], {})
        if rec.get("category") in ("cable", "tie", "screw", "insert", "connector") or rec.get("link") not in TD:
            continue
        A = u.get_transform(rec["link"]).copy(); A[:3, 3] *= 1000
        m = trimesh.Trimesh(g[nd["mesh"]]["pos"], g[nd["mesh"]]["idx"].reshape(-1, 3), process=False)
        m.apply_transform(TD[rec["link"]] @ np.linalg.inv(A) @ nd["matrix"])
        out.append(m)
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("--duck-glb", default=None, help="the viewer's duck.glb (make_viewer_data.py --out ...) for the docked picture")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    made = []
    for state in ("dock", "docked"):
        C = DA.components(state)
        items = [(c["mesh"], color_of(c)) for c in C if c["id"] != "adapter" and not c["id"].startswith("adapter_cord")]
        F = fasteners() if state == "dock" else []
        fi = [(m, c) for m, c, f in F]
        W = wires() if state == "dock" else []
        if state == "dock":
            # 1. whole dock
            fig = plt.figure(figsize=(11, 9)); ax = fig.add_subplot(111, projection="3d")
            draw3d(ax, items + fi, None, None, elev=20, azim=-130, wire=W)
            ax.set_xlim(-120, 200); ax.set_ylim(-160, 160); ax.set_zlim(0, 470); ax.set_box_aspect((320, 320, 470))
            ax.set_title("Dock, every part (CAD check only): printed parts, bought parts, screws, wires", fontsize=9)
            fig.tight_layout(); f = os.path.join(a.out, "dock_whole.png"); fig.savefig(f, dpi=110); plt.close(fig); made.append(f)
            # 2. paddle and pins: section at y 0 and y 3, and 3D
            fig = plt.figure(figsize=(15, 6.5))
            ax = fig.add_subplot(131)
            section(ax, items + fi, (0, 0.0, 0), (0, 1, 0), (0, 2), ((-8, 160), (125, 245)), "Section y 0: paddle, pins CHG+ and SENSE, carrier, rod plane, spring channel")
            ax = fig.add_subplot(132)
            section(ax, items + fi, (0, 3.0, 0), (0, 1, 0), (0, 2), ((-4, 16), (148, 222)), "Section y +3: pins SYS_L, GND_L (tip %.2f mm proud, 0933 press-fit, solder cup)" % DP.PIN_PROUD)
            ax = fig.add_subplot(133, projection="3d")
            draw3d(ax, items + fi, (-5, -60, 128), (40, 60, 240), elev=15, azim=-35, wire=W)
            ax.set_title("Paddle, pins, carrier, pivot screws (3D)", fontsize=8)
            fig.tight_layout(); f = os.path.join(a.out, "dock_paddle_pins.png"); fig.savefig(f, dpi=110); plt.close(fig); made.append(f)
            # 3. spring channel
            fig = plt.figure(figsize=(15, 6))
            ax = fig.add_subplot(121)
            section(ax, items + fi, (0, 40.0, 0), (0, 1, 0), (0, 2), ((60, 160), (150, 210)), "Section y +40: rod, carriage, CF37CS coil on its drum, strip screw, channel bolts")
            ax = fig.add_subplot(122, projection="3d")
            draw3d(ax, items + fi, (70, 25, 150), (160, 55, 210), elev=35, azim=-60, wire=W)
            ax.set_title("Constant-force spring in its open-top channel (3D)", fontsize=8)
            fig.tight_layout(); f = os.path.join(a.out, "dock_spring_channel.png"); fig.savefig(f, dpi=110); plt.close(fig); made.append(f)
            # 4. seat, springs, switch
            fig = plt.figure(figsize=(15, 6.5))
            ax = fig.add_subplot(131)
            section(ax, items + fi, (0, 0.0, 0), (0, 1, 0), (0, 2), ((-115, 35), (0, 125)), "Section y 0: seat base, sprung top (no duck, +6 mm), springs, spine, inserts")
            ax = fig.add_subplot(132)
            section(ax, items + fi, (-63.3, 0, 0), (1, 0, 0), (1, 2), ((-22, 22), (60, 125)), "Section x -63.3: switch, slotted tower, finger over the lever")
            ax = fig.add_subplot(133, projection="3d")
            cut = [(m, c) for m, c in items + fi]
            draw3d(ax, cut, (-110, 0, 0), (-15, 22, 120), elev=20, azim=-110, wire=W)
            ax.set_title("Seat (half cut at y 0): posts, CC-28CS springs, D2F-01L on its tower", fontsize=8)
            fig.tight_layout(); f = os.path.join(a.out, "dock_seat_springs.png"); fig.savefig(f, dpi=110); plt.close(fig); made.append(f)
            # 5. electronics bay (lid off)
            fig = plt.figure(figsize=(14, 7))
            ax = fig.add_subplot(121, projection="3d")
            bay = [(m, c) for (m, c), cc in zip(items, [c for c in C if c["id"] != "adapter" and not c["id"].startswith("adapter_cord")]) if cc["id"] != "dock_bay_lid"]
            draw3d(ax, bay + fi, (100, -102, 0), (200, 102, 52), elev=55, azim=-120, wire=W)
            ax.set_title("Electronics bay, lid off: charger board, gate board, 2815, fuse holder, DC jack, wires", fontsize=8)
            ax = fig.add_subplot(122)
            section(ax, items + fi, (0, 0, 22.0), (0, 0, 1), (0, 1), ((100, 195), (-105, 105)), "Section z 22: bay boards, standoffs, rims, jack")
            for P, c, od in W:
                ax.plot(P[:, 0], P[:, 1], color=c, lw=0.8)
            fig.tight_layout(); f = os.path.join(a.out, "dock_bay.png"); fig.savefig(f, dpi=110); plt.close(fig); made.append(f)
            # 6. cable routes
            fig = plt.figure(figsize=(15, 7))
            ghost = [(m, (0.92, 0.92, 0.92)) for m, c in items]
            ax = fig.add_subplot(121, projection="3d")
            draw3d(ax, ghost, None, None, elev=18, azim=-135, wire=W, alpha=0.12)
            ax.set_xlim(-120, 200); ax.set_ylim(-160, 160); ax.set_zlim(0, 260); ax.set_box_aspect((320, 320, 260))
            ax.set_title("Every dock wire routed in 3D (parts pale)", fontsize=8)
            ax = fig.add_subplot(122)
            for P, c, od in W:
                ax.plot(P[:, 0], P[:, 2], color=c, lw=1.0)
            section(ax, [(m, (0.85, 0.85, 0.85)) for m, c in items], (0, 20.0, 0), (0, 1, 0), (0, 2), ((-115, 200), (0, 260)), "Wires seen from the side over a section at y 20")
            fig.tight_layout(); f = os.path.join(a.out, "dock_cables.png"); fig.savefig(f, dpi=110); plt.close(fig); made.append(f)
        else:
            duck = duck_meshes(a.duck_glb)
            fig = plt.figure(figsize=(14, 7))
            ax = fig.add_subplot(121, projection="3d")
            draw3d(ax, items + [(m, COL["duck"]) for m in duck], None, None, elev=12, azim=-120)
            ax.set_xlim(-200, 200); ax.set_ylim(-200, 200); ax.set_zlim(0, 470); ax.set_box_aspect((400, 400, 470))
            ax.set_title("Docked (sim pose, hard seed 0): the paddle pushed %.1f mm, yaw %.1f deg; seat top at 112 mm" % (DA.PUSH_DOCKED, np.degrees(DA.YAW_DOCKED)), fontsize=8)
            ax = fig.add_subplot(122)
            section(ax, items + [(m, COL["duck"]) for m in duck], (0, 0.0, 0), (0, 1, 0), (0, 2), ((-150, 120), (90, 260)), "Section y 0, docked: chest pad on the pins, belly on the seat")
            fig.tight_layout(); f = os.path.join(a.out, "dock_docked.png"); fig.savefig(f, dpi=110); plt.close(fig); made.append(f)
    print("\n".join(made))


if __name__ == "__main__":
    main()
