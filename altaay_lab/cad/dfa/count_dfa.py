#!/usr/bin/env python3
"""Count fitted fasteners from the CAD schedule and write the DFA note and figure.

The schedule is altaay_lab/fasteners/fasteners.json. altaay_lab/cad/fasteners/ is not
in the tree. This script does not edit print/, fasteners.json, or any FEA mesh.
Numbers in DFA.md are filled from this count so the note cannot drift from the JSON.
"""
import json
import os
from collections import Counter, defaultdict

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
LAB = os.path.join(REPO, "altaay_lab")
FAST = os.path.join(LAB, "fasteners", "fasteners.json")
SLICE = os.path.join(LAB, "print", "SLICE_SUMMARY.md")
PARTS = os.path.join(LAB, "print", "parts.csv")

# PR 43 study members, plus the foot supports that study fixes (TOPOLOGY.md, st_fea_run.py).
FEA_PARTS = {
    "shin_left_sheet", "shin_right_sheet", "shin_spacer",
    "knee_to_ankle_left_sheet", "knee_to_ankle_right_sheet", "leg_spacer",
    "left_roll_to_pitch", "right_roll_to_pitch",
    "roll_motor_top", "roll_motor_bottom",
    "foot_top", "foot_side", "foot_bottom_pla",
    "neck_left_sheet", "neck_right_sheet",
    "head_roll_mount",
}
FRAME = {"trunk_top", "trunk_bottom", "body_middle_top", "body_middle_bottom"}
SHELL = {"body_front", "body_back", "battery_pack_lid", "head_bot_sheet"}


def left_out(row):
    st = str(row.get("status") or "")
    return ("NOT FITTED" in st) or ("LEAVE OUT" in st)


def supply_bucket(row):
    sup = row.get("supply") or ""
    spec = row.get("spec") or ""
    if "factory" in sup.lower():
        return "factory"
    if "SG90" in sup or "SG90" in spec:
        return "sg90"
    # 10 button heads and 2 M2x12 still say NEW LINE / NEW LENGTH. FASTENERS.md
    # section 2 counts them on BOM 17j and 17m, inside the 205 to buy.
    if "BOM 17" in sup or sup.startswith("NEW LINE") or sup.startswith("NEW LENGTH"):
        return "buy"
    if "servo bag" in sup or "comes with servo" in sup or "Feetech" in spec:
        return "bag"
    return "other:" + sup


def role(row):
    anchor = row.get("anchor") or ""
    spec = row.get("spec") or ""
    part = row.get("part") or ""
    into = row.get("into") or ""
    if row.get("kind") != "screw":
        return "insert"
    if "factory" in anchor or "FACTORY" in str(row.get("status") or ""):
        return "factory"
    if "SG90" in spec or "antenna" in part:
        return "ears"
    if anchor.startswith("horn") or "output shaft" in anchor or "idle boss" in anchor:
        return "horn"
    if "servo pilot" in anchor or anchor.startswith("servo"):
        return "case"
    if part in SHELL:
        return "cover"
    if anchor == "M3 insert" or part in FEA_PARTS or into in FEA_PARTS or part in FRAME or into in FRAME:
        return "structure"
    return "cover"


def proposal(part, into, anchor, spec):
    anchor = anchor or ""
    spec = spec or ""
    part = part or ""
    into = into or ""
    if "factory" in anchor:
        return ("Keep", "Factory screws inside the servo. The builder does not fit them.")
    if "SG90" in spec or "antenna" in part:
        return ("Keep", "Screws twin keeps the ear screws. Antenna impact is not modelled, so a cut is BLOCKER.")
    if part == "neck_stop":
        return ("Keep", "Two case screws, lengthened to hold the neck stop. Servo clamp stays screwed.")
    if "shin_left_sheet" in part and anchor.startswith("horn"):
        return ("Keep", "Servo load. PR 46 keeps four drive-horn screws on each shin (eight fitted). D42 unchanged.")
    if anchor.startswith("horn") or "output shaft" in anchor or "idle boss" in anchor:
        return ("Keep", "Servo load path. The screws twin keeps the servo chain. Foot and the hip-roll stage clear the PR 43 soft-fall margin. Roll, shin, thigh, neck, and head do not. No horn screw is removed.")
    if "servo pilot" in anchor or anchor.startswith("servo"):
        return ("Keep", "Clamps the servo case. The reaction stays screwed.")
    if part == "body_back":
        return ("Keep", "D38 kept these screws because a 3-screw back shell fails the downward fall check. Six stay fitted. Not cut further.")
    if part in SHELL:
        return ("Keep", "Screws twin: a thin plate keeps a 3-point set. D42 rejected a non-uniform 3, so the fitted uniform set stays.")
    if "cache" in part:
        return ("Keep", "Screws twin keeps the cache with the leg stack. leg_spacer is in the thigh study. STL not changed.")
    if part in ("foot_top", "foot_side", "foot_bottom_pla", "foot_bottom_tpu") or into in ("foot_top", "foot_side", "foot_bottom_pla"):
        return ("Keep", "Foot joint. PR 43 fixes foot_bottom_pla and foot_side when it loads foot_top. STL not changed. Solver not re-run.")
    if part in FEA_PARTS or into in FEA_PARTS:
        return ("Keep", "Printed structure on a PR 43 or PR 46 part. STL not changed. Solver not re-run.")
    if part in FRAME and into in FRAME:
        return ("Keep", "Frame joint. The screws twin kept the trunk stack (no lateral key). Not a PR 43 mesh member. STL not changed.")
    if "charger" in part:
        return ("Keep", "One screw. The screws twin keeps it for the plug force.")
    if "bno" in part:
        return ("Keep", "Four screws. The screws twin keeps the IMU at 4.")
    if "mic" in part.lower() or "tof" in part or "cliff" in part:
        return ("Keep", "A mirror pair or a diagonal pair already (D42). No new clip is drawn.")
    return ("Keep", "Already at the screws twin minimum for a board (a diagonal or a mirror pair). The only snap in the repo is the K3 cable clip, and its coupon has not been run.")


def slice_base():
    """Cited part-row total in SLICE_SUMMARY.md, before the freeze prose delta."""
    text = open(SLICE, encoding="utf-8").read()
    # The totals row under the per-part table: | Total | 68 | 1355.5 | 119.9 |
    want = None
    for ln in text.splitlines():
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if cells and cells[0] == "Total" and len(cells) >= 4:
            try:
                parts = int(cells[1])
                grams = float(cells[2])
                hours = float(cells[3])
            except ValueError:
                continue
            if parts == 68 and grams > 1000:
                want = (parts, grams, hours)
    if want is None:
        raise SystemExit("SLICE_SUMMARY total row not found")
    return want


def parts_qty():
    import csv
    with open(PARTS, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return len(rows), sum(int(float(r["qty"])) for r in rows)


def load():
    data = json.load(open(FAST, encoding="utf-8"))
    rows = data["fasteners"]
    screws = [r for r in rows if r["kind"] == "screw"]
    inserts = [r for r in rows if r["kind"] == "insert"]
    other = [r for r in rows if r["kind"] not in ("screw", "insert")]
    if other:
        raise SystemExit("unexpected fastener kinds: %s" % Counter(r["kind"] for r in other))
    fit = [r for r in screws if not left_out(r)]
    out = [r for r in screws if left_out(r)]
    ins_fit = [r for r in inserts if not left_out(r)]
    ins_out = [r for r in inserts if left_out(r)]
    if len(fit) != 324 or len(out) != 37:
        raise SystemExit("screw fit/out %d/%d, expected 324/37" % (len(fit), len(out)))
    if len(ins_fit) != 48 or len(ins_out) != 10:
        raise SystemExit("insert fit/out %d/%d, expected 48/10" % (len(ins_fit), len(ins_out)))
    buckets = Counter(supply_bucket(r) for r in fit)
    if buckets["buy"] != 205 or buckets["bag"] != 57 or buckets["factory"] != 56 or buckets["sg90"] != 6:
        raise SystemExit("supply split %s, expected buy 205, bag 57, factory 56, sg90 6" % dict(buckets))
    if any(k.startswith("other") for k in buckets):
        raise SystemExit("unbucketed supply %s" % dict(buckets))
    washers = sum(2 for r in fit if "washer" in (r.get("spec") or "").lower() and "0.3" in (r.get("spec") or ""))
    # Eye screws carry two washers in the spec string. No other washer rows.
    if washers != 8:
        raise SystemExit("washers %d, expected 8" % washers)
    roles = Counter(role(r) for r in fit)
    if sum(roles.values()) != 324:
        raise SystemExit("roles do not sum")
    horn_specs = Counter(r["spec"] for r in fit if role(r) == "horn")
    joints = defaultdict(list)
    for r in fit:
        key = (r.get("part"), r.get("into"), r.get("anchor"), r.get("spec"))
        joints[key].append(r["id"])
    joint_rows = []
    for (part, into, anchor, spec), ids in sorted(joints.items(), key=lambda kv: (-len(kv[1]), str(kv[0]))):
        action, why = proposal(part, into, anchor, spec)
        if action != "Keep" or len(ids) == 0:
            raise SystemExit("bad proposal")
        joint_rows.append({
            "part": part, "into": into, "anchor": anchor, "spec": spec,
            "qty": len(ids), "ids": ids, "action": action, "why": why,
            "role": role({"kind": "screw", "part": part, "into": into, "anchor": anchor, "spec": spec, "status": ""}),
        })
    if sum(j["qty"] for j in joint_rows) != 324:
        raise SystemExit("joint qty")
    return {
        "fit": len(fit), "out": len(out), "screw_rows": len(screws),
        "inserts_fit": len(ins_fit), "inserts_out": len(ins_out), "insert_rows": len(inserts),
        "nuts": 0, "washers": washers,
        "buckets": dict(buckets), "roles": dict(roles), "horn_specs": dict(horn_specs),
        "builder_screws": len(fit) - buckets["factory"],
        "joints": joint_rows,
        "specs": dict(Counter(r["spec"] for r in fit)),
    }


def draw(count, path):
    font = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    font_b = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    title = ImageFont.truetype(font_b, 28)
    sub = ImageFont.truetype(font, 16)
    label = ImageFont.truetype(font, 15)
    small = ImageFont.truetype(font, 13)
    bold = ImageFont.truetype(font_b, 15)
    W, H = 1400, 860
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.text((40, 28), "Fitted fasteners, before and after this check", font=title, fill="#1a1a1a")
    d.text((40, 68), "CAD check only, from the fastener schedule. After matches before. No new latch was drawn.", font=sub, fill="#333333")

    # Left panel: before / after groups
    names = ["Screws", "Inserts", "Nuts", "Washers"]
    vals = [count["fit"], count["inserts_fit"], count["nuts"], count["washers"]]
    origin_x, origin_y = 80, 760
    max_v = 360
    plot_h = 520
    group_w = 150
    bar_w = 46
    colors = ("#1f4e79", "#e07a3d")
    d.text((80, 110), "Before and after", font=bold, fill="#1a1a1a")
    for i, (name, val) in enumerate(zip(names, vals)):
        gx = origin_x + i * group_w
        for j, color in enumerate(colors):
            h = int(plot_h * val / max_v) if val else 2
            x0 = gx + j * (bar_w + 8)
            y0 = origin_y - h
            d.rectangle([x0, y0, x0 + bar_w, origin_y], fill=color)
            d.text((x0, y0 - 22), str(val), font=small, fill="#1a1a1a")
        d.text((gx, origin_y + 10), name, font=label, fill="#1a1a1a")
    # legend
    d.rectangle([80, 800, 100, 820], fill=colors[0])
    d.text((108, 798), "Before", font=small, fill="#1a1a1a")
    d.rectangle([200, 800, 220, 820], fill=colors[1])
    d.text((228, 798), "After (same count)", font=small, fill="#1a1a1a")

    # Right panel: where the screws sit
    d.text((760, 110), "Where the 324 fitted screws sit", font=bold, fill="#1a1a1a")
    d.text((760, 134), "Same split before and after.", font=small, fill="#333333")
    order = [
        ("factory", "Factory, inside the servo", "#7f8c8d"),
        ("horn", "Horns and shaft screws", "#1f4e79"),
        ("case", "Servo case clamps", "#2e86ab"),
        ("structure", "Printed structure and frame", "#c47b2b"),
        ("cover", "Covers, boards, eyes", "#3d6b4f"),
        ("ears", "Ear servos", "#6b4f8a"),
    ]
    roles = count["roles"]
    if sum(roles[k] for k, _, _ in order) != 324:
        raise SystemExit("figure roles %s" % roles)
    top = 180
    bar_max = 520
    for i, (key, name, color) in enumerate(order):
        y = top + i * 78
        val = roles[key]
        w = int(bar_max * val / 180)
        d.rectangle([760, y, 760 + max(w, 8), y + 36], fill=color)
        d.text((760 + max(w, 8) + 12, y + 8), "%d  %s" % (val, name), font=label, fill="#1a1a1a")
    d.text((760, 680), "Horns, shaft screws, and case clamps stay.", font=small, fill="#333333")
    d.text((760, 702), "They carry servo load. PR 43 and PR 46 parts are not edited.", font=small, fill="#333333")
    d.text((760, 724), "Inserts 48 fitted, 10 already left out. Nuts 0. Washers 8.", font=small, fill="#333333")
    img.save(path, "PNG", optimize=True)
    if os.path.getsize(path) > 5 * 1024 * 1024:
        raise SystemExit("png over 5 MB")


def write_md(count, path):
    parts_rows, parts_n = parts_qty()
    if parts_n != 68 or parts_rows != 49:
        raise SystemExit("parts.csv %d rows qty %d" % (parts_rows, parts_n))
    _p, grams, hours = slice_base()
    if (grams, hours) != (1355.5, 119.9):
        raise SystemExit("slice total %s %s" % (grams, hours))
    # Freeze prose in the same file: head, speaker_interface, body_front, +5.88 g and +0.74 h.
    # Those three rows in the table are still the pre-freeze grams (checked by the note's "was" figures).
    fil_g = round(grams + 5.88, 1)
    fil_h = round(hours + 0.74, 1)
    if fil_g != 1361.4 or fil_h != 120.6:
        raise SystemExit("filament sum %s %s" % (fil_g, fil_h))
    lines = []
    a = lines.append
    a("# DFA: fastener count")
    a("")
    a("2026-11-12. This pass counts the CAD schedule and checks each joint against patterns already in the lab or on a page opened for this note. It does not draw a new latch, clip, hinge, or twist-lock. It does not edit print/, the fastener schedule, or the structure meshes.")
    a("")
    a("altaay_lab/cad/fasteners/ is not in the tree. The count is altaay_lab/fasteners/fasteners.json (361 screw rows, 58 insert rows). The screws twin, D39, and D42 already removed what their checks allowed. This note builds on that. It does not repeat their cuts as if they were still available.")
    a("")
    a("Labels: CAD check only is a count or a fit read from that schedule or from parts.csv. Cited is a page or a lab file named in the sentence. Calc only is arithmetic on those. FEA pass only is a safety factor from PR 43 or PR 46, not a new solve. BLOCKER means the number was not measured here.")
    a("")
    a("## Before and after")
    a("")
    a("| Item | Before | After | Label |")
    a("|---|---|---|---|")
    a("| Screws fitted | 324 | 324 | CAD check only |")
    a("| Screws left out on purpose | 37 | 37 | CAD check only |")
    a("| Screw rows in the schedule | 361 | 361 | CAD check only |")
    a("| Inserts fitted | 48 | 48 | CAD check only |")
    a("| Inserts left out | 10 | 10 | CAD check only |")
    a("| Nuts | 0 | 0 | CAD check only (no nut rows). FASTENERS.md cites a feat3d run with 0 hex pockets (cited, not re-run) |")
    a("| Washers on the eye screws | 8 | 8 | CAD check only (4 screws, 2 washers each in the spec string) |")
    a("| Printed parts | 68 | 68 | CAD check only (parts.csv qty sum, 49 STL files) |")
    a("| Print filament, slicer estimate | 1361.4 g | 1361.4 g | calc only: SLICE_SUMMARY.md part-row total 1355.5 g plus the freeze prose +5.88 g in that same file. Not weighed |")
    a("| Print time, slicer estimate | 120.6 h | 120.6 h | calc only: 119.9 h plus the freeze prose +0.74 h. Not a timed print |")
    a("| Fastener and STL change | 0 | 0 | CAD check only. Mass change from this pass is 0 |")
    a("| Weighed robot mass | BLOCKER | BLOCKER | not weighed |")
    a("| Builder screws to turn | 268 | 268 | CAD check only (324 fitted minus 56 factory) |")
    a("| Fastening minutes | BLOCKER | BLOCKER | operation count is unchanged, so the time does not change, but the seconds per screw were not re-measured |")
    a("| Full assembly minutes | BLOCKER | BLOCKER | insert time, handling, routing, and tests are BLOCKER in the screws twin |")
    a("")
    a("The 324 fitted screws split the same way FASTENERS.md section 1 does: 205 to buy, 57 from the servo bag, 56 factory, 6 from the ear-servo bag (CAD check only). 205 + 57 + 56 + 6 = 324. Twelve of the 205 still carry a supply string of NEW LINE or NEW LENGTH in the JSON (the 10 button heads and the 2 M2x12 screws). Section 2 of that file counts them on BOM 17j and 17m. The fitted total does not change.")
    a("")
    a("By job (CAD check only), same before and after:")
    a("")
    a("| Job | Screws |")
    a("|---|---|")
    a("| Factory, inside the servo | %d |" % count["roles"]["factory"])
    a("| Horns and shaft screws | %d |" % count["roles"]["horn"])
    a("| Servo case clamps | %d |" % count["roles"]["case"])
    a("| Printed structure and frame | %d |" % count["roles"]["structure"])
    a("| Covers, boards, eyes | %d |" % count["roles"]["cover"])
    a("| Ear servos | %d |" % count["roles"]["ears"])
    a("| Sum | 324 |")
    a("")
    a("Figure: dfa_before_after.png.")
    a("")
    a("## What was checked, and not used")
    a("")
    a("Each idea below is a published pattern or a pattern already drawn in this repo. None of them removes a screw that is still fitted.")
    a("")
    a("Snap fit. The Fictiv cantilever note (opened for this file, https://www.fictiv.com/articles/how-to-design-snap-fit-components) gives strain = 1.5 t Y / (L squared Q), with Q = 1 for a simple case. That is the formula already used for coupon K3 (twin/screws/data/lips.json): arms 0.9 mm by 12 mm, 0.4 mm barb, strain 0.375 percent, service limit 0.535 percent. K3 snaps a 6 mm cable bundle. It is not a cover retainer. Its coupon has not been run (twin/screws/SCREWS_TWIN.md). The same page says a snap should not stay bent in service (creep) and that repeated use needs an S-N curve, which this lab does not have. A new cover snap is not drawn.")
    a("")
    a("Captive nuts. STRUCTURE_TWIN.md already cites the CNC Kitchen comparison of screws, heat-set inserts, and embedded nuts. A nut would replace an insert. The screw stays. Nuts would rise from 0. That is not a smaller fastener count. Nothing is added to the buy list.")
    a("")
    a("Twist-lock. The schedule has no twist-lock row (CAD check only). The lab files do not contain a twist-lock pattern to copy. One is not drawn.")
    a("")
    a("Fewer, larger screws. Horn screws are M3 into the four holes of the servo horn (FASTENERS.md, 2.4 mm of thread, which meets that joint's rule). A larger screw does not fit those holes. The lid and the head plate stay on the uniform set from D42. Not used.")
    a("")
    a("Merged parts. The speaker sits in a cage made by speaker_stand and speaker_interface (twin/assembly/ASSEMBLY_TWIN.md). Joining those two STLs would close the cage. The leg sheets, the foot plates, and the hip-roll motor shells have to open to take a servo. They are not merged.")
    a("")
    a("Horn screws, one size. Each horn keeps four screws. The length and the head are set by the stack, not by a free choice. Counts here are CAD check only.")
    a("")
    a("| Spec | On horns or the D19 sites | All fitted of this spec | Why it stays |")
    a("|---|---|---|---|")
    a("| M3x6 DIN 912 | %d | %d | Leg, hip-roll, and shin horns. Head height 3.0 mm (ISO 4762, cited in sim/mass_budget.py). The other fitted M3x6 screws are structure, frame, and case-adjacent joints, not a second horn size. |" % (count["horn_specs"].get("M3x6 DIN 912 A2", 0), count["specs"]["M3x6 DIN 912 A2"]))
    a("| M3x5 DIN 912 | %d | %d | Neck and head-pitch horns. FASTENERS.md: the short stack engages 2.4 mm, which is the rule, and a longer screw bottoms. |" % (count["horn_specs"].get("M3x5 DIN 912 A2", 0), count["specs"]["M3x5 DIN 912 A2"]))
    a("| M3x6 ISO 7380 button | %d | %d | D19, all 10 sites (idle horns and the two spacer screws F002 and F010). A DIN 912 head hits the hip part. Button head height 1.65 mm max, socket 2 mm nominal (ISO 7380-1 table 1, https://westfieldfasteners.co.uk/Standards/ScrewBolt-SHBtn-M.html, opened for this file). |" % (count["specs"]["M3x6 ISO 7380 A2 button head"], count["specs"]["M3x6 ISO 7380 A2 button head"]))
    a("")
    a("Those three cannot collapse to one screw without a new horn or a collision. Not changed. PR 46 keeps the four M3x6 drive screws on the shin.")
    a("")
    a("Printed clips. Same as the snap row. The only clip geometry in the repo is K3, for a cable, coupon not run.")
    a("")
    a("Living hinge. The Fictiv page opened here describes cantilever, annular, and torsion snaps. It does not give a living-hinge pattern, and it says fatigue needs an S-N curve. No living hinge is added. Battery and shell service stays on the screws already fitted.")
    a("")
    a("Tongue and groove on the body shells is already in the printed parts (D38, screws twin). The screws that remain on those shells are the ones D38 and D42 kept. This pass does not cut them again.")
    a("")
    a("## Tools")
    a("")
    a("Tool-free assembly is not met. One-tool assembly is not met.")
    a("")
    a("Socket sizes, cited:")
    a("")
    a("- M3 DIN 912 uses a 2.5 mm hex (ISO 4762, sim/mass_budget.py, https://www.fasteners.eu/standards/DIN/912/).")
    a("- M2.5 DIN 912 uses a 2.0 mm hex (same source).")
    a("- M3 ISO 7380 uses a 2 mm hex nominal (Westfield table opened above).")
    a("")
    a("That is two hex keys for the screws this design chooses. D36 already adds cross-head drivers for the M2 pan heads. The ear-servo bag screw size is not published (FASTENERS.md, F162 and F163). The driver for that pair is BLOCKER.")
    a("")
    a("## FEA check (PR 43 and PR 46)")
    a("")
    a("No STL in those studies is in the edit list, because the edit list is empty. st_fea.py was not re-run. An unchanged mesh is not a new result. The pitches below are the ones to reuse if a later job does change a part.")
    a("")
    a("PR 43 (twin/structure/TOPOLOGY.md), FEA pass only, room-temperature PLA, voxel pitches: roll 0.9 mm, shin and thigh and neck 0.75 to 0.8 mm, head 1.0 mm, foot and hip 1.1 to 1.3 mm. Walking safety factor, then soft-fall worst, after the kept pads:")
    a("")
    a("| Part | Walk | Soft worst | Soft falls under 1.2 | This pass |")
    a("|---|---|---|---|---|")
    a("| roll_to_pitch | 2.41 | 0.78 | 3 of 11 | STL not changed |")
    a("| shin drive eye | 1.30 | 0.87 | 3 of 11 | STL not changed. Horn screws stay four |")
    a("| thigh sheets | 1.71 | 0.94 | 2 of 11 | STL not changed |")
    a("| neck sheets | 11.85 | 0.99 | 6 of 11 | STL not changed |")
    a("| head_roll_mount | 52.49 | 1.03 | 2 of 11 | STL not changed |")
    a("| foot_top | 3.86 | 2.76 | 0 of 11 | STL not changed |")
    a("| hip roll stage | 16.74 | 2.33 | 0 of 11 | STL not changed |")
    a("")
    a("Those factors are not hardware. Hot PLA strength and the fall contact stiffness stay guesses, as in that file.")
    a("")
    a("PR 46 (twin/structure/shin_eye/SHIN_EYE.md) re-ran the shin at 0.75 mm so it matches the topology walk (stock 0.80, collar 1.30, FEA pass only). The recommendation, not installed in print/, is the recessed web in PA6-CF: walk 2.85, push 2.48, soft worst 1.61, 0 of 9 under 1.2, at 0.75 mm with the drive sheet at the PA6-CF modulus (FEA pass only). Hot tensile and wet tensile are BLOCKER there. This pass does not copy that STL and does not remove F203, F205, F207, or F250 (or the matching four on the other leg).")
    a("")
    a("## CAD edits")
    a("")
    a("None.")
    a("")
    a("No line in print/. No line in altaay_lab/fasteners/fasteners.json. No hole opened or closed. D39 and D42 are unchanged. The shin horn pattern is unchanged.")
    a("")
    a("## Joints")
    a("")
    a("Every fitted screw is in one row. Qty is the fitted count, both sides included when the part name is shared. After equals before on every row.")
    a("")
    a("| Qty | Joint | Spec | Decision |")
    a("|---|---|---|---|")
    for j in count["joints"]:
        name = "%s -> %s (%s)" % (j["part"], j["into"], j["anchor"])
        a("| %d | %s | %s | %s |" % (j["qty"], name.replace("|", "/"), j["spec"].replace("|", "/"), j["why"].replace("|", "/")))
    a("")
    a("## Open items")
    a("")
    a("- Full assembly minutes: BLOCKER. The screws twin lists insert time, part handling, cable routing, labels, and tests as unmeasured. This pass does not invent those minutes.")
    a("- Seconds per screw: BLOCKER as a fresh cite. twin/screws/SCREWS_TWIN.md quotes 8 to 12 s from https://dfma.com/resources/assembly-cost-estimating.asp and says that page was not fetched. It was not opened here either. The builder still turns 268 screws (CAD check only), the same set, so the fastening time does not move.")
    a("- Ear-servo bag screw size, and the driver that fits it: BLOCKER (FASTENERS.md on F162 and F163).")
    a("- Weighed robot mass: BLOCKER.")
    a("- Hot tensile of the printed arms, and of PA6-CF at the knee temperature: BLOCKER, already recorded in TOPOLOGY.md and SHIN_EYE.md. This pass does not treat those safety factors as a bench result.")
    a("")
    text = "\n".join(lines) + "\n"
    for bad, name in (("\u2014", "em dash"), ("\u2013", "en dash"), ("/agent", "local path"), ("/home/", "local path"), ("#43", "hash PR"), ("#46", "hash PR")):
        if bad in text:
            raise SystemExit("forbidden %s" % name)
    if "$" in text:
        raise SystemExit("price character")
    open(path, "w", encoding="utf-8").write(text)


def main():
    count = load()
    os.makedirs(HERE, exist_ok=True)
    # Joint id lists stay in count.json. The note has the qty.
    out = {k: count[k] for k in ("fit", "out", "screw_rows", "inserts_fit", "inserts_out", "insert_rows", "nuts", "washers", "buckets", "roles", "horn_specs", "builder_screws", "specs")}
    out["joints"] = [{k: j[k] for k in ("part", "into", "anchor", "spec", "qty", "ids", "action", "role")} for j in count["joints"]]
    json.dump(out, open(os.path.join(HERE, "count.json"), "w"), indent=1)
    png = os.path.join(HERE, "dfa_before_after.png")
    draw(count, png)
    write_md(count, os.path.join(HERE, "DFA.md"))
    print("fit", count["fit"], "roles", count["roles"], "joints", len(count["joints"]))
    print("png", os.path.getsize(png))


if __name__ == "__main__":
    main()
