#!/usr/bin/env python3
"""render_freeze.py: section and 3D close-up pictures of the freeze changes. CAD check only.

Run: python3 altaay_lab/twin/freeze/render_freeze.py --out <folder outside the repo>
Pictures: mic seats (print/head.stl), the speaker duct and the closed grille ring, the cliff ToF seat in body_front,
the touch pads and boards. Sections are mesh cuts in the URDF world (zero pose); the 3D views cut the meshes to a box
round the item (cut faces capped) and shade them by facet.
"""
import argparse
import json
import os

import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from flib import HERE, scene, head_inst, inst_by_key, speaker_frame, placements, placement_box, box_mesh

COL = {"shell": (0.86, 0.78, 0.64), "new": (0.20, 0.55, 0.85), "board": (0.15, 0.55, 0.25), "pad": (0.85, 0.45, 0.15),
       "part": (0.70, 0.70, 0.72), "cone": (0.95, 0.25, 0.25)}


def cut(m, o, n):
    s = m.section(plane_origin=o, plane_normal=n)
    return [] if s is None else [np.asarray(e) for e in s.discrete]


def section(ax, items, o, n, idx, lim, title):
    for m, c, lw in items:
        for e in cut(m, o, n):
            ax.plot(e[:, idx[0]], e[:, idx[1]], color=c, lw=lw)
    ax.set_xlim(*lim[0]); ax.set_ylim(*lim[1]); ax.set_aspect("equal"); ax.grid(alpha=0.25)
    ax.set_xlabel("xyz"[idx[0]] + " (URDF world, mm)"); ax.set_ylabel("xyz"[idx[1]] + " (mm)")
    ax.set_title(title, fontsize=8)


def boxcut(m, lo, hi):
    m = m.copy()
    for k in range(3):
        for sgn, v in ((1, lo[k]), (-1, hi[k])):
            n = np.zeros(3); n[k] = sgn
            o = np.zeros(3); o[k] = v
            m = m.slice_plane(o, n, cap=True)
            if m is None or not len(m.faces):
                return None
    return m


def view3d(path, parts, lo, hi, views, title):
    tris, cols = [], []
    for m, c in parts:
        mm = boxcut(m, lo, hi)
        if mm is None:
            continue
        v, f = trimesh.remesh.subdivide_to_size(mm.vertices, mm.faces, max_edge=3.0)
        t = v[f]
        tris.append(t); cols.append(np.tile(c, (len(t), 1)))
    T = np.vstack(tris); C = np.vstack(cols)
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    for elev, azim, tag in views:
        fig = plt.figure(figsize=(8, 6.5), dpi=110)
        ax = fig.add_subplot(111, projection="3d")
        el, az = np.radians(elev), np.radians(azim)
        vw = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])
        nf = n * np.sign(n @ vw)[:, None]
        li = vw + np.array([0.3, -0.3, 0.5]); li /= np.linalg.norm(li)
        sh = 0.35 + 0.65 * np.clip(nf @ li, 0, 1)
        ax.add_collection3d(Poly3DCollection(T, facecolors=np.clip(C * sh[:, None], 0, 1), edgecolors="none"))
        ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1]); ax.set_zlim(lo[2], hi[2])
        ax.set_box_aspect(tuple(np.array(hi) - np.array(lo)))
        ax.view_init(elev=elev, azim=azim)
        ax.set_xlabel("x mm"); ax.set_ylabel("y mm"); ax.set_zlabel("z mm")
        ax.set_title(title + " (%s). CAD check only." % tag, fontsize=8)
        fig.tight_layout()
        fig.savefig(path.replace(".png", "_%s.png" % tag))
        plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    S = scene()
    H = S.world_mesh(head_inst(S))
    SI = S.world_mesh(inst_by_key(S, "speaker_interface")[0])
    ST = S.world_mesh(inst_by_key(S, "speaker_stand")[0])
    BF = S.world_mesh(inst_by_key(S, "body_front")[0])
    PL = placements()
    box = {k: placement_box(PL[k]) for k in PL}
    sg = [S.world_mesh(i) for i in S.inst if i.get("urdf") == "sg90.stl"]
    out = []
    # 1. mic seats
    ms = json.load(open(os.path.join(os.path.dirname(HERE), "companion", "mic_seats.json")))["seats"]
    pl_, pr_ = np.array(ms["left"]["mic_port_world"]), np.array(ms["right"]["mic_port_world"])
    fig, axs = plt.subplots(1, 2, figsize=(14, 6), dpi=110)
    section(axs[0], [(H, "#8d6e63", 0.8), (box["mic_l"], "g", 0.8), (box["mic_r"], "g", 0.8)] + [(m, "r", 0.6) for m in sg],
            pl_, (1, 0, 0), (1, 2), ((-100, 100), (170, 240)),
            "print/head.stl cut at x = %.1f mm through both mic ports: shell (brown), mic boards (green), ear SG90s (red)" % pl_[0])
    section(axs[1], [(H, "#8d6e63", 0.8), (box["mic_l"], "g", 0.8)] + [(m, "r", 0.6) for m in sg], pl_, (0, 0, 1), (0, 1),
            ((-70, -5), (35, 75)), "left seat, cut at z = %.1f (port height): bosses, port tube and the 1.2 mm port" % pl_[2])
    fig.tight_layout(); p = os.path.join(a.out, "mic_seats_section.png"); fig.savefig(p); plt.close(fig); out.append(p)
    view3d(os.path.join(a.out, "mic_seat_left_3d.png"), [(H, COL["shell"]), (box["mic_l"], COL["board"])] + [(m, (0.8, 0.2, 0.2)) for m in sg],
           pl_ - [25, 18, 20], pl_ + [25, 6, 14], [(10, -80, "from_inside"), (35, -130, "from_inside_behind")],
           "Left mic seat in print/head.stl: shell tan, board green, ear SG90 red")
    out += [os.path.join(a.out, "mic_seat_left_3d_from_inside.png"), os.path.join(a.out, "mic_seat_left_3d_from_inside_behind.png")]
    # 2. speaker duct
    c, ax_, u, v, _ = speaker_frame()
    fig, axs = plt.subplots(1, 2, figsize=(14, 6), dpi=110)
    nrm = np.cross(ax_, [0, 0, 1.0]); nrm /= np.linalg.norm(nrm)
    section(axs[0], [(H, "#8d6e63", 0.8), (SI, "#1f77b4", 1.0), (ST, "#777777", 0.6), (box["mic_r"], "g", 0.8)],
            c, (0, 0, 1), (0, 1), ((-50, 70), (-100, -20)),
            "z = %.1f mm through the speaker axis: head (brown), interface with the duct (blue), stand (grey), right mic (green)" % c[2])
    section(axs[1], [(H, "#8d6e63", 0.8), (SI, "#1f77b4", 1.0), (ST, "#777777", 0.6)], c, nrm, (0, 2),
            ((-5, 50), (175, 230)), "cut along the speaker axis, plane through the axis and z: duct to 1.0 mm off the wall")
    fig.tight_layout(); p = os.path.join(a.out, "speaker_duct_section.png"); fig.savefig(p); plt.close(fig); out.append(p)
    view3d(os.path.join(a.out, "speaker_duct_3d.png"), [(H, COL["shell"]), (SI, COL["new"]), (ST, COL["part"])],
           c + np.array([-30, -22, -28]), c + np.array([30, 6, 28]), [(15, 120, "from_inside"), (5, -70, "grille_outside")],
           "Speaker duct (blue, one piece with speaker_interface) to the grille; 36 outer holes closed")
    out += [os.path.join(a.out, "speaker_duct_3d_from_inside.png"), os.path.join(a.out, "speaker_duct_3d_grille_outside.png")]
    # 3. cliff ToF seat
    CS = json.load(open(os.path.join(HERE, "cliff_seat.json")))
    import cliff_seat as CSm
    O = np.array(CS["board"]["origin_pcb_top_centre"])
    brd = CSm.board_box(-1.6, 3.0)
    cone = CSm.cone(CSm.APEX_N, 60.0)
    others = [S.world_mesh(i) for i in S.inst if i["key"] in ("body_middle_bottom", "trunk_bottom")]
    fig, axs = plt.subplots(1, 2, figsize=(14, 6), dpi=110)
    section(axs[0], [(BF, "#8d6e63", 0.9), (brd, "g", 0.9), (cone, "r", 0.6), (box["dock_dk2"], "m", 0.7)] + [(m, "#777777", 0.5) for m in others],
            O, (0, 1, 0), (0, 2), ((0, 70), (-45, 50)),
            "y = 0 through the cliff ToF: body_front (brown), board (green), field of view (red), DK2 (magenta), belly (grey)")
    section(axs[1], [(BF, "#8d6e63", 0.9), (brd, "g", 0.9), (cone, "r", 0.6)], O + [7, 0, 0], (1, 0, 0), (1, 2),
            ((-40, 40), (-45, 50)), "x = %.1f: the standoffs and the window; the dock pad starts at z 0, the lead hole at z 38" % (O[0] + 7))
    fig.tight_layout(); p = os.path.join(a.out, "cliff_seat_section.png"); fig.savefig(p); plt.close(fig); out.append(p)
    view3d(os.path.join(a.out, "cliff_seat_3d.png"), [(BF, COL["shell"]), (brd, COL["board"])],
           O + np.array([-18, -22, -32]), O + np.array([12, 22, 16]), [(20, 200, "from_inside"), (-15, 20, "window_outside")],
           "Cliff ToF seat in body_front: board green on 4 standoffs, window on the field of view")
    out += [os.path.join(a.out, "cliff_seat_3d_from_inside.png"), os.path.join(a.out, "cliff_seat_3d_window_outside.png")]
    # 4. touch pads
    TP = json.load(open(os.path.join(HERE, "touch_pads.json")))
    BMT = S.world_mesh(inst_by_key(S, "body_middle_top")[0])
    pads = {}
    for pid, p_ in TP["pads"].items():
        cc = np.array(p_["centre_world"]); sz = p_["pad_mm"]
        pads[pid] = box_mesh(cc - [0, 0, 0.6], np.eye(3), [sz[0], sz[1], 1.0])
        g = p_["footprint_with_guard_mm"]
        ring = box_mesh(cc - [0, 0, 0.6], np.eye(3), [g[0], g[1], 0.8])
        pads[pid + "g"] = ring
    fig, axs = plt.subplots(1, 2, figsize=(14, 6), dpi=110)
    section(axs[0], [(H, "#8d6e63", 0.8), (pads["PH1"], "#ff7f0e", 1.2), (pads["PH2"], "#ff7f0e", 1.2), (box["tch_h"], "g", 0.9),
                     (pads["PH1g"], "#bbbbbb", 0.5), (pads["PH2g"], "#bbbbbb", 0.5)],
            (0, 0, 0), (0, 1, 0), (0, 2), ((-100, 105), (170, 240)),
            "head at y = 0: pads PH1 (top) and PH2 (back) in orange with their guard ring (grey); head touch board in green (at y 35)")
    section(axs[1], [(BMT, "#8d6e63", 0.8), (pads["PB1"], "#ff7f0e", 1.2), (pads["PB1g"], "#bbbbbb", 0.5), (box["tch_b"], "g", 0.9)],
            (-95, 0, 0), (1, 0, 0), (1, 2), ((-60, 60), (45, 115)),
            "body_middle_top at x = -95: pad PB1 (orange) on the inner roof, body touch board (green) on the left wall at x -88")
    fig.tight_layout(); p = os.path.join(a.out, "touch_pads_section.png"); fig.savefig(p); plt.close(fig); out.append(p)
    view3d(os.path.join(a.out, "touch_head_3d.png"), [(H, COL["shell"]), (pads["PH1"], COL["pad"]), (pads["PH2"], COL["pad"]), (box["tch_h"], COL["board"])],
           np.array([-95, -50, 200]), np.array([40, 60, 236]), [(-35, -60, "from_below")],
           "Head pads PH1, PH2 (orange) and the head touch board (green) on the inner roof, seen from below")
    view3d(os.path.join(a.out, "touch_body_3d.png"), [(BMT, COL["shell"]), (pads["PB1"], COL["pad"]), (box["tch_b"], COL["board"])],
           np.array([-118, -10, 55]), np.array([-60, 56, 110]), [(-25, -120, "from_below")],
           "Back pad PB1 (orange) and the body touch board (green), inside body_middle_top")
    out += [os.path.join(a.out, "touch_head_3d_from_below.png"), os.path.join(a.out, "touch_body_3d_from_below.png")]
    print("\n".join(out))


if __name__ == "__main__":
    main()
