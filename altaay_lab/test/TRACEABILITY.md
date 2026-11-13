# Traceability: Definition of Done gates to tests

Written 2026-11-13. A row is not closed because a test exists. DEFINITION_OF_DONE.md says a sim, a calc, and a CAD check do not pass a gate. Status here is the gate status, not the status of the script.

| Gate | Clause | Test or procedure | Status | Evidence |
|---|---|---|---|---|
| 0 | Mechanical, every solid in the twin | CAD checks in print/ and twin/sit/SIT.md. Nest install is still open. | GAP | TWIN_CHECKLIST.md complete 3D row |
| 0 | Mechanical, screws D42 and D39 | twin/holes/HOLES_TWIN.md. Nest not in the same set. | GAP | CAD check only |
| 0 | Mechanical, fall loads and margin | twin/structure/STRUCTURE_TWIN.md | GAP | FEA pass only, several parts under the margin |
| 0 | Mechanical, topology re-run | No study that is installed in print/ | GAP | V1_PLAN.md is not the study |
| 0 | Mechanical, friction and stiffness from a coupon | test/CHARACTERIZATION.md CHAR-SIT and CHAR-SOLE | GAP | Friction is BLOCKER |
| 0 | Thermal, charger in the duck, windows held | twin/thermal/BQ24133_HEAT.md and test/bec12_heat.py | GAP | Sim pass only. Die in the trunk is BLOCKER. |
| 0 | Electrical, netlist is the duck | wiring/netlist.yaml, sim/POWER_PATH_SIM.md. Nest nets and the charger board are not that netlist. | GAP | TWIN_CHECKLIST.md electrical row |
| 0 | Software, same code on the twin, camera included | software/servo_limits.json. No camera program. | GAP | D61 camera finding is untested |
| 0 | Bill, one click | bom/order/ORDER.md | GAP | Felt, wells, gate board, weld are BLOCKER |
| 1 | Mechanical, datasheet on every screw, pin, cloth, felt | PARTS_AUDIT.md. Pin tip mismatch already noted. | GAP | Standards not applied as a check |
| 1 | Thermal, servo, cell, and PLA limits match the sheets | test/bec12_heat.py window block. Twin 70 C cut is on the sheet. The 60 C operating line is the one the walk leaves. | GAP | Sim pass only |
| 1 | Electrical, servo, cell, charger, radio match a datasheet | Opened sheets in PARTS_AUDIT.md and circuitry/. Charger die in the trunk is BLOCKER. | GAP | Stall used by the old walk is stronger than the C001 sheet |
| 1 | Software, limits inside the printed stops | software/servo_limits.json, TEST_PLAN 19.1 | GAP | Not read back from a servo |
| 1 | Automated part limits | verify/part_limits.yaml and verify/check_power_limits.py | GAP | Named so they are not written twice. Not in this change. |
| 2 | Mechanical, cables, fits, sit, well coupon | TEST_PLAN 1, 19, 20.1 to 20.4. Templates in test/records/templates/. | GAP | Not run |
| 2 | Thermal, servo hold, switch, charger in the duck | TEST_PLAN 7.3, 4.2, 20.8. tp_04_switch.yaml, tp_20_charge_heat.yaml | GAP | Not run |
| 2 | Electrical, pack, regulator, hop, walk log, gate | TEST_PLAN 3 to 9 and 20.5. tp_04_bec.yaml, tp_05_hop.yaml, tp_09_walk.yaml | GAP | Not run |
| 2 | Software, limits, walk log, cutoff on the real bus | TEST_PLAN 8, 9, 11, 19.1. Bench scripts pass on a simulated bus only. | GAP | software/SOFTWARE.md |
| 3 | Mechanical, ten sits, low pack and full pack | TEST_PLAN 20.6 and 20.7 | GAP | Sims fell on a mat edge. That is not this gate. |
| 3 | Thermal, cells and PLA after those docks | TEST_PLAN 20.8 after 20.6 | GAP | Not run |
| 3 | Electrical, charge current at both pack levels | TEST_PLAN 20.7 | GAP | Not run |
| 3 | Software, camera finds the nest | TEST_PLAN 20.9 | GAP | Pose stand-in is not a camera |
| 4 | Mechanical, life counts written before the test | test/WEAR_COUPONS.md. Knee loop is TEST_PLAN 19.7. | GAP | Counts are written. Cycles are not run. |
| 4 | Thermal, worn contact has no hot spot | WEAR_COUPONS.md well section, 10 min at 1.00 A | GAP | Not run |
| 4 | Electrical, ohms after wear inside the 20.1 line | tp_20_contact.yaml | GAP | Not run |
| 4 | Software, dock program unchanged after refit | No dock program yet | GAP | MISSING |
| 5 | Mechanical, pins stay in, coin does not bridge | TEST_PLAN 20.3 | GAP | Not run |
| 5 | Thermal, charge temperatures | TEST_PLAN 20.8. Sim sit is not this pass. | GAP | Sim pass only for the shell |
| 5 | Electrical, two-wire gate, and UN 38.3 for any shipped pack | TEST_PLAN 20.5. 49 CFR 173.185. | GAP | Pack is not built |
| 5 | Software, duck does not stand on a live mat | fault_inject.py charge_allowed. Not product code. | GAP | Specification test only |
| 6 | Mechanical, radio label on the outside | COMPLIANCE_FIRST_PASS.md. FCC id not read from the grant. | GAP | 47 CFR 15.212 |
| 6 | Thermal, lab report if the standard asks | IEC 62133-2 and UL 2054 named in the playbook. Text not opened. | GAP | Uncertain |
| 6 | Electrical, host radio check and unintentional radiator | COMPLIANCE_FIRST_PASS.md | GAP | Not submitted |
| 6 | Software, camera on only when a person can tell | No product code | GAP | MISSING |
| 7 | Mechanical, days of walking, sitting, docking, falls, get-up | No field log | GAP | Get-up is sim pass only |
| 7 | Thermal, logs over those days inside the named limits | No field log | GAP | NEEDS HARDWARE |
| 7 | Electrical, returns to the nest alone | TEST_PLAN 20.9 and the charge program | GAP | Not written |
| 7 | Software, fall recovery on the robot, camera privacy | COMPLIANCE_FIRST_PASS.md | GAP | Not written |
| 8 | Mechanical, a second person builds from the documents | twin/assembly/BUILD_ORDER.md, fasteners/. Nest not included. | GAP | Nothing has been built |
| 8 | Thermal, second unit matches the first within a band written first | Band is not written because the first unit has no log | GAP | NEEDS HARDWARE |
| 8 | Electrical, second unit uses the final bill | PARTS_AUDIT.md | GAP | Bill does not match the twin |
| 8 | Software, a user guide | No user guide | GAP | MISSING |

Playbook levels that point at these gates are in test/PLAYBOOK.md.
