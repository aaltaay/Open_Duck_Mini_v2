"""Structure twin: writes tables.md and fills the generated tables of STRUCTURE_TWIN.md (sim pass only, FEA pass only).

Reads the scratch outputs (ODM_SCRATCH/fea, fea_conv, report, slice_proposals.json). Each generated table sits in
STRUCTURE_TWIN.md between <!-- KEY --> and <!-- /KEY --> (a bare KEY line is replaced the first time), so a re-run
replaces only the tables.
Run: ODM_SCRATCH=... python3 altaay_lab/twin/structure/st_finalize.py
"""
import os, sys, io, re, json, glob, contextlib
import numpy as np
SCR = os.environ.get("ODM_SCRATCH", "/tmp/odm_twin_structure")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import st_report as RP

def cap(fn, *a, **k):
    b = io.StringIO()
    with contextlib.redirect_stdout(b): out = fn(*a, **k)
    return b.getvalue(), out

def tab(text): return "\n".join(l for l in text.splitlines() if l.startswith("|"))

LV = {"MuJoCo default": "_tc0.02_dr1", "soft": "_tc0.0158_dr0.2", "mid": "_tc0.005_dr0.2", "hard": "_tc0.00289_dr0.2"}
BASE = ["roll_to_pitch", "shin_segment", "thigh_segment", "hip_roll_stage", "foot", "neck_sheets", "head_roll_mount"]
PROP = {"roll_to_pitch_upx": ("roll_to_pitch printed with +x up (hip roll axis vertical)", "roll_to_pitch printed with +x up (hip roll axis vertical)", 2),
        "roll_to_pitch_upy": ("roll_to_pitch printed with +y up (the wall between the horn ears flat)", "roll_to_pitch printed with +y up (the wall between the horn ears flat)", 2),
        "roll_to_pitch_w3": ("roll_to_pitch 3 walls 15 % (its profile before D22)", "roll_to_pitch 3 walls 15 % (its profile before D22)", 2),
        "roll_to_pitch_w4i40": ("roll_to_pitch 4 walls 40 %", "roll_to_pitch 4 walls 40 %", 2),
        "roll_to_pitch_w6i40": ("roll_to_pitch 6 walls 40 % (the 5 mm walls print solid)", "roll_to_pitch 6 walls 40 % (the 5 mm walls print solid)", 2),
        "shin_segment_w5i40": ("knee sheets 5 walls 40 % (all 8)", ("knee sheet (left) 5 walls 40 %", "knee sheet (right) 5 walls 40 %"), 1)}

def load(st, sub="fea"):
    f = os.path.join(SCR, sub, st + ".json")
    return json.load(open(f)) if os.path.exists(f) else None

def falls(C):
    fl = C.get("fall", {}).get("per_run", {}); sf = {}
    for lv, tag in LV.items():
        v = {k.replace(tag, ""): 1 / x["FI"] for k, x in fl.items() if k.endswith(tag)}
        if v:
            w = min(v, key=v.get); sf[lv] = dict(worst=v[w], run=w, n_under=sum(1 for s in v.values() if s < 1.2), n=len(v), all=v)
    return sf

def alt_sf(c, lab):
    """SF with the maker interlayer value or with PETG strengths. From the whole-field evaluation when the run has it
    ('alt'); else exact for an in-plane weak spot (maker Z changes nothing; PETG scales by 34 / 47.1) and an upper
    bound (the value at the room-temperature weak spot) for an interlayer one."""
    if c.get("alt") and lab in c["alt"]: return 1 / c["alt"][lab]["FI"], "", c["alt"][lab]
    sf = 1 / c["FI"]
    if c["mode"] == "in-plane": return (sf if lab == "makerZ" else sf * 34.0 / 47.1), "", None
    X, Z = (47.1, 39.4) if lab == "makerZ" else (34.0, 23.0)
    return 1 / max(c["vm"] / X, np.hypot(max(c["szz"], 0.0) / Z, c["tz"] / Z)), "at most ", None

def fmt_fall(f):
    return f"{f['worst']:.2f} ({f['n_under']} of {f['n']})" if f else "-"

def fea_rows():
    rows = []; data = {}
    for st in BASE:
        d = load(st)
        if not d: continue
        m = d["meshes"][-1]; C = m["cases"]; w, p = C["walk"], C.get("push")
        sf = falls(C); raw = w.get("raw_element_peak")
        mz, mzb, _ = alt_sf(w, "makerZ"); pg, pgb, _ = alt_sf(w, "PETG")
        mzp, mzpb, _ = alt_sf(p, "makerZ") if p else (None, "", None); pgp, pgpb, _ = alt_sf(p, "PETG") if p else (None, "", None)
        data[st] = dict(walk=1 / w["FI"], push=1 / p["FI"] if p else None, mode=w["mode"], member=w["member"], zone=w["zone"], where=w["where_link"],
                        sample=w["sample"], push_sample=p["sample"] if p else None, push_where=p["where_link"] if p else None, push_mode=p["mode"] if p else None,
                        vm=w["vm"], szz=w["szz"], tz=w["tz"], principal=w.get("principal"),
                        walk_makerZ=mz, walk_makerZ_bound=bool(mzb), push_makerZ=mzp, walk_petg=pg, walk_petg_bound=bool(pgb), push_petg=pgp,
                        walk_50C=0.625 / w["FI"], push_50C=0.625 / p["FI"] if p else None, raw=1 / raw["FI"] if raw else None,
                        falls={k: dict(worst=v["worst"], run=v["run"], n_under=v["n_under"], n=v["n"]) for k, v in sf.items()},
                        nodes=m["nodes"], tets=m["tets"], solver=m["solver"], members=d["members"], insert_loads=w.get("insert_loads"))
        rows.append([st, ", ".join(d["members"]), f"{1 / w['FI']:.2f}", f"{1 / p['FI']:.2f}" if p else "-",
                     f"{mzb}{mz:.2f} / {mzpb}{mzp:.2f}" if p else f"{mzb}{mz:.2f}", f"{pgb}{pg:.2f} / {pgpb}{pgp:.2f}" if p else f"{pgb}{pg:.2f}",
                     fmt_fall(sf.get("soft")), fmt_fall(sf.get("mid")), fmt_fall(sf.get("MuJoCo default")),
                     f"{w['member']}, {w['zone']}, {w['mode']} (von Mises {w['vm']:.1f}, s_zz {w['szz']:.1f}, tau_z {w['tz']:.1f} MPa) at {w['where_link']} mm; {w['sample']}",
                     f"{1 / raw['FI']:.2f}" if raw else "-", f"{m['nodes']} / {m['tets']}"])
    head = ["study", "parts", "SF walk", "SF push", "SF walk / push, maker Z 39.4 MPa", "SF walk / push, PETG",
            "falls soft: worst SF (falls under 1.2 of 10)", "falls mid", "falls MuJoCo default", "weak spot at the walking peak (link frame)",
            "SF walk, raw element peak", "nodes / tets"]
    return RP.md(rows, head), data

def prop_rows(fat):
    S = {r["label"]: r for r in json.load(open(os.path.join(SCR, "slice_proposals.json")))}
    rows = []; data = {}
    for st, (label, slab, mult) in PROP.items():
        d = load(st)
        if not d: continue
        m = d["meshes"][-1]; C = m["cases"]; w, p = C["walk"], C.get("push"); sf = falls(C)
        labs = slab if isinstance(slab, tuple) else (slab,)
        dg = sum(S[l]["d_g_robot"] for l in labs if l in S) * mult; dh = sum(S[l]["d_h_robot"] for l in labs if l in S) * mult
        if st.endswith(("upx", "upy")):          # orientation rows: d_g_robot and d_h_robot already count both legs
            dg /= mult; dh /= mult
        sup = S.get(labs[0], {}).get("new_support_g")
        life = min((r["life_h"] for r in fat.get(st, {}).values()), default=None)
        data[st] = dict(label=label, walk=1 / w["FI"], push=1 / p["FI"] if p else None, falls={k: dict(worst=v["worst"], n_under=v["n_under"], n=v["n"]) for k, v in sf.items()},
                        where=w["where_link"], mode=w["mode"], d_g=dg, d_h=dh, support_g=sup, life_h=life, walk_50C=0.625 / w["FI"], push_50C=0.625 / p["FI"] if p else None)
        rows.append([label, f"{1 / w['FI']:.2f}", f"{1 / p['FI']:.2f}" if p else "-", fmt_fall(sf.get("soft")), fmt_fall(sf.get("mid")),
                     f"{w['member']}, {w['zone']}, {w['mode']} at {w['where_link']} mm", f"{0.625 / w['FI']:.2f} / {0.625 / p['FI']:.2f}" if p else "-",
                     f"{life:.3g}" if life is not None else "-",
                     f"+{dg:.1f} g, +{dh:.2f} h" + (f" (support {sup:.1f} g per part instead of 1.3 g)" if sup else "")])
    head = ["change (same loads and supports)", "SF walk", "SF push", "falls soft: worst (under 1.2 of 10)", "falls mid", "weak spot (link frame)",
            "SF walk / push at 50 C", "design-curve life h (worst walking case)", "grams and print hours, both legs (PrusaSlicer 2.7.2)"]
    return RP.md(rows, head), data

def conv_rows():
    rows = []; data = {}
    for st in ("roll_to_pitch", "shin_segment"):
        lv = []
        d1 = load(st)
        dc = load(st, "fea_conv")
        if d1: lv += [m for m in d1["meshes"] if int(m["maxvol"]) == 1]
        if dc: lv += [m for m in dc["meshes"] if int(m["maxvol"]) > 1 or not d1]
        d3 = load(st, "fea_conv3")                     # a level run on its own (same code, run in parallel to save time)
        if d3: lv = [m for m in lv if int(m["maxvol"]) not in [int(x["maxvol"]) for x in d3["meshes"]]] + d3["meshes"]
        for m in sorted(lv, key=lambda m: m["maxvol"]):
            C = m["cases"]; w = C["walk"]; p = C.get("push"); raw = w.get("raw_element_peak")
            data.setdefault(st, []).append(dict(level=int(m["maxvol"]), nodes=m["nodes"], tets=m["tets"], walk=1 / w["FI"], push=1 / p["FI"] if p else None,
                                                raw=1 / raw["FI"] if raw else None, where=w["where_link"], solver=m["solver"], falls=falls(C)))
            sf = falls(C)
            rows.append([st, int(m["maxvol"]), m["nodes"], m["tets"], f"{1 / w['FI']:.2f}", f"{1 / p['FI']:.2f}" if p else "-", fmt_fall(sf.get("soft")),
                         f"{1 / raw['FI']:.2f}" if raw else "-", str(w["where_link"]), f"{max(m['u_unit_max_mm']):.4f}", m["solver"].split(", ", 1)[1]])
    head = ["study", "mesh level", "nodes", "tets", "SF walk (1 mm average)", "SF push", "falls soft", "SF walk, raw element peak",
            "walking weak spot (link frame mm)", "largest unit-load displacement mm", "CG (last unit load)"]
    return RP.md(rows, head), data

def avg_rows():
    rows = []; data = {}
    for f in sorted(glob.glob(os.path.join(SCR, "fea_conv", "avgcheck_*.json"))):
        d = json.load(open(f)); data[d["study"]] = d["rows"]
        for r in d["rows"]:
            rows.append([d["study"], "raw element" if r["radius_mm"] == 0 else f"{r['radius_mm']:g} mm", f"{r['walk']['SF']:.2f}", f"{r['push']['SF']:.2f}",
                         f"{r['fall_soft']['worst_SF']:.2f} ({r['fall_soft']['n_under_1_2']} of {r['fall_soft']['n']})",
                         f"{r['fall_mid']['worst_SF']:.2f} ({r['fall_mid']['n_under_1_2']} of {r['fall_mid']['n']})",
                         f"{r['walk']['where_link']} ({r['walk']['n_elements_in_radius']})"])
    head = ["study (mesh level 1)", "stress averaging", "SF walk", "SF push", "falls soft", "falls mid", "walking weak spot (elements inside the radius there)"]
    return RP.md(rows, head), data

def sheet_rows():
    f = os.path.join(SCR, "fea_conv", "sheet_local.json")
    if not os.path.exists(f): return "", []
    d = json.load(open(f)); rows = []
    for r in d:
        rows.append([r["level"], r["nodes"], r["tets"], f"{r['raw']['vm_neck_per_Nm']:.2f} at {r['raw']['neck_at']}", f"{r['avg1mm']['vm_neck_per_Nm']:.2f}",
                     f"{r['raw']['vm_peak_per_Nm']:.2f} at {r['raw']['at']}", f"{r['avg1mm']['vm_peak_per_Nm']:.2f} at {r['avg1mm']['at']}", f"{r['u_max_mm_per_Nm']:.3f}"])
    head = ["mesh level", "nodes", "tets", "neck: raw von Mises MPa per N m (where)", "neck: 1 mm average", "whole sheet: raw peak (where)",
            "whole sheet: 1 mm average peak (where)", "largest displacement mm per N m"]
    return RP.md(rows, head), d

def fill(doc, key, text):
    block = f"<!-- {key} -->\n{text}\n<!-- /{key} -->"
    pat = re.compile(rf"<!-- {key} -->\n.*?\n<!-- /{key} -->", re.S)
    if pat.search(doc): return pat.sub(lambda _: block, doc)
    return re.sub(rf"(?m)^{key}$", lambda _: block, doc)

if __name__ == "__main__":
    parts = {}
    for k, fn in (("loads", RP.loads_table), ("falls", RP.falls_table), ("fasteners", RP.fastener_table), ("hot", RP.fea_table)):
        parts[k], _ = cap(fn)
    fat_txt, fat = cap(RP.fatigue_table)
    pfat_txt, pfat = cap(RP.fatigue_table, studies=list(PROP), tag="fatigue_proposals")
    fea_md, fdata = fea_rows(); prop_md, pdata = prop_rows(pfat); conv_md, cdata = conv_rows(); avg_md, adata = avg_rows(); sheet_md, sdata = sheet_rows()
    json.dump(dict(fea=fdata, proposals=pdata, convergence=cdata, averaging=adata, sheet_local=sdata), open(os.path.join(SCR, "report", "fea_summary.json"), "w"), indent=1, default=float)
    open(os.path.join(HERE, "tables.md"), "w").write(
        "# Structure twin tables (generated by st_finalize.py from the scratch outputs; sim pass only, FEA pass only)\n\n"
        "## Joint loads, walking and push recovery\n\n" + tab(parts["loads"]) + "\n\n## Falls by contact level\n\n" + tab(parts["falls"]) +
        "\n\n## Horn and servo case screws\n\n" + tab(parts["fasteners"]) +
        "\n\n## FEA safety factors (room temperature)\n\n" + fea_md + "\n\n## FEA of the proposed print changes\n\n" + prop_md +
        "\n\n## Fatigue at the weak spots (cited design curve, P_s 95 %)\n\n" + tab(fat_txt) + "\n\n## Fatigue of the proposed print changes\n\n" + tab(pfat_txt) +
        "\n\n## FEA hot case and PETG (per study)\n\n" + tab(parts["hot"]) + "\n\n## Mesh convergence\n\n" + conv_md + "\n\n## Stress averaging radius\n\n" + avg_md +
        "\n\n## Knee sheet eye, local mesh check (unit knee torque)\n\n" + sheet_md + "\n")
    p = os.path.join(HERE, "STRUCTURE_TWIN.md"); doc = open(p).read()
    for key, text in (("FEA_TABLE", fea_md), ("CONV_TABLE", conv_md + "\n\n" + avg_md + "\n\n" + sheet_md), ("FATIGUE_TABLE", tab(fat_txt)), ("PROPOSALS_FEA_TABLE", prop_md)):
        doc = fill(doc, key, text)
    open(p, "w").write(doc)
    print(fea_md); print(); print(prop_md); print(); print(conv_md); print(); print(avg_md); print(); print(sheet_md); print(); print(tab(fat_txt)); print(); print(tab(pfat_txt))
