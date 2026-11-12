#!/usr/bin/env python3
"""score.py: falls and the flush window for the close-up runs. sim pass only.

The window is calc only, from the flush study: +/-254 mm along the wall, +/-161 mm deep.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
Y_MM, X_MM = 254.0, 161.0


def in_box(xy):
    return abs(xy[1] * 1000.0) <= Y_MM and abs(xy[0] * 1000.0) <= X_MM


def one(path):
    d = json.load(open(path))
    rr = [r for r in d["runs"] if "error" not in r and r.get("cfg")]
    out = dict(file=os.path.basename(path), mode=d.get("mode"), n=len(rr),
               crashed=sum("error" in r for r in d["runs"]), label="sim pass only")
    for name, sel in (("all", lambda r: True),
                      ("6.0", lambda r: r["cfg"]["volt"] == 6.0),
                      ("7.2", lambda r: r["cfg"]["volt"] == 7.2)):
        q = [r for r in rr if sel(r)]
        sat = [r for r in q if r.get("sits")]
        first = sum(in_box(r["sits"][0]["seat_xy"]) for r in sat)
        anyb = sum(any(in_box(s["seat_xy"]) for s in r["sits"]) for r in sat)
        pin1 = sum(bool(r["sits"][0]["ok"] and not r["sits"][0]["fell"]) for r in sat)
        pin3 = sum(any(s["ok"] and not s["fell"] for s in r["sits"]) for r in sat)
        lost = [r["camera"]["last_fix_range_m"] for r in q
                if r.get("camera") and r["camera"].get("last_fix_range_m") is not None]
        heads = [r["camera"]["head_pitch_deg_min"] for r in q
                 if r.get("camera") and r["camera"].get("head_pitch_deg_min") is not None]
        necks = [r["extra"]["look_neck_deg"] for r in q
                 if r.get("extra") and r["extra"].get("look_neck_deg") is not None]
        resight = sum(bool(r.get("extra") and r["extra"].get("resight")) for r in q)
        out[name] = dict(
            n=len(q),
            falls=sum(bool(r.get("fell")) for r in q),
            reached_a_sit=len(sat),
            flush_first=first,
            flush_within_3=anyb,
            old_pins_first=pin1,
            old_pins_within_3=pin3,
            resight=resight,
            last_fix_m=None if not lost else dict(
                n=len(lost), median=round(float(np.median(lost)), 3),
                p10=round(float(np.percentile(lost, 10)), 3),
                p90=round(float(np.percentile(lost, 90)), 3)),
            head_pitch_deg_min=None if not heads else round(float(min(heads)), 1),
            look_neck_deg_min=None if not necks else round(float(min(necks)), 1),
        )
    return out


if __name__ == "__main__":
    paths = sys.argv[1:] or [os.path.join(HERE, "close_%s.json" % m) for m in ("pitch", "marker", "wide", "turn")]
    blocks = []
    for p in paths:
        if not os.path.exists(p):
            continue
        b = one(p)
        blocks.append(b)
        print(json.dumps(b, indent=1))
    if blocks:
        json.dump(blocks, open(os.path.join(HERE, "summary.json"), "w"), indent=1)
        print("wrote", os.path.join(HERE, "summary.json"))
