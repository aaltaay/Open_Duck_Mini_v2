"""phase2_notes.py: writes COMPLETE3D.md section 9 and the history file of the V1 3D track from the phase 2 outputs.
Run last: python3 altaay_lab/twin/complete3d/phase2_notes.py   (numbers from cables3d.json, d12_ribbon.json, inventory.json)
"""
import datetime
import glob
import json
import os
from zoneinfo import ZoneInfo

from common import CABLES3D, HERE, LAB, OUT

NOW = datetime.datetime.now(ZoneInfo("America/New_York"))


def main():
    c3 = json.load(open(CABLES3D))
    C = {c["id"]: c for c in c3["cables"]}
    rib = json.load(open(os.path.join(HERE, "d12_ribbon.json")))
    inv = json.load(open(os.path.join(HERE, "inventory.json")))
    o = json.load(open(os.path.join(OUT, "phase2_data_out.json")))
    lp = rib.get("slack_loop_300") or {}
    n = inv["counts"]
    d13 = C["D13"]
    w13 = d13["wires"][0]
    chk = {k: C[k].get("check") for k in ("D10", "D12", "D13", "SP1", "SP2", "SP4", "SP5", "P15")}
    runs = sum(len(c.get("runs") or [1]) for c in c3["cables"])
    loops = ", ".join("radius %g mm, legs %.1f mm, %.2f mm clear" % (d["radius_mm"], d["leg_mm"], d["clr_exact_min_mm"])
                      for d in lp.get("loops", [])) or "none found clear (BLOCKER: lay it at TO9)"
    sec = """
## 9. Phase 2 applied (%s)

Phase 2 of the V1 3D track, after D34 (300 mm camera cable, the spare in a gentle loop; camera screws M2x5 in pilots drilled
to 4.5 mm) and D33 (head as upstream). CAD check only; lengths calc only. Scripts: phase2_data.py (data and code),
phase2_docs.py (docs), phase2_notes.py (this section and the history file); ribbon_d12.py now designs the 300 mm loop.

- Camera: drawn as its PCB (25 x 24 x 1.0 mm) on the measured boss faces, board centre 3.75 mm toward the lens row (the box
  that poked through the front wall is gone). F344 to F347 are M2x5 "camera to head", 4.0 mm engaged; the pilot drill step is
  print/PRINT_PLAN.md After printing (1/16 in bit, needs Ahmed's OK, $1.98 Walmart or $1.95 Zoro, read via search index).
- D12: the 300 mm flat strip, route %.1f mm (centre line, no twist), %.1f mm spare in %d gentle loop(s): %s. Check: %s.
  Drawn as a flat band in the viewer. 150 mm and 200 mm stay short (77.4 and 27.4 mm).
- D13 (new, D30): the OFF wire, Pi GPIO26 (pin 37) to the 2813 OFF input, 26 AWG on the P13 route plus the P12 hop and the
  header: zero pose %.1f mm, worst %s mm, cut %d mm, check %s. The 2813 OFF pad position is a stand-in (BLOCKER).
- P15 stays the button lead entry (the netlist names it 2813 A and B to the button, D30); its wires still name the 2815 SW
  and GND_SW pads: the 2813 pad names need the Pololu 2813 pinout (BLOCKER, pololu.com not read here). Check: %s.
- D10: fan-out runs %s; check %s. SP1, SP2, SP4, SP5: lead-ins from the SPV and SPG splice bodies (power_splice box) %s;
  checks %s.
- roll_to_pitch: the CAD has 2 pilots per part (F029 to F032): the viewer mount text now says 2 x M2x6 (B63).
- Viewer: head_board ghost not drawn; x-ray switch (printed shells see-through); part and cable labels (labels.json, the page
  hides a label that faces away or would overlap one already shown, so none hides another; LED names kept); camera screw
  labels from the record. Republish from /home/user/v1_out/3d/viewer: index.html, manifest.json, duck.glb.txt.
- Counts after: %d cables in %d runs, all drawn; %s of %s parts rows seated; both ends at the right part %s of %s cables.
""" % (NOW.strftime("%Y-%m-%d about %I:%M %p ET").replace(" 0", " "), rib["centerline_mm"], 300 - rib["centerline_mm"],
       lp.get("n_loops") or 0, loops, chk["D12"], o.get("D13_zero_mm", 0), w13.get("length_max_mm"), w13["cut_mm"], chk["D13"],
       chk["P15"], ", ".join(o.get("D10 fans", [])), chk["D10"],
       ", ".join("%s %.1f mm" % (k.split()[0], v) for k, v in o.items() if k.endswith("lead-in mm")),
       ", ".join("%s %s" % (k, chk[k]) for k in ("SP1", "SP2", "SP4", "SP5")),
       len(c3["cables"]), runs, n["parts_seated"], n["parts_rows"], n["cables_ends_ok"], len(c3["cables"]))
    cm = os.path.join(HERE, "COMPLETE3D.md")
    t = open(cm).read()
    if "## 9. Phase 2 applied" not in t:
        open(cm, "w").write(t.rstrip("\n") + "\n" + sec)
    hist = glob.glob(os.path.join(LAB, "history", "*_v1_complete3d.md"))
    path = hist[0] if hist else os.path.join(LAB, "history", NOW.strftime("%Y-%m-%d_%H%M") + "_v1_complete3d.md")
    open(path, "w").write("# %s: V1 track \"everything in 3D\" (phases 1 and 2)\n\n" % NOW.strftime("%Y-%m-%d %I:%M %p ET").replace(" 0", " ") +
                          "Agent of the V1 3D track, for the lead. CAD check only; lengths calc only. Details: "
                          "altaay_lab/twin/complete3d/COMPLETE3D.md (sections 1 to 9) and TABLES.md.\n\n"
                          "- Phase 1: inventory of every part, cable and screw against the viewer; camera seat measured on head.stl; "
                          "D12 as a flat strip needs 227.4 mm, so Ahmed chose the 300 mm cable (D34).\n" + sec.split("\n", 3)[3] +
                          "\nNeeds Ahmed's OK: the 1/16 in drill bit for the camera pilots (not in the tool lines). Nothing bought.\n")
    print("wrote", os.path.relpath(path, LAB), "and COMPLETE3D.md section 9")


if __name__ == "__main__":
    main()
