#!/usr/bin/env python3
"""Slice the printed dock parts with the lab's light PLA profile (print/config_light stack of print/slice.py: printer,
2-wall PLA print, Overture Easy PLA filament) and write stl/slice.json (grams and hours per part; calc only).

Run: python3 altaay_lab/twin/dock/dock_slice.py --scratch <folder outside the repo>
G-code and the oriented STLs stay in the scratch folder (lab rule: no G-code in git).
"""
import argparse, json, os, re, subprocess
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(os.path.dirname(HERE))
CFG = os.path.join(LAB, "print", "config")
STACK = ["printer_generic.ini", "pla_print.ini", "filament_easy_pla.ini"]
ORIENT = {  # rotation (axis, degrees) that puts the print face on the bed
    "dock_seat_top": ((1, 0, 0), 180), "dock_spine": ((1, 0, 0), 90), "dock_paddle": ((0, 1, 0), -90),
    "dock_paddle_carrier": ((0, 1, 0), 90), "dock_spring_drum": ((1, 0, 0), 90),
    **{f"dock_column_{s}{i}": ((0, 1, 0), -90) for s in "lr" for i in (1, 2, 3)},
}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--scratch", required=True); a = ap.parse_args()
    os.makedirs(a.scratch, exist_ok=True)
    pj = json.load(open(os.path.join(HERE, "stl", "parts.json")))
    out = {}
    for name, r in pj.items():
        if not r.get("printed"):
            continue
        m = trimesh.load(os.path.join(HERE, "stl", name + ".stl"), force="mesh")
        if name in ORIENT:
            ax, deg = ORIENT[name]
            m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(deg), ax))
        m.apply_translation(-m.bounds[0])
        m.apply_translation((110 - m.extents[0] / 2, 110 - m.extents[1] / 2, 0))
        stl = os.path.join(a.scratch, name + "_print.stl"); m.export(stl)
        gc = os.path.join(a.scratch, name + ".gcode")
        cmd = ["prusa-slicer", "--export-gcode", "--output", gc]
        for c in STACK:
            cmd += ["--load", os.path.join(CFG, c)]
        cmd += ["--dont-arrange", stl]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        txt = open(gc, errors="ignore").read() if os.path.exists(gc) else ""
        g = re.search(r"; total filament used \[g\] = ([0-9.]+)", txt) or re.search(r"; filament used \[g\] = ([0-9.]+)", txt)
        t = re.search(r"; estimated printing time \(normal mode\) = (.+)", txt)
        h = None
        if t:
            parts = dict((u, float(v)) for v, u in re.findall(r"([0-9]+)([dhms])", t.group(1)))
            h = parts.get("d", 0) * 24 + parts.get("h", 0) + parts.get("m", 0) / 60 + parts.get("s", 0) / 3600
        out[name] = dict(grams=float(g.group(1)) if g else None, hours=round(h, 2) if h else None, qty=r["qty"],
                         orient=ORIENT.get(name, ((0, 0, 1), 0)), ok=p.returncode == 0, err=(p.stderr[-300:] if p.returncode else ""))
        print(name, out[name]["grams"], out[name]["hours"], out[name]["ok"], flush=True)
    tot_g = sum((v["grams"] or 0) * v["qty"] for v in out.values()); tot_h = sum((v["hours"] or 0) * v["qty"] for v in out.values())
    json.dump(dict(profile="print/config: " + " + ".join(STACK) + " (the light PLA profile, D22)", parts=out,
                   total_g=round(tot_g, 1), total_h=round(tot_h, 1), label="calc only (slicer estimate)"),
              open(os.path.join(HERE, "stl", "slice.json"), "w"), indent=1)
    print("total", round(tot_g, 1), "g", round(tot_h, 1), "h")


if __name__ == "__main__":
    main()
