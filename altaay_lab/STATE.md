# STATE

Last updated: 2026-11-02 about 1:20 AM ET (America/New_York) by agent NL2, final docs pass of the 2026-11-01 night session. Each job has its own entry in history/.

Phase: ready for the coupon print. Nothing bought, nothing printed.

## Done tonight (2026-11-01 evening into 2026-11-02)
- Every-part BOM (BOM_FULL.md) and the cable-by-cable harness build sheet (HARNESS_BUILD.md).
- Mass budget: the build is 2.65 kg (2.77 kg before D22), 26 % over the trained 2.107 kg; the stock policy still walks it on flat ground, slower (sim pass only; the walks ran at 2.77 and 2.64 kg).
- Sourcing pass: missing purchase lines and test equipment TE1 to TE4 (SOURCING_2026-11-02.md, BOM.md).
- Connectors, splices, solder joints and small parts in the 3D view (viewer/scene_extras.json, blueprint/).
- Fastener schedule: 342 screws to fit, 221 to buy, 58 inserts, 16 washers, two 0.3 mm under each eye screw (fasteners/; D19 to D21 and the D21 note).
- Pi setup from a blank SD card, and bench scripts tested on a simulated servo bus (software/, bench/).
- Servo upgrade options in case the TO1 heat test fails (SERVO_UPGRADE_OPTIONS.md).
- Clean wiring sheets, one subsystem per sheet (wiring/sheets/).
- Verification matrix of every check that needs no robot (VERIFICATION.md, verify/).
- Every cable routed in 3D with seats, ties and joint loops (cables3d/); tie mounts and ties in the BOM.
- Light print profile: 128 g lighter, gated by light coupons in S1 (print/MASS_STUDY.md; D22).
- Power fix: second feeds SP4 and SP5 into both ankles, 3S pack held (sim/POWER_FIX.md; D23).
- Netlist final pass: cables3d cut lengths, SP4 and SP5 (390 and 420 mm), fuse holder lead extensions, refs and labels; ERC 0 errors on 124 wires; sheets, harness sheet, BOM and BOM_FULL rebuilt (agent NL1).
- Final docs pass: D23 and D24, bench gates in TEST_PLAN.md, blockers B33 to B35, verification re-run.

## Decisions
D1 to D24 are in DECISIONS.md, all decided (D14 superseded by D15). Tonight: D19 button heads at the hip pitch, D20 drill the neck recesses, D21 eye screw washers, D22 light print profile, D23 ankle feeds with the 3S pack held, D24 drill the projector lead hole.

## Blockers and checks
- Blockers: 21 of 35 cleared or decided, 2 waiting on the parts check, 5 settled by the coupon test prints, 7 assembly or bench checks. None blocks the coupon print (HARDWARE_AUDIT.md section 6).
- Verification (VERIFICATION.md, full run 1:05 to 1:16 AM ET): 22 checks, 21 PASS, 1 FAIL, 0 NOT RUN. The FAIL is C3: two 20 mm ground tails (JG10 and JG30 to the first servo) route 21 mm. Sim and test pass only; nothing has run on real parts.

## Open questions for Ahmed (one at a time, most important first)
1. OK to start the coupon print session? S1: 9 coupons, 36.2 g PLA, 3.60 h. S2: one TPU sole, 17.6 g, 2.19 h (print/PRINT_PLAN.md; lab rule 4).
2. OK to buy the test order (BOM.md "Needs test order", $226.46)? (lab rule 7)
3. Which printer will print the duck? The package needs a bed of at least 220 x 220 mm.

## Next
1. Coupon session; results into history/.
2. Test order: TEST_PLAN.md sections 1 to 7 (cables, battery and BMS, BEC dropout, Pololu 2815 heat, 5 V regulator, one servo with register 85, firmware and the thermal hold, Kelvin hop).
3. First leg print and its checks (D18, D19, the B33 foot_side fit), then the other plates: the full print on a 220 bed is 18 jobs, 1347.8 g PLA, 17.6 g TPU, 118.6 h (with the coupons 1384.0 g PLA, 124.4 h). Then the freeze tag.
4. Staged power-up with the hip yaw limit, then the walking voltage log (TEST_PLAN.md sections 8 to 12). The log decides the 3S pack (D23).
5. Later lab step: self-docking and get-up after falls, in sim first.

3D view (private artifact): https://claude.ai/artifact/PHSJH2PwQZLhZnTf9WgaMo
