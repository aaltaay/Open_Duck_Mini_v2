# STATE

Last updated: 2026-11-01 (America/New_York)

- Phase: research done, nothing purchased, nothing printed.
- Upstream cloned and read on the lab box (not committed here).
- US BOM drafted: core about $570, with expression pack about $616, before shipping and tax (see BOM.md). Several lines are estimates marked (not verified).
- Gap list drafted (GAPS.md). Open questions for Ahmed are in DECISIONS.md.
- Sim check: MJCF loads in MuJoCo 3.17 on the box, 14 actuators, about 2.11 kg.
- D3 decided 2026-11-01 1:09 PM ET: servo regulator added (Castle CC BEC Pro at 7.2 V, 15 A fuse). BOM with lab changes: core $684.99, grand $730.94.
- Wiring schematic drafted (WIRING.md, wiring/).
- Sim: stock BEST_WALK_ONNX_2 walks in MuJoCo with no falls, about 0.097 m/s for a 0.15 m/s command, turns about 0.81 rad/s for 1.0 (sim/SIM_WALK.md).
- Hardware audit done 2026-11-01 (HARDWARE_AUDIT.md, PRINT_CHECK.md, CABLE_MAP.md, MOUNTING.md): every hole, insert, bearing seat and cable measured from upstream STL commit 730c14b. Final BOM: build $715.27, with expression $761.22, with tools $899.89, before shipping and tax. 29 BLOCKERS listed with what is needed to clear each.
- Blockers before ordering: servo variant (D1), Pi Zero 2 W stock in US, a Windows PC to program the BEC.

## Next
1. Ahmed answers D1, D2, D4, D6, D7.
2. Order a single STS3215 of the chosen variant and bench test it at 7.2 V (regulated) and at low pack voltage.
3. Print one leg in PLA, check bearing fit (6804ZZ, seat measured 32.19 mm) and insert size.
4. Bench test the CC BEC Pro: setpoint, dropout at 7.0 and 6.5 V input, temperature at 8 A with no airflow.
