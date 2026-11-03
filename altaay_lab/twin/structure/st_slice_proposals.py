"""Structure twin: grams and hours of the proposed print changes (PrusaSlicer 2.7.2 estimates, as print/slice.py).

Each proposal is one STL sliced with the lab configs (print/config/, the parts.csv overrides of that part) plus the
proposed change, against the same STL with its D22 settings. PETG grams scale the PLA toolpath volume by the density
ratio 1.27 / 1.20 (Generic PETG in /usr/share/PrusaSlicer/profiles/PrusaResearch.ini, line 7810; Overture Easy PLA
TDS 1.20 g/cm3, print/config/filament_easy_pla.ini); PETG print time is not estimated (the profile would change).
Run: ODM_SCRATCH=... python3 altaay_lab/twin/structure/st_slice_proposals.py   (G-code in ODM_SCRATCH/slice_prop/)
"""
import os, sys, json, csv
HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, "../.."))
sys.path.insert(0, os.path.join(LAB, "print"))
import slice as SLC                                   # unchanged lab file: oriented, config_stack, run_slicer, parse_gcode

SCR = os.environ.get("ODM_SCRATCH", "/tmp/odm_twin_structure")
OUT = os.path.join(SCR, "slice_prop"); os.makedirs(OUT, exist_ok=True)
ROWS = {r["stl"]: r for r in csv.DictReader(open(os.path.join(LAB, "print/parts.csv")))}
PROPOSALS = [   # (label, stl, extra settings)
    ("roll_to_pitch 4 walls 40 %", "left_roll_to_pitch.stl", {"perimeters": "4", "fill_density": "40%"}),
    ("roll_to_pitch 3 walls 15 % (its profile before D22)", "left_roll_to_pitch.stl", {"perimeters": "3"}),
    ("knee sheet (left) 5 walls 40 %", "knee_to_ankle_left_sheet.stl", {"perimeters": "5", "fill_density": "40%"}),
    ("knee sheet (right) 5 walls 40 %", "knee_to_ankle_right_sheet.stl", {"perimeters": "5", "fill_density": "40%"}),
    ("leg_spacer 4 walls 40 % (no rings needed)", "leg_spacer.stl", {"perimeters": "4", "fill_density": "40%"}),
    ("roll_motor_top 4 walls 40 %", "roll_motor_top.stl", {"perimeters": "4", "fill_density": "40%"}),
    ("foot_top 4 walls 40 %", "foot_top.stl", {"perimeters": "4", "fill_density": "40%"}),
]
ORIENT = [("roll_to_pitch printed with +x up (hip roll axis vertical)", "left_roll_to_pitch.stl", "+x"),
          ("roll_to_pitch printed with +y up (the wall between the horn ears flat)", "left_roll_to_pitch.stl", "+y")]

def slice_one(stl, extra, tag, up=None):
    r = ROWS[stl]; ov = r["overrides"]
    cfgs = SLC.config_stack(r["material"], ov)
    if extra:
        p = os.path.join(OUT, f"extra_{tag}.ini")
        open(p, "w").write("".join(f"{k} = {v}\n" for k, v in extra.items())); cfgs = cfgs + [p]
    src = SLC.oriented(stl, up or r["up"], os.path.join(OUT, "oriented" + ("_" + up.replace("+", "p").replace("-", "m") if up else "")))
    g = os.path.join(OUT, f"{stl[:-4]}_{tag}.gcode")
    SLC.run_slicer([src], cfgs, g)
    return SLC.parse_gcode(g, 1.20)

if __name__ == "__main__":
    res = []
    for k, (label, stl, extra) in enumerate(PROPOSALS):
        base = slice_one(stl, {}, "base")
        new = slice_one(stl, extra, f"p{k}")
        qty = int(ROWS[stl]["qty"])
        row = dict(label=label, stl=stl, qty=qty, base_g_model=base["g_model"], new_g_model=new["g_model"], base_h=base["s"] / 3600, new_h=new["s"] / 3600,
                   d_g_robot=round((new["g_model"] - base["g_model"]) * qty, 2), d_h_robot=round((new["s"] - base["s"]) / 3600 * qty, 2),
                   petg_g_model=round(new["g_model"] * 1.27 / 1.20, 2))
        res.append(row); print(row, flush=True)
    for label, stl, up in ORIENT:
        base = slice_one(stl, {}, "base"); new = slice_one(stl, {}, "orient", up=up)
        row = dict(label=label, stl=stl, qty=int(ROWS[stl]["qty"]), base_g_model=base["g_model"], new_g_model=new["g_model"], base_h=base["s"] / 3600,
                   new_h=new["s"] / 3600, base_support_g=base["g_support"], new_support_g=new["g_support"],
                   d_g_robot=round((new["g_model"] - base["g_model"]) * 2, 2), d_h_robot=round((new["s"] - base["s"]) / 3600 * 2, 2))
        res.append(row); print(row, flush=True)
    json.dump(res, open(os.path.join(SCR, "slice_proposals.json"), "w"), indent=1)
