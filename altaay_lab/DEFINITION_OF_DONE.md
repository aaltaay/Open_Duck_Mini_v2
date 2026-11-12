# DEFINITION OF DONE

Written 2026-11-11 ET. Ahmed's meaning of done is a finished product: built, checked, and usable at home.
A passing sim is not done. A calc is not done. A CAD check is not done. Those labels mean the work toward
a gate has started. They do not pass the gate.

The duck is not printed, the pack is not welded, and the full order is not placed before gate 0 passes.
Today none of that has been done, and gate 0 has not passed.

One exception, so the checklist can be finished: a characterization coupon that a gate 0 row names may be
bought and made after Ahmed says yes. For the pins that is TEST_PLAN.md 20.1 to 20.4 (a few pins, a scrap
of cloth, a scrap of felt, no whole duck). The coupon is not the product and it is not the one-click bill.
Its only job is to replace a guess in the twin with a measurement.

Each line is Covered or GAP. Covered means a file in this repo already holds that work, and the label on
that work is named. GAP means the pass criterion is not met.

Public sources used for the shape of the later gates, not as a claim that those gates are passed:
47 CFR 15.212 (opened; a radio approval does not by itself approve the host), 49 CFR 173.185 (retrieved;
a lithium cell or battery that is shipped has to be a type shown to meet UN 38.3), and the Raspberry Pi
Zero 2 W product brief (opened; the board's own mark is for the board, and a case and other devices can
change compliance). COMPLIANCE_FIRST_PASS.md has the citations. A systems-engineering handbook was not
opened this session. The gate list is Ahmed's.

## Gate 0. The twin matches the real duck, and the bill can be ordered in one click

The duck is not printed, the pack is not welded, and the full order is not placed before this gate passes.
The coupon exception above is the only buy. The twin and the bill have to describe the same duck, line by
line: the same parts, the same screws, the same wires, the same masses, the same materials. A sim of a
stand-in does not count.

### Mechanical
- Pass: every solid that will be printed or bought is in the twin at the size on its drawing, including
  the nest pins, the felt, the cloth, and the two-step mat edge. Covered for the walking duck and the sit
  in print/ and twin/sit/SIT.md (CAD check only). GAP for the nest: the nest CAD is drawn and not installed
  (twin/dock/nest/cad/NEST_CAD.md).
- Pass: screws follow D42 (a uniform pattern) and D39 (no empty hole). Covered as a CAD pass for the
  walking duck in twin/holes/HOLES_TWIN.md. The nest CAD has its own hole check. It is not in the print
  set. GAP for one matched set.
- Pass: the structure holds the fall loads with the margin the structure twin already uses. Covered as
  FEA on sim loads in twin/structure/STRUCTURE_TWIN.md (sim pass only, FEA pass only). Several leg and
  neck results are under that margin (D26, still open). GAP.
- Pass: a topology pass has removed material that does not carry load, and the twin was re-run after it.
  GAP. No topology study is in the repo. V1_PLAN.md records the ask for an optimized design. That sentence
  is not the study.
- Pass: materials in the twin are the materials that will be bought (PLA, TPU, felt, cloth, pin steel),
  with friction and stiffness from a datasheet or a coupon, not from a guess. GAP. Felt and cloth friction
  are not measured. PARTS_AUDIT.md lists the guesses.

### Thermal
- Pass: the thermal twin includes the charger inside the duck (D61) and stays inside the PLA limit and
  the cell charge window from the opened cell sheet (0 C to 60 C). Covered for the walk without that
  charger, twin/thermal/THERMAL_TWIN.md (sim pass only). GAP for the charger. The 1.9 to 3.2 W figure is
  calc only.

### Electrical
- Pass: the netlist, the power sim, and the electrical twin are the duck that will be built, including
  two nest wires, the charger in the trunk, and the safety gate. Covered for the walking power path in
  sim/POWER_PATH_SIM.md and twin/electrical/ELECTRICAL_TWIN.md (sim pass only, calc only). The netlist
  still has the older dock. GAP for the nest.

### Software
- Pass: the same code that will run on the Pi runs against the twin, including camera-only nest finding,
  the joint limits, and a walk at low and full battery. Covered for the walk policy and the sit limits
  as sim pass only (software/servo_limits.json, twin/sit/SIT.md). GAP for the camera. The nest sim uses
  a pose stand-in, not a camera (D61).

### The bill
- Pass: one order, exact part numbers, quantities, and live stock, buys every part and nothing the design
  no longer uses. GAP. PARTS_AUDIT.md: nothing is orderable today by that rule. The Pi and the P45B were
  out of stock at the named sellers. The nest parts are not on the bill.

## Gate 1. Every part checked against its datasheet

### Mechanical
- Pass: each screw, insert, bearing, pin, cloth, and felt has a datasheet or a standard, and the drawing
  uses a number from that document. GAP. Fastener standards were not opened this session. The pin catalog
  was opened and does not show the 2.3 mm tip the CAD assumed (PARTS_AUDIT.md, MISMATCH).

### Thermal
- Pass: servo operating temperature, cell charge temperature, and PLA limits used by the thermal twin
  match the documents. GAP. The opened STS3215 sheet says -20 C to 60 C. The twin's 70 C cut is not on
  that sheet. The cell sheet's 0 C to 60 C charge window is now a real document. The twin has not been
  updated to cite that sheet revision.

### Electrical
- Pass: servo torque, speed, current, and backlash; cell capacity and resistance; charger voltage, current,
  timer, and dropout; radio and camera identity. All match a datasheet. Covered in part: STS3215 stall
  19.5 kg.cm and 52 RPM at 7.4 V, backlash at most 0.5 deg (sheet opened). The twin's stall is stronger
  than that sheet (MISMATCH). P45B capacity, 45 A, and 15 mOhm DC match the opened sheet. The sheet maximum
  (21.55 mm by 70.15 mm) is the top of the tolerance the bay already used, and the sleeved pack is 22.2 by
  43.7 by 71.0 mm (CAD check only, twin/battery/bay_edit.py), so the cavity does not need a resize. Charger
  datasheet not opened (BLOCKER). Pi and camera briefs match the boards
  named on the bill (VERIFIED). GAP overall.

### Software
- Pass: joint limits in software/servo_limits.json sit inside the servo's travel and inside the printed
  stops. Covered as a CAD and software file (twin/sit/SIT.md). The servo sheet says the sensor can turn
  a full turn and names no mechanical stop. The printed stops are the limit. GAP until gate 2 measures
  them on a real servo.

## Gate 2. Bench tests

The list is TEST_PLAN.md. A step passes only when the number is measured on the part. Sim predictions in
that file are not the pass.

### Mechanical
- Pass: cables, fits, the sit, the knee loop to 150 deg with no charge wires in the leg (D61), and the
  pin-on-cloth coupon (contact, snag, hair, dirt). The plan is TEST_PLAN.md sections 1, 19, and 20.1 to
  20.4. GAP. Not run.

### Thermal
- Pass: the servo hold (TEST_PLAN.md 7.3), the switch heat (4.2), and the in-duck charger (20.8). GAP.
  Not run. 7.3 exists because the servo sheet has no duty curve the twin can trust.

### Electrical
- Pass: pack, BMS, regulator, hop resistance, one servo, the walking voltage log, and the two-wire gate
  on the bench (TEST_PLAN.md 3 to 9 and 20.5). GAP. Not run.

### Software
- Pass: angle limits read back from the servos, the walk log, and the battery cutoff behave as the files
  say (TEST_PLAN.md 8, 9, 11, 19.1). GAP. Bench scripts have been run on a simulated bus only
  (software/SOFTWARE.md). That is not this gate.

## Gate 3. The duck docks itself, with the camera, at low and full battery

### Mechanical
- Pass: ten sits at a low pack and ten at a full pack, on the real mat, no fall, no part touching the
  wall or the rim, all four pins connected. TEST_PLAN.md 20.6 and 20.7. GAP. The sims fell on the mat
  edge (sim pass only). Those falls are a warning, not a result for this gate.

### Thermal
- Pass: after those docks the cells and the nearest PLA are still inside the gate 5 limits. GAP.

### Electrical
- Pass: charge current actually flows at both battery levels, and the mat returns to the probe state
  when the duck stands. GAP.

### Software
- Pass: the camera finds the nest with no tags and no pose handed in by the sim, from about 1 m and
  about 2 m, lights on and lights dim (TEST_PLAN.md 20.9). GAP. Not written against a real camera.

## Gate 4. Wear

### Mechanical
- Pass: pins on cloth, the cloth itself, the knee-loop wires, and the screws that carry repeated sit
  loads survive a cycle count written down before the test starts. The pin catalog's 500,000 cycles are
  in a socket, not on cloth (catalog opened). TEST_PLAN.md 19.7 is the knee wire. TEST_PLAN.md 20.4 is
  only a 500-cycle first look. GAP for a life number.

### Thermal
- Pass: a worn pin and a worn cloth still charge without a hot spot at the contact. GAP.

### Electrical
- Pass: contact resistance after the wear cycles stays inside the TEST_PLAN.md 20.1 limit. GAP.

### Software
- Pass: the dock program still completes after the worn hardware is refitted, with no change to the
  limits. GAP.

## Gate 5. Safety of the charger, the pack, and the mat

This gate is measured. COMPLIANCE_FIRST_PASS.md is the reason the tests exist. It is not the pass.

### Mechanical
- Pass: the pins cannot be pulled out by hand, and a coin cannot bridge plus and minus. TEST_PLAN.md
  20.3. GAP.

### Thermal
- Pass: during a full charge with the charger in the duck, cells stay at 0 C to 45 C, the charger case
  stays under 70 C, and the nearest PLA stays under 45 C (TEST_PLAN.md 20.8). The cell sheet allows
  charge up to 60 C. The bench limit is tighter. GAP.

### Electrical
- Pass: the two-wire gate refuses water, metal, and a skin stand-in, and drops power when the duck
  leaves (TEST_PLAN.md 20.5). The pack used for any shipment has a UN 38.3 test summary for that pack.
  49 CFR 173.185 is the US shipping rule retrieved this session. GAP. The pack is not built and has no
  summary.

### Software
- Pass: the duck will not stand on a live mat. It turns the signature off and waits until the mat is
  back at the probe, then it stands. That behavior is described in the stripe study (calc only) and is
  not code. GAP.

## Gate 6. Certification basics

COMPLIANCE_FIRST_PASS.md is the map. Passing this gate means the paperwork and the lab tests it names,
not the existence of that file.

### Mechanical
- Pass: the outside of the body can carry the radio label 47 CFR 15.212 requires when the module's own
  id is hidden, and the antenna is still the one on the Pi. GAP. The FCC id was not read from the grant.

### Thermal
- Pass: a lab report, if the chosen standard asks for one, covers charge temperature and the adapter.
  Which UL or IEC document applies was not opened. Uncertain. GAP.

### Electrical
- Pass: the finished duck has the host radio check and the unintentional-radiator check, and the pack
  has its transport summary, before any sale or shipment. GAP.

### Software
- Pass: the camera can be shown to a reviewer as on only when a person can tell, with nest finding that
  does not keep a face library. GAP. See gate 7.

## Gate 7. Days of home use

A finished product lives in a home, gets up when it falls, and does not surprise the people there.

### Mechanical
- Pass: several days of real walking, sitting, and docking, including falls onto the floor the home
  actually has, with no broken screw, no cracked printed part, and a successful get-up through the sit
  (D60). The get-up exists only as sim pass only (twin/sit/getup/VIA_SIT_EVAL.md). GAP.

### Thermal
- Pass: over those days the cells, the servos, and the PLA stay inside the limits already named, with
  the log kept. GAP.

### Electrical
- Pass: the duck returns to the nest on its own as the pack falls, charges, and leaves again, without a
  person placing it. GAP.

### Software
- Pass: fall recovery runs on the real robot. Camera privacy is in the software: a cue when the camera
  is active, no stored face library, no upload by default. COMPLIANCE_FIRST_PASS.md states why.
  GAP. Not written.

## Gate 8. Someone else can build a second duck from the documents

### Mechanical
- Pass: print files, the fastener schedule, and an assembly guide match the duck that passed gates 2
  to 7. A second unit built from those documents, by someone who did not design it, passes the same
  tests. Covered in part for the first duck's screws and build order (twin/assembly/BUILD_ORDER.md,
  fasteners/). GAP for the nest, and GAP for a second unit. Nothing has been built.

### Thermal
- Pass: the second unit's heat log matches the first unit's passing log within a band written down
  before the build. GAP.

### Electrical
- Pass: the bill used for the second unit is the final bill (gate 0's bill, after every later change),
  and the second unit's electrical tests match. GAP. PARTS_AUDIT.md is the list of what that bill is
  missing now.

### Software
- Pass: a user guide says how to charge, how to tell that the camera is on, and how the duck gets up.
  The second unit runs that guide without a developer in the room. GAP. No user guide exists.

## Where the repo stands

Gates 0 through 8 are open. The twins that exist (structure, heat, power, electrical, sit, nest sim)
are the start of gates 0 and 1 only, and only as sim pass only, calc only, or CAD check only. The
bench plan for gate 2 is TEST_PLAN.md. The parts gap for gates 0 and 1 is PARTS_AUDIT.md. The safety
and certification map for gates 5 and 6 is COMPLIANCE_FIRST_PASS.md. None of those files is a pass.
