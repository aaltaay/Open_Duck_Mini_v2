#!/usr/bin/env python3
"""Score stored nest seats against the contact windows. No new MuJoCo run.

The seats are the archived 540-seed runs. This file only reads them.
Counts of those runs are sim pass only. The window tests on those seats are calc only.

Windows, all in the nest frame (sun at the origin, x toward the wall, y along the wall):
  flush box     the belly field, +/-254 mm along the wall and +/-161 mm deep
                (flush study section 6, calc only)
  stripe phase  the same box, and the five wells each land on one polarity
                with the fixed stripe phase this CAD uses (the flush study's band rule)
  r45           seat centre within 45 mm of the sun (the old sun window's radius)
  r16           seat centre within 16.5 mm (largest magnetic housing on the EDAC sheet)
  r8            seat centre within 8.25 mm (half of that housing)
  r10           seat centre within 10 mm (phone-coil offset in NATURAL_DOCK_IDEAS.md section 4.3)

Heading for the stripe test is the stored heading minus pi, in degrees. The flush
study's 0 deg is the duck facing the room. Files that did not store a heading skip
that test.
"""
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
DOCK = os.path.join(REPO, "altaay_lab", "twin", "dock")

# Flush study, draw_flush.py. Not edited. The rule is copied so this folder does not write there.
WELLS_Y = np.array([-24.0, -12.0, 0.0, 12.0, 24.0])
WELL_R = 1.5
STRIPE = 20.0
GAP = 5.0
PERIOD = STRIPE + GAP
Y_MM, X_MM = 254.0, 161.0


def band(y):
    p = np.mod(y, PERIOD)
    if p >= STRIPE:
        return "G"
    return "P" if int(np.floor(y / PERIOD)) % 2 == 0 else "M"


# Both poles of this CAD run from x = -180 to x = 180. A well whose disc
# leaves that range is not on foil, even if its y phase is right.
FOIL_X = 180.0


def stripe_ok(heading_deg, phase, seat_x=0.0):
    """The flush study's classify(), fixed phase, plus the real foil x range.
    A well on the gap is a miss, not a fail. Fail means a well bridges plus
    and minus, a disc leaves the foil in x, or one polarity is missing.
    Phase is the seat centre's y.
    """
    th = np.deg2rad(heading_deg)
    wy = WELLS_Y * np.cos(th) + phase
    wx = WELLS_Y * np.sin(th) + seat_x
    hits = []
    for x, y in zip(wx, wy):
        if abs(x) + WELL_R > FOIL_X:
            return False
        labs = [band(y - WELL_R), band(y), band(y + WELL_R)]
        if labs[0] == labs[1] == labs[2] and labs[0] in ("P", "M"):
            hits.append(labs[0])
        elif "P" in labs and "M" in labs:
            return False
        else:
            hits.append("miss")
    return hits.count("P") >= 1 and hits.count("M") >= 1


def heading_deg(h):
    if h is None:
        return None
    err = (float(h) - math.pi + math.pi) % (2 * math.pi) - math.pi
    return math.degrees(err)


def load_runs(path, volt=None):
    d = json.load(open(path))
    out = []
    for r in d["runs"]:
        if "error" in r:
            continue
        if volt is not None and r.get("cfg", {}).get("volt") != volt:
            continue
        out.append(r)
    return out, d


def first_sit(r):
    sits = r.get("sits") or []
    if not sits:
        return None
    return sits[0]


def xy_mm(sit):
    x, y = sit["seat_xy"]
    return float(x) * 1000.0, float(y) * 1000.0


def in_box(x, y):
    return abs(y) <= Y_MM and abs(x) <= X_MM


def score_runs(runs):
    n = len(runs)
    falls = sum(bool(r.get("fell")) for r in runs)
    sat = [r for r in runs if r.get("sits")]
    rows = []
    for r in sat:
        s = r["sits"][0]
        x, y = xy_mm(s)
        h = heading_deg(s.get("heading"))
        rad = math.hypot(x, y)
        box = in_box(x, y)
        phase = stripe_ok(h, y, x) if h is not None else None
        rows.append(dict(x=x, y=y, h=h, rad=rad, box=box, phase=phase,
                         old=bool(s.get("ok") if "ok" in s else (s.get("nest") or {}).get("ok")),
                         fell=bool(s.get("fell"))))
    any_box = 0
    any_phase = 0
    for r in sat:
        hit_b = False
        hit_p = False
        for s in r["sits"]:
            x, y = xy_mm(s)
            if in_box(x, y):
                hit_b = True
                h = heading_deg(s.get("heading"))
                if h is not None and stripe_ok(h, y, x):
                    hit_p = True
        any_box += hit_b
        any_phase += hit_p
    rads = np.array([t["rad"] for t in rows]) if rows else np.array([])
    heads = [t["h"] for t in rows if t["h"] is not None]

    def cnt(pred):
        return int(sum(1 for t in rows if pred(t) and not t["fell"]))

    out = dict(
        n=n,
        falls=int(falls),
        reached=len(sat),
        flush_first=cnt(lambda t: t["box"]),
        flush_within_3=int(any_box),
        stripe_first=None if not heads else cnt(lambda t: t["box"] and t["phase"]),
        stripe_within_3=None if not heads else int(any_phase),
        old_pins_first=cnt(lambda t: t["old"]),
        r45_first=cnt(lambda t: t["rad"] <= 45.0),
        r16_first=cnt(lambda t: t["rad"] <= 16.5),
        r8_first=cnt(lambda t: t["rad"] <= 8.25),
        r10_first=cnt(lambda t: t["rad"] <= 10.0),
        heading_over_46=None if not heads else int(sum(abs(h) > 46.0 for h in heads)),
        heading_abs_max=None if not heads else round(max(abs(h) for h in heads), 1),
    )
    if len(rads):
        out["radial_mm"] = dict(
            n=int(len(rads)),
            median=round(float(np.median(rads)), 1),
            p95=round(float(np.percentile(rads, 95)), 1),
            worst=round(float(rads.max()), 1),
        )
    return out


def main():
    blind, _ = load_runs(os.path.join(DOCK, "blind", "blind_runs_b190.json"))
    card, _ = load_runs(os.path.join(DOCK, "closeup", "close_marker.json"))
    steps, _ = load_runs(os.path.join(DOCK, "nest", "sim", "v3", "nest_runs_steps.json"), volt=6.0)
    aim, _ = load_runs(os.path.join(DOCK, "nest", "sim", "v3", "nest_runs_aim20full.json"))
    true_pose = steps + aim
    report = dict(
        label="sim pass only for the run counts; calc only for the window tests on those seats",
        note="No new physics run. Same seeds as the nest matrices.",
        blind_190=score_runs(blind),
        wall_card=score_runs(card),
        true_pose_v3=score_runs(true_pose),
    )
    # The true-pose splice must be 270 + 270.
    report["true_pose_v3"]["splice"] = "6.0 V from nest_runs_steps.json, 7.2 V from nest_runs_aim20full.json"
    path = os.path.join(HERE, "score.json")
    with open(path, "w") as fh:
        json.dump(report, fh, indent=1)
        fh.write("\n")
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
