#!/usr/bin/env python3
"""Pictures of every fastener on the assembly, coloured by spec (x-ray: screws drawn over the parts).

  python3 altaay_lab/fasteners/render_fasteners.py --scratch <folder outside the repo>

Writes altaay_lab/fasteners/fasteners_assembled.png (two views of the zero pose) and fasteners_exploded.png
(subassemblies pulled apart with the viewer's level-1 explode vectors, scaled 0.6). Each PNG is quantized to stay
under 500 kB. Reads fasteners.json; the parts come from fastlib.Scene (print/ STLs, URDF zero pose).
"""
import argparse
import json
import os
import sys
from collections import Counter

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fastlib  # noqa: E402

EXPLODE = {"head": (0, 0, 300), "neck": (0, 0, 165), "trunk": (0, 0, 0),
           "left_hip": (0, 75, -35), "left_bracket": (0, 120, -60), "left_thigh": (0, 165, -105),
           "left_shin": (0, 165, -175), "left_foot": (0, 165, -245),
           "right_hip": (0, -75, -35), "right_bracket": (0, -120, -60), "right_thigh": (0, -165, -105),
           "right_shin": (0, -165, -175), "right_foot": (0, -165, -245)}   # viewer/make_viewer_data.py SUBS
PART_COL = {"pla": (0.86, 0.83, 0.77), "tpu": (0.55, 0.75, 0.72), "servo": (0.42, 0.45, 0.50),
            "horn": (0.80, 0.80, 0.82), "elec": (0.55, 0.72, 0.50), "other": (0.75, 0.72, 0.68)}


def part_colour(i):
    n = i["name"]
    if n.startswith("wj-"):
        return PART_COL["servo"]
    if "palonier" in n:
        return PART_COL["horn"]
    if n in ("board", "raspberrypizerow", "bno055", "usb_c_charger", "power_switch", "bms"):
        return PART_COL["elec"]
    if i["printed"]:
        return PART_COL["tpu"] if "tpu" in n else PART_COL["pla"]
    return PART_COL["other"]


def view_basis(az, el):
    az, el = np.radians(az), np.radians(el)
    d = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])   # from target to eye
    up = np.array([0, 0, 1.0])
    x = np.cross(up, d)
    x /= np.linalg.norm(x)
    y = np.cross(d, x)
    return x, y, d


def draw(ax, S, recs, az, el, explode=0.0, title="", target_faces=60000, subs=None):
    from matplotlib.collections import PolyCollection, LineCollection
    import fast_simplification
    bx, by, bd = view_basis(az, el)
    light = bd * 0.6 + np.array([0.3, 0.2, 0.75])
    light /= np.linalg.norm(light)
    polys, cols, depth = [], [], []
    tot = sum(len(S.mesh(k).faces) for k in range(len(S.inst)))
    for k, i in enumerate(S.inst):
        m = S.mesh(k)
        off = np.array(EXPLODE.get(fastlib.LINK_SUB.get(i["link"], "trunk"), (0, 0, 0)), float) * explode
        v, f = np.asarray(m.vertices), np.asarray(m.faces)
        keep = max(200, int(len(f) * target_faces / tot))
        if len(f) > keep:
            v, f = fast_simplification.simplify(v, f, target_reduction=1 - keep / len(f))
        v = v + off
        tri = v[f]
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        nn = np.linalg.norm(n, axis=1)
        ok = nn > 1e-9
        tri, n = tri[ok], n[ok] / nn[ok, None]
        vis = n @ bd > -0.05
        tri, n = tri[vis], n[vis]
        sh = 0.45 + 0.55 * np.clip(np.abs(n @ light), 0, 1)
        base = np.array(part_colour(i))
        P2 = np.stack([tri @ bx, tri @ by], axis=2)
        polys.append(P2)
        cols.append(np.clip(base[None, :] * sh[:, None], 0, 1))
        depth.append((tri @ bd).mean(1))
    P = np.concatenate(polys)
    C = np.concatenate(cols)
    Dp = np.concatenate(depth)
    o = np.argsort(Dp)
    ax.add_collection(PolyCollection(P[o], facecolors=C[o], edgecolors="none", linewidths=0, antialiased=False))
    # screws (x-ray, on top)
    segs, scol, heads, hcol, hs = [], [], [], [], []
    for r in recs:
        if str(r.get("status") or "").startswith(("NOT FITTED", "LEAVE OUT")):
            continue
        off = np.array(EXPLODE.get(r["viewer_sub"], (0, 0, 0)), float) * explode
        s0 = np.array(r["seat_world"]) + off
        a = np.array(r["axis_world"])
        L = r.get("draw_length_mm") or 4.0
        h = r.get("head") or {}
        k = (h.get("k") or 1.0)
        p_head = s0 - a * k
        p_tip = s0 + a * L
        segs.append([[p_head @ bx, p_head @ by], [p_tip @ bx, p_tip @ by]])
        scol.append(r["color"])
        c = s0 - a * k / 2
        heads.append([c @ bx, c @ by])
        hcol.append(r["color"])
        hs.append(9 if r["kind"] == "insert" else 7 + 3 * (h.get("dk") or 3) / 5.5)
    ax.add_collection(LineCollection(segs, colors=scol, linewidths=1.6, zorder=3))
    H = np.array(heads)
    ax.scatter(H[:, 0], H[:, 1], s=np.array(hs) ** 1.25, c=hcol, edgecolors="k", linewidths=0.35, zorder=4)
    allp = P.reshape(-1, 2)
    lo, hi = allp.min(0), allp.max(0)
    pad = 0.03 * (hi - lo).max()
    ax.set_xlim(lo[0] - pad, hi[0] + pad)
    ax.set_ylim(lo[1] - pad, hi[1] + pad)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, fontsize=10)


def save_small(fig, path, limit=495_000):
    from PIL import Image
    tmp = path + ".tmp.png"
    fig.savefig(tmp, dpi=fig.dpi, facecolor="white")
    im = Image.open(tmp).convert("RGB")
    for ncol in (256, 192, 128, 96, 64):
        q = im.quantize(colors=ncol, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        q.save(path, optimize=True)
        if os.path.getsize(path) <= limit:
            break
    os.remove(tmp)
    return os.path.getsize(path)


def legend(fig, recs, colors):
    from matplotlib.patches import Patch
    cnt = Counter(r["color_key"] for r in recs if not str(r.get("status") or "").startswith(("NOT FITTED", "LEAVE OUT")))
    order = [k for k in colors if k in cnt] + [k for k in cnt if k not in colors]
    labels = {"M2 servo bag": "M2x6 servo bag", "M2 kit": "M2 kit (x4, x5, x8)", "M3 horn centre": "M3x6 horn centre (bag)",
              "PA3 idle": "PA3.0x5 idle horn (bag)", "M2 case (factory)": "STS3215 case screw (factory)",
              "SG90 bag": "SG90 bag screw", "M3 insert": "M3 heat-set insert"}
    h = [Patch(color=colors.get(k, "#17becf"), label="%s: %d" % (labels.get(k, k), cnt[k])) for k in order]
    fig.legend(handles=h, loc="lower center", ncol=min(6, len(h)), fontsize=8, frameon=False)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--scratch", default=os.environ.get("ODM_FASTENER_SCRATCH"))
    ap.add_argument("--json", default=os.path.join(HERE, "fasteners.json"))
    ap.add_argument("--outdir", default=HERE)
    a = ap.parse_args()
    if not a.scratch:
        sys.exit("give --scratch or ODM_FASTENER_SCRATCH (outside the repo)")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    D = json.load(open(a.json))
    recs = D["fasteners"]
    colors = D["meta"]["colors"]
    S = fastlib.Scene(os.path.abspath(a.scratch))
    n_fit = sum(1 for r in recs if not str(r.get("status") or "").startswith(("NOT FITTED", "LEAVE OUT")))
    fig, axs = plt.subplots(1, 2, figsize=(16, 10), dpi=100)
    draw(axs[0], S, recs, 35, 18, title="Front left, zero pose")
    draw(axs[1], S, recs, 215, 18, title="Back right, zero pose")
    legend(fig, recs, colors)
    fig.suptitle("Open Duck Mini v2: all %d fitted fasteners (screws and inserts), coloured by spec, drawn over the parts" % n_fit, fontsize=12)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.94, bottom=0.08, wspace=0.02)
    p1 = os.path.join(a.outdir, "fasteners_assembled.png")
    print(p1, save_small(fig, p1))
    plt.close(fig)
    fig, ax = plt.subplots(1, 1, figsize=(14, 12), dpi=100)
    draw(ax, S, recs, 25, 15, explode=0.6, title="Exploded by subassembly (viewer level-1 vectors x 0.6)")
    legend(fig, recs, colors)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.96, bottom=0.07)
    p2 = os.path.join(a.outdir, "fasteners_exploded.png")
    print(p2, save_small(fig, p2))


if __name__ == "__main__":
    main()
