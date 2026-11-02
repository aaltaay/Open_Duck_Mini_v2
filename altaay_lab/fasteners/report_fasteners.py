#!/usr/bin/env python3
"""Write FASTENERS.md and fasteners.csv from fasteners.json (after make_fasteners.py and sweep_fasteners.py).

  python3 altaay_lab/fasteners/report_fasteners.py [--time "2026-11-02 1:23 AM ET"]

Also marks the D18 screw (outer roll_motor_bottom screw per leg, found by the sweep as a hit against
roll_to_pitch) as LEAVE OUT, and recounts every spec against BOM.md lines 16 and 17a to 17i.
"""
import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from make_fasteners import write_csv, bom_lines, SRC  # noqa: E402

GROUPS = [("left_leg", "Left leg (roll_to_pitch down to the foot)"), ("right_leg", "Right leg (roll_to_pitch down to the foot)"),
          ("trunk_hips", "Trunk and hips (trunk shell, hip yaw and hip roll stages, battery lid)"),
          ("neck", "Neck (neck pitch, head pitch, head yaw stages)"), ("head", "Head (shell, floor, head roll stage, eyes, speaker, antennas)"),
          ("electronics", "Electronics (Pi, servo adapter, IMU, charger, camera)")]


def short_part(p):
    return (p or "").replace("wj-wk00-0122topcabinetcase_95", "servo top case").replace("wj-wk00-0124bottomcase_45", "servo bottom case") \
        .replace("raspberrypizerow", "Pi Zero 2 W").replace("drive_palonier", "drive horn").replace("passive_palonier", "idle horn") \
        .replace("board", "servo adapter (board.stl)").replace("bno055", "BNO055").replace("usb_c_charger", "USB-C charger")


def fmt(x, nd=1):
    return "" if x is None else (("%." + str(nd) + "f") % x)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--time", default="", help="clock time to print (run TZ=America/New_York date first)")
    a = ap.parse_args()
    path = os.path.join(HERE, "fasteners.json")
    D = json.load(open(path))
    R = D["fasteners"]
    screws = [r for r in R if r["kind"] == "screw"]
    inserts = [r for r in R if r["kind"] == "insert"]
    hits = D.get("sweep", {}).get("hits", [])
    if not hits and "sweep" not in D:
        sys.exit("run sweep_fasteners.py first")
    # ---- D18: the roll_motor_bottom screw whose head hits roll_to_pitch over the hip roll range
    d18 = []
    for h in hits:
        r = next(x for x in screws if x["id"] == h["id"])
        if r.get("part") == "roll_motor_bottom" and h["kind"] == "head" and "roll_to_pitch" in h["against"] \
                and h["where"].endswith("hip_roll"):
            r["status"] = "LEAVE OUT (D18)"
            r["leave_out"] = True
            d18.append((r, h))
    # ---- button heads where the sweep shows a DIN 912 head is hit first and an ISO 7380 head clears
    from make_fasteners import COLORS
    D["meta"]["colors"].update(COLORS)
    for r in screws:
        if r.get("color_key") in D["meta"]["colors"]:
            r["color"] = D["meta"]["colors"][r["color_key"]]
    D["meta"]["head_models"]["M3_iso7380"] = [5.7, 1.65]
    button = []
    for r in screws:
        mine = [h for h in hits if h["id"] == r["id"] and h.get("cls") in ("screw", "static overlap")
                and not (r.get("status") == "LEAVE OUT (D18)")]
        low = (r.get("sweep") or {}).get("with_iso7380_head") or {}
        if not mine or not (r.get("head") or {}).get("type", "").endswith("din912") or r.get("size") != "M3":
            continue
        fixed = [h for h in mine if h["against"] in (low.get("against"),) or "roll_to_pitch" in h["against"]]
        if low and (low.get("clearance_mm", -1) > 0 or "roll_to_pitch" not in low.get("against", "")):
            if any("roll_to_pitch" in h["against"] for h in mine):
                r["spec"] = r["spec"].replace("DIN 912 A2", "ISO 7380 A2 button head")
                r["head"] = dict(type="M3_iso7380", dk=5.7, k=1.65)
                r["line"], r["supply"], r["color_key"] = None, "NEW LINE: M3x6 ISO 7380 A2 button head", "M3x6 button"
                r["color"] = COLORS["M3x6 button"]
                r["notes"] = r.get("notes", []) + ["DIN 912 head is hit by roll_to_pitch (%.2f mm); ISO 7380 head (k 1.65) "
                                                   "clears it in the sweep, see FASTENERS.md section 3" % min(h["worst_mm"] for h in mine)]
                button.append(r["id"])
    # ---- counts
    fitted = [r for r in screws if r.get("status") not in ("NOT FITTED", "LEAVE OUT (D18)")]
    by_spec = Counter(r["spec"] for r in fitted)
    supply = Counter()
    for r in fitted:
        if r.get("source") == "servo_case":
            supply["factory (inside the servos)"] += 1
        elif (r.get("line") or "") == "1":
            supply["servo bag (BOM 1)"] += 1
        elif (r.get("line") or "") == "14":
            supply["SG90 bag (BOM 14)"] += 1
        else:
            supply["to buy (BOM 17a to 17l)"] += 1
    bl = bom_lines()
    need = defaultdict(Counter)
    for r in fitted:
        ln = r.get("line")
        if r.get("source") == "servo_case" or ln in ("1", "14"):
            continue
        need[ln or "new"][r["spec"].split(" + ")[0]] += 1
        if r.get("washer"):
            need["17l"]["M2.5 flat washer, 0.3 mm"] += r["washer"].get("n", 1)
    need["16"]["M3 heat-set insert"] = len(inserts)
    bom_rows = []
    for ln in sorted(set(list(need)) | {k for k in bl if k == "16" or k.startswith("17")}, key=lambda s: (s == "new", s)):
        b = bl.get(ln, {})
        bn = re.match(r"\d+", b.get("need", "") or "")
        bn = int(bn.group(0)) if bn else None
        cnt = sum(need[ln].values())
        bom_rows.append(dict(line=ln, item=b.get("item", "(no line yet)"), bom_need=bn, bom_buy=b.get("buy"), count=cnt,
                             specs=", ".join("%s %d" % kv for kv in sorted(need[ln].items())), ok=(bn == cnt)))
    D["bom"] = bom_rows
    with open(path, "w") as fh:
        json.dump(D, fh, separators=(",", ":"))
    write_csv(os.path.join(HERE, "fasteners.csv"), R)

    # ---- markdown
    L = []
    w = L.append
    w("# FASTENERS")
    w("")
    w("Every screw, insert, washer, nut, pin and standoff of Open Duck Mini v2, found in the CAD, specified, checked and posed "
      "for the exploded view. Generated by `report_fasteners.py` from `fasteners.json`%s; do not edit by hand." % (
          (" (" + a.time + ")") if a.time else ""))
    w("")
    w("Regenerate (scratch folder outside the repo): `python3 altaay_lab/fasteners/make_fasteners.py --scratch S`, then "
      "`sweep_fasteners.py --scratch S`, `report_fasteners.py`, `render_fasteners.py --scratch S`.")
    w("")
    w("Files: fasteners.json (every instance, the viewer reads it, see VIEWER_NOTE.md), fasteners.csv (same, flat), "
      "fasteners_assembled.png and fasteners_exploded.png (every fitted fastener coloured by spec), scripts fastlib.py, "
      "make_fasteners.py, sweep_fasteners.py, report_fasteners.py (with report_text.py, narrative.py), render_fasteners.py.")
    w("")
    w("Tags: [U] upstream file, [L] lab measurement or script in this repo, [I] internet page. Scene: robot.urdf (b23317a) at "
      "zero joint angles in mm, print/ STLs (730c14b) swapped in, head internals in the head.stl frame (same as viewer/). "
      "All geometry numbers are [L] from these scripts unless tagged.")
    w("")
    w("## 1. Totals")
    w("")
    w("| Kind | Count | Source |")
    w("|---|---|---|")
    tot_scr = len(fitted)
    w("| Screws to fit | %d | [L] fasteners.json |" % tot_scr)
    for k, v in supply.most_common():
        w("| . of which %s | %d | [L] |" % (k, v))
    w("| Screws left out on purpose | %d | D18 hip roll screws %d; idle horn screws not fitted %d |" % (
        len(screws) - tot_scr, len(d18), sum(1 for r in screws if r.get("status") == "NOT FITTED")))
    w("| M3 heat-set inserts | %d | [L] bores 3.8 to 4.3 mm, 5 to 8 mm deep, in printed parts |" % len(inserts))
    w("| Washers | %d | eye screws only, two 0.3 mm under each head (section 3) |" % sum(r["washer"].get("n", 1) for r in fitted if r.get("washer")))
    w("| Nuts | 0 | [L] no hex pocket in any STL (feat3d finds %d hex features) |" % D["meta"]["scene"]["hex_features"])
    w("| Pins, dowels | 0 | [L] no pin hole; the antenna rods sit in 1.8 mm holes of the antenna holders (no BOM line) |")
    w("| Standoffs | 0 to buy | the servo adapter sits on 4 bosses printed into trunk_top (MOUNTING.md) |")
    w("| Bearings (not fasteners) | 3 | BOM 18, seats listed in section 7 |")
    w("")
    w("## 2. Counts per spec against BOM.md")
    w("")
    w("| BOM line | Item | BOM Need | Counted here | Specs counted | Match |")
    w("|---|---|---|---|---|---|")
    for b in bom_rows:
        w("| %s | %s | %s | %d | %s | %s |" % (b["line"], b["item"], b["bom_need"], b["count"], b["specs"], "yes" if b["ok"] else "**no**"))
    w("")
    w("Bag and factory screws (not on a buy line): " + ", ".join("%s %d" % kv for kv in sorted(Counter(
        r["spec"] for r in fitted if r.get("source") == "servo_case" or r.get("line") in ("1", "14")).items())) + ".")
    w("")
    D["_d18"] = [(r["id"], h["worst_mm"]) for r, h in d18]
    with open(os.path.join(HERE, "_report_state.json"), "w") as fh:
        json.dump(dict(d18=D["_d18"], bom=bom_rows, by_spec=by_spec, supply=supply), fh)
    from narrative import narrative
    F_, servo_, rules_, edits_ = narrative(D, screws, inserts, fitted, hits, d18, bom_rows, SRC)
    D["_findings"], D["_servo_text"], D["_rules_text"], D["_edits_text"] = F_, servo_, rules_, edits_
    # sections 3+ are appended by report_text() below
    L += report_text(D, screws, inserts, fitted, hits, d18, bom_rows)
    with open(os.path.join(HERE, "FASTENERS.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")
    os.remove(os.path.join(HERE, "_report_state.json"))
    print("FASTENERS.md written: %d lines; fitted screws %d, inserts %d, D18 %s" % (len(L), tot_scr, len(inserts), [r["id"] for r, _ in d18]))
    for b in bom_rows:
        print("  %-4s %-26s need %-5s counted %-4d %s" % (b["line"], b["item"][:26], b["bom_need"], b["count"], "ok" if b["ok"] else "MISMATCH"))


def report_text(D, screws, inserts, fitted, hits, d18, bom_rows):
    """Findings, schedule, checks, ledger, sources. Kept in one place so the numbers come from the data."""
    from report_text import build
    return build(D, screws, inserts, fitted, hits, d18, bom_rows, short_part, fmt, GROUPS, SRC)


if __name__ == "__main__":
    main()
