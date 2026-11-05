"""Cable work for a fast build: count every cable operation, time it with cited per operation times, before and
after the proposed changes, and list the 5 slowest cable steps with their fix (calc only).

Read only: HARNESS_BUILD.md (124 wire rows, splices), cables3d/cables3d.json (75 tie points), CABLE_MAP.md (currents),
BOM_FULL.md C51 (34 sleeves), DECISIONS.md D25. Writes data/cable_ops.csv, data/cable_steps.csv,
data/cable_changes.json (phase 2 input for the 3D job and the joint motion job) and stl/K4_tie_bridge.stl.
The cable geometry belongs to the 3D job (cables3d/, viewer/): nothing here moves a route.
"""
import csv, json, os, re, collections
import trimesh
from shapely.geometry import box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, "..", ".."))
DATA = os.path.join(HERE, "data")

T = {  # seconds: (low, mid, high), source
    "solder_end": ((120, 120, 120), "[I] aPriori cost model guide 2019 R2, Process Defaults and Thresholds (search text: "
                   "120 s to solder a single wire into a connector) https://www.apriori.com/Collateral/Documents/English-US/online_help/2019_R2/COST_MODEL_GUIDE/AP_CMG0982Process_Defaults_and_Thresholds.html"),
    "crimp_end": ((90, 90, 90), "calc: 0.75 x the 120 s solder default; [I] Smiths Interconnect HG tech note, termination time study "
                  "(search text: crimp and poke about 25 % faster than soldering into solder cups; $2.73 against $3.73 per connector) "
                  "https://www.smithsinterconnect.com/getattachment/8d0803ae-a168-4e08-8f7c-f8a49053fe1f/HG-Tech-Note-Termination-Time-Study.pdf"),
    "sleeve": ((5.1, 5.1, 5.1), "[I] aPriori (search text: about 8.6 s per inch to fit and shrink tubing) x the 15 mm splice piece of HARNESS_BUILD.md"),
    "tie": ((5, 5, 5), "[I] aPriori (search text: 5 s per cable tie in branch layout)"),
    "mount": ((2, 3, 4), "DFA press-fit class, [I] https://dfma.com/resources/assembly-cost-estimating.asp (search text: 2 to 4 s); lab mapping"),
    "plug": ((2, 3, 4), "DFA snap-fit class, same source (2 to 4 s); lab mapping"),
    "lever": ((2, 3, 4), "DFA snap-fit class per wire (lever splice), same source; lab mapping"),
}
DWELL_H = (8, "[I] Panduit adhesive mount selection guide (search text: acrylic adhesive foam tape dwell 8 h, rubber 2 h) "
              "https://manualmachine.com/panduit/acc19am/26595738-selection-guide")
BLOCKERS = {
    "routing": "time to lay a cable through its channels, holes and edges in the robot: no published time found (check: time the left leg routing at the TEST_PLAN 1.4 test fit)",
    "labels": "time per cable label (2 per cable): not published (check: time 10 labels at the bench)",
    "drill": "time to drill a 4.0 mm tie-hole pair (D25 ii, 3 pairs): not published (check: time the first pair)",
    "test": "continuity test per made cable (TEST_PLAN 2): no reliable published time (check: time the first 5 cables)",
    "in_robot": "how much slower a joint is made inside the robot than on the bench: not published (check: time one splice at the bench and one in place)",
}
KK = dict(part="Molex KK 254 crimp terminal 08-50-0114 (22 to 30 AWG) with KK 254 crimp housings",
          rating="3 A ([I] https://www.datasheets.com/molex/08-50-0114, search text) to 4 A ([I] https://octopart.com/part/molex/08-50-0114, search text); 3 A used",
          price="BLOCKER: not read in this session (link above)", ok="needs Ahmed's OK")
WAGO = dict(part="WAGO 221-415 (5 conductor) and 221-413 (3 conductor) lever splices, 24 to 12 AWG, 20 A",
            link="[I] https://core-electronics.com.au/wago-snap-action-solderless-connection-5-conductor-221-415.html (search text: "
                 "24-12 AWG, 20 A, 600 V; about AUD 1.95 each; other listings EUR 0.71 and USD 0.94)",
            size="BLOCKER: outline not read (the 3D job checks the space in the battery bay)", ok="needs Ahmed's OK")


def classify(e):
    e = e.lower()
    if "kit cable plug" in e or e.startswith("servo socket") or "plug in" in e:
        return "plug"
    if "crimp" in e:
        return "crimp"
    if "join at splice" in e:
        return "splice_end"
    if "pi header" in e:
        return "pi_end"
    if "solder" in e or "tin" in e:
        return "solder_end"
    return "other"


def main():
    # "before" is the harness as it stood before phase 2 (commit 52d2637); the file in the tree now carries X1 and X4
    import subprocess
    r = subprocess.run(["git", "show", "52d2637:altaay_lab/HARNESS_BUILD.md"], cwd=LAB, capture_output=True, text=True)
    L = (r.stdout if r.returncode == 0 else open(os.path.join(LAB, "HARNESS_BUILD.md")).read()).split("\n")
    section, cable, ends = None, None, []
    for l in L:
        if l.startswith("## "):
            section = l[3:].strip()
        elif l.startswith("### "):
            cable = l[4:].split(":")[0].strip()
        elif re.match(r"^\| \d+ \|", l) and section and cable:
            c = [x.strip() for x in l.strip().strip("|").split("|")]
            for side, txt, where in ((0, c[6], c[1]), (1, c[7], c[2])):
                ends.append(dict(section=section, cable=cable, wire=c[0], gauge=c[3], where=where, op=classify(txt), text=txt[:120]))
    C3 = json.load(open(os.path.join(LAB, "cables3d", "cables3d.json")))
    ret = C3["retention"]
    kinds = collections.Counter(r["kind"] for r in ret)
    n_mount = sum(v for k, v in kinds.items() if "adhesive" in k or "mount" in k)
    splices = [l for l in L if re.match(r"^\| (G|J5|JBN|JBP|JFI|JFO|JG|JG10|JG20|JG30|SPG|SPV|VSW|YD3|YG3) \|", l)]
    housings = 7      # CABLE_MAP.md connector parts: Mini-SPOX 50-37-5033, 7 used
    sleeves = 34      # BOM_FULL.md C51
    op = collections.Counter(e["op"] for e in ends)
    pi_cables = sorted({e["cable"] for e in ends if e["op"] == "pi_end"})
    before = dict(solder_ends=op["solder_end"] + op["splice_end"] + op["pi_end"], of_which_pi_header=op["pi_end"],
                  of_which_at_splices=op["splice_end"], crimps=op["crimp"], housings=housings, sleeves=sleeves,
                  plugs=op["plug"] + housings + 1, ties=len(ret), mounts=n_mount, splices=len(splices),
                  tie_point_kinds=dict(kinds), drilled_pairs=3, cables=len({e["cable"] for e in ends}), wire_rows=len(ends) // 2)

    def seconds(c, lv):
        return (c["solder_ends"] * T["solder_end"][0][lv] + c["crimps"] * T["crimp_end"][0][lv] + c["sleeves"] * T["sleeve"][0][lv]
                + c["plugs"] * T["plug"][0][lv] + c["ties"] * T["tie"][0][lv] + c["mounts"] * T["mount"][0][lv]
                + c.get("levers", 0) * T["lever"][0][lv])
    # ---- the changes ---------------------------------------------------------------------------------
    changes = []
    after = dict(before)
    # X1 Pi header: crimped KK 254 housings on the pins instead of 27 solder ends (the Pi then unplugs)
    n_pi = before["of_which_pi_header"]
    after["solder_ends"] -= n_pi
    after["crimps"] += n_pi
    after["plugs"] += len(pi_cables)
    after["solder_ends"] += 2; after["sleeves"] += 2   # R4, R5 (D17) move from the pins into the D3, D4 leads
    changes.append(dict(id="X1", what="Pi header: crimp KK 254 terminals and push them into 1-row housings on the pre-soldered header, one housing per cable (%s); R4 and R5 (D17) go inline in D3 and D4 under heat shrink" % ", ".join(pi_cables),
                        why="the 27 Pi header joints are the most cramped solder work in the build (head floor); with plugs the head and the Pi come off without the iron",
                        current="P12 peak 2.4 A (pin 2), P17 peak 1.9 A (pin 4) [L] CABLE_MAP.md, under the 3 A terminal rating used here",
                        parts=KK, delta_s=round(n_pi * (T["crimp_end"][0][1] - T["solder_end"][0][1]) + len(pi_cables) * 3 + 2 * 125.1, 0),
                        checks=["the housings clear the head floor parts and the Pi camera cable (3D job)", "pull test each crimp (TEST_PLAN 1.3)"]))
    # X2 adhesive mounts -> printed tie bridges on the parts (the tie stays, the mount and its 8 h dwell go)
    after["mounts"] = 0
    changes.append(dict(id="X2", what="replace the %d stick-on mounts (MB3A, ABM1M-AT-C) by printed tie bridges on the same spots (stl/K4_tie_bridge.stl: 2 posts and a 1.6 mm bridge, slot 3.0 x 1.6 for the 2.5 mm tie)" % n_mount,
                        why="removes mount placement and the %d h adhesive dwell before ties can be loaded, and stops mounts peeling off 2-wall PLA" % DWELL_H[0],
                        parts="printed (no buy); STL change on the parts that carry a mount spot: the 3D job places them from cables3d.json retention",
                        delta_s=-n_mount * T["mount"][0][1], calendar_h=-DWELL_H[0],
                        checks=["coupon K4 (print and tie, pull 20 N by hand)", "bridge 1 mm from moving parts over the joint sweep (joint motion job)", "D25 loops still 3 x OD"]))
    # X3 service splits: head and legs come off by unplugging
    n_d34 = sum(1 for e in ends if e["cable"] in ("D3", "D4")) // 2      # wire rows of D3 and D4 (HARNESS_BUILD.md)
    after_noX3 = dict(after)
    after["solder_ends"] += 4; after["sleeves"] += 4   # X3a P13: XT30U solder cups, 2 conductors x 2 halves
    after["plugs"] += 1
    after_X3b = dict(after)                   # X3b D3, D4 hip splits: every conductor, both sides (optional)
    after_X3b["crimps"] += 2 * n_d34
    after_X3b["plugs"] += 2
    changes.append(dict(id="X3", what="service splits: X3a (recommended) an inline plug in P13 at the neck base (2 conductors, 20 AWG); X3b (optional) inline plugs in D3 and D4 at each hip; S2 (kit cable) and SP4, SP5 (ankle BUS 1 housings) already unplug",
                        why="with X1 the head comes off by unplugging the Pi housings and P13; a leg by unplugging S2, SP4 or SP5 at the ankle and D3 or D4 at the hip, cutting only its ties",
                        current="P13 peak 1.91 A (2.21 A at 6.4 V) [L] CABLE_MAP.md",
                        parts="P13 is 20 AWG, outside the 22 to 30 AWG of KK 254 and Mini-SPOX: an XT30U pair (BOM 12) is proposed, rating BLOCKER (not read); D3, D4: KK 254 (X1 parts)",
                        conductors_D3_D4=n_d34, delta_s_X3a=round(4 * (T["solder_end"][0][1] + T["sleeve"][0][1]) + 3, 0),
                        delta_s_X3b=round(2 * n_d34 * T["crimp_end"][0][1] + 2 * 3, 0), delta_s=round(4 * (T["solder_end"][0][1] + T["sleeve"][0][1]) + 3, 0),
                        checks=["each split on a straight run, 20 mm or more from a joint loop end (NASA-STD-8739.4A 7.2.36, as HARNESS_BUILD.md splices)", "the joint motion job re-checks the D25 loops with the housing in place", "D3, D4 conductor count from wiring/netlist.yaml"]))
    # X4 lever splices for the battery bay stars G and VSW (power only, 16 to 20 AWG)
    n_lever = 4 + 3
    for a_ in (after, after_noX3, after_X3b):     # X4 (after_X3b is copied from after, so X3a is in it too)
        a_["solder_ends"] -= n_lever; a_["levers"] = n_lever; a_["sleeves"] -= 2
    after_noX3["mounts"] = 0
    changes.append(dict(id="X4", what="splices G (4 wires) and VSW (3 wires) in the battery bay as WAGO lever splices instead of solder in heat shrink",
                        why="7 solder ends in the tightest spot go; the bay can be opened and changed without the iron",
                        parts=WAGO, delta_s=round(n_lever * (T["lever"][0][1] - T["solder_end"][0][1]) - 2 * T["sleeve"][0][1], 0),
                        checks=["space in the battery bay (3D job)", "vibration: tug test after the TEST_PLAN 8 walk", "keep SPV, SPG (6 wires, 22 AWG servo leads) soldered: no 6 way lever splice"]))
    # X5 to X7: no time credit in the cited data, kept for fewer mistakes and for the D25 checks
    changes.append(dict(id="X5", what="bench pieces with a length drawing: the belly power star (P11, SPV, SPG, SP1 to SP5 with JB+, JB-) and the battery bay piece (P1 to P10, P14, P16, XT30U, fuse holder) built and tested before they go in, on a printed length board (pegs at the cut lengths of netlist.yaml)",
                        why="HARNESS_BUILD.md already builds on the bench; the board makes every cut length match D25 and the cables3d reach check", delta_s=0, note=BLOCKERS["in_robot"]))
    changes.append(dict(id="X6", what="label and colour: a printed heat shrink label with the cable ID at both ends (HARNESS_BUILD.md asks for it), and one colour per bus: red and black power, yellow data, blue foot switches, green head signals",
                        why="no plug in the wrong socket; no cited time credit", delta_s=0, note=BLOCKERS["labels"]))
    changes.append(dict(id="X7", what="build order: plug each cable while both ends are open: legs on the bench first (S kit cables, SP4 and SP5 housings), then the trunk with the belly star, then the neck, the head last with X1 housings; the shells and the lid close last",
                        why="no plug blind behind a part; no cited time credit", delta_s=0, note=BLOCKERS["routing"]))
    s_b = [seconds(before, i) for i in range(3)]
    s_a = [seconds(after, i) for i in range(3)]
    s_n = [seconds(after_noX3, i) for i in range(3)]
    s_x = [seconds(after_X3b, i) for i in range(3)]
    # ---- the slowest cable steps (mid times) ------------------------------------------------------------
    steps = collections.Counter()
    for e in ends:
        k = {"solder_end": "solder", "splice_end": "splice", "pi_end": "Pi header", "crimp": "crimp", "plug": "plug"}.get(e["op"])
        if not k:
            continue
        tsec = {"solder": 120, "splice": 120, "Pi header": 120, "crimp": 90, "plug": 3}[k]
        name = "Pi header joints (head floor)" if k == "Pi header" else ("splices, %s" % e["section"] if k == "splice" else "%s, %s" % (k, e["section"]))
        steps[name] += tsec
    steps["ties (75) and stick-on mounts (%d)" % n_mount] += len(ret) * 5 + n_mount * 3
    steps["heat shrink (34 sleeves)"] += sleeves * 5.1
    slow = steps.most_common(5)
    fix = {"Pi header joints (head floor)": "X1", "ties (75) and stick-on mounts (%d)" % n_mount: "X2"}
    with open(os.path.join(DATA, "cable_steps.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["step", "minutes_mid", "fix"])
        for k, v in steps.most_common():
            w.writerow([k, round(v / 60, 1), fix.get(k, "X4 (battery bay stars), X5 bench piece" if "splice" in k else ("X5 bench piece" if "solder" in k else ""))])
    with open(os.path.join(DATA, "cable_ops.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["section", "cable", "wire", "gauge", "end at", "op", "text"])
        for e in ends:
            w.writerow([e["section"], e["cable"], e["wire"], e["gauge"], e["where"], e["op"], e["text"]])
    # K4 printed tie bridge coupon: 2 posts on a pad, a bridge on top, slot for a 2.5 mm tie
    base = box(-6, -4, 6, 4)
    m = trimesh.creation.extrude_polygon(base, 1.6)
    posts = [trimesh.creation.box(extents=[2.5, 6, 2.8]).apply_translation([x, 0, 1.6 + 1.4]) for x in (-3.0, 3.0)]
    top = trimesh.creation.box(extents=[8.5, 6, 1.6]).apply_translation([0, 0, 1.6 + 2.8 + 0.8])
    k4 = trimesh.boolean.union([m] + posts + [top], engine="manifold")
    k4.export(os.path.join(HERE, "stl", "K4_tie_bridge.stl"))
    out = dict(before=before, after=after,
               hours=dict(before=[round(x / 3600, 2) for x in s_b], after_X1_X2_X3a_X4=[round(x / 3600, 2) for x in s_a],
                          after_without_X3=[round(x / 3600, 2) for x in s_n], after_with_X3b_too=[round(x / 3600, 2) for x in s_x]),
               calendar=dict(adhesive_dwell_h_before=DWELL_H[0], after=0, src=DWELL_H[1]),
               times={k: dict(s=v[0], src=v[1]) for k, v in T.items()}, blockers=BLOCKERS,
               slowest_5=[dict(step=k, minutes=round(v / 60, 1), fix=fix.get(k, "X4 and X5" if "splice" in k else "X5")) for k, v in slow],
               changes=changes, kept=["D25 joint loops 3 x OD and every cut length are unchanged (no route moves)",
                                      "strain relief: first tie after each connector stays (NASA Table 9-2, D25)",
                                      "fixed lengths at the joint limits: the joint motion job re-checks X2 bridges and X3 housings"],
               k4_tie_bridge=dict(stl="stl/K4_tie_bridge.stl", slot_mm=[3.0, 1.6], note="prints flat; the bridge is a 3.0 mm span (PRINT_CHECK.md bridge, no support)"))
    json.dump(out, open(os.path.join(DATA, "cable_changes.json"), "w"), indent=1)
    print(json.dumps(dict(before=before, after={k: after[k] for k in ("solder_ends", "crimps", "plugs", "sleeves", "mounts", "levers")},
                          hours=out["hours"], slowest=out["slowest_5"], pi_cables=pi_cables, ops=dict(op))))
    print([(c["id"], c["delta_s"]) for c in changes])


if __name__ == "__main__":
    main()
