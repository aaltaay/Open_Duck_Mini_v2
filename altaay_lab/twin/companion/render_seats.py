"""render_seats.py: section and close-up pictures of the mic seats in the edited head (CAD check only).

Run: python3 altaay_lab/twin/companion/render_seats.py
Writes altaay_lab/twin/companion/mic_section.png (the head cut on the plane through both mic ports, x = const in the
URDF world) and mic_seat_left.png, mic_seat_right.png (close-ups: a cut through the port axis, along x and along z).
The edited head.stl (stl/head.stl, print/ frame) is put in the URDF world with the head instance transform.
"""
import json
import os
import sys

import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(LAB, "twin", "complete3d"))
from common import scene, head_instances, inst_name, inst_world   # noqa: E402


def cut(mesh, origin, normal):
    s = mesh.section(plane_origin=origin, plane_normal=normal)
    return [] if s is None else [np.asarray(e) for e in s.discrete]


def draw(ax, polys, idx, color, lw=0.8):
    for p in polys:
        ax.plot(p[:, idx[0]], p[:, idx[1]], color=color, lw=lw)


def main():
    S = scene()
    hi = [i for i in head_instances(S) if inst_name(i).startswith("head[")][0]
    head = trimesh.load(os.path.join(HERE, "stl", "head.stl"), force="mesh")
    head.apply_transform(inst_world(S, hi))
    others = {inst_name(i): S.world_mesh(i) for i in head_instances(S) if i is not hi and np.ptp(S.world_mesh(i).bounds, axis=0).min() > 0.5}
    J = json.load(open(os.path.join(HERE, "mic_seats.json")))
    R = json.load(open(os.path.join(HERE, "mic_routes.json")))["routes"]
    pL = np.array(J["seats"]["left"]["mic_port_world"]); pR = np.array(J["seats"]["right"]["mic_port_world"])
    x0 = float(pL[0])
    # full section, plane x = x0 (y right to left is shown as seen from behind: y to the left on the page)
    fig, ax = plt.subplots(figsize=(8, 4.6), dpi=110)
    draw(ax, cut(head, [x0, 0, 0], [1, 0, 0]), (1, 2), "#333333")
    for n, m in others.items():
        draw(ax, cut(m, [x0, 0, 0], [1, 0, 0]), (1, 2), "#1f77b4", 0.6)
    for side, p, s in (("left", pL, J["seats"]["left"]), ("right", pR, J["seats"]["right"])):
        c = np.array(s["board_centre_world"]); n = np.array(s["inward_normal"])
        ax.plot([p[1]], [p[2]], "o", color="#d62728", ms=4)
        ax.annotate(f"{side} mic port", (p[1], p[2]), (p[1] - 30 * np.sign(p[1]), p[2] + 18), fontsize=7,
                    arrowprops=dict(arrowstyle="-", lw=0.5))
    for k, col in (("D14", "#2ca02c"), ("D15", "#9467bd")):
        P = np.array(R[k]["points"]); ax.plot(P[:, 1], P[:, 2], "--", color=col, lw=1.0, label=f"{k} route (projected)")
    ax.set_aspect("equal"); ax.invert_xaxis(); ax.set_xlabel("y, mm (robot left on the left)"); ax.set_ylabel("z, mm")
    ax.set_title(f"Head cut at x = {x0:.1f} mm: shell (black), other head parts (blue), mic ports (red)", fontsize=8)
    ax.legend(fontsize=6, loc="lower center"); ax.grid(alpha=0.2)
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "mic_section.png")); plt.close(fig)
    # close-ups: two cuts that contain the port axis (the wall normal n): one with the vertical, one with the horizontal
    for side, p in (("left", pL), ("right", pR)):
        n = np.array(J["seats"][side]["inward_normal"])
        h = np.cross(n, [0, 0, 1.0]); h /= np.linalg.norm(h)
        v = np.cross(h, n)
        fig, axs = plt.subplots(1, 2, figsize=(8, 3.8), dpi=110)
        for ax, (nrm, e2, lab) in zip(axs, ((h, v, "cut through the port axis and the vertical"),
                                             (v, h, "cut through the port axis and the horizontal"))):
            def proj(polys):
                return [np.stack([(q - p) @ n, (q - p) @ e2], 1) for q in polys]
            draw(ax, proj(cut(head, p, nrm)), (0, 1), "#333333", 1.0)
            for nm, m in others.items():
                draw(ax, proj(cut(m, p, nrm)), (0, 1), "#1f77b4", 0.6)
            ax.plot([0], [0], "o", color="#d62728", ms=4)
            ax.annotate("outside", (-5.5, 11), fontsize=7); ax.annotate("inside (board side)", (2, 11), fontsize=7)
            ax.set_xlim(-8, 10); ax.set_ylim(-13, 13); ax.set_aspect("equal"); ax.grid(alpha=0.2)
            ax.set_xlabel("along the wall normal, mm (+ inward)", fontsize=7); ax.set_title(lab, fontsize=8)
        fig.suptitle(f"{side} mic seat: wall 3.2 mm, port tube 4.0/2.0 x 3.0 mm, 1.2 mm port (red dot = mic port; the 2 bosses lie off these cuts)", fontsize=8)
        fig.tight_layout(); fig.savefig(os.path.join(HERE, f"mic_seat_{side}.png")); plt.close(fig)
    print("written")


if __name__ == "__main__":
    main()
