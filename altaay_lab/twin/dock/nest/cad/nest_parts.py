#!/usr/bin/env python3
"""nest_parts.py: the nest: the felt mat with its golden sun and pale gold ring, and the soft rim at the wall with the
power jack and the electronics box inside. CAD check only (geometry), calc only (areas, resistances).

Run: NEST_OCP=<folder with OCP> python3 nest_parts.py
Writes stl/, step/ and nest_parts.json next to this file. Nest frame (mm): the sun centre on the floor is the origin,
x toward the wall (wall face at x = 190), y along the wall, z up. Every part is written in its assembled pose.

The mat, bottom to top (all flat cut parts, no printing):
  nest_felt_base   lower felt layer, 1.0 mm, radius 267, back cut flat 6 mm from the wall.
  nest_felt_top    upper felt layer, 1.0 mm, radius 247. The 20 mm tread of the lower layer means the duck never meets
                   a step higher than 1.0 mm (the sim tripped on a single 2 mm edge while steering). Two slits, each
                   with a job: the sun slit (the plus feed dives under the sun) and the box slit (it comes up again).
  nest_feed        plus feed: 12 mm copper foil tape wrapped in polyimide tape, BETWEEN the two felt layers, from under
                   the sun to the box. It never lies open on the mat.
  nest_sun_foil    copper foil disc, 90 mm, under the sun cloth: the plus current spreads in copper, not in cloth.
  nest_sun         golden conductive cloth disc, 100 mm across, plus. Centre 190 mm from the wall.
  nest_ring        pale gold conductive cloth ring, minus: radius 82 to 235 around the sun, cut 56 mm from the wall,
                   with a 24 mm notch over the plus feed and a tab that runs under the rim into the box.
The rim (454 x 50 x 30 mm, against the wall):
  nest_box_tray    printed PLA tray, 180 x 44.9 x 21.5 mm: jack hole in the left end wall, two terminal posts and four
                   lid posts with M3 heat-set inserts, two floor slots where the feed and the ring tab come up.
  nest_box_lid     printed PLA lid, 2 mm, 4 x M3x6 button head (BOM 17j) on the 4 corners (D42).
  nest_bolster_left, nest_bolster_right   foam blocks (cut, not printed) that continue the rim to both ends; the left
                   one carries the adapter cord in a channel along the wall and has a pocket for the plug.
  nest_rim_cover   felt sleeve over box and foam (sewn from 2 mm felt): what you see. Envelope only.
"""
import os
import sys

import numpy as np
import trimesh
from shapely.geometry import Point, Polygon, box as sbox, LineString
from shapely import affinity

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nestcad_lib as N  # noqa: E402
from nestcad_lib import L  # noqa: E402

W = N.WALL_X
RIM_X0 = W - N.RIM["depth"]                 # the rim's room-side face: 140
BX0, BX1 = W - N.BOX["x1"], W - N.VHB_T     # the box: 144.0 to 188.9 (VHB between its back and the wall)
BZ0, BZ1 = N.BOX["z0"], 25.5                # the box stands on the mat; lid top at 25.5
LID_T = N.BOX["lid"]
SLOT = dict(x0=BX0 + 2.5, x1=BX0 + 5.0, half=8.0)       # floor slots, 16 x 2.5 mm, at y = +TAB_Y (ring) and -TAB_Y (plus)
TAB_Y = 25.0
POST_X = BX0 + 10.0                          # terminal posts
LID_POSTS = [(BX0 + 14.0, 84.0), (BX0 + 14.0, -84.0), (BX1 - 6.0, 84.0), (BX1 - 6.0, -84.0)]      # 6 mm inside the lid's four corners
SUN_SLIT = dict(x0=43.0, x1=44.5, half=7.0)
FEED_A, FEED_B = np.array([30.0, 0.0]), np.array([SLOT["x0"] + 1.25, -TAB_Y])
JACK_Y = N.BOX["half_len"]
STANDINS = {   # what the box has to hold (stand-in envelopes, mm, nest frame centre; est unless a repo source is named)
    "jack": dict(size=(14.0, 20.0, 12.0), c=(W - N.JACK["x"], N.BOX["half_len"] - 2.0 - 10.0, N.JACK["z"]), note="Same Sky PJ-005A panel jack (dock BOM K6b), body est"),
    "fuse_holder": dict(size=(17.2, 50.0, 17.2), c=(BX1 - N.BOX["wall"] - 0.5 - 8.6, 40.0, 4.0 + 8.6), note="Littelfuse FHAC0001ZXJ (BOM DK3 class), body 50 x 17.2 x 17.2 (repo)"),
    "gate_board": dict(size=(26.0, 70.0, 14.0), c=(BX1 - N.BOX["wall"] - 0.5 - 13.0, -43.0, 4.0 + 2.0 + 7.0), note="gate and current limit board: NOT DESIGNED (BLOCKER); 70 x 26 x 14 mm is the space kept for it, clear of the terminal posts"),
}


def circle(rad, n=180, c=(0.0, 0.0)):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return Polygon(np.c_[c[0] + rad * np.cos(a), c[1] + rad * np.sin(a)])


def ext(poly, z0, z1):
    """extrude a shapely polygon (or multi) between z0 and z1"""
    polys = [poly] if poly.geom_type == "Polygon" else list(poly.geoms)
    ms = []
    for p in polys:
        m = trimesh.creation.extrude_polygon(p, z1 - z0)
        m.apply_translation((0, 0, z0))
        ms.append(m)
    return trimesh.util.concatenate(ms) if len(ms) > 1 else ms[0]


def strip(a, b, w):
    return LineString([a, b]).buffer(w / 2.0, cap_style=2)


def mat_shapes():
    back = sbox(-400, -400, W - N.MAT_BACK, 400)
    base = circle(N.BASE_R).intersection(back)
    top = circle(N.TOP_R).intersection(back)
    sun_slit = sbox(SUN_SLIT["x0"], -SUN_SLIT["half"], SUN_SLIT["x1"], SUN_SLIT["half"])
    box_slit = sbox(SLOT["x0"], -TAB_Y - SLOT["half"], SLOT["x1"], -TAB_Y + SLOT["half"])
    top = top.difference(sun_slit).difference(box_slit)
    sun = circle(N.SUN_R, 120)
    sun_foil = circle(45.0, 96)
    feed_top = sbox(FEED_A[0], -N.FEED_W / 2, SUN_SLIT["x1"], N.FEED_W / 2)                 # on the top felt, under the sun
    d = FEED_B - np.array([SUN_SLIT["x0"], 0.0])
    feed_mid = strip((SUN_SLIT["x0"], 0.0), tuple(FEED_B), N.FEED_W)                         # between the layers
    notch = strip((SUN_SLIT["x0"], 0.0), tuple(FEED_B + 40 * d / np.linalg.norm(d)), 24.0)
    ring = circle(N.RING_R1).difference(circle(N.RING_R0, 120)).intersection(sbox(-400, -400, W - N.RING_BACK, 400)).difference(notch)
    tab = sbox(W - N.RING_BACK - 1.0, TAB_Y - 7.0, SLOT["x1"], TAB_Y + 7.0)
    ring = ring.union(tab)
    return dict(base=base, top=top, sun=sun, sun_foil=sun_foil, feed_top=feed_top, feed_mid=feed_mid, ring=ring, notch=notch, tab=tab)


def loaf(x0, x1, y0, y1, z1, r_):
    """a soft loaf: vertical sides with rounded plan corners, a rounded top (hull of 4 spheres and 4 cylinders)"""
    pts = []
    for x in (x0 + r_, x1 - r_):
        for y in (y0 + r_, y1 - r_):
            s = trimesh.creation.icosphere(subdivisions=2, radius=r_)
            s.apply_translation((x, y, z1 - r_))
            c = trimesh.creation.cylinder(radius=r_, height=z1 - r_, sections=24)
            c.apply_translation((x, y, (z1 - r_) / 2))
            pts += [s.vertices, c.vertices]
    return L.hull_pts(np.vstack(pts))


def box_profile(inset=0.0, z_top=None):
    """the box cross-section in (x, z): a rectangle with the room-side top edge chamfered; inset shrinks it"""
    c = N.BOX["chamfer"] - 1.0
    zt = BZ1 if z_top is None else z_top
    P = Polygon([(BX0, BZ0), (BX1, BZ0), (BX1, zt), (BX0 + c, zt), (BX0, zt - c)])
    return P.buffer(-inset, join_style=2) if inset else P


def prism_xz(poly, y0, y1):
    """extrude an (x, z) polygon along y"""
    m = trimesh.creation.extrude_polygon(poly, y1 - y0)          # polygon in (x, y'), extruded along z'
    T = np.array([[1, 0, 0, 0], [0, 0, 1, y0], [0, 1, 0, 0], [0, 0, 0, 1.0]])     # (x, y', z') -> (x, z', y')
    m.apply_transform(T)
    if m.volume < 0:
        m.invert()
    return m


def cylz(x, y, z0, z1, d, sec=32):
    c = trimesh.creation.cylinder(radius=d / 2.0, height=z1 - z0, sections=sec)
    c.apply_translation((x, y, (z0 + z1) / 2.0))
    return c


def rim_parts():
    B = N.BOX
    hl, wl, fl = B["half_len"], B["wall"], B["floor"]
    z_split = BZ1 - LID_T                                       # the lid's underside: 23.5
    outer = N.man(prism_xz(box_profile(), -hl, hl))
    cav = N.man(prism_xz(box_profile(wl), -hl + wl, hl - wl))
    below = N.man(L.box((0, -300, -10), (300, 300, z_split)))
    tray = (outer - cav) ^ below
    # posts: 4 lid posts and 2 terminal posts, each with an M3 heat-set insert bore from its top
    posts, bores = [], []
    for (x, y) in LID_POSTS:
        posts.append(N.man(cylz(x, y, BZ0 + 0.5, z_split, 8.0)))
        posts.append(N.man(L.box((x - 4.0, min(y, y + np.sign(y) * 5.5), BZ0 + 0.5), (x + 4.0, max(y, y + np.sign(y) * 5.5), z_split))))     # tied into the end wall
        bores.append(N.man(cylz(x, y, z_split - N.INSERT_DEPTH, z_split + 1, N.INSERT_D, 24)))
    z_post = BZ0 + fl + 7.0
    for y in (TAB_Y, -TAB_Y):
        posts.append(N.man(cylz(POST_X, y, BZ0 + 0.5, z_post, 9.0)))
        bores.append(N.man(cylz(POST_X, y, z_post - N.INSERT_DEPTH, z_post + 1, N.INSERT_D, 24)))
        bores.append(N.man(L.box((SLOT["x0"], y - SLOT["half"], BZ0 - 1), (SLOT["x1"], y + SLOT["half"], BZ0 + fl + 0.01))))   # floor slot
    tray = (tray + L.union(posts)) ^ outer
    jack = trimesh.creation.cylinder(radius=N.JACK["hole"] / 2, height=wl + 2, sections=32)
    jack.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (1, 0, 0)))
    jack.apply_translation((W - N.JACK["x"], hl - wl / 2, N.JACK["z"]))
    tray = tray - L.union(bores) - N.man(jack)
    lid = outer ^ N.man(L.box((0, -300, z_split), (300, 300, 100)))
    lid = lid - L.union([N.man(cylz(x, y, z_split - 1, BZ1 + 1, N.M3_CLEAR, 24)) for (x, y) in LID_POSTS])
    # the soft parts
    R = N.RIM
    out_loaf = loaf(RIM_X0, W + 30, -R["half_len"], R["half_len"], R["height"], R["r_top"]) ^ N.man(L.box((0, -400, -1), (W, 400, 100)))   # flat against the wall
    t = 2.0
    in_loaf = loaf(RIM_X0 + t, W + 30, -R["half_len"] + t, R["half_len"] - t, R["height"] - t, R["r_top"] - t) ^ N.man(L.box((0, -400, -1), (W, 400, 100)))
    cord = N.man(L.box((W - 12.0, R["half_len"] - 30.0, -1), (W + 1, R["half_len"] + 5, 12.0)))        # cord exit, left end at the wall
    cover = out_loaf - in_loaf - cord
    mat_room = N.man(L.box((0, -400, -1), (W + 1, 400, 2 * N.FELT_T)))                                 # the mat passes under the rim
    core = in_loaf - mat_room
    left = core ^ N.man(L.box((0, hl + 0.5, -1), (300, 400, 100)))
    right = core ^ N.man(L.box((0, -400, -1), (300, -hl - 0.5, 100)))
    channel = N.man(L.box((W - 12.0, hl, -1), (W + 1, 400, 12.0)))                                      # adapter cord along the wall
    plug = N.man(L.box((W - N.JACK["x"] - 9.0, hl, N.JACK["z"] - 9.0), (W - N.JACK["x"] + 9.0, hl + 48.0, N.JACK["z"] + 9.0)))   # jack nut, plug body
    drop = N.man(L.box((W - N.JACK["x"], hl + 30.0, -1), (W + 1, hl + 48.0, N.JACK["z"] + 9.0)))        # the cord drops from the plug to the channel
    left = left - channel - plug - drop
    return dict(nest_box_tray=tray, nest_box_lid=lid, nest_rim_cover=cover, nest_bolster_left=left, nest_bolster_right=right), dict(
        z_split=z_split, z_post=z_post, inner_clear=dict(x=N.r(BX1 - BX0 - 2 * wl), y=N.r(2 * hl - 2 * wl), z=N.r(z_split - BZ0 - fl)))


def standins():
    out = {}
    for k, v in STANDINS.items():
        s, c = np.array(v["size"]), np.array(v["c"])
        out[k] = L.box(c - s / 2, c + s / 2)
    return out


def build():
    S = mat_shapes()
    z1, z2 = N.FELT_T, 2 * N.FELT_T
    parts = dict(
        nest_felt_base=ext(S["base"], 0.0, z1),
        nest_felt_top=ext(S["top"], z1, z2),
        nest_sun_foil=ext(S["sun_foil"], z2, z2 + N.FOIL_T),
        nest_sun=ext(S["sun"], z2 + N.FOIL_T, z2 + N.FOIL_T + N.CLOTH_T),
        nest_ring=ext(S["ring"], z2, z2 + N.CLOTH_T),
    )
    # the feed, one strip: under the sun on the top felt, down the sun slit, between the layers, up the box slit, to its post
    fd = [N.man(ext(S["feed_top"], z2, z2 + N.FOIL_T)), N.man(ext(S["feed_mid"], z1 - N.FOIL_T, z1)),
          N.man(L.box((SUN_SLIT["x0"], -N.FEED_W / 2, z1 - N.FOIL_T), (SUN_SLIT["x0"] + N.FOIL_T, N.FEED_W / 2, z2 + N.FOIL_T)))]
    rp, info = rim_parts()
    z_post = info["z_post"]
    fd.append(N.man(L.box((SLOT["x0"] + 1.2, -TAB_Y - N.FEED_W / 2, z1 - N.FOIL_T), (SLOT["x0"] + 1.2 + N.FOIL_T, -TAB_Y + N.FEED_W / 2, z_post + N.FOIL_T))))
    fd.append(N.man(L.box((SLOT["x0"] + 1.2, -TAB_Y - N.FEED_W / 2, z_post), (POST_X + 5.0, -TAB_Y + N.FEED_W / 2, z_post + N.FOIL_T))))
    parts["nest_feed"] = N.tm(L.union(fd))
    # the ring tab's rise into the box (cloth), part of the ring
    up = [N.man(parts["nest_ring"]), N.man(L.box((SLOT["x0"] + 1.2, TAB_Y - 7.0, z2), (SLOT["x0"] + 1.2 + N.CLOTH_T, TAB_Y + 7.0, z_post + N.CLOTH_T))),
          N.man(L.box((SLOT["x0"] + 1.2, TAB_Y - 7.0, z_post), (POST_X + 5.0, TAB_Y + 7.0, z_post + N.CLOTH_T)))]
    parts["nest_ring"] = N.tm(L.union(up))
    for k, M in rp.items():
        parts[k] = N.clean(M, k)
    return parts, S, info


MATERIAL = dict(nest_felt_base="wool or polyester felt, 1 mm (cut)", nest_felt_top="wool or polyester felt, 1 mm (cut)",
                nest_sun_foil="copper foil tape with conductive adhesive, 0.07 mm (cut)", nest_sun="gold conductive cloth, about 0.1 mm (cut)",
                nest_ring="pale gold conductive cloth, about 0.1 mm (cut)", nest_feed="12 mm copper foil tape in polyimide tape (cut)",
                nest_box_tray="PLA, printed", nest_box_lid="PLA, printed", nest_rim_cover="felt, 2 mm, sewn sleeve (envelope)",
                nest_bolster_left="soft foam, cut", nest_bolster_right="soft foam, cut")


def main():
    parts, S, info = build()
    rec = {}
    for k, m in parts.items():
        m.merge_vertices()
        N.write_part(k, m, rec, material=MATERIAL[k])
    areas = {k: N.r(S[k].area, 0) for k in ("base", "top", "sun", "sun_foil", "ring")}
    N.dump(dict(generated_by="nest_parts.py", label="CAD check only (geometry); calc only (areas)",
                frame="nest frame: sun centre on the floor is the origin, x toward the wall (wall at x = %g), y along the wall, z up; mm" % W,
                wall_x=W, sun_r=N.SUN_R, ring_r=[N.RING_R0, N.RING_R1], ring_back_from_wall=N.RING_BACK, felt_layers_mm=[N.FELT_T, N.FELT_T],
                top_r=N.TOP_R, base_r=N.BASE_R, tread_mm=N.BASE_R - N.TOP_R, stack_mm=dict(felt=2 * N.FELT_T, at_ring=2 * N.FELT_T + N.CLOTH_T,
                                                                                       at_sun=2 * N.FELT_T + N.FOIL_T + N.CLOTH_T),
                areas_mm2=areas, rim=N.RIM, box=dict(x=[BX0, BX1], z=[BZ0, BZ1], half_len=N.BOX["half_len"], **info),
                terminals=dict(plus=[POST_X, -TAB_Y], minus=[POST_X, TAB_Y]), lid_posts=LID_POSTS, jack=dict(y=JACK_Y, x=W - N.JACK["x"], z=N.JACK["z"]),
                standins=STANDINS, parts=rec), os.path.join(HERE, "nest_parts.json"))
    for k, v in rec.items():
        print("%-22s faces %6s vol %11s bbox %s stl %7s step %8s" % (k, v["faces"], v["volume_mm3"], v["bbox_mm"], v["bytes"], v.get("step_bytes")))
    print(info, areas)


if __name__ == "__main__":
    main()
