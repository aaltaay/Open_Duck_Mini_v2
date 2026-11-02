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
    jc = int(math.ceil((j["length_max_mm"] + 40) / 10.0) * 10)
    out.append(("build-blocking", "Foot switch jumpers D3 and D4 (FSL1 to FSL2, FSR1 to FSR2, one wire each): the two "
                "foot_top slots are 50 mm apart (viewer seats); each jumper routes %.0f mm inside the foot with full "
                "clearance, the netlist cut is 40 mm. Cut %d mm (exact edits below). Status 2026-11-02: applied in the netlist "
                "(110 mm)." % (j["length_max_mm"], jc)))
    d7 = cab(data, "D7")
    out.append(("print-blocking (head.stl)", "Projector LED (D7): flash_light_module sits outside the head's left wall and "
                "its 4 mm lead channel opens at the module back (x 67) outside the shell; the stock head.stl has no "
                "passage, so no inside route exists. Proposed CAD edit: a 4 mm hole through the head wall (3.2 mm thick) "
                "on y at world (64.5, 84.8, 209.3), 2.5 mm behind the module. With it D7 runs inside the head to the hole, "
                "through it and into the channel: %.0f mm worst, the 160 mm cut passes. Without the hole the leads would "
                "have to run outside the shell (an earlier route went under the head floor): not acceptable. Status 2026-11-02: "
                "decided by D24 without an STL edit: the 4.0 mm hole is drilled in the printed head (print/PRINT_PLAN.md "
                "\"After printing\" step 4)." % d7.get("worst_mm", 0)))
    out.append(("note", "Clearance: every run was checked against the exact meshes (centreline samples every 1 mm, 3 mm "
                "left out at each terminal): no tube enters a part (smallest gap %.2f mm, i.e. touching). The routing "
                "grid uses the cable radius + 1.0 mm so the 1 mm voxels cannot hide a penetration." % min(
                    (c.get("clearance_min_mm") for c in data["cables"] if c.get("clearance_min_mm") is not None), default=0)))
    fr = sorted([(c.get("free_stretch_mm") or 0, c["id"]) for c in data["cables"]], reverse=True)
    out.append(("note", "Free stretches (no seat and no tie): longest %s. Ties are placed at most 76.2 mm apart on fixed pieces "
                "(a lab support spacing: NASA-STD-8739.4A Table 9-1 is the spacing of the ties that bind a harness, 19.1 mm "
                "for a harness of 6.4 mm or less, and the standard gives no number for fixing a harness to the structure); "
                "longer free stretches left are the designed loops at the joints." % (
                    ", ".join("%s %.0f mm" % (cid, v) for v, cid in fr[:6]))))
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
                "edge and the camera on the front wall, route %.0f mm, so %.0f mm spare instead of 40. Keep it and fit it on "
                "the test order (TO9), as D25 decided. The fallback named in the BOM E7 note (no buy line): the Raspberry Pi Standard-Mini camera cable, 200 mm, "
                "Adafruit 5818, 22-pin 0.5 mm to 15-pin 1 mm, $2.70, in stock (https://www.adafruit.com/product/5818, read "
                "2026-11-02 1:46 AM ET); Kiwi Electronics lists the same Raspberry Pi cable (MPN SC1892) for the Pi 5, Zero "
                "and CM4 (https://www.kiwi-electronics.com/en/raspberry-pi-camera-cable-standard-mini-200mm-11588, read "
                "1:46 AM ET). It leaves %.0f mm over the 40 mm slack; the spare ribbon folds flat inside the head." % (
                    d12.get("worst_mm", 0), 150 - d12.get("worst_mm", 0), 200 - 40 - d12.get("worst_mm", 0))))
    d9 = cab(data, "D9")
    out.append(("note", "SG90 right antenna lead D9: routed %.0f mm worst, so the 250 mm lead reaches with %.0f mm to spare; "
                "the 20 mm extension in the netlist is not needed (CABLE_MAP measured 228 mm through part centres). The "
                "SG90 lead exit point is UNVERIFIED (the CAD body has no lead): even 23 mm worse it still fits. Edit: D9 "
                "cut_mm 270 -> 250 and gauge 'SG90 lead' on its three wires. Status 2026-11-02: applied in the netlist (250 mm, "
                "no extension)." % (d9.get("worst_mm", 0), 250 - 40 - d9.get("worst_mm", 0))))
    out.append(("build-blocking", "Battery bay leads with the seats as placed: P6/P8 (BMS P to XT30 female, the XT30 seated "
                "left of the holder as Tnkr places it, the BMS on the right) need 140 mm; P7 load (fuse holder far end to "
                "the 2815) needs 130 mm, so the 90 mm holder lead must be extended with 16 AWG (the netlist note already "
                "allows it); the fuse holder's -y end lead leaves only about 4 mm from the body wall, so it turns at once. "
                "P11 (BEC output leads joint to the power splices) needs 100 mm, or join the BEC leads nearer the splices "
                "(BEC lead length not published). Status 2026-11-02: applied in the netlist (P6 and P8 150 mm, P11 100 mm; "
                "P7 holder leads extended at splices JFI and JFO; the JFI extension is 30 mm since the splice pass, so 120 "
                "and 130 mm per conductor)."))
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
    out.append(("build-blocking (test fit)" if bad else "note", "Service loops: the two ties of every joint crossing are pushed "
                "away from the crossing until the loop between them meets 3 x OD in two models (uniform bend over the largest "
                "joint angle, and the length the loop needs at the farthest pose stored as one arc over the closest "
                "tie-to-tie chord). Where two crossings are under 8 mm apart along the route with no room for a tie between them (the "
                "link head_pitch_to_yaw carries 0 to 3 mm of the neck bundle; hip_roll_assembly_2 6 mm of SP5) they make "
                "one loop over both joints. "
                "%d of %d loops meet both over the full URDF range (free length between the ties %.0f to "
                "%.0f mm). %d cannot inside the route room: %s. Within the Runtime head ranges %d still fail the length "
                "storage model, because the loop carries the cable the full URDF range needs. The build does instead: dress "
                "each loop with the length in the table below, then turn the joint through its whole range by hand at the "
                "TEST_PLAN 1.4 fit and look for a kink or a pull at the ties." % (
                    len(lp) - len(bad), len(lp), min(x["free_mm"] for _, x in lp), max(x["free_mm"] for _, x in lp), len(bad),
                    "; ".join("%s at %s: free %.0f mm, bend R %.1f mm, storage R %.1f mm, needs %.1f mm" % (
                        cid, "+".join(x["joints"]), x["free_mm"], x["radius_bend_mm"], x["radius_storage_mm"], x["rule_mm"])
                        for cid, x in bad) or "none", len(bad_rt))))
    out.append(("note", "Speaker seat (terminals: speaker) is not credible from the CAD: the 36.1 mm speaker clears the CAD "
                "parts only 4.3 mm behind speaker_interface (B8, test order 7). D11 is routed to that seat."))
    R = data.get("retention", [])
    mt = Counter((t.get("mount_fit") or {}).get("type") or "none" for t in R if t["kind"] == "adhesive tie mount")
    op = [t for t in R if t.get("open")]
    tf = [t for t in R if t.get("hold") == "bundle tie, test fit"]
    case = [t for t in R if (t.get("mount_fit") or {}).get("on_servo_case")]
    holes = [t for t in R if t["kind"] == "drilled printed feature"]
    out.append(("build-blocking" if op else "test fit", "Retention (D25): %d tie points. %d through existing printed "
                "features; %d stick-on mounts, each on a flat patch checked with exact rays with the mount height free above "
                "it: MB3A 19 x 19 x 4.8 mm (BOM 34) at %d, Panduit ABM1M-AT-C 12.7 x 12.7 mm (BOM 34b) at %d (%d of the "
                "mounts sit on an STS3215 case: pull check at the dry fit); %d through a pair of 4.0 mm tie holes drilled "
                "in a printed part after printing (D25 ii, print/PRINT_PLAN.md After printing: %s); %d tied to a neighbour "
                "cable that its own anchor holds (D25 i); %d loop ties moved further out along the route to an anchor (D25 "
                "iii). Bundle tie, test fit (no anchor fits; D25 adds no printed parts and no STL change): %d (%s): a tie "
                "round the bundle only, checked at both joint limits at the TEST_PLAN 1.4 test fit; a drilled tie-hole pair or "
                "a printed anchor only if the bundle reaches a moving part.%s Open: %d%s." % (
                    len(R), sum(1 for t in R if t["kind"] == "existing printed feature"),
                    sum(1 for t in R if t["kind"] == "adhesive tie mount" and (t.get("mount_fit") or {}).get("type")),
                    mt.get("MB3A", 0), mt.get("ABM1M", 0), len(case), len(holes),
                    ", ".join("%s on %s" % (t["id"], t["part"]) for t in holes) or "none",
                    sum(1 for t in R if t["kind"] == "cable tie to a neighbour cable"),
                    sum(1 for t in R if "tie moved" in t.get("note", "")), len(tf), ", ".join(t["id"] for t in tf) or "none",
                    "".join(" %s: route change tried%s." % (t["id"], t["plan"].split("; route change tried", 1)[1]) for t in tf
                            if "; route change tried" in (t.get("plan") or "")), len(op),
                    (", each with a named plan: " + "; ".join("%s (%s on %s): %s" % (
                        t["id"], ", ".join(t["cables"]), t["link"], t.get("plan", "NO PLAN")) for t in op)) if op else "")))
    sp = {e["id"]: e for e in data.get("cable_ends", [])}
    out.append(("note (splices)", "Splice tails: JG20, JG10 and JG30 float in the bundle (no part holds them), so their "
                "tails are judged with the leads they join, fixed end to fixed end. A tail must hold 3.5 mm in the terminal "
                "(Molex 5263 catalog drawing B-101: crimp section 3.50 of the 7.00 mm terminal), the lap (3 to 6 wire "
                "diameters, NASA-STD-8739.4A 19.4.1 c) and the 15 mm adhesive sleeve, cut from a 3.5 in Wirefy kit piece "
                "(BOM 26 listing, read 2026-11-02 1:31 AM ET), that reaches 2 x OD = 3.4 mm onto the insulation (19.2.6): "
                "about 15 mm at least. The tails are now 30 mm, so the stiff sleeve sits past the bend at the plug exit "
                "(7.2.36: no splice in a bend); the 3D model puts each splice centre 23.5 mm along the route from the plug "
                "(%s). YG3 sits 15 mm past YD3 on the adapter H3 lead (stem G 45 mm, stem D 30 mm), so the two sleeves do "
                "not overlap (7.2.35, splices staggered); the 3D model draws both at Y.SD1. The P7 JFI extension (16 AWG) is "
                "30 mm, room for the XT30 cup sleeve and the JFI sleeve (2 x 3.0 mm onto the insulation)." % ", ".join(
                    "%s at %s" % (k, sp[k]["p_world0"]) for k in ("JG20", "JG10", "JG30") if k in sp)))
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
    w("Last updated: %s. Generated by altaay_lab/cables3d/make_report.py from cables3d.json (scripts: route_cables.py, "
      "seats_ties.py, check_cables.py, render_cables.py; routes by agent C, splice tails, loop ties, mount fit and this "
      "report by agent CAB on 2026-11-02). Nothing here is built or bought. Numbers are measured on the upstream CAD at the "
      "zero pose and swept over the joint ranges: geometry checks only, not a physical test." % clock)
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
      "joint sweep. Inline splices (VSW, G, YD3, YG3, JG20, JG10, JG30, J5, JG; JFI and JFO are summed into P7) are solder "
      "splices that no part holds: they float, so their tails are judged as part of the chain. SPV and SPG are seated on the "
      "belly (MOUNTING.md) and JB is where the BEC leads end: fixed ends |")
    w("| Splice tail | at least 15 mm for 22 AWG: 3.5 mm in the terminal, 3 to 6 wire diameters of lap, a 15 mm adhesive "
      "sleeve reaching 2 x OD onto the insulation; no splice in a bend; splices staggered | [I] Molex 5263 catalog page "
      "MX01 B-101 (terminal 7.00 mm, crimp section 3.50 mm; https://www.rcscomponents.kiev.ua/datasheets/mx5263-datasheet.pdf, "
      "read 2026-11-02 1:29 AM ET); NASA-STD-8739.4A Change 4 19.4.1 c, 19.2.6, 7.2.35, 7.2.36 (URL below, read 1:27 AM ET); "
      "Wirefy 3:1 kit, 7 sizes 3/32 to 3/4 in, precut 3.5 in (https://www.amazon.com/dp/B084GDLSCK, read 1:31 AM ET) |")
    w("| Bend radius | NASA-STD-8739.4A Change 4 (2016-06-30) 7.2.19 and Table 7-1, overall harness of AWG 10 or smaller "
      "without coax: minimum 3 x OD, optimum 10 x OD (OD of the bundle), for bending in the installed harness; the standard "
      "has no separate value for repeated flexing (7.2.11 asks for protection from flexing). The BNTECHGO 22 and 26 AWG "
      "listings give no bend radius (read 2026-11-02 1:45 AM ET). Measured on the taut route after relaxing it inside free "
      "space (circle through points 3 mm apart) | [I] https://standards.nasa.gov/sites/default/files/standards/NASA/A/4/"
      "nasa-std-87394a_w_change_4_0.pdf (read 2026-11-02 1:27 AM ET) |")
    w("| Service loop | the loop between the two ties of a crossing meets 3 x OD in both models: bend R = free length / "
      "largest joint angle from zero; length storage R = the cable the loop needs at the farthest pose (fixed pieces plus "
      "the span chord) bowed as one circular arc over the closest tie-to-tie chord (61 samples per joint). The ties are "
      "pushed out from the crossing (at most 60 mm per side, up to the previous tie and the midpoint to the next crossing) "
      "until both hold | [L] on the Table 7-1 minimum |")
    w("| Rub | smallest surface gap to a part of another link, every nearby joint swept alone (13 samples), connector "
      "zones (8 mm) left out; flagged under %.1f mm. Free spans are reported apart (taut straight span) | [L] |" %
      meta.get("check", {}).get("rub_warn_mm", 2.0))
    w("| Connector room | free straight length along the exit of each terminal (exact ray) >= 3 x OD + OD/2 | [L] from "
      "Table 7-1 minimum radius |")
    w("| Retention | a fixed point on both sides of every joint crossing; first tie 25.4 to 50.8 mm from each connector "
      "(Table 9-2, harness under 12.7 mm); then at most 76.2 mm apart; ties within 8 mm on one link merged | [I] "
      "NASA-STD-8739.4A Table 9-2 and 7.2.29 (support to limit vibration stress, no number). [L] the 76.2 mm support spacing: "
      "Table 9-1 is the spacing of the ties that bind a harness, 19.1 mm for a harness of 6.4 mm or less, not a support "
      "spacing |")
    w("| Stick-on mount | a flat patch under the whole base (within 0.4 mm of the plane, normals within 15 deg) with the "
      "mount height free above it, centre at most 20 mm from the cable line: MB3A 19.0 x 19.0 x 4.8 mm (BOM 34), else the "
      "Panduit ABM1M-AT-C 12.7 x 12.7 mm (BOM 34b), checked as 13.0 x 13.0 x 4.1 mm (the HellermannTyton MB2APT size, which "
      "covers the ABM1M's 0.50 x 0.50 in base; its height is not on a US page read: search index 4 mm) | [I] HellermannTyton "
      "151-01629 spec sheet (https://ftcelectronics.com/datasheets-3c/151-01629.pdf, read 2026-11-02 1:52 AM ET); Hisco "
      "ABM1M-AT-C page (0.50 x 0.50 in, read 2:43 AM ET); HellermannTyton Product Catalogue 2016/2017 p. 1.7, MB2APT "
      "151-00996 (https://docs.rs-online.com/fd67/0900766b8139134b.pdf, read 1:53 AM ET); [L] tolerances |")
    w("| Where no mount fits (D25) | in order: (i) a tie to a neighbour cable within 4 mm that its own anchor holds within 20 "
      "mm; (ii) two 4.0 mm tie holes drilled through a printed wall of the same link after printing, checked with exact rays: "
      "at least 1.6 mm of plastic round each hole and between them, wall 1.6 to 12 mm, every screw, insert and empty hole at "
      "least 1.6 mm off, 1.5 mm free behind the wall, the strap at least 1 mm from moving parts over the joint sweep; (iii) "
      "the loop tie moved further from the joint along the route (the loop still meets 3 x OD) to a feature, mount or hole "
      "pair; (iv) at a loop end, a stick-on mount on the STS3215 case of the same link, 8 mm off the plug axis and 1 mm from "
      "moving parts; else open with a named plan | [I] 4.0 mm: the BOM T14 bit (D24), which passes the 2.54 mm line 32 tie up "
      "to 3.1 mm thick; 1.6 mm: the lab's insert-wall minimum (CNC Kitchen, PRINT_CHECK.md flag 1); [L] the other gaps |")
    w("| Wire OD | 16 AWG 3.0, 20 AWG 1.8, 22 AWG 1.7, 26 AWG 1.5 mm (BNTECHGO listings), USB 3.5 mm (BOM line 20); "
      "kit cable, SG90 lead, FPC, BEC lead UNVERIFIED (drawn 1.3, 1.0, 1.0, 2.0 mm) | [I] cables3d.json meta.sources |")
    w("")
    npass = sum(1 for c in C if c["check"].startswith("pass"))
    nfit = sum(1 for c in C if c["check"] == "test fit")
    nfail = sum(1 for c in C if c["check"] == "fail")
    w("## Summary")
    w("- %d active cables routed, 0 left as straight placeholders. Length: %d pass (%d of them with notes), %d test fit "
      "(they reach, but with less than the 40 mm slack: the cut covers the worst routed length; the TEST_PLAN.md 1.4 test "
      "fit at both joint limits decides), %d fail (cannot reach)." % (
          len(C), npass, sum(1 for c in C if c["check"] == "pass with notes"), nfit, nfail))
    mt = Counter((t.get("mount_fit") or {}).get("type") or "none" for t in R if t["kind"] == "adhesive tie mount")
    w("- Retention: %d tie points (%s); stick-on mounts: MB3A %d (BOM 34), ABM1M-AT-C %d (BOM 34b), %d of them on a servo "
      "case; drilled tie-hole pairs %d; bundle tie, test fit %d; open %d." % (
        len(R), ", ".join("%d %s" % (v, k) for k, v in Counter(t["kind"] for t in R).most_common()), mt.get("MB3A", 0),
        mt.get("ABM1M", 0), sum(1 for t in R if (t.get("mount_fit") or {}).get("on_servo_case")),
        sum(1 for t in R if t["kind"] == "drilled printed feature"),
        sum(1 for t in R if t.get("hold") == "bundle tie, test fit"), sum(1 for t in R if t.get("open"))))
    lp_all = [x for c in C for x in c.get("service_loops", [])]
    two = Counter("+".join(x["joints"]) for x in lp_all if len(x.get("spans") or []) > 1)
    w("- Service loops: %d of %d meet 3 x OD in both models over the full URDF range (%d of them span two crossings with "
      "no tie between: %s)." % (
        sum(1 for x in lp_all if x["ok"]), len(lp_all), sum(two.values()),
        ", ".join("%d at %s" % (v, k) for k, v in sorted(two.items())) or "none"))
    w("- Twist (D25): the made multi-wire cables SP3, SP4, SP5, P13, D2, D3, D4, D6, D10 and SD1 branch b are twisted (lay "
      "and take-up in wiring/netlist.yaml 'twist'); the chain lengths carry the take-up. Kit cables stay as shipped.")
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
    w("Clear = smallest exact gap between the tube surface and any part (negative = enters it; within 0.1 mm = touching). "
      "Free = longest stretch with no seat (hole, channel, edge) and no tie.")
    w("")
    w("| Cable | What | Gauge | OD | Joints | L0 | max | max RT | cut | need | margin | Rub | Clear | Free | Bend (3xOD) | Result | Findings |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for c in C:
        wl = [x for x in c["wires"] if x.get("runs")]
        worst = min(wl, key=lambda x: x.get("margin_mm", 1e9)) if wl else None
        rt = worst.get("length_max_runtime_mm") if worst else None
        js = ", ".join(c.get("joints", [])) or "none"
        w("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s (%s) | %s | %s |" % (
            c["id"], c["desc"].replace("|", "/"), c["gauge"], f(c["d_mm"], 1), js,
            f(worst["length_zero_mm"]) if worst else "-", f(worst["length_max_mm"]) if worst else "-", f(rt),
            worst["cut_mm"] if worst else "-", f(worst.get("required_mm")) if worst else "-",
            f(worst.get("margin_mm")) if worst else "-", f(c.get("rub_min_gap_mm"), 1),
            f(c.get("clearance_min_mm"), 1), f(c.get("free_stretch_mm")),
            f(c.get("bend_min_radius_mm"), 1), f(3 * c["d_mm"], 1), c["check"],
            "; ".join(c.get("findings", [])).replace("|", "/") or "-"))
    w("")
    w("## Service loops at the joints")
    w("Each joint crossing gets a free loop between its two ties (retention items 'joint crossing ... end of the free loop', "
      "or the plug when the loop runs to a connector). Rule (both models, NASA-STD-8739.4A Table 7-1 minimum 3 x OD): "
      "bend R = free length / largest joint angle from zero; length storage R = the loop length to leave (the cable the loop "
      "needs at the farthest pose) bowed as one arc over the closest tie-to-tie chord. Leave = cable to leave between the "
      "two ties; extra = how much of it is slack at the zero pose (dress it as a loop).")
    w("")
    w("| Cable | Run | Joints | Angle rad (RT) | OD | Rule R | Free mm | Leave mm | Extra mm | Closest chord mm | Bend R | Storage R | Storage R RT | OK full | OK RT |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    nl = nbad = nbad_rt = 0
    for c in C:
        for x in c.get("service_loops", []):
            nl += 1
            nbad += not x["ok"]
            nbad_rt += not x["ok_runtime"]
            w("| %s | %s | %s | %.2f (%.2f) | %.1f | %.1f | %.0f | %s | %s | %s | %s | %s | %s | %s | %s |" % (
                c["id"], x["run"], "+".join(x["joints"]), x["angle_rad"], x["angle_runtime_rad"], x["od_mm"], x["rule_mm"],
                x["free_mm"], f(x.get("loop_length_mm")), f(x.get("dress_extra_mm")), f(x.get("chord_min_mm"), 1),
                f(x.get("radius_bend_mm"), 1), f(x.get("radius_storage_mm"), 1), f(x.get("radius_storage_runtime_mm"), 1),
                "yes" if x["ok"] else "NO", "yes" if x["ok_runtime"] else "NO"))
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
    d23 = [c for c in C if "provisional record from cables3d (D23)" in (c.get("note") or "")]
    if d23:
        w("## New cables SP4 and SP5 (D23): exact netlist lines")
        w("Routed along the leg chain cables (vias at the hip roll, hip pitch and knee servo sockets), ending at the free "
          "BUS 1 port of the ankle servo. cut_mm = worst routed length + 40 mm slack, rounded up to 10 mm.")
        w("")
        w("```yaml")
        w("# cables:")
        for c in d23:
            js = c.get("joints") or []
            w("  - {id: %s, status: active, desc: \"%s\", regions: [belly, trunk_bottom, %s], joints: [%s], polyline_mm: %.1f, "
              "rule_mm: null, source: \"[L] D23 (sim/POWER_FIX.md), route altaay_lab/cables3d\", note: \"service loop at every "
              "leg joint; ties in cables3d.json retention\"}" % (c["id"], c["desc"].replace(" (D23)", ""),
                                                               "left_leg" if c["id"] == "SP4" else "right_leg",
                                                               ", ".join(js), c["length_zero_mm"]))
        w("# wires:")
        for c in d23:
            for x in c["wires"]:
                cut = int(math.ceil((x["length_max_mm"] + 40) / 10.0) * 10)
                w("  - {cable: %s, from: %s, to: %s, net: %s, gauge: 22 AWG, color: %s, cut_mm: %d, i_mean_a: null, "
                  "i_peak_a: null, ends: [splice, Molex 50-37-5033 housing (DATA position empty) + 08-70-1040 crimp], "
                  "source: \"[L] D23; cut = route worst %.0f + 40 slack (cables3d)\"}" % (
                      c["id"], x["from"], x["to"], x["net"], x["color"], cut, x["length_max_mm"]))
        w("```")
        tie23 = [t for t in R if set(t["cables"]) & {"SP4", "SP5"}]
        own = [t for t in tie23 if set(t["cables"]) <= {"SP4", "SP5"}]
        w("")
        w("Ties holding SP4 or SP5: %d (%d shared with the chain cables, %d only for SP4/SP5: %s). Kinds: %s." % (
            len(tie23), len(tie23) - len(own), len(own), ", ".join(t["id"] for t in own) or "none",
            ", ".join("%d %s" % (v, k) for k, v in Counter(t["kind"] for t in tie23).most_common())))
        for c in d23:
            lp = c.get("service_loops", [])
            w("- %s: worst %.0f mm (Runtime ranges %s), %d service loops, %d meet R >= 3 x OD; check %s%s." % (
                c["id"], c.get("worst_mm") or c["length_max_mm"], f(min(x.get("length_max_runtime_mm") or 0 for x in c["wires"] if x.get("runs"))),
                len(lp), sum(1 for x in lp if x["ok"]), c["check"], ("; " + "; ".join(c.get("findings", []))) if c.get("findings") else ""))
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
    w("%d of %d tie points have no hole, slot or bar to loop a tie through within 15 mm on the same link. Each is held by a "
      "stick-on tie mount where a flat patch fits (MB3A, BOM 34; or ABM1M-AT-C 12.7 x 12.7 mm, BOM 34b), by a tie to a "
      "neighbour cable that its own anchor holds, by a pair of tie holes drilled after printing (print/PRINT_PLAN.md After "
      "printing), or by a tie round the bundle only, checked at the TEST_PLAN 1.4 test fit (HARDWARE_AUDIT B35, D25). The "
      "community parts in print/mods/v2_Jaimes_Mods (Hip Cable Holder 14 x 8 x "
      "22 mm, Upper and Lower Cable Guides about 25 x 11 x 27 mm, measured from the 3MF files) have no screw holes and their "
      "mounting interface cannot be checked here: fit on stock parts UNVERIFIED, test print before relying on them." % (
          len(gaps), len(R)))
    w("")
    w("| Tie | Cables | Link | Kind | Mount fit | Part to fix to | Note |")
    w("|---|---|---|---|---|---|---|")
    for t in gaps:
        mf = t.get("mount_fit") or {}
        w("| %s | %s | %s | %s | %s | %s | %s |" % (
            t["id"], ", ".join(t["cables"]), t["link"], t["kind"] + (" (OPEN)" if t.get("open") else "") +
            (" (bundle tie, test fit)" if t.get("hold") == "bundle tie, test fit" else ""),
            ("%s%s, %.0f mm from the cable" % (mf["type"], " on the servo case" if mf.get("on_servo_case") else "",
                                               mf["from_cable_mm"])) if mf.get("type") else
            ("holes %s mm, %s mm apart" % (t["tie_holes"]["hole_d_mm"], t["tie_holes"]["spacing_mm"]) if t.get("tie_holes") else
             ("none" if t["kind"] == "adhesive tie mount" else "-")), t.get("part") or "-",
            t["note"] + ((" PLAN: " + t["plan"]) if t.get("plan") else "")))
    w("")
    w("## Tie count by size")
    cnt = Counter(t["tie"] for t in R)
    for k, v in cnt.most_common():
        w("- %s: %d (one per tie point)" % (k, v))
    w("- stick-on mounts: MB3A %d (BOM 34), ABM1M-AT-C %d (BOM 34b); mount spots with no fit (open) %d" % (
        mt.get("MB3A", 0), mt.get("ABM1M", 0), mt.get("none", 0)))
    w("- ties through existing printed features: %d; through drilled tie-hole pairs: %d; to an anchored neighbour cable: %d; "
      "round the bundle only (bundle tie, test fit): %d; open in all: %d" % (
          sum(1 for t in R if t["kind"] == "existing printed feature"),
          sum(1 for t in R if t["kind"] == "drilled printed feature"),
          sum(1 for t in R if t["kind"] == "cable tie to a neighbour cable"),
          sum(1 for t in R if t.get("hold") == "bundle tie, test fit"), sum(1 for t in R if t.get("open"))))
    w("")
    w("## Regenerate")
    w("```")
    w("S=/path/outside/the/repo   # grid cache, about 45 MB")
    w("python3 altaay_lab/cables3d/route_cables.py --scratch $S    # routes, binding, sweeps (about 4 min, 10 min first run);")
    w("#   --only SP1,SP2,SP3,SD1,SD2 writes $S/cables3d_partial.json (splice positions from the netlist cuts) to merge by hand")
    w("python3 altaay_lab/cables3d/seats_ties.py                   # seats, tie anchors, retention")
    w("python3 altaay_lab/cables3d/check_cables.py --scratch $S    # length, rub, bend, connector room")
    w("python3 altaay_lab/cables3d/make_report.py \"$(TZ=America/New_York date '+%Y-%m-%d %-I:%M %p ET')\"")
    w("python3 altaay_lab/cables3d/render_cables.py --scratch $S --views both")
    w("```")
    open(OUT, "w").write("\n".join(L) + "\n")
    print("wrote", OUT, os.path.getsize(OUT), "bytes;", len(edits), "edits")


if __name__ == "__main__":
    main()
