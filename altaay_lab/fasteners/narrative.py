"""Narrative parts of FASTENERS.md (findings, servo hardware, rules, proposed edits), filled from the data."""
from collections import Counter


def narrative(D, screws, inserts, fitted, hits, d18, bom_rows, SRC):
    byid = {r["id"]: r for r in screws}
    F = []          # (severity, text)
    cnt = Counter(r["spec"] for r in fitted)
    # --- hip pitch idle horn screws vs roll_to_pitch (screw-specific sweep hits on horn(passive) of the hip pitch servo)
    hp = [h for h in hits if h.get("cls") in ("screw", "static overlap") and "roll_to_pitch" in h["against"]
          and byid[h["id"]].get("anchor") == "horn(passive)" and byid[h["id"]].get("servo", "").endswith("hip_pitch")]
    hp_ids = sorted({h["id"] for h in hp})
    if hp_ids:
        worst = min(h["worst_mm"] for h in hp)
        low = [byid[i]["sweep"].get("with_iso7380_head", {}) for i in hp_ids]
        lw = min((x.get("clearance_mm", 99) for x in low if "roll_to_pitch" in x.get("against", "")), default=None)
        F.append(("build-blocking (NEW)", "The 4 M3 screws that hold each thigh (knee_to_ankle_right_sheet) to the idle horn of the hip "
                  "pitch servo (%s) sit in 6.5 mm recesses only 0.8 mm deep, and the roll_to_pitch wall is 1.83 mm above the recess "
                  "floor. A DIN 912 head (3.0 mm tall) overlaps roll_to_pitch by up to %.2f mm at every hip pitch angle, both legs "
                  "(sweep, static and swept). With an ISO 7380 button head (k max 1.65 mm %s) the worst clearance over the same sweep "
                  "against roll_to_pitch is %+.2f mm (under the 0.3 mm margin). Fix: M3x6 ISO 7380 A2 button heads at these %d "
                  "positions (new BOM line, set in fasteners.json) and a rub check on the first leg; if they touch, relieve "
                  "roll_to_pitch locally (same path as D18)." % (
                      ", ".join(hp_ids), -worst, SRC["iso7380"], lw if lw is not None else float("nan"), len(hp_ids))))
    # --- other screw-specific hits
    other = [h for h in hits if h.get("cls") == "screw" and not (h["id"] in hp_ids and "roll_to_pitch" in h["against"])
             and not any(h["id"] == r["id"] for r, _ in d18)]
    for h in sorted(other, key=lambda h: h["worst_mm"]):
        r = byid[h["id"]]
        low = (r.get("sweep") or {}).get("with_iso7380_head")
        F.append(("note (NEW)",
                  "%s, now %s (%s to %s, %s): with a DIN 912 head it overlaps %s by up to %.2f mm from %s %s deg on (worst at "
                  "%s, %d sweep steps); the bare parts do not touch there. %s" % (
                      h["id"], r["spec"], r.get("part"), r.get("into"), r["link"], h["against"], -h["worst_mm"], h["where"],
                      h.get("onset"), h["at"], h["n_steps"],
                      ("With an ISO 7380 head: %+.2f mm against %s, so the button head is the fix." % (low["clearance_mm"], low["against"]))
                      if low and low["clearance_mm"] > 0 else
                      ("An ISO 7380 head still overlaps (%+.2f mm against %s), so the bare thigh passes close to it there: keep "
                       "this joint under %s deg (a joint range point for the sim and controller owners)." % (
                           low["clearance_mm"], low["against"], abs(h.get("onset") or 0)))
                      if low else "Keep the joint short of that angle or check on the first leg.")))
    # --- static overlaps not explained elsewhere
    st = [h for h in hits if h.get("cls") == "static overlap" and h["id"] not in hp_ids and not any(h["id"] == r["id"] for r, _ in d18)]
    fac = [h for h in st if byid[h["id"]]["source"] == "servo_case"]
    if fac:
        F.append(("note (model limit)", "%d factory case screw heads at the far end of the servo top face overlap the bracket above "
                  "by %.2f mm with the 4.0 x 1.6 mm stand-in head; every bracket leaves a %.2f mm relief there, so the real head is at most "
                  "that tall or sits lower. Not a fault; measure the head on the first servo (test order 1)." % (
                      len({h["id"] for h in fac}), -min(h["worst_mm"] for h in fac), 1.6 + min(h["worst_mm"] for h in fac))))
    for h in [h for h in st if byid[h["id"]]["source"] != "servo_case"]:
        r = byid[h["id"]]
        if h["against"] == "bms":
            F.append(("note", "%s %s (USB-C charger to body_back): its head touches the CAD bms.stl body by %.2f mm. The real BMS is the "
                      "Tenergy 32175 (34 x 16 x 4.5 mm, D10), seated by audit/placements.json; keep 0.5 mm between the board and this "
                      "screw head when it is wrapped and placed." % (r["id"], r["spec"], -h["worst_mm"])))
        elif h["against"] == "antenna":
            F.append(("note", "%s %s (%s): the antenna rod (antenna.stl, in the 1.8 mm holes of the holder, no BOM line) passes "
                      "%.2f mm above the holder face at this screw, less than the 1.6 mm stand-in head. Fit the horn screw before the "
                      "rod and check the rod clears the real head (SG90 bag screw size not published)." % (
                          r["id"], r["spec"], r.get("part"), 1.6 + h["worst_mm"])))
        else:
            F.append(("note", "%s %s: static overlap %.2f mm with %s at the zero pose." % (r["id"], r["spec"], -h["worst_mm"], h["against"])))
    # --- recess fit
    rec = Counter()
    for r in fitted:
        rc = r.get("recess_check") or {}
        if rc.get("status") in ("INTERFERENCE", "TIGHT"):
            rec[(r["size"], rc["recess"], rc["status"])] += 1
    m3_55 = sum(v for (s, d, st_), v in rec.items() if s == "M3" and abs(d - 5.5) < 0.01)
    if m3_55:
        parts = Counter((r["part"], r.get("into")) for r in fitted if (r.get("recess_check") or {}).get("recess") == 5.5 and r["size"] == "M3")
        F.append(("build-blocking (NEW)", "%d M3 DIN 912 heads sit in 5.5 mm recesses (%s). ISO 4762 allows dk 5.50 for a smooth head and "
                  "5.68 for a knurled one %s, and FDM holes print undersize, so the head will not drop in; it would then sit on the "
                  "face and lose the recess depth of engagement. Fix: open these recesses to 6.0 mm with a hand drill after printing "
                  "(or print with hole compensation); check on the coupon session." % (
                      m3_55, ", ".join("%s to %s %d" % (a, b, v) for (a, b), v in parts.items()), SRC["din912"].split(" (")[0])))
    m2_40 = sum(v for (s, d, st_), v in rec.items() if s == "M2" and abs(d - 4.0) < 0.01)
    if m2_40:
        F.append(("note", "%d servo-bag M2 heads sit in 4.0 mm recesses (trunk_top, head_yaw_to_roll, roll_to_pitch). The bag screw head is "
                  "not published; at 4.0 mm it has zero clearance. Measure the bag screw (B2, B21) and open the recesses to 4.5 mm "
                  "if the head is over 3.8 mm." % m2_40))
    # --- clearance holes
    tight = [r for r in fitted if (r.get("clearance") or {}).get("status") in ("TIGHT", "INTERFERENCE")]
    if tight:
        F.append(("note", "battery_pack_lid: %d clearance holes are 2.5 mm for M2.5 screws (zero clearance in a printed part); "
                  "drill them to 2.7 mm (ISO 273 fine series value, not sourced here) so the lid clamps instead of threading." % len(tight)))
    # --- eyes
    eye = [r for r in fitted if r.get("anchor") == "plastic pilot (eye)"]
    if eye:
        F.append(("build-blocking (NEW)", "Eye screws: the eye pilots are blind (3.0 mm deep with a 1.5 mm front skin, ray cast), not "
                  "open as MOUNTING.md says. M2.5x8 reaches the pilot floor exactly; M2.5x6 leaves 1.0 mm of thread. Fit M2.5x8 with "
                  "two 0.3 mm M2.5 washers under each head (16 washers, BOM 17l, D21 note): 2.4 mm of thread, 0.6 mm short of the floor. "
                  "Still below the 2 x d rule (pilot depth), light parts."))
    # --- speaker interface
    spk = [r for r in fitted if r.get("part") == "speaker_interface"]
    if spk:
        F.append(("note (NEW)", "speaker_interface has 4 clearance holes 2.7 mm on a 32 x 32 mm square over the 4 side pilots 2.12 mm of "
                  "speaker_stand (same square). HARDWARE_AUDIT B8 says there is no screw. 4 x M2.5x5 DIN 912 (new length) fit: "
                  "2.7 to 2.9 mm of thread, 0.3 mm short of the pilot floor. The stand pilots are drilled 20.7 deg off the hole axis "
                  "(the face is tilted, the holes were drilled along y), so the screws enter at an angle; check on the head print."))
    # --- SG90 tabs
    sg = [r for r in fitted if r["source"] == "sg90_tab"]
    if sg:
        F.append(("note (NEW)", "SG90 tab pilots in head.stl (1.55 x 3.8 mm) are drilled along y while the SG90 and its tab holes follow "
                  "the antenna axis, 20.7 deg off (both the URDF head and print/head.stl). The 4 tab screws (SG90 bag) enter the pilots "
                  "at 20.7 deg. Spacing matches (B5), direction does not. Check with the first head; fallback: hot glue, or drill the "
                  "pilot along the tab axis."))
    # --- camera
    cam = [r for r in fitted if r["source"] == "camera"]
    if cam:
        r = cam[0]
        F.append(("note (B9 open)", "Camera: the 4 head pilots are 3.2 mm deep. With an assumed 1.0 mm PCB, M2x4 ends %.2f mm short of "
                  "the floor (below the 0.3 mm margin) with 3.0 mm of thread; the PCB thickness is not published, measure it (test "
                  "order 8) before choosing M2x4 or a shorter screw." % r.get("tip_gap", 0)))
    # --- lengths vs BOM choices
    F.append(("note", "Engagement below the cited rule where the CAD pilot or bore is too shallow for any stock length: "
              "%s. Biggest gaps: leg_spacer inserts (M3x6, 3.85 to 4.15 mm of 4.5; M3x8 would hit the 2.0 mm hole shoulder), "
              "foot_top inserts (M3x10, 4.0 mm; M3x12 bottoms), head_roll_mount inserts (M3x6, 4.1 mm; M3x8 leaves 0.24 mm to the "
              "floor), electronics M2.5 screws in 5 mm pilots (3.0 to 4.6 mm of 5.0), servo case pilots (3.0 mm of 3.8 at 48 "
              "screws; the pilots are 4.0 and 4.8 mm deep in the servo model)." % ", ".join(
                  "%s %d" % kv for kv in Counter(r.get("anchor") for r in fitted if (r.get("len_status") or "").startswith("BELOW")).most_common())))
    F.append(("note", "Upstream guide lengths differ: trunk_top to trunk_bottom M3x10 in the guide gives 2.9 mm of insert thread, the rule "
              "gives M3x12 (4.9 mm, 2.0 mm to the floor); foot_bottom_tpu to foot_bottom_pla M3x6 in the guide gives 3.0 mm, the rule "
              "gives M3x8 (5.0 mm) " + SRC["guide"].split(" (")[0] + "."))
    F.append(("note", "Print STLs differ from the URDF meshes the older audit used: print/head.stl (up to 5.0 mm, adds 127 grille holes, "
              "drops the 4 pilots under the head board.stl copy) and left/right_roll_to_pitch.stl (the 2 bottom holes moved 1.18 mm onto "
              "the servo pilots, which clears B4: the 4 NONE rows of screws2.json now land on case pilots). audit/screws2.json, "
              "sites.json and MOUNTING.md row 'Second board.stl copy' are based on the older meshes."))
    F.append(("note", "The 6 NONE anchors of audit/screws2.json are resolved. 4 in left/right_roll_to_pitch: with the print/ STLs the "
              "2 bottom holes per side land on the hip pitch servo's bottom case pilots (M2x6 servo bag screws, window 3.0 to 7.9 mm, "
              "2.9 to 3.0 mm of thread, below the 3.8 mm rule by pilot depth). 2 in the antenna holders: the hole is on the antenna "
              "joint axis (0.04 mm); the SG90 horn screw goes from the holder's outer face into the SG90 output shaft (the 5.05 mm "
              "recess is the spline pocket); size not published, test order 6. No BLOCKER left from them."))
    F.append(("note", "HARDWARE_AUDIT B7 basis is wrong: the head board.stl copy does not share the Pi holes (Pi 58 x 23 mm on the left "
              "side, board 28 x 37 mm on the right). The conclusion holds for another reason: print/head.stl has no pilots under it."))
    F.append(("note", "Stacked rows in audit/screws2.json: 4 leg screws were counted twice (knee_to_ankle sheet and leg cover on the "
              "same insert: one long screw from the cover), so the insert screws are 58, one per insert, matching BOM line 16."))
    # servo bag text
    servo = [
        "Seeed part list for the C001 servo: servo x1, servo horn x2, screw x18, JST wire x1 " + SRC["seeed"] + ".",
        "Feetech datasheet: rocker (horn) screw M3X6 (item 6-13); drawing callouts 8-PA2.0 self-tapping (the 8 mounting holes), "
        "M3X6 machine screw at the output, PA3.0X5 self-tapping at the idle boss; packing photo shows 18 screws: 8 small pointed "
        "pan heads, 7 flat-end flanged heads, 2 flat-end button heads, 1 pointed large washer head (count from the photo; sizes of "
        "the 7 + 2 machine screws not printed, UNVERIFIED) " + SRC["feetech_ds"] + ".",
        "LeRobot SO-101 guide (same servo): M3x6 on the top horn, no screw on the bottom (idle) horn, M2x6 'smallest screws' into "
        "the case, M3x6 printed part to horn " + SRC["so101"] + ". Used here: the bag M2 pointed screws are taken as M2x6 "
        "(UNVERIFIED for this bag, B2).",
        "Used from the bags: %d x M2x6 into case pilots, %d horn centre screws, %d PA3.0x5 idle screws (only where nothing holds "
        "the idle horn: both hip yaws and head roll); the other %d idle screws stay in the bag. Bags supply 8 pointed M2 per servo "
        "(112 in all). Case screws: %d (4 per servo, factory fitted, do not remove)." % (
            cnt.get("M2x6 self-tapping pan head", 0), cnt.get("M3x6 machine screw (Feetech rocker screw)", 0),
            cnt.get("PA3.0x5 self-tapping, washer head (Feetech idle screw)", 0),
            sum(1 for r in screws if r.get("status") == "NOT FITTED"), cnt.get("PA2.0 self-tapping (factory)", 0)),
        "SG90 bags: 2 tab screws per servo and 1 horn screw per antenna holder (6 in all); sizes not published " + SRC["sg90"] + ".",
    ]
    rules = [
        "Brass insert (CNC Kitchen M3 x 5.7): thread engaged >= 1.5 x d = 4.5 mm, capped at the 5.7 mm insert " + SRC["insert_rule"] + "; " + SRC["insert"] + ".",
        "M2.5 and M2 self-tapping into printed PLA pilots: screw-in depth >= 2 x d (5.0 and 4.0 mm) " + SRC["pla_rule"] + ".",
        "M2 self-tapping into the STS3215 case: >= 1.9 x d = 3.8 mm " + SRC["pa_rule"] + ".",
        "M3 into the metal servo horns: engage the full horn thread (2.4 mm drive, 2.2 mm idle, CAD [L]) with the tip clear of the "
        "case; 2 x d for aluminium is not reachable by design " + SRC["alu_rule"] + ".",
        "No bottoming: the tip stays 0.3 mm short of the first solid surface found by 9 rays down the screw core from the head seat "
        "(lab margin [L]). Shortest stock length that meets the rule; if none, the longest that does not bottom (BELOW RULE).",
        "Head sizes: DIN 912 " + SRC["din912"] + "; ISO 7380 " + SRC["iso7380"] + "; servo bag and SG90 screws use the D18 stand-in "
        "4.0 x 1.6 mm " + SRC["d18"] + "; horn centre screw ISO 7045 M3 pan head stand-in 5.6 x 2.4 mm (UNVERIFIED).",
        "Clearance: hole minus screw diameter, printed holes below 0.15 mm margin are TIGHT [L]; recess minus head dk (DIN 912 "
        "knurled max): below 0.3 mm TIGHT, below 0 INTERFERENCE [L].",
    ]
    edits = []
    for b in bom_rows:
        if not b["ok"]:
            if b["line"] == "new":
                edits.append("BOM.md: add lines for %s (counts from fasteners.json; supplier part numbers UNVERIFIED: boltdepot.com refuses curl)." % b["specs"])
            else:
                edits.append("BOM.md line %s (%s): Need %s -> %d (%s); raise Buy to Need plus 10 to 20 %%." % (
                    b["line"], b["item"], b["bom_need"], b["count"], b["specs"]))
    edits += [
        "MOUNTING.md row 'Eyes': replace 'pilot 3.0 mm long, open at the far end' and 'tip ends flush with the eye front face' with "
        "'blind pilot 3.0 mm with a 1.5 mm front skin (ray cast, print/left_eye.stl, right_eye.stl); M2.5x8 plus two 0.3 mm washers: "
        "2.4 mm engaged, 0.6 mm to the floor (fasteners/FASTENERS.md)'.",
        "MOUNTING.md row 'Second board.stl copy': replace 'same 4 holes as the Pi Zero 2 W (58 x 23 mm)' with '4 holes on 28 x 37 mm, "
        "right side of the head; print/head.stl has no pilots under them (the URDF head mesh did), so nothing is fitted there'.",
        "MOUNTING.md row 'Speaker': add 'speaker_interface screws to the 4 side pilots of speaker_stand: 4 x M2.5x5 (fasteners/)'.",
        "HARDWARE_AUDIT.md B8: replace 'speaker_interface has no clip or screw' with 'speaker_interface has 4 holes 2.7 mm that match "
        "4 pilots 2.12 mm in speaker_stand (32 x 32 mm); the pilots are 20.7 deg off the hole axis'.",
        "HARDWARE_AUDIT.md section 1: replace the screw totals with the fasteners/ counts (section 2 here) and add the hip pitch idle "
        "horn button heads, the eye washers and the 6.0 mm recess drilling step.",
        "DECISIONS.md: a new decision is needed for the hip pitch idle horn screws (ISO 7380 button heads, or relieve roll_to_pitch).",
        "print/PRINT_PLAN.md coupon list: add a 5.5 mm recess and a 4.0 mm recess (from head_pitch_to_yaw and trunk_top) to test "
        "head fit, and the eye pilot depth on the left_eye test print.",
        "Open BLOCKERs kept: B2 (bag split by size), B9 (camera PCB thickness), B21 (bag M2 head size vs 4.0 mm recesses), SG90 "
        "screw sizes (test order 6). New: hip pitch idle horn heads (decision needed), 5.5 mm recesses (drill step or coupon).",
    ]
    return F, servo, rules, edits
