"""PrusaSlicer 2.7.2 grams and hours for the shin eye shapes.

Uses print/slice.py (config stack, orientation, g-code parse) the same way as
st_slice_proposals.py. PLA density in that parser is 1.20 g/cm3. Other materials
scale the toolpath volume by the cited density. The lab has no PETG, ASA, PLA-CF
or PA6-CF print profile, so the time is the PLA profile time.

Usage: PRUSA_SLICER=<binary> ODM_SCRATCH=<scratch> python3 eye_slice.py
"""
import os
import sys
import json
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
STRUCT = os.path.abspath(os.path.join(HERE, ".."))
LAB = os.path.abspath(os.path.join(STRUCT, "../.."))
sys.path.insert(0, os.path.join(LAB, "print"))
sys.path.insert(0, STRUCT)
import slice as SLC  # noqa: E402
import st_slice_proposals as SP  # noqa: E402

# cited densities, g/cm3. PLA is the parser's 1.20 (Overture Easy PLA, the lab filament file).
DENS = {"PLA": 1.20, "PETG": 1.28, "PLA-CF": 1.22, "ASA": 1.05, "PA6-CF": 1.09}
SRC = {
    "collar": os.path.join(STRUCT, "topology", "stl", "shin_left_sheet.stl"),
    "taper": os.path.join(HERE, "stl", "shin_left_sheet_taper.stl"),
    "taper_cbore": os.path.join(HERE, "stl", "shin_left_sheet_taper_cbore.stl"),
    "web": os.path.join(HERE, "stl", "shin_left_sheet_web.stl"),
}


def one(tag, src, extra=None):
    r = SP.ROWS["shin_left_sheet.stl"]
    work = os.path.join(SP.OUT, "shin_eye", tag)
    os.makedirs(work, exist_ok=True)
    m = __import__("trimesh").load(src, force="mesh")
    m.apply_transform(SLC.rot_up(r["up"]))
    m.apply_translation(-m.bounds[0])
    path = os.path.join(work, "shin_left_sheet.stl")
    m.export(path)
    cfgs = SLC.config_stack(r["material"], r["overrides"])
    if extra:
        ini = os.path.join(work, "extra.ini")
        open(ini, "w").write("".join("%s = %s\n" % kv for kv in extra.items()))
        cfgs = cfgs + [ini]
    g = os.path.join(work, "out.gcode")
    SLC.run_slicer([path], cfgs, g)
    pla = SLC.parse_gcode(g, 1.20)
    qty = int(r["qty"])
    row = dict(tag=tag, qty=qty, g_model=round(pla["g_model"], 2), h=round(pla["s"] / 3600.0, 2),
               g_support=round(pla.get("g_support") or 0, 2))
    row["robot_g"] = round(row["g_model"] * qty, 2)
    row["robot_h"] = round(row["h"] * qty, 2)
    row["by_material_g"] = {k: round(pla["g_model"] * qty * (d / 1.20), 2) for k, d in DENS.items()}
    print(row, flush=True)
    return row


if __name__ == "__main__":
    base = SP.slice_one("shin_left_sheet.stl", {}, "shin_base")
    qty = int(SP.ROWS["shin_left_sheet.stl"]["qty"])
    rows = [dict(tag="stock", qty=qty, g_model=round(base["g_model"], 2), h=round(base["s"] / 3600.0, 2),
                 g_support=round(base.get("g_support") or 0, 2),
                 robot_g=round(base["g_model"] * qty, 2), robot_h=round(base["s"] / 3600.0 * qty, 2),
                 by_material_g={k: round(base["g_model"] * qty * (d / 1.20), 2) for k, d in DENS.items()})]
    print(rows[0], flush=True)
    for tag, src in SRC.items():
        rows.append(one(tag, src))
    rows.append(one("web_w5i40", SRC["web"], {"perimeters": "5", "fill_density": "40%"}))
    # gyroid (the lab infill) is rejected at 100%. Rectilinear is the solid fill.
    rows.append(one("web_solid", SRC["web"], {"fill_pattern": "rectilinear", "perimeters": "6", "fill_density": "100%"}))
    json.dump(rows, open(os.path.join(HERE, "slice.json"), "w"), indent=1)
    print("wrote slice.json")
