#!/usr/bin/env python3
"""Propose screw cuts from the fitted schedule. Does not edit print/ or fasteners.json.

Writes CUTS.md. The 324 fitted count is the same one cad/fasteners/schedule.json repeats.
"""
import csv
import json
import os
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
FAST = os.path.join(REPO, "altaay_lab", "fasteners", "fasteners.json")
PARTS = os.path.join(REPO, "altaay_lab", "print", "parts.csv")
PRINT = os.path.join(REPO, "print")
OUT = os.path.join(HERE, "CUTS.md")

TAU = 12.7          # N/mm2, low end, STRUCTURE_TWIN.md
Y_BARB = 0.4        # mm, K3 deflection, lips.json
T_ARM = 0.9
L_ARM = 12.0
# eps = 1.5 * t * y / L^2 = 0.00375 (0.375 percent), under 0.535 percent
G = 9.81
A_HEAD = 196        # mid fall, head, SCREWS_TWIN.md
A_TRUNK = 128


def left_out(row):
    st = str(row.get("status") or "")
    return ("NOT FITTED" in st) or ("LEAVE OUT" in st)


def bucket(row):
    sup = row.get("supply") or ""
    spec = row.get("spec") or ""
    if "factory" in sup.lower():
        return "factory"
    if "SG90" in sup or "SG90" in spec:
        return "sg90"
    if "BOM 17" in sup or sup.startswith("NEW LINE") or sup.startswith("NEW LENGTH"):
        return "buy"
    if "servo bag" in sup or "comes with servo" in sup or "Feetech" in spec:
        return "bag"
    raise SystemExit("supply " + sup)


def bbox(path):
    raw = open(path, "rb").read()
    n = struct.unpack_from("<I", raw, 80)[0]
    xs, ys, zs = [], [], []
    off = 84
    for _ in range(n):
        vals = struct.unpack_from("<12fH", raw, off)
        xs += list(vals[3:12:3])
        ys += list(vals[4:12:3])
        zs += list(vals[5:12:3])
        off += 50
    return (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))


def up_extent(stl, ups):
    dx, dy, dz = bbox(os.path.join(PRINT, stl))
    spec = ups[stl]
    sizes = {"x": dx, "y": dy, "z": dz}
    if spec.startswith("vec:"):
        nums = spec[4:].split()
        comps = [abs(float(v)) for v in nums]
        axis = "xyz"[comps.index(max(comps))]
    else:
        axis = spec[-1]
    return sizes[axis], (dx, dy, dz), spec + " -> " + axis


def required_n(mass_g, accel):
    """One fastener must hold the mid-fall load at SF 1.2. Walk at 3 g and SF 2 is smaller for these masses."""
    m = mass_g / 1000.0
    fall = 1.2 * m * accel * G
    walk = 2.0 * m * 3.0 * G
    return max(fall, walk), fall, walk


def barb_width(force_n):
    return force_n / (Y_BARB * TAU)


def main():
    data = json.load(open(FAST, encoding="utf-8"))
    fit = [r for r in data["fasteners"] if r["kind"] == "screw" and not left_out(r)]
    if len(fit) != 324:
        raise SystemExit(len(fit))
    ups = {}
    with open(PARTS, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ups[row["stl"]] = row["up"]

    lines = []
    for r in fit:
        key = (r.get("part"), r.get("into"), r.get("spec"), bucket(r))
        lines.append(key)
    from collections import defaultdict
    grouped = defaultdict(lambda: {"n": 0, "ids": []})
    for r in fit:
        key = (r.get("part"), r.get("into"), r.get("spec"), bucket(r))
        grouped[key]["n"] += 1
        grouped[key]["ids"].append(r["id"])
    factory = builder = 0
    rows = []
    for key, rec in sorted(grouped.items(), key=lambda kv: (-kv[1]["n"], str(kv[0]))):
        part, into, spec, buck = key
        n = rec["n"]
        fac = n if buck == "factory" else 0
        bld = 0 if buck == "factory" else n
        factory += fac
        builder += bld
        rows.append((n, fac, bld, buck, spec, part, into, rec["ids"]))
    if factory != 56 or builder != 268:
        raise SystemExit((factory, builder))

    # package: K3 section, barb width set by the force, extrude along print-up
    # mass, accel, screws, stl that must be thick enough in the print-up axis, cite
    cands = [
        ("Eyes, both", 9.0, A_HEAD, 4, "left_eye.stl", "STRUCTURE_TWIN.md eye stack 9.0 g"),
        ("Speaker stand to head", 38.8, A_HEAD, 2, "speaker_stand.stl", "STRUCTURE_TWIN.md 38.8 g"),
        ("Speaker interface to stand", 31.1, A_HEAD, 2, "speaker_interface.stl", "STRUCTURE_TWIN.md 31.1 g"),
        ("Pi", 12.6, A_HEAD, 2, "head.stl", "STRUCTURE_TWIN.md 12.6 g, clip on the head"),
        ("Adapter", 16.0, A_TRUNK, 2, "trunk_top.stl", "STRUCTURE_TWIN.md 16 g, clip on trunk_top"),
        ("Mics, both", 0.4, A_HEAD, 4, "head.stl", "COMPANION.md 0.4 g each, product page"),
        ("Cliff board", 1.8, A_TRUNK, 2, "body_front.stl", "FREEZE.md 1.8 g"),
        ("Battery lid", 136.0, A_TRUNK, 4, "battery_pack_lid.stl", "SCREWS_TWIN.md 136 g with cells"),
        ("Head bottom sheet", 61.0, A_HEAD, 4, "head_bot_sheet.stl", "SCREWS_TWIN.md 61 g"),
    ]
    decisions = []
    for name, mass, accel, screws, stl, cite in cands:
        R, fall, walk = required_n(mass, accel)
        b = barb_width(R)
        ext, dims, up = up_extent(stl, ups)
        # Print the stock 5 mm K3 barb when the part is tall enough, else the
        # minimum width. Leave 0.3 mm, the hip-head margin in D19.
        stock = 5.0
        if ext >= max(b, stock) + 0.3:
            used = max(b, stock)
        elif ext >= b + 0.3:
            used = b
        else:
            used = b
        ok = ext + 1e-9 >= used + 0.3
        decisions.append(dict(name=name, mass=mass, accel=accel, screws=screws, stl=stl, cite=cite,
                              R=R, fall=fall, walk=walk, b=b, used=used, ext=ext, dims=dims, up=up, ok=ok))
    taken = [d for d in decisions if d["ok"]]
    saved = sum(d["screws"] for d in taken)
    if saved != 14:
        raise SystemExit("saved %s %s" % (saved, [(d["name"], d["ok"], round(d["b"], 2), round(d["ext"], 2)) for d in decisions]))

    out = []
    a = out.append
    a("# Screw cuts")
    a("")
    a("2026-11-12. Follows the DFA check (PR 52) and the fastener schedule in altaay_lab/cad/fasteners/. That schedule counts the same file: 361 screw rows, 324 fitted, 37 left out. Nest joints in that folder are not part of the 324, and this note does not add or remove them. print/ is not edited.")
    a("")
    a("The target is under 200 fitted screws. The package that passes the checks removes %d. Fitted screws go from 324 to %d. Screws the builder turns go from 268 to %d. Under 200 is not met. The screws that would have to go next are the horn screws, the case clamps, and the shell and frame screws. The checks below say those stay." % (saved, 324 - saved, 268 - saved))
    a("")
    a("Labels: CAD check only is a count or a mesh bound. Calc only is arithmetic on a cited load and the K3 section. Cited is a lab file or a page named in the sentence. BLOCKER means the number is not known, so that cut is not in the package.")
    a("")
    a("## The gap, line by line")
    a("")
    a("324 fitted minus 268 builder-turned is 56. That 56 is one schedule line, not a mix of leftovers from other joints.")
    a("")
    a("| Supply | Fitted | Who turns it |")
    a("|---|---|---|")
    a("| Buy lines (BOM 17, including 10 button heads and 2 M2x12 whose supply string still says NEW LINE or NEW LENGTH) | 205 | builder |")
    a("| Servo bag (horn centre screws, fitted idle screws, M2 case screws from the bag) | 57 | builder |")
    a("| Ear-servo bag | 6 | builder |")
    a("| Factory case screws, already in the servo | 56 | not the builder |")
    a("| Sum | 324 | 268 builder |")
    a("")
    a("205 + 57 + 6 = 268. 268 + 56 = 324. CAD check only, from fasteners.json, the same split cad/fasteners/schedule.json repeats.")
    a("")
    a("The 56 factory screws are PA2.0, servo top case into servo bottom case, status FACTORY. There are 14 servos and 4 of these screws on each (head pitch, head roll, head yaw, neck pitch, and both ankles, knees, hip pitches, hip rolls, and hip yaws). 14 x 4 = 56. No other line has a factory screw. On every other line the builder count equals the fitted count.")
    a("")
    a("| Fitted | Factory | Builder turns | Supply | Spec | Joint |")
    a("|---|---|---|---|---|---|")
    for n, fac, bld, buck, spec, part, into, ids in rows:
        joint = "%s -> %s" % (part, into)
        a("| %d | %d | %d | %s | %s | %s |" % (n, fac, bld, buck, spec.replace("|", "/"), joint.replace("|", "/")))
    a("")
    a("Sum of the fitted column is 324. Sum of the factory column is 56. Sum of the builder column is 268.")
    a("")
    a("## What a cut has to clear")
    a("")
    a("The clip is the K3 cable clip already drawn (twin/screws/mesh_designs.py and lips.json): arm 0.9 mm thick, 12 mm long, barb overlap 0.4 mm. Strain is 1.5 x 0.9 x 0.4 / 12 squared = 0.375 percent. The service limit already used there is 0.535 percent. Changing only the barb width does not change that strain. The formula is the cantilever on the Fictiv page opened for DFA.md (https://www.fictiv.com/articles/how-to-design-snap-fit-components).")
    a("")
    a("One clip has to hold the whole part, the same one-fastener rule as the screws twin. The load is the mid fall, 196 g on the head and 128 g on the trunk (cited, SCREWS_TWIN.md). SF 1.2. Walk at 3 g and SF 2 is the smaller number on every row below, so the fall sets the clip. Shear uses 12.7 MPa, the low end of the range in STRUCTURE_TWIN.md (0.577 x 22 MPa). One barb at width b and overlap 0.4 mm holds b x 0.4 x 12.7 N.")
    a("")
    a("The arm bends in the layer plane, which is the Fictiv note for a printed cantilever. The barb width is then the print-up height. parts.csv names that axis. A clip is not used when the required width is taller than that print-up extent (CAD check only).")
    a("")
    a("A clip comes off the same way it goes on: the Fictiv note says a return angle equal to the lead angle uses one force both ways. The parts stay separate, so the speaker still drops into the cage (ASSEMBLY_TWIN.md). They are not merged.")
    a("")
    a("## Package: %d screws" % saved)
    a("")
    a("These pass the force calc and the print-up bound with 0.3 mm to spare (the hip-head margin in D19). Rank is screws saved. The effort is the same on each row: the K3 section, barb width only. A minimum under 5 mm is printed at the stock 5 mm when the part is tall enough.")
    a("")
    a("| Rank | Joint | Screws now | After | Saved | Barb used mm | Print-up extent mm | STL |")
    a("|---|---|---|---|---|---|---|---|")
    rank = 1
    order = sorted(taken, key=lambda z: (-z["screws"], z["name"]))
    for d in order:
        a("| %d | %s | %d | 0 | %d | %.1f | %.1f (%s) | %s |" % (
            rank, d["name"], d["screws"], d["screws"], d["used"], d["ext"], d["up"], d["stl"]))
        rank += 1
    a("| | Sum | %d | 0 | %d | | | |" % (saved, saved))
    a("")
    a("Fitted screws 324 - %d = %d. Builder-turned screws 268 - %d = %d. Washers stay 8 (the eye screws stay). Inserts stay 48. These joints use pilots, not the heat-set inserts." % (
        saved, 324 - saved, saved, 268 - saved))
    a("")
    a("Per row, calc only unless noted:")
    a("")
    for d in order:
        note = "Printed at the stock 5 mm." if abs(d["used"] - 5.0) < 0.05 else "Wider than 5 mm, same arm thickness and length."
        a("- %s. Mass %g g (%s). Required %.1f N, so the minimum barb is %.1f mm. Printed width %.1f mm. Print-up extent %.1f mm on %s, axis %s, bounds %.1f x %.1f x %.1f mm (CAD check only). %s" % (
            d["name"], d["mass"], d["cite"], d["R"], d["b"], d["used"], d["ext"], d["stl"], d["up"], d["dims"][0], d["dims"][1], d["dims"][2], note))
    a("")
    a("The cliff board keeps the printed standoffs from D54. The clip only holds the board down. The 25.4 x 17.8 mm board (cited, FREEZE.md) is wider than a 5 mm clip.")
    a("")
    a("The mic board is 16.7 x 12.7 mm (cited, COMPANION.md). A 5 mm clip fits that edge. The arm sits on the head. The 0.4 g is each board, and each board gets its own clip.")
    a("")
    a("Neighbour clash of the new clip against the next part is not swept. That sweep is the CAD check still open before anyone edits an STL. It is not a reason these %d fail the force check." % saved)
    a("")
    a("## Checked, and not in the %d" % saved)
    a("")
    a("| Idea | Screws it would touch | Result | Check |")
    a("|---|---|---|---|")
    a("| Eye clips | 4, and 8 washers | Minimum barb 4.1 mm, print-up extent 4.3 mm. Gap 0.2 mm, under the 0.3 mm margin. Screws stay. | CAD check only, fails |")
    a("| Battery lid clip | 4 | Print-up extent 7.5 mm, required barb 40.3 mm. Does not fit. Screws stay. | CAD check only, fails |")
    a("| Head bottom sheet clip | 4 | Print-up extent 3.0 mm, required barb 27.7 mm. Does not fit. Screws stay. | CAD check only, fails |")
    a("| Body shells | 10 (back 6, front 4) | Mid shell hit 2800 N (cited, SCREWS_TWIN.md). SF 1.2 needs about 660 mm of barb. The lips already carry shear. The screws stay. | calc only, fails |")
    a("| Horn screws, 4 down to 2 | 50 if every 4-hole horn lost 2 | Halving the screw count is taken as doubling the peak. Foot walk 3.86 becomes 1.93, under 2. Hip-roll soft fall 2.33 becomes 1.17, under 1.2. Roll, shin, thigh, neck, and head are already under a margin (PR 43, FEA pass only). PR 46 keeps four drive screws on each shin. Not cut. | calc only, fails |")
    a("| Servo case clamps | 68 | docs/assembly_guide.md says to fit the plastic screws that come with the servos. Pull-out of those M2 screws from the case is already a BLOCKER (STRUCTURE_TWIN.md). Not cut. | BLOCKER |")
    a("| Ear screws | 6 | Antenna impact is not modelled (screws twin). | BLOCKER |")
    a("| IMU, 4 screws | 4 | The screws twin keeps all 4. Not a clip. | cited |")
    a("| Charger, 1 screw | 1 | Inertial load is small. The plug force is not in the schedule. | BLOCKER |")
    a("| Camera, 2 screws | 2 | STRUCTURE_TWIN.md marks the 4 g mass UNVERIFIED. | BLOCKER |")
    a("| Heat-set insert swapped for a captive nut | 0 | The screw stays. Nuts would rise from 0. CNC Kitchen comparison is already cited in STRUCTURE_TWIN.md. Not a screw cut. | cited |")
    a("| Merge speaker interface and stand | 2 | The speaker is caged between them (ASSEMBLY_TWIN.md). Merging closes the cage. The clip keeps both parts. | CAD check only |")
    a("| Merge foot side and foot top | 4 | Those faces are the supports in the PR 43 foot study. A merge needs that study again. Not run. Not in the package. | FEA pass only, not run |")
    a("| Cache screws into the spacer | 4 | The screw also ties the knee sheet (screws twin). The spacer is in the thigh study. Not cut. | FEA pass only, not run |")
    a("")
    a("Even if the failed horn cut (50) and a rough half of the case clamps (34) were added to the %d, fitted screws would be 324 - %d - 50 - 34 = %d. Still over 200. Crossing under 200 would also drop shell screws or the frame and spacer screws. Those are the joints that hold the legs and the trunk. They are not in this package." % (
        saved, saved, 324 - saved - 50 - 34))
    a("")
    a("## CAD edits, not applied")
    a("")
    a("No file under print/ changes. No row in fasteners.json changes. When a later job does the STL work, the edits are:")
    a("")
    edits = {
        "Mics, both": "head.stl: stock K3 section, barb %.1f mm, at each mic board (F356, F357, F358, F359). Close those pilots.",
        "Pi": "head.stl: K3 section, barb %.1f mm, at the Pi pilots (F111, F114). Close those pilots.",
        "Adapter": "trunk_top.stl: K3 section, barb %.1f mm, at the adapter (F119, F122). Close those pilots.",
        "Cliff board": "body_front.stl: K3 section, barb %.1f mm, holding the cliff board (F360, F361). Keep the D54 standoffs. Close only the two screw pilots.",
        "Speaker interface to stand": "speaker_interface.stl: K3 section, barb %.1f mm. Close the stand pilots for F353 and F354. The two parts stay separate.",
        "Speaker stand to head": "speaker_stand.stl: K3 section, barb %.1f mm. Close the head pilots for F108 and F109.",
    }
    for d in order:
        a("- " + (edits[d["name"]] % d["used"]))
    a("")
    a("D42: a joint with no screws left is a uniform pattern. The holes close with the STL edit, which is D39.")
    a("")
    a("## Open items")
    a("")
    a("- Under 200 fitted screws: not met. %d is the package. The next %d are blocked by the checks above." % (324 - saved, 324 - saved - 200))
    a("- Neighbour clash of each new clip: not swept. CAD check still open before an STL edit.")
    a("- Coupon K3 has not been printed (screws twin). The strain number is calc only.")
    a("- Camera mass: BLOCKER (UNVERIFIED in STRUCTURE_TWIN.md).")
    a("- Charger plug force: BLOCKER.")
    a("- Ear impact: BLOCKER.")
    a("- M2 pull-out from the servo case: BLOCKER (STRUCTURE_TWIN.md).")
    a("- Hot tensile of the printed arms: BLOCKER, already in TOPOLOGY.md. These clips are not on those arms.")
    a("")
    text = "\n".join(out) + "\n"
    for bad, name in (("\u2014", "em"), ("\u2013", "en"), ("/agent", "path"), ("/home/", "path"), ("#52", "hash"), ("#43", "hash"), ("#46", "hash"), ("$", "price")):
        if bad in text:
            raise SystemExit(name)
    if ("| | Sum | %d | 0 | %d |" % (saved, saved)) not in text:
        raise SystemExit("sum row")
    open(OUT, "w", encoding="utf-8").write(text)
    print("wrote", OUT, "lines", len(out), "saved", saved)


if __name__ == "__main__":
    main()
