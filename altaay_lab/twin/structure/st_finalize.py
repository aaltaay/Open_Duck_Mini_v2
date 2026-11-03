"""Structure twin: writes tables.md and fills the FEA, convergence, fatigue and proposal tables of STRUCTURE_TWIN.md.
Run: ODM_SCRATCH=... python3 altaay_lab/twin/structure/st_finalize.py
"""
import os, sys, io, json, glob, contextlib
import numpy as np
SCR = os.environ.get("ODM_SCRATCH", "/tmp/odm_twin_structure")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import st_report as RP

def cap(fn):
    b = io.StringIO()
    with contextlib.redirect_stdout(b): out = fn()
    return b.getvalue(), out

def tab(text): return "\n".join(l for l in text.splitlines() if l.startswith("|"))

LV = {"MuJoCo default": "_tc0.02_dr1", "soft": "_tc0.0158_dr0.2", "mid": "_tc0.005_dr0.2", "hard": "_tc0.00289_dr0.2"}

def fea_rows():
    rows = []; data = {}
    order = ["roll_to_pitch", "shin_segment", "thigh_segment", "hip_roll_stage", "foot", "neck_sheets", "head_roll_mount",
             "roll_to_pitch_upx", "roll_to_pitch_w4i40", "shin_segment_w5i40"]
    for st in order:
        f = os.path.join(SCR, "fea", st + ".json")
        if not os.path.exists(f): continue
        d = json.load(open(f)); m = d["meshes"][-1]; C = m["cases"]
        if "walk" not in C: continue
        w, p = C["walk"], C.get("push", {})
        fl = C.get("fall", {}).get("per_run", {})
        sf = {}
        for lv, tag in LV.items():
            v = {k: x for k, x in fl.items() if k.endswith(tag)}
            if v:
                worst = min(v.items(), key=lambda kv: 1 / kv[1]["FI"])
                n_bad = sum(1 for x in v.values() if 1 / x["FI"] < 1.2)
                sf[lv] = (1 / worst[1]["FI"], worst[0].replace(tag, ""), n_bad, len(v))
        def maker(c):                                  # SF at the same element with the maker Z 39.4 MPa (S = Z), in-plane unchanged
            fz = np.hypot(max(c["szz"], 0.0) / 39.4, c["tz"] / 39.4); fv = c["vm"] / 47.1
            return 1 / max(fz, fv)
        zw = maker(w); zp = maker(p) if p else None
        def petg(c):                                   # Bambu PETG HF TDS: X 34, Z 23 MPa (S = Z), same stresses
            return 1 / max(c["vm"] / 34.0, np.hypot(max(c["szz"], 0.0) / 23.0, c["tz"] / 23.0))
        hot_parts = ("knee_to_ankle_left_sheet", "knee_to_ankle_right_sheet", "leg_spacer", "left_roll_to_pitch", "trunk_top")
        raw = w.get("raw_element_peak", {})
        data[st] = dict(walk=1 / w["FI"], push=1 / p["FI"] if p else None, mode=w["mode"], member=w["member"], zone=w["zone"], where=w["where_link"],
                        sample=w["sample"], walk_makerZ=zw, push_makerZ=zp, falls=sf, hot=w["member"] in hot_parts,
                        walk_50C=0.625 / w["FI"], push_50C=(0.625 / p["FI"]) if p else None, walk_petg=petg(w), push_petg=petg(p) if p else None, raw=1 / raw["FI"] if raw else None, nodes=m["nodes"], tets=m["tets"],
                        stand=None, members=d["members"], insert_loads=w.get("insert_loads"), push_mode=p.get("mode"), push_where=p.get("where_link"),
                        principal=w.get("principal"), vm=w.get("vm"), szz=w.get("szz"), tz=w.get("tz"))
        fs = sf.get("soft"); fm = sf.get("mid")
        rows.append([st, ", ".join(d["members"]), f"{1 / w['FI']:.2f} ({zw:.2f})", (f"{1 / p['FI']:.2f} ({zp:.2f})") if p else "-",
                     f"{fs[0]:.2f} ({fs[2]} of {fs[3]} under 1.2)" if fs else "-", f"{fm[0]:.2f} ({fm[2]} of {fm[3]} under 1.2)" if fm else "-",
                     f"{w['member']}, {w['zone']}, {w['mode']} (s_zz {w['szz']:.1f}, tau_z {w['tz']:.1f}, von Mises {w['vm']:.1f} MPa) at {w['where_link']} mm, link frame; {w['sample']}",
                     f"{1 / raw['FI']:.2f}" if raw else "-", f"{m['nodes']} / {m['tets']}"])
    return rows, data

def conv_rows():
    rows = []
    for f in sorted(glob.glob(os.path.join(SCR, "fea_conv", "*.json"))):
        d = json.load(open(f))
        if "meshes" not in d: continue
        for m in d["meshes"]:
            C = m["cases"]
            rows.append([d["study"], int(m["maxvol"]), m["nodes"], m["tets"], f"{1 / C['walk']['FI']:.3f}", f"{1 / C['push']['FI']:.3f}" if "push" in C else "-",
                         f"{1 / C['walk'].get('raw_element_peak', {}).get('FI', np.nan):.3f}" if C["walk"].get("raw_element_peak") else "-",
                         str(C["walk"]["where_link"]), f"{max(m['u_unit_max_mm']):.4f}"])
    # level 1 of the screening run, for the studies that have a level 2 or 3 file
    return rows

if __name__ == "__main__":
    parts = []
    for fn in (RP.loads_table, RP.falls_table, RP.fastener_table, RP.fatigue_table, RP.fea_table):
        t, _ = cap(fn); parts.append(t)
    frows, fdata = fea_rows(); crows = conv_rows()
    head = ["study", "parts", "SF walk (maker Z)", "SF push (maker Z)", "SF fall soft (falls under 1.2)", "SF fall mid (falls under 1.2)",
            "weak spot at the walking peak", "SF walk, raw element peak", "nodes / tets"]
    fea_md = RP.md(frows, head)
    conv_md = RP.md(crows, ["study", "mesh level", "nodes", "tets", "SF walk (1 mm average)", "SF push", "SF walk, raw element peak", "weak spot (link frame mm)", "largest unit displacement mm"])
    json.dump(fdata, open(os.path.join(SCR, "report", "fea_summary.json"), "w"), indent=1, default=float)
    open(os.path.join(HERE, "tables.md"), "w").write(
        "# Structure twin tables (generated by st_finalize.py from the scratch outputs; sim pass only, FEA pass only)\n\n"
        "## Joint loads, walking and push recovery\n\n" + tab(parts[0]) + "\n\n## Falls by contact level\n\n" + tab(parts[1]) +
        "\n\n## Horn and servo case screws\n\n" + tab(parts[2]) + "\n\n## Fatigue at the weak spots (cited design curve, P_s 95 %)\n\n" + tab(parts[3]) +
        "\n\n## FEA safety factors\n\n" + fea_md + "\n\n## FEA hot case and PETG\n\n" + tab(parts[4]) + "\n\n## Mesh convergence\n\n" + conv_md + "\n")
    print(fea_md); print(); print(conv_md); print(); print(tab(parts[3]))
