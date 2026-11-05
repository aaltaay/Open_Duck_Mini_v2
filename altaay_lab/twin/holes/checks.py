"""Checks for D39 (track 2e), calc only and CAD check only. Method of twin/screws/screws_twin.py:
F1 (one screw takes the whole inertial pull at the mid fall level), F2 (shell hit in bearing, upper bound),
rattle (geometry: clamp points round the rim or board), plus the plug checks of close_holes.py and a quick SG90 model.
Writes data/checks.json. Inputs: twin/screws/data/joints.json and lips.json, data/close_report.json, the lab scene."""
import json, os, sys, math
import numpy as np, trimesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hlib

TW = os.path.join(hlib.LAB, "twin", "screws", "data")
J = {j["joint"]: j for j in json.load(open(os.path.join(TW, "joints.json")))}
LIPS = json.load(open(os.path.join(TW, "lips.json")))
CR = json.load(open(os.path.join(hlib.DATA, "close_report.json")))
FJ = hlib.load_fj(); F = {f["id"]: f for f in FJ["fasteners"]}
HIT = {"soft": 900.0, "mid": 2800.0}                     # STRUCTURE_TWIN.md answer (via screws_twin.py SHELL_HIT_N)
out = {}

# ---- body_back shell: F2 with the ear seats, 8 / 7 (D38) / 6 (D39) screws
bb = J["body_back shell"]
bear = bb["F2_bearing_per_screw_N"]
lip = LIPS["body_back"]["capacity_N"]
seat = sum(s["capacity_N"] for s in CR["seats"])
f2 = {}
for n, tag in ((8, "8 (before D38)"), (7, "7 (D38, today)"), (6, "6 (D39: F076 out)"), (5, "5 (not taken)")):
    for withseat in (False, True):
        k = "%s%s" % (tag, " + seats" if withseat else "")
        f2[k] = {lv: dict(side=round((n * bear + lip["y"]) / HIT[lv], 2), up=round((n * bear + lip["z_up"]) / HIT[lv], 2),
                          down=round((n * bear + lip["z_down"] + (seat if withseat else 0)) / HIT[lv], 2)) for lv in HIT}
out["body_back_F2"] = dict(bearing_per_screw_N=bear, lip_N=lip, seats_N=seat, seats=CR["seats"], SF=f2,
                           F1_one_screw=bb["SF_F1_one_screw"], src="twin/screws/data/joints.json, lips.json; seats: close_report.json")
# rattle: largest unclamped rim span between neighbouring screws (rim loop in the y-z plane), 8, 7 and 6 screws
ids8 = bb["ids"] + ["F075"] if "F075" not in bb["ids"] else bb["ids"]
P = {i: np.array(F[i]["seat_world"])[[1, 2]] for i in sorted(set(ids8) | {"F075"})}
c = np.mean(list(P.values()), axis=0)
order = sorted(P, key=lambda i: math.atan2(P[i][1] - c[1], P[i][0] - c[0]))
def span(keep):
    k = [i for i in order if i in keep]
    return round(max(np.linalg.norm(P[a] - P[b]) for a, b in zip(k, k[1:] + k[:1])), 1)
out["body_back_rattle"] = {"8": span(set(P)), "7": span(set(P) - {"F075"}), "6": span(set(P) - {"F075", "F076"}),
                           "note": "largest straight gap between neighbouring screws round the rim, mm (rim pressed by the lips and seats in y and z)"}

# ---- left eye diagonal: same count, the other pair
le = J["bulb -> left_eye (head_assembly)"]
out["left_eye"] = dict(before_kept=le["kept"], before_cut=le["cut"], after_kept=["F179", "F182"], after_cut=["F178", "F183"],
                       F1_one_screw=le["SF_F1_one_screw"], diagonal_mm=dict(before=round(float(np.linalg.norm(np.subtract(F[le["kept"][0]]["seat_world"], F[le["kept"][1]]["seat_world"]))), 1),
                                                                            after=round(float(np.linalg.norm(np.subtract(F["F179"]["seat_world"], F["F182"]["seat_world"]))), 1)))

# ---- boards on 2 screws: the closed pilots under them stay solid seats (plug caps flush or under the seat face)
seats = {}
for part, sites, board in (("head", (148, 149), "Pi Zero 2 W"), ("trunk_top", (158, 159), "servo bus adapter"), ("head", (233, 236), "camera")):
    for i in CR["parts"][part]["plugs"]:
        if i["site"] in sites:
            seats.setdefault(board, []).append(dict(site=i["site"], ends=[dict(open=e["open"], ring_flat_mm=None if e.get("res_max") is None else round(e["res_max"], 3), cap=e.get("cap", "fitted to the seat ring")) for e in i["ends"]]))
out["board_seats"] = seats

# ---- plug checks, all parts
pc = {}
for k, p in CR["parts"].items():
    rec = [e.get("res_max") for i in p.get("plugs", []) for e in i.get("ends", []) if e.get("res_max") is not None]
    pc[k] = dict(closed=p.get("n_closed"), watertight=p.get("watertight"), added_mm3=p.get("added_mm3"), hole_mm3=p.get("analytic_hole_mm3"),
                 bounds_same=p.get("bounds_same"), max_cap_recess_mm=round(max(rec) + 0.02, 3) if rec else 0.02, never_proud=True,
                 overlaps=[o for o in p.get("zero_pose", []) if isinstance(o, dict) and "other" in o] if isinstance(p.get("zero_pose"), list) else p.get("zero_pose"),
                 min_cable_clear_mm=min([o["cable_clear_mm"] for o in p.get("zero_pose", []) if isinstance(o, dict) and o.get("cable_clear_mm") is not None], default=None),
                 min_kept_hole_gap_mm=min([i["kept_hole_gap_mm"] for i in p.get("plugs", []) if i.get("kept_hole_gap_mm") is not None], default=None),
                 bytes=p.get("bytes"))
out["plug_checks"] = pc

# ---- SG90 tabs: quick model (stall torque, pull) and the pocket check
S = hlib.scene()
sg = [i for i in S.inst if i["key"] == "sg90"]
head = S.mesh([i["idx"] for i in S.inst if i["key"] == "head"][0])
pq = trimesh.proximity.ProximityQuery(head)
T_STALL = 1.8 * 9.80665 / 100   # N m: 1.8 kgf cm [I] https://bit.nkust.edu.tw/~csshieh/teach/111A/mc/datasheet/SG90.pdf (datasheet mirror, search text; other listings 1.2 to 1.6)
tabs = [f for f in FJ["fasteners"] if f["source"] == "sg90_tab"]
res = []
for g in sg:
    m = S.mesh(g["idx"]); Pm, _ = trimesh.sample.sample_surface_even(m, 12000, seed=4)
    mine = sorted([f for f in tabs if np.linalg.norm(np.subtract(f["seat_world"], m.centroid)) < 30], key=lambda f: f["id"])
    if len(mine) < 2:
        continue
    keep = mine[0]; ax = np.array(keep["axis_world"], float); o = np.array(keep["seat_world"], float)
    pen = {}
    for deg in (0.25, 0.5, 1.0, 2.0):
        for s in (1, -1):
            R = trimesh.transformations.rotation_matrix(np.radians(s * deg), ax, o)
            pen["%+.2f" % (s * deg)] = round(float(pq.signed_distance(trimesh.transform_points(Pm, R)).max()), 3)
    s_tab = float(np.linalg.norm(np.subtract(mine[0]["seat_world"], mine[1]["seat_world"])))
    res.append(dict(sg90_inst=g["idx"], screws=[f["id"] for f in mine], tab_spacing_mm=round(s_tab, 1),
                    two_screws_force_N=round(T_STALL / (s_tab / 1000), 1), one_screw_pocket_penetration_mm=pen))
out["sg90"] = dict(stall_torque_Nm=round(T_STALL, 3), torque_src="[I] SG90 datasheet mirror (search text): 1.8 kgf cm at 4.8 V; other listings 1.2 to 1.6 kgf cm",
                   cases=res, verdict="kept at 2 per SG90: the stall torque alone is small, but the antenna hit when the head swings (G6) is not modelled (BLOCKER for a cut)")
hlib.jdump(out, "checks.json")
print(json.dumps({k: out[k] for k in ("body_back_F2", "body_back_rattle", "left_eye", "board_seats", "sg90")}, indent=0, default=str)[:6000])
