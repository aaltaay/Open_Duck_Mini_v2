#!/usr/bin/env python3
"""figs.py: small figures for the v3 nest study. sim pass only, except the edge profile which is the height field itself.

  PYTHONDONTWRITEBYTECODE=1 python3 figs.py profile
  PYTHONDONTWRITEBYTECODE=1 python3 figs.py bars
profile draws the three mat edges. bars draws the run comparisons from the result files that exist.
"""
import os
import sys

import numpy as np

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.dirname(HERE)
sys.path.insert(0, SIM)

INK, MUT, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3de", "#fcfcfb"
COLS = {"old": "#8a8982", "v2": "#2a78d6", "mix": "#1f7a4d", "steps": "#c46b1a", "taper": "#7a4e9a", "wall": "#9a3b3b"}


def _style():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": MUT, "xtick.color": MUT,
                         "ytick.color": MUT, "text.color": INK, "axes.spines.top": False, "axes.spines.right": False,
                         "figure.facecolor": SURF, "axes.facecolor": SURF, "font.family": "DejaVu Sans"})
    return plt


def profile():
    import nestlib as N
    plt = _style()
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    saved = os.environ.get("NEST_EDGE")
    curves = []
    for mode, label in (("one", "one 2 mm step (archived)"), ("steps", "two 1 mm steps, 20 mm apart"), ("taper", "20 mm ramp, no step")):
        os.environ["NEST_EDGE"] = mode
        n, h = N.hfield_data()
        half = N.field_half()
        g = np.linspace(-half, half, n)
        iy = int(np.argmin(np.abs(g)))
        # room side, y = 0: x from -0.32 to -0.18
        sel = (g < -0.18) & (g > -0.32)
        z = (-N.HF_DROP + h[iy, sel] * (N.MAT_H + N.HF_DROP)) * 1000
        z = np.maximum(z, 0.0)   # below the floor the floor plane carries the duck
        curves.append((g[sel] * 1000, z, label))
    if saved is None:
        os.environ.pop("NEST_EDGE", None)
    else:
        os.environ["NEST_EDGE"] = saved
    colors = ["#8a8982", "#c46b1a", "#7a4e9a"]
    for (x, z, label), col in zip(curves, colors):
        ax.plot(x, z, color=col, lw=2.2, label=label)
    ax.axhline(0, color=GRID, lw=0.8)
    ax.set_xlabel("x, room side of the sun (mm). The sun centre is 0.")
    ax.set_ylabel("height the foot meets (mm)")
    ax.set_ylim(-0.15, 2.6)
    ax.set_xlim(-320, -180)
    ax.legend(frameon=False, fontsize=8, loc="center left")
    ax.set_title("Mat edge in the sim height field", loc="left", fontsize=11, fontweight="bold")
    ax.grid(color=GRID, lw=0.7)
    ax.tick_params(length=0)
    fig.tight_layout()
    path = os.path.join(HERE, "V3_edge_profile.png")
    fig.savefig(path, dpi=120)
    print(path)


def _series():
    """named run lists. The aim row uses the stepped-edge 6.0 V runs plus the 7.2 V aim-20 runs,
    because the aim is applied only at 7.2 V. Missing files are skipped."""
    sys.path.insert(0, os.path.join(SIM, "v2"))
    import compare as C
    out = []

    def add(name, runs):
        out.append((name, [r for r in runs if "error" not in r]))

    old, _ = C.load(os.path.join(SIM, "nest_runs_main.json"))
    v2, _ = C.load(os.path.join(SIM, "v2", "nest_runs_v2.json"))
    add("old steering", old)
    add("v2 straight", v2)
    here = HERE

    def load_tag(tag):
        path = os.path.join(here, "nest_runs_%s.json" % tag)
        if not os.path.exists(path):
            return None
        runs, _ = C.load(path)
        return runs

    mix = load_tag("mix")
    steps = load_tag("steps")
    taper = load_tag("taper")
    aim = load_tag("aim20full")
    wall = load_tag("wall215")
    if mix:
        add("mixed", mix)
    if steps:
        add("two steps", steps)
    if taper:
        add("taper", taper)
    if steps and aim:
        s6 = [r for r in steps if r["cfg"]["volt"] == 6.0]
        add("aim 20 mm", s6 + aim)
    if wall:
        add("wall 215 mm", wall)
    return out


def _count(runs, volt, which):
    rr = [r for r in runs if volt is None or r["cfg"]["volt"] == volt]
    if which == "falls":
        return sum(bool(r.get("fell")) for r in rr)
    def ok(r, k):
        sits = r.get("sits") or []
        if not sits:
            return False
        if k == 1:
            return bool(sits[0]["nest"]["ok"] and not sits[0]["fell"])
        return any(s["nest"]["ok"] and not s["fell"] for s in sits)
    return sum(ok(r, 1 if which == "first" else 3) for r in rr)


def _worst(runs, key):
    return min(r[key][0] for r in runs)


def bars():
    plt = _style()
    series = _series()
    if len(series) < 2:
        print("no study runs yet")
        return
    names = [s[0] for s in series]
    x = np.arange(len(names))
    w = 0.36
    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.2))
    ax = axes[0]
    f6 = [_count(s[1], 6.0, "falls") for s in series]
    f7 = [_count(s[1], 7.2, "falls") for s in series]
    ax.bar(x - w / 2, f6, w, color="#8a8982", label="6.0 V")
    ax.bar(x + w / 2, f7, w, color="#c46b1a", label="7.2 V")
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=8, rotation=18, ha="right")
    ax.set_ylabel("falls, of 270")
    ax.set_title("Falls", loc="left", fontweight="bold")
    ax.legend(frameon=False, fontsize=8)
    ax.grid(axis="y", color=GRID, lw=0.7)
    ax.tick_params(length=0)
    top = max(f6 + f7 + [1])
    ax.set_ylim(0, top * 1.25)
    for i, (a, b) in enumerate(zip(f6, f7)):
        ax.text(i - w / 2, a + top * 0.02, str(a), ha="center", va="bottom", fontsize=7)
        ax.text(i + w / 2, b + top * 0.02, str(b), ha="center", va="bottom", fontsize=7)

    ax = axes[1]
    c6 = [_count(s[1], 6.0, "first") for s in series]
    c7 = [_count(s[1], 7.2, "first") for s in series]
    ax.bar(x - w / 2, c6, w, color="#8a8982", label="6.0 V")
    ax.bar(x + w / 2, c7, w, color="#1f7a4d", label="7.2 V")
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=8, rotation=18, ha="right")
    ax.set_ylabel("first sit charging, of 270")
    ax.set_ylim(0, 340)
    ax.set_title("Charge at the first sit", loc="left", fontweight="bold")
    ax.legend(frameon=False, fontsize=8)
    ax.grid(axis="y", color=GRID, lw=0.7)
    ax.tick_params(length=0)
    for i, (a, b) in enumerate(zip(c6, c7)):
        ax.text(i - w / 2, a + 4, str(a), ha="center", va="bottom", fontsize=6.5)
        ax.text(i + w / 2, b + 4, str(b), ha="center", va="bottom", fontsize=6.5)
    fig.suptitle("Nest docking, same seeds. sim pass only.", fontsize=12, fontweight="bold", x=0.02, ha="left")
    fig.tight_layout()
    path = os.path.join(HERE, "V3_compare.png")
    fig.savefig(path, dpi=120)
    print(path)

    fig, ax = plt.subplots(figsize=(11.4, 4.0))
    wall = [_worst(s[1], "min_wall_clear_mm") for s in series]
    rim = [_worst(s[1], "min_rim_clear_mm") for s in series]
    ax.bar(x - w / 2, wall, w, color="#2a78d6", label="head to wall, worst run")
    ax.bar(x + w / 2, rim, w, color="#7a4e9a", label="foot to rim, worst run")
    ax.axhline(0, color=INK, lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=8, rotation=18, ha="right")
    ax.set_ylabel("closest gap over all runs (mm)")
    ax.set_title("Closest a part came to the wall or the rim. Negative means inside. sim pass only.", loc="left", fontweight="bold")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.grid(axis="y", color=GRID, lw=0.7)
    ax.tick_params(length=0)
    span = max(abs(min(wall + rim)), max(wall + rim), 1)

    def lab(v):
        return "%.0f" % v if abs(v) >= 100 else "%.1f" % v

    for i, (a, b) in enumerate(zip(wall, rim)):
        ax.text(i - w / 2, a + (span * 0.03 if a >= 0 else -span * 0.03), lab(a), ha="center",
                va="bottom" if a >= 0 else "top", fontsize=7)
        ax.text(i + w / 2, b + (span * 0.03 if b >= 0 else -span * 0.03), lab(b), ha="center",
                va="bottom" if b >= 0 else "top", fontsize=7)
    fig.tight_layout()
    path = os.path.join(HERE, "V3_clearance.png")
    fig.savefig(path, dpi=120)
    print(path)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "profile"
    if cmd == "profile":
        profile()
    elif cmd == "bars":
        bars()
    else:
        raise SystemExit("profile or bars")
