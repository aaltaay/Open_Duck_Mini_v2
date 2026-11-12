"""Shin drive eye on the structure-twin load set (FEA pass only).

Same element, assembler, solver, 1 mm stress average and failure index as st_fea.py.
Voxel pitch 0.8 mm, inside the 0.75 to 0.8 mm band of the topology pass.
Loads are a new run of st_loads.py (walk and push) and the soft-fall level of
st_falls.py (time constant 0.0158 s, damping ratio 0.2).

Usage: ODM_SCRATCH=<scratch> python3 eye_fea.py [case ...]
"""
import os
import sys
import json
import shutil
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
STRUCT = os.path.abspath(os.path.join(HERE, ".."))
os.environ.setdefault("ODM_SCRATCH", "/tmp/odm_twin_structure")
os.environ["ST_VOXEL_MM"] = os.environ.get("ST_VOXEL_MM", "0.8")
sys.path.insert(0, STRUCT)
import numpy as np  # noqa: E402
import st_fea as FE  # noqa: E402
import st_fea_run as FR  # noqa: E402

# X, Z, S in MPa. S = Z is the structure twin's assumption, not a datasheet shear.
# E is the X-Y modulus, MPa. Sources are named in SHIN_EYE.md.
MATS = {
    "PLA": (47.1, 22.0, 22.0, 2641.0),
    "PETG": (34.0, 23.0, 23.0, 1810.0),
    "PLA-CF": (38.0, 26.0, 26.0, None),
    "ASA": (37.0, 31.0, 31.0, 2450.0),
    "PA6-CF": (102.0, 48.0, 48.0, 4430.0),
}
TOPO = os.path.join(STRUCT, "topology", "stl", "shin_left_sheet.stl")
TAPER = os.path.join(HERE, "stl", "shin_left_sheet_taper.stl")
CBORE = os.path.join(HERE, "stl", "shin_left_sheet_taper_cbore.stl")
WEB = os.path.join(HERE, "stl", "shin_left_sheet_web.stl")


def iso(E, nu):
    lam = E * nu / ((1 + nu) * (1 - 2 * nu))
    mu = E / (2 * (1 + nu))
    M = np.zeros((6, 6))
    M[:3, :3] = lam
    M[0, 0] += 2 * mu
    M[1, 1] += 2 * mu
    M[2, 2] += 2 * mu
    M[3, 3] = M[4, 4] = M[5, 5] = mu
    return M


def prepare(stl, prof, solid, E_left):
    d = tempfile.mkdtemp(prefix="shin_eye_")
    if stl:
        shutil.copy(stl, os.path.join(d, "shin_left_sheet.stl"))
        FE.PRINT = d
    else:
        FE.PRINT = os.path.join(FE.REPO, "print")
    st = dict(FR.STUDIES["shin_segment"])
    if prof:
        st = dict(st, prof_over={"shin_left_sheet": prof})
    FR.STUDIES["shin_eye_tmp"] = st
    P, S = FR.setup("shin_eye_tmp", 1)
    print("mesh", FE.PRINT, {k: round(v, 0) for k, v in P.member_vol.items()}, flush=True)
    if solid:
        k = [i for i, M in enumerate(P.members) if M["name"] == "shin_left_sheet"][0]
        P.zone[(P.mem == k) & (P.zone == 3)] = 0
        P.material()
    if E_left:
        k = [i for i, M in enumerate(P.members) if M["name"] == "shin_left_sheet"][0]
        sel = P.mem == k
        Cs = iso(E_left, FE.NU_SOLID)
        P.C[sel] = Cs
        inf = sel & (P.zone == 3)
        for rho in np.unique(P.infill[inf]) if inf.any() else []:
            P.C[inf & (P.infill == rho)] = iso(E_left * rho ** FE.GYROID_N, 0.30)
    if solid or E_left:
        P.assemble()
        if hasattr(P, "_ml"):
            del P._ml
    sig = FR.solve_units(P, S)
    return P, S, sig


def one(P, S, sig, which, strengths):
    hist, names = FR.history(S, which)
    if not len(hist):
        return None
    r = FR.evaluate(P, S, sig, hist, names, strengths=strengths[:3])[0]
    out = dict(SF=round(1.0 / max(r["FI"], 1e-9), 2), FI=round(r["FI"], 4), mode=r["mode"],
               zone=r["zone"], member=r["member"], where_link=r["where_link"], sample=r["sample"],
               vm=round(r["vm"], 2), szz=round(r["szz"], 2), tz=round(r["tz"], 2))
    if which == "fall":
        sfs = []
        per = {}
        for nm in sorted(set(names.tolist())):
            sel = names == nm
            P._mag_key = None
            rr = FR.evaluate(P, S, sig, hist[sel], names[sel], k_elem=800, strengths=strengths[:3])[0]
            sf = 1.0 / max(rr["FI"], 1e-9)
            sfs.append(sf)
            per[nm] = round(sf, 2)
        out["soft_worst"] = round(min(sfs), 2)
        out["n_under_1_2"] = int(sum(s < 1.2 for s in sfs))
        out["n"] = len(sfs)
        out["per"] = per
    return out


def run(name, stl, prof=None, solid=False, E_left=None, mats=("PLA",)):
    t0 = time.time()
    P, S, sig = prepare(stl, prof, solid, E_left)
    rows = []
    for mat in mats:
        X, Z, S_, E = MATS[mat]
        # a modulus override already baked into this solve; do not pretend another E
        rec = dict(case=name, material=mat, E_solve=E_left or FE.E_SOLID,
                   X=X, Z=Z, S=S_, pitch_mm=float(os.environ["ST_VOXEL_MM"]),
                   nodes=len(P.X), tets=len(P.T))
        for which in ("walk", "push", "fall"):
            P._mag_key = None
            rec[which] = one(P, S, sig, which, (X, Z, S_, E))
        rows.append(rec)
        w = rec["walk"]
        f = rec["fall"]
        print(f"{name} {mat}: walk {w['SF']} {w['mode']} {w['zone']} at {w['where_link']} "
              f"soft {f['soft_worst']} ({f['n_under_1_2']} of {f['n']}) "
              f"{len(P.X)} nodes {time.time() - t0:.0f}s", flush=True)
    return rows


CASES = [
    ("stock", None, None, False, None, ("PLA", "PETG", "PLA-CF", "ASA", "PA6-CF")),
    ("collar", TOPO, None, False, None, ("PLA", "PETG", "PLA-CF", "ASA", "PA6-CF")),
    ("taper", TAPER, None, False, None, ("PLA", "PETG", "PLA-CF", "ASA", "PA6-CF")),
    ("taper_cbore", CBORE, None, False, None, ("PLA",)),
    ("taper_w5i40", TAPER, dict(walls=5, infill=0.40), False, None, ("PLA",)),
    ("taper_solid", TAPER, None, True, None, ("PLA",)),
    ("taper_upx", TAPER, dict(up="+x"), False, None, ("PLA",)),
    ("collar_pacf_E", TOPO, None, False, 4430.0, ("PA6-CF",)),
    ("taper_pacf_E", TAPER, None, False, 4430.0, ("PA6-CF",)),
    ("taper_petg_E", TAPER, None, False, 1810.0, ("PETG",)),
    ("collar_cbore", os.path.join(HERE, "stl", "shin_left_sheet_collar_cbore.stl"), None, False, None, ("PLA", "PA6-CF")),
    ("web", WEB, None, False, None, ("PLA", "PETG", "PLA-CF", "ASA", "PA6-CF")),
    ("web_pacf_E", WEB, None, False, 4430.0, ("PA6-CF",)),
    ("web_solid", WEB, None, True, None, ("PLA",)),
    ("web_cbore", os.path.join(HERE, "stl", "shin_left_sheet_web_cbore.stl"), None, False, None, ("PLA", "PA6-CF")),
    ("web_cbore_E", os.path.join(HERE, "stl", "shin_left_sheet_web_cbore.stl"), None, False, 4430.0, ("PA6-CF",)),
]


if __name__ == "__main__":
    want = sys.argv[1:]
    path = os.path.join(HERE, "fea.json")
    out = json.load(open(path)) if os.path.exists(path) else []
    done = {(r["case"], r["material"]) for r in out}
    for name, stl, prof, solid, E_left, mats in CASES:
        if want and name not in want:
            continue
        mats = tuple(m for m in mats if (name, m) not in done)
        if not mats:
            continue
        try:
            rows = run(name, stl, prof, solid, E_left, mats)
        except Exception as e:
            print("FAIL", name, type(e).__name__, e, flush=True)
            raise
        out.extend(rows)
        json.dump(out, open(path, "w"), indent=1)
    print("wrote", path, len(out))
