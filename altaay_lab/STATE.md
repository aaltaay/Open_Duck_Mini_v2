# STATE

Last updated: 2026-11-02 about 5:40 AM ET (America/New_York) by agent INT, the integration pass after the PRT, PWR, SW and CAB jobs (branch claude/preprint-fixes). Each job has its own entry in history/.

Phase: at the edge of printing. The coupon print is next and waits for Ahmed's OK. Nothing bought, nothing printed.

## Done (2026-11-01 evening into 2026-11-02)
- Every-part BOM (BOM_FULL.md: 196 rows, 798 pieces, 0 needing action) and the cable-by-cable harness build sheet (HARNESS_BUILD.md).
- Mass budget: the build is 2.65 kg (2.77 kg before D22), 26 % over the trained 2.107 kg; the stock policy still walks it on flat ground, slower (sim pass only; the walks ran at 2.77 and 2.64 kg).
- Sourcing pass: missing purchase lines and test equipment TE1 to TE4 (SOURCING_2026-11-02.md, BOM.md).
- Connectors, splices, solder joints and small parts in the 3D view (viewer/scene_extras.json, blueprint/).
- Fastener schedule: 342 screws to fit, 221 to buy, 58 inserts, 16 washers, two 0.3 mm under each eye screw (fasteners/; D19 to D21 and the D21 notes).
- Pi setup from a blank SD card, and bench scripts tested on a simulated servo bus (software/, bench/).
- Servo upgrade options in case the TO1 heat test fails (SERVO_UPGRADE_OPTIONS.md).
- Clean wiring sheets, one subsystem per sheet (wiring/sheets/).
- Verification matrix of every check that needs no robot (VERIFICATION.md, verify/).
- Every cable routed in 3D with seats, ties and joint loops (cables3d/).
- Light print profile: 128 g lighter, gated by light coupons in S1 (print/MASS_STUDY.md; D22).
- Power fix: second feeds SP4 and SP5 into both ankles, 3S pack held (sim/POWER_FIX.md; D23).
- Power path as wired is the checked case now (sim/POWER_PATH_SIM.md 'As built'; VERIFICATION.md E6, E6b, C7; sim pass only): D15 plus the D23 feeds with the netlist lengths. Nominal pack, our 2.65 kg build: ankles under 6 V 6.2 % of the walk (typical corner, gate 10 %) and 21.4 % (high-side); the knees and the head roll are now the lowest servos (right knee 9.6 %, typical); no servo under 4.5 V. Pololu 2815 at 99 % of its 6 A point (TEST_PLAN 4.2 heat check).
- Netlist final pass and final docs pass (agents NL1 and NL2, 12:44 and 1:17 AM ET).
- Eye screw stack coupon (agent PRT): coupon T1 clamps the real 5.6 mm stack, two 0.3 mm washers (BOM 17l) on the printed bulb T1b and head wall T1w (D21 note). S1 is now 11 coupons, 41.2 g PLA, 4.14 h. Every heat shrink sleeve is counted (34, by the BOM_FULL rule) and drawn; the 16 eye washers are drawn; C4 checks the kit counts per size.
- Walking voltage log on its own timer (agent SW): bench/power_log.py --walk reads every servo at a random time in each 27 ms slot, only inside the walk loop's own sleep, so no read delays a control write, and counts time under 6 V by phase of the 20 ms cycle for every servo (TEST_PLAN 9). 63 bench tests pass on the simulated bus.
- Cable retention, D25 (agent CAB): 75 tie points: 32 MB3A mounts (BOM 34), 23 Panduit ABM1M-AT-C mounts (new BOM 34b), 6 stock holes or slots, 3 drilled tie-hole pairs (print/PRINT_PLAN.md After printing step 5), 2 ties to an anchored neighbour cable and 9 bundle ties checked at the TEST_PLAN 1.4 test fit. All 43 joint loops meet 3 x OD in CAD; the made multi-wire cables are twisted; C3 passes.
- Integration pass (agent INT): the four jobs' texts in DECISIONS.md, TEST_PLAN.md, HARDWARE_AUDIT.md, BOM.md, print/PRINT_PLAN.md and the scripts; test order line TO17; scene extras, viewer data and BOM_FULL regenerated; the full verification run.

## Decisions
D1 to D25 are in DECISIONS.md, all decided (D14 superseded by D15). Tonight: D19 button heads at the hip pitch, D20 drill the neck recesses, D21 eye screw washers, D22 light print profile, D23 ankle feeds with the 3S pack held, D24 drill the projector lead hole, D25 cable retention, joint loops, twist and the camera cable. Lead decisions under Ahmed's delegation: L1, TEST_PLAN 9 times every servo, none under 6.0 V for more than 10 % of the walk at a nominal pack (D23 note); L2, the BelMetric lines 17j to 17l join the test order as one order, TO17, so coupon T1 has its washers (D21 note).

## Numbers now
- Print package (print/PRINT_PLAN.md, PrusaSlicer 2.7.2 estimates, D22 profile): coupon session S1 41.2 g PLA and S2 17.6 g TPU; the full print on a 220 bed 18 jobs, 1347.8 g PLA, 17.6 g TPU, 118.6 h; with the coupons 1389.0 g PLA, 35.1 g TPU, 125.0 h.
- Mass: 2.65 kg by sim/MASS_BUDGET.md (not weighed).
- Fasteners: 342 screws to fit, 221 to buy, 58 inserts, 16 washers. Heat shrink: 34 sleeves.
- Tie points (D25): 75, as listed above.
- BOM.md, item prices without shipping: build total $1,018.29, with the expression parts $1,100.69, with tools $1,350.75; test order $231.50 (17 lines).
- Power path as built (sim pass only): see the line above; the TEST_PLAN 5 hop gate stays 40 mOhm, and the sim holds every servo under 10 % only to about 28 mOhm (TEST_PLAN 5 note, E6b).

## Blockers and checks
- Blockers: 22 of 35 cleared or decided, 2 waiting on the parts check, 5 settled by the coupon test prints, 6 assembly or bench checks. None blocks the coupon print (HARDWARE_AUDIT.md section 6).
- Verification (VERIFICATION.md, full run 5:22 to 5:35 AM ET): 22 checks, 20 PASS, 2 FAIL, 0 NOT RUN (2 FAIL and 20 WARN findings). Both FAILs are known and need an owner, not a doc fix. E6b: the TEST_PLAN 5 hop gate stays 40 mOhm (L1), but in sim every servo stays under 10 % only to about 28 mOhm (right knee 13.4 % at 40 mOhm, our build). C8: the 15 N pushes walk of today's model (2.6528 kg) tracks 0.618 of the command against 0.63 in print/MASS_STUDY.md variant (c), just past the check's 0.011 (0 falls in 36 runs). E8: 63 bench tests pass; C3 passes; C9 finds 0 disagreements. Sim and test pass only; nothing has run on real parts.

## Open questions for Ahmed (one at a time, most important first)
1. OK to start the coupon print session? S1: 11 coupons, 41.2 g PLA, 4.14 h. S2: one TPU sole, 17.6 g, 2.19 h (print/PRINT_PLAN.md; lab rule 4).
2. OK to buy the test order (BOM.md "Needs test order", 17 lines, $231.50)? (lab rule 7)
3. Which printer will print the duck? The package needs a bed of at least 220 x 220 mm.

## Next
1. Coupon session; results into history/.
2. Test order: TEST_PLAN.md sections 1 to 7 (cables, battery and BMS, BEC dropout, Pololu 2815 heat, 5 V regulator, one servo with register 85, firmware and the thermal hold, Kelvin hop).
3. First leg print and its checks (D18, D19, the B33 foot_side fit), then the other plates: the full print on a 220 bed is 18 jobs, 1347.8 g PLA, 17.6 g TPU, 118.6 h (with the coupons 1389.0 g PLA, 125.0 h). After printing, the drill steps: the D20 recesses, the D24 projector hole and the 3 D25 tie-hole pairs (print/PRINT_PLAN.md). Then the freeze tag.
4. Harness build and the test fit: TEST_PLAN 1.3 (sleeves, twist), 1.4 (loops and the 75 tie points), 1.5 (ankle plugs).
5. Staged power-up with the hip yaw and head yaw limits (TEST_PLAN 8.2a, 8.2b), then the walking voltage log (sections 8 to 12). The log decides the 3S pack (D23).
6. Later lab step: self-docking and get-up after falls, in sim first.

## Open for other owners (not blockers)
- sim/MASS_BUDGET.md says 2651.9 g; sim/mass_budget.py on today's netlist gives 2652.8 g (wires 121.8 g: +0.9 g from the D25 cut changes). A re-run and the walk doc that C8 compares with belong to the sim owner (C8 FAIL). Both round to 2.65 kg.
- sim/POWER_PATH_SIM.md 'As built' ran on the netlist of 2:05 AM ET; with the D25 cuts (SP4 and SP5 +10 mm) the our-build numbers move a little in this run: ankles 6.4 % (doc 6.2 %), right knee 9.8 % (9.6 %) under 6 V, typical corner; Pololu 2815 RMS 5.93 A (5.92 A). A re-run of the doc belongs to the power sim owner.
- sim/MASS_BUDGET.md counts 1 g of cable ties ("a few small cable ties", UNVERIFIED); the 75 ties and 55 stick-on mounts of D25 are not in it, and no lab file gives their mass.
- bench/sim_profiles.py still replays the star profiles (the battery guard replays and the D16 table in software/SOFTWARE.md section 5 rest on them): its own job.
- walk_with_guard.py's guard tick still reads inside its cycle (0.71 ms every 0.25 s). On the Pi, the share of the walk read (9.coverage) and when a servo copies Present Voltage into its reply are UNVERIFIED.
- UPSTREAM_ISSUES.md was triaged against the decisions up to D12 only; D13 to D25 are not checked against the upstream issues (VERIFICATION.md C9 WARN).
- Not published: the XT30U cup diameter, the resistor, LED and cell holder lead diameters (3 sleeve sizes open), the holder lead length. The projector's 4 mm lead channel holds one sleeved joint at a time: the cathode joint sits staggered behind the resistor (a fit check at the build).

3D view (private artifact): https://claude.ai/artifact/PHSJH2PwQZLhZnTf9WgaMo
