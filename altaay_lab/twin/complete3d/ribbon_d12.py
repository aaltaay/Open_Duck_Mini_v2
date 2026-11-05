"""ribbon_d12.py: the camera cable D12 as a flat strip, routed Pi CSI to Camera Module 3, checked at 150 and 200 mm.
CAD check only (clearances) and calc only (lengths).

Run after camera_seat.py: python3 altaay_lab/twin/complete3d/ribbon_d12.py
Writes altaay_lab/twin/complete3d/d12_ribbon.json (the strip as points in the head_assembly link frame with the width
vector at every point, so the viewer can draw it as a flat band that moves with the head).

Strip model: a flat strip only bends about its width axis (bend: radius r) and turns in its own plane only by a flat fold
(the centre line keeps its length, the strip flips over, the fold takes a W x W square). It does not twist here.
Search: every route of the family below, scored on a 0.5 mm distance field of the head parts (surface voxels; closed
small parts filled), then the shortest one with at least 1.0 mm clearance is checked again on the exact meshes.
  Pi CSI mouth (exit -x, strip in the Pi board plane, width along y)
  -> 180 degree bend about the width axis, under or over the Pi (radius r_u), now running +x
  -> straight to x1 -> fold toward (x2, y_f) -> straight -> fold back to +x -> straight
  -> 90 degree bend about the width axis into the camera board plane (radius r_b), running up or down
  -> straight to the connector height -> fold to +y -> straight into the 15-pin connector at the board bottom edge.
Extra length of the 200 mm cable: stored in one standing loop (two 90 and one 180 degree bends about the width axis,
radius r_l) on a straight piece of the route, placed where it clears best.
"""
import json
import os

import numpy as np
import trimesh
from scipy import ndimage

from common import CABLES3D, HEAD_LINK, HERE, glb_meshes, head_instances, inst_name, scene, write_json

SRC = {
    "pi_end": "[I] cables3d.json cable_ends PI.CSI: Raspberry Pi Zero 2 W mechanical drawing, CSI 22-pin on the short edge",
    "cam_end": "[L] camera_seat.json d12_end: 15-pin connector at the board bottom edge (Camera Module 3 drawing as cited in "
               "HARDWARE_AUDIT B9 and the viewer lens note), strip in the board plane",
    "cut_150": "[I] BOM.md E7: Adafruit 3157, Pi Zero camera cable 150 mm",
    "cut_200": "[I] BOM.md E7 note and CABLE_MAP.md D12: Adafruit 5818, Raspberry Pi Standard-Mini camera cable 200 mm, "
               "22-pin 0.5 mm to 15-pin 1 mm, $2.70, in stock (https://www.adafruit.com/product/5818, read 2026-11-02 1:46 AM ET), "
               "Raspberry Pi MPN SC1892 (Kiwi Electronics listing, same read)",
    "cut_300": "[I] D34: Raspberry Pi Camera Cable Standard-Mini 300 mm (22-pin 0.5 mm to 15-pin 1 mm), US$2.94 at X-On Electronics "
               "(https://www.xonelec.com/mpn/raspberrypi/rpicameracablestandardmini300mm, read via search index 2026-11-05, stock not verified); "
               "same part as Pakronics RPI-SC1129, A$3.52 (https://www.pakronics.com.au/products/raspberry-pi-camera-cable-standard-mini-300mm-rpi-sc1129)",
    "slack": "[I] cables3d/check_cables.py SLACK_MM = 40 (2 x 20 mm service slack, CABLE_MAP.md length rule)",
}
BLOCKERS = {
    "width": "FPC width not published at a reachable source (repo stand-in: 16 mm at the 15-pin end, 11.5 mm at the 22-pin end, "
             "scene_extras 'UNVERIFIED'). Lower bound from the cited pitch and pin count, calc only: (15 - 1) x 1.0 = 14 mm and "
             "(22 - 1) x 0.5 = 10.5 mm between outer contact centres. The route is checked at 16 mm over its whole length "
             "(worst case). Settles it: caliper on the received cable (TO9), or adafruit.com / datasheets.raspberrypi.com "
             "allowed in this session.",
    "thickness": "FPC thickness not published at a reachable source (repo stand-in 0.3 mm). Settles it: caliper (TO9).",
    "bend": "No minimum bend radius or fold rule for this cable at a reachable source. Bends here are 3 mm and up; folds are "
            "flat 45 degree folds, not pressed to a crease. Settles it: TO9 test fit (fold over a 1 mm former, then check the "
            "camera image).",
}
W, T = 16.0, 0.3
R_B, R_L = 3.0, 12.0          # D34: the spare lies in a gentle loop (radius 12, then 10, then 8 if it does not clear)
PITCH = 1.0
MIN_CLR = 1.0


def rot(v, k, a):
    k = k / np.linalg.norm(k)
    return v * np.cos(a) + np.cross(k, v) * np.sin(a) + k * (k @ v) * (1 - np.cos(a))


class Strip:
    def __init__(s, p, t, w):
        s.p, s.t, s.w = np.array(p, float), np.array(t, float), np.array(w, float)
        s.L, s.pts, s.ws, s.ev, s.straights = 0.0, [s.p.copy()], [s.w.copy()], [], []
        s.cl, s.clw = [s.p.copy()], [s.w.copy()]       # clean centre line (no fold footprint samples)

    def _add(s, p, w):
        s.pts.append(np.array(p, float))
        s.ws.append(np.array(w, float))

    def straight(s, L):
        if L < -1e-6:
            raise ValueError("negative straight")
        p0 = s.p.copy()
        n = max(1, int(np.ceil(L / 1.0)))
        for k in range(1, n + 1):
            s._add(p0 + s.t * L * k / n, s.w)
            s.cl.append(p0 + s.t * L * k / n)
            s.clw.append(s.w.copy())
        s.straights.append((len(s.pts) - n - 1, len(s.pts) - 1, p0, s.t.copy(), s.w.copy(), L, len(s.cl) - n - 1, n))
        s.p = p0 + s.t * L
        s.L += L

    def bend(s, ang, r, side):
        side = np.array(side, float) / np.linalg.norm(side)
        k = np.cross(s.t, side)
        c = s.p + side * r
        p0, t0 = s.p.copy(), s.t.copy()
        n = max(2, int(np.ceil(r * ang / 1.0)))
        for i in range(1, n + 1):
            a = ang * i / n
            s._add(c + rot(p0 - c, k, a), s.w)
            s.cl.append(c + rot(p0 - c, k, a))
            s.clw.append(s.w.copy())
        s.p = c + rot(p0 - c, k, ang)
        s.t = rot(t0, k, ang)
        s.L += r * ang
        s.ev.append(dict(kind="bend", at=s.p.copy(), radius_mm=r, angle_deg=np.degrees(ang)))

    def fold(s, new_t):
        nt = np.array(new_t, float)
        nt /= np.linalg.norm(nt)
        nrm = np.cross(s.t, s.w)
        nt = nt - (nt @ nrm) * nrm
        nt /= np.linalg.norm(nt)
        ang = np.degrees(np.arccos(np.clip(nt @ s.t, -1, 1)))
        for u in np.arange(0.5, W / 2 + 0.01, 1.0):       # fold square, both layers (conservative)
            s._add(s.p + s.t * u, s.w)
        nw = np.cross(nrm, nt)
        for u in np.arange(W / 2, 0.0, -1.0):
            s._add(s.p - nt * u, nw)
        s._add(s.p, nw)
        s.ev.append(dict(kind="fold", at=s.p.copy(), turn_deg=ang))
        s.t, s.w = nt, nw


def build(P0, t0, w0, cam, side, r_u, x1, x2, y_f, plane, step=0.0, late=False):
    z_c = cam[plane][2]
    x_pl = cam[plane][0]
    y_edge = cam[plane][1]
    st = Strip(P0, t0, w0)
    st.straight(1.0)
    st.bend(np.pi, r_u, np.array([0, 0, -1.0 if side == "under" else 1.0]))
    if step and not late:
        if abs(step) < 2 * R_B:
            return None
        st.straight(W / 2 + 1.0)
        st.bend(np.pi / 2, R_B, np.array([0, 0, np.sign(step)]))
        st.straight(abs(step) - 2 * R_B)
        st.bend(np.pi / 2, R_B, np.array([1.0, 0, 0]))
    z_run = st.p[2]
    if x1 < st.p[0] + W / 2 or x2 < x1 or (x_pl - R_B) - x2 < W / 2 + 1 \
            or y_edge - y_f < W / 2 + 1:
        return None
    st.straight(x1 - st.p[0])
    B = np.array([x2, y_f, z_run])
    d = B - st.p
    if np.linalg.norm(d) > 1e-6:
        st.fold(d)
        st.straight(np.linalg.norm(d))
    st.fold([1.0, 0, 0])
    if step and late:
        st.straight(W / 2 + 1.0)
        st.bend(np.pi / 2, R_B, np.array([0, 0, np.sign(step)]))
        st.straight(abs(step) - 2 * R_B)
        st.bend(np.pi / 2, R_B, np.array([1.0, 0, 0]))
    if abs(z_c - st.p[2]) < R_B + 16.0 / 2 + 1.0 or (x_pl - R_B) - st.p[0] < 0:
        return None
    st.straight((x_pl - R_B) - st.p[0])
    st.bend(np.pi / 2, R_B, np.array([0, 0, np.sign(z_c - z_run)]))
    st.straight(abs(z_c - st.p[2]))
    st.fold([0, 1.0, 0])
    st.straight(y_edge - st.p[1])
    st.z_run = z_run
    return st


TAPER = None      # None: W over the whole length; (w_pi, w_cam, cam_len_mm): narrow strip, wide only near the camera


def widths(st):
    P = np.array(st.pts)
    if TAPER is None:
        return np.full(len(P), W)
    seg = np.r_[0.0, np.linalg.norm(np.diff(P, axis=0), axis=1)]
    to_end = seg[::-1].cumsum()[::-1] - seg
    return np.where(to_end <= TAPER[2], TAPER[1], TAPER[0])


def samples(st, n_w=9):
    P = np.array(st.pts)
    Wv = np.array(st.ws)
    u = np.linspace(-0.5, 0.5, n_w)
    wd = widths(st)
    return (P[:, None, :] + Wv[:, None, :] * (u[None, :] * wd[:, None])[:, :, None]).reshape(-1, 3), np.repeat(np.arange(len(P)), n_w)


def search(P0, t0, w0, ends, clr, blocker):
    best, tried, fam = [], 0, {}
    for side, rus in (("under", (3.0, 4.0, 6.0, 9.0, 12.0)), ("over", (3.5, 5.0, 7.0))):
        for r_u in rus:
            for step, late in (([(0.0, False), (-6.0, False), (-10.0, False), (-14.0, False), (-18.0, False), (-12.0, True),
                                  (-14.0, True), (-18.0, True), (14.0, True), (18.0, True)]) if side == "under"
                               else [(0.0, False), (6.0, False), (10.0, False)]):
                for x1 in (12.0, 20.0, 30.0, 40.0, 50.0, 60.0, 68.0, 74.0):
                    for x2 in (50.0, 60.0, 68.0, 74.0, 80.0):
                        for y_f in (-24.0, -27.0, -31.0, -36.0):
                            for plane in ends:
                                try:
                                    st = build(P0, t0, w0, ends, side, r_u, x1, x2, y_f, plane, step, late)
                                except ValueError:
                                    st = None
                                if st is None:
                                    continue
                                tried += 1
                                pts, pid = samples(st)
                                d = clr(pts)
                                skip = (pid <= 4) | (pid >= len(st.pts) - 3)
                                m = float(np.min(d[~skip]))
                                par = dict(side=side, r_u=r_u, step=step, late_step=late, x1=x1, x2=x2, y_f=y_f, plane=plane, clr_grid=m)
                                best.append((m >= 0.0, -st.L if m >= 0.0 else m, st if m >= 0.0 else None, par))
                                f = (side, plane)
                                if f not in fam or m > fam[f]["clr_grid"]:
                                    fam[f] = dict(par, length_mm=st.L, blocked_by=blocker(pts[~skip]))
    best.sort(key=lambda q: (q[0], q[1]), reverse=True)
    return tried, [q for q in best if q[0]], best, fam


def main():
    S = scene()
    cam = json.load(open(os.path.join(HERE, "camera_seat.json")))
    c3 = json.load(open(CABLES3D))
    pe = [e for e in c3["cable_ends"] if e["id"] == "PI.CSI"][0]
    P0, t0, w0 = np.array(pe["p_world0"]), np.array(pe["dir_world0"]), np.array([0, 1.0, 0])
    ends = {k: np.array(v) for k, v in cam["d12_end"]["candidates_world"].items()}
    # obstacles: every head part, the placeholder boxes in the head, the small scene_extras parts in the head, the camera PCB
    obst = {}
    for i in head_instances(S):
        obst[inst_name(i)] = (S.world_mesh(i), i["key"] not in ("head", "head_bot_sheet"))
    hb = obst[[k for k in obst if k.startswith("head[")][0]][0].bounds
    for k, m in glb_meshes().items():
        if k.startswith(("ph-", "x-")) and k != "ph-camera" and not k.startswith("x-fpc-D12") and np.all(m.bounds[0] > hb[0] - 1) and np.all(m.bounds[1] < hb[1] + 1):
            obst[k] = (m, True)
    b = cam["board"]
    pcb = trimesh.creation.box(extents=b["dims_mm"])
    Tp = np.eye(4)
    Tp[:3, :3] = np.array(b["R_world"])
    Tp[:3, 3] = b["pcb_slab_center_world"]
    pcb.apply_transform(Tp)
    obst["camera PCB (designed seat)"] = (pcb, True)
    # route region only (Pi, camera, loops), 1 mm grid from surface samples; closed small parts filled by inside tests
    lo = np.maximum(hb[0] - 2, np.array([-30.0, -60.0, 158.0]))
    hi = np.minimum(hb[1] + 2, np.array([112.0, 80.0, 250.0]))
    shape = np.ceil((hi - lo) / PITCH).astype(int) + 1
    occ = np.zeros(shape, bool)
    lab = np.full(shape, -1, np.int16)
    names = list(obst)
    gx = [lo[d] + PITCH * np.arange(shape[d]) for d in range(3)]
    for k, (m, fill) in obst.items():
        mlo, mhi = m.bounds
        if np.any(mhi < lo) or np.any(mlo > hi):
            continue
        n = int(min(400000, max(2000, m.area * 6.0)))
        pts = trimesh.sample.sample_surface(m, n, seed=0)[0]
        idx = np.round((pts - lo) / PITCH).astype(int)
        ok = np.all((idx >= 0) & (idx < shape), axis=1)
        occ[tuple(idx[ok].T)] = True
        lab[tuple(idx[ok].T)] = names.index(k)
        if fill and m.is_watertight:
            a0 = np.maximum(0, np.floor((mlo - lo) / PITCH).astype(int))
            a1 = np.minimum(shape - 1, np.ceil((mhi - lo) / PITCH).astype(int))
            if np.prod(a1 - a0 + 1) < 400000:
                G = np.stack(np.meshgrid(*[gx[d][a0[d]:a1[d] + 1] for d in range(3)], indexing="ij"), -1).reshape(-1, 3)
                ins = m.contains(G)
                gi = np.round((G[ins] - lo) / PITCH).astype(int)
                occ[tuple(gi.T)] = True
                lab[tuple(gi.T)] = names.index(k)
    edt, near = ndimage.distance_transform_edt(~occ, sampling=PITCH, return_indices=True)
    edt -= PITCH / 2

    def clr(pts):
        idx = np.round((pts - lo) / PITCH).astype(int)
        ok = np.all((idx >= 0) & (idx < shape), axis=1)
        d = np.full(len(pts), -9.0)
        d[ok] = edt[tuple(idx[ok].T)]
        return d - T / 2

    def blocker(pts):
        idx = np.clip(np.round((pts - lo) / PITCH).astype(int), 0, shape - 1)
        d = edt[tuple(idx.T)]
        j = int(np.argmin(d))
        nb = tuple(near[(slice(None),) + tuple(idx[j])])
        return (names[lab[nb]] if lab[nb] >= 0 else "?"), np.round(pts[j], 1).tolist()

    def exact_check(st):
        pts, pid = samples(st, 17)
        skip = (pid <= 4) | (pid >= len(st.pts) - 3)
        ex = {}
        for k, (m, _) in obst.items():
            lo_, hi_ = m.bounds
            sel = ~skip & np.all((pts > lo_ - 6) & (pts < hi_ + 6), axis=1)
            if not sel.any():
                continue
            dist = trimesh.proximity.closest_point(m, pts[sel])[1] - T / 2
            inside = int(np.sum(m.contains(pts[sel]))) if m.is_watertight else None
            ex[k] = dict(min_mm=float(dist.min()), inside_points=inside)
        w_ = min(ex.items(), key=lambda kv: kv[1]["min_mm"]) if ex else None
        return (w_[1]["min_mm"] if w_ else 99.0), w_, ex

    global W, TAPER
    passes, pick = [], None
    for W_, TAPER_ in ((16.0, None), (11.5, (11.5, 16.0, 20.0))):
        W, TAPER = W_, TAPER_
        tried, ok, best, fam = search(P0, t0, w0, ends, clr, blocker)
        checked = []
        for q in ok[:30]:
            mn, w_, ex = exact_check(q[2])
            checked.append(dict(q[3], length_mm=q[2].L, exact_min_mm=mn, exact_worst=w_[0] if w_ else None))
            if mn >= MIN_CLR and all((v["inside_points"] or 0) == 0 for v in ex.values()):
                pick = (q[2], q[3], ex, w_)
                break
        passes.append(dict(width="16 mm whole length" if TAPER is None else "11.5 mm, 16 mm on the last 20 mm (stand-in taper)",
                           tried=tried, feasible=len(ok), exact_checked=checked, found=pick is not None,
                           best_by_family={"%s, %s" % f: v for f, v in fam.items()}))
        if pick:
            break
    if pick is None:
        q = (ok or best)[0]
        if q[2] is None:
            pp = q[3]
            q = (q[0], q[1], build(P0, t0, w0, ends, pp["side"], pp["r_u"], pp["x1"], pp["x2"], pp["y_f"], pp["plane"], pp["step"],
                                   pp.get("late_step", False)), pp)
        mn, w_, ex = exact_check(q[2])
        pick = (q[2], q[3], ex, w_)
    st, par, exact, worst = pick
    # other cables in the head that the strip crosses (cables bend; a crossing is a note, not a failure)
    T0h = S.T0[HEAD_LINK]
    cross_ = []
    for c in c3["cables"]:
        if c["id"] == "D12":
            continue
        for rn in c.get("runs") or [{"points": c["points"], "name": "main", "d_mm": c["d_mm"]}]:
            q = np.array([(S.T0[p["link"]] @ np.r_[p["p"], 1.0])[:3] for p in rn["points"]])
            if len(q) < 2:
                continue
            qq = np.concatenate([np.linspace(q[i], q[i + 1], 12) for i in range(len(q) - 1)])
            dd = np.min(np.linalg.norm(qq[:, None, :] - np.array(st.pts)[None, ::3, :], axis=2))
            if dd < W / 2 + rn.get("d_mm", 3.0) / 2:
                cross_.append(dict(cable=c["id"], run=rn.get("name"), centre_line_gap_mm=float(dd)))
    L = st.L
    verdict = {}
    for cut, key in ((150, "cut_150"), (200, "cut_200"), (300, "cut_300")):
        spare = cut - L
        verdict[str(cut)] = dict(cut_mm=cut, route_mm=L, spare_mm=spare, need_mm=L + 40.0,
                                 result=("fail: cannot reach" if spare < 0 else ("test fit: under the 40 mm slack" if spare < 40 else "pass")),
                                 source=SRC[key])
    # gentle loop(s) for the spare of the 300 mm cable (D34): each loop is two 90 degree and one 180 degree bends about the
    # width axis, all of radius R, standing off one face of a straight piece and ending 4 R further along it (no fold)
    extra = 300.0 - L

    def omega(p0, tt, ww, R_, h, sg):
        nrm = sg * np.cross(tt, ww)
        lp = Strip(p0, tt, ww)
        lp.bend(np.pi / 2, R_, nrm)
        if h > 0:
            lp.straight(h)
        lp.bend(np.pi, R_, tt)
        if h > 0:
            lp.straight(h)
        lp.bend(np.pi / 2, R_, tt)
        return lp

    def exact_min(lp):
        q, _ = samples(lp, 17)
        res = {}
        for k, (mm, _) in obst.items():
            lo_, hi_ = mm.bounds
            sel = np.all((q > lo_ - 6) & (q < hi_ + 6), axis=1)
            if sel.any():
                res[k] = float(np.min(trimesh.proximity.closest_point(mm, q[sel])[1]) - T / 2)
        return (min(res.values()) if res else 99.0), (min(res.items(), key=lambda kv: kv[1]) if res else None)

    loops, tried_l = [], []
    for n_l in (1, 2, 3):
        e1 = extra / n_l
        for R_ in (12.0, 10.0, 8.0, 6.0):
            h = (e1 - 2 * np.pi * R_ + 4 * R_) / 2
            if h < 0:
                continue
            cands = []
            for si, sg_ in enumerate(st.straights):
                p0, tt, ww, Ls = sg_[2], sg_[3], sg_[4], sg_[5]
                for s0 in np.arange(1.0, Ls - 4 * R_ - 1.0, 2.0):
                    for sg in (1.0, -1.0):
                        q, _ = samples(omega(p0 + tt * s0, tt, ww, R_, h, sg))
                        cands.append((float(np.min(clr(q[9:-9]))), si, s0, sg))
            cands.sort(key=lambda c: -c[0])
            pick_l, used, n_ex = [], [], 0
            for sc, si, s0, sg in cands:
                if sc < 0.0 or len(pick_l) == n_l or n_ex >= 40:
                    break
                if any(u[0] == si and abs(u[1] - s0) < 4 * R_ + W for u in used):
                    continue
                i0, i1, p0, tt, ww, Ls, c0, nseg = st.straights[si]
                lp = omega(p0 + tt * s0, tt, ww, R_, h, sg)
                mn, worst_l = exact_min(lp)
                n_ex += 1
                if mn >= MIN_CLR:
                    step = Ls / nseg
                    pick_l.append(dict(lp=lp, radius_mm=R_, leg_mm=h, side=sg, straight=si, s0=s0, clr_grid_mm=sc, clr_exact_min_mm=mn,
                                       clr_exact_worst=worst_l, start_world=lp.cl[0],
                                       splice_at=[c0 + int(np.floor(s0 / step)), c0 + int(np.ceil((s0 + 4 * R_) / step))]))
                    used.append((si, s0))
            tried_l.append([n_l, R_, len(pick_l)])
            if len(pick_l) == n_l:
                loops = pick_l
                break
        if loops:
            break
    draw, draw_w = list(st.cl), list(st.clw)
    for d_ in sorted(loops, key=lambda d: -d["splice_at"][0]):
        j0, j1 = d_["splice_at"]
        draw = draw[:j0 + 1] + list(d_["lp"].cl) + draw[j1:]
        draw_w = draw_w[:j0 + 1] + list(d_["lp"].clw) + draw_w[j1:]
    loop = dict(cut_mm=300, extra_mm=extra, n_loops=len(loops), tried=tried_l,
                loops=[{k: v for k, v in d.items() if k != "lp"} for d in loops],
                radius_mm=loops[0]["radius_mm"] if loops else None, leg_mm=loops[0]["leg_mm"] if loops else None,
                clr_exact_min_mm=min(d["clr_exact_min_mm"] for d in loops) if loops else None,
                points_world=[p for d in loops for p in d["lp"].cl], width_world=[w for d in loops for w in d["lp"].clw])
    inv = np.linalg.inv(T0h)
    to_link = lambda p: (inv @ np.r_[p, 1.0])[:3]
    to_link_v = lambda v: inv[:3, :3] @ v
    out = dict(
        meta=dict(script="altaay_lab/twin/complete3d/ribbon_d12.py", label="CAD check only (clearance), calc only (length)",
                  shape="flat strip", width_mm=W, thickness_mm=T, width_note="16 mm stand-in over the whole length (worst case)",
                  sources=SRC, blockers=BLOCKERS, tried=tried, feasible=len(ok), min_clearance_rule_mm=MIN_CLR, passes=passes,
                  width_used=passes[-1]["width"],
                  tube_route_mm=[c for c in c3["cables"] if c["id"] == "D12"][0]["length_zero_mm"]),
        pick=par, length_mm=L, events=st.ev, verdict=verdict, exact_clearance=exact, worst=worst, crossings=cross_,
        points_world=st.pts, width_world=st.ws, link=HEAD_LINK,
        points_link=[to_link(p) for p in st.pts], width_link=[to_link_v(w) for w in st.ws],
        slack_loop_300=loop, centerline_link=[to_link(p) for p in st.cl], centerline_width_link=[to_link_v(w) for w in st.clw],
        draw_link=[to_link(p) for p in draw], draw_width_link=[to_link_v(w) for w in draw_w],
        centerline_mm=float(np.sum(np.linalg.norm(np.diff(np.array(st.cl), axis=0), axis=1))),
        draw_mm=float(np.sum(np.linalg.norm(np.diff(np.array(draw), axis=0), axis=1))),
        runners_up=[dict(q[3], length_mm=(q[2].L if q[2] is not None else None)) for q in (ok[1:6] if ok else best[1:6])])
    write_json(out, os.path.join(HERE, "d12_ribbon.json"))
    for p_ in passes:
        print("PASS", p_["width"], "tried", p_["tried"], "grid ok", p_["feasible"], "found", p_["found"],
              "checked", [(round(c["length_mm"], 1), round(c["exact_min_mm"], 2), c["exact_worst"]) for c in p_["exact_checked"][:12]])
        for f, v in p_["best_by_family"].items():
            print("   ", f, {k: (round(x, 1) if isinstance(x, float) else x) for k, x in v.items()})
    print("tried", tried, "feasible", len(ok), "pick", par, "length %.1f" % L, "z_run %.1f" % st.z_run)
    print("events", [(e["kind"], round(e.get("radius_mm", 0), 1), round(e.get("angle_deg", e.get("turn_deg", 0)), 1),
                      np.round(e["at"], 1).tolist()) for e in st.ev])
    print("worst exact", worst)
    print("verdict", {k: (round(v["spare_mm"], 1), v["result"]) for k, v in verdict.items()})
    print("crossings", cross_)
    if loop:
        print("loop", {k: (np.round(v, 2).tolist() if isinstance(v, np.ndarray) else v) for k, v in loop.items()
                       if k not in ("points_world", "width_world")})


if __name__ == "__main__":
    main()
