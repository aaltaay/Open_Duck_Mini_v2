# STATE

Last updated: 2026-11-01 7:32 PM ET (America/New_York), Claude Code agent, print-readiness pass (started about 7:00 PM ET). Earlier entries are in history/.

- Phase: design ready for the first print; nothing purchased, nothing printed.
- Blockers: 18 of 30 cleared or decided (B30, the hip roll screw from upstream issue 17, was found by the print package check and decided by D18), 4 settled by the coupon test prints, 6 assembly or bench checks with real parts, 2 waiting on part arrival for fit (B8 speaker, B18 USB cable, both chosen). No print-blocking blocker left (HARDWARE_AUDIT.md section 6).
- Decisions D1 to D18 made under Ahmed's delegation (DECISIONS.md), including the power path (Tenergy BMS, 15 A fuse, Pololu 2815 switch, CC BEC Pro at 7.2 V, servo power bypassing the adapter) and the GPIO mapping to the Runtime code.
- Parts not in the CAD all have measured seats; no STL edit needed (MOUNTING.md, audit/placements.json).
- Electrical verification (sim pass only): current budget, ngspice power path, ERC with 0 errors, TEST_PLAN.md with pass/fail numbers.
- Wiring: wiring/netlist.yaml is the single source; schematic, harness and pictorial drawings are generated from it.
- Upstream: all 137 issues and PRs triaged (UPSTREAM_ISSUES.md).
- Exploded 3D parts check (private artifact): https://claude.ai/artifact/PHSJH2PwQZLhZnTf9WgaMo

- Print package (print/PRINT_PLAN.md, sliced estimates): coupon session 5.0 h (27.8 g PLA, 18.2 g TPU); full print 126.4 h in 15 jobs on a 220 mm bed (1474.5 g PLA, 18.1 g TPU, includes 10 spares). Robot set alone: 1372.7 g PLA, 114.4 h.

## Open questions for Ahmed
1. OK to start the coupon print session (print/PRINT_PLAN.md: 5.0 h, 27.8 g PLA, 18.2 g TPU)? (lab rule 4)
2. OK to buy the test order (BOM.md "Needs test order")? (lab rule 7)
3. Which printer will print the duck? (the package is printer-agnostic, bed at least 220 x 220 mm)

## Next
1. Coupon session, results into history/.
2. Test order bench checks: TEST_PLAN.md sections 1 to 7.
3. Freeze tag, full print, assembly map.
4. Staged power-up and the walking voltage log: TEST_PLAN.md sections 8 to 11.
