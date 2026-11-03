"""Structure twin: tables for STRUCTURE.md from the load, fall, interface and FEA outputs (sim pass only, FEA pass only).

Reads ODM_SCRATCH/{loads,falls,fea}/ and interfaces.json; writes ODM_SCRATCH/report/*.json and prints markdown tables.
Run: ODM_SCRATCH=... python3 altaay_lab/twin/structure/st_report.py [loads|falls|fasteners|fea|fatigue|all]
"""
import os, sys, json, glob
import numpy as np
SCR = os.environ.get("ODM_SCRATCH", "/tmp/odm_twin_structure")      # read before st_sim (via st_loads) changes it
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import st_interfaces as SI
import st_loads as SL
OUT = os.path.join(SCR, "report"); os.makedirs(OUT, exist_ok=True)
J = SI.JOINTS
GAIT_S = 0.54                         # gait period [U] Playground polynomial_coefficients.pkl (sim/ADDED_MASS_SIM.md)
CYC_PER_H = 3600 / GAIT_S             # 6667 load cycles per hour per leg while walking
# fall contact levels: (tc, dr) of st_falls.TCS used as the stated stiffness range
LEVELS = {"MuJoCo default": (0.02, 1.0), "soft": (0.0158, 0.2), "mid": (0.005, 0.2), "hard": (0.00289, 0.2)}

def md(rows, head):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for r in rows: out.append("| " + " | ".join(str(x) for x in r) + " |")
    return "\n".join(out)

def chan(d, sel, ji):
    F = d["F"][sel, ji].astype(float); T = d["T"][sel, ji].astype(float)
    return dict(F_radial=np.hypot(F[:, 0], F[:, 1]), F_axial=np.abs(F[:, 2]), M_axis=np.abs(T[:, 2]), M_bend=np.hypot(T[:, 0], T[:, 1]))

def loads_table():
    sets = dict(walk=["walk_forward*", "turn_*", "walk_side*", "walk_backlash*"], stand=["stand_*"], push=["push1_*", "walk_pushes_*"])
    res = {}
    for sname, pats in sets.items():
        files = sorted(sum([glob.glob(os.path.join(SCR, "loads", p + ".npz")) for p in pats], []))
        agg = {j: {c: [0.0, 0.0] for c in ("F_radial", "F_axial", "M_axis", "M_bend")} for j in J}
        rf = {j: [] for j in J}; dur = 0.0; nrun = 0; fell = 0
        for f in files:
            d = np.load(f, allow_pickle=True); nm = os.path.basename(f)[:-4]
            sel = SI.window(d, nm); nrun += 1; fell += int(len(d["falls"]) > 0)
            if sel.sum() < 10: continue
            dur += float(sel.sum()) * float(d["dt"])
            for ji, j in enumerate(J):
                ch = chan(d, sel, ji)
                for c, v in ch.items():
                    agg[j][c][0] = max(agg[j][c][0], float(v.max())); agg[j][c][1] = max(agg[j][c][1], float(np.percentile(v, 99.9)))
                if sname == "walk":
                    cyc = SL.rainflow(ch["M_bend"]); r = np.array([a for a, _, _ in cyc]); n = np.array([c for _, _, c in cyc])
                    big = r >= 0.25 * r.max(); rf[j].append(float(n[big].sum()))
        res[sname] = dict(peaks=agg, runs=nrun, fell=fell, dur_s=dur,
                          rf_cycles_per_s={j: (sum(rf[j]) / dur if dur and rf[j] else None) for j in J})
    json.dump(res, open(os.path.join(OUT, "loads_table.json"), "w"), indent=1)
    rows = []
    for j in J:
        w, p, s = res["walk"]["peaks"][j], res["push"]["peaks"][j], res["stand"]["peaks"][j]
        rows.append([j, f"{s['F_radial'][0]:.0f} / {s['M_bend'][0]:.2f}",
                     f"{w['F_radial'][0]:.0f} ({w['F_radial'][1]:.0f})", f"{w['F_axial'][0]:.0f}", f"{w['M_axis'][0]:.2f} ({w['M_axis'][1]:.2f})", f"{w['M_bend'][0]:.2f} ({w['M_bend'][1]:.2f})",
                     f"{p['F_radial'][0]:.0f}", f"{p['F_axial'][0]:.0f}", f"{p['M_axis'][0]:.2f}", f"{p['M_bend'][0]:.2f}",
                     f"{res['walk']['rf_cycles_per_s'][j] * 3600:.0f}" if res["walk"]["rf_cycles_per_s"][j] else "-"])
    print(md(rows, ["joint", "stand F rad N / M bend Nm", "walk F radial N (p99.9)", "walk F axial N", "walk M axis Nm (p99.9)", "walk M bend Nm (p99.9)",
                    "push F radial N", "push F axial N", "push M axis Nm", "push M bend Nm", "walk M bend cycles per h (rainflow, over 25 % of max range)"]))
    print("runs", {k: (v["runs"], v["fell"], round(v["dur_s"], 1)) for k, v in res.items()})
    return res

def falls_table():
    R = json.load(open(os.path.join(SCR, "falls", "summary_falls.json")))
    cases = sorted(set(r["case"] for r in R if r.get("t_hit")))
    out = {}
    rows = []
    for c in cases:
        out[c] = {}
        for lv, (tc, dr) in LEVELS.items():
            rr = [r for r in R if r["case"] == c and r.get("tc") == tc and r.get("dr") == dr]
            if not rr: continue
            r = rr[0]
            bodies = {b: v for b, v in r["bodies"].items() if b not in ("foot_assembly", "foot_assembly_2")}
            top = max(bodies.items(), key=lambda kv: kv[1]["peak_N"])
            keff = top[1]["peak_N"] / max(top[1]["pen_mm_at_peak"], 1e-3) * 1000
            mj = {j: r["joints"][j] for j in J}
            out[c][lv] = dict(hit=top[0], peak_N=top[1]["peak_N"], pen_mm=top[1]["pen_mm_at_peak"], k_eff_N_per_m=keff,
                              v_down=top[1]["v_pre_down_mps"], impulse_30ms=top[1]["impulse_first30ms_Ns"],
                              acc_head_g=r["acc_peak_g"].get("head_assembly"), acc_trunk_g=r["acc_peak_g"].get("trunk_assembly"), joints=mj)
            rows.append([c, lv, top[0], f"{top[1]['peak_N']:.0f}", f"{keff / 1e6:.2f}", f"{r['acc_peak_g'].get('head_assembly', 0):.0f}",
                         f"{r['acc_peak_g'].get('trunk_assembly', 0):.0f}", f"{mj['head_roll']['F_total']:.0f}", f"{mj['neck_pitch']['M_bend']:.1f}",
                         f"{max(mj['left_hip_pitch']['M_bend'], mj['right_hip_pitch']['M_bend']):.1f}", f"{max(mj['left_knee']['M_axis'], mj['right_knee']['M_axis']):.1f}",
                         f"{max(mj['left_ankle']['F_total'], mj['right_ankle']['F_total']):.0f}"])
    json.dump(out, open(os.path.join(OUT, "falls_table.json"), "w"), indent=1)
    print(md(rows, ["fall", "contact level", "printed part body hit hardest", "peak contact N", "K eff (MN/m)", "head g", "trunk g",
                    "head_roll joint F N", "neck_pitch M bend Nm", "hip pitch M bend Nm", "knee M axis Nm", "ankle F N"]))
    return out

# ---------------------------------------------------------------------------------------------------------------
# Fatigue: Ezeh and Susmel 2018 reference curve for 3D-printed PLA (probability of survival over 95 %): negative
# inverse slope k = 5.5, endurance limit at N_A = 2e6 cycles = 10 % of the ultimate tensile strength, with the
# maximum stress of the cycle as the reference stress (their mean stress rule). UTS: in-plane 47.1 MPa (Overture PLA
# TDS v5.1, XY), interlayer 22 MPa (Ezeh and Susmel 2019 conservative static reference). Miner sum over the rainflow
# cycles of the stress history at the critical element of each FEA study.
K_SN, N_A, FRAC_A = 5.5, 2.0e6, 0.10
def damage(stress, uts):
    cyc = SL.rainflow(np.asarray(stress, float))
    if not cyc: return 0.0, 0.0
    D = 0.0; smax_all = 0.0
    for rng, mean, n in cyc:
        smax = mean + rng / 2.0
        if smax <= 0: continue
        smax_all = max(smax_all, smax)
        D += n / (N_A * (FRAC_A * uts / smax) ** K_SN)
    return D, smax_all

def max_amplitude(stress):
    cyc = SL.rainflow(np.asarray(stress, float))
    return max((r / 2.0 for r, _, _ in cyc), default=0.0)

def fatigue_table():
    rows = []; out = {}
    for f in sorted(glob.glob(os.path.join(SCR, "fea", "*_walk_hist.npz"))):
        st = os.path.basename(f).replace("_walk_hist.npz", "")
        d = np.load(f, allow_pickle=True); names = d["names"]; vm = d["vm"]; szz = d["szz"]
        res = {}
        for case in ("walk_forward_0.15", "turn_1.0", "walk_side_0.2", "walk_backlash"):
            Dv = Dz = 0.0; dur = 0.0; smv = smz = 0.0; amp = 0.0
            for run in sorted(set(n for n in names if n.startswith(case))):
                sel = names == run; n = int(sel.sum()); dur += n * 0.004       # 250 Hz samples (every second 2 ms step)
                dv, sv = damage(vm[sel], 47.1); dz, sz = damage(np.clip(szz[sel], 0, None), 22.0)
                Dv += dv; Dz += dz; smv = max(smv, sv); smz = max(smz, sz); amp = max(amp, max_amplitude(vm[sel]))
            if dur == 0: continue
            hours = dur / 3600.0
            life_v = hours / Dv if Dv > 0 else float("inf"); life_z = hours / Dz if Dz > 0 else float("inf")
            res[case] = dict(walk_s=dur, D_per_h_vm=Dv / hours, D_per_h_szz=Dz / hours, life_h=min(life_v, life_z),
                             smax_vm=smv, smax_szz=smz, limit_mode="interlayer" if life_z < life_v else "in-plane", amp_vm=amp,
                             cycles_per_h=None)
        out[st] = res
        for case, r in res.items():
            rows.append([st, case, f"{r['smax_vm']:.2f}", f"{r['smax_szz']:.2f}", f"{r['amp_vm']:.2f}", f"{r['life_h']:.3g}", r["limit_mode"],
                         "yes" if r["life_h"] < 100 else "no", "yes" if r["amp_vm"] < 35.8 else "NO"])
    json.dump(out, open(os.path.join(OUT, "fatigue_table.json"), "w"), indent=1, default=float)
    print(md(rows, ["FEA study", "walk case", "max von Mises MPa", "max interlayer tension MPa", "largest von Mises amplitude MPa",
                    "life h, design curve (P_s 95 %)", "limit", "under 100 h (design curve)", "amplitude under 35.8 MPa (best-case data, in-plane)"]))
    return out


# ---------------------------------------------------------------------------------------------------------------
# Fasteners and inserts
SIG_B = 47.1          # MPa, PLA bearing allowable = the TDS XY tensile strength (ASSUMPTION: bearing >= tensile)
TAU_PLA = (0.577 * 22.0, 0.577 * 47.1)   # MPa shear (von Mises) from the 22 MPa conservative and the 47.1 MPa TDS strengths
INSERT_PULL = (1354.0, 1552.0)            # N, M3 heat-set in FDM PLA, 3 wall thicknesses x 3 infill patterns (Eng. Proc. 2026)
INSERT_TORQUE = 3.5                      # N m, CNC Kitchen M3 inserts in PLA (torque-out), search result text
INSERT_SIDE = (0.5 * 4.6 * 5.7 * SIG_B, 4.6 * 5.7 * SIG_B)   # N, lateral: knurl OD x length x bearing, half as the low end (ASSUMPTION)
MARGIN = dict(walk=2.0, push=2.0, fall_soft=1.2, fall_mid=1.2)

def strip_pla(d, L):
    """thread strip of a self-tapping screw in a printed PLA pilot: 0.6 pi d L tau (shear area of a formed internal
    thread, ASSUMPTION), for both shear strengths"""
    return tuple(0.6 * np.pi * d * L * t for t in TAU_PLA)

def fastener_table():
    I = json.load(open(os.path.join(SCR, "interfaces.json")))
    G = json.load(open(os.path.join(SCR, "interface_groups.json")))
    F = SI.fasteners(); byid = {x["id"]: x for x in F}
    rows = []; out = []
    # 1. horn screws: PLA bearing (shear) and head pull-through plug (tension)
    for j in J:
        for kind in ("drive", "idle"):
            g = G[j].get(kind)
            if not g or not g.get("ids"): continue
            x = byid[g["ids"][0]]; t = float(x["near"]); d = 3.0
            cap_b = SIG_B * d * t; dk = x["head"]["dk"] if x.get("head") else 5.5
            cap_t = min(np.pi * dk * t * TAU_PLA[0], np.pi / 4 * (dk ** 2 - 3.3 ** 2) * SIG_B)
            r = dict(group=f"{j} {kind} horn", n=g["n"], spec=g["spec"], part=g["part"], t_pla=t, cap_shear=cap_b, cap_tension=cap_t, loads={})
            for sname in ("walk", "push", "fall_default", "fall_soft", "fall_mid", "fall_hard"):
                a = I.get(sname, {}).get(j, {})
                sh = a.get(f"{kind}_shear", 0.0); tA = a.get(f"{kind}_tension_A", 0.0); tB = a.get(f"{kind}_tension_B", 0.0)
                r["loads"][sname] = dict(shear=sh, tension_A=tA, tension_B=tB, SF_shear=cap_b / max(sh, 1e-9), SF_tension_A=cap_t / max(tA, 1e-9),
                                         SF_tension_B=cap_t / max(tB, 1e-9))
            out.append(r)
    # 2. servo case screws (M2 self-tapping into the PA+GF case): PLA bearing of the bracket hole
    for j in J:
        cs = G[j]["case"]
        if not cs: continue
        x = byid[cs[0]["id"]]; t = float(x["near"]); d = 2.0; cap_b = SIG_B * d * t
        r = dict(group=f"{j} servo case screws", n=len(cs), spec=", ".join(sorted(set(c["spec"] for c in cs))), part=", ".join(sorted(set(c["part"] for c in cs))),
                 t_pla=t, cap_shear=cap_b, cap_tension=None, loads={})
        for sname in ("walk", "push", "fall_default", "fall_soft", "fall_mid", "fall_hard"):
            a = I.get(sname, {}).get(j, {}); sh = a.get("case_shear", 0.0); pl = a.get("case_pull", 0.0)
            r["loads"][sname] = dict(shear=sh, pull=pl, SF_shear=cap_b / max(sh, 1e-9))
        out.append(r)
    json.dump(out, open(os.path.join(OUT, "fastener_table.json"), "w"), indent=1, default=float)
    for r in out:
        L = r["loads"]
        def sf(k, key): return f"{L[k][key]:.1f}" if k in L else "-"
        rows.append([r["group"], r["n"], r["part"], f"{r['t_pla']:.1f}", f"{r['cap_shear']:.0f}",
                     f"{L['walk']['shear']:.0f} / {sf('walk', 'SF_shear')}", f"{L['push']['shear']:.0f} / {sf('push', 'SF_shear')}",
                     f"{L['fall_soft']['shear']:.0f} / {sf('fall_soft', 'SF_shear')}", f"{L['fall_mid']['shear']:.0f} / {sf('fall_mid', 'SF_shear')}"])
    print(md(rows, ["screw group", "n", "printed part", "PLA t mm", "PLA bearing cap. N", "walk N / SF", "push N / SF", "fall soft N / SF", "fall mid N / SF"]))
    return out


# ---------------------------------------------------------------------------------------------------------------
# FEA safety factors, the hot case and PETG
HOT = {  # strength and modulus retention of printed PLA against room temperature (sources in STRUCTURE_TWIN.md)
    "50 C": dict(strength=50.0 / 80.0, modulus=0.84, src_s="Slavkovic et al. 2024, compression stress about 80 / 60 / 50 MPa at 25 / 37 / 50 C",
                 src_m="Grasso et al. 2018, printed PLA stiffness down about 16 % from 40 to 50 C (flat below 40 C)"),
    "60 C": dict(strength=None, modulus=350.0 / 1400.0, src_s="BLOCKER: no strength value at 60 C found for printed PLA",
                 src_m="Grasso et al. 2018 (as cited in a search result): about 1400 MPa at 30 C, 350 MPa at 60 C"),
}
PETG = dict(X=34.0, Z=23.0, E=1810.0, hdt_045=69.0, hdt_18=62.0, tg=66.0, src="Bambu PETG HF TDS V1.0 (tensile 34 +- 4 X-Y, 23 +- 4 Z, E 1810 X-Y; HDT 69 C at 0.45 MPa, 62 C at 1.8 MPa)")
HOT_PARTS = {"knee_to_ankle_left_sheet": "54 to 66 C (continuous and 50/50 walking), 47 to 55 C (25/75)",
             "knee_to_ankle_right_sheet": "54 to 66 C (continuous and 50/50 walking), 47 to 55 C (25/75)",
             "leg_spacer": "between the knee sheets (not listed by the thermal twin; ASSUMPTION: as the sheets)",
             "left_roll_to_pitch": "up to 61 C (backlash walk, warm room)", "right_roll_to_pitch": "up to 61 C (backlash walk, warm room)",
             "trunk_top": "up to 61 C", "body_middle_bottom": "belly floor under the BEC above 50 C", "battery_pack_lid": "above 50 C at the 2815 and BMS"}

def fea_table():
    rows = []; out = {}
    for f in sorted(glob.glob(os.path.join(SCR, "fea", "*.json"))):
        if "_v1_" in f: continue
        d = json.load(open(f)); st = d["study"]
        if not d["meshes"]: continue
        m = d["meshes"][-1]; C = m["cases"]
        r = dict(study=st, members=d["members"], nodes=m["nodes"], tets=m["tets"])
        for k in ("walk", "push"):
            if k in C: r[k] = dict(SF=1 / C[k]["FI"], mode=C[k]["mode"], zone=C[k]["zone"], member=C[k]["member"], where=C[k]["where_link"], sample=C[k]["sample"],
                                   vm=C[k]["vm"], szz=C[k]["szz"], load=C[k]["load"], insert_loads=C[k].get("insert_loads"))
        if "fall" in C:
            per = C["fall"]["per_run"]; lv = {}
            for name, (tc, dr) in LEVELS.items():
                tag = f"_tc{tc:g}_dr{dr:g}"
                vals = {k: v for k, v in per.items() if k.endswith(tag)}
                if vals:
                    worst = max(vals.items(), key=lambda kv: kv[1]["FI"])
                    lv[name] = dict(SF=1 / worst[1]["FI"], run=worst[0], member=worst[1]["member"], mode=worst[1]["mode"], where=worst[1]["where_link"],
                                    SF_all={k.replace(tag, ""): round(1 / v["FI"], 3) for k, v in vals.items()})
            r["fall"] = lv
        # hot case: same stresses (uniform modulus loss leaves a force-loaded linear solution unchanged), lower strength
        hot = {}
        if "walk" in r:
            hot_member = r["walk"]["member"] in HOT_PARTS
            for T, h in HOT.items():
                hot[T] = dict(applies=hot_member, SF_walk=(r["walk"]["SF"] * h["strength"]) if h["strength"] else None,
                              SF_push=(r["push"]["SF"] * h["strength"]) if (h["strength"] and "push" in r) else None,
                              deflection_factor=1 / h["modulus"])
            # PETG: room-temperature strength ratio, held to about 60 C (below its 1.8 MPa HDT of 62 C; ASSUMPTION, no hot data)
            ratio = (PETG["Z"] / 22.0) if r["walk"]["mode"] == "interlayer" else (PETG["X"] / 47.1)
            hot["PETG"] = dict(SF_walk=r["walk"]["SF"] * ratio, SF_push=r["push"]["SF"] * ratio if "push" in r else None, strength_ratio=ratio,
                               deflection_factor=E_PLA / PETG["E"])
        r["hot"] = hot
        out[st] = r
    json.dump(out, open(os.path.join(OUT, "fea_table.json"), "w"), indent=1, default=float)
    for st, r in out.items():
        fl = r.get("fall", {})
        rows.append([st, ", ".join(r["members"]), f"{r['walk']['SF']:.2f}" if "walk" in r else "-", f"{r['push']['SF']:.2f}" if "push" in r else "-",
                     f"{fl['soft']['SF']:.2f}" if "soft" in fl else "-", f"{fl['mid']['SF']:.2f}" if "mid" in fl else "-",
                     f"{fl['MuJoCo default']['SF']:.2f}" if "MuJoCo default" in fl else "-",
                     f"{r['walk']['member']}, {r['walk']['zone']}, {r['walk']['mode']}, at {r['walk']['where']} mm ({r['walk']['sample']})" if "walk" in r else "-",
                     f"{r['hot']['50 C']['SF_walk']:.2f}" if r.get("hot", {}).get("50 C", {}).get("SF_walk") else "-",
                     f"{r['hot']['PETG']['SF_walk']:.2f}" if r.get("hot", {}).get("PETG") else "-"])
    print(md(rows, ["study", "parts", "SF walk", "SF push", "SF fall soft", "SF fall mid", "SF fall MuJoCo default", "weak spot (walking peak)", "SF walk at 50 C (PLA)", "SF walk PETG"]))
    return out

E_PLA = 2641.0

if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("loads", "all"): loads_table()
    if what in ("falls", "all"): falls_table()
    if what in ("fatigue", "all"): fatigue_table()
    if what in ("fasteners", "all"): fastener_table()
    if what in ("fea", "all"): fea_table()
