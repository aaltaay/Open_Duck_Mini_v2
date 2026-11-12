#!/usr/bin/env python3
"""summarize.py: the same counts as sim/v2/compare.py, for one v3 result file. sim pass only.

  PYTHONDONTWRITEBYTECODE=1 python3 summarize.py nest_runs_mix.json [more.json ...]
Writes summary.json (no per-run traces) next to the first file's folder, and prints a short table.
"""
import json
import os
import sys

import numpy as np

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.join(os.path.dirname(HERE), "v2")
sys.path.insert(0, V2)
import compare as C  # noqa: E402


def one(path):
    runs, meta = C.load(path)
    err = [r for r in runs if "error" in r]
    ok = [r for r in runs if "error" not in r]
    slices = {k: C.extra([r for r in ok if f(r)]) for k, f in C.SL}
    return dict(file=os.path.basename(path), meta={k: v for k, v in meta.items() if k != "params_v2_default"},
                crashed=len(err), errors=[r.get("error") for r in err[:5]], slices=slices)


def line(S, key):
    d = S[key]
    return "%s %% (%d of %d)" % (d["pct"], d["k"], d["n"])


def show(block):
    print("==", block["file"], "crashed", block["crashed"])
    meta = block["meta"]
    print("edge", meta.get("edge"), "wall_m", meta.get("wall_x_m"), "aim_mm", meta.get("aim_mm_right_at_7v2"),
          "only_volt", meta.get("only_volt"))
    for name in ("all", "6.0 V", "7.2 V"):
        S = block["slices"][name]
        w = S.get("wall_mm") or {}
        rm = S.get("rim_mm") or {}
        print(" ", name, "n", S["n"], "falls", S["falls_all"], "by", S["falls_by_stage"],
              "first", line(S, "charge_first_sit"), "within3", line(S, "charge_within_3"),
              "gave_up", S["never_reached_the_sit_no_fall"],
              "wall_worst", w.get("min"), "rim_worst", rm.get("min"),
              "inside", S.get("runs_inside_wall_or_rim"))


if __name__ == "__main__":
    blocks = [one(p if os.path.isabs(p) else os.path.join(HERE, p)) for p in sys.argv[1:]]
    for b in blocks:
        show(b)
    # drop nothing: slices are small. Write beside this script, one file per input plus a combined copy of the last call.
    out = {}
    for b in blocks:
        tag = os.path.splitext(b["file"])[0].replace("nest_runs_", "")
        out[tag] = b
        json.dump(b, open(os.path.join(HERE, "summary_%s.json" % tag), "w"), indent=1)
        print("wrote summary_%s.json" % tag)
