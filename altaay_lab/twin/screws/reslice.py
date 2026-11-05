"""Re-slice the 3 parts changed by D38 and the coupon session with K1 to K4 added, with the repo's slice.py (D22 light
profile). Outputs outside the repo: /home/user/v1_out/screws/{coupons_all,slice_c,slice_p}. Prints the numbers."""
import json, os, subprocess, sys
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, "..", ".."))
PRINT = os.path.join(LAB, "print")
OUT = "/home/user/v1_out/screws"
CD, SC, SP = os.path.join(OUT, "coupons_all"), os.path.join(OUT, "slice_c"), os.path.join(OUT, "slice_p")
env = dict(os.environ, ODM_SLICER_THREADS="2")
run = lambda *a: subprocess.run(["nice", "-n", "10", sys.executable, *a], cwd=PRINT, check=True, env=env)

run("make_coupons.py", CD)
man = json.load(open(os.path.join(CD, "manifest.json")))
UPV = {"+x": [1, 0, 0], "-x": [-1, 0, 0], "+z": [0, 0, 1]}
K = [("K1a_body_middle_top", "+x", "insert"), ("K1b_body_front", "+x", ""), ("K2a_body_middle_bottom", "+z", "insert"),
     ("K2b_body_back", "-x", "pilot"), ("K3_cable_clip", "+z", ""), ("K4_tie_bridge", "+z", "")]
for name, up, rings in K:
    m = trimesh.load(os.path.join(HERE, "stl", name + ".stl"))
    R = trimesh.geometry.align_vectors(UPV[up], [0, 0, 1])
    m.apply_transform(R)
    m.apply_translation([-m.bounds[0][0], -m.bounds[0][1], -m.bounds[0][2]])
    m.export(os.path.join(CD, name + ".stl"))
    if not any(c["file"] == name + ".stl" for c in man["coupons"]):
        man["coupons"].append(dict(id=name.split("_")[0], file=name + ".stl", material="PLA", overrides="", rings=rings,
                                   source="altaay_lab/twin/screws/stl/%s.stl (D38 coupon, %s up)" % (name, up)))
json.dump(man, open(os.path.join(CD, "manifest.json"), "w"), indent=1)
run("slice.py", "coupons", "--out", SC, "--coupons", CD)
run("slice.py", "parts", "--out", SP, "--only", "body_front.stl,body_middle_top.stl,body_middle_bottom.stl")
cj = json.load(open(os.path.join(SC, "coupons.json")))
print("SESSION", json.dumps(cj["session"])[:1500])
print("K", {k: (round(v["g"], 2), round(v["s"] / 3600, 2), round(v["g_support"], 2)) for k, v in cj["coupons"].items() if k.startswith("K")})
for f in sorted(os.listdir(SP)):
    if f.endswith(".json"):
        print("PART", f, json.dumps(json.load(open(os.path.join(SP, f))))[:600])
