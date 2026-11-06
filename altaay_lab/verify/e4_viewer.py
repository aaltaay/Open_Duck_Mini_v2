"""E4: run viewer/make_viewer_data.py --out <scratch> (never --write-bom) and check its count checks: printed parts,
servos, inserts and bearings found in the CAD must equal the expected numbers (PRINT_CHECK.md, BOM.md lines 1, 16, 18).
Keeps manifest.json in the output folder: C1 reads its bom_full rows and node counts.

Usage: VERIFY_OUT=<folder outside the repo> python3 altaay_lab/verify/e4_viewer.py
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vlib as V  # noqa: E402

R = V.Result("E4", "Exploded-view data build and its CAD count checks (viewer/make_viewer_data.py)",
             "VERIFY_OUT=<out> python3 altaay_lab/verify/e4_viewer.py",
             "URDF zero pose with print/ STLs swapped in; printed parts, servos, inserts, bearings found vs expected; "
             "STL vs URDF frame check; BOM lines with a view mapping; eye washers drawn vs fasteners.json; heat shrink sleeves drawn "
             "vs the BOM_FULL count",
             "Fit of parts not in the CAD beyond their boxes; anything the page shows but does not count")
od = os.path.join(V.out_dir(), "e4_viewer")
os.makedirs(od, exist_ok=True)
R.inp(V.lab("viewer", "make_viewer_data.py"), V.lab("PRINT_CHECK.md"), V.lab("BOM.md"), V.lab("audit", "sites.json"),
      V.lab("audit", "placements.json"))
p = subprocess.run(["nice", "-n", "10", sys.executable, V.lab("viewer", "make_viewer_data.py"), "--out", od],
                   capture_output=True, text=True, timeout=3600)
log = p.stdout + p.stderr
open(os.path.join(od, "stdout.txt"), "w").write(log)
man = os.path.join(od, "manifest.json")
if p.returncode != 0 or not os.path.exists(man):
    R.not_run("make_viewer_data.py failed (exit %d): %s" % (p.returncode, log[-400:]))
    R.write()
    sys.exit(0)
m = re.search(r"printed parts found (\d+) / expected (\d+) over (\d+) STLs; servos (\d+) / (\d+); inserts (\d+) / (\d+)", log)
M = json.load(open(man))
_rw = next((r for r in M["bom_full"] if r.get("line") == "17l"), None)
_rh = next((r for r in M["bom_full"] if r["item"].startswith("Heat shrink")), None)
KEY_W = "%d/%s" % (len(_rw["nodes"]) if _rw else 0, _rw["qty"] if _rw else "-")
KEY_H = "%d/%s" % (sum(1 for n in M["nodes"].values() if n.get("sleeve")), _rh["qty"] if _rh else "-")
S = M["checklist"]["summary"]
if not m:
    R.find("FAIL", "count line not found in the viewer output", fix="check make_viewer_data.py output format")
else:
    pf, pe, nstl, sf, se, inf, ine = (int(x) for x in m.groups())
    bf, be = S["bearings"]["found"], S["bearings"]["expected"]
    R.ev("printed parts %d / %d over %d STLs; servos %d / %d; inserts %d / %d; bearings %d / %d" % (pf, pe, nstl, sf, se, inf, ine, bf, be))
    R.key("found in the CAD: printed parts %d/%d, servos %d/%d, inserts %d/%d, bearings %d/%d; drawn and counted: eye washers "
          "%s, heat shrink sleeves %s" % (pf, pe, sf, se, inf, ine, bf, be, KEY_W, KEY_H))
    for what, a, b in (("printed parts", pf, pe), ("servos", sf, se), ("inserts", inf, ine), ("bearings", bf, be)):
        if a != b:
            R.find("FAIL", "%s: %d found in the CAD, %d expected" % (what, a, b), fix="see the viewer checklist for the part")
pm = S.get("printed_mismatches") or []
if pm:
    R.find("FAIL", "printed mismatches: %s" % pm)
bm = S["bom"]["mismatches"]
R.ev("BOM lines %d (cad %d, placeholder %d, filament %d, not modelled %d); count mismatches %s" % (
    S["bom"]["lines"], S["bom"]["cad"], S["bom"]["placeholder"], S["bom"]["filament"], S["bom"]["not_modelled"], bm or "none"))
for b in bm:
    R.find("FAIL", "BOM line %s count in the view differs from BOM Need" % b)
meta = M["meta"]
bad_frames = {k: v for k, v in meta["frame_check_mm"].items() if v > 0.05}
R.ev("STL vs URDF frame check: %d parts, worst %.3f mm; assembly.json match %s; unmapped meshes %s" % (
    len(meta["frame_check_mm"]), max(meta["frame_check_mm"].values()), meta["assembly_json_match"], meta["unmapped"] or "none"))
if bad_frames:
    R.find("FAIL", "print STL and URDF frames differ over 0.05 mm (both bounding faces of an axis moved): %s" % bad_frames)
grown = meta.get("frame_grown_mm") or {}
R.ev("faces of the print STLs that moved against the URDF mesh (one face per axis: printed features the lab added, "
     "mm, + = grown): %s" % (grown or "none"))
for w in meta["warnings"]:
    R.find("WARN", "viewer warning: " + w)
R.ev("screws drawn %d (%s); cables drawn %d (%s)" % (S["screws"]["found"], meta["sources"].get("fasteners"),
                                                   S["cables"]["found"], meta["sources"].get("cables")))
# washers under screw heads (fasteners.json 'washer', D21 note) and heat shrink sleeves (BOM_FULL rule): drawn vs counted
nodes = M["nodes"]
fj = V.lab("fasteners", "fasteners.json")
want_w = sum(int(f["washer"].get("n", 1)) for f in json.load(open(fj))["fasteners"]
             if f.get("kind") == "screw" and f.get("washer") and not any(s in str(f.get("status") or "") for s in ("NOT FITTED", "LEAVE OUT")))
row_w = next((r for r in M["bom_full"] if r.get("line") == "17l"), None)
got_w = len(row_w["nodes"]) if row_w else 0
sl = [n for n in nodes.values() if n.get("sleeve")]
row_h = next((r for r in M["bom_full"] if r["item"].startswith("Heat shrink")), None)
R.ev("washers drawn %d (BOM_FULL row %s, %s pcs), fasteners.json fits %d; heat shrink sleeves drawn %d (%d with a netlist joint), "
     "BOM_FULL counts %s" % (got_w, row_w["id"] if row_w else "none", row_w["qty"] if row_w else "-", want_w, len(sl),
                             sum(1 for n in sl if n.get("sleeve_pins")), row_h["qty"] if row_h else "no row"))
if got_w != want_w or (row_w and V.num(row_w["qty"]) != want_w):
    R.find("FAIL", "washers: the 3D view draws %d and BOM_FULL counts %s, fasteners.json fits %d" % (
        got_w, row_w["qty"] if row_w else "none", want_w), fix="viewer/scene_extras.json washer items (two per eye screw, D21 note)",
        where="altaay_lab/viewer/scene_extras.json")
if row_h and (len(sl) != V.num(row_h["qty"]) or any(not n.get("sleeve_pins") for n in sl)):
    R.find("FAIL", "heat shrink: the 3D view draws %d sleeves (%d with no netlist joint), BOM_FULL counts %s" % (
        len(sl), sum(1 for n in sl if not n.get("sleeve_pins")), row_h["qty"]),
        fix="viewer/scene_extras.json or make_viewer_data.py step 10f", where="altaay_lab/viewer")
R.ev("GLB %.2f MB, %d nodes (output kept in the scratch folder, not in git)" % (meta["glb"]["bytes"] / 1e6, meta["glb"]["nodes"]))
R.write()
