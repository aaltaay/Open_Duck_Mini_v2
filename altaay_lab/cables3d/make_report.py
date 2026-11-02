#!/usr/bin/env python3
"""Write altaay_lab/cables3d/CABLES_3D.md from cables3d.json and wiring/netlist.yaml (no geometry work here).

Usage: python3 altaay_lab/cables3d/make_report.py "<clock time line>"
The clock time is passed in (run `TZ=America/New_York date` first) so the file never carries a guessed time.
"""
import json
import math
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
DATA = os.path.join(HERE, "cables3d.json")
NET = os.path.join(LAB, "wiring", "netlist.yaml")
OUT = os.path.join(HERE, "CABLES_3D.md")


def f(x, nd=0):
    if x is None:
        return "-"
    if isinstance(x, float) and math.isinf(x):
        return "-"
    return ("%." + str(nd) + "f") % x


def proposed_edits(data, net_lines):
    """for every failing chain with known cuts, the smallest cut change on its longest wire; exact netlist lines"""
    need = {}
    for c in data["cables"]:
        for w in c["wires"]:
            for ch in w.get("chains", []):
                if ch.get("margin_mm") is None or ch["margin_mm"] >= 0:
                    continue
                refs = ch["chain"]
                # longest wire of the chain carries the extra length
                best = None
                for ref in refs:
                    cid, rest = ref.split(":", 1)
                    frm, to = rest.split(">")
                    cc = [x for x in data["cables"] if x["id"] == cid][0]
                    ww = [x for x in cc["wires"] if x["from"] == frm and x["to"] == to][0]
                    if ww.get("gauge") in ("kit cable", "FPC ribbon", "holder lead"):
                        best = ("fixed", cid, ww)
                        break
                    if best is None or ww["cut_mm"] > best[2]["cut_mm"]:
                        best = ("cut", cid, ww)
                kind, cid, ww = best
                key = (cid, ww["from"], ww["to"])
                new = int(math.ceil((ww["cut_mm"] - ch["margin_mm"]) / 10.0) * 10)
                if key not in need or new > need[key][1]:
                    need[key] = (kind, new, ww, ch)
    edits = []
    for (cid, frm, to), (kind, new, ww, ch) in sorted(need.items()):
        old_line = None
        for ln in net_lines:
            if ("cable: %s," % cid) in ln and ("from: %s," % frm) in ln and ("to: %s," % to) in ln:
                old_line = ln.rstrip("\n")
                break
        new_line = old_line.replace("cut_mm: %s," % ww["cut_mm"], "cut_mm: %d," % new, 1) if old_line else None
        edits.append(dict(cable=cid, frm=frm, to=to, kind=kind, old=ww["cut_mm"], new=new, old_line=old_line,
                          new_line=new_line, fits=ww.get("fits_mm"), chain=ch))
    return edits


def wire(data, cid, frm, to):
    c = [x for x in data["cables"] if x["id"] == cid][0]
    return [x for x in c["wires"] if x["from"] == frm and x["to"] == to][0]


def cab(data, cid):
    return [x for x in data["cables"] if x["id"] == cid][0]


def curated(data):
    out = []
    j = wire(data, "D3", "FSL1.NO", "FSL2.NO")
    out.append(("build-blocking", "Foot switch jumpers D3 and D4 (FSL1 to FSL2, FSR1 to FSR2): the two foot_top slots are "
                "50 mm apart (viewer seats); the jumper route is %.0f mm, the netlist cut is 40 mm. Cut 100 mm (exact "
                "edits below)." % j["length_max_mm"]))
    d7 = cab(data, "D7")
    out.append(("build-blocking", "Projector LED (D7): flash_light_module is mounted outside the head's left wall and its "
                "4 mm lead channel opens at the module back (x 67) outside the shell; head.stl has no hole there. The "
                "route found runs outside the shell to the nearest opening: %.0f mm, cut 160. Either cut 220 mm (edit "
                "below) and run the pair along the outside of the wall, or add a 4 mm hole through head.stl behind the "
                "module (CAD edit, about world (66, 85, 209), the module axis) and re-route (shorter)." % d7["length_max_mm"]))
    rooms = [x for c in data["cables"] for x in c.get("connector_room", []) if x.get("plug_gap_mm") is not None]
    ank = [x for x in rooms if x["end"].startswith(("SV24", "SV14"))]
    if ank:
        g_ = min(x["plug_gap_mm"] for x in ank)
        G_ = max(x["plug_gap_mm"] for x in ank)
        rng_txt = ("%.1f" % g_) if abs(G_ - g_) < 0.05 else ("%.1f to %.1f" % (g_, G_))
        out.append(("build-blocking (test fit)", "Ankle servo sockets (ID 24, ID 14, BUS 2 used) sit at the apex of foot_side: "
                    "the plug back is " + rng_txt + " mm from foot_side at the zero pose (exact mesh distance), with the plug "
                    "protrusion itself UNVERIFIED. The wire exit straight out is free, but the plug body may touch the "
                    "apex when the foot is flat. Test fit one servo with a printed foot_side before the full print "
                    "(TEST_PLAN test order); if it touches, a 2 mm relief at the foot_side apex is the CAD fix."))
    hp = [x for x in rooms if x["end"].startswith(("SV22", "SV12"))]
    if hp:
        out.append(("note (test fit)", "Hip pitch servo sockets (ID 22, ID 12) face the inner wall of left/right_roll_to_pitch "
                    "8.2 mm from the slot mouth (exact ray); after a plug of about 3 mm the kit cable must turn within "
                    "about 5 mm and run in that gap to the bracket edge. Free straight length measured %s mm." %
                    ", ".join(sorted({"%.0f" % x["free_mm"] for x in hp}))))
    for cid, other in (("S2", "S7"),):
        a, b = cab(data, cid), cab(data, other)
        out.append(("note (test fit)", "Kit cables S2 and S7 (hip yaw servo to hip roll servo, 150 mm): worst routed %.0f "
                    "and %.0f mm, so they fit taut (%.0f and %.0f mm spare) but not with the 40 mm slack. The hip yaw "
                    "sockets face up toward body_middle_top, so the lead goes up and round the servo. Contingency X1 "
                    "(200 mm made lead, BOM) if the test fit is tight. CABLE_MAP's worst case S12 passes here (worst "
                    "%.0f mm)." % (a.get("worst_mm", 0), b.get("worst_mm", 0), 150 - a.get("worst_mm", 0),
                                    150 - b.get("worst_mm", 0), cab(data, "S12").get("worst_mm", 0))))
    d12 = cab(data, "D12")
    out.append(("note (test fit)", "Camera ribbon D12 (Adafruit 3157, 150 mm): the Pi camera connector is on the Pi's back "
                "edge and the camera on the front wall, route %.0f mm, so 24 mm spare instead of 40. Keep it and fit it on "
                "the test order (TO9), or use a longer Zero camera cable." % d12.get("worst_mm", 0)))
    d9 = cab(data, "D9")
    out.append(("note", "SG90 right antenna lead D9: routed %.0f mm worst, so the 250 mm lead reaches with %.0f mm to spare; "
                "the 20 mm extension in the netlist is not needed (CABLE_MAP measured 228 mm through part centres). The "
                "SG90 lead exit point is UNVERIFIED (the CAD body has no lead): even 23 mm worse it still fits. Edit: D9 "
                "cut_mm 270 -> 250 and gauge 'SG90 lead' on its three wires." % (d9.get("worst_mm", 0),
                                                                              250 - 40 - d9.get("worst_mm", 0))))
    out.append(("build-blocking", "Battery bay leads with the seats as placed: P6/P8 (BMS P to XT30 female, the XT30 seated "
                "left of the holder as Tnkr places it, the BMS on the right) need 140 mm; P7 load (fuse holder far end to "
                "the 2815) needs 130 mm, so the 90 mm holder lead must be extended with 16 AWG (the netlist note already "
                "allows it); the fuse holder's -y end lead leaves only about 4 mm from the body wall, so it turns at once. "
                "P11 (BEC output leads joint to the power splices) needs 100 mm, or join the BEC leads nearer the splices "
                "(BEC lead length not published)."))
    out.append(("note", "BNO055 (D2): the board hangs under the trunk_top plate with a 3 mm gap above it (section at y 0), so "
                "its four wires must be soldered from the underside and leave downward; the header edge (front) is a [L] "
                "choice tied to B20."))
    out.append(("note", "Servo adapter (D1, SD1, SD2): the CAD bosses fix the 42 mm side along x, so 'USB-C toward the neck' "
                "(MOUNTING.md) can only mean the USB-C end of its long edge faces forward; the USB-C plug then leaves "
                "sideways (-y) at x -73 and the two sockets are on the +y edge. Confirm at the first fit; H3 = front "
                "socket is a [L] choice (H3 and H5 are in parallel)."))
    hr = [c for c in data["cables"] if c.get("rub_min_gap_runtime_mm") is not None and c["rub_min_gap_runtime_mm"] < 0]
    if hr:
        out.append(("note (build)", "Rub: %d cables touch a moving part even within the Runtime head ranges or at the leg "
                    "joint limits (taut routes, gap under 0 mm): %s. Most are the neck bundle against head_pitch_to_yaw "
                    "near the head yaw crossing and kit cables against the hip brackets at their limits. Dress the slack "
                    "away from those brackets, put the tie points of the gap list on both sides, and sleeve the cable "
                    "(spiral wrap or heat shrink) where it crosses a moving edge." % (
                        len(hr), ", ".join("%s %.1f mm" % (c["id"], c["rub_min_gap_runtime_mm"]) for c in hr))))
    lp = [(c["id"], x) for c in data["cables"] for x in c.get("service_loops", [])]
    bad = [(cid, x) for cid, x in lp if not x["ok"]]
    bad_rt = [(cid, x) for cid, x in lp if not x["ok_runtime"]]
    out.append(("build-blocking" if bad_rt else "note", "Service loops: %d joint crossings now have a designed free "
                "section (ties pushed back from the crossing). %d still cannot reach R >= 3 x OD over the full URDF range "
                "(%s), %d within the Runtime head ranges%s. The limit is route room between neighbouring crossings: the "
                "fix is a longer free section by the builder (more slack between the two ties, so the ties sit further "
                "from the joint) or a smaller joint range in software." % (
                    len(lp), len(bad), ", ".join(sorted({"%s %s" % (cid, "+".join(x["joints"])) for cid, x in bad}))[:600],
                    len(bad_rt), (" (" + ", ".join(sorted({"%s %s" % (cid, "+".join(x["joints"])) for cid, x in bad_rt})) + ")")
                    if bad_rt else "")))
    out.append(("note", "Speaker seat (terminals: speaker) is not credible from the CAD: the 36.1 mm speaker clears the CAD "
                "parts only 4.3 mm behind speaker_interface (B8, test order 7). D11 is routed to that seat."))
    R = data.get("retention", [])
    out.append(("build-blocking", "Retention: %d tie points by the rule; only %d meet a hole or slot in the stock CAD, %d need "
                "a stick-on cable tie mount (gap list), %d are free air where only a bundle tie is possible (a printed "
                "guide is needed to fix the cable there). The stick-on mounts are not in the BOM yet (part number not "
                "chosen, UNVERIFIED)." % (len(R), sum(1 for t in R if t["kind"] == "existing printed feature"),
                                          sum(1 for t in R if t["kind"] == "adhesive tie mount"),
                                          sum(1 for t in R if t.get("gap") and t["kind"] == "cable tie"))))
    return out


def main():
    clock = sys.argv[1] if len(sys.argv) > 1 else "(time not given)"
    data = json.load(open(DATA))
    net_lines = open(NET).read().splitlines(True)
    C = data["cables"]
    R = data.get("retention", [])
    meta = data["meta"]
    L = []
    w = L.append
    w("# CABLES_3D: every cable in 3D, bound to the links, checked over the joint ranges")
    w("")
    w("Last updated: %s by the Claude Code cable agent (agent C). Generated by altaay_lab/cables3d/make_report.py from "
      "cables3d.json (scripts: route_cables.py, seats_ties.py, check_cables.py, render_cables.py). Nothing here is built "
      "or bought. Numbers are measured on the upstream CAD at the zero pose and swept over the joint ranges: geometry "
      "checks only, not a physical test." % clock)
    w("")
    w("Pictures: cables_all.png (whole robot, two views), cables_detail.png (left leg and neck with seats and ties).")
    w("Viewer: VIEWER_NOTE.md says how to draw the tubes per link. Data: cables3d.json (%d cables, %d runs, %d ties, "
      "%d terminals seated here)." % (len(C), sum(len(c.get("runs", [])) for c in C), len(R), len(data.get("terminals", []))))
    w("")
    w("## How the routes were made [L]")
    w("- Robot posed from mini_bdx/robots/open_duck_mini_v2/robot.urdf at zero (yourdfpy, mm); printed parts from print/; "
      "head parts that exist only in print/ added in the head.stl frame; boxes for bought parts not in the CAD "
      "(audit/placements.json, viewer seats for the 5 V regulator, camera and foot switches, and the six seats chosen here).")
    w("- 1 mm occupancy grid (voxel solid when its centre is inside a watertight part or the surface crosses it), "
      "distance field, then a shortest clear path for each run (Dijkstra, clearance = bundle radius + 0.5 mm, fallbacks "
      "to 0.6 mm), string pulled. Runs follow the servo chains through the neck and legs (vias 10 mm off each servo "
      "socket), the lab corridors in the trunk and the hull of the trunk and head shells.")
    w("- Every point is bound to the URDF link of the part it rides on (dynamic programming along the kinematic chain, "
      "cost = distance to that link's parts). Where the link changes the segment is a free span across the joint "
      "(the service loop). Points are stored in link-frame mm (cables3d.json `points[].p`).")
    w("- Lengths: zero pose, and min/max over the full URDF range of every joint each free span crosses (61 samples for "
      "one joint, 21 x 21 for two). A second sweep uses the head ranges the Runtime commands from the gamepad "
      "(head pitch -0.78..0.30, yaw -0.5..0.5, roll -0.5..0.5 rad, Open_Duck_Mini_Runtime 376de65 "
      "mini_bdx_runtime/mini_bdx_runtime/xbox_controller.py lines 15 to 17) [U].")
    w("- The routes are centrelines of taut cables. They never cross a solid voxel; the grid is 1 mm, so gaps under "
      "about 1 mm are not resolved (the exact-mesh ray checks in seats_ties.py and the connector room check use the "
      "real meshes).")
    w("")
    w("## Rules and sources")
    w("| Check | Rule | Source |")
    w("|---|---|---|")
    w("| Length | cut_mm of a conductor chain (fixed end to fixed end, through floating inline splices) >= worst routed "
      "length + 20 mm service slack per fixed end (40 mm) | [L] CABLE_MAP.md length rule, its 2 x 20 mm service-slack "
      "term; its connector tolerance (2 x 22.6 mm) and 10 mm per radian terms are replaced by measured terminals and the "
      "joint sweep. Inline splices (VSW, G, YD3, YG3, JG20, JG10, JG30, J5, JG) float, so their tails are judged as part "
      "of the chain |")
    w("| Bend radius | NASA-STD-8739.4A Table 7-1, harness of AWG 10 or smaller without coax: minimum 3 x OD, optimum "
      "10 x OD (OD of the bundle). Measured on the taut route after relaxing it inside free space (circle through points "
      "3 mm apart) | [I] https://standards.nasa.gov/sites/default/files/standards/NASA/A/4/nasa-std-87394a_w_change_4_0.pdf |")
    w("| Rub | smallest surface gap to a part of another link, every nearby joint swept alone (13 samples), connector "
      "zones (8 mm) left out; flagged under %.1f mm. Free spans are reported apart (taut straight span) | [L] |" %
      meta.get("check", {}).get("rub_warn_mm", 2.0))
    w("| Connector room | free straight length along the exit of each terminal (exact ray) >= 3 x OD + OD/2 | [L] from "
      "Table 7-1 minimum radius |")
    w("| Retention | a fixed point on both sides of every joint crossing; first tie 25.4 to 50.8 mm from each connector "
      "(Table 9-2, bundles under 12.7 mm); then at most 76.2 mm apart (Table 9-1, largest spacing); ties within 8 mm on "
      "one link merged | [I] NASA-STD-8739.4A Tables 9-1, 9-2 (same URL); 7.2.29 support to limit vibration stress |")
    w("| Wire OD | 16 AWG 3.0, 20 AWG 1.8, 22 AWG 1.7, 26 AWG 1.5 mm (BNTECHGO listings), USB 3.5 mm (BOM line 20); "
      "kit cable, SG90 lead, FPC, BEC lead UNVERIFIED (drawn 1.3, 1.0, 1.0, 2.0 mm) | [I] cables3d.json meta.sources |")
    w("")
    npass = sum(1 for c in C if c["check"].startswith("pass"))
    nfail = sum(1 for c in C if c["check"] == "fail")
    nfit = sum(1 for c in C if c["check"] == "fail" and all((w_.get("fits_mm") or 0) >= 0 for w_ in c["wires"] if w_.get("length_check", "").startswith("fail")))
    w("## Summary")
    w("- %d active cables routed, 0 left as straight placeholders. Length: %d pass (%d of them with notes), %d fail the "
      "slack rule, of which %d still fit taut (the cut covers the worst routed length, not the 40 mm slack)." % (
          len(C), npass, sum(1 for c in C if c["check"] == "pass with notes"), nfail, nfit))
    w("- Retention: %d ties (%s)." % (len(R), ", ".join("%d %s" % (v, k) for k, v in Counter(t["kind"] for t in R).most_common())))
    w("")
    w("## Findings that change the build")
    w("Severity: print-blocking (fix before printing), build-blocking (fix before or at assembly, or the cable cannot be "
      "fitted as drawn), note (check at the build). Numbers from cables3d.json [L].")
    w("")
    for sev, text in curated(data):
        w("- **%s**: %s" % (sev, text))
    w("")
    w("## Per cable")
    w("Lengths in mm. L0 = zero pose; max = worst over the full URDF ranges (max RT = within the Runtime head ranges); "
      "need = worst + slack of the worst chain; margin = cut - need. Rub = smallest gap to a moving part (full range). "
      "Bend = smallest taut radius (3 x OD in brackets).")
    w("")
    w("| Cable | What | Gauge | OD | Joints | L0 | max | max RT | cut | need | margin | Rub | Bend (3xOD) | Result | Findings |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for c in C:
        wl = [x for x in c["wires"] if x.get("runs")]
        worst = min(wl, key=lambda x: x.get("margin_mm", 1e9)) if wl else None
        rt = worst.get("length_max_runtime_mm") if worst else None
        js = ", ".join(c.get("joints", [])) or "none"
        w("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s (%s) | %s | %s |" % (
            c["id"], c["desc"].replace("|", "/"), c["gauge"], f(c["d_mm"], 1), js,
            f(worst["length_zero_mm"]) if worst else "-", f(worst["length_max_mm"]) if worst else "-", f(rt),
            worst["cut_mm"] if worst else "-", f(worst.get("required_mm")) if worst else "-",
            f(worst.get("margin_mm")) if worst else "-", f(c.get("rub_min_gap_mm"), 1),
            f(c.get("bend_min_radius_mm"), 1), f(3 * c["d_mm"], 1), c["check"],
            "; ".join(c.get("findings", [])).replace("|", "/") or "-"))
    w("")
    w("## Service loops at the joints")
    w("Each joint crossing gets a free section between its two ties (retention items 'joint crossing ... end of the free "
      "loop'). Rule: bend radius under the joint motion R = free length / largest joint angle from zero (uniform bend "
      "model, conservative) >= 3 x OD (NASA-STD-8739.4A Table 7-1 minimum). The ties are pushed back from the crossing "
      "until the free length meets the rule or the route runs out (previous crossing, or 25.4 mm from a terminal).")
    w("")
    w("| Cable | Run | Joints | Angle rad (RT) | OD | Rule R | Free mm | R full | R RT | OK full | OK RT |")
    w("|---|---|---|---|---|---|---|---|---|---|---|")
    nl = nbad = nbad_rt = 0
    for c in C:
        for x in c.get("service_loops", []):
            nl += 1
            nbad += not x["ok"]
            nbad_rt += not x["ok_runtime"]
            w("| %s | %s | %s | %.2f (%.2f) | %.1f | %.1f | %.0f | %s | %s | %s | %s |" % (
                c["id"], x["run"], "+".join(x["joints"]), x["angle_rad"], x["angle_runtime_rad"], x["od_mm"], x["rule_mm"],
                x["free_mm"], f(x["radius_mm"], 1), f(x["radius_runtime_mm"], 1), "yes" if x["ok"] else "NO",
                "yes" if x["ok_runtime"] else "NO"))
    w("")
    w("%d loops: %d meet the rule over the full URDF ranges, %d do not; within the Runtime head ranges %d do not." % (
        nl, nl - nbad, nbad, nbad_rt))
    w("")
    edits = proposed_edits(data, net_lines)
    w("## Proposed netlist cut_mm changes (exact text for the lead to apply to wiring/netlist.yaml)")
    w("Each change makes the failing chain meet the slack rule; the longest wire of the chain takes the extra length. "
      "Parts whose length is fixed by the product (kit cable, FPC, fuse holder lead) get a note instead of a cut change.")
    w("")
    for e in edits:
        if e["kind"] == "fixed" or not e["old_line"]:
            w("- %s %s -> %s: fixed-length part (cut %s mm); the chain needs %s mm (fits taut with %s mm). See findings." % (
                e["cable"], e["frm"], e["to"], e["old"], f(e["chain"]["required_mm"]), f(e["fits"])))
            continue
        w("- %s %s -> %s: cut_mm %s -> %d" % (e["cable"], e["frm"], e["to"], e["old"], e["new"]))
        w("  - old: `%s`" % e["old_line"].strip())
        w("  - new: `%s`" % e["new_line"].strip())
    w("")
    w("## Terminals seated by this work (top-level `terminals` in cables3d.json, for audit/placements.json)")
    w("| id | centre (world, zero pose) | dims | link | how |")
    w("|---|---|---|---|---|")
    for t in data.get("terminals", []):
        w("| %s | %s | %s | %s | %s |" % (t["id"], t["center_mm"], t["dims_xyz_mm"], t["link"], t["how"].replace("|", "/")))
    w("")
    w("All %d cable ends (servo sockets, header pins, pads, splices) are in `cable_ends` with their source; servo "
      "sockets from the Feetech drawing and the measured slot in wj-wk00-0124bottomcase_45.stl (BUS1 at case +z, BUS2 at "
      "case -z, the two are in parallel)." % len(data.get("cable_ends", [])))
    w("")
    w("## Seats and ties per cable, end to end")
    w("Seat kinds: hole, channel, edge, none (free air over 40 mm). Ties: id, kind, part, why. A tie that holds several "
      "cables is listed under each.")
    w("")
    by_cable = defaultdict(list)
    for t in R:
        for cid in t["cables"]:
            by_cable[cid].append(t)
    for c in C:
        seats = c.get("seats", [])
        sk = Counter(s["kind"] for s in seats)
        w("- **%s** (%s): seats %s." % (c["id"], c["desc"].replace("|", "/"),
                                         ", ".join("%d %s" % (v, k) for k, v in sk.most_common()) or "none"))
        for s_ in seats:
            if s_["kind"] in ("hole", "channel"):
                w("  - %s through/along %s at %s, size %s mm, run %s point %d" % (
                    s_["kind"], s_["part"], s_["center_mm"], s_.get("size_mm"), s_.get("run"), s_["point_index"]))
        for t in by_cable.get(c["id"], []):
            w("  - tie %s: %s on %s (%s), %s" % (t["id"], t["kind"], t.get("part") or "-", t["link"], "; ".join(t["why"])))
    w("")
    gaps = [t for t in R if t.get("gap")]
    w("## Gap list (no tie anchor in the stock CAD)")
    w("%d of %d tie points have no hole, slot or bar to loop a tie through within 15 mm on the same link. Proposed fix "
      "for each: a stick-on cable tie mount on the named printed surface (adhesive, generic 12.7 x 12.7 mm base; part "
      "number not chosen, UNVERIFIED), or later a printed guide. The community parts in print/mods/v2_Jaimes_Mods "
      "(Hip Cable Holder 14 x 8 x 22 mm, Upper and Lower Cable Guides about 25 x 11 x 27 mm, measured from the 3MF "
      "files) have no screw holes and their mounting interface cannot be checked here (the assembly STEP needs a CAD "
      "kernel this machine lacks): fit on stock parts UNVERIFIED, test print before relying on them." % (len(gaps), len(R)))
    w("")
    w("| Tie | Cables | Link | Part to fix to | Note |")
    w("|---|---|---|---|---|")
    for t in gaps:
        w("| %s | %s | %s | %s | %s |" % (t["id"], ", ".join(t["cables"]), t["link"], t.get("part") or "-", t["note"]))
    w("")
    w("## Tie count by size")
    cnt = Counter(t["tie"] for t in R)
    for k, v in cnt.most_common():
        w("- %s: %d" % (k, v))
    w("- adhesive tie mounts (stick-on bases) needed: %d" % sum(1 for t in R if t["kind"] == "adhesive tie mount"))
    w("- ties through existing printed features: %d; free-air bundle ties (no surface within 15 mm): %d" % (
        sum(1 for t in R if t["kind"] == "existing printed feature"), sum(1 for t in R if t.get("gap") and t["kind"] == "cable tie")))
    w("")
    w("## Regenerate")
    w("```")
    w("S=/path/outside/the/repo   # grid cache, about 45 MB")
    w("python3 altaay_lab/cables3d/route_cables.py --scratch $S    # routes, binding, sweeps (about 4 min, 10 min first run)")
    w("python3 altaay_lab/cables3d/seats_ties.py                   # seats, tie anchors, retention")
    w("python3 altaay_lab/cables3d/check_cables.py --scratch $S    # length, rub, bend, connector room")
    w("python3 altaay_lab/cables3d/make_report.py \"$(TZ=America/New_York date '+%Y-%m-%d %-I:%M %p ET')\"")
    w("python3 altaay_lab/cables3d/render_cables.py --scratch $S --views both")
    w("```")
    open(OUT, "w").write("\n".join(L) + "\n")
    print("wrote", OUT, os.path.getsize(OUT), "bytes;", len(edits), "edits")


if __name__ == "__main__":
    main()
