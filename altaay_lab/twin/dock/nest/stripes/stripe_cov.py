#!/usr/bin/env python3
"""stripe_cov.py: does a duck sitting anywhere on an alternating-polarity mat always touch + and - ?  calc only.

Geometry taken from files (nothing invented):
  sole flat face 84.8 x 15.8 mm            print/foot_bottom_tpu.stl (measured in this study, STRIPE_MAT_STUDY.md 1.1)
  in the D59 sit the sole is rolled 8 deg  sit_soles.json (sim pass only): it rests on the INNER long edge of that face
  sole centres 201.7 mm apart in the sit   sit_soles.json; 184 to 185 mm standing tall; 178.7 mm walking (DEEP_ANALYSIS 2.1)
  stagger -2.0 to +3.2 mm in the sit       sit_soles.json; up to 52 mm at a walking stop (DEEP_ANALYSIS 2.2)
  sole yaw to the trunk -1.9 to +1.2 deg   sit_soles.json

Model: N contacts per foot on the inner edge line of each sole. A contact is a disc of radius RC (the touch patch plus
its position tolerance). It is MADE on a polarity only when the whole disc lies on one conductor. A disc can never touch
two conductors because every gap is wider than the disc (checked). A pose is POWERED when at least one contact is made
on + and one on - (both feet as one set). REDUNDANT: at least two on each. PER FOOT: each foot alone has + and -.

  python3 stripe_cov.py search     design search for the parallel stripes (stripe_search.json)
  python3 stripe_cov.py final      the chosen designs, all patterns: exhaustive grid and Monte Carlo (stripe_cov.json)
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FLAT_L, FLAT_W = 84.8, 15.8          # mm, the sole's flat face
SPAN = 76.0                          # mm, first to last contact centre (4.4 mm kept from each end of the flat face)
RC = 1.5                             # mm, contact disc radius (a 3 mm touch patch with its tolerance)
W_SIT, W_STAND, W_WALK = 201.7, 184.8, 178.7
RNG = np.random.default_rng(20261111)


# ------------------------------------------------------------------------------------------------- contacts
def layout(n, half_offset=True, span=SPAN):
    """along-foot positions (mm from the sole centre) of the n contacts of the left and the right foot.
    half_offset: the right foot's row is shifted by half a spacing against the left one (inside the same span)"""
    if isinstance(n, (list, tuple)):            # explicit positions (mm from the sole centre); the right foot is the
        L = np.array(n, float)                  # same row, or the row reversed heel to toe when half_offset is set
        R = -L[::-1] if half_offset else L
        return L, R, float(np.diff(L).min())
    s = span / (n - 1) if not half_offset else span / (n - 0.5)
    a = np.arange(n) * s
    if half_offset:
        L, R = a - span / 2, a + s / 2 - span / 2
    else:
        L = R = a - span / 2
    return L, R, s


def contacts(X, Y, psi, W, stag, dL, dR, aL, aR):
    """world x, y of every contact; arrays broadcast over the pose arrays. Returns (..., 2n) x and y, left foot first.
    Body frame: x forward, y left. psi: heading (rad) from the mat's x axis."""
    out_x, out_y = [], []
    for f, a, d in ((1, aL, dL), (-1, aR, dR)):
        cx = f * stag / 2.0
        cy = f * W / 2.0
        e = -f * FLAT_W / 2.0                       # the inner edge, toward the body centre line
        d = d[..., None]
        bx = cx[..., None] + a * np.cos(d) - e * np.sin(d)
        by = cy[..., None] + a * np.sin(d) + e * np.cos(d)
        c, s = np.cos(psi)[..., None], np.sin(psi)[..., None]
        out_x.append(X[..., None] + c * bx - s * by)
        out_y.append(Y[..., None] + s * bx + c * by)
    return np.concatenate(out_x, -1), np.concatenate(out_y, -1)


# ------------------------------------------------------------------------------------------------- patterns
# each returns +1 / -1 where a disc of radius RC centred at (x, y) lies wholly on that polarity, else 0
def _stripe1d(u, w, g):
    P = 2 * (w + g)
    t = np.mod(u, P)
    plus = (t >= RC) & (t <= w - RC)
    minus = (t >= w + g + RC) & (t <= 2 * w + g - RC)
    return plus.astype(np.int8) - minus.astype(np.int8)


def pat_stripes_par(x, y, w, g):
    """stripes run parallel to the wall (along y); x is the distance from the wall"""
    return _stripe1d(x, w, g)


def pat_stripes_perp(x, y, w, g):
    """stripes run away from the wall (along x)"""
    return _stripe1d(y, w, g)


def pat_checker(x, y, w, g):
    """square pads of side w, gap g, polarity by the parity of column + row"""
    P = w + g
    i, j = np.floor(x / P), np.floor(y / P)
    tx, ty = x - i * P, y - j * P
    inside = (tx >= RC) & (tx <= w - RC) & (ty >= RC) & (ty <= w - RC)
    par = np.mod(i + j, 2)
    return (inside * (1 - 2 * par)).astype(np.int8)


def pat_hex(x, y, w, g):
    """hexagonal pads, w across the flats, gap g, flat sides left and right; polarity alternates by row. A honeycomb
    cannot be 2-coloured so that every neighbour differs: here 4 of the 6 neighbours are of the other polarity."""
    a = w + g                                   # centre spacing in a row
    h = a * np.sqrt(3) / 2                      # row spacing
    j = np.round(y / h)
    best_d = np.full(np.shape(x), 1e9)
    best_j = np.zeros(np.shape(x))
    for dj in (-1, 0, 1):
        jj = j + dj
        off = np.where(np.mod(jj, 2) == 1, a / 2, 0.0)
        ii = np.round((x - off) / a)
        px, py = x - (ii * a + off), y - jj * h
        d = np.maximum(np.abs(px), np.maximum(np.abs(0.5 * px + np.sqrt(3) / 2 * py), np.abs(0.5 * px - np.sqrt(3) / 2 * py)))
        upd = d < best_d
        best_d = np.where(upd, d, best_d)
        best_j = np.where(upd, jj, best_j)
    inside = best_d <= w / 2 - RC
    return (inside * (1 - 2 * np.mod(best_j, 2))).astype(np.int8)


def pat_rings(x, y, w, g):
    """concentric rings about a point on the wall line at the middle of the mat (0, 0): polarity by radius"""
    return _stripe1d(np.hypot(x, y), w, g)


PATTERNS = dict(stripes_parallel_to_wall=pat_stripes_par, stripes_perpendicular_to_wall=pat_stripes_perp,
                checkerboard=pat_checker, hex_rows=pat_hex, concentric_rings=pat_rings)


# ------------------------------------------------------------------------------------------------- scoring
def score(pol, n):
    n = len(n) if isinstance(n, (list, tuple)) else n
    npl = (pol > 0).sum(-1)
    nmi = (pol < 0).sum(-1)
    L, R = pol[..., :n], pol[..., n:]
    per_foot = ((L > 0).any(-1) & (L < 0).any(-1)) & ((R > 0).any(-1) & (R < 0).any(-1))
    return dict(powered=(npl >= 1) & (nmi >= 1), redundant=(npl >= 2) & (nmi >= 2), per_foot=per_foot)


def sample_poses(m, yaw_max_deg, period, stance="sit", ring_area=None):
    """random poses. stance 'sit': the D59 sit ranges with +/-3 mm on the width; 'any': walking to sit width, stagger to
    +/-52 mm (a stop with one foot ahead)"""
    if ring_area is None:
        X, Y = RNG.uniform(0, period[0], m), RNG.uniform(0, period[1], m)
    else:
        X, Y = RNG.uniform(*ring_area[0], m), RNG.uniform(*ring_area[1], m)
    psi = np.radians(RNG.uniform(-yaw_max_deg, yaw_max_deg, m))
    if stance == "sit":
        W = RNG.uniform(W_SIT - 3, W_SIT + 3, m)
        stag = RNG.uniform(-5, 5, m)
    else:
        W = RNG.uniform(W_WALK - 3, W_SIT + 3, m)
        stag = RNG.uniform(-52, 52, m)
    dL, dR = np.radians(RNG.uniform(-2.5, 2.5, m)), np.radians(RNG.uniform(-2.5, 2.5, m))
    return X, Y, psi, W, stag, dL, dR


def mc_rigid(name, w, g, n, m, yaw):
    """the stiff worst case: only 2 of the contacts of each foot touch (a stiff row on a stiff mat rests on 2 points),
    which 2 is random. Fraction of poses still powered."""
    aL, aR, s = layout(n, False)
    k = len(aL)
    X, Y, psi, W, stag, dL, dR = sample_poses(m, yaw, period_of(name, w, g), "sit")
    x, y = contacts(X, Y, psi, W, stag, dL, dR, aL, aR)
    pol = PATTERNS[name](x, y, w, g).copy()
    for f in (0, 1):
        keep = np.argsort(RNG.random((m, k)), 1)[:, :2]
        mask = np.zeros((m, k), bool)
        np.put_along_axis(mask, keep, True, 1)
        pol[:, f * k:(f + 1) * k] *= mask
    return float(((pol > 0).any(1) & (pol < 0).any(1)).mean())


def period_of(name, w, g):
    P = 2 * (w + g)
    if name == "hex_rows":
        return (w + g, (w + g) * np.sqrt(3))
    return (P, P)


def mc(name, w, g, n, half, m, yaw, stance="sit"):
    aL, aR, s = layout(n, half)
    area = ((150.0, 330.0), (-200.0, 200.0)) if name == "concentric_rings" else None     # trunk positions on a 400 x 600 mat
    X, Y, psi, W, stag, dL, dR = sample_poses(m, yaw, period_of(name, w, g), stance, area)
    x, y = contacts(X, Y, psi, W, stag, dL, dR, aL, aR)
    sc = score(PATTERNS[name](x, y, w, g), n)
    return {k: float(v.mean()) for k, v in sc.items()}


def grid(name, w, g, n, half, W=W_SIT, stag=0.0, step=1.0, yaw_step=1.0):
    """exhaustive: every position on a 'step' mm grid over one pattern period and every heading on a yaw_step grid, at the
    nominal sit stance. Returns the fraction powered per heading and the whole boolean map."""
    aL, aR, s = layout(n, half)
    P = period_of(name, w, g)
    xs = np.arange(0, P[0], step)
    ys = np.arange(0, P[1], step) if name not in ("stripes_parallel_to_wall",) else np.array([0.0])
    if name == "stripes_perpendicular_to_wall":
        xs, ys = np.array([0.0]), np.arange(0, P[1], step)
    yaws = np.arange(-180, 180, yaw_step)
    res = {k: np.zeros(len(yaws)) for k in ("powered", "redundant", "per_foot")}
    maps = np.zeros((len(yaws), max(len(xs), len(ys))), bool)
    z = np.zeros(1)
    for iy, yw in enumerate(yaws):
        X, Y = np.meshgrid(xs, ys, indexing="ij")
        psi = np.full(X.shape, np.radians(yw))
        x, y = contacts(X, Y, psi, np.full(X.shape, W), np.full(X.shape, stag), np.zeros(X.shape), np.zeros(X.shape), aL, aR)
        sc = score(PATTERNS[name](x, y, w, g), n)
        for k in res:
            res[k][iy] = sc[k].mean()
        if min(len(xs), len(ys)) == 1:               # 1-D patterns: keep the whole heading x position map
            maps[iy] = sc["powered"].ravel()
    return yaws, res, maps


def band(yaws, v, lim):
    k = np.abs(yaws) <= lim
    return float(v[k].mean()), float(v[k].min())


# ------------------------------------------------------------------------------------------------- runs
def search():
    """parallel stripes: every (w, g, n, offset) on an exhaustive 0.5 mm x 2 deg grid, at 9 stances of the sit (width
    198.7, 201.7, 204.7 mm x stagger -5, 0, +5 mm). The numbers kept are the WORST stance, so a design cannot win by a
    lucky match of the stripe pitch to one stance width."""
    rows = []
    stances = [(W, st) for W in (W_SIT - 3, W_SIT, W_SIT + 3) for st in (-5.0, 0.0, 5.0)]
    for n in (3, 4, 5, 6):
        for half in (False, True):
            for g in (4, 5, 6, 8):
                for w in range(8, 42, 2):
                    R = [grid("stripes_parallel_to_wall", w, g, n, half, W=W, stag=st, step=0.5, yaw_step=2.0) for W, st in stances]
                    yaws = R[0][0]
                    res = {k: np.min([x[1][k] for x in R], 0) for k in ("powered", "redundant")}       # worst stance per heading
                    avg = {k: np.mean([x[1][k] for x in R], 0) for k in ("powered", "redundant")}
                    r = dict(n=n, half_offset=half, w=w, g=g, pitch=2 * (w + g), metal_frac=round(w / (w + g), 3))
                    for lim in (30, 45, 60, 180):
                        for k in ("powered", "redundant"):
                            r["%s_mean_%d" % (k, lim)] = round(band(yaws, avg[k], lim)[0], 5)
                    for k in ("powered", "redundant"):
                        full = 0
                        for lim in range(0, 91, 2):
                            if res[k][np.abs(yaws) <= lim].min() >= 1.0:
                                full = lim
                            else:
                                break
                        r["full_band_deg_" + k] = full
                    rows.append(r)
    rows.sort(key=lambda r: (-r["full_band_deg_redundant"], -r["full_band_deg_powered"], -r["powered_mean_180"], -r["w"]))
    json.dump(dict(label="calc only", note="parallel stripes, exhaustive 0.5 mm x 2 deg grid, worst of 9 sit stances (width 198.7 to 204.7, stagger -5 to +5); means are over the 9 stances",
                   rc_mm=RC, span_mm=SPAN, rows=rows), open(os.path.join(HERE, "stripe_search.json"), "w"), indent=1)
    for r in rows[:30]:
        print(r["n"], r["half_offset"], "w", r["w"], "g", r["g"], "band100 pow/red", r["full_band_deg_powered"], r["full_band_deg_redundant"],
              "all-yaw", r["powered_mean_180"], r["redundant_mean_180"], "60:", r["powered_mean_60"], r["redundant_mean_60"])


def final(designs, m=400000):
    out = dict(label="calc only", rc_mm=RC, span_mm=SPAN, flat_face_mm=[FLAT_L, FLAT_W],
               contact_rule="made only when the whole 3 mm disc is on one conductor; powered = at least one + and one -",
               designs=[])
    for d in designs:
        name, w, g, n, half = d["pattern"], d["w"], d["g"], d["n"], d["half_offset"]
        assert g > 2 * RC, "a contact could bridge the gap"
        aL, aR, s = layout(n, half)
        r = dict(d, min_spacing_mm=round(s, 2), left_mm=np.round(aL, 2).tolist(), right_mm=np.round(aR, 2).tolist())
        if name != "concentric_rings":
            step = 1.0 if name.startswith("stripes") else 2.0
            yaws, res, mp = grid(name, w, g, n, half, step=0.5 if name.startswith("stripes") else step, yaw_step=1.0)
            if d.get("save_map"):
                json.dump(dict(label="calc only", id=d["id"], note="powered (1) or not (0) per heading (rows, -180 to 179 deg, 0 = facing the room) and per position across one stripe period (columns, 0.5 mm steps); nominal sit stance",
                               period_mm=2 * (w + g), map=mp.astype(int).tolist()), open(os.path.join(HERE, "stripe_map_%s.json" % d["id"]), "w"))
            r["grid"] = dict(note="exhaustive, nominal sit stance (width 201.7 mm, stagger 0, sole yaw 0), 1 deg headings, positions over one period",
                             yaw_deg=yaws.tolist(), **{k: np.round(v, 5).tolist() for k, v in res.items()})
            for k in res:
                full = 0
                for lim in range(0, 181):
                    if res[k][np.abs(yaws) <= lim].min() >= 1.0:
                        full = lim
                    else:
                        break
                r["full_band_deg_" + k] = full
                for lim in (30, 60, 180):
                    r["grid_%s_%d" % (k, lim)] = round(band(yaws, res[k], lim)[0], 5)
        r["mc"] = {}
        for stance in ("sit", "any"):
            for yaw in (30, 45, 60, 75, 90, 180):
                r["mc"]["%s_yaw%d" % (stance, yaw)] = {k: round(v, 5) for k, v in mc(name, w, g, n, half, m, yaw, stance).items()}
        if d.get("save_map"):
            r["mc_two_random_contacts_per_foot"] = {"yaw%d" % yw: round(mc_rigid(name, w, g, n, m, yw), 5) for yw in (30, 60, 180)}
            print("    rigid 2 per foot", r["mc_two_random_contacts_per_foot"])
        out["designs"].append(r)
        print(d["id"], name, "w", w, "g", g, "n", n, "100% bands", r.get("full_band_deg_powered"), r.get("full_band_deg_redundant"))
        for k, v in r["mc"].items():
            print("    ", k, v)
    json.dump(out, open(os.path.join(HERE, "stripe_cov.json"), "w"), indent=1)


def search_rows(trials=400):
    """uneven contact rows: random 4- and 5-contact rows inside the 76 mm span (ends fixed, neighbours 8 mm or more
    apart), right foot = the same row reversed heel to toe, on parallel stripes w 20 to 30, g 5. Score: the widest
    heading band with 100 % redundant power at the worst of 3 sit widths, then the all-heading mean."""
    rng = np.random.default_rng(7)
    best = []
    for w in (20, 24, 26, 30):
        for n in (4, 5):
            for t in range(trials // 8):
                while True:
                    mid = np.sort(rng.uniform(-SPAN / 2 + 8, SPAN / 2 - 8, n - 2))
                    row = np.concatenate([[-SPAN / 2], mid, [SPAN / 2]])
                    if np.diff(row).min() >= 8:
                        break
                row = [round(float(v), 1) for v in row]
                for rev in (False, True):
                    R = [grid("stripes_parallel_to_wall", w, 5, row, rev, W=W, step=1.0, yaw_step=3.0) for W in (W_SIT - 3, W_SIT, W_SIT + 3)]
                    yaws = R[0][0]
                    r = dict(w=w, g=5, row=row, reversed_right=rev)
                    for k in ("powered", "redundant"):
                        worst = np.min([x[1][k] for x in R], 0)
                        full = 0
                        for lim in range(0, 91, 3):
                            if worst[np.abs(yaws) <= lim].min() >= 1.0:
                                full = lim
                            else:
                                break
                        r["full_band_deg_" + k] = full
                        r[k + "_mean_180"] = round(float(np.mean([x[1][k] for x in R])), 5)
                    best.append(r)
    best.sort(key=lambda r: (-r["full_band_deg_redundant"], -r["full_band_deg_powered"], -r["redundant_mean_180"]))
    json.dump(dict(label="calc only", note=search_rows.__doc__, rows=best[:60]), open(os.path.join(HERE, "stripe_search_rows.json"), "w"), indent=1)
    for r in best[:15]:
        print(r)
    for n in (4, 5):
        for w in (20, 24, 26, 30):
            c = [r for r in best if len(r["row"]) == n and r["w"] == w][0]
            print("best n", n, "w", w, c)


def twozone():
    """the hybrid: one + zone under the left foot and one - zone under the right foot, a dead gap between them along
    the mat's centre line (running away from the wall). All contacts of a foot are one net (an edge strip). OK when the
    left strip has 10 mm or more on + and none on -, and the right strip the mirror. Fore-aft position does not matter.
    Grid: lateral offset 1 mm, heading 1 deg, the sit widths 198.7, 201.7, 204.7 mm (worst kept), stagger 0."""
    a = np.arange(-SPAN / 2, SPAN / 2 + 0.01, 1.0)
    lat = np.arange(-130, 131, 1.0)
    yaws = np.arange(-90, 91, 1.0)
    out = dict(label="calc only", note=twozone.__doc__, cases=[])
    for gap in (30.0, 40.0, 50.0):
        ok_all = np.ones((len(yaws), len(lat)), bool)
        short_any = np.zeros((len(yaws), len(lat)), bool)
        for W in (W_SIT - 3, W_SIT, W_SIT + 3):
            Y, PSI = np.meshgrid(lat, np.radians(yaws))
            z = np.zeros(Y.shape)
            x, y = contacts(z, Y, PSI, np.full(Y.shape, W), z, z, z, a, a)
            n = len(a)
            yl, yr = y[..., :n], y[..., n:]
            on_p = lambda v: v >= gap / 2 + RC
            on_m = lambda v: v <= -gap / 2 - RC
            touch_p = lambda v: v > gap / 2 - RC
            touch_m = lambda v: v < -gap / 2 + RC
            short = (touch_p(yl).any(-1) & touch_m(yl).any(-1)) | (touch_p(yr).any(-1) & touch_m(yr).any(-1))
            ok = (on_p(yl).sum(-1) >= 10) & ~touch_m(yl).any(-1) & (on_m(yr).sum(-1) >= 10) & ~touch_p(yr).any(-1)
            ok_all &= ok
            short_any |= short
        c = dict(gap_mm=gap)
        i0 = int(np.where(lat == 0)[0][0])
        j0 = int(np.where(yaws == 0)[0][0])
        row = ok_all[j0]
        c["lateral_window_at_yaw0_mm"] = [float(lat[row].min()), float(lat[row].max())]
        col = ok_all[:, i0]
        c["yaw_window_centred_deg"] = [float(yaws[col].min()), float(yaws[col].max())]
        c["boxes"] = []
        for yl_ in (10, 20, 30, 40, 50, 60):
            sel = np.abs(yaws) <= yl_
            good = ok_all[sel].all(0)
            half = 0
            for h in range(0, 131):
                if good[np.abs(lat) <= h].all():
                    half = h
                else:
                    break
            c["boxes"].append(dict(yaw_pm_deg=yl_, lateral_pm_mm=half))
        c["foot_bridges_both_zones_possible"] = bool(short_any.any())
        out["cases"].append(c)
        print(c)
    json.dump(out, open(os.path.join(HERE, "twozone.json"), "w"), indent=1)


if __name__ == "__main__":
    if sys.argv[1] == "twozone":
        twozone()
    elif sys.argv[1] == "search":
        search()
    elif sys.argv[1] == "rows":
        search_rows()
    else:
        D = json.load(open(os.path.join(HERE, "designs.json")))
        final(D["designs"])
