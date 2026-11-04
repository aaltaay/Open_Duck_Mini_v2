#!/usr/bin/env python3
"""V1 track 2 (assembly) calcs, calc only: the hold of every part with no screw against the worst fall shock, the mass
recount (342 fitted screws against the 274 modelled, the D25 ties, the D30 switch), the D30 switch numbers, and
BUILD_ORDER.md from asm_geom.json. Reads sim/mass_budget.py for its cited constants and screw formulas (import only;
build_budget is not run). Run after asm_geom.py: python3 altaay_lab/twin/assembly/asm_calc.py"""
import collections
import json
import math
import os
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(os.path.dirname(HERE))
OUT = os.environ.get("ASM_OUT", "/home/user/v1_out/asm")
sys.path.insert(0, os.path.join(LAB, "sim"))
import mass_budget as MB  # noqa: E402

G = json.load(open(os.path.join(OUT, "asm_geom.json")))
FJ = json.load(open(os.path.join(LAB, "fasteners", "fasteners.json")))["fasteners"]
NET = yaml.safe_load(open(os.path.join(LAB, "wiring", "netlist.yaml")))
G0 = 9.80665                                   # standard gravity, m/s2
FALL = {"soft": {"head": 71, "trunk": 45}, "mid": {"head": 196, "trunk": 128}}   # g, STRUCTURE_TWIN.md section 3 (worst of 10 falls)
VHB_DESIGN_KPA = 12 * 6.894757                 # 3M VHB dynamic design value 12 lb/in2 (3M data sheets, via search index)
VHB_SHEAR_KPA = 80 * 6.894757                  # VHB 4950 dynamic overlap shear 80 lb/in2 (FindTape listing, via search index)
out = {"sources": {"fall": "twin/structure/STRUCTURE_TWIN.md section 3: worst head and trunk accelerations of the 10 falls",
                   "vhb_design": "3M VHB data sheets: 12 lb/in2 (85 kPa) for most dynamic stresses (search index 2026-11-04); 82.7 kPa used",
                   "vhb_shear": "3M VHB 4950 dynamic overlap shear 80 lb/in2 = 552 kPa (FindTape listing via search index 2026-11-04)",
                   "areas": "twin/thermal/THERMAL_TWIN.md line 213 (geometry.json, VHB contact within 1.5 mm): BEC 1858, Pololu switch seat 353, fuse holder 745 mm2; D30V30F5 0.7 x 0.8 in (BOM 9)"}}

# ---------------------------------------------------------------- 1. hold of the parts with no screw
sl = G.get("side_lamp", {})
lamp_g = 8.40 + 2.32 + MB.REFL_G + MB.LED_G    # print/SLICE_SUMMARY.md g each (flash_light_module, flash_reflector_interface)
rows = [
    ("Castle CC BEC Pro", MB.BEC_G, "trunk", "VHB 4950 on the 47 x 33 face", 1858.0, 13.0, 33.0, 47.0),
    ("Littelfuse fuse holder (UNVERIFIED mass)", MB.FUSEHOLDER_G, "trunk", "VHB 4950, 52 mm edge along y", 745.0, 8.6, 17.2, 52.0),
    ("Pololu 2813 (D30, 2.7 g Pololu)", 2.7, "trunk", "VHB 4950 on the 2815 seat", 353.0, 2.05, 20.3, 25.4),
    ("Pololu D30V30F5 5 V regulator", MB.REG_G, "head", "VHB 4950, board face 0.7 x 0.8 in", 361.0, None, None, None),
    ("Adafruit MAX98357A amp", MB.AMP_G, "head", "VHB 4950 (board size not read: area needed shown)", None, None, None, None),
    ("USB cable slack coil", 10.95, "trunk", "line 32 tie to a line 34 mount, plus VHB", None, None, None, None),
    ("Side lamp: flash_light_module + reflector interface + E5 + LED", lamp_g, "head",
     "nothing in the CAD (no screw, MOUNTING.md); fix: VHB 4950 on its contact face with the head", sl.get("contact_area_mm2_within_0p3"), None, None, None),
    ("D30 button plate with the NKK button (plate 0.64 g; button mass not read)", 0.64, "trunk", "flange on the outer face: inward by the flange, outward by VHB on the flange ring", 23.4 * 11.0 - 15.5 * 7.0, None, None, None),
]
hold = []
for name, m, where, mount, A, h, b, L in rows:
    r = dict(part=name, mass_g=round(m, 2), where=where, mount=mount, area_mm2=A)
    for lvl in ("soft", "mid"):
        F = m / 1000 * FALL[lvl][where] * G0
        r["F_%s_N" % lvl] = round(F, 2)
        r["area_needed_%s_mm2" % lvl] = round(F / (VHB_DESIGN_KPA / 1000), 1)
        if A:
            s_ = F / A * 1000
            r["stress_%s_kPa" % lvl] = round(s_, 1)
            r["SF_design_%s" % lvl] = round(VHB_DESIGN_KPA / s_, 1)
            r["SF_shear_%s" % lvl] = round(VHB_SHEAR_KPA / s_, 1)
            if h and b:     # tipping: the load at the box centre height h, linear edge stress over the footprint
                edge = (F / A + 6 * F * h / (L * b ** 2)) * 1000
                r["edge_kPa_%s" % lvl] = round(edge, 1)
                r["SF_edge_design_%s" % lvl] = round(VHB_DESIGN_KPA / edge, 2)
    hold.append(r)
out["hold"] = hold

# ---------------------------------------------------------------- 4. mass recount
def screw_mass(f):
    t, L = f["head"]["type"], f["length_mm"] or f.get("draw_length_mm") or 4.0
    if t == "M3_din912":
        return MB.shcs_g("M3", L)
    if t == "M2.5_din912":
        return MB.shcs_g("M2.5", L)
    if t == "M3_iso7380":
        return MB.panhead_g(3.0, 0.5, 5.7, 1.65, L)
    if t in ("M2_pan_selftap", "SG90_screw"):
        return MB.panhead_g(2.0, 0.4, 4.0, 1.6, L if t != "SG90_screw" else 4.0)
    if t == "M3_horn_centre":
        return MB.panhead_g(3.0, 0.5, f["head"]["dk"], f["head"]["k"], L)
    if t == "PA3_idle":
        return MB.panhead_g(3.0, 0.5, f["head"]["dk"], f["head"]["k"], L)
    raise ValueError(t)


fit = [f for f in FJ if f["kind"] == "screw" and not f.get("leave_out") and f.get("install") is not False]
driven = [f for f in fit if f["source"] != "servo_case"]
by = collections.defaultdict(lambda: [0, 0.0])
for f in driven:
    by[f["spec"]][0] += 1
    by[f["spec"]][1] += screw_mass(f)
scr_g = sum(v[1] for v in by.values())
washer_g = 16 * math.pi / 4 * (5.0 ** 2 - 2.7 ** 2) * 0.3 * MB.A2_DENS / 1000
tie_n, tie_g_ub = 75 + 3, 0.417                  # BOM 32: 75 along the cables plus 1 to 3; Panduit PLT1.5M-C gross 0.417 g (TME, 142 mm, an upper bound)
p13 = next(c for c in NET["cables"] if c["id"] == "P13")
off_len = p13.get("rule_mm") or p13.get("polyline_mm")
off_g = off_len / 1000 * MB.WIRE_GPM[26]
plate_g = 534.8 / 1694.9 * 2.04                   # button plate volume (asm_geom) x the bulb's sliced g per CAD mm3 (SLICE_SUMMARY, same base profile)
d = collections.OrderedDict()
d["screws: 286 driven screws (fasteners.json) against the 175.3 g of 274 modelled"] = scr_g - 175.3
d["washers: 16 x ISO 7092 2.7 x 5.0 x 0.3 mm"] = washer_g
d["cable ties: 78 fitted at most, 0.417 g upper bound, against the 1.0 g modelled"] = tie_n * tie_g_ub - 1.0
d["D30: Pololu 2813 2.7 g in place of the 2815 2.6 g (Pololu specs)"] = 2.7 - 2.6
d["D30: OFF wire GPIO26 to the 2813, 26 AWG on the P13 route"] = off_g
d["D30: printed button plate (CAD volume x the sliced bulb ratio)"] = plate_g
tot = sum(d.values())
out["mass"] = dict(by_spec={k: [v[0], round(v[1], 2)] for k, v in sorted(by.items())}, screws_new_g=round(scr_g, 1),
                   n_driven=len(driven), n_fitted=len(fit), deltas={k: round(v, 2) for k, v in d.items()},
                   total_delta_g=round(tot, 1), new_total_g=round(2652.8 + tot, 1), pct=round(100 * tot / 2652.8, 2),
                   not_counted=["55 adhesive tie mounts (BOM 34 and 34b: no mass published by HellermannTyton or Panduit pages read)",
                                "the NKK button (mass not read; the 2.0 g UNVERIFIED panel switch stays as its stand-in)",
                                "kapton wrap on the BMS (thickness not stated, BOM 33)", "VHB pieces added for the amp, speaker, side lamp, plate"],
                   tie_upper_bound_g=round(tie_n * tie_g_ub, 1), off_wire_mm=off_len)

# ---------------------------------------------------------------- 6. D30 numbers
out["d30"] = dict(peak_window_A=15.89, rms_A=[5.90, 5.92], rating_55C_A=6.0, rating_150C_A=16.0, max_A=90.0, off_uA=0.2,
                  bms_uA=10.0, off_total_uA=10.2, size_in=[0.8, 1.0, 0.16], size_mm=[20.3, 25.4, 4.1], mass_g=2.7,
                  rms_pct_of_55C=[round(5.90 / 6 * 100, 1), round(5.92 / 6 * 100, 1)],
                  peak_pct_of_max=round(15.89 / 90 * 100, 1), peak_pct_of_150C=round(15.89 / 16 * 100, 1),
                  source="https://www.pololu.com/product/2813 read 2026-11-04 with curl (/home/user/v1_out/asm/pololu2813.html): HP column")

# ---------------------------------------------------------------- seam cables (body_back module pulled 20 mm back)
seam = []
for c in NET["cables"]:
    rg = c.get("regions") or []
    if "battery_bay" in rg and len(set(rg)) > 1 or c["id"] in ("P10", "P11", "P12", "P13", "P15"):
        seam.append(dict(id=c["id"], desc=c.get("desc"), regions=rg, polyline_mm=c.get("polyline_mm"), rule_mm=c.get("rule_mm"),
                         slack_mm=round((c.get("rule_mm") or 0) - (c.get("polyline_mm") or 0), 1)))
out["seam_cables"] = seam

# ---------------------------------------------------------------- BUILD_ORDER.md
fin = G["build_order_final"]
L_ = ["# Build order (CAD check only)", "",
      "Written 2026-11-04 by the V1 track 2 agent from twin/assembly/asm_geom.py (every driven screw: 286 = 342 fitted less the 56 factory case screws inside the servos). "
      "Each line is a run of screws in the order they are driven; a part goes on just before its first screw. JOIN marks a screw that joins two subassemblies. "
      "Tools: hex2.0 and hex2.5 are the BOM T4 keys (Bondhus long series), PH0 and PH1 the proposed Wera 2050 drivers, the PH0 x 25 mm bit the proposed Wera 851/1 Z (both need Ahmed's OK). "
      "The order was checked: no screw's tool path or way in crosses a part that is already joined to it (0 violations, asm_geom.json verify).", ""]
step, prev = 0, None
for st in fin:
    key = (st["part"], st["into"], st["tool"], st["note"], st["group"])
    if prev and key == prev["key"] and not st["joins"]:
        prev["n"] += 1
        prev["ids"].append(st["id"])
        continue
    if prev:
        L_.append(prev["line"] % (prev["n"], ", ".join(prev["ids"]) if len(prev["ids"]) <= 4 else prev["ids"][0] + " to " + prev["ids"][-1]))
    step += 1
    line = "%d. " % step + ("JOIN " if st["joins"] else "") + "%%d x %s: %s into %s, %s%s (%%s)" % (
        st["spec"], st["part"], st["into"], st["tool"], (", " + st["note"]) if st["note"] else "")
    prev = dict(key=key, n=1, ids=[st["id"]], line=line)
L_.append(prev["line"] % (prev["n"], ", ".join(prev["ids"]) if len(prev["ids"]) <= 4 else prev["ids"][0] + " to " + prev["ids"][-1]))
L_ += ["", "Rules found by the cast (each one is in the order above):",
       "- Trunk core first: trunk_top to trunk_bottom (F073, F074, M3x12) before the centre servo goes in (its case sits 0.0 to 0.1 mm over their heads); the centre servo's side screws F050 and F139 before the hip yaw servos (2.0 mm from their heads); the hip yaw top case screws F126, F128, F130, F132 before the hip roll brackets go on the hip yaw horns (roll_motor_top 1.5 mm from their heads), and with the 25 mm bit (the trunk bearing is 58.5 mm out, inside the 60 mm blade).",
       "- Each horn: the horn centre screw into the servo before the part that covers it; the part to horn screws with the horn on the servo unless the servo body covers them (neck yaw: head_yaw_to_roll to its horn, F158 to F161, own bracket 64.9 mm out: 2.5 mm key with its short arm in the socket, 210 to 250 deg of free swing at 15 to 30 mm).",
       "- Head: camera screws before the head roll servo and head_roll_mount go in; SG90 tab screws F348 and F350 with the 25 mm bit (the head's own wall is 35.6 mm out, inside the 60 mm blade); head_roll_mount to head before head_bot_sheet (sheet 41 mm out); head_bot_sheet F083 and F084 with the neck pitch at -9.4 deg (body_middle_top 74 mm out, inside the 88 mm key).",
       "- Battery bay: the charger screw (F123) before the BMS goes in (BMS 0.7 mm from its head); cells, holder and BMS in before the lid; the fuse holder and the Pololu switch taped on the lid face after the lid screws; antennas into their holders after the holder's horn screw."]
open(os.path.join(HERE, "BUILD_ORDER.md"), "w").write("\n".join(L_) + "\n")
json.dump(out, open(os.path.join(HERE, "asm_calc.json"), "w"), indent=1)
print(json.dumps({k: out[k] for k in ("hold", "mass", "d30")}, indent=None)[:5000])
print("seam", json.dumps(seam)[:1500])
print("BUILD_ORDER lines", len(L_))
