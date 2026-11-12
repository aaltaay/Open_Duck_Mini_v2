#!/usr/bin/env python3
"""score.py: falls, charge, and the flush-contact window. sim pass only for the counts.
The window is calc only, from the flush study: +/-254 mm along the wall, +/-161 mm deep.
"""
import json
import os
import sys

import numpy as np

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
# flush study, section 6, calc only. Not edited here.
Y_MM, X_MM = 254.0, 161.0


def ok_charge(sits, which):
    if not sits:
        return False
    if which == 1:
        return bool(sits[0]["nest"]["ok"] and not sits[0]["fell"])
    return any(s["nest"]["ok"] and not s["fell"] for s in sits)


def in_box(xy):
    x, y = xy[0] * 1000.0, xy[1] * 1000.0
    return abs(y) <= Y_MM and abs(x) <= X_MM


def one(path):
    d = json.load(open(path))
    rr = [r for r in d["runs"] if "error" not in r]
    out = dict(file=os.path.basename(path), n=len(rr), crashed=sum("error" in r for r in d["runs"]),
               wall_x_m=d.get("wall_x_m"))
    for name, sel in (("all", lambda r: True), ("6.0", lambda r: r["cfg"]["volt"] == 6.0), ("7.2", lambda r: r["cfg"]["volt"] == 7.2)):
        q = [r for r in rr if sel(r)]
        sat = [r for r in q if r.get("sits")]
        first_box = sum(in_box(r["sits"][0]["seat_xy"]) for r in sat)
        any_box = sum(any(in_box(s["seat_xy"]) for s in r["sits"]) for r in sat)
        lost = [r["camera"]["last_fix_range_m"] for r in q if r.get("camera") and r["camera"].get("last_fix_range_m") is not None]
        out[name] = dict(
            n=len(q),
            falls=sum(bool(r.get("fell")) for r in q),
            first_sit=sum(ok_charge(r.get("sits") or [], 1) for r in q),
            within_3=sum(ok_charge(r.get("sits") or [], 3) for r in q),
            reached_a_sit=len(sat),
            first_seat_in_window=first_box,
            any_sit_in_window=any_box,
            last_fix_m=None if not lost else dict(n=len(lost), median=round(float(np.median(lost)), 3),
                                                   p10=round(float(np.percentile(lost, 10)), 3),
                                                   p90=round(float(np.percentile(lost, 90)), 3)),
        )
    return out


if __name__ == "__main__":
    blocks = []
    for p in sys.argv[1:]:
        b = one(p if os.path.isabs(p) else os.path.join(HERE, p))
        blocks.append(b)
        print(json.dumps(b, indent=1))
    if blocks:
        json.dump(blocks, open(os.path.join(HERE, "score.json"), "w"), indent=1)
