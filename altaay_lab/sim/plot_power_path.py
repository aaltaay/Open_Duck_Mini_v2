"""Plot the servo supply voltage over a walk from the ngspice power path sim (sim pass only).

Inputs: the v_*.npz time series that sim/power_path_sim.py writes when ODM_SAVE_V=1 (one per case).
Usage:
  ODM_SAVE_TRACES=1 ODM_OUT=<dir> python3 sim/current_budget.py walk_backlash
  ODM_TRACES=<dir> ODM_OUT=<dir> ODM_SAVE_V=1 python3 -c "import power_path_sim ..."   (see sim/POWER_PATH_SIM.md)
  python3 sim/plot_power_path.py <dir> <out.png>
Colours: dataviz reference palette (categorical slots 1 to 3, validated), status warning and critical for the gates.
"""
import glob
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"
CHAIN = [("Left leg", "left_", "#2a78d6"), ("Right leg", "right_", "#eb6834"), ("Neck and head", "", "#1baf7a")]
WARN, CRIT = "#fab219", "#d03b3b"
ORDER = ["hip_yaw", "hip_roll", "hip_pitch", "knee", "ankle"]
HEAD = ["neck_pitch", "head_pitch", "head_yaw", "head_roll"]


def chain_of(n):
    if n.startswith("left_"):
        return 0
    if n.startswith("right_"):
        return 1
    return 2


def nice(n):
    return n.replace("left_", "").replace("right_", "").replace("_", " ")


def load(d, tag):
    f = [p for p in glob.glob(os.path.join(d, "v_*.npz")) if tag in os.path.basename(p)]
    if not f:
        sys.exit("no v_*.npz with %r in %s" % (tag, d))
    z = np.load(f[0], allow_pickle=True)
    t = z["t"] - z["t"][0]
    return t, list(z["names"]), z["V"], str(z["label"])


def main(d, out):
    cases = [("nominal__typical", "Typical resistances (expected)"), ("nominal__high_side", "High-side resistances (worst corner)")]
    data = [load(d, tag) for tag, _ in cases]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK2, "text.color": INK})
    fig = plt.figure(figsize=(16, 9.6), dpi=100, facecolor=SURF)
    gs = fig.add_gridspec(2, 2, width_ratios=[2.25, 1], hspace=0.38, wspace=0.16, left=0.055, right=0.985, top=0.86, bottom=0.08)
    fig.text(0.055, 0.955, "Servo supply voltage while the duck walks", fontsize=19, weight="bold", color=INK)
    fig.text(0.055, 0.918, "ngspice model of the whole power path (cells, BMS, fuse, switch, BEC, wires, every connector hop), "
             "star wiring D15, pack at nominal 7.4 V, 6 s of the stock walk. Sim pass only.", fontsize=11.5, color=INK2)
    fig.text(0.055, 0.893, "Each thin line is one servo's voltage at its connector. Bold line: the lowest servo in that chain.",
             fontsize=11.5, color=INK2)
    mins = {}
    for row, ((t, names, V, label), (_, title)) in enumerate(zip(data, cases)):
        ax = fig.add_subplot(gs[row, 0], facecolor=SURF)
        worst_by_chain = {}
        for i, n in enumerate(names):
            c = chain_of(n)
            mins.setdefault(n, [None, None])[row] = float(V[i].min())
            if c not in worst_by_chain or V[i].min() < V[worst_by_chain[c]].min():
                worst_by_chain[c] = i
        for i, n in enumerate(names):
            c = chain_of(n)
            ax.plot(t, V[i], color=CHAIN[c][2], lw=0.8, alpha=0.32, zorder=2)
        for c, i in worst_by_chain.items():
            ax.plot(t, V[i], color=CHAIN[c][2], lw=2.0, zorder=3)
        for y, col, txt in ((6.0, WARN, "6.0 V walk gate (TEST_PLAN 9)"), (4.5, CRIT, "4.5 V hard limit")):
            ax.axhline(y, color=col, lw=1.6, ls=(0, (5, 3)), zorder=1)
            ax.text(t[-1], y + 0.07, txt, ha="right", va="bottom", fontsize=10, color=INK2)
        ax.set_xlim(0, t[-1])
        ax.set_ylim(2.5, 8.0)
        ax.set_ylabel("Volts at the servo")
        ax.set_xlabel("Time in the walk (s)")
        ax.grid(axis="y", color=GRID, lw=0.8)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.set_title(title, loc="left", fontsize=13, weight="bold", color=INK, pad=8)
        # direct labels for the lowest servo of each chain, placed at its minimum
        for c, i in sorted(worst_by_chain.items()):
            k = int(np.argmin(V[i]))
            ax.annotate("%s %s, min %.2f V" % (CHAIN[c][0].split()[0].lower() if c < 2 else "", nice(names[i]), V[i][k]),
                        xy=(t[k], V[i][k]), xytext=(t[k] + 0.12, V[i][k] - 0.42 - 0.28 * c), fontsize=10, color=INK,
                        arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))
    # right: min voltage per servo, both corners
    ax = fig.add_subplot(gs[:, 1], facecolor=SURF)
    rows = [n for p in ("left_", "right_") for n in [p + o for o in ORDER]] + HEAD
    rows = [n for n in rows if n in mins]
    y = np.arange(len(rows))[::-1]
    for yy, n in zip(y, rows):
        c = chain_of(n)
        a, b = mins[n]
        ax.plot([b, a], [yy, yy], color=CHAIN[c][2], lw=2, zorder=2)
        ax.plot(a, yy, "o", ms=9, color=CHAIN[c][2], mec=SURF, mew=2, zorder=3)
        ax.plot(b, yy, "o", ms=9, mfc=SURF, mec=CHAIN[c][2], mew=2, zorder=3)
        ax.text(a + 0.08, yy, "%.2f" % a, va="center", fontsize=9.5, color=INK2)
    ax.axvline(6.0, color=WARN, lw=1.6, ls=(0, (5, 3)), zorder=1)
    ax.axvline(4.5, color=CRIT, lw=1.6, ls=(0, (5, 3)), zorder=1)
    ax.set_yticks(y)
    ax.set_yticklabels([("L " if n.startswith("left_") else "R " if n.startswith("right_") else "") + nice(n) for n in rows])
    ax.set_xlim(2.5, 8.0)
    ax.set_xlabel("Lowest voltage in the walk (V)")
    ax.grid(axis="x", color=GRID, lw=0.8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_title("Lowest voltage per servo", loc="left", fontsize=13, weight="bold", color=INK, pad=8)
    from matplotlib.lines import Line2D
    h = [Line2D([0], [0], color=col, lw=2.5, label=lab) for lab, _, col in CHAIN]
    h += [Line2D([0], [0], marker="o", ls="", ms=8, color=INK2, mec=SURF, label="typical"),
          Line2D([0], [0], marker="o", ls="", ms=8, mfc=SURF, mec=INK2, mew=2, label="high-side")]
    ax.legend(handles=h, loc="lower left", frameon=False, fontsize=10)
    fig.text(0.055, 0.02, "Source: altaay_lab/sim/power_path_sim.py and plot_power_path.py. The real hop resistance is measured on the bench "
             "(TEST_PLAN.md section 5) and the walk is logged on the robot (section 9).", fontsize=9.5, color=INK2)
    fig.savefig(out, dpi=100, facecolor=SURF)
    print("wrote", out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
