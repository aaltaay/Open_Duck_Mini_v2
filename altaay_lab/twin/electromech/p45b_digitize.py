"""Digitize the Molicel INR-21700-P45B data sheet figure 'Discharge Rate Characteristics' (23 C).

Source: Molicel product data sheet INR-21700-P45B, version 1.2, the file PARTS_AUDIT.md cites:
https://www.molicel.com/wp-content/uploads/INR21700P45B_1.2_Product-Data-Sheet-of-INR-21700-P45B-80109.pdf
The figure is a raster on page 1. Axes read from that figure: voltage 2.5 to 4.5 V, capacity 0 to 5000 mAh.
Curves: 0.2C, 1.0C, 10 A, 20 A, 30 A, 45 A. The figure states charge CC-CV 4.5 A / 4.2 V (50 mA cut-off),
discharge CC to 2.5 V, ambient 23 C.

Method: render the page, find the five horizontal grid lines of the upper chart (4.5, 4.0, 3.5, 3.0, 2.5 V)
and the vertical grid (0, 1000, 2000, 3000, 4000, 5000 mAh), then track each curve by colour from a column
where the curves are apart. The text box in the lower left of the chart is masked. Resampled every 50 mAh.
This is a reading of the data sheet figure, not a measurement on a cell.

Usage: python3 p45b_digitize.py <P45B data sheet PDF> [out.json]   (needs pdftoppm from poppler-utils)
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "p45b_datasheet.json")
# 0.2C and 1.0C of the data sheet typical capacity 4500 mAh
CURRENTS = {"0.2C": 0.9, "1.0C": 4.5, "10A": 10.0, "20A": 20.0, "30A": 30.0, "45A": 45.0}
DPI = 200


def render(pdf, tmp):
    subprocess.run(["pdftoppm", "-png", "-r", str(DPI), "-f", "1", "-l", "1", pdf, os.path.join(tmp, "page")], check=True)
    return os.path.join(tmp, "page-1.png")


def _grid(a):
    """upper discharge chart: (y of 4.5..2.5 V), (x of 0..5000 mAh)"""
    R, G, B = a[:, :, 0].astype(int), a[:, :, 1].astype(int), a[:, :, 2].astype(int)
    gray = (np.abs(R - G) < 18) & (np.abs(G - B) < 18) & (R > 120) & (R < 220)
    dark = (R < 90) & (G < 90) & (B < 90)
    h, w = a.shape[:2]
    rows = []
    for y in range(int(h * 0.25), int(h * 0.70)):
        if gray[y, int(w * 0.55):int(w * 0.90)].sum() > 140 or dark[y, int(w * 0.55):int(w * 0.90)].sum() > 250:
            rows.append(y)
    groups = []
    for y in rows:
        if groups and y - groups[-1][-1] <= 3:
            groups[-1].append(y)
        else:
            groups.append([y])
    centers = [int(np.mean(g)) for g in groups if len(g) >= 1]
    # five lines, about 69 px apart at 200 dpi; extra text rules sit between them, so the five
    # are not five neighbours in the raw list
    best = None
    for i, yA in enumerate(centers):
        for step in range(60, 80):
            want = [yA + step * k for k in range(5)]
            got = []
            for w in want:
                near = [c for c in centers if abs(c - w) <= 3]
                if len(near) != 1:
                    got = None
                    break
                got.append(near[0])
            if got and (best is None or got[0] < best[0]):
                best = got
    if best is None:
        raise SystemExit("discharge chart grid rows not found: %s" % centers)
    cols = []
    y0, y1 = best[0], best[-1]
    for x in range(int(w * 0.45), int(w * 0.95)):
        if gray[y0:y1, x].sum() > 80 or dark[y0:y1, x].sum() > 120:
            cols.append(x)
    cgroups = []
    for x in cols:
        if cgroups and x - cgroups[-1][-1] <= 3:
            cgroups[-1].append(x)
        else:
            cgroups.append([x])
    xc = [int(np.mean(g)) for g in cgroups]
    # six lines, about 90 px apart; a tick or a label can sit between them
    bestc = None
    for xA in xc:
        for step in range(80, 105):
            want = [xA + step * k for k in range(6)]
            got = []
            for w in want:
                near = [c for c in xc if abs(c - w) <= 3]
                if len(near) != 1:
                    got = None
                    break
                got.append(near[0])
            if got and (bestc is None or got[0] < bestc[0]):
                bestc = got
    if bestc is None:
        raise SystemExit("discharge chart grid cols not found: %s" % xc)
    return best, bestc


def _ink(px):
    """colour family of one pixel, or None for paper and grid"""
    R, G, B = (int(v) for v in px)
    chroma = max(R, G, B) - min(R, G, B)
    if chroma < 18 and R > 140:
        return None
    if R > 160 and R > G + 45 and R > B + 35 and G < 170 and B < 180:
        return "1.0C"
    if G > 150 and B > 150 and R < 210 and min(G, B) > R + 20:
        return "20A"
    if R > 160 and B > 140 and G < 190 and R > G + 40 and B > G + 30 and abs(R - B) < 80:
        return "30A"
    if 70 < R < 200 and 60 < B < 210 and G + 18 < min(R, B) and abs(R - B) < 70 and not (R > 170 and B > 170):
        return "10A"
    if R > 80 and R > G > B and (R - B) > 28 and (G - B) > 10 and B < 160 and chroma > 22:
        return "45A"
    # the 0.2C line is a thin dark stroke, often one pixel and not pure black
    if R < 120 and G < 120 and B < 120 and chroma < 28 and R > 15:
        return "0.2C"
    return None


def _bands(col):
    """list of (y_centre, colour) for ink runs of at least 2 pixels"""
    out = []
    y = 0
    n = len(col)
    while y < n:
        kind = _ink(col[y])
        if kind is None:
            y += 1
            continue
        y1 = y + 1
        while y1 < n and _ink(col[y1]) == kind:
            y1 += 1
        if y1 - y >= 2 or kind == "0.2C":
            out.append((0.5 * (y + y1 - 1), kind))
        y = y1
    return out


def digitize(png):
    a = np.asarray(Image.open(png).convert("RGB"))
    ys, xs = _grid(a)
    kv = np.polyfit(ys, [4.5, 4.0, 3.5, 3.0, 2.5], 1)
    kq = np.polyfit(xs, [0.0, 1000, 2000, 3000, 4000, 5000], 1)
    # text box sits in the lower left of this chart (measured on the version 1.2 page at 200 dpi,
    # then stored as a fraction of the frame so a different render still masks it)
    top, bot, left, right = ys[0] + 2, ys[-1] - 1, xs[0] + 1, xs[-1] - 1
    box = (ys[0] + 0.78 * (ys[-1] - ys[0]), ys[-1] - 2, xs[0], xs[0] + 0.55 * (xs[-1] - xs[0]))
    names = list(CURRENTS)          # top curve to bottom curve: 0.2C, 1C, 10A, 20A, 30A, 45A
    # seed at 2000 mAh, where the six curves are apart and in that order
    x_seed = int(round(xs[0] + (xs[-1] - xs[0]) * (2000.0 / 5000.0)))

    def column(x):
        col = a[top:bot, x].copy()
        if box[2] <= x <= box[3]:
            yA = int(box[0]) - top
            yB = int(box[1]) - top
            col[max(0, yA):max(0, yB)] = (255, 255, 255)
        return col

    seed_bands = sorted(_bands(column(x_seed)))
    y_seed = []
    used = set()
    floor = -1.0
    for n in names:
        cands = [(j, yb) for j, (yb, kind) in enumerate(seed_bands) if kind == n and j not in used and yb > floor + 3]
        if not cands:
            raise SystemExit("seed column x=%d has no %s band below y %.0f; bands %s" % (x_seed, n, floor, seed_bands))
        j, yb = min(cands, key=lambda t: t[1])
        used.add(j)
        y_seed.append(float(yb))
        floor = yb
    if not all(y_seed[i] < y_seed[i + 1] - 4 for i in range(5)):
        raise SystemExit("seed curves are not in voltage order: %s" % list(zip(names, y_seed)))
    raw = {n: [] for n in names}
    last_y = list(y_seed)
    for n, yb in zip(names, y_seed):
        raw[n].append((float(np.polyval(kq, x_seed)), float(np.polyval(kv, top + yb))))
    grid_x = set()
    for gx in xs:
        grid_x.update(range(gx - 2, gx + 3))
    alive = [True] * 6
    miss = [0] * 6

    def step_to(x):
        if x in grid_x:
            return
        bands = _bands(column(x))
        q = float(np.polyval(kq, x))
        picked = [None] * 6
        used = set()
        for i, n in enumerate(names):
            if not alive[i]:
                continue
            best, bd = None, 1e9
            for j, (yb, kind) in enumerate(bands):
                if j in used or kind != n:
                    continue
                dist = abs(yb - last_y[i])
                if dist < bd:
                    best, bd = j, dist
            # the knee drops quickly; 14 px is about 0.20 V at this render
            if best is not None and bd <= 14:
                used.add(best)
                picked[i] = bands[best][0]
        for i, n in enumerate(names):
            if not alive[i]:
                continue
            if picked[i] is None:
                miss[i] += 1
                if miss[i] > 8:
                    alive[i] = False
                continue
            # do not cross a neighbour that was found on this column
            if i > 0 and picked[i - 1] is not None and picked[i] < picked[i - 1] + 2:
                miss[i] += 1
                continue
            if i < 5 and picked[i + 1] is not None and picked[i] > picked[i + 1] - 2:
                miss[i] += 1
                continue
            miss[i] = 0
            last_y[i] = picked[i]
            raw[n].append((q, float(np.polyval(kv, top + picked[i]))))

    x = x_seed
    while x < right and any(alive):
        x += 1
        step_to(x)
    last_y = list(y_seed)
    alive = [True] * 6
    miss = [0] * 6
    x = x_seed
    while x > left and any(alive):
        x -= 1
        step_to(x)
    grid = np.arange(0.0, 5001.0, 50.0)
    curves = {}
    for n, pts in raw.items():
        if len(pts) < 20:
            raise SystemExit("curve %s has only %d points" % (n, len(pts)))
        pts = sorted(pts)
        qq = np.array([p[0] for p in pts])
        vv = np.array([p[1] for p in pts])
        # one voltage per mAh column: median of pixels that landed in the same mAh
        order = np.argsort(qq)
        qq, vv = qq[order], vv[order]
        # drop the steep junk at the frame by keeping the longest decreasing run
        ok = np.ones(len(qq), bool)
        # resample: for each grid mAh, median of samples within 25 mAh
        volts = []
        for g in grid:
            m = np.abs(qq - g) <= 25.0
            volts.append(None if m.sum() < 1 else round(float(np.median(vv[m])), 4))
        # trim a leading hole and a trailing hole; do not fill across a long gap
        idx = [i for i, v in enumerate(volts) if v is not None]
        i0, i1 = idx[0], idx[-1]
        # interior holes of one sample: linear fill
        for i in range(i0, i1 + 1):
            if volts[i] is None:
                L = next(j for j in range(i - 1, -1, -1) if volts[j] is not None)
                R = next(j for j in range(i + 1, len(volts)) if volts[j] is not None)
                f = (i - L) / (R - L)
                volts[i] = round(volts[L] * (1 - f) + volts[R] * f, 4)
        end = float(grid[i1])
        curves[n] = dict(current_A=CURRENTS[n], volts=volts, end_mAh=end, n_pixels=len(pts))
    return dict(grid_y=ys, grid_x=xs, volts_per_px=float(kv[0]), mah_per_px=float(kq[0]),
                mAh=grid.round(1).tolist(), curves=curves)


def main():
    pdf = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else OUT
    sha = hashlib.sha256(open(pdf, "rb").read()).hexdigest()
    with tempfile.TemporaryDirectory() as tmp:
        png = render(pdf, tmp)
        d = digitize(png)
    doc = dict(
        source="Molicel INR-21700-P45B product data sheet version 1.2, figure 'Discharge Rate Characteristics', "
               "23 C ambient, charge CC-CV 4.5 A / 4.2 V (50 mA cut-off), discharge CC to 2.5 V; "
               "https://www.molicel.com/wp-content/uploads/INR21700P45B_1.2_Product-Data-Sheet-of-INR-21700-P45B-80109.pdf",
        pdf_sha256_16=sha[:16],
        datasheet_impedance={"AC_30pct_SOC_mOhm": 7, "DC_50pct_SOC_mOhm": 15},
        datasheet_capacity_mAh={"typical": 4500, "minimum": 4300},
        datasheet_voltage={"nominal_V": 3.6, "charge_V": 4.2, "discharge_cutoff_V": 2.5},
        datasheet_current_A={"charge_standard": 4.5, "charge_maximum": 13.5, "discharge_continuous": 45},
        datasheet_temperature_C={"charge": [0, 60], "discharge": [-40, 60],
                                 "charge_max_current_cutoff": 70, "discharge_continuous_cutoff": 80},
        datasheet_mass_g_max=70, datasheet_size_mm_max={"diameter": 21.55, "height": 70.15},
        discharge_cutoff_V=2.5,
        method="twin/electromech/p45b_digitize.py: 200 dpi render, grid of the Discharge Rate Characteristics chart, "
               "colour tracking, 50 mAh resampling. 0.2C is 0.9 A and 1.0C is 4.5 A from the typical capacity 4500 mAh.",
        cal=dict(volts_per_px=d["volts_per_px"], mah_per_px=d["mah_per_px"], grid_rows=d["grid_y"], grid_cols=d["grid_x"]),
        mAh=d["mAh"],
        curves={n: dict(current_A=c["current_A"], end_mAh=c["end_mAh"], n_pixels=c["n_pixels"], volts=c["volts"])
                for n, c in d["curves"].items()},
    )
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(doc, open(out, "w"), indent=1)
    print("wrote", out)
    for n, c in doc["curves"].items():
        vv = [v for v in c["volts"] if v is not None]
        print("%-5s end %6.0f mAh  V0 %.3f  Vend %.3f  pixels %d" % (n, c["end_mAh"], vv[0], vv[-1], c["n_pixels"]))


if __name__ == "__main__":
    main()
