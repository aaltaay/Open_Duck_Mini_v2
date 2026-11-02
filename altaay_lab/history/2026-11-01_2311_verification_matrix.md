# Verification matrix: every check that runs without the robot

- When: 2026-11-01 11:11 PM (America/New_York)
- Source: this commit, branch claude/every-part; checks by the verification sub-agent (agent Q), after Ahmed said there were tests still to do
- Written: 2026-11-01 by the Claude Code agent

- VERIFICATION.md and verify/ (run_all.sh runs everything, results outside the repo): 22 checks, 17 PASS, 5 FAIL, 0 NOT RUN. Passing: ERC (0 errors, catches 9 of 10 injected faults), BOM totals and bom.json, CAD part counts, both sims reproduce the docs, servo IDs and GPIO agree across netlist, docs, viewer and the Runtime, current ratings, the hip yaw range (walk and turn reach at most 10.4 deg against the 21.7 deg where F198 and F211 touch; nothing in the Runtime clamps hip yaw, so a limit is needed before TEST_PLAN 8.3).
- FAIL E6b: the TEST_PLAN section 5 hop gate (40 mOhm) is too loose for the section 9 ankle gate; even 22 AWG leg leads leave an ankle under 6 V 19 % of the walk (sim). Handed to the power path follow-up.
- FAIL E8: after the rustypot panic the fallback stop reports torque off while servos keep torque (flaky under load). Being fixed: read register 40 back and retry.
- FAIL C1: BOM_FULL.md stale, and the proposed adhesive tie mounts had no BOM line (being added).
- FAIL C3: D3 and D4 foot jumpers (cut 40, route 54 mm) and D7 projector leads (cut 160, route 178 mm) are short before slack; cut lengths to change in the netlist with the cable routing's final numbers.
- FAIL C9: blocker counts and B8, B18 wording disagree across STATE, BOM, CABLE_MAP and HARDWARE_AUDIT; fixed in the docs pass.
