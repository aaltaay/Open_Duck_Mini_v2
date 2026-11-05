# Battery bay for the 2S1P Molicel P45B pack (V1 track 9, D44, D45)

Written 2026-11-05 about 1:00 AM ET by the V1 battery job (track 9) for the lead. CAD check only, calc only and sim pass only;
nothing printed, bought or built. The study behind it: BATTERY_STUDY.md (this folder); the dock side: CHARGE_INTERFACE.md.

## 1. What changed
- **Cell (D44):** Molicel INR21700-P45B, 2 in series, spot-welded with pure nickel strip in a 2S sleeve, no holder (BOM lines
  6 and 7). P45B: 4.5 Ah typical, 45 A continuous, 15 mOhm DC at 50 % SOC, 21.40 +/- 0.15 x 70.00 +/- 0.15 mm, 70.0 g max
  (Molicel INR21700P45B-01 v0.2). The cell comparison (BATTERY_STUDY.md section 8.2) found no cell that clearly beats it by
  the D45 rule; the Molicel P50B (5.0 Ah, 12.8 mOhm, 21.55 x 70.15 mm max, 71 g, $11.99 in stock on 2026-11-04 ET) fits the
  same bay and is the drop-in if the P45B ($9.99) is still out of stock. So no new DECISIONS entry.
- **print/body_back.stl:** the bay grows from a 20.6 x 41.4 mm free section to the pack's outline: the cut (bay_edit.py,
  manifold3d difference, watertight) is a prism over z -4.5 to 67.5 mm (trunk frame) with the section
  (-119.0, -20.7), (-137.8, -20.7), (-144.45, -14.05), (-144.45, 16.9), (-137.8, 23.55), (-119.0, 23.55) mm: 45 deg chamfers
  tangent to the two cell outlines (0.25 mm clear), so the part still prints front face down (up = -x) with no support on them.
  All the widening is on +y: the charger screw F123's pilot ends 1.0 mm from the -y wall, as before.
- **Unchanged:** battery_pack_lid.stl (its centre pad at x -121.5 sits 0.5 mm in front of the pack; a 1 mm foam pad goes on
  it), the Tenergy 32175 BMS seat (y -24.9 to -28.5) and its wall, the XT30 seat (y +30), the fuse holder and the Pololu 2813
  on the lid face, the 3 lid screws (D38, D42) and every other screw: no screw pattern changes (D42) and no hole opens (D39).

## 2. CAD check (bay_edit.py, data/bay_edit.json)
| Check | Result |
|---|---|
| body_back watertight after the cut | yes; solid 105982.6 to 89439.7 mm3 |
| the pack (two 22.2 mm sleeve circles on axes x -133.1, y -9.35 and +12.2, z -4.0 to 67.0) against every part at the zero pose | 0 mm3 overlap with every part, the edited body_back included |
| material left (rays) | back 9.65 mm (was 14.4), the two chamfers 5.48 and 7.53 mm, +y side 2.25 mm (was 5.1), -y side 5.1 mm (unchanged) |
| fastener pilots near the cut | F027 4.17 mm, F028 3.34 mm (lid screws, axis to the cut); F017, F018 over 6 mm; F123 1.0 mm (unchanged) |
| close-ups looked at | section views before and after (z = 31.5, x = -133.1, y = +12.2 mm; bay_png.py) and three viewer close-ups of the bay (cells seated, lid on and off) |

## 3. Print (print/slice.py parts --only body_back.stl, PrusaSlicer 2.7.2, D22 light profile)
78.48 to 79.21 g with support (support 8.10 to 10.72 g), 6.42 to 6.54 h; model 70.34 to 68.45 g (the run before the change gave
78.48 g against SLICE_SUMMARY.md's 78.28 g: run to run noise). print/SLICE_SUMMARY.md row and per part total updated; plates
not re-run.

## 4. Mass and centre of mass (sim/mass_budget.py, calc only)
+26.0 g for the pack (2 x 70.0 g cells, 5 g strip, sleeve and leads UNVERIFIED, the 25 g holder out), -1.7 g body_back:
2720.1 g, about 2.72 kg with the STS3250 knees (not weighed). Whole robot centre of mass at the home pose [-27.6, 0.4, 49.7] to
[-28.7, 0.5, 49.4] mm (1.1 mm back; the walk held 3.6 to 4.4 mm back in sim/ADDED_MASS_SIM.md). Trunk principal inertia
(kg m2 x 1e-4) [19.70, 34.90, 41.26] to [19.84, 36.98, 43.39].

## 5. Walk, falls and get-ups at the new mass (sim pass only)
The shared lab gym (overlay gym/overlays/duck), the V1 electrical job's push sets with the track 1b guard and the get-up
library, the stock policy, STS3250 knees (`sts3250_high_d0.56` for the walk and pushes, `sts3250_high` for get-ups, as the
V1 knee job ran them), the final pack at its seats (trunk inertial patched in the run process only):

| Check | Today (P30B) | P45B pack |
|---|---|---|
| hard shoves, falls | 28 of 29 | 28 of 29 |
| policy left running on the floor, falls | not run in the knee job | 8 of 9 |
| push ladder (10 to 25 N), falls | 8 of 24 | 7 of 24 |
| 15 N push series while walking | no fall | no fall |
| 20 s walk at 0.15 m/s | 1.321 m | 1.292 m (-2 %) |
| worst 4 ms servo bus | 9.63 A | 9.72 A |
| get-ups at 7.2 V: back / side | 19 of 19, up 10.3 s / 10 of 10, 11.8 s | the same |
| live twin, continuous walking, 32 C, backlash (run with the cells at the old seats, +46 g: heavier and 0.6 mm further back than the final pack) | 24.6 walking min to the battery stop, 0.086 m/s, knee 63 C | 30 min run, 51 % left, 0.103 m/s, knee 64 C, no cut, lowest servo 6.04 V |

The front get-up program fails to load in both (a pre-existing get-up library error). Runtime per charge (calc on the twin's
pack power, BATTERY_STUDY.md section 5.5): 39 walking minutes and 50 min sessions (50/50), against 24.6 and 33 today.

## 6. Heat at the dock charge current (DOCK_INTERFACE.md: 2.0 A; calc only)
Cells 2 x 2.0^2 x 0.015 = 0.12 W, BMS main loop 2.0^2 x 0.025 = 0.10 W, fuse and XT30 under 0.05 W: about 0.27 W in the bay.
Adiabatic bound over a 2.6 h charge (4.5 Ah at 2.0 A, x 1.15 for the CV tail): 0.27 W x 9360 s / (145 g x about 1.0 J/(g K))
= 17 K; the bay's thermal resistance is a BLOCKER, and 10 to 20 K/W (ASSUMPTION) gives 3 to 5 K at the cells. Walking heat in
the cells drops from about 0.72 W (P30B, 17 mOhm, 4.61 A) to 0.57 W (P45B, 15 mOhm, 4.37 A).

## 7. Checks run on this tree
- Viewer data rebuilt (viewer/make_viewer_data.py, the cells drawn as 21.4 x 70 mm cylinders on the new axes, the holder as the
  pack strips); viewer/test_viewer.js: STATE loaded, ERRORS none, 0 mismatches.
- verify/c1_bom_coverage.py, c2_connectors.py and c4_fasteners.py: the same results as on the base 3191e03 (their FAILs are
  older: the BOM line 12 count, F07 in BOM_FULL, D13 PI.37); verify/c9_docs.py PASS, 0 FAIL, the base's 10 WARN.
- BOM_FULL.md and bom_full.csv: only rows E01 and E02 changed, by hand from the generator's output (the generator would also
  rewrite older rows: the STS3250 split and the D36 tools, as the 2e follow-up noted).

## 8. Left open
- BLOCKER: the nickel strip, sleeve and spot welding (a tool or a pack shop), not sourced or priced (BOM line 7 at $0.00).
- cables3d still starts the pack leads at the old cell foot (-129.6, -10.5, -6.5 mm); the new pack's lead ends are within
  4 mm of it; C3 was not re-run (track 4).
- The dock's sense NTC on the cells (DOCK_INTERFACE.md C3): a seat is left in the valley between the cells under the lid
  pad; the dock job wires it.
- First print: check the +y side wall (2.25 mm) and the chamfers; the slice puts 10.72 g of support in the bay.
