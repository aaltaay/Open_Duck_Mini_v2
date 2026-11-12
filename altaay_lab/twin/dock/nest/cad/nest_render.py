#!/usr/bin/env python3
"""nest_render.py: the renders of the nest assembly. CAD check only.

Run: MUJOCO_GL=egl python3 nest_render.py     (after duck_pins.py, nest_parts.py; reads the repo's sit pose and meshes)
Writes renders/*.png: side, top, three-quarter, the pin close-ups (a section through the right pins and a view of the
belly from below), the mat layers pulled apart, and the rim with its cover off.
"""
import os
import sys

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nestcad_lib as N  # noqa: E402
from nestcad_lib import L  # noqa: E402
import nest_assembly as A  # noqa: E402

W_, H_ = 1500, 1050
INK = (46, 44, 40)


def project(p, az, el, dist, look, w=W_, h=H_, fovy=30.0, ortho=None):
    a, e = np.radians(az), np.radians(el)
    fwd = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
    right = np.cross(fwd, [0, 0, 1.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    cam = np.asarray(look, float) / 1000.0 - dist * fwd
    v = np.asarray(p, float) / 1000.0 - cam
    if ortho:
        k = h / ortho
        return w / 2 + k * (v @ right), h / 2 - k * (v @ up)
    f = (h / 2) / np.tan(np.radians(fovy) / 2)
    return w / 2 + f * (v @ right) / (v @ fwd), h / 2 - f * (v @ up) / (v @ fwd)


def annotate(path, cam, labels, fovy=30.0, ortho=None):
    """labels: [(text, 3D point mm, (dx, dy) text offset in px)]: a leader line from the point to the text"""
    im = Image.open(path)
    dr = ImageDraw.Draw(im)
    try:
        f = ImageFont.truetype("DejaVuSans.ttf", 19)
    except OSError:
        f = ImageFont.load_default()
    for text, p, (dx, dy) in labels:
        x, y = project(p, *cam, fovy=fovy, ortho=ortho)
        tx, ty = x + dx, y + dy
        lines = text.split("\n")
        wd = max(dr.textlength(s, font=f) for s in lines)
        ht = 23 * len(lines)
        bx0 = tx if dx >= 0 else tx - wd
        by0 = ty - ht / 2
        dr.line([(x, y), (tx if dx >= 0 else tx, ty)], fill=INK, width=2)
        dr.ellipse([x - 4, y - 4, x + 4, y + 4], fill=INK)
        dr.rectangle([bx0 - 5, by0 - 3, bx0 + wd + 5, by0 + ht + 3], fill=(251, 250, 246), outline=(150, 146, 136))
        for k, s in enumerate(lines):
            dr.text((bx0, by0 + 23 * k), s, fill=INK, font=f)
    im.save(path)


def shot(name, items, cam, title, sub, labels=(), fovy=30.0, ortho=None):
    az, el, dist, look = cam
    out = os.path.join(N.IMG_DIR, name)
    N.render([(it["mesh"], it["rgba"]) for it in items], az, el, dist, look, out, title, w=W_, h=H_, fovy=fovy, sub=sub, ortho=ortho)
    if labels:
        annotate(out, cam, labels, fovy, ortho)
    print("wrote", name)


def cut(items, origin, normal, skip=("room",)):
    """keep the side of the plane the normal points to; capped where the mesh is watertight"""
    out = []
    for it in items:
        if it["group"] in skip:
            out.append(it)
            continue
        m = it["mesh"]
        d = (m.vertices - origin) @ np.asarray(normal, float)
        if d.min() >= 0:
            out.append(it)
            continue
        if d.max() <= 0:
            continue
        try:
            c = trimesh.intersections.slice_mesh_plane(m, normal, origin, cap=bool(m.is_watertight))
        except Exception:
            c = trimesh.intersections.slice_mesh_plane(m, normal, origin, cap=False)
        if len(c.faces):
            out.append(dict(it, mesh=c))
    return out


def section_fig(items, info):
    """a flat section drawing through the duck's right pins (nest plane y = +10): what sits where, to scale"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MPoly, Rectangle
    Y0 = 10.02
    fill = {"sit_seat": "#59606b", "sit_bumper": "#59606b", "pin_carrier_seat": "#3f9bc4", "pin_carrier_bumper": "#3f9bc4",
            "body_middle_bottom": "#f3d04f", "body_back": "#f3d04f", "body_front": "#f3d04f", "nest_felt_base": "#a9bd94", "nest_felt_top": "#b9cba3",
            "nest_sun": "#e0a92a", "nest_ring": "#efdc9a", "nest_sun_foil": "#c87f3f", "nest_feed": "#c87f3f", "nest_rim_cover": "#9db88c",
            "nest_box_tray": "#cfc5a8", "nest_box_lid": "#cfc5a8", "wall": "#e9e4d8", "floor": "#d8d2c3", "trunk_bottom": "#f3d04f",
            "foot_bottom_tpu": "#59606b"}
    segs, polys = [], []
    for it in items:
        key = it.get("key", it["name"])
        m = it["mesh"]
        if m.bounds[0][1] > Y0 or m.bounds[1][1] < Y0 or it["name"].startswith(("pin_plunger", "pin_socket", "lead_")):
            continue
        sec = m.section(plane_origin=(0, Y0, 0), plane_normal=(0, 1, 0))
        if sec is None:
            continue
        for e in sec.discrete:
            segs.append((key, np.asarray(e)[:, [0, 2]]))
        if key in fill:
            from shapely.geometry import Polygon as SPoly
            acc = None
            for e in sorted(sec.discrete, key=lambda q: -len(q)):
                q = np.asarray(e)[:, [0, 2]]
                if len(q) < 4:
                    continue
                pg = SPoly(q).buffer(0)
                if pg.is_empty:
                    continue
                acc = pg if acc is None else acc.symmetric_difference(pg)           # even-odd: holes come out as holes
            if acc is not None and not acc.is_empty:
                for pg in ([acc] if acc.geom_type == "Polygon" else list(acc.geoms)):
                    if pg.geom_type == "Polygon":
                        polys.append((key, pg))
    pins = info["pins"]
    fig, axs = plt.subplots(1, 2, figsize=(15, 8.3), gridspec_kw=dict(width_ratios=[1, 1]))
    fig.patch.set_facecolor("#fbfaf6")
    views = [("bump_R", "Belly bumper pin (minus)", (-170, -92), (-8, 62)), ("seat_R", "Seat block pin (plus)", (-39, 39), (-8, 62))]
    P = N.PIN
    Tn = np.array(info["trunk_T_nest_mm"])
    for ax, (pk, ttl, xl, zl) in zip(axs, views):
        ax.set_facecolor("#fbfaf6")
        for key, pg in polys:
            ax.add_patch(MPoly(np.asarray(pg.exterior.coords), closed=True, fc=fill[key], ec="none", zorder=2 if key.startswith(("nest", "wall", "floor")) else 3))
            for h in pg.interiors:
                ax.add_patch(MPoly(np.asarray(h.coords), closed=True, fc="#fbfaf6", ec="none", zorder=3.5))
        for key, e in segs:
            ax.plot(e[:, 0], e[:, 1], color="#2e2c28", lw=0.5 if key not in fill else 0.9, zorder=4, alpha=0.45 if key not in fill else 1)
        which = "bump" if pk.startswith("bump") else "seat"
        T = Tn @ N.pin_frame(which)
        r_ = N.BLOCK[which]["r"]
        y = -N.PIN_Y                                             # the duck's right pin is at nest y +10 (the duck faces -x)

        def pt(u):
            return (T @ np.array([0, y, u, 1.0]))[[0, 2]]
        comp = min(pins[pk]["compression_mm"], N.PROUD[which])
        tip = -r_ - N.PROUD[which] + comp
        mouth = -r_ - N.PROUD[which] + P["exposed"]
        for (u0, u1, d, c, z) in ((tip, mouth + 2 + comp, P["tube_d"], "#e8b923", 6), (mouth, mouth + P["socket_len"], P["socket_d"], "#9aa0a8", 5),
                                  (mouth + P["socket_len"], mouth + P["socket_len"] + P["tail_len"], 1.2, "#9aa0a8", 5)):
            a, b = pt(u0), pt(u1)
            n = np.array([-(b - a)[1], (b - a)[0]])
            n = n / np.linalg.norm(n) * d / 2
            ax.add_patch(MPoly([a - n, a + n, b + n, b - n], closed=True, fc=c, ec="#2e2c28", lw=0.5, zorder=z))
        tp = pt(tip)
        fp = pt(-r_)
        ax.plot([tp[0]], [tp[1] + P["tip_d"] / 2 * 0.0], "o", ms=5, color="#e8b923", mec="#2e2c28", zorder=7)
        ax.set_xlim(*xl)
        ax.set_ylim(*zl)
        ax.set_aspect("equal")
        ax.set_title(ttl, fontsize=15, loc="left", color="#2e2c28")
        ax.set_xlabel("mm from the sun centre (the wall is to the right)")
        ax.set_ylabel("mm above the floor")
        ax.grid(True, color="#d9d5ca", lw=0.5, zorder=0)
        kw = dict(fontsize=11, color="#2e2c28", zorder=9, bbox=dict(fc="#fbfaf6", ec="#96928a", lw=0.6), arrowprops=dict(arrowstyle="-", color="#2e2c28", lw=0.9))
        if which == "bump":
            ax.annotate("plunger: 7.5 mm proud when free,\npressed %.1f mm here: %.2f N (calc only)" % (pins[pk]["compression_mm"], pins[pk]["force_n"]), tp, (xl[0] + 2, -5.0), **kw)
            ax.annotate("bumper %.1f mm above the ring here\n(sim range 2.5 to 6.0 mm)" % pins[pk]["gap_mm"], (fp[0] - 9, (fp[1] + pins[pk]["mat_top_z"]) / 2 + 1.5), (xl[0] + 2, 10), **kw)
            ax.annotate("TPU bumper (D59):\npocket and 3.6 mm well", (fp[0] + 9, fp[1] + 8), (xl[1] - 30, 12), **kw)
            ax.annotate("PLA pin carrier, captive\nin the pocket, on VHB", pt(8.0) + [3.0, 0], (xl[1] - 30, 24), **kw)
            ax.annotate("socket (est size) pressed\ninto the carrier", pt(mouth + 14) + [0.8, 0], (xl[0] + 2, 22), **kw)
            ax.annotate("3.4 mm feedthrough in the\n11.2 mm belly floor: solder\ncup and 22 AWG lead", pt(mouth + P["socket_len"] + 3) + [1.2, 0], (xl[0] + 2, 52), **kw)
            ax.annotate("ring cloth (minus)\non 2 x 1 mm felt", (xl[1] - 12, 2.05), (xl[1] - 26, -5.0), **kw)
            ax.annotate("belly floor (body_middle_bottom)", (xl[1] - 22, 44), (xl[1] - 36, 56), **kw)
        else:
            ax.annotate("plunger: 3.0 mm proud when free,\npressed flush here: %.2f N (calc only)" % pins[pk]["force_n"], tp, (xl[0] + 2, -5.0), **kw)
            ax.annotate("TPU seat block (D59) rests\non the sun: the TPU takes\nthe load, not the pin", (fp[0] - 10, fp[1] + 6), (xl[0] + 2, 12), **kw)
            ax.annotate("PLA pin carrier", pt(14.0) + [-3.0, 0], (xl[0] + 2, 30), **kw)
            ax.annotate("3.4 mm feedthrough in the\n3.1 mm shell", pt(mouth + P["socket_len"] + 4.5) + [1.2, 0], (xl[1] - 32, 58), **kw)
            ax.annotate("sun cloth on copper foil (plus)", (xl[1] - 18, 2.1), (xl[1] - 36, -5.0), **kw)
            ax.annotate("body_back", (xl[1] - 12, 62), (xl[1] - 14, 44), **kw)
    fig.suptitle("Close-up of the pins: section through the duck's right pins, in the sit on the mat (to scale)", fontsize=17, x=0.02, ha="left", color="#2e2c28")
    fig.text(0.02, 0.925, "CAD check only. Pose: twin/sit/sit_pose.json (sim pass only). Probe and socket sizes are est and UNVERIFIED (catalog not opened). Thin grey lines: other parts cut by the plane.",
             fontsize=11, color="#5a564e")
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    fig.savefig(os.path.join(N.IMG_DIR, "pins_section.png"), dpi=110)
    print("wrote pins_section.png")


def main():
    os.makedirs(N.IMG_DIR, exist_ok=True)
    items, info = A.scene()
    pins = info["pins"]
    WX = N.WALL_X
    # ---------------------------------------------------------------- 1 side (orthographic: a true side view)
    cam = (90, 0.0, 3.0, (-25, 0, 225))
    yf = -430
    shot("nest_side.png", items, cam, "The nest, from the side: the duck sits on the sun, back to the wall",
         ["CAD check only. Sit pose: repo record twin/sit/sit_pose.json (sim pass only). Wall on the right, the room on the left. Flat (orthographic) view."],
         [("soft rim: 50 mm deep,\n30 mm high (jack and\nelectronics box inside)", (WX - 25, yf, 30), (75, -90)),
          ("felt mat, 2 layers of 1 mm:\nno step higher than 1 mm", (-255, yf, 1), (-70, -130)),
          ("seat block on the golden sun (plus)", (-4, yf, 3), (20, 98)),
          ("belly bumper: %.1f mm above the ring here,\nits two pins reach down (minus)" % pins["bump_L"]["gap_mm"], (-131, yf, 4), (-130, 75)),
          ("wall", (WX + 12, yf, 400), (60, -30)),
          ("tail: %.0f mm from the wall" % info["tail_to_wall_mm"], (WX - info["tail_to_wall_mm"], yf, info["tail_z_mm"]), (30, -130)),
          ("sun centre: 190 mm\nfrom the wall", (0, yf, 0), (255, 38))], ortho=0.62)
    # ---------------------------------------------------------------- 2 top (orthographic)
    cam = (90, -90.0, 3.0, (-5, 34, 0))
    shot("nest_top.png", items, cam, "The nest, from above",
         ["CAD check only. Sun 100 mm across, centre 190 mm from the wall; ring radius 82 to 235 mm; felt out to 247 and 267 mm.",
          "The wall is at the right. The duck faces the room (left). Flat (orthographic) view."],
         [("golden sun, plus\n(under the tail)", (44, 22, 3), (285, -250)),
          ("pale gold ring, minus", (-150, -160, 3), (-200, 60)),
          ("lower felt layer:\na 20 mm tread, 1 mm high", (-185, 180, 1), (-140, -60)),
          ("soft rim against the wall", (WX - 25, 120, 30), (110, -20)),
          ("adapter cord leaves here", (WX - 6, 227, 5), (80, -50)),
          ("plain felt gap, 32 mm", (66, 10, 2), (255, -20)),
          ("24 mm notch in the ring over\nthe hidden plus feed", (110, -18, 2), (200, 90)),
          ("ring tab goes under the rim", (136, 25, 2), (190, 100))], ortho=0.72)
    # ---------------------------------------------------------------- 3 three-quarter
    cam = (38, -24, 1.95, (-40, 0, 110))
    shot("nest_three_quarter.png", items, cam, "The nest, three-quarter view from the room",
         ["CAD check only. Nothing technical shows: felt, cloth and a soft rim. No tags, no markers. The golden sun is under the duck."],
         [("pale gold cloth ring", (-120, -190, 3), (-140, 120)),
          ("soft felt rim, fixed to the wall", (WX - 25, -180, 30), (120, 110)),
          ("felt edge: two 1 mm steps", (-150, -215, 1), (-330, 60))])
    alone = [it for it in items if not it["group"].startswith("duck")]
    cam = (38, -30, 1.55, (-10, 0, 20))
    shot("nest_alone.png", alone, cam, "The nest without the duck",
         ["CAD check only. A round felt mat, a golden cloth sun, a pale gold ring, and a soft rim along the wall. The plus feed runs hidden between the felt layers."],
         [("golden cloth sun, 100 mm, plus", (0, 0, 3), (-330, -230)),
          ("pale gold cloth ring, minus", (-120, -150, 3), (-190, 150)),
          ("soft felt rim: jack and box inside", (WX - 25, -150, 30), (140, 100)),
          ("plain felt, 32 mm, between sun and ring", (66, 0, 2), (150, -260)),
          ("adapter cord leaves along the wall", (WX - 6, 227, 4), (-300, -110))])
    # ---------------------------------------------------------------- 4 pins: section drawing
    section_fig(items, info)
    # ---------------------------------------------------------------- 5 pins: the belly from below (trunk frame, plungers free, legs hidden)
    S = L.scene(fresh=True)
    DP = A.duck_pins_json()
    under = []
    for i in S.inst:
        if i["link"] not in (N.TR, "sit_seat", "sit_bumper") or i["key"] in A.SKIP or i["key"] in ("servo_mid", "servo_top", "servo_bottom", "drive_palonier", "passive_palonier"):
            continue
        Tw = S.T0[i["link"]] @ i["T"]
        m = A.load_part(i["key"]) if i["key"] in A.CHANGED else S.mesh(i).copy()
        m.apply_transform(Tw)
        under.append(dict(mesh=m, rgba=N.COL["tpu"] if i["key"].startswith("sit_") else N.COL["duck"], group="duck"))
    tips = {}
    for which in ("seat", "bump"):
        T = N.pin_frame(which)
        r_ = N.BLOCK[which]["r"]
        for y in (N.PIN_Y, -N.PIN_Y):
            t = -r_ - N.PROUD[which]
            head = trimesh.creation.icosphere(subdivisions=2, radius=N.PIN["tip_d"] / 2)
            head.apply_translation((0, y, t + N.PIN["tip_d"] / 2))
            head.apply_transform(T)
            under.append(dict(mesh=trimesh.util.concatenate([head, N.cyl_u(T, y, t + 1.0, -r_ + 3.0, N.PIN["tube_d"], 16)]), rgba=(1.0, 0.78, 0.1, 1), group="pin"))
            tips[(which, y)] = (T @ np.array([0, y, t, 1.0]))[:3]
    cam = (55, 38, 0.46, (-45, 0, -52))
    shot("pins_underside.png", under, cam, "Close-up of the pins: the belly from below, plungers free (legs hidden)",
         ["CAD check only. Trunk parts only, zero pose, seen from below and behind. Two pins in the seat block (plus), two in the belly bumper (minus),",
          "20 mm apart, 130 mm between the pairs. The blocks keep their D59 outer shape; each pin stands in a 3.6 mm well."],
         [("seat pins (plus): 3.0 mm proud", tips[("seat", -N.PIN_Y)], (-150, 170)),
          ("bumper pins (minus): 7.5 mm proud", tips[("bump", N.PIN_Y)], (60, 130)),
          ("TPU seat block", (-112, -34, -50), (-260, -120)),
          ("TPU belly bumper", (20, -26, -55), (150, -170)),
          ("belly (body_middle_bottom)", (-40, 30, -35), (-330, 210))])
    # ---------------------------------------------------------------- 6 the mat layers pulled apart
    nest, _ = A.scene(duck=False, room=False, standins=False, cover=False)
    lift = dict(nest_felt_base=0, nest_feed=190, nest_felt_top=380, nest_sun_foil=570, nest_ring=570, nest_sun=610)
    ex = []
    for it in nest:
        if it["name"] in lift:
            m = it["mesh"].copy()
            m.apply_translation((0, 0, lift[it["name"]]))
            ex.append(dict(it, mesh=m))
    cam = (62, -24, 4.0, (0, 0, 300))
    shot("mat_layers.png", ex, cam, "How the conductors reach the rim: the mat layers pulled apart",
         ["CAD check only. Bottom to top: felt 1 mm, plus feed (copper foil in polyimide tape), felt 1 mm, then the sun (cloth on a foil disc) and the ring cloth.",
          "The wall side is at the right. Both conductors end on M3 terminal posts inside the rim's box."],
         [("lower felt, 1 mm, radius 267", (-200, -150, 0), (-170, 80)),
          ("plus feed, between the felt layers:\nnever open on the mat", (100, -14, 190), (150, 60)),
          ("its end rises through the box slit\nto the plus terminal post", (152, -25, 197), (120, -40)),
          ("upper felt, 1 mm, radius 247", (-150, -150, 380), (-300, 60)),
          ("sun slit: the feed comes up here\nunder the sun", (44, 0, 381), (150, 40)),
          ("ring cloth (minus), notched 24 mm\nover the feed", (-130, 150, 570), (-90, -150)),
          ("ring tab: under the rim, up to\nthe minus terminal post", (148, 25, 574), (120, -30)),
          ("sun cloth (plus)", (-20, 0, 610), (-250, -90)),
          ("90 mm copper foil disc\nunder the sun cloth", (30, -30, 570), (190, 70))], ortho=1.15)
    # ---------------------------------------------------------------- 7 the rim with the cover and the lid off
    rim = [it for it in A.scene(duck=False, room=True, standins=True, cover=False)[0] if it["name"] not in ("nest_box_lid",)]
    cam = (22, -48, 0.62, (WX - 26, 25, 8))
    shot("rim_open.png", rim, cam, "Inside the rim: felt sleeve and lid taken off",
         ["CAD check only. Printed tray 180 x 44.9 x 21.5 mm between two foam blocks. Stand-in boxes: jack, fuse holder, gate board (the board is NOT designed)."],
         [("DC jack (PJ-005A) in the end wall", (WX - N.JACK["x"], 82, N.JACK["z"] + 6), (-200, -230)),
          ("fuse holder (stand-in)", (WX - 12, 40, 21), (60, -230)),
          ("room kept for the gate board\n70 x 26 x 14 mm (BLOCKER)", (WX - 16, -43, 20), (150, -150)),
          ("minus terminal post:\nring tab under an M3x8", (154, 25, 11), (-330, 170)),
          ("plus terminal post:\nfeed foil under an M3x8", (154, -25, 11), (-120, 230)),
          ("foam block with the cord channel\nand the plug pocket", (WX - 30, 150, 28), (10, 250)),
          ("lid post with M3 insert (4)", (158, -84, 23.5), (150, 150)),
          ("plain foam block", (WX - 30, -170, 28), (-330, 130))])


if __name__ == "__main__":
    main()
