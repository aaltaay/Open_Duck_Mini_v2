"""Digitize the Molicel INR-18650-P30B data sheet figure 'Discharge Rate Characteristics' (23 C) into
twin/electromech/data/p30b_datasheet.json (sim pass only; the data sheet is the source, this is a reading of it).

Source: Molicel Product Data Sheet INR-18650-P30B, Version 1.0, the link sim/runtime_thermal.py cites:
https://cdn.shopify.com/s/files/1/0481/9678/0183/files/Product-Data-Sheet-of-INR-18650-P30B-80111-2.pdf
(read 2026-11-03; sha256 of the PDF starts 9d5dd80c32f2dc73). The figure is an embedded 601 x 420 px JPEG
(pdfimages image 2). Curves: 0.2C (0.6 A), 0.5C (1.5 A), 1C (3 A), 10 A, 20 A (the 30 A curve ends at 3.0 V under
the 80 C cut-off and is not used). Charge CC/CV 3.0 A / 4.2 V (60 mA), discharge CC to 2.5 V, 23 C.

Method: axis calibration from the grid lines found in the image (rows of 4.0, 3.5 and 3.0 V; columns of 1000 and
2000 mAh); each curve by its colour, pixel column by pixel column, as the centre of the largest colour band; the
legend and the text box are masked; resampled every 25 mAh. The 0 mAh row comes from sim/runtime_thermal.py (the
18650batterystore.com digitization of the same figure) because the curves start under the frame line.
Check: the digitization is compared with the sim/runtime_thermal.py table at 500 to 2500 mAh (printed).

Usage: python3 p30b_digitize.py <P30B data sheet PDF> [out.json]   (needs pdfimages from poppler-utils)
"""
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "p30b_datasheet.json")
CURRENTS = {"0.6A (0.2C)": 0.6, "1.5A (0.5C)": 1.5, "3A (1C)": 3.0, "10A": 10.0, "20A": 20.0}
# sim/runtime_thermal.py P30B table (18650batterystore digitization of the same figure), for the 0 mAh row and the check
RT_Q = [0, 500, 1000, 1500, 2000, 2500]
RT = {0.6: [4.19, 4.01, 3.83, 3.67, 3.48, 3.18], 1.5: [4.18, 3.99, 3.81, 3.64, 3.46, 3.16], 3.0: [4.15, 3.95, 3.78, 3.60, 3.43, 3.13],
      10.0: [4.09, 3.83, 3.67, 3.51, 3.34, 3.07], 20.0: [3.99, 3.70, 3.57, 3.42, 3.26, 3.00]}


def figure_png(pdf, tmp):
    subprocess.run(["pdfimages", "-png", pdf, os.path.join(tmp, "img")], check=True)
    return os.path.join(tmp, "img-002.png")


def digitize(png):
    a = np.asarray(Image.open(png).convert("RGB")).astype(int)
    if a.shape[:2] != (420, 601):
        raise SystemExit("unexpected figure size %s (expected the 601 x 420 data sheet figure)" % (a.shape[:2],))
    R, G, B = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    grey = (np.abs(R - G) < 12) & (np.abs(G - B) < 12) & (a.sum(2) > 450) & (a.sum(2) < 705)
    rows = grey[50:349, 110:515].sum(1)
    cols = grey[50:349, 110:515].sum(0)
    grid_rows = [i + 50 for i in range(len(rows)) if rows[i] > 120]
    grid_cols = [j + 110 for j in range(len(cols)) if cols[j] > 100]
    if len(grid_rows) != 3 or len(grid_cols) != 2:
        raise SystemExit("grid lines not found: rows %s cols %s" % (grid_rows, grid_cols))
    kv = np.polyfit(grid_rows, [4.0, 3.5, 3.0], 1)
    kq = np.polyfit(grid_cols, [1000.0, 2000.0], 1)
    masks = {
        "0.6A (0.2C)": (R < 70) & (G < 70) & (B < 70) & (np.abs(R - B) < 25),
        "1.5A (0.5C)": (R > 150) & (G < 70) & (B < 70),
        "3A (1C)": (B > 170) & (R < 80) & (G < 80),
        "10A": (R > 190) & (G > 95) & (G < 175) & (B < 90),
        "20A": (G > 85) & (R < 60) & (B < 60),
    }
    top, bot, left, right = 49, 349, 109, 516
    grid = np.arange(0, 3001, 25.0)
    curves = {}
    for name, m in masks.items():
        m = m.copy()
        m[:top] = False; m[bot:] = False; m[:, :left] = False; m[:, right:] = False
        m[50:100, 330:516] = False                      # legend
        def bands(c):
            rr = np.where(m[:, c])[0]
            rr = rr[rr < 345]
            if not len(rr):
                return []
            gs = [g for g in np.split(rr, np.where(np.diff(rr) > 1)[0] + 1) if len(g) >= 2]
            if name.startswith("0.6A"):
                gs = [g for g in gs if not (250 <= g.mean() < 349 and c < 330)]   # text box (black letters)
            return gs
        # curve tracking: start at 1000 mAh (curves well apart, largest band), then walk left and right taking the band
        # nearest the linear prediction from the last two centres (at most 6 px off; the end-of-discharge drop is steep)
        c0 = int(round(grid_cols[0])) + 4
        while not bands(c0):
            c0 += 1
        start = max(bands(c0), key=len).mean()
        found = {c0: start}
        for step in (1, -1):
            hist = [start]
            c = c0 + step
            while left <= c < right:
                gs = bands(c)
                pred = hist[-1] + ((hist[-1] - hist[-2]) if len(hist) > 1 else 0.0)
                if gs:
                    g = min(gs, key=lambda x: abs(x.mean() - pred))
                    if abs(g.mean() - pred) <= 6 + 0.5 * abs(hist[-1] - (hist[-2] if len(hist) > 1 else hist[-1])):
                        found[c] = g.mean(); hist.append(g.mean())
                c += step
        pts = [(float(np.polyval(kq, c)), float(np.polyval(kv, r))) for c, r in sorted(found.items())]
        pts = np.array(sorted(pts))
        q, v = pts[:, 0], pts[:, 1]
        vv = np.interp(grid, q, v, left=np.nan, right=np.nan)
        vv[grid > q.max()] = np.nan
        curves[name] = dict(current_A=CURRENTS[name], volts=[None if np.isnan(x) else round(float(x), 4) for x in vv],
                            end_mAh=round(float(q.max()), 1), v_at_end=round(float(v[-1]), 3), n_columns=int(len(q)))
    for name, c in curves.items():                       # 0 mAh row from sim/runtime_thermal.py (see the docstring)
        c["volts"][0] = RT[c["current_A"]][0]
    return dict(cal=dict(volts_per_px=float(kv[0]), mah_per_px=float(kq[0]), grid_rows=grid_rows, grid_cols=grid_cols),
                mAh=grid.tolist(), curves=curves)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pdf = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else OUT
    import hashlib
    sha = hashlib.sha256(open(pdf, "rb").read()).hexdigest()[:16]
    with tempfile.TemporaryDirectory() as tmp:
        res = digitize(figure_png(pdf, tmp))
    res = dict(source="Molicel INR-18650-P30B Product Data Sheet v1.0, figure 'Discharge Rate Characteristics', 23 C ambient, charge "
                      "CC/CV 3.0 A / 4.2 V (60 mA), discharge CC to 2.5 V; "
                      "https://cdn.shopify.com/s/files/1/0481/9678/0183/files/Product-Data-Sheet-of-INR-18650-P30B-80111-2.pdf",
               pdf_sha256_16=sha, datasheet_impedance=dict(AC_30pct_SOC_mOhm=8, DC_50pct_SOC_mOhm=17),
               datasheet_capacity_mAh=dict(typical=3000, minimum=2900), discharge_cutoff_V=2.5,
               method="twin/electromech/p30b_digitize.py: colour bands per pixel column of the embedded 601 x 420 px figure, volts from "
                      "the 4.0/3.5/3.0 V grid rows, mAh from the 1000/2000 mAh grid columns, 25 mAh resampling; 0 mAh row from "
                      "sim/runtime_thermal.py", **res)
    worst = 0.0
    g = np.array(res["mAh"])
    for name, c in res["curves"].items():
        v = np.array([np.nan if x is None else x for x in c["volts"]])
        d = [v[g == q][0] - ref for q, ref in zip(RT_Q[1:], RT[c["current_A"]][1:])]
        worst = max(worst, max(abs(x) for x in d))
        print("%-12s end %6.1f mAh; minus sim/runtime_thermal.py at 500..2500 mAh: %s mV" % (name, c["end_mAh"], " ".join("%+.0f" % (1000 * x) for x in d)))
    res["check_vs_runtime_thermal_max_abs_mV"] = round(1000 * worst, 1)
    print("largest difference against sim/runtime_thermal.py: %.1f mV" % (1000 * worst))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(res, open(out, "w"), indent=1)
    print("wrote", out)


if __name__ == "__main__":
    main()
