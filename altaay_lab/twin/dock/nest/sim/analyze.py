#!/usr/bin/env python3
"""analyze.py: tables from nest_runs_<tag>.json. sim pass only.
  PYTHONDONTWRITEBYTECODE=1 python3 analyze.py [tag ...]     -> nest_results.json, tables on stdout (markdown)
Several tags are pooled (runs added later with another tag).
"""
import json
import os
import sys

import numpy as np

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
MAT_R = 0.247
NOISE_TXT = {"low": "5 mm / 1 deg", "mid": "15 mm / 3 deg", "high": "30 mm / 6 deg"}


def wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(100 * (c - h), 1), round(100 * (c + h), 1)]


def pct(k, n):
    return round(100.0 * k / n, 1) if n else None


def ms(v, scale=1.0, nd=1):
    v = np.array(v, float) * scale
    if not len(v):
        return None
    return dict(mean=round(float(v.mean()), nd), sd=round(float(v.std()), nd), min=round(float(v.min()), nd), max=round(float(v.max()), nd))


def load(tags):
    R, meta = [], None
    for t in tags:
        d = json.load(open(os.path.join(HERE, "nest_runs_%s.json" % t)))
        meta = meta or {k: v for k, v in d.items() if k != "runs"}
        R += d["runs"]
    return R, meta


def is_trip(r):
    """a fall while walking with the trunk within 150 mm of the mat edge line"""
    if not r.get("fell") or r.get("fall_stage") not in ("approach", "walk_on", "walk_off", "fine", "shuffle"):
        return False
    x, y = r.get("fall_xy", [9, 9])
    return abs(float(np.hypot(x, y)) - MAT_R) < 0.15


def summarize(rr, meta):
    n = len(rr)
    sit_shift = np.array(meta["sit_shift"])
    S = dict(n=n, crashed=sum("error" in r for r in rr))
    rr = [r for r in rr if "error" not in r]
    seq = lambda r: r.get("fall_stage") not in ("walk_off", "walk_off_stand")  # noqa: E731   a fall in the docking sequence proper
    falls = [r for r in rr if r["fell"]]
    S["falls_total"] = len(falls)
    S["falls_by_stage"] = {}
    for r in falls:
        S["falls_by_stage"][r["fall_stage"]] = S["falls_by_stage"].get(r["fall_stage"], 0) + 1
    S["falls_before_or_in_sit_sequence"] = sum(1 for r in falls if seq(r))
    S["trips_at_mat_edge"] = sum(is_trip(r) for r in rr)
    S["approach_timeouts"] = sum((not r.get("approach_ok")) and not r["fell"] for r in rr)
    sat = [r for r in rr if r["sits"]]
    S["reached_first_sit"] = len(sat)
    first = [r["sits"][0] for r in sat]

    def succ(key, sub="ok", which="first"):
        if which == "first":
            return sum(bool(r["sits"] and r["sits"][0][key][sub] and not r["sits"][0]["fell"]) for r in rr)
        return sum(bool(r["sits"] and any(s[key][sub] and not s["fell"] for s in r["sits"])) for r in rr)
    out = {}
    for key, name in (("nest", "nest"), ("rug", "rug_at_nest_aim"), ("rug_own_aim", "rug_at_rug_aim")):
        for sub in ("ok", "strict"):
            k1 = succ(key, sub)
            out["%s_%s_first_sit" % (name, sub)] = dict(k=k1, n=n, pct=pct(k1, n), ci95=wilson(k1, n))
    k3 = succ("nest", "ok", "any")
    out["nest_ok_within_3_sits"] = dict(k=k3, n=n, pct=pct(k3, n), ci95=wilson(k3, n))
    k3s = succ("nest", "strict", "any")
    out["nest_strict_within_3_sits_note"] = "the duck re-sits only when the lenient rule fails, so strict within 3 is not a separate experiment"
    k2 = sum(bool(len(r["sits"]) >= 1 and any(s["nest"]["ok"] for s in r["sits"][:2])) for r in rr)
    out["nest_ok_within_2_sits"] = dict(k=k2, n=n, pct=pct(k2, n))
    kg = sum(bool(r["sits"] and r["sits"][0]["nest_geom"]["ok"]) for r in rr)
    out["nest_first_sit_by_position_only"] = dict(k=kg, n=n, pct=pct(kg, n))
    S["success"] = out
    S["n_sits_hist"] = {str(k): sum(len(r["sits"]) == k for r in rr) for k in (0, 1, 2, 3)}
    S["sits_not_wholly_on_mat"] = sum(s.get("surface") == "field" for r in rr for s in r["sits"])
    fails = [s for s in first if not s["nest"]["ok"]]
    why = {}
    for s in fails:
        if s["fell"]:
            k = "fell in the sit"
        elif s["nest"]["bridge"]:
            k = "a pin on the wrong zone (bridge)"
        elif s["nest"]["seat_on"] == 0 and s["nest_geom"]["seat_on"] > 0 or s["nest"]["bump_on"] == 0 and s["nest_geom"]["bump_on"] > 0:
            k = "in place but a pin does not touch"
        elif s["nest"]["seat_on"] == 0:
            k = "seat pins off the sun"
        else:
            k = "bumper pins off the ring"
        why[k] = why.get(k, 0) + 1
    S["first_sit_failure_reasons"] = why
    # landing scatter
    if first:
        pre = np.array([s["pre_sit_trunk"] for s in first])
        S["before_sit_trunk_error"] = dict(x_mm=ms(pre[:, 0] - sit_shift[0], 1000), y_mm=ms(pre[:, 1] - sit_shift[1], 1000), yaw_deg=ms(np.degrees(wrap(pre[:, 2] - np.pi))))
        seat = np.array([s["seat_xy"] for s in first])
        rad = np.hypot(seat[:, 0], seat[:, 1]) * 1000
        S["after_torque_off_seat_pins"] = dict(x_mm=ms(seat[:, 0], 1000), y_mm=ms(seat[:, 1], 1000), yaw_deg=ms(np.degrees(wrap(np.array([s["heading"] for s in first]) - np.pi))),
                                               radial_mm=dict(mean=round(float(rad.mean()), 1), p50=round(float(np.percentile(rad, 50)), 1), p95=round(float(np.percentile(rad, 95)), 1), max=round(float(rad.max()), 1)),
                                               within_45mm_pct=pct(int((rad < 45).sum()), len(rad)))
        # where the accuracy goes (first sit): walk-on (perception + creep), turn + stop, sit
        ok = [r for r in sat if "pre_turn" in r]
        tr = np.array([r["pre_turn"]["truth"] for r in ok])
        es = np.array([r["pre_turn"]["est"] for r in ok])
        tg = np.array([r["pre_turn"]["target"] for r in ok])
        e_walk = tr[:, :2] - tg
        e_perc = es[:, :2] - tr[:, :2]
        seat = np.array([r["sits"][0]["seat_xy"] for r in ok])
        pre = np.array([r["sits"][0]["pre_sit_trunk"] for r in ok])
        c, sn = np.cos(pre[:, 2]), np.sin(pre[:, 2])
        pred = pre[:, :2] + np.c_[c * sit_shift[0] - sn * sit_shift[1], sn * sit_shift[0] + c * sit_shift[1]]
        e_sit = seat - pred
        e_turn = seat - e_walk - e_sit
        rms = lambda e: round(float(np.sqrt((e ** 2).sum(1).mean())) * 1000, 1)  # noqa: E731
        bud = {}
        for nm, e in (("walk_on_and_fine_moves", e_walk), ("of_which_pose_stand_in_error", e_perc), ("turn_and_stop", e_turn), ("sit_down", e_sit), ("total_seat_pins", seat)):
            bud[nm] = dict(x_mm=ms(e[:, 0], 1000), y_mm=ms(e[:, 1], 1000), rms_radial_mm=rms(e))
        bud["pre_turn_heading_deg"] = ms(np.degrees(tr[:, 2]))
        bud["imu_yaw_error_at_turn_end_deg"] = ms([r["imu_yaw_err_deg"] for r in ok if "imu_yaw_err_deg" in r])
        S["accuracy_budget_first_sit"] = bud
        S["fine_rounds"] = ms([r.get("fine_rounds", 0) for r in ok])
        mv = {}
        for r in rr:
            for c_, n_ in r.get("moves", []):
                k = "fwd" if c_[0] > 0 else "back" if c_[0] < 0 else "left" if c_[1] > 0 else "yaw+" if c_[2] > 0 else "yaw-"
                mv[k] = mv.get(k, 0) + 1
        S["creep_moves_used"] = mv
        # pins and the sit
        P = {}
        for k in ("seat_L", "seat_R", "bump_L", "bump_R"):
            P[k] = dict(F_N=ms([s["pins"][k]["F"] for s in first], 1, 2), comp_mm=ms([s["pins"][k]["comp_mm"] for s in first], 1, 2),
                        no_touch=sum(s["pins"][k]["F"] <= 0 for s in first))
        S["pins_first_sit"] = P
        S["seat_block_force_N"] = ms([s["contacts_N"].get("sit_seat_trunk_assembly_1_collision", 0.0) for s in first], 1, 2)
        S["soles_force_N"] = ms([s["contacts_N"].get("left_foot_bottom_tpu", 0.0) + s["contacts_N"].get("right_foot_bottom_tpu", 0.0) for s in first], 1, 2)
        S["joints_on_stops_count"] = ms([len(s["stops"]) for s in first])
        S["falls_in_sit"] = sum(s["fell"] for r in rr for s in r["sits"])
    # time
    S["time_s"] = dict(to_first_sit_torque_off=ms([r["t_first_sit_s"] for r in rr if "t_first_sit_s" in r]), to_done_incl_retries=ms([r["t_done_s"] for r in rr if "t_done_s" in r]))
    st = {}
    for r in rr:
        for k, v in r["stages"].items():
            st.setdefault(k, []).append(v)
    S["stage_time_s_mean_when_run"] = {k: round(float(np.mean(v)), 1) for k, v in st.items()}
    S["edge_cross_160mm_s"] = ms([r["edge_cross_s"] for r in rr if "edge_cross_s" in r], 1, 2)
    S["mat_edge_touches_per_run"] = ms([len(r["events"]["edge"]) for r in rr])
    # clearances
    wc = np.array([r["min_wall_clear_mm"][0] for r in sat])
    rc = np.array([r["min_rim_clear_mm"][0] for r in sat])
    if len(wc):
        S["wall_clearance_mm"] = dict(min=round(float(wc.min()), 1), p5=round(float(np.percentile(wc, 5)), 1), mean=round(float(wc.mean()), 1), collisions=int((wc < 0).sum()),
                                      closest_part=max(set(r["min_wall_clear_mm"][1] for r in sat), key=[r["min_wall_clear_mm"][1] for r in sat].count),
                                      closest_stage=max(set(r["min_wall_clear_mm"][2] for r in sat), key=[r["min_wall_clear_mm"][2] for r in sat].count))
        S["rim_clearance_mm"] = dict(min=round(float(rc.min()), 1), p5=round(float(np.percentile(rc, 5)), 1), mean=round(float(rc.mean()), 1), collisions=int((rc < 0).sum()),
                                     closest_part=max(set(r["min_rim_clear_mm"][1] for r in sat), key=[r["min_rim_clear_mm"][1] for r in sat].count))
    S["rim_contacts_physics"] = sum(len(r["events"]["rim"]) > 0 for r in rr)
    S["wall_contacts_physics"] = sum(len(r["events"]["wall"]) > 0 for r in rr)
    # currents
    cur = {}
    for r in rr:
        for k, v in r["currents"].items():
            cur.setdefault(k, []).append((v["bus_mean_A"], v["bus_peak_20ms_A"], v["servo_peak_A"]))
    S["currents_A"] = {k: dict(bus_mean=round(float(np.mean([a[0] for a in v])), 2), bus_peak_20ms_mean=round(float(np.mean([a[1] for a in v])), 2),
                               bus_peak_20ms_max=round(float(np.max([a[1] for a in v])), 2), servo_peak_max=round(float(np.max([a[2] for a in v])), 2)) for k, v in cur.items()}
    # walk-off
    wo = [r["walk_off"] for r in rr if "walk_off" in r]
    S["walk_off"] = dict(n=len(wo), falls=sum(w["fell"] for w in wo), falls_standing_up=sum(w["fell"] and w["fall_stage"] == "walk_off_stand" for w in wo),
                         dist_m=ms([w["dist_m"] for w in wo if not w["fell"]], 1, 2))
    # retries
    f1 = [r for r in sat if not r["sits"][0]["nest"]["ok"] and not r["sits"][0]["fell"]]
    S["retries"] = dict(first_sit_failed=len(f1), fixed_on_sit_2=sum(len(r["sits"]) >= 2 and r["sits"][1]["nest"]["ok"] for r in f1),
                        fixed_on_sit_3=sum(len(r["sits"]) >= 3 and r["sits"][2]["nest"]["ok"] and not r["sits"][1]["nest"]["ok"] for r in f1),
                        fell_in_retry=sum(r["fell"] and r.get("fall_stage") not in ("walk_off", "walk_off_stand") for r in f1))
    return S


def row(cells):
    return "| " + " | ".join(str(c) for c in cells) + " |"


if __name__ == "__main__":
    tags = sys.argv[1:] or ["main"]
    R, meta = load(tags)
    OUT = dict(label="sim pass only", tags=tags, meta=meta, by_noise={}, by_noise_volt={}, by_noise_mu={}, by_volt={}, by_mu={})
    for nz in ("low", "mid", "high"):
        OUT["by_noise"][nz] = summarize([r for r in R if r["cfg"]["noise"] == nz], meta)
        for v in (6.0, 7.2):
            OUT["by_noise_volt"]["%s %.1f" % (nz, v)] = summarize([r for r in R if r["cfg"]["noise"] == nz and r["cfg"]["volt"] == v], meta)
        for mu in (0.6, 0.8, 1.0):
            OUT["by_noise_mu"]["%s %.1f" % (nz, mu)] = summarize([r for r in R if r["cfg"]["noise"] == nz and r["cfg"]["mu"] == mu], meta)
    for v in (6.0, 7.2):
        OUT["by_volt"]["%.1f" % v] = summarize([r for r in R if r["cfg"]["volt"] == v], meta)
    for mu in (0.6, 0.8, 1.0):
        OUT["by_mu"]["%.1f" % mu] = summarize([r for r in R if r["cfg"]["mu"] == mu], meta)
    OUT["all"] = summarize(R, meta)
    json.dump(OUT, open(os.path.join(HERE, "nest_results.json"), "w"), indent=1)

    def sc(S, k):
        d = S["success"][k]
        return "%s %% (%d/%d)" % (d["pct"], d["k"], d["n"])
    print("\n### success\n")
    print(row(["pose noise (1 sigma)", "runs", "nest first sit", "95 % range", "nest within 3 sits", "nest strict (all 4 pins) first sit", "rug first sit, nest aim", "rug first sit, rug aim", "falls in the sequence", "edge trips"]))
    print(row(["---"] * 10))
    for nz in ("low", "mid", "high"):
        S = OUT["by_noise"][nz]
        print(row([NOISE_TXT[nz], S["n"], sc(S, "nest_ok_first_sit"), "%s to %s" % tuple(S["success"]["nest_ok_first_sit"]["ci95"]), sc(S, "nest_ok_within_3_sits"), sc(S, "nest_strict_first_sit"),
                   sc(S, "rug_at_nest_aim_ok_first_sit"), sc(S, "rug_at_rug_aim_ok_first_sit"), S["falls_before_or_in_sit_sequence"], S["trips_at_mat_edge"]]))
    S = OUT["all"]
    print(row(["all", S["n"], sc(S, "nest_ok_first_sit"), "%s to %s" % tuple(S["success"]["nest_ok_first_sit"]["ci95"]), sc(S, "nest_ok_within_3_sits"), sc(S, "nest_strict_first_sit"),
               sc(S, "rug_at_nest_aim_ok_first_sit"), sc(S, "rug_at_rug_aim_ok_first_sit"), S["falls_before_or_in_sit_sequence"], S["trips_at_mat_edge"]]))
    print("\n### by voltage and by mat friction (all noise levels)\n")
    print(row(["slice", "runs", "nest first sit", "nest within 3", "rug first sit (rug aim)", "falls in the sequence", "edge trips", "walk-off falls", "time to first sit s", "edge crossing s"]))
    print(row(["---"] * 10))
    for nm, S in [("%s V" % k, v) for k, v in OUT["by_volt"].items()] + [("mat mu %s" % k, v) for k, v in OUT["by_mu"].items()]:
        print(row([nm, S["n"], sc(S, "nest_ok_first_sit"), sc(S, "nest_ok_within_3_sits"), sc(S, "rug_at_rug_aim_ok_first_sit"), S["falls_before_or_in_sit_sequence"], S["trips_at_mat_edge"],
                   "%d of %d" % (S["walk_off"]["falls"], S["walk_off"]["n"]), S["time_s"]["to_first_sit_torque_off"]["mean"] if S["time_s"]["to_first_sit_torque_off"] else "-",
                   S["edge_cross_160mm_s"]["mean"] if S["edge_cross_160mm_s"] else "-"]))
    print("\n### noise x voltage\n")
    print(row(["noise", "V", "runs", "nest first sit", "nest within 3", "falls in the sequence", "falls by stage"]))
    print(row(["---"] * 7))
    for k, S in OUT["by_noise_volt"].items():
        nz, v = k.split()
        print(row([NOISE_TXT[nz], v, S["n"], sc(S, "nest_ok_first_sit"), sc(S, "nest_ok_within_3_sits"), S["falls_before_or_in_sit_sequence"], json.dumps(S["falls_by_stage"])]))
    print("\n### landing scatter, first sit (mm, deg; mean / 1 sigma)\n")
    print(row(["noise", "before the sit: x", "y", "yaw", "after torque off (seat pins): x", "y", "yaw", "radial mean / p95 / max", "inside 45 mm"]))
    print(row(["---"] * 9))
    f = lambda d: "%s / %s" % (d["mean"], d["sd"])  # noqa: E731
    for nz in ("low", "mid", "high"):
        S = OUT["by_noise"][nz]
        b, a = S["before_sit_trunk_error"], S["after_torque_off_seat_pins"]
        print(row([NOISE_TXT[nz], f(b["x_mm"]), f(b["y_mm"]), f(b["yaw_deg"]), f(a["x_mm"]), f(a["y_mm"]), f(a["yaw_deg"]),
                   "%s / %s / %s" % (a["radial_mm"]["mean"], a["radial_mm"]["p95"], a["radial_mm"]["max"]), "%s %%" % a["within_45mm_pct"]]))
    print("\n### where the accuracy goes, first sit (mm: mean / 1 sigma in x, in y; RMS radial)\n")
    print(row(["noise", "walk-on and fine moves", "of which pose stand-in error", "turn and stop", "sit down", "total at the seat pins"]))
    print(row(["---"] * 6))
    g = lambda d: "x %s, y %s; RMS %s" % (f(d["x_mm"]), f(d["y_mm"]), d["rms_radial_mm"])  # noqa: E731
    for nz in ("low", "mid", "high"):
        B = OUT["by_noise"][nz]["accuracy_budget_first_sit"]
        print(row([NOISE_TXT[nz], g(B["walk_on_and_fine_moves"]), g(B["of_which_pose_stand_in_error"]), g(B["turn_and_stop"]), g(B["sit_down"]), g(B["total_seat_pins"])]))
    print("\n### by voltage: accuracy budget\n")
    for v, S in OUT["by_volt"].items():
        B = S["accuracy_budget_first_sit"]
        print(row([v + " V", g(B["walk_on_and_fine_moves"]), g(B["of_which_pose_stand_in_error"]), g(B["turn_and_stop"]), g(B["sit_down"]), g(B["total_seat_pins"])]))
    print("\n### other (all runs)\n")
    S = OUT["all"]
    for k in ("falls_total", "falls_by_stage", "trips_at_mat_edge", "approach_timeouts", "n_sits_hist", "sits_not_wholly_on_mat", "first_sit_failure_reasons", "retries", "walk_off", "time_s",
              "stage_time_s_mean_when_run", "edge_cross_160mm_s", "mat_edge_touches_per_run", "wall_clearance_mm", "rim_clearance_mm", "rim_contacts_physics", "wall_contacts_physics",
              "currents_A", "pins_first_sit", "seat_block_force_N", "soles_force_N", "joints_on_stops_count", "falls_in_sit", "fine_rounds", "creep_moves_used", "crashed"):
        print("- %s: %s" % (k, json.dumps(S.get(k))))
