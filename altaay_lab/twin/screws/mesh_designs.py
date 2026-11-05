"""Printed shear lips for the trunk shells, so 3 screws per shell can hold body_front and body_back
(CAD check only, calc only). Also the coupons for the lip fit and the printed cable clip (snap).

Why: with 8 screws per shell the side and vertical shear of a fall on a shell goes through the screws in bearing
(STRUCTURE_TWIN.md has no lip: lateral contact 35 to 65 mm2, data/geom_joints.json). A lip on the middle part, just
inside the shell wall, carries that shear by bearing on the shell wall, and the screws then only hold the shell on.

What it builds (all NEW files; print/ is not touched):
  - body_middle_top: a lip on its front face only. That face is the top of its print (up +x, print/parts.csv), so the
    lip grows straight up; its back face is the print bed, so no lip there.
  - body_middle_bottom (up +z): front and back faces are vertical in print. Side lips are vertical plates; the
    bottom keys are short ribs whose 4 x 2 mm undersides face down (they add small supported overhangs to a part that
    already prints on supports: PRINT_CHECK.md, body_middle_bottom 6143 mm2).
Checks per new part: fit against the shell and every other trunk part (gap >= the design clearance, no overlap),
lip thickness, added overhang area (PRINT_CHECK.md rule: downward faces steeper than 45 deg from vertical), and the
lip capacity per load direction (bearing on the shell wall and root bending, cited PLA strengths).
Run under ramcap (about 1.5 GB). Writes data/lips.json, STLs to /home/user/v1_out/screws/stl and, when under 5 MB,
to twin/screws/stl/.
"""
import json, os, sys, math
import numpy as np
import trimesh
from shapely.geometry import Polygon, MultiPolygon, box, Point
from shapely.ops import unary_union
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(LAB, "fasteners"))
from fastlib import Scene  # noqa: E402

OUT = "/home/user/v1_out/screws/stl"
GIT_STL = os.path.join(HERE, "stl")
C, T_LIP, H_LIP = 0.25, 2.5, 2.0          # design clearance, lip thickness, lip height (mm)
RIB_W, RIB_T, RIB_PITCH = 4.0, 4.0, 12.0  # bottom ribs: width along the wall, height, pitch
KEEP_OUT_R = 5.0                           # free circle round every screw site (boss, insert, head)
ANCHOR = 3.5                               # the lip's root: the middle part's inner wall thickened this deep, 45 deg steps
PLA_X, PLA_Z = 47.1, 22.0                  # MPa, STRUCTURE_TWIN.md section 2.2 (Overture TDS X; Ezeh and Susmel Z)
E_PLA = 2641.0                             # MPa, STRUCTURE_TWIN.md section 2.2 (Overture TDS)
UP = {"body_middle_top": np.array([1.0, 0, 0]), "body_middle_bottom": np.array([0, 0, 1.0])}  # print/parts.csv


def frame(d):
    v = np.array([0, 0, 1.0])
    u = np.cross(v, d); u /= np.linalg.norm(u)
    return u, np.cross(d, u), d


def section_polys(mesh, O, u, v, d, s):
    p = mesh.section(plane_origin=O + s * d, plane_normal=d)
    if p is None:
        return Polygon()
    R = np.eye(4); R[:3, :3] = np.vstack([u, v, d]); R[:3, 3] = -R[:3, :3] @ (O + s * d)
    planar, _ = p.to_planar(to_2D=R, check=False)
    return unary_union([g.buffer(0) for g in planar.polygons_full])


def cavity_of(poly):
    """Inside of a shell section: its convex hull less its material (a U-shaped section has no hole of its own)."""
    if poly.is_empty:
        return Polygon()
    return poly.convex_hull.difference(poly.buffer(0.05))


def parts(g):
    return [x for x in getattr(g, "geoms", [g]) if not x.is_empty and x.area > 0.5]


def extrude(poly2d, O, u, v, d, s0, h):
    out = []
    for g in parts(poly2d):
        m = trimesh.creation.extrude_polygon(g, h)
        T = np.eye(4); T[:3, 0], T[:3, 1], T[:3, 2], T[:3, 3] = u, v, d, O + s0 * d
        m.apply_transform(T)
        out.append(m)
    return trimesh.util.concatenate(out) if out else None


def lip_for(S, shell_i, mid_i, screw_seats, scene_trunk, other_mid_i):
    mS, mM = S.mesh(shell_i), S.mesh(mid_i)
    name = S.inst[mid_i]["key"]
    cS = mS.centroid
    # d: from the middle part toward the shell, along x
    d = np.array([1.0, 0, 0]) if cS[0] > mM.centroid[0] else np.array([-1.0, 0, 0])
    x0 = float((mS.vertices @ d).min())                  # shell rim plane along d
    u, v, _ = frame(d)
    O = np.zeros(3)
    up = UP[name]
    dup = float(d @ up)
    rep = dict(part=name, shell=S.inst[shell_i]["key"], d=d.tolist(), rim_plane=round(x0, 2), d_dot_up=dup)
    if dup < -0.7:
        rep["lip"] = "none: this face is the print bed (a lip would hang under the bed)"
        return rep, None
    cav = cavity_of(section_polys(mS, O, u, v, d, x0 + 0.6))
    secM = section_polys(mM, O, u, v, d, x0 - 0.6)
    cavM = cavity_of(unary_union([secM, section_polys(S.mesh(other_mid_i), O, u, v, d, x0 - 0.6)]))
    others = []
    for k in scene_trunk:
        if k in (mid_i, shell_i):
            continue
        m = S.mesh(k)
        lo, hi = float((m.vertices @ d).min()), float((m.vertices @ d).max())
        for z in np.arange(-ANCHOR + 0.25, H_LIP + 0.31, 0.5):
            if lo <= x0 + z <= hi:
                others.append(section_polys(m, O, u, v, d, x0 + z))
    keep_O = unary_union(others).buffer(C) if others else Polygon()
    keep_S = unary_union([section_polys(mS, O, u, v, d, x0 + z) for z in (0.3, H_LIP / 2, H_LIP + 0.3)]).buffer(C)
    sites = unary_union([Point((p - O) @ u, (p - O) @ v).buffer(KEEP_OUT_R) for p in screw_seats])
    band = cav.buffer(-C).difference(cav.buffer(-C - T_LIP)).difference(keep_S).difference(sites).difference(keep_O)
    vlim = box(-1e4, secM.bounds[1], 1e4, secM.bounds[3] - 0.5)   # only where this middle part has wall at the face
    band = band.intersection(vlim)
    rep["cavity_mm2"] = dict(shell=round(cav.area, 0), middle=round(cavM.area, 0))
    if cav.area < 1000:   # solid cover plate (body_front is 10 mm deep): tongue on the middle part's rim, groove in the cover
        return tongue_for(S, shell_i, mid_i, mS, mM, O, u, v, d, x0, up, dup, secM, sites, keep_O, scene_trunk, rep)
    pieces = []
    if dup > 0.7:  # grows straight up in print: the whole band
        pieces = [(g, "band") for g in parts(band)]
    else:          # horizontal in print: vertical plates along the side walls, ribs along the bottom wall
        vmin = min(g.bounds[1] for g in parts(cav)) if parts(cav) else 0
        vmax = max(g.bounds[3] for g in parts(cav)) if parts(cav) else 0
        side = band.difference(box(-1e4, -1e4, 1e4, vmin + C + T_LIP + 2.0)).difference(box(-1e4, vmax - C - T_LIP - 2.0, 1e4, 1e4))
        for g in parts(side):
            w, h = g.bounds[2] - g.bounds[0], g.bounds[3] - g.bounds[1]
            if h > 2 * w:   # keep runs along the print up direction only
                pieces.append((g, "side"))
        bot = cav.buffer(-C).intersection(box(-1e4, vmin + C, 1e4, vmin + C + RIB_T)).difference(keep_S).difference(sites).difference(keep_O).intersection(vlim)
        bb = bot.bounds if not bot.is_empty else None
        if bb:
            n = int((bb[2] - bb[0]) // RIB_PITCH)
            for k in range(n + 1):
                uc = bb[0] + RIB_PITCH / 2 + k * RIB_PITCH
                r = bot.intersection(box(uc - RIB_W / 2, -1e4, uc + RIB_W / 2, 1e4))
                for g in parts(r):
                    if g.area > 0.7 * RIB_W * RIB_T:
                        pieces.append((g, "rib"))
    pieces = [(g, k) for g, k in pieces if not g.buffer(-0.6).is_empty]   # 1.2 mm minimum wall
    if not pieces:
        rep["lip"] = "none fits"
        return rep, None
    # root: the middle part's inner wall thickened behind each piece, in 0.5 mm steps that grow 0.5 mm per step
    # away from the face (45 deg, so the underside needs no support when the face is the top of the print)
    wallM = cavM.difference(cavM.buffer(-(C + T_LIP + 0.6))).intersection(secM.buffer(C + T_LIP + 0.7)).difference(keep_O).difference(sites)
    if dup <= 0.7:   # ribs stand on the floor of the middle part: root goes down to its floor
        vminM = min(g.bounds[1] for g in parts(cavM)) if parts(cavM) else 0
        wallM = unary_union([wallM, cavM.intersection(box(-1e4, vminM - 1, 1e4, vminM + C + RIB_T))])
    sol = []
    for g, kind in pieces:
        sol.append(extrude(g, O, u, v, d, x0 - ANCHOR, ANCHOR + H_LIP))
        reach = g.buffer(C + 0.6)
        nst = int(ANCHOR / 0.5)
        for j in range(nst):
            grow = (j + 1) / nst
            r = wallM.intersection(reach).intersection(cavM.difference(cavM.buffer(-(C + T_LIP + 0.6) * grow))) if dup > 0.7 else wallM.intersection(reach)
            if not r.is_empty and r.area > 0.2:
                top = min(x0 - ANCHOR + (j + 1) * 0.5 + 0.02, x0 - C)
                if top > x0 - ANCHOR + j * 0.5:
                    sol.append(extrude(r, O, u, v, d, x0 - ANCHOR + j * 0.5, top - (x0 - ANCHOR + j * 0.5)))
    solid = trimesh.util.concatenate([m for m in sol if m is not None])
    # ---- checks ------------------------------------------------------------------------------------
    pts, fi = trimesh.sample.sample_surface_even(solid, max(4000, int(solid.area * 6)), seed=2)
    outer = pts[(pts - O) @ d > x0 - ANCHOR - 0.5]       # the whole lip and its root
    gaps = {}
    for k, inst in scene_trunk.items():
        if k == mid_i:
            continue
        m = S.mesh(k)
        if m.bounds[0][0] > solid.bounds[1][0] + 2 or m.bounds[1][0] < solid.bounds[0][0] - 2:
            continue
        q = trimesh.sample.sample_surface_even(m, max(2000, int(m.area * 3)), seed=3)[0]
        dd, _ = cKDTree(q).query(outer)
        inside = 0
        if m.is_watertight:
            inside = int(m.contains(outer[::7]).sum())
        gaps[inst["key"] + "#%d" % k] = dict(min_gap_mm=round(float(dd.min()), 2), lip_points_inside=inside)
    down = solid.face_normals @ up < -math.cos(math.radians(45))
    on_root = np.zeros(len(solid.faces), bool)
    overhang = float(solid.area_faces[down & ~on_root].sum())
    widths = [round(2 * max(r for r in np.arange(0.05, 5, 0.05) if not g.buffer(-r).is_empty), 2) for g, _ in pieces]
    # ---- capacity per load direction (calc only) ------------------------------------------------------
    root_strength = PLA_Z if dup > 0.7 else PLA_X     # root plane is a layer plane when the lip grows up in print
    cap = {"+y": 0.0, "-y": 0.0, "z_up": 0.0, "z_down": 0.0}
    for g, kind in pieces:
        c2 = np.array(g.centroid.coords[0])
        cw = O + c2[0] * u + c2[1] * v
        minx, miny, maxx, maxy = g.bounds
        if kind == "rib":
            w, t = maxx - minx, maxy - miny
            bearing = w * H_LIP * PLA_X
            bend = PLA_X * w * t ** 2 / 6 / (H_LIP / 2)
            cap["z_up"] += min(bearing, bend)
            continue
        L = max(maxx - minx, maxy - miny)
        bearing = L * H_LIP * PLA_X
        bend = root_strength * L * T_LIP ** 2 / 6 / (H_LIP / 2)
        f = min(bearing, bend)
        horiz = (maxx - minx) > (maxy - miny)
        if horiz:
            cap["z_down" if c2[1] > (cav.bounds[1] + cav.bounds[3]) / 2 else "z_up"] += f
        else:
            cap["-y" if cw[1] > 0 else "+y"] += f   # a lip at +y world stops the shell moving +y
    rep.update(lip="built", pieces=[k for _, k in pieces], n_pieces=len(pieces), thickness_mm=widths,
               min_thickness_mm=min(widths), lip_volume_mm3=round(float(solid.volume), 0),
               added_overhang_mm2_over_45deg=round(overhang, 0), fit=gaps,
               capacity_N={k: round(v, 0) for k, v in cap.items()}, root_strength_MPa=root_strength)
    return rep, solid


T_TONGUE = 3.0


def tongue_for(S, shell_i, mid_i, mS, mM, O, u, v, d, x0, up, dup, secM, sites, keep_O, scene_trunk, rep):
    secS = section_polys(mS, O, u, v, d, x0 + 0.6)
    rim = secM.intersection(secS)
    hull = unary_union([secM, secS]).convex_hull
    tongue = hull.buffer(-1.0).difference(hull.buffer(-1.0 - T_TONGUE)).intersection(rim.buffer(-0.3))
    tongue = tongue.difference(sites).difference(keep_O)
    vminM = float((mM.vertices @ up).min())
    pieces = []
    for g in parts(tongue):
        if g.buffer(-0.6).is_empty:
            continue
        w, h = g.bounds[2] - g.bounds[0], g.bounds[3] - g.bounds[1]
        if dup > 0.7:
            pieces.append((g, "tongue"))
        elif h > 2 * w:
            pieces.append((g, "tongue side"))
        else:   # horizontal run: only where it lies on the print bed (no overhang)
            c3 = O + g.bounds[1] * v + x0 * d
            if abs(float(c3 @ up) - vminM) < 0.6 and abs(up @ v) > 0.9:
                pieces.append((g, "tongue bottom on bed"))
    rep["mode"] = "tongue and groove (the cover is a solid plate)"
    if not pieces:
        rep["lip"] = "none fits"
        return rep, None
    solid = trimesh.util.concatenate([extrude(g, O, u, v, d, x0 - 0.3, H_LIP + 0.3) for g, _ in pieces])
    groove = trimesh.util.concatenate([extrude(g.buffer(C), O, u, v, d, x0 - 0.01, H_LIP + C + 0.01) for g, _ in pieces])
    newS = trimesh.boolean.difference([mS, groove], engine="manifold")
    pts = trimesh.sample.sample_surface_even(solid, max(4000, int(solid.area * 6)), seed=2)[0]
    q = trimesh.sample.sample_surface_even(newS, max(4000, int(newS.area * 3)), seed=3)[0]
    dd, _ = cKDTree(q).query(pts[(pts - O) @ d > x0 + 0.05])
    upS = np.array([1.0, 0, 0]) if S.inst[shell_i]["key"] == "body_front" else np.array([-1.0, 0, 0])
    gdown = groove.face_normals @ (-upS) > math.cos(math.radians(45))   # groove faces become downward roofs in the cover
    root_strength = PLA_Z if dup > 0.7 else PLA_X
    cap = {"+y": 0.0, "-y": 0.0, "z_up": 0.0, "z_down": 0.0}
    for g, kind in pieces:
        W, Hh = g.bounds[2] - g.bounds[0], g.bounds[3] - g.bounds[1]
        tt = T_TONGUE
        fr = lambda L: min(L * H_LIP * PLA_X, root_strength * L * tt ** 2 / 6 / (H_LIP / 2))
        if W > 10 and Hh > 10:   # one U-shaped band: top run (vertical shear both ways) and two legs (side shear)
            cap["z_up"] += fr(W); cap["z_down"] += fr(W)
            cap["+y"] += fr(Hh - tt); cap["-y"] += fr(Hh - tt)
            continue
        L = max(W, Hh)
        f = fr(L)
        if W > Hh:
            cap["z_up"] += f; cap["z_down"] += f      # a groove holds the tongue both ways
            continue
        else:
            cap["+y"] += f; cap["-y"] += f
    widths = [round(2 * max(r for r in np.arange(0.05, 3, 0.05) if not g.buffer(-r).is_empty), 2) for g, _ in pieces]
    rep.update(lip="built", pieces=[k for _, k in pieces], n_pieces=len(pieces), tongue_width_mm=widths,
               min_tongue_width_mm=min(widths), lip_volume_mm3=round(float(solid.volume), 0),
               fit={"cover with groove": dict(min_gap_mm=round(float(dd.min()), 2) if len(dd) else None)},
               groove_roof_mm2=round(float(groove.area_faces[gdown].sum()), 0),
               groove_note="the groove roofs are bridges %.1f mm wide in the cover's print (bed face); PRINT_CHECK.md counts them as overhang" % (T_TONGUE + 2 * C),
               capacity_N={k: round(v, 0) for k, v in cap.items()}, root_strength_MPa=root_strength,
               new_cover=S.inst[shell_i]["key"] + "_groove")
    rep["_cover_mesh"] = newS
    return rep, solid


def clip_snap():
    """Printed cable clip (C clip, two cantilever arms) that snaps over a bundle: strain check (calc only)."""
    t, L, y = 0.9, 12.0, 0.4
    eps = 1.5 * t * y / L ** 2
    eps_lin = PLA_X / E_PLA
    allow_once, allow_service = eps_lin / 2, 0.6 * eps_lin / 2
    return dict(arm_t_mm=t, arm_L_mm=L, deflection_mm=y, strain_pct=round(100 * eps, 3),
                linear_limit_pct=round(100 * eps_lin, 3), allow_once_pct=round(100 * allow_once, 3),
                allow_service_pct=round(100 * allow_service, 3), passes=eps <= allow_service,
                formula="[I] https://www.fictiv.com/articles/how-to-design-snap-fit-components (search text: Bayer cantilever "
                        "eps = 1.5 t y / (L^2 Q), Q = 1 here; frequent separation: 60 % of the one-time strain)",
                limit="linear limit X 47.1 / E 2641 MPa (STRUCTURE_TWIN.md 2.2) with the lab margin 2; ASSUMPTION: printed "
                      "PLA stays linear to that strain; coupon K3 checks it")


def clip_mesh():
    """Two-arm snap clip for a bundle up to 6.0 mm: base 10 x 2, arms 0.9 thick and 12 long, barbs 0.4 in with a
    45 deg lead-in (opening 5.2). Prints flat, so the arms bend in the layer plane."""
    base = box(-5, 0, 5, 2)
    arms = [box(-3.9, 2, -3.0, 14), box(3.0, 2, 3.9, 14)]
    barbs = [Polygon([(-3.0, 12.6), (-2.6, 13.0), (-2.6, 13.6), (-3.0, 14.0)]),
             Polygon([(3.0, 12.6), (2.6, 13.0), (2.6, 13.6), (3.0, 14.0)])]
    return trimesh.creation.extrude_polygon(unary_union([base] + arms + barbs), 5.0)


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(GIT_STL, exist_ok=True)
    S = Scene("/home/user/v1_out/screws/scene")
    F = json.load(open(os.path.join(LAB, "fasteners", "fasteners.json")))["fasteners"]
    idx = {i["key"]: k for k, i in enumerate(S.inst)}
    trunk = {k: i for k, i in enumerate(S.inst) if i["link"] == "trunk_assembly" and i["printed"] or
             (i["link"] == "trunk_assembly" and k < S.n_urdf)}
    report, solids, covers = {}, {}, {}
    for shell in ("body_front", "body_back"):
        seats = [np.array(x["seat_world"]) for x in F if x["kind"] == "screw" and x["part"] == shell]
        report[shell] = {"pieces": {}}
        cover = None
        for mid in ("body_middle_top", "body_middle_bottom"):
            other = idx["body_middle_bottom" if mid == "body_middle_top" else "body_middle_top"]
            rep, solid = lip_for(S, idx[shell], idx[mid], seats, trunk, other)
            report[shell]["pieces"][mid] = rep
            if solid is not None:
                solids.setdefault(mid, []).append(solid)
            cm = rep.pop("_cover_mesh", None)
            if cm is not None:
                cover = cm if cover is None else trimesh.boolean.intersection([cover, cm], engine="manifold")
            print(shell, mid, {k: rep[k] for k in rep if k not in ("fit",)})
            if "fit" in rep:
                print("  fit:", {k: v for k, v in rep["fit"].items() if v["min_gap_mm"] < 1.0 or v["lip_points_inside"]})
        if cover is not None:
            k = idx[shell]
            cv = cover.copy(); cv.apply_transform(np.linalg.inv(S.inst[k]["T"]))
            covers[shell] = cover
            pth = os.path.join(OUT, shell + "_groove.stl"); cv.export(pth)
            report.setdefault("files", {})[shell] = dict(path=pth, bytes=os.path.getsize(pth), watertight=bool(cv.is_watertight))
            if os.path.getsize(pth) < 5e6:
                cv.export(os.path.join(GIT_STL, shell + "_groove.stl"))
        cap = {}
        for rep in report[shell]["pieces"].values():
            for k, v in rep.get("capacity_N", {}).items():
                cap[k] = cap.get(k, 0) + v
        report[shell]["capacity_N"] = cap
        report[shell]["capacity_N"]["y"] = min(cap.get("+y", 0), cap.get("-y", 0))
        report[shell]["capacity_N"]["z"] = min(cap.get("z_up", 0), cap.get("z_down", 0))
    # new middle parts, back in their STL frame
    for mid, sl in solids.items():
        k = idx[mid]
        base = S.mesh(k)
        new = trimesh.boolean.union([base] + sl, engine="manifold")
        new.apply_transform(np.linalg.inv(S.inst[k]["T"]))
        p = os.path.join(OUT, mid + "_lip.stl")
        new.export(p)
        sz = os.path.getsize(p)
        report.setdefault("files", {})
        report["files"][mid] = dict(path=p, bytes=sz, watertight=bool(new.is_watertight),
                                                     volume_added_mm3=round(float(new.volume - trimesh.load(os.path.join(LAB, "..", "print", mid + ".stl")).volume), 0))
        if sz < 5e6:
            new.export(os.path.join(GIT_STL, mid + "_lip.stl"))
    # coupons: K1 lip fit (a 40 mm slice of body_middle_bottom with a side lip + the matching slice of body_front),
    # K3 cable clip
    coup = {}
    def cut_pair(name, mid, cover, lo, hi):
        k = idx[mid]
        base = trimesh.boolean.union([S.mesh(k)] + solids[mid], engine="manifold")
        bx = trimesh.creation.box(bounds=[lo, hi])
        for nm, m in ((name + "a_" + mid, base), (name + "b_" + cover, covers.get(cover, S.mesh(idx[cover])))):
            c_ = trimesh.boolean.intersection([m, bx], engine="manifold")
            c_.export(os.path.join(OUT, nm + ".stl")); c_.export(os.path.join(GIT_STL, nm + ".stl"))
            coup[nm] = dict(volume_mm3=round(float(c_.volume), 0), box_world=[list(map(float, lo)), list(map(float, hi))])
    if "body_middle_top" in solids:     # K1: front tongue and groove, 30 mm of the top run
        bt = S.mesh(idx["body_middle_top"]).bounds
        cut_pair("K1", "body_middle_top", "body_front", np.array([36 - 8, -15, bt[1][2] - 14]), np.array([36 + 10.5, 15, bt[1][2] + 1]))
    if "body_middle_bottom" in solids:  # K2: back side lip and two ribs
        bb = S.mesh(idx["body_middle_bottom"]).bounds
        cut_pair("K2", "body_middle_bottom", "body_back", np.array([-114 - 12, bb[1][1] - 16, bb[0][2] - 1]), np.array([-114 + 8, bb[1][1] + 1, bb[0][2] + 30]))
    clip = clip_mesh()
    clip.export(os.path.join(OUT, "K3_cable_clip.stl"))
    clip.export(os.path.join(GIT_STL, "K3_cable_clip.stl"))
    coup["K3_cable_clip"] = dict(volume_mm3=round(float(clip.volume), 0), snap=clip_snap())
    report["coupons"] = coup
    report["design"] = dict(clearance_mm=C, lip_t_mm=T_LIP, lip_h_mm=H_LIP, rib=[RIB_W, RIB_T, RIB_PITCH], keep_out_r_mm=KEEP_OUT_R)
    json.dump(report, open(os.path.join(HERE, "data", "lips.json"), "w"), indent=1)
    print(json.dumps({s: report[s]["capacity_N"] for s in ("body_front", "body_back")}))
    print(json.dumps(report.get("files")), json.dumps(coup)[:600])


if __name__ == "__main__":
    main()
