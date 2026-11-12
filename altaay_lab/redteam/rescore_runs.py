#!/usr/bin/env python3
"""Hostile rescore of the nest runs already on disk. calc only on those seats.

Reused, not rewritten:
  twin/dock/nest/sim/nestlib.py score_nest (the pin rule and the constants below)
  twin/dock/blind/score.py in_box (the flush window, +/-254 mm by +/-161 mm)
  twin/dock/blind/blind_runs_b190.json (PR 45, the merged 190 mm file)
  twin/dock/closeup/close_marker.json (PR 47, the wall-card file)

No new physics. The wall and the rim are not given a contact here. This script only
moves the cloth relative to seats the sims already stored.
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, ".."))
BLIND = os.path.join(LAB, "twin", "dock", "blind", "blind_runs_b190.json")
CARD = os.path.join(LAB, "twin", "dock", "closeup", "close_marker.json")

# nestlib.py, the approved 190 mm concept. A pin counts 3 mm inside its zone.
WALL_X = 0.190
RC, GAP, ROUT = 0.050, 0.032, 0.235
RING_BACK = 0.074
TIP_M = 0.003
# blind/score.py, the flush study section 6 box.
Y_MM, X_MM = 254.0, 161.0
SUN_R_MM = (RC - TIP_M) * 1000.0  # 47 mm, the seat-pin test


def score_nest(pins, dx=0.0, dy=0.0, wall_x=WALL_X):
    """Same rule as nestlib.score_nest, after the sun moves by (dx, dy) in the old frame.
    The wall moves with the sun, so wall_x stays 0.190 unless the caller changes it.
    """
    def xy(v):
        return (v["xy"][0] - dx, v["xy"][1] - dy)

    shifted = {k: xy(v) for k, v in pins.items()}
    r = {k: math.hypot(*p) for k, p in shifted.items()}
    made = {k: v["F"] > 0 for k, v in pins.items()}
    ring_ok = {k: (wall_x - shifted[k][0]) > RING_BACK + TIP_M for k in pins}
    ring_any = {k: (wall_x - shifted[k][0]) > RING_BACK - TIP_M for k in pins}
    seat = [k for k in pins if k.startswith("seat")]
    bump = [k for k in pins if k.startswith("bump")]
    seat_on = [made[k] and r[k] < RC - TIP_M for k in seat]
    seat_bad = [made[k] and (RC + GAP - TIP_M < r[k] < ROUT + TIP_M) and ring_any[k] for k in seat]
    bump_on = [made[k] and (RC + GAP + TIP_M < r[k] < ROUT - TIP_M) and ring_ok[k] for k in bump]
    bump_bad = [made[k] and r[k] < RC + TIP_M for k in bump]
    bridge = any(seat_bad) or any(bump_bad)
    return bool(any(seat_on) and any(bump_on) and not bridge)


def in_box(xy, dx=0.0, dy=0.0):
    x = (xy[0] - dx) * 1000.0
    y = (xy[1] - dy) * 1000.0
    return abs(y) <= Y_MM and abs(x) <= X_MM


def pct(n, d):
    return None if not d else round(100.0 * n / d, 1)


def blind_block(runs):
    n = len(runs)
    mismatch = 0
    first_old = 0
    within_old = 0
    first_box = 0
    within_box = 0
    falls = 0
    sat = 0
    wall_neg = 0
    wall_neg_and_box = 0
    wall_neg_and_old = 0
    radii = []
    by = {}
    for r in runs:
        falls += int(bool(r.get("fell")))
        sits = r.get("sits") or []
        if sits:
            sat += 1
            radii.append(math.hypot(*sits[0]["seat_xy"]) * 1000.0)
        clr = r.get("min_wall_clear_mm")
        neg = isinstance(clr, list) and clr and clr[0] < 0
        wall_neg += int(bool(neg))
        box1 = bool(sits) and in_box(sits[0]["seat_xy"])
        box3 = any(in_box(s["seat_xy"]) for s in sits)
        first_box += int(box1)
        within_box += int(box3)
        # check the copied rule against the stored nest.ok at zero shift
        if sits:
            mine = score_nest(sits[0]["pins"])
            stored = bool(sits[0]["nest"]["ok"])
            if mine != stored:
                mismatch += 1
        old1 = bool(sits) and sits[0]["nest"]["ok"] and not sits[0]["fell"]
        old3 = any(s["nest"]["ok"] and not s["fell"] for s in sits)
        first_old += int(old1)
        within_old += int(old3)
        if neg and box1:
            wall_neg_and_box += 1
        if neg and old1:
            wall_neg_and_old += 1
        key = (r["cfg"]["volt"], r["cfg"]["mu"])
        cell = by.setdefault(key, dict(n=0, old=0, box=0, falls=0))
        cell["n"] += 1
        cell["old"] += int(old1)
        cell["box"] += int(box1)
        cell["falls"] += int(bool(r.get("fell")))

    def moved(dx, dy, wall_x=WALL_X):
        old = 0
        box = 0
        for r in runs:
            sits = r.get("sits") or []
            if not sits:
                continue
            s0 = sits[0]
            if score_nest(s0["pins"], dx, dy, wall_x) and not s0["fell"]:
                old += 1
            if in_box(s0["seat_xy"], dx, dy):
                box += 1
        return dict(first_old_pins=old, first_flush_box=box, of=n)

    radii.sort()
    def q(p):
        if not radii:
            return None
        i = min(len(radii) - 1, max(0, int(round((len(radii) - 1) * p))))
        return round(radii[i], 1)

    splits = []
    for (volt, mu), cell in sorted(by.items()):
        splits.append(dict(volt=volt, mu=mu, **cell))

    shifts = {
        "unmoved": moved(0, 0),
        "along_wall_50mm": moved(0, 0.050),
        "along_wall_100mm": moved(0, 0.100),
        "along_wall_150mm": moved(0, 0.150),
        "into_room_50mm": moved(-0.050, 0),
        "into_room_100mm": moved(-0.100, 0),
        "toward_wall_50mm": moved(0.050, 0),
    }
    return dict(
        n=n, falls=falls, reached_a_sit=sat,
        stored_old_pins_first=first_old, stored_old_pins_within_3=within_old,
        flush_box_first=first_box, flush_box_within_3=within_box,
        rule_mismatches_on_first_sit=mismatch,
        min_wall_clear_negative=wall_neg,
        negative_wall_and_flush_first=wall_neg_and_box,
        negative_wall_and_old_pins_first=wall_neg_and_old,
        first_seat_radius_mm=dict(n=len(radii), p50=q(0.50), p95=q(0.95)),
        by_volt_mu=splits,
        nest_moved=shifts,
    )


def card_block(runs):
    """The card file stores the seat centre and the stored pin flag, not the four pin tips.
    A moved sun is scored on the seat centre only. A centre past 47 mm cannot be a seat pin
    on the sun. That is a bound, not nestlib.score_nest.
    """
    n = len(runs)

    def one(dx, dy):
        box = 0
        centre_in_sun = 0
        stored_ok = 0
        for r in runs:
            sits = r.get("sits") or []
            if not sits:
                continue
            s0 = sits[0]
            if in_box(s0["seat_xy"], dx, dy):
                box += 1
            x = s0["seat_xy"][0] - dx
            y = s0["seat_xy"][1] - dy
            if math.hypot(x, y) * 1000.0 <= SUN_R_MM and not s0["fell"]:
                centre_in_sun += 1
            if dx == 0 and dy == 0 and s0.get("ok") and not s0["fell"]:
                stored_ok += 1
        return dict(first_flush_box=box, seat_centre_inside_47mm=centre_in_sun,
                    stored_pin_ok_first=stored_ok if dx == 0 and dy == 0 else None, of=n)

    return dict(
        n=n,
        falls=sum(int(bool(r.get("fell"))) for r in runs),
        note="seat centre only; the four pin tips are not in this file",
        unmoved=one(0, 0),
        along_wall_50mm=one(0, 0.050),
        along_wall_100mm=one(0, 0.100),
        into_room_100mm=one(-0.100, 0),
        toward_wall_50mm=one(0.050, 0),
    )


def main():
    blind = json.load(open(BLIND))
    card = json.load(open(CARD))
    out = dict(
        label="calc only on seats from sim pass only runs",
        reused=[
            "altaay_lab/twin/dock/nest/sim/nestlib.py score_nest",
            "altaay_lab/twin/dock/blind/score.py flush window",
            "altaay_lab/twin/dock/blind/blind_runs_b190.json",
            "altaay_lab/twin/dock/closeup/close_marker.json",
        ],
        blind_190mm=blind_block(blind["runs"]),
        wall_card=card_block(card["runs"]),
    )
    dest = os.path.join(HERE, "rescore.json")
    json.dump(out, open(dest, "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
