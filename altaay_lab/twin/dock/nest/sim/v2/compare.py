#!/usr/bin/env python3
"""compare.py: the original 540 runs against the v2 540 runs, side by side. sim pass only.
Uses the original analyze.summarize() on both files, plus the v2-only records.
  PYTHONDONTWRITEBYTECODE=1 python3 compare.py [new_tag]    -> compare.json, compare_table.md, V2_compare.png
"""
import json
import os
import sys

import numpy as np

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(HERE)
sys.path.insert(0, PARENT)
import analyze as A  # noqa: E402

WALK_IN = ("approach", "stage", "cross", "walk_on")
A.is_trip = lambda r: bool(r.get("fell") and r.get("fall_stage") in WALK_IN + ("fine", "shuffle", "walk_off")  # noqa: E731
                           and abs(float(np.hypot(*r.get("fall_xy", [9, 9]))) - A.MAT_R) < 0.15)


def extra(rr):
    """numbers the original summary does not have, computed the same way for both controllers"""
    n = len(rr)
    sat = [r for r in rr if r.get("sits")]
    k1 = sum(bool(r["sits"][0]["nest"]["ok"] and not r["sits"][0]["fell"]) for r in sat)
    k3 = sum(any(s["nest"]["ok"] and not s["fell"] for s in r["sits"]) for r in sat)
    ec = np.array([r["edge_cross_s"] for r in rr if "edge_cross_s" in r])
    fall_walk_in = [r for r in rr if r.get("fell") and r.get("fall_stage") in WALK_IN]
    never = [r for r in rr if not r.get("sits") and not r.get("fell")]
    t = np.array([r["t_first_sit_s"] for r in rr if "t_first_sit_s" in r])
    seat = np.array([r["sits"][0]["seat_xy"] for r in sat]) * 1000
    rad = np.hypot(seat[:, 0], seat[:, 1]) if len(seat) else np.zeros(0)
    pt = [r for r in rr if "pre_turn" in r]
    e = np.array([np.array(r["pre_turn"]["truth"][:2]) - np.array(r["pre_turn"]["target"]) for r in pt]) * 1000
    yaw = np.degrees([r["pre_turn"]["truth"][2] for r in pt])
    mv = {}
    for r in rr:
        for c_, n_ in r.get("moves", []):
            k = "fwd" if c_[0] > 0 else "back" if c_[0] < 0 else "left" if c_[1] > 0 else "yaw+" if c_[2] > 0 else "yaw-"
            mv[k] = mv.get(k, 0) + 1
    f = lambda a: None if not len(a) else [round(float(np.mean(a)), 1), round(float(np.std(a)), 1)]  # noqa: E731
    out = dict(n=n, falls_all=sum(bool(r.get("fell")) for r in rr), falls_walk_in=len(fall_walk_in),
               falls_by_stage={k: sum(r.get("fall_stage") == k for r in rr if r.get("fell")) for k in sorted({str(r.get("fall_stage")) for r in rr if r.get("fell")})},
               never_reached_the_sit_no_fall=len(never), reached_first_sit=len(sat),
               edge_window_slower_than_6s=int((ec > 6).sum()), edge_window_s=dict(n=len(ec), mean=round(float(ec.mean()), 2), p95=round(float(np.percentile(ec, 95)), 2), max=round(float(ec.max()), 2)) if len(ec) else None,
               charge_first_sit=dict(k=k1, n=n, pct=A.pct(k1, n), ci95=A.wilson(k1, n)), charge_within_3=dict(k=k3, n=n, pct=A.pct(k3, n), ci95=A.wilson(k3, n)),
               charge_first_sit_given_sit=dict(k=k1, n=len(sat), pct=A.pct(k1, len(sat)), ci95=A.wilson(k1, len(sat))),
               charge_within_3_given_sit=dict(k=k3, n=len(sat), pct=A.pct(k3, len(sat))),
               seat_x_mm=f(seat[:, 0]) if len(seat) else None, seat_y_mm=f(seat[:, 1]) if len(seat) else None,
               seat_radial_mm=dict(mean=round(float(rad.mean()), 1), p50=round(float(np.percentile(rad, 50)), 1), p95=round(float(np.percentile(rad, 95)), 1), max=round(float(rad.max()), 1),
                                   inside_45mm_pct=A.pct(int((rad < 45).sum()), len(rad)), beyond_100mm=int((rad > 100).sum())) if len(rad) else None,
               time_to_first_sit_s=dict(mean=round(float(t.mean()), 1), p95=round(float(np.percentile(t, 95)), 1), min=round(float(t.min()), 1), max=round(float(t.max()), 1)) if len(t) else None,
               turn_spot_err_x_mm=f(e[:, 0]) if len(e) else None, turn_spot_err_y_mm=f(e[:, 1]) if len(e) else None,
               turn_spot_err_rms_mm=round(float(np.sqrt((e ** 2).sum(1).mean())), 1) if len(e) else None,
               turn_spot_err_beyond_60mm=int((np.hypot(e[:, 0], e[:, 1]) > 60).sum()) if len(e) else None,
               heading_before_turn_deg=f(yaw) if len(yaw) else None, heading_before_turn_abs_max_deg=round(float(np.abs(yaw).max()), 1) if len(yaw) else None,
               fine_rounds_mean=round(float(np.mean([r["fine_rounds"] for r in pt])), 2) if pt else None, creep_moves=mv)
    wc = np.array([r["min_wall_clear_mm"][0] for r in sat])
    rc = np.array([r["min_rim_clear_mm"][0] for r in sat])
    if len(wc):
        out["wall_mm"] = dict(min=round(float(wc.min()), 1), p5=round(float(np.percentile(wc, 5)), 1), mean=round(float(wc.mean()), 1), touched=int((wc < 0).sum()))
        out["rim_mm"] = dict(min=round(float(rc.min()), 1), p5=round(float(np.percentile(rc, 5)), 1), mean=round(float(rc.mean()), 1), touched=int((rc < 0).sum()))
    # v2-only records
    if any("stage" in r for r in rr):
        st = [r["stage"] for r in rr if "stage" in r]
        cr = [r["cross"] for r in rr if "cross" in r]
        out["v2"] = dict(runs_with_a_turn_or_side_command_while_a_sole_was_on_the_edge=sum(bool(r.get("steer_on_edge_steps")) for r in rr),
                         those_by_stage={k: sum(k in r.get("steer_on_edge_steps", {}) for r in rr) for k in sorted({k for r in rr for k in r.get("steer_on_edge_steps", {})})},
                         stage_turn_moves=dict(mean=round(float(np.mean([s["rounds"] for s in st])), 2), none=sum(s["rounds"] == 0 for s in st), max=max(s["rounds"] for s in st)),
                         stage_toe_to_edge_mm=dict(min=float(np.min([s["toe_to_edge_mm"] for s in st])), mean=round(float(np.mean([s["toe_to_edge_mm"] for s in st])), 1),
                                                   max=float(np.max([s["toe_to_edge_mm"] for s in st]))),
                         stage_heading_error_left_deg=f(np.array([s["yaw_err_left_deg"] for s in st])),
                         cross_not_done=sum(not c["done"] for c in cr), cross_retries_runs=sum(c["retries"] > 0 for c in cr), cross_retries=sum(c["retries"] for c in cr),
                         cross_stage_s=dict(mean=round(float(np.mean([c["s"] for c in cr])), 2), max=float(np.max([c["s"] for c in cr]))),
                         heel_inside_when_steering_resumed_mm=dict(min=float(np.min([c["heel_inside_mm"] for c in cr if c["done"]])), mean=round(float(np.mean([c["heel_inside_mm"] for c in cr if c["done"]])), 1)),
                         feet_not_both_on_when_steering_resumed=sum(c["done"] and c["feet"] != ["on", "on"] for c in cr),
                         stage_time_s={k: round(float(np.mean([r["stages"][k] for r in rr if k in r["stages"]])), 1) for k in ("approach", "stage", "cross", "walk_on", "fine")})
    else:
        out["stage_time_s"] = {k: round(float(np.mean([r["stages"][k] for r in rr if k in r["stages"]])), 1) for k in ("approach", "walk_on", "fine")}
    return out


SL = [("all", lambda r: True), ("6.0 V", lambda r: r["cfg"]["volt"] == 6.0), ("7.2 V", lambda r: r["cfg"]["volt"] == 7.2),
      ("noise low", lambda r: r["cfg"]["noise"] == "low"), ("noise mid", lambda r: r["cfg"]["noise"] == "mid"), ("noise high", lambda r: r["cfg"]["noise"] == "high"),
      ("mat mu 0.6", lambda r: r["cfg"]["mu"] == 0.6), ("mat mu 0.8", lambda r: r["cfg"]["mu"] == 0.8), ("mat mu 1.0", lambda r: r["cfg"]["mu"] == 1.0)]


def load(path):
    d = json.load(open(path))
    return d["runs"], {k: v for k, v in d.items() if k != "runs"}


def table(O, Nw):
    def c(S, key, sub=None, fmt="%s"):
        v = S.get(key)
        if v is None:
            return "-"
        if sub:
            v = v[sub]
        return fmt % v
    rows = []
    add = lambda name, fn: rows.append([name] + [fn(O[s]) for s in ("all", "6.0 V", "7.2 V")] + [fn(Nw[s]) for s in ("all", "6.0 V", "7.2 V")])  # noqa: E731
    pc = lambda d: "%s %% (%d of %d)" % (d["pct"], d["k"], d["n"])  # noqa: E731
    add("Runs", lambda S: S["n"])
    add("Falls, whole run", lambda S: S["falls_all"])
    add("Falls in the walk-in (floor, edge, mat)", lambda S: S["falls_walk_in"])
    add("Falls by stage", lambda S: ", ".join("%s %d" % kv for kv in S["falls_by_stage"].items()) or "none")
    add("Stalls: 160 mm edge window slower than 6 s", lambda S: S["edge_window_slower_than_6s"])
    add("Edge window time, mean / 95th / worst (s)", lambda S: "%s / %s / %s" % (S["edge_window_s"]["mean"], S["edge_window_s"]["p95"], S["edge_window_s"]["max"]))
    add("Never reached the sit, no fall (gave up)", lambda S: S["never_reached_the_sit_no_fall"])
    add("Reached the first sit", lambda S: S["reached_first_sit"])
    add("Charge at the first sit", lambda S: pc(S["charge_first_sit"]))
    add("95 % range of that", lambda S: "%s to %s" % tuple(S["charge_first_sit"]["ci95"]))
    add("Charge within 3 sits", lambda S: pc(S["charge_within_3"]))
    add("Charge at the first sit, given the sit was reached", lambda S: pc(S["charge_first_sit_given_sit"]))
    add("Charge within 3 sits, given the sit was reached", lambda S: pc(S["charge_within_3_given_sit"]))
    add("Seat pins after torque off, x mean / sigma (mm)", lambda S: "%s / %s" % tuple(S["seat_x_mm"]))
    add("Seat pins after torque off, y mean / sigma (mm)", lambda S: "%s / %s" % tuple(S["seat_y_mm"]))
    add("Radial miss mean / median / 95th / worst (mm)", lambda S: "%(mean)s / %(p50)s / %(p95)s / %(max)s" % S["seat_radial_mm"])
    add("Inside 45 mm", lambda S: "%s %%" % S["seat_radial_mm"]["inside_45mm_pct"])
    add("Landings more than 100 mm out", lambda S: S["seat_radial_mm"]["beyond_100mm"])
    add("Error at the turn spot before the turn, x mean / sigma (mm)", lambda S: "%s / %s" % tuple(S["turn_spot_err_x_mm"]))
    add("Error at the turn spot before the turn, y mean / sigma (mm)", lambda S: "%s / %s" % tuple(S["turn_spot_err_y_mm"]))
    add("Error at the turn spot, RMS (mm)", lambda S: S["turn_spot_err_rms_mm"])
    add("Heading before the turn, mean / sigma / worst (deg)", lambda S: "%s / %s / %s" % (*S["heading_before_turn_deg"], S["heading_before_turn_abs_max_deg"]))
    add("Fine-move rounds on the mat, mean", lambda S: S["fine_rounds_mean"])
    add("Time to torque off at the first sit, mean / 95th / worst (s)", lambda S: "%(mean)s / %(p95)s / %(max)s" % S["time_to_first_sit_s"])
    add("Closest to the wall: worst / 5th percentile / mean (mm)", lambda S: "%(min)s / %(p5)s / %(mean)s" % S["wall_mm"])
    add("Closest to the rim: worst / 5th percentile / mean (mm)", lambda S: "%(min)s / %(p5)s / %(mean)s" % S["rim_mm"])
    add("Wall or rim touched", lambda S: S["wall_mm"]["touched"] + S["rim_mm"]["touched"])
    hd = ["sim pass only", "Old: all", "Old: 6.0 V", "Old: 7.2 V", "New: all", "New: 6.0 V", "New: 7.2 V"]
    return "\n".join([A.row(hd), A.row(["---"] * 7)] + [A.row(r) for r in rows])


def figure(Ro, Rn, O, Nw, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    CO, CN, INK, MUT, GRID, SURF = "#8a8982", "#2a78d6", "#0b0b0b", "#52514e", "#e4e3de", "#fcfcfb"
    plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": MUT, "xtick.color": MUT, "ytick.color": MUT, "text.color": INK,
                         "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": SURF, "axes.facecolor": SURF, "font.family": "DejaVu Sans"})
    fig = plt.figure(figsize=(13.5, 8.6))
    gs = fig.add_gridspec(2, 12, hspace=0.50, wspace=1.6, left=0.055, right=0.985, top=0.86, bottom=0.075)
    fig.suptitle("Nest docking in sim: old walk-in (steer across the mat edge) against new (line up, then cross straight)", x=0.055, y=0.975, ha="left", fontsize=13, fontweight="bold")
    fig.text(0.055, 0.925, "sim pass only. 540 runs each, same seeds, start poses, voltages and pose noise. 270 runs per voltage.", color=MUT, fontsize=9.5)
    hnd = [plt.Rectangle((0, 0), 1, 1, color=CO), plt.Rectangle((0, 0), 1, 1, color=CN)]
    fig.legend(hnd, ["old controller", "new controller (v2)"], loc="upper right", bbox_to_anchor=(0.985, 0.945), ncol=2, frameon=False, fontsize=10)

    def bars(ax, cats, vo, vn, title, ylabel, fmt="%d", ymax=None, err_o=None, err_n=None):
        x = np.arange(len(cats))
        w = 0.36
        for xs, v, col, er in ((x - w / 2 - 0.01, vo, CO, err_o), (x + w / 2 + 0.01, vn, CN, err_n)):
            ax.bar(xs, v, w, color=col, zorder=3)
            if er is not None:
                ax.errorbar(xs, v, yerr=er, fmt="none", ecolor=INK, elinewidth=0.9, capsize=2.5, zorder=4)
            for i, (xx, vv) in enumerate(zip(xs, v)):
                top = vv + (er[1][i] if er is not None else 0)
                ax.text(xx, top + (ymax or max(max(vo), max(vn), 1)) * 0.015, fmt % vv, ha="center", va="bottom", fontsize=8.5, color=INK)
        ax.set_xticks(x)
        ax.set_xticklabels(cats)
        ax.set_title(title, loc="left", fontsize=10, fontweight="bold", pad=8)
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", color=GRID, lw=0.7, zorder=0)
        ax.tick_params(length=0)
        if ymax:
            ax.set_ylim(0, ymax)
        else:
            ax.set_ylim(0, max(max(vo), max(vn), 1) * 1.18)

    V = ("6.0 V", "7.2 V")
    # A: falls and stalls per voltage
    ax = fig.add_subplot(gs[0, 0:4])
    cats = ["falls\n6.0 V", "falls\n7.2 V", "slow\nedge\n6.0 V", "slow\nedge\n7.2 V", "gave up\n6.0 V", "gave up\n7.2 V"]
    g = lambda S, k: [S[v][k] for v in V]  # noqa: E731
    vo = g(O, "falls_walk_in") + g(O, "edge_window_slower_than_6s") + g(O, "never_reached_the_sit_no_fall")
    vn = g(Nw, "falls_walk_in") + g(Nw, "edge_window_slower_than_6s") + g(Nw, "never_reached_the_sit_no_fall")
    bars(ax, cats, vo, vn, "Walk-in failures (runs of 270; slow edge = over 6 s)", "runs")
    ax.tick_params(axis="x", labelsize=8)
    # B: charge
    ax = fig.add_subplot(gs[0, 4:8])
    cats = ["first sit\nall", "first sit\n6.0 V", "first sit\n7.2 V", "within\n3 sits\nall", "first sit,\nif the sit\nwas reached"]
    keys = [("all", "charge_first_sit"), ("6.0 V", "charge_first_sit"), ("7.2 V", "charge_first_sit"), ("all", "charge_within_3"), ("all", "charge_first_sit_given_sit")]
    vo = [O[s][k]["pct"] for s, k in keys]
    vn = [Nw[s][k]["pct"] for s, k in keys]
    er = lambda S: None  # noqa: E731
    bars(ax, cats, vo, vn, "Charging (% of runs)", "%", fmt="%.0f", ymax=112)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.tick_params(axis="x", labelsize=8)
    # C: edge window time, sorted runs per voltage (log y)
    ax = fig.add_subplot(gs[0, 8:12])
    for R_, col in ((Ro, CO), (Rn, CN)):
        for v, ls in ((6.0, "-"), (7.2, "--")):
            e = np.sort([r["edge_cross_s"] for r in R_ if r["cfg"]["volt"] == v and "edge_cross_s" in r])
            ax.plot(e, 100.0 * (np.arange(len(e)) + 1) / 270, color=col, ls=ls, lw=2)
    ax.axvline(6, color=MUT, lw=0.8, ls=":")
    ax.text(6.4, 30, "over 6 s:\ncounted as\na slow edge", color=MUT, fontsize=8, va="bottom")
    ax.set_xscale("log")
    ax.set_xticks([1, 2, 3, 6, 10, 20, 40])
    ax.set_xticklabels(["1", "2", "3", "6", "10", "20", "40"])
    ax.set_xlabel("seconds for the 160 mm over the mat edge (log scale)")
    ax.set_ylabel("% of the 270 runs done by then")
    ax.set_ylim(0, 104)
    ax.grid(color=GRID, lw=0.7)
    ax.tick_params(length=0)
    ax.set_title("How long the edge takes", loc="left", fontsize=10, fontweight="bold", pad=8)
    ax.legend([plt.Line2D([0], [0], color=MUT, lw=2, ls="-"), plt.Line2D([0], [0], color=MUT, lw=2, ls="--")], ["6.0 V", "7.2 V"], frameon=False, loc="lower right", fontsize=8.5)
    # D, E: landing scatter old / new
    for j, (R_, col, nm) in enumerate(((Ro, CO, "old"), (Rn, CN, "new"))):
        ax = fig.add_subplot(gs[1, 4 * j:4 * j + 4])
        sat = [r for r in R_ if r.get("sits")]
        P = np.array([r["sits"][0]["seat_xy"] for r in sat]) * 1000
        okk = np.array([bool(r["sits"][0]["nest"]["ok"]) for r in sat])
        th = np.linspace(0, 2 * np.pi, 200)
        ax.fill(50 * np.sin(th), 50 * np.cos(th), color="#f3e3b0", zorder=1, lw=0)
        ax.plot(45 * np.sin(th), 45 * np.cos(th), color=MUT, lw=0.8, ls=":", zorder=2)
        lim = 110
        inn = (np.abs(P[:, 0]) < lim) & (np.abs(P[:, 1]) < lim)
        ax.scatter(P[inn & okk, 1], P[inn & okk, 0], s=9, color=col, alpha=0.55, lw=0, zorder=3)
        ax.scatter(P[inn & ~okk, 1], P[inn & ~okk, 0], s=34, marker="x", color=INK, lw=1.3, zorder=4)
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_aspect("equal")
        ax.set_xlabel("along the wall, y (mm)")
        ax.set_ylabel("toward the wall, x (mm)")
        ax.grid(color=GRID, lw=0.7, zorder=0)
        ax.tick_params(length=0)
        S = (O if j == 0 else Nw)["all"]
        ax.set_title("Seat pins at the first sit, %s (%d sits)" % (nm, len(sat)), loc="left", fontsize=10, fontweight="bold", pad=8)
        txt = "sigma x %.0f, y %.0f mm\n95th radial %.0f mm\n%d not charging (x)\n%d outside this frame" % (S["seat_x_mm"][1], S["seat_y_mm"][1], S["seat_radial_mm"]["p95"], int((~okk).sum()), int((~inn).sum()))
        ax.text(0.03, 0.97, txt, transform=ax.transAxes, va="top", fontsize=8.5, color=INK, bbox=dict(facecolor=SURF, edgecolor="none", alpha=0.85, pad=2))
        ax.text(0, -58, "sun disc, 50 mm radius", ha="center", va="top", fontsize=8, color=MUT)
    # F: time to first sit
    ax = fig.add_subplot(gs[1, 8:12])
    cats = ["6.0 V\nmean", "6.0 V\n95th", "7.2 V\nmean", "7.2 V\n95th"]
    vo = [O[v]["time_to_first_sit_s"][k] for v in V for k in ("mean", "p95")]
    vn = [Nw[v]["time_to_first_sit_s"][k] for v in V for k in ("mean", "p95")]
    bars(ax, cats, vo, vn, "Time from start to torque off at the first sit (s)", "s", fmt="%.0f")
    fig.savefig(path, dpi=130)


if __name__ == "__main__":
    tag = sys.argv[1] if len(sys.argv) > 1 else "v2"
    Ro, mo = load(os.path.join(PARENT, "nest_runs_main.json"))
    Rn, mn = load(os.path.join(HERE, "nest_runs_%s.json" % tag))
    err = [r for r in Rn if "error" in r]
    Rn = [r for r in Rn if "error" not in r]
    O = {k: extra([r for r in Ro if f(r)]) for k, f in SL}
    Nw = {k: extra([r for r in Rn if f(r)]) for k, f in SL}
    # run by run: what happened to the same seed
    bo = {r["cfg"]["seed"]: r for r in Ro}
    cls = lambda r: "fell" if r.get("fell") and r.get("fall_stage") not in ("walk_off", "walk_off_stand") else "no sit" if not r.get("sits") else "charged first sit" if r["sits"][0]["nest"]["ok"] else "charged later" if any(s["nest"]["ok"] for s in r["sits"]) else "never charged"  # noqa: E731
    pair = {}
    for r in Rn:
        k = "%s -> %s" % (cls(bo[r["cfg"]["seed"]]), cls(r))
        pair[k] = pair.get(k, 0) + 1
    fails = [dict(seed=r["cfg"]["seed"], noise=r["cfg"]["noise"], volt=r["cfg"]["volt"], mu=r["cfg"]["mu"], old=cls(bo[r["cfg"]["seed"]]), new=cls(r), fall_stage=r.get("fall_stage"),
                  seat_mm=[round(v * 1000, 1) for v in r["sits"][0]["seat_xy"]] if r.get("sits") else None, cross=r.get("cross", {}).get("s"), retries=r.get("cross", {}).get("retries"),
                  n_sits=len(r.get("sits", []))) for r in Rn if cls(r) != "charged first sit"]
    full = dict(old=A.summarize(Ro, mo), new=A.summarize(Rn, mn))
    json.dump(dict(label="sim pass only", old_file="../nest_runs_main.json", new_file="nest_runs_%s.json" % tag, crashed_new=len(err), old=O, new=Nw, same_seed_outcomes=pair,
                   new_runs_not_charging_at_first_sit=fails, original_summary_tables=full), open(os.path.join(HERE, "compare.json"), "w"), indent=1)
    T = table(O, Nw)
    open(os.path.join(HERE, "compare_table.md"), "w").write(T + "\n")
    print(T)
    print("\nsame seed outcomes:", json.dumps(pair, indent=1))
    print("\nv2 records:", json.dumps({k: Nw[k].get("v2") for k in ("all", "6.0 V", "7.2 V")}, indent=1))
    print("creep moves old", O["all"]["creep_moves"], "new", Nw["all"]["creep_moves"])
    print("crashed", len(err))
    for f_ in fails:
        print(f_)
    figure(Ro, Rn, O, Nw, os.path.join(HERE, "V2_compare.png"))
