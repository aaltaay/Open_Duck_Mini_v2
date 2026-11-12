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

E_MPA = 2641.0      # STRUCTURE_TWIN.md, the modulus used for K3
Y_MM = 0.4          # K3 overlap, lips.json and clip_mesh
EPS_MAX = 0.00535   # 0.535 percent service limit already used for K3
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
    """One clip must hold the mid-fall load at SF 1.2. Walk at 3 g and SF 2 is smaller for these masses."""
    m = mass_g / 1000.0
    fall = 1.2 * m * accel * G
    walk = 2.0 * m * 3.0 * G
    return max(fall, walk), fall, walk


def strain(t, L, y=Y_MM):
    return 1.5 * t * y / (L * L)


def pull_off_n(b, t, L, y=Y_MM):
    """Both arms. 45 degree return, friction not credited, so pull-off equals the force that deflects both arms by y."""
    return 2.0 * E_MPA * b * (t ** 3) * y / (4.0 * (L ** 3))


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

    # name, mass_g, accel, screws, stl, cite, barb width, thickness, length
    # Arms are the K3 cantilever with the same 45 degree return. Thickness and length
    # are raised only when the stock 0.9 x 12 mm arm cannot meet the pull-off.
    cands = [
        ("Mics, both", 0.4, A_HEAD, 4, "head.stl", "COMPANION.md 0.4 g each, product page", 5.0, 0.9, 12.0),
        ("Cliff board", 1.8, A_TRUNK, 2, "body_front.stl", "FREEZE.md 1.8 g", 5.0, 1.27, 12.0),
        ("Adapter", 16.0, A_TRUNK, 2, "trunk_top.stl", "STRUCTURE_TWIN.md 16 g, clip on trunk_top", 10.0, 3.5, 20.0),
        ("Pi", 12.6, A_HEAD, 2, "head.stl", "STRUCTURE_TWIN.md 12.6 g, clip on the head", 12.0, 3.5, 20.0),
        ("Speaker interface to stand", 31.1, A_HEAD, 2, "speaker_interface.stl", "STRUCTURE_TWIN.md 31.1 g", 14.0, 5.5, 25.0),
        ("Speaker stand to head", 38.8, A_HEAD, 2, "speaker_stand.stl", "STRUCTURE_TWIN.md 38.8 g", 33.0, 3.5, 20.0),
    ]
    decisions = []
    for name, mass, accel, screws, stl, cite, b, t, L in cands:
        R, fall, walk = required_n(mass, accel)
        ext, dims, up = up_extent(stl, ups)
        # up extent is the barb-width direction. The other two axes are length and thickness.
        inplane = sorted([dims[i] for i, ax in enumerate("xyz") if ax != up.split("->")[-1].strip()])
        w = pull_off_n(b, t, L)
        eps = strain(t, L)
        fits = ext >= b + 0.3 and inplane[-1] >= L + 2.0 and inplane[0] >= t
        ok = fits and w + 1e-9 >= R and eps <= EPS_MAX + 1e-12
        decisions.append(dict(name=name, mass=mass, accel=accel, screws=screws, stl=stl, cite=cite,
                              R=R, fall=fall, walk=walk, b=b, t=t, L=L, w=w, eps=eps, ext=ext,
                              dims=dims, up=up, inplane=inplane, ok=ok))
    taken = [d for d in decisions if d["ok"]]
    saved = sum(d["screws"] for d in taken)
    if saved != 14 or len(taken) != 6:
        raise SystemExit("saved %s %s" % (saved, [(d["name"], d["ok"], round(d["w"], 2), round(d["R"], 2), round(100 * d["eps"], 3)) for d in decisions]))
    stock_pi = pull_off_n(5.7, 0.9, 12.0)
    if not (1.2 < stock_pi < 1.4):
        raise SystemExit("stock pi pull-off %.3f" % stock_pi)

    out = []
    a = out.append
    a("# Screw cuts")
    a("")
    a("2026-11-12. Follows the DFA check (PR 52) and the fastener schedule in altaay_lab/cad/fasteners/. That schedule counts the same file: 361 screw rows, 324 fitted, 37 left out. Nest joints in that folder are not part of the 324, and this note does not add or remove them. print/ is not edited.")
    a("")
    a("The target is under 200 fitted screws. The package that passes pull-off removes %d. Fitted screws go from 324 to %d. Screws the builder turns go from 268 to %d. Under 200 is not met. The screws that would have to go next are the horn screws, the case clamps, and the shell and frame screws. The checks below say those stay." % (saved, 324 - saved, 268 - saved))
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
    a("The clip is the K3 cantilever already drawn in twin/screws/mesh_designs.py. The return face runs 0.4 mm across and 0.4 mm up, so it is 45 degrees, the same angle as the lead-in. A pull through that face spreads the arms. The barbs do not have to shear. Pull-off is the force that deflects both arms by the 0.4 mm overlap.")
    a("")
    a("With friction left at zero, that force equals the sum of the two beam forces. Each beam is P = E b t cubed y / (4 L cubed), E = 2641 MPa (the modulus already used for K3). Strain is 1.5 t y / L squared, and it stays at or under 0.535 percent, the service limit already used for K3. The Fictiv cantilever page is the same source as DFA.md (https://www.fictiv.com/articles/how-to-design-snap-fit-components). A stock Pi clip, 5.7 mm wide on the unchanged 0.9 x 12 mm arms, pulls off at %.2f N. The Pi needs %.1f N. That clip does not pass. Shear area is not the check." % (stock_pi, required_n(12.6, A_HEAD)[0]))
    a("")
    a("One clip has to hold the whole part, the same one-fastener rule as the screws twin. The load is the mid fall, 196 g on the head and 128 g on the trunk (cited, SCREWS_TWIN.md). SF 1.2. Walk at 3 g and SF 2 is smaller on every row, so the fall sets the clip. Where the stock arm is too soft, thickness and length go up, and the 45 degree return stays so the part still comes off by hand. The parts stay separate, so the speaker still drops into the cage (ASSEMBLY_TWIN.md).")
    a("")
    a("The barb width is the print-up height. parts.csv names that axis. The arm length and thickness have to fit the other two bounds. A clip needs 0.3 mm spare on the print-up axis, the hip-head margin in D19.")
    a("")
    a("## Package: %d screws" % saved)
    a("")
    a("These pass pull-off, the strain limit, and the part bounds. Rank is screws saved. Effort is the same kind of edit on each row: the K3 cantilever, resized only as the table says.")
    a("")
    a("| Rank | Joint | Saved | Arm mm | Pull-off N | Required N | Strain percent |")
    a("|---|---|---|---|---|---|---|")
    rank = 1
    order = sorted(taken, key=lambda z: (-z["screws"], z["name"]))
    for d in order:
        a("| %d | %s | %d | %.2f x %.1f x %.0f | %.2f | %.2f | %.3f |" % (
            rank, d["name"], d["screws"], d["t"], d["b"], d["L"], d["w"], d["R"], 100.0 * d["eps"]))
        rank += 1
    a("| | Sum | %d | | | | |" % saved)
    a("")
    a("Arm is thickness x width x length. Pull-off and required force are calc only. Strain is calc only.")
    a("")
    a("Fitted screws 324 - %d = %d. Builder-turned screws 268 - %d = %d. Washers stay 8 (the eye screws stay). Inserts stay 48. These joints use pilots, not the heat-set inserts." % (
        saved, 324 - saved, saved, 268 - saved))
    a("")
    for d in order:
        a("- %s. Mass %g g (%s). Print-up extent %.1f mm on %s, axis %s, bounds %.1f x %.1f x %.1f mm (CAD check only)." % (
            d["name"], d["mass"], d["cite"], d["ext"], d["stl"], d["up"], d["dims"][0], d["dims"][1], d["dims"][2]))
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
    eye_w = pull_off_n(4.0, 5.1, 24.0)
    eye_r = required_n(9.0, A_HEAD)[0]
    a("| Eye clips | 4, and 8 washers | Largest arm inside the 0.3 mm margin (4.0 x 5.1 x 24 mm) pulls off at %.1f N. The stack needs %.1f N. Screws stay. | calc only, fails |" % (eye_w, eye_r))
    a("| Battery lid clip | 4 | Stock K3 pull-off is %.2f N. The lid needs %.0f N. Print-up extent is 7.5 mm. Screws stay. | calc only, fails |" % (pull_off_n(5.0, 0.9, 12.0), required_n(136.0, A_TRUNK)[0]))
    a("| Head bottom sheet clip | 4 | Same stock pull-off, %.2f N, against %.0f N. Print-up extent is 3.0 mm. Screws stay. | calc only, fails |" % (pull_off_n(5.0, 0.9, 12.0), required_n(61.0, A_HEAD)[0]))
    a("| Body shells | 10 (back 6, front 4) | Mid shell hit 2800 N (cited, SCREWS_TWIN.md). A 45 degree clip in this size range is a few newtons. The lips already carry shear. The screws stay. | calc only, fails |")
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
        "Mics, both": "head.stl: K3 clip, arm %.2f x %.1f x %.0f mm, at each mic board (F356, F357, F358, F359). Close those pilots.",
        "Pi": "head.stl: same cantilever and 45 degree return, arm %.2f x %.1f x %.0f mm, at the Pi pilots (F111, F114). Close those pilots.",
        "Adapter": "trunk_top.stl: same clip, arm %.2f x %.1f x %.0f mm, at the adapter (F119, F122). Close those pilots.",
        "Cliff board": "body_front.stl: same clip, arm %.2f x %.1f x %.0f mm, holding the cliff board (F360, F361). Keep the D54 standoffs. Close only the two screw pilots.",
        "Speaker interface to stand": "speaker_interface.stl: same clip, arm %.2f x %.1f x %.0f mm. Close the stand pilots for F353 and F354. The two parts stay separate.",
        "Speaker stand to head": "speaker_stand.stl: same clip, arm %.2f x %.1f x %.0f mm. Close the head pilots for F108 and F109.",
    }
    for d in order:
        a("- " + (edits[d["name"]] % (d["t"], d["b"], d["L"])))
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
    if ("| | Sum | %d |" % saved) not in text:
        raise SystemExit("sum row")
    open(OUT, "w", encoding="utf-8").write(text)
    print("wrote", OUT, "lines", len(out), "saved", saved)


if __name__ == "__main__":
    main()
