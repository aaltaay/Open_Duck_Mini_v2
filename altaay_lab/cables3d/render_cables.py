#!/usr/bin/env python3
"""PNG views of every cable in cables3d.json on the robot (numpy rasterizer, no OpenGL needed).

Usage: python3 altaay_lab/cables3d/render_cables.py --scratch <folder outside the repo> [--views all|detail]
Writes altaay_lab/cables3d/cables_all.png (whole robot, two views) and cables_detail.png (left leg and neck close-ups
with seats and ties) when the data carries them. Mesh decimation cache goes to the scratch folder.
Shell parts that hide the cables (body covers, head shell, leg covers) are left out and listed on the image.
"""
import argparse
import json
import os
import pickle
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import c3d_lib as L  # noqa: E402
import route_cables as RC  # noqa: E402

DRAW_SCALE = 1.4    # tubes drawn 1.4 x the bundle OD (at least 2.4 mm) so 26 AWG pairs stay visible
HIDE = {"body_front", "body_back", "body_middle_top", "body_middle_bottom", "battery_pack_lid", "head", "left_cache",
        "right_cache", "antenna", "bms"}
PART_COL = {"servo_top": (88, 96, 112), "servo_mid": (88, 96, 112), "servo_bottom": (88, 96, 112),
            "drive_palonier": (214, 150, 90), "passive_palonier": (214, 150, 90)}


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def decimated(s, scratch):
    import fast_simplification
    path = os.path.join(scratch, "c3d_render_meshes.pkl")
    if os.path.exists(path):
        return pickle.load(open(path, "rb"))
    out = {}
    for i in s.inst:
        if i["path"] in out:
            continue
        m = s.mesh(i)
        v, f = np.asarray(m.vertices), np.asarray(m.faces)
        tgt = 3500 if "servo" in i["key"] else 7000
        if len(f) > tgt:
            v, f = fast_simplification.simplify(v, f, target_reduction=1 - tgt / len(f))
        out[i["path"]] = (v, f)
    pickle.dump(out, open(path, "wb"))
    return out


def world_pts(s, pts):
    return np.array([(s.T0[p["link"]] @ np.r_[p["p"], 1.0])[:3] for p in pts])


def draw_scene(cv, s, dec, data, hide=HIDE, ghost=0.0, only_links=None, ties=True, seats=True, boxes=True):
    for i in s.inst:
        if i["key"] in hide:
            continue
        if only_links and i["link"] not in only_links:
            continue
        v, f = dec[i["path"]]
        T = s.T0[i["link"]] @ i["T"]
        V = (T[:3, :3] @ v.T).T + T[:3, 3]
        col = PART_COL.get(i["key"], (214, 208, 196) if i["printed"] else (110, 160, 105))
        cv.draw(V, f[:, ::-1] if i.get("mirrored") else f, col, ident=i["idx"])
    k = 5000
    if boxes:
        for t in data.get("terminals", []) + data.get("placed_boxes", []):
            if not t.get("center_mm"):
                continue
            b = L.box_mesh(t["center_mm"], t["dims_xyz_mm"])
            cv.draw(b.vertices, b.faces, (168, 120, 200), ident=k)
            k += 1
    for c in data["cables"]:
        cols = [hexrgb(x) for x in (c.get("colors") or [c["color"]])]
        for r in c.get("runs", [{"points": c["points"], "d_mm": c["d_mm"]}]):
            P = world_pts(s, r["points"])
            if len(P) < 2:
                continue
            P = RC.resample(P, 2.0)
            n = max(1, min(len(cols), 6))
            for V, F, col in L.bundle_tubes(P, cols[:n], max(r["d_mm"] * DRAW_SCALE, 2.4)):
                cv.draw(V, F, col, ident=k, ambient=0.6)
            k += 1
    if ties:
        for t in data.get("retention", []):
            c = np.array(t["center_mm"])
            ax = np.array(t.get("axis") or [0, 0, 1.0], float)
            ax /= np.linalg.norm(ax)
            rr = t.get("bundle_d_mm", 4.0) / 2 + 0.8
            ang = np.linspace(0, 2 * np.pi, 13)
            a = np.cross(ax, [0, 0, 1.0] if abs(ax[2]) < 0.9 else [1.0, 0, 0])
            a /= np.linalg.norm(a)
            b = np.cross(ax, a)
            ring = np.array([c + rr * (np.cos(q) * a + np.sin(q) * b) for q in ang])
            V, F = L.tube(ring, 0.7, k=5)
            cv.draw(V, F, (20, 20, 20), ident=k)
            k += 1
    cv.outline(depth_jump=3.0, strength=0.55)


def label(im, lines, xy=(8, 6), fill=(30, 30, 30)):
    d = ImageDraw.Draw(im)
    y = xy[1]
    for ln in lines:
        d.text((xy[0], y), ln, fill=fill)
        y += 13


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--views", default="all")
    a = ap.parse_args()
    s = RC.make_scene()
    dec = decimated(s, os.path.abspath(a.scratch))
    data = json.load(open(RC.OUT_JSON))
    if a.views in ("all", "both"):
        W, H = 760, 980
        ims = []
        for eye, tgt in (((420, 360, 300), (-35, 0, 30)), ((-430, -330, 260), (-35, 0, 30))):
            cv = L.Canvas(W, H, eye, tgt, up=(0, 0, 1), ortho_half=W / H * 275)
            draw_scene(cv, s, dec, data)
            ims.append(cv.image())
        out = Image.new("RGB", (2 * W, H), "white")
        for k, im in enumerate(ims):
            out.paste(im, (k * W, 0))
        n_runs = sum(len(c.get("runs", [])) for c in data["cables"])
        label(out, ["Open Duck Mini v2: all %d active cables (%d runs), coloured as wiring/netlist.yaml; kit cables grey" % (
            len(data["cables"]), n_runs), "Hidden to show the cables: body covers, head shell, leg covers, antennas. "
            "Purple boxes: parts seated by this work (XT30, amp, speaker, LEDs). Black rings: ties. Tubes drawn 1.4 x OD.",
            "Left: front-left view. Right: back-right view. Zero pose. Source: altaay_lab/cables3d/cables3d.json"])
        p = os.path.join(HERE, "cables_all.png")
        out = out.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        out.save(p, optimize=True)
        print(p, os.path.getsize(p) // 1024, "kB")
    if a.views in ("detail", "both"):
        W, H = 760, 760
        ims = []
        leg = {"trunk_assembly", "hip_roll_assembly", "left_roll_to_pitch_assembly", "knee_and_ankle_assembly",
               "knee_and_ankle_assembly_2", "foot_assembly"}
        neck = {"trunk_assembly", "neck_pitch_assembly", "head_pitch_to_yaw", "neck_yaw_assembly", "head_assembly"}
        specs = [(leg, (180, 420, -20), (-30, 80, -70), 150, "Left leg (seen from the left, slightly front)"),
                 (neck, (330, -260, 230), (5, 0, 150), 105, "Neck and head floor (seen from the front-right)")]
        for links, eye, tgt, half, title in specs:
            cv = L.Canvas(W, H, eye, tgt, up=(0, 0, 1), ortho_half=half)
            sub = dict(data)
            sub["cables"] = [c for c in data["cables"]]
            draw_scene(cv, s, dec, sub, only_links=links, hide=HIDE | {"head_bot_sheet"} if "head_assembly" not in links else HIDE)
            im = cv.image()
            label(im, [title])
            ims.append(im)
        out = Image.new("RGB", (2 * W, H), "white")
        for k, im in enumerate(ims):
            out.paste(im, (k * W, 0))
        p = os.path.join(HERE, "cables_detail.png")
        out = out.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        out.save(p, optimize=True)
        print(p, os.path.getsize(p) // 1024, "kB")


if __name__ == "__main__":
    main()
